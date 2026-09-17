#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：engine.py
@Explain : 审批流引擎

负责流程的：发起、审批流转、条件分支判断、抄送、并行审批、驳回、撤回。
节点数据契约与 AntFlow-Designer 前端保持一致：
- nodes 为扁平数组，每个节点包含 nodeId/nodeName/nodeType/nodeFrom/nodeTo/nodeProperty
- 节点类型：1-开始 2-条件网关 3-条件 4-审批人 5-并行审核网关 6-抄送人 7-并行审核人
"""
import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from .models import FlowData, FlowRecord, FlowAuditUsers

user = get_user_model()
logger = logging.getLogger(__name__)


# ==================== 常量（与前端 constant.js 一致） ====================
class NodeType:
    StartNode = 1              # 开始节点
    GatewayNode = 2            # 条件网关
    ConditionNode = 3          # 条件节点
    ApproveNode = 4            # 审批人
    ParallelApproveWayNode = 5 # 并行审核网关
    CopyNode = 6               # 抄送人
    ParallelApproveNode = 7    # 并行审核人


# 流程状态
STATUS_RUNNING = 0    # 进行中
STATUS_APPROVED = 1   # 审核通过
STATUS_REJECTED = 2   # 审核驳回
STATUS_REVOKED = 3    # 审核撤销


# 审批人类型
class AssigneeType:
    Member = 1        # 指定成员
    Role = 2          # 指定角色
    Leader = 3        # 直属领导
    Self = 5          # 发起人自己
    DirectorLevel = 6 # 指定层级主管
    MultiLevel = 7    # 层层审批
    SelectByStarter = 8  # 发起人自选审批人


class FlowEngineError(Exception):
    """流程引擎业务异常"""
    pass


class FlowEngine:
    """审批流引擎"""

    # ==================== 发起流程 ====================
    @classmethod
    def start(cls, flow_info, form_data=None, start_user=None, selected_approvers=None):
        """
        发起流程
        :param flow_info: FlowInfo 实例
        :param form_data: 申请表单数据 dict
        :param start_user: 发起人 UserModel
        :param selected_approvers: 发起人自选审批人 {nodeId: [userId,...]}
        :return: FlowData 实例
        """
        if not start_user:
            raise FlowEngineError("缺少发起人")
        if flow_info.status != 1:
            raise FlowEngineError("流程未发布，无法发起")
        nodes = cls._get_nodes(flow_info)
        if not nodes:
            raise FlowEngineError("流程未配置节点")

        with transaction.atomic():
            flow_data = FlowData.objects.create(
                flow_info=flow_info,
                name=flow_info.name,
                status=STATUS_RUNNING,
                start_user=start_user,
                form_data=form_data or {},
                selected_approvers=selected_approvers or {},
                current_node={},
            )
            start_node = cls._find_start_node(nodes)
            if not start_node:
                raise FlowEngineError("流程缺少开始节点")
            cls._advance(flow_data, start_node, nodes, parent_node_id=None, is_start=True)
            # 如果发起后没有任何进行中的审批节点（全跳过/全抄送），则直接完成
            flow_data.refresh_from_db()
            if flow_data.status == STATUS_RUNNING and not flow_data.current_node:
                cls._finish(flow_data, STATUS_APPROVED)
            return flow_data

    # ==================== 节点推进 ====================
    @classmethod
    def _advance(cls, flow_data, node, nodes, parent_node_id=None, is_start=False):
        """
        递归推进流程节点（事务内调用）
        :param node: 当前要处理的节点 dict
        :param parent_node_id: 并行分支所属的网关节点 id
        """
        if not node:
            return
        node_type = node.get("nodeType")

        if node_type == NodeType.ApproveNode or node_type == NodeType.ParallelApproveNode:
            cls._handle_approve_node(flow_data, node, parent_node_id)
            return

        if node_type == NodeType.CopyNode:
            cls._handle_copy_node(flow_data, node)
            # 抄送完成后继续后续节点
            cls._advance(flow_data, cls._next_node(nodes, node), nodes, parent_node_id)
            return

        if node_type == NodeType.GatewayNode:
            cls._handle_gateway(flow_data, node, nodes)
            return

        if node_type == NodeType.ParallelApproveWayNode:
            cls._handle_parallel_way(flow_data, node, nodes)
            return

        if node_type == NodeType.ConditionNode:
            # 条件节点本身不处理，由网关逻辑选择后从其分支进入
            cls._advance(flow_data, cls._next_node(nodes, node), nodes, parent_node_id)
            return

        if node_type == NodeType.StartNode:
            cls._advance(flow_data, cls._next_node(nodes, node), nodes, parent_node_id)
            return

        # 未知类型节点直接跳过
        cls._advance(flow_data, cls._next_node(nodes, node), nodes, parent_node_id)

    @classmethod
    def _handle_approve_node(cls, flow_data, node, parent_node_id=None):
        """处理审批节点：解析审批人并创建待办记录"""
        approvers = cls._resolve_approvers(node, flow_data)
        if not approvers:
            # 审批人为空处理策略
            no_header_action = int((node.get("nodeProperty") or {}).get("noHeaderAction", 1))
            if no_header_action == 0:
                raise FlowEngineError(f"节点「{node.get('nodeName', '审批')}」未配置审批人，不允许发起")
            # 1-跳过 2-转交管理员（此处同样跳过并记录日志）
            FlowRecord.objects.create(
                flow_data=flow_data,
                type="Approval",
                status=STATUS_APPROVED,
                current_node_id=node.get("nodeId"),
                parent_node_id=parent_node_id,
                comment="审批人为空，已跳过",
                completed_time=timezone.now(),
            )
            nodes = cls._get_nodes(flow_data.flow_info)
            cls._advance(flow_data, cls._next_node(nodes, node), nodes, parent_node_id)
            return

        approver_ids = [u.id for u in approvers]
        # 更新流程当前节点
        flow_data.current_node = {
            "node_id": node.get("nodeId"),
            "node_name": node.get("nodeName") or node.get("nodeDisplayName") or "审批",
            "node_type": node.get("nodeType"),
            "approvers": approver_ids,
            "sign_type": int((node.get("nodeProperty") or {}).get("signType", 1)),
            "assignee_type": int((node.get("nodeProperty") or {}).get("assigneeType", 1)),
            "parent_node_id": parent_node_id,
        }
        flow_data.save(update_fields=["current_node", "update_datetime"])
        # 创建流转记录 + 审核人员
        record = FlowRecord.objects.create(
            flow_data=flow_data,
            type="Approval",
            status=STATUS_RUNNING,
            current_node_id=node.get("nodeId"),
            parent_node_id=parent_node_id,
        )
        FlowAuditUsers.objects.bulk_create([
            FlowAuditUsers(flow_record=record, audit_user=u, status=STATUS_RUNNING)
            for u in approvers
        ])

    @classmethod
    def _handle_copy_node(cls, flow_data, node):
        """处理抄送节点"""
        copyers = cls._resolve_approvers(node, flow_data)
        if not copyers:
            return
        record = FlowRecord.objects.create(
            flow_data=flow_data,
            type="Cc",
            status=STATUS_APPROVED,
            current_node_id=node.get("nodeId"),
            comment=f"抄送：{node.get('nodeName', '抄送')}",
            completed_time=timezone.now(),
        )
        record.pre_user.set(copyers)

    @classmethod
    def _handle_gateway(cls, flow_data, node, nodes):
        """处理条件网关：选择命中分支并推进"""
        form_data = flow_data.form_data or {}
        node_property = node.get("nodeProperty") or {}
        condition_nodes = node_property.get("conditionNodes") or []
        if not condition_nodes:
            # 无分支配置，直接继续
            cls._advance(flow_data, cls._next_node(nodes, node), nodes)
            return
        # 按优先级排序（nodeWeight），默认分支（isDefault=1）兜底
        ordered = sorted(condition_nodes, key=lambda c: (1 if (c.get("nodeProperty") or {}).get("isDefault") == 1 else 0, c.get("nodeWeight", 0)))
        matched = None
        for cond in ordered:
            if (cond.get("nodeProperty") or {}).get("isDefault") == 1:
                matched = cond
                continue
            if cls._check_condition(cond, form_data):
                matched = cond
                break
        if not matched:
            matched = ordered[0]
        # 进入选中的分支链（分支内节点通过 nodeTo 链式衔接，分支尾部 nodeTo 指向合并节点）
        branch_start = cls._next_node(nodes, matched)
        if branch_start is None:
            # 空分支：直接推进网关的合并节点
            merge_node = cls._find_merge_node(nodes, node.get("nodeId"))
            cls._advance(flow_data, merge_node, nodes)
            return
        cls._advance(flow_data, branch_start, nodes)

    @classmethod
    def _handle_parallel_way(cls, flow_data, node, nodes):
        """处理并行审核网关：所有分支同时进入审批"""
        node_property = node.get("nodeProperty") or {}
        parallel_nodes = node_property.get("parallelNodes") or []
        if not parallel_nodes:
            cls._advance(flow_data, cls._next_node(nodes, node), nodes)
            return
        gateway_id = node.get("nodeId")
        for branch in parallel_nodes:
            branch_id = branch.get("nodeId")
            branch_start = cls._next_node(nodes, branch)
            if branch_start is None:
                # 空分支直接标记完成
                FlowRecord.objects.create(
                    flow_data=flow_data,
                    type="Approval",
                    status=STATUS_APPROVED,
                    current_node_id=branch_id,
                    parent_node_id=gateway_id,
                    comment="空分支已跳过",
                    completed_time=timezone.now(),
                )
                continue
            cls._advance(flow_data, branch_start, nodes, parent_node_id=gateway_id)
        # 当前节点记录为并行网关
        flow_data.current_node = {
            "node_id": gateway_id,
            "node_name": node.get("nodeName") or "并行审批",
            "node_type": node.get("nodeType"),
            "approvers": [],
            "sign_type": 2,
            "assignee_type": 0,
            "parent_node_id": None,
        }
        flow_data.save(update_fields=["current_node", "update_datetime"])

    # ==================== 审批操作 ====================
    @classmethod
    def approve(cls, flow_data, node_id, audit_user, comment=""):
        """审批通过（同意）"""
        return cls._handle_audit(flow_data, node_id, audit_user, comment, is_agree=True)

    @classmethod
    def reject(cls, flow_data, node_id, audit_user, comment=""):
        """审批驳回（拒绝）"""
        return cls._handle_audit(flow_data, node_id, audit_user, comment, is_agree=False)

    @classmethod
    def _handle_audit(cls, flow_data, node_id, audit_user, comment="", is_agree=True):
        """
        处理审批动作
        支持：或签(1) / 会签(2) / 顺序会签(3)
        """
        if flow_data.status != STATUS_RUNNING:
            raise FlowEngineError("流程已结束，无法审批")
        current = flow_data.current_node or {}
        current_node_id = current.get("node_id")
        # 并行网关场景：当前节点为并行网关，实际待办在子分支，按待办记录还原节点配置
        if current.get("node_type") == NodeType.ParallelApproveWayNode:
            pending = FlowRecord.objects.filter(
                flow_data=flow_data,
                type="Approval",
                status=STATUS_RUNNING,
                parent_node_id=current_node_id,
                current_node_id=node_id,
            ).first()
            if pending:
                node = next((n for n in cls._get_nodes(flow_data.flow_info) if n.get("nodeId") == node_id), None)
                if node:
                    current = {
                        "node_id": node.get("nodeId"),
                        "node_name": node.get("nodeName") or "审批",
                        "node_type": node.get("nodeType"),
                        "approvers": [u.id for u in cls._resolve_approvers(node, flow_data)],
                        "sign_type": int((node.get("nodeProperty") or {}).get("signType", 1)),
                        "assignee_type": int((node.get("nodeProperty") or {}).get("assigneeType", 1)),
                        "parent_node_id": current_node_id,
                    }
                    current_node_id = current.get("node_id")
        if current_node_id != node_id:
            raise FlowEngineError("该节点不是当前待办节点")
        if current.get("parent_node_id") and current.get("node_type") not in (NodeType.ApproveNode, NodeType.ParallelApproveNode):
            raise FlowEngineError("该节点不是审批节点")

        node_type = current.get("node_type")
        if node_type not in (NodeType.ApproveNode, NodeType.ParallelApproveNode):
            raise FlowEngineError("当前节点不支持审批操作")

        with transaction.atomic():
            # 找到当前节点的进行中记录
            record = FlowRecord.objects.filter(
                flow_data=flow_data,
                current_node_id=node_id,
                status=STATUS_RUNNING,
                type="Approval",
            ).order_by("-create_datetime").first()
            if not record:
                raise FlowEngineError("未找到待办记录")
            audit_qs = FlowAuditUsers.objects.filter(flow_record=record, audit_user=audit_user)
            if not audit_qs.exists():
                raise FlowEngineError("您不是该节点的审批人")
            audit = audit_qs.first()

            sign_type = int(current.get("sign_type", 1))
            approvers = current.get("approvers") or []
            action_name = "同意" if is_agree else "驳回"

            if not is_agree:
                # 任一审批人驳回 → 整个流程驳回
                audit.status = STATUS_REJECTED
                audit.description = comment
                audit.save(update_fields=["status", "description", "update_datetime"])
                record.status = STATUS_REJECTED
                record.handler = audit_user
                record.comment = comment
                record.completed_time = timezone.now()
                record.save(update_fields=["status", "handler", "comment", "completed_time", "update_datetime"])
                cls._finish(flow_data, STATUS_REJECTED)
                return flow_data

            # ===== 同意 =====
            audit.status = STATUS_APPROVED
            audit.description = comment
            audit.save(update_fields=["status", "description", "update_datetime"])

            # 判断节点是否完成
            approved_count = FlowAuditUsers.objects.filter(
                flow_record=record, status=STATUS_APPROVED
            ).count()
            total_count = approvers and len(approvers) or FlowAuditUsers.objects.filter(flow_record=record).count()

            node_done = False
            if sign_type == 1:
                # 或签：一人同意即完成
                node_done = True
            elif sign_type in (2, 3):
                # 会签/顺序会签：全部同意才完成
                node_done = approved_count >= total_count

            if not node_done:
                record.handler = audit_user
                record.comment = comment
                record.save(update_fields=["handler", "comment", "update_datetime"])
                return flow_data

            # 节点完成
            record.handler = audit_user
            record.comment = comment
            record.status = STATUS_APPROVED
            record.completed_time = timezone.now()
            record.save(update_fields=["handler", "comment", "status", "completed_time", "update_datetime"])

            cls._after_node_done(flow_data, node_id, comment)
            return flow_data

    @classmethod
    def _after_node_done(cls, flow_data, node_id, comment=""):
        """节点审批完成后：推进流程（处理并行分支汇聚）"""
        nodes = cls._get_nodes(flow_data.flow_info)
        node_map = {n.get("nodeId"): n for n in nodes}
        done_node = node_map.get(node_id)
        if not done_node:
            return
        # 从已完成的待办记录取父节点，判断是否并行分支（current_node 在并行场景下是网关节点）
        done_record = FlowRecord.objects.filter(
            flow_data=flow_data,
            current_node_id=node_id,
            type="Approval",
            status=STATUS_APPROVED,
        ).first()
        parent_node_id = done_record.parent_node_id if done_record else None
        if parent_node_id:
            # 并行分支：先推进分支链内下一节点（nodeTo 指向合并节点时视为分支结束），分支链结束再检查汇聚
            merge_node = cls._find_merge_node(nodes, parent_node_id)
            next_branch_node = cls._next_node(nodes, done_node)
            if next_branch_node and merge_node and next_branch_node.get("nodeId") == merge_node.get("nodeId"):
                next_branch_node = None
            if next_branch_node:
                cls._advance(flow_data, next_branch_node, nodes, parent_node_id=parent_node_id)
                return
            # 分支链结束：检查同网关下其他分支是否全部完成
            pending = FlowRecord.objects.filter(
                flow_data=flow_data,
                parent_node_id=parent_node_id,
                type="Approval",
                status=STATUS_RUNNING,
            ).exclude(current_node_id=node_id).exists()
            if pending:
                # 还有分支未完成，等待
                return
            # 所有分支完成，推进并行网关的合并节点
            flow_data.current_node = {}
            flow_data.save(update_fields=["current_node", "update_datetime"])
            cls._advance(flow_data, merge_node, nodes)
            cls._check_finish(flow_data)
            return
        # 普通节点：推进下一节点
        flow_data.current_node = {}
        flow_data.save(update_fields=["current_node", "update_datetime"])
        cls._advance(flow_data, cls._next_node(nodes, done_node), nodes)
        cls._check_finish(flow_data)

    @classmethod
    def revoke(cls, flow_data, audit_user, comment=""):
        """发起人撤回流程"""
        if flow_data.start_user_id != audit_user.id:
            raise FlowEngineError("只有发起人可以撤回")
        if flow_data.status != STATUS_RUNNING:
            raise FlowEngineError("流程已结束，无法撤回")
        with transaction.atomic():
            # 未处理的待办记录标记为已撤销
            FlowRecord.objects.filter(flow_data=flow_data, status=STATUS_RUNNING).update(
                status=STATUS_REVOKED, comment=comment or "发起人撤回", completed_time=timezone.now()
            )
            FlowAuditUsers.objects.filter(
                flow_record__flow_data=flow_data, status=STATUS_RUNNING
            ).update(status=STATUS_REVOKED, description=comment or "发起人撤回")
            cls._finish(flow_data, STATUS_REVOKED, comment=comment or "发起人撤回")
        return flow_data

    # ==================== 辅助方法 ====================
    @classmethod
    def _finish(cls, flow_data, status, comment=None):
        """结束流程"""
        flow_data.status = status
        flow_data.completed_time = timezone.now()
        flow_data.current_node = {}
        flow_data.save(update_fields=["status", "completed_time", "current_node", "update_datetime"])

    @classmethod
    def _check_finish(cls, flow_data):
        """流程是否自然结束（无当前节点且无进行中记录）"""
        has_pending = FlowRecord.objects.filter(flow_data=flow_data, status=STATUS_RUNNING).exists()
        if not has_pending and flow_data.status == STATUS_RUNNING:
            cls._finish(flow_data, STATUS_APPROVED)

    @classmethod
    def _get_nodes(cls, flow_info):
        """获取流程节点列表（扁平数组）"""
        config = flow_info.config or {}
        nodes = config.get("nodes") or []
        return nodes or []

    @classmethod
    def _find_start_node(cls, nodes):
        for n in nodes:
            if n.get("nodeType") == NodeType.StartNode:
                return n
        return None

    @classmethod
    def _next_node(cls, nodes, node):
        """取节点的第一个后续节点"""
        node_map = {n.get("nodeId"): n for n in nodes}
        node_to = node.get("nodeTo") or []
        if not node_to:
            return None
        nid = node_to[0]
        return node_map.get(nid)

    @classmethod
    def _find_merge_node(cls, nodes, gateway_id):
        """寻找网关的合并节点（nodeFrom 指向网关且不是条件/并行审批分支节点）"""
        for n in nodes:
            node_from = n.get("nodeFrom") or []
            if gateway_id in node_from and n.get("nodeType") not in (NodeType.ConditionNode, NodeType.ParallelApproveNode):
                return n
        return None

    # ==================== 审批人解析 ====================
    @classmethod
    def _resolve_approvers(cls, node, flow_data):
        """根据节点配置解析审批人"""
        node_property = node.get("nodeProperty") or {}
        assignee_type = int(node_property.get("assigneeType", 1))
        result = []
        if assignee_type == AssigneeType.Member:
            target_ids = [a.get("targetId") for a in (node_property.get("assigneeList") or []) if a.get("targetId")]
            result = list(user.objects.filter(id__in=target_ids))
        elif assignee_type == AssigneeType.Role:
            target_ids = [a.get("targetId") for a in (node_property.get("assigneeList") or []) if a.get("targetId")]
            result = list(user.objects.filter(role__id__in=target_ids).distinct())
        elif assignee_type == AssigneeType.Leader:
            result = cls._find_leader(flow_data.start_user, level=1)
        elif assignee_type == AssigneeType.Self:
            result = [flow_data.start_user]
        elif assignee_type == AssigneeType.DirectorLevel:
            level = int(node_property.get("directorLevel", 1) or 1)
            result = cls._find_leader(flow_data.start_user, level=level)
        elif assignee_type == AssigneeType.MultiLevel:
            result = cls._find_all_leaders(flow_data.start_user)
        elif assignee_type == AssigneeType.SelectByStarter:
            selected = (flow_data.selected_approvers or {}).get(node.get("nodeId")) or []
            result = list(user.objects.filter(id__in=selected))
        # 去重
        if node_property.get("IsDistinct") or flow_data.flow_info.distinct_type in (1, 2):
            seen, unique = set(), []
            for u in result:
                if u.id not in seen:
                    seen.add(u.id)
                    unique.append(u)
            result = unique
        return result

    @classmethod
    def _find_leader(cls, start_user, level=1):
        """查找发起人的第 N 级领导（按部门负责人 name 匹配用户，找不到逐级向上）"""
        if not start_user.dept_id:
            return []
        dept = start_user.dept
        current = dept
        for _ in range(max(level, 1)):
            leader = cls._match_owner(current)
            if leader:
                return [leader]
            current = current.get_parent() if current else None
            if not current:
                return []
        return []

    @classmethod
    def _find_all_leaders(cls, start_user):
        """层层审批：收集从直属部门到根部门所有负责人（从低到高，去重）"""
        if not start_user.dept_id:
            return []
        result = []
        current = start_user.dept
        seen = set()
        while current:
            leader = cls._match_owner(current)
            if leader and leader.id not in seen:
                seen.add(leader.id)
                result.append(leader)
            current = current.get_parent() if current else None
        return result

    @classmethod
    def _match_owner(cls, dept):
        """取部门负责人（owner 为关联用户的外键）"""
        if not dept.owner_id:
            return None
        return dept.owner

    # ==================== 条件判断 ====================
    @classmethod
    def _check_condition(cls, condition_node, form_data):
        """判断条件节点是否命中"""
        node_property = condition_node.get("nodeProperty") or {}
        if node_property.get("isDefault") == 1:
            return True
        groups = node_property.get("groupConditions") or []
        if not groups:
            return False
        group_results = []
        for group in groups:
            condition_list = group.get("conditionList") or []
            if not condition_list:
                group_results.append(False)
                continue
            relation = group.get("condRelation", True)  # True=且 False=或
            item_results = [cls._match_item(item, form_data) for item in condition_list]
            group_results.append(all(item_results) if relation else any(item_results))
        group_relation = node_property.get("groupRelation", False)  # True=且 False=或
        return all(group_results) if group_relation else any(group_results)

    @classmethod
    def _match_item(cls, item, form_data):
        """单条条件比较"""
        field = item.get("columnDbName") or item.get("key")
        if not field:
            return False
        value = form_data.get(field)
        if value is None:
            return False
        opt = item.get("optType") or "="
        target = item.get("zdy1")
        target2 = item.get("zdy2")
        field_type = item.get("type")

        # 多选（checkbox）：值包含选中项
        if field_type == "checkbox":
            values = value if isinstance(value, list) else [value]
            target_list = target if isinstance(target, list) else [target]
            return any(str(v) in [str(t) for t in target_list] for v in values)

        if opt == "between":
            return cls._compare(value, ">=", target) and cls._compare(value, "<=", target2)

        # 数字/日期类型数值化比较，字符串类型直接比较
        if field_type in ("number", "date", "time", "switch", "radio", "select"):
            try:
                return cls._compare(value, opt, target)
            except (TypeError, ValueError):
                return False
        return str(value) == str(target)

    @classmethod
    def _compare(cls, left, opt, right):
        """比较两个值"""
        if right is None or right == "":
            return False
        try:
            l, r = float(left), float(right)
        except (TypeError, ValueError):
            l, r = str(left), str(right)
        if opt == "=" or opt == "==":
            return l == r
        if opt == ">":
            return l > r
        if opt == "<":
            return l < r
        if opt == ">=":
            return l >= r
        if opt == "<=":
            return l <= r
        if opt == "!=":
            return l != r
        return False
