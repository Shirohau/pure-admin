#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
部门视图集：
    - DeptViewSet         部门增删改查 + 树移动 + 同步导入导出
    - DeptExportJobViewSet 异步导出任务
    - DeptImportJobViewSet 异步导入任务

N+1 查询优化说明：
    1. owner 外键（含负责人姓名/电话/邮箱/所属部门）：
       select_related 一次性 JOIN 用户表与其所属部门表，
       列表场景从「1 + N×2」次查询降为固定 1 次查询；
    2. 详情场景 descendant_count / children_ids：
       retrieve 只执行 1 次子树查询（get_descendants），结果同时缓存
       到 _descendant_ids，供序列化器的两个字段共用，避免 2 次子树查询；
    3. parent_path 为 path 字符串截断（纯内存运算），无额外查询。
"""

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action

from extends.drf.response import success_response, error_response
from extends.drf.views_mixins import *

from .filters import DeptFilter
from .models import DeptModel
from .resources import DeptExportResource, DeptImportResource
from .serializers import DeptRetrieveSerializer, DeptSerializer, DeptCreateSerializer, DeptUpdateSerializer


@extend_schema(tags=["部门"])
class DeptViewSet(CrudViewSet, ExportMixin, ImportMixin):
    queryset = DeptModel.objects.all()
    serializer_class = DeptSerializer
    retrieve_serializer_class = DeptRetrieveSerializer
    create_serializer_class = DeptCreateSerializer
    update_serializer_class = DeptUpdateSerializer
    filterset_class = DeptFilter
    export_resource_class = DeptExportResource
    import_resource_class = DeptImportResource
    # 预加载关联外键，避免 N+1：
    #   - owner / owner__dept：负责人信息（含负责人所属部门名），供 DeptOwnerSerializer 使用
    #   - creator / updater / dept_belong：审计字段展示名，基类默认配置
    select_related = ["creator", "updater", "dept_belong", "owner", "owner__dept"]

    def retrieve(self, request, *args, **kwargs):
        """
        查询部门详情（树节点点击场景）。

        查询优化：先通过 get_object()（已含 select_related）获取部门，
        再执行 1 次子树查询（get_descendants）一次性取回全部后代 ID，
        缓存在实例 _descendant_ids 上。序列化器中的 descendant_count 与
        children_ids 均读取该缓存，将原来的 2 次子树查询合并为 1 次。

        Returns:
            统一成功响应（含详情数据：树统计信息 + 负责人信息）
        """
        instance = self.get_object()
        # 一次性取回全部后代 ID（不含自身）；无后代时为空列表
        instance._descendant_ids = list(
            instance.get_descendants().values_list("id", flat=True)
        )
        serializer = self.get_serializer(instance)
        return success_response(message="查询详情成功", data=serializer.data)

    @extend_schema(summary="新增", extensions={'x-function': 'Create'})
    def create(self, request, *args, **kwargs):
        """
        创建部门：
        - 前端必传 parentId
          - 如果 parentId is None → 创建为根节点
          - 否则 → 作为 parentId 部门的子节点（挂在其下最后一个子节点位置）

        Returns:
            创建成功响应（含新增后的部门详情）
        """
        data = request.data.copy()
        parentId = data.pop('parentId', None)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data.copy()

        if parentId is None:
            # 创建根节点（depth=1，path 为 4 位 hex 编码）
            instance = DeptModel.add_root(**validated_data)
        else:
            try:
                parent = DeptModel.objects.get(id=parentId)
            except DeptModel.DoesNotExist:
                return error_response(message="父部门不存在")
            # 在父节点下创建子节点（treebeard 自动拼接 path 并重排兄弟位置）
            instance = parent.add_child(**validated_data)
        serializer = DeptRetrieveSerializer(instance)
        return success_response(message="创建成功", data=serializer.data)

    @extend_schema(summary="修改", extensions={'x-function': 'Update'})
    def update(self, request, *args, **kwargs):
        """
        修改部门：
        - 前端必传 parentId
            - 如果 parentId is None → 修改为根节点（提升为最后一个根节点的右兄弟）
            - 如果 parentId == 当前父级 ID → 不移动，仅更新普通字段
            - 如果 parentId <> 当前父级 ID → 移动到新父节点的最后一个子节点位置

        循环引用防护：
            - parentId == 自身 id → 拒绝（不能设为自己的子部门）
            - 新父节点 path 以自身 path 为前缀 → 拒绝（不能移入自身或其子树），
              利用 treebeard path 前缀编码特性 O(1) 判断，无需遍历子树

        Returns:
            修改成功响应（含修改后的部门详情）
        """
        instance = self.get_object()
        parentId = request.data.pop('parentId', None)

        # 1. 先保存普通字段（partial=True 支持只传部分字段）
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # 2. 获取当前父级 ID（get_parent 按 path 前缀查询，1 次查询）
        current_parent = instance.get_parent()
        current_parent_id = current_parent.id if current_parent else None

        # 3. 处理移动逻辑
        if parentId is None:
            # 目标：设为根节点
            if current_parent_id is not None:  # 当前不是根，才需要移动
                # 提升为根节点：移动到最后一个根节点的右侧（保持兄弟顺序稳定）
                root_nodes = DeptModel.get_root_nodes()
                instance.move(root_nodes.last(), 'right')
                instance.refresh_from_db()  # 刷新 path/depth 等物化路径字段

        elif parentId != current_parent_id:
            # 父级变了，执行移动逻辑
            if parentId == instance.id:
                return error_response(message="不能将部门设为自己的子部门")

            try:
                new_parent = DeptModel.objects.get(id=parentId)
            except DeptModel.DoesNotExist:
                return error_response(message="目标父部门不存在")

            # 防止循环引用：目标父节点是自身或自身后代（path 前缀判定）
            if new_parent.path.startswith(instance.path):
                return error_response(message="不能将部门移动到其自身或其子部门下")

            # 移动为新父节点的最后一个子节点
            instance.move(new_parent, 'last-child')
            instance.refresh_from_db()  # 刷新 path/depth 等物化路径字段

        serializer = DeptRetrieveSerializer(instance)
        return success_response(message="修改成功", data=serializer.data)

    @extend_schema(summary="移动", extensions={'x-function': 'Move'})
    @action(methods=['GET'], detail=True)
    def move(self, request, *args, **kwargs):
        """
        移动部门（同级上移/下移）：
        - 前端必传 direction
            - 'up' 表示上移（与前一兄弟交换位置）
            - 'down' 表示下移（与后一兄弟交换位置）
        - 边界情况：已在最顶部上移 / 已在最底部下移时返回错误提示

        Returns:
            移动成功响应；已在边界时返回错误响应
        """
        direction = request.query_params.get('direction')
        instance = self.get_object()
        if direction == 'up':
            previous_sibling = instance.get_prev_sibling()
            if previous_sibling is None:
                return error_response(message="已经是第一个部门")
            else:
                instance.move(previous_sibling, 'left')
        elif direction == 'down':
            next_sibling = instance.get_next_sibling()
            if next_sibling is None:
                return error_response(message="已经是最后一个部门")
            else:
                instance.move(next_sibling, 'right')
        instance.refresh_from_db()
        return success_response(message="移动成功")


@extend_schema(tags=["部门"])
class DeptExportJobViewSet(CustomExportJobViewSet):
    """部门异步导出任务视图集（Celery 后台执行，导出资源类见 resources.py）。"""

    resource_class = DeptExportResource


@extend_schema(tags=["部门"])
class DeptImportJobViewSet(CustomImportJobViewSet):
    """部门异步导入任务视图集（Celery 后台执行，导入资源类见 resources.py）。"""

    resource_class = DeptImportResource
