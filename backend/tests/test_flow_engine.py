# -*- coding: UTF-8 -*-
"""审批流引擎测试脚本：覆盖发起/审批/条件分支/抄送/并行/驳回/撤回"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'application.settings')
django.setup()

from django.contrib.auth import get_user_model
from extends.workflow.models import FlowInfoModel, FlowData, FlowRecord, FlowAuditUsers
from extends.workflow.engine import FlowEngine, FlowEngineError

user = get_user_model()

PASS, FAIL = [], []


def check(name, cond, extra=""):
    if cond:
        PASS.append(name)
        print(f"  [PASS] {name}")
    else:
        FAIL.append(name)
        print(f"  [FAIL] {name} {extra}")


def make_node(node_id, name, node_type, node_to=None, node_from=None, prop=None):
    return {
        "nodeId": node_id, "nodeName": name, "nodeType": node_type,
        "nodeTo": node_to or [], "nodeFrom": node_from or [],
        "nodeProperty": prop or {},
    }


def main():
    # ==================== 测试数据准备 ====================
    zhangsan, _ = user.objects.get_or_create(username="flow_zhangsan", defaults={"name": "张三", "is_staff": True})
    lisi, _ = user.objects.get_or_create(username="flow_lisi", defaults={"name": "李四"})
    wangwu, _ = user.objects.get_or_create(username="flow_wangwu", defaults={"name": "王五"})
    zhaoliu, _ = user.objects.get_or_create(username="flow_zhaoliu", defaults={"name": "赵六"})

    # ==================== 场景1：基础流程（指定成员 → 抄送 → 自选审批人） ====================
    print("\n===== 场景1：发起 → 指定成员审批 → 抄送 → 自选审批人 =====")
    flow1 = FlowInfoModel.objects.create(
        name="请假审批", key="leave_flow", status=1, frm_type=1,
        config={"name": "请假审批", "nodes": [
            make_node("s1", "开始", 1, node_to=["a1"]),
            make_node("a1", "部门主管审批", 4, node_from=["s1"], node_to=["c1"], prop={
                "assigneeType": 1, "signType": 1, "noHeaderAction": 0,
                "assigneeList": [{"targetId": lisi.id}],
            }),
            make_node("c1", "抄送人事", 6, node_from=["a1"], node_to=["a2"], prop={
                "assigneeType": 1, "assigneeList": [{"targetId": wangwu.id}],
            }),
            make_node("a2", "总经理审批", 4, node_from=["c1"], prop={
                "assigneeType": 8, "signType": 1, "noHeaderAction": 0,
            }),
        ]},
    )
    fd1 = FlowEngine.start(flow1, form_data={"days": 3, "reason": "回家"}, start_user=zhangsan,
                           selected_approvers={"a2": [zhaoliu.id]})
    check("发起成功", fd1.status == 0 and fd1.current_node.get("node_id") == "a1")
    check("待办记录创建", FlowRecord.objects.filter(flow_data=fd1, type="Approval", status=0).count() == 1)

    # 李四同意 → 进入抄送
    FlowEngine.approve(fd1, "a1", lisi, "同意")
    check("抄送已创建", FlowRecord.objects.filter(flow_data=fd1, type="Cc").count() == 1)
    cc_record = FlowRecord.objects.filter(flow_data=fd1, type="Cc").first()
    check("抄送人正确", cc_record.pre_user.filter(id=wangwu.id).exists())
    check("推进到自选节点", fd1.current_node.get("node_id") == "a2")

    # 非自选人审批被拒绝
    try:
        FlowEngine.approve(fd1, "a2", lisi, "越权")
        check("越权审批被拒绝", False)
    except FlowEngineError as e:
        check("越权审批被拒绝", "不是该节点的审批人" in str(e))
    # 赵六同意 → 流程结束
    FlowEngine.approve(fd1, "a2", zhaoliu, "同意")
    fd1.refresh_from_db()
    check("流程通过", fd1.status == 1)

    # ==================== 场景2：条件分支（金额>1000 → A / 默认 → B） ====================
    print("\n===== 场景2：条件分支 =====")
    cond_a = make_node("cond_a", "金额>1000", 3, node_to=["a_high"], prop={
        "isDefault": 0, "nodeWeight": 0,
        "groupConditions": [{"condRelation": True, "conditionList": [
            {"columnDbName": "amount", "optType": ">", "zdy1": "1000", "type": "number"},
        ]}],
    })
    cond_b = make_node("cond_b", "默认分支", 3, node_to=["a_low"], prop={"isDefault": 1, "nodeWeight": 1})
    flow2 = FlowInfoModel.objects.create(
        name="报销审批", key="expense_flow", status=1, frm_type=1,
        config={"name": "报销审批", "nodes": [
            make_node("s2", "开始", 1, node_to=["g2"]),
            make_node("g2", "金额判断", 2, node_from=["s2"], node_to=["m2"], prop={
                "conditionNodes": [cond_a, cond_b],
            }),
            make_node("a_high", "财务经理审批", 4, node_from=["cond_a"], node_to=["m2"], prop={
                "assigneeType": 1, "signType": 1, "assigneeList": [{"targetId": lisi.id}],
            }),
            make_node("a_low", "部门经理审批", 4, node_from=["cond_b"], node_to=["m2"], prop={
                "assigneeType": 1, "signType": 1, "assigneeList": [{"targetId": wangwu.id}],
            }),
            make_node("m2", "出纳复核", 4, node_from=["g2"], prop={
                "assigneeType": 1, "signType": 1, "assigneeList": [{"targetId": zhaoliu.id}],
            }),
        ]},
    )
    # 金额 5000 → 走财务经理
    fd2 = FlowEngine.start(flow2, form_data={"amount": 5000, "note": "出差"}, start_user=zhangsan)
    check("高额走财务经理分支", fd2.current_node.get("node_id") == "a_high")
    check("分支待办唯一", FlowRecord.objects.filter(flow_data=fd2, type="Approval", status=0).count() == 1)
    FlowEngine.approve(fd2, "a_high", lisi, "金额没问题")
    check("分支完成后进入合并节点", fd2.current_node.get("node_id") == "m2")
    FlowEngine.approve(fd2, "m2", zhaoliu, "复核通过")
    fd2.refresh_from_db()
    check("条件流程通过", fd2.status == 1)

    # 金额 500 → 走部门经理
    fd2b = FlowEngine.start(flow2, form_data={"amount": 500}, start_user=zhangsan)
    check("低额走部门经理分支", fd2b.current_node.get("node_id") == "a_low")

    # ==================== 场景3：并行审批（两分支同时进行） ====================
    print("\n===== 场景3：并行审批 =====")
    p1 = make_node("p1", "并行分支1", 7, node_to=["pa1"], node_from=["g3"])
    p2 = make_node("p2", "并行分支2", 7, node_to=["pa2"], node_from=["g3"])
    flow3 = FlowInfoModel.objects.create(
        name="采购审批", key="purchase_flow", status=1, frm_type=1,
        config={"name": "采购审批", "nodes": [
            make_node("s3", "开始", 1, node_to=["g3"]),
            make_node("g3", "并行网关", 5, node_from=["s3"], node_to=["m3"], prop={
                "parallelNodes": [p1, p2],
            }),
            make_node("pa1", "技术评审", 4, node_from=["p1"], node_to=["m3"], prop={
                "assigneeType": 1, "signType": 1, "assigneeList": [{"targetId": lisi.id}],
            }),
            make_node("pa2", "财务评审", 4, node_from=["p2"], node_to=["m3"], prop={
                "assigneeType": 1, "signType": 1, "assigneeList": [{"targetId": wangwu.id}],
            }),
            make_node("m3", "总监审批", 4, node_from=["g3"], prop={
                "assigneeType": 1, "signType": 1, "assigneeList": [{"targetId": zhaoliu.id}],
            }),
        ]},
    )
    fd3 = FlowEngine.start(flow3, form_data={"goods": "服务器"}, start_user=zhangsan)
    check("并行两分支均创建待办",
          FlowRecord.objects.filter(flow_data=fd3, type="Approval", status=0, parent_node_id="g3").count() == 2)
    # 只完成一个分支 → 流程仍在等待
    FlowEngine.approve(fd3, "pa1", lisi, "技术OK")
    check("单分支完成后等待另一分支",
          FlowRecord.objects.filter(flow_data=fd3, type="Approval", status=0, current_node_id="pa2").exists())
    FlowEngine.approve(fd3, "pa2", wangwu, "财务OK")
    check("全部分支完成后进入合并节点", fd3.current_node.get("node_id") == "m3")
    FlowEngine.approve(fd3, "m3", zhaoliu, "批准")
    fd3.refresh_from_db()
    check("并行流程通过", fd3.status == 1)

    # ==================== 场景4：会签（两人都同意才通过） ====================
    print("\n===== 场景4：会签 =====")
    flow4 = FlowInfoModel.objects.create(
        name="合同审批", key="contract_flow", status=1, frm_type=1,
        config={"name": "合同审批", "nodes": [
            make_node("s4", "开始", 1, node_to=["a4"]),
            make_node("a4", "双人会签", 4, node_from=["s4"], prop={
                "assigneeType": 1, "signType": 2, "noHeaderAction": 0,
                "assigneeList": [{"targetId": lisi.id}, {"targetId": wangwu.id}],
            }),
        ]},
    )
    fd4 = FlowEngine.start(flow4, form_data={"title": "采购合同"}, start_user=zhangsan)
    check("会签待办2人", FlowAuditUsers.objects.filter(flow_record__flow_data=fd4, status=0).count() == 2)
    FlowEngine.approve(fd4, "a4", lisi, "同意")
    check("一人同意流程仍进行中", fd4.status == 0)
    FlowEngine.approve(fd4, "a4", wangwu, "同意")
    fd4.refresh_from_db()
    check("会签全部同意后通过", fd4.status == 1)

    # ==================== 场景5：驳回 ====================
    print("\n===== 场景5：驳回 =====")
    flow5 = FlowInfoModel.objects.create(
        name="申请审批", key="apply_flow", status=1, frm_type=1,
        config={"name": "申请审批", "nodes": [
            make_node("s5", "开始", 1, node_to=["a5"]),
            make_node("a5", "主管审批", 4, node_from=["s5"], prop={
                "assigneeType": 1, "signType": 1, "assigneeList": [{"targetId": lisi.id}],
            }),
        ]},
    )
    fd5 = FlowEngine.start(flow5, form_data={"title": "测试"}, start_user=zhangsan)
    FlowEngine.reject(fd5, "a5", lisi, "材料不全")
    fd5.refresh_from_db()
    check("驳回后状态为驳回", fd5.status == 2)
    check("驳回记录完成",
          FlowRecord.objects.filter(flow_data=fd5, status=2, comment="材料不全").exists())

    # ==================== 场景6：撤回 ====================
    print("\n===== 场景6：撤回 =====")
    flow6 = FlowInfoModel.objects.create(
        name="撤回测试", key="revoke_flow", status=1, frm_type=1,
        config={"name": "撤回测试", "nodes": [
            make_node("s6", "开始", 1, node_to=["a6"]),
            make_node("a6", "主管审批", 4, node_from=["s6"], prop={
                "assigneeType": 1, "signType": 1, "assigneeList": [{"targetId": lisi.id}],
            }),
        ]},
    )
    fd6 = FlowEngine.start(flow6, form_data={"title": "撤回"}, start_user=zhangsan)
    try:
        FlowEngine.revoke(fd6, lisi)
        check("非发起人撤回被拒绝", False)
    except FlowEngineError as e:
        check("非发起人撤回被拒绝", "只有发起人可以撤回" in str(e))
    FlowEngine.revoke(fd6, zhangsan, "填错了")
    fd6.refresh_from_db()
    check("撤回后状态为撤销", fd6.status == 3)
    check("待办被标记撤销",
          FlowRecord.objects.filter(flow_data=fd6, status=3, comment="填错了").exists())

    # ==================== 场景7：未发布流程禁止发起 ====================
    print("\n===== 场景7：未发布禁止发起 =====")
    flow7 = FlowInfoModel.objects.create(name="草稿", key="draft_flow", status=0)
    try:
        FlowEngine.start(flow7, start_user=zhangsan)
        check("未发布流程禁止发起", False)
    except FlowEngineError as e:
        check("未发布流程禁止发起", "未发布" in str(e))

    print(f"\n================= 结果：{len(PASS)} 通过 / {len(FAIL)} 失败 =================")
    if FAIL:
        print("失败项:", FAIL)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
