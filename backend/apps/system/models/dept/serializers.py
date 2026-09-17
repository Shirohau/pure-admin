#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
部门序列化器：
    - DeptOwnerSerializer   负责人（关联用户）只读序列化器
    - DeptRetrieveSerializer 详情序列化器（树节点点击场景）
    - DeptSerializer        列表序列化器（树 / 表格列表场景）
    - DeptCreateSerializer  新增序列化器
    - DeptUpdateSerializer  修改序列化器

查询优化约定：
    - owner 关联用户，且负责人序列化器含 dept_name（用户所属部门），
      使用方必须配置 select_related('owner', 'owner__dept')，否则每个部门
      会产生 2 条额外查询（用户 + 用户所属部门），形成 N+1；
    - descendant_count / children_ids 依赖子树查询，由视图在 retrieve 时
      一次性预计算并缓存到实例属性 _descendant_ids 上，序列化器优先读取
      缓存（无缓存时回退为逐次查询，保证序列化器可独立复用）。
"""

from rest_framework import serializers

from extends.drf.serializers import CustomSerializer
from ..user.models import UserModel
from .models import DeptModel, STEPLEN


class DeptOwnerSerializer(serializers.ModelSerializer):
    """
    部门负责人（关联用户）只读信息：姓名/电话/邮箱实时取自用户表。

    字段说明：
        - dept_name：负责人的所属部门名称（source="dept.name"）。
          ⚠️ 使用本字段时查询集必须 select_related('owner__dept')，
          否则每个部门负责人都会额外触发 1 次用户所属部门查询（N+1）。

    边界情况：
        - 部门未设置负责人（owner=None）→ 序列化为 None；
        - 负责人已被删除（SET_NULL）→ 同样为 None。
    """

    dept_name = serializers.CharField(source="dept.name", read_only=True, label="用户所属部门")

    class Meta:
        model = UserModel
        fields = ['id', 'username', 'name', 'mobile', 'email', 'dept_name']


class DeptRetrieveSerializer(CustomSerializer):
    """详情序列化器：在列表序列化器基础上附加树统计信息（仅树节点点击场景使用）。"""

    parentId = serializers.IntegerField(label="上级部门ID")

    descendant_count = serializers.SerializerMethodField(label="下级组织数")

    def get_descendant_count(self, instance) -> int:
        """
        下级组织数（后代部门数量，不含自身）。

        优先读取视图预计算并缓存在实例上的 _descendant_ids（由 retrieve
        一次性子树查询得到），避免重复执行 COUNT 查询；无缓存时回退到
        treebeard 自带的 get_descendant_count()（1 次 COUNT 查询）。
        """
        cached = getattr(instance, "_descendant_ids", None)
        if cached is not None:
            # 缓存含全部后代（不含自身），数量即 len(cached)；无后代时为 0
            return len(cached)
        return instance.get_descendant_count()

    children_ids = serializers.SerializerMethodField(label="下级组织ID列表")

    def get_children_ids(self, instance) -> list:
        """
        下级组织 ID 列表（含自身，如 '[1, 2, 3]'）。

        优先读取视图预计算的 _descendant_ids 缓存（与 descendant_count 共用
        同一次子树查询）；无缓存时回退到模型方法 children_ids()。
        """
        cached = getattr(instance, "_descendant_ids", None)
        if cached is not None:
            # 结果 = 自身 id + 全部后代 id（缓存中已是后代 id 列表）
            return [instance.id] + list(cached)
        return instance.children_ids()

    owner = DeptOwnerSerializer(read_only=True, label="负责人")

    class Meta:
        model = DeptModel
        fields = '__all__'


class DeptSerializer(CustomSerializer):
    """列表序列化器：树接口（不分页）与表格列表场景通用。"""

    parent_path = serializers.SerializerMethodField(label="上级部门路径")

    def get_parent_path(self, instance) -> str:
        """
        上级部门路径（供前端 XEUtils.toArrayTree 组装树结构）。

        实现原理：treebeard 的 path 为定长物化路径，父级 path 恰好是当前
        path 去掉末尾 STEPLEN(4) 位后的前缀字符串（根节点为 ''）。
        纯字符串运算，无任何额外数据库查询，列表场景零开销。
        """
        return instance.path[:-STEPLEN]

    owner = DeptOwnerSerializer(read_only=True, label="负责人")

    class Meta:
        model = DeptModel
        fields = '__all__'


class DeptCreateSerializer(CustomSerializer):
    """新增部门序列化器：仅接收可写入的业务字段（父级由视图通过 parentId 处理）。"""

    class Meta:
        model = DeptModel
        fields = ['id', 'name', 'code', 'status', 'owner']


class DeptUpdateSerializer(CustomSerializer):
    """修改部门序列化器：可写入字段与新增保持一致。"""

    class Meta:
        model = DeptModel
        fields = ['id', 'name', 'code', 'status', 'owner']
