#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：models.py
@Author  ：李小涛
@Date    ：2025/12/11 上午9:04
@Explain : 部门
"""

import bisect
from collections import defaultdict

from django.db import models
from django.db.models import Q
from treebeard.mp_tree import MP_Node

from apps.system.models import table_prefix
from extends.drf.models import CustomModel

# treebeard 的 steplen：path 中每级节点的定长步进（默认 4，hex 字符）
# 路径拼接规则：子节点 path = 父节点 path + 4 位 hex 编码，如 '0001' → '00010001'
STEPLEN = 4


def annotate_dept_full_path(page, dept_field='dept_id', annotate_attr_name='_dept_full_path'):
    """
    为任意对象列表批量注入部门 full_path（基于 dept 的 path），避免逐行查询。

    N+1 分析：
        - 本函数恒定执行 2 次批量查询（部门基础信息 + 祖先名称），
          查询次数与 page 大小无关，不会随数据量线性膨胀。
        - 依赖 treebeard 的 path 前缀编码：任意节点的祖先 path 必然是该
          节点 path 的前缀（每级固定 STEPLEN 位），因此只需按长度截断即可
          还原出所有祖先的 path，无需逐级查询。

    :param page: 对象列表（如 User 列表），将被原地注入 full_path 属性
    :param dept_field: page 中部门 ID 的字段名，默认 'dept_id'
    :param annotate_attr_name: 注入的属性名，默认 '_dept_full_path'
    :return: page（已注入属性）；部门缺失时注入空字符串
    """
    # 提取去重后的部门 ID（去重避免重复查询，None 直接剔除）
    dept_ids = list({getattr(obj, dept_field, None) for obj in page})
    dept_ids = [did for did in dept_ids if did is not None]

    if not dept_ids:
        return page

    # 第一次批量查询：取出所有涉及部门的 path 与 name（id → 部门信息映射）
    dept_list = list(DeptModel.objects.filter(id__in=dept_ids).values('id', 'path', 'name'))
    dept_map = {d['id']: d for d in dept_list}

    # 收集所有需要的 path：部门自身 path + 每级祖先 path（按 STEPLEN 截断）
    all_needed_paths = set()
    for d in dept_list:
        path = d['path']
        all_needed_paths.add(path)
        depth = len(path) // STEPLEN
        for i in range(1, depth):
            all_needed_paths.add(path[:i * STEPLEN])

    # 第二次批量查询：一次性取出所有祖先 + 自身的名称（path → name 映射）
    path_to_name = {
        item['path']: item['name']
        for item in DeptModel.objects.filter(path__in=all_needed_paths).values('path', 'name')
    }

    # 按 path 层级顺序拼接 full_path（如 '总公司/研发部/后端组'）
    for obj in page:
        dept_id = getattr(obj, dept_field, None)
        if not dept_id or dept_id not in dept_map:
            setattr(obj, annotate_attr_name, "")
            continue

        dept_path = dept_map[dept_id]['path']
        depth = len(dept_path) // STEPLEN
        ancestor_paths = [dept_path[:i * STEPLEN] for i in range(1, depth)]
        names = [path_to_name[ap] for ap in ancestor_paths if ap in path_to_name]
        current_name = path_to_name.get(dept_path)
        names.append(current_name if current_name is not None else "[部门已删除]")

        setattr(obj, annotate_attr_name, '/'.join(names))

    return page


def annotate_dept_children_ids(page, dept_field='dept_id', annotate_attr_name='_dept_children_ids'):
    """
    为任意对象列表批量注入部门的所有后代 ID（包括自身），避免逐行查询。

    N+1 分析：
        - 本函数恒定执行 2 次批量查询（目标部门 path + 全部相关后代），
          查询次数与 page 大小无关。
        - 依赖 treebeard 的 path 前缀编码：某部门的全部后代（含自身）恰好是
          path 以该部门 path 为前缀的所有记录，可用一次 LIKE 前缀查询取回。

    :param page: 对象列表（如 User 列表），将被原地注入 children_ids 属性
    :param dept_field: page 中部门 ID 的字段名，默认 'dept_id'
    :param annotate_attr_name: 注入的属性名，默认 '_dept_children_ids'
    :return: page（已注入属性）；部门缺失时注入空列表
    """
    # 提取去重后的部门 ID
    dept_ids = list({getattr(obj, dept_field, None) for obj in page})
    dept_ids = [did for did in dept_ids if did is not None]

    if not dept_ids:
        return page

    # 第一次批量查询：目标部门的 path（id → path 映射）
    dept_id_to_path = dict(
        DeptModel.objects.filter(id__in=dept_ids).values_list('id', 'path')
    )
    if not dept_id_to_path:
        return page

    # 构建 OR 前缀查询：一次取回所有"以任一目标 path 开头"的部门（含自身与全部后代）
    q = Q()
    for p in dept_id_to_path.values():
        q |= Q(path__startswith=p)
    all_related_depts = list(DeptModel.objects.filter(q).values_list('path', 'id'))

    # 按 path 排序：treebeard 的 path 为定长 hex 字符串，前缀相同的记录排序后必然相邻
    all_related_depts.sort(key=lambda item: item[0])
    sorted_paths = [item[0] for item in all_related_depts]

    # 对每个目标 path，用二分查找定位"以其为前缀"的连续区间（O(log n) 每个目标）
    # 上界使用 '\uffff'（Unicode 最大值），保证所有以 target 开头的 path 都 < target + '\uffff'
    children_map = defaultdict(list)  # 目标部门 id -> 后代 id 列表（含自身）
    for target_id, target_path in dept_id_to_path.items():
        lo = bisect.bisect_left(sorted_paths, target_path)
        hi = bisect.bisect_left(sorted_paths, target_path + '\uffff')
        children_map[target_id] = [item[1] for item in all_related_depts[lo:hi]]

    # 注入结果
    for obj in page:
        dept_id = getattr(obj, dept_field, None)
        if dept_id and dept_id in children_map:
            setattr(obj, annotate_attr_name, children_map[dept_id])
        else:
            setattr(obj, annotate_attr_name, [])

    return page


class DeptModel(MP_Node, CustomModel):
    """
    部门模型：treebeard MP_Node 物化路径树 + 标准审计字段。

    树结构约定（treebeard MP_Node）：
        - path：定长物化路径字符串，每级节点占用 STEPLEN(4) 位 hex 字符，
          子节点 path = 父节点 path + 4 位编码，如 '0001' → '00010001'；
        - depth：节点深度，根节点为 1；
        - 同层兄弟按 path 字典序排列，上移/下移即调整兄弟间的相对位置；
        - 借助 path 前缀特性可高效实现：祖先查询（截断）、子树查询（前缀匹配）。

    负责人说明：
        - owner 外键关联用户表且不建数据库约束（db_constraint=False），
          用户被删除时置空（SET_NULL），保证部门数据不被级联删除；
        - 负责人的姓名/电话/邮箱实时取自用户表，用户修改后部门侧自动生效。
    """

    name = models.CharField(max_length=64, verbose_name="部门名称", db_comment="部门名称")
    code = models.CharField(max_length=64, unique=True, verbose_name="部门编号", db_comment="部门编号")
    status = models.BooleanField(default=True, null=True, blank=True, verbose_name="部门状态", db_comment="部门状态")
    # 负责人：外键关联用户表，用户修改电话/邮箱后部门侧实时获取最新数据
    owner = models.ForeignKey(
        to='UserModel',
        on_delete=models.SET_NULL,
        related_name='owner_departments',
        db_constraint=False,
        null=True,
        blank=True,
        verbose_name='负责人',
        db_comment='负责人（关联用户）',
        help_text='负责人（关联用户表）',
    )

    def full_path(self):
        """
        返回部门全路径，如 '总公司/研发部/后端组'。

        查询开销：内部调用 get_ancestors()，会产生 1 次祖先子树查询。
        仅适合单对象场景（如详情展示）；批量场景请使用模块级工具函数
        annotate_dept_full_path()（恒定 2 次查询）。

        Returns:
            str: 以 '/' 拼接的部门全路径
        """
        ancestors = self.get_ancestors()  # 祖先（不包括自己）
        names = [node.name for node in ancestors] + [self.name]
        return '/'.join(names)

    def children_ids(self):
        """
        返回所有后代部门的 ID 列表（包括自身），如 '[1, 2, 3]'。

        查询开销：内部调用 get_descendants()，会产生 1 次子树查询。
        仅适合单对象场景；批量场景请使用模块级工具函数
        annotate_dept_children_ids()（恒定 2 次查询）。

        Returns:
            list[int]: 自身 + 所有后代的 ID 列表；无后代时返回 [自身 id]
        """
        descendants = self.get_descendants()  # 后代（不包括自己）
        ids = [self.id] + [node.id for node in descendants]
        return ids

    def parentId(self):
        """
        返回父级部门 ID。

        查询开销：内部调用 get_parent()，会产生 1 次按 path 前缀的查询。
        根节点（depth=1）没有父级，返回 None。

        Returns:
            int | None: 父级部门 ID；根节点返回 None
        """
        parent = self.get_parent()
        return parent.id if parent else None

    class Meta:
        db_table = table_prefix + "dept"
        verbose_name = "部门"
        verbose_name_plural = verbose_name
        db_table_comment = verbose_name
