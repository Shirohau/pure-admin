#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：parser.py
@Author  ：李小涛
@Date    ：2026/7/30
@Explain : URL 查询参数解析模块 — 将 HTTP 参数字符串映射为 ORM 条件对象

本模块是 URL 参数 → Django ORM 条件的核心桥梁，负责：
    1. 从 URL 参数 key 中提取字段路径和查询表达式（extract_lookup_from_key）
    2. 校验字段是否真实存在于模型上（validate_first_field）
    3. 统一解析所有查询参数，按字段分组（parse_query_params）
    4. 提供值转换工具（split_in_values、parse_isnull_flag）

数据流向：
    HTTP QueryDict
        │
        ▼
    parse_query_params()
        │  按字段分组
        ▼
    CustomFilter.filter_queryset()
        │  逐字段构造 Q 对象并应用
        ▼
    filtered QuerySet
"""

import re
import logging

from django.core.exceptions import FieldDoesNotExist

from .constants import (
    SAFE_LOOKUPS,
    VALUE_SPLIT_PATTERN,
)

logger = logging.getLogger(__name__)


def extract_lookup_from_key(key):
    """
    从 URL 参数 key 中提取字段路径（field_path）和查询表达式（lookup）。

    ─────────────────────────────────────────────────────────────────────
    解析策略：从右向左最长优先匹配
    ─────────────────────────────────────────────────────────────────────

    将 key 按双下划线拆分为 segments 后，从末尾向前逐段尝试拼接候选
    lookup，在 SAFE_LOOKUPS 白名单中匹配，匹配到的最长候选即为 lookup，
    左侧剩余部分即为 field_path。

    为什么最长优先？
        假设 key="author__name__not_contains"：
        - segments = ['author', 'name', 'not_contains']
        - 候选1（i=2）："not_contains" 在白名单中 ✓
        - 结果：field_path="author__name", lookup="not_contains"

        若从短到长匹配，可能把中间的字段段误当作 lookup（如先匹配到
        "name"），因此必须从最长候选开始尝试。

    支持格式：
        ┌──────────────────────────┬─────────────────┬────────────┐
        │ 参数 key                  │ field_path      │ lookup     │
        ├──────────────────────────┼─────────────────┼────────────┤
        │ name__icontains          │ name            │ icontains  │
        │ author__name__startswith │ author__name    │ startswith │
        │ age__gte                 │ age             │ gte        │
        └──────────────────────────┴─────────────────┴────────────┘

    参数：
        key : str
            URL 参数字符串，如 "name__icontains"。

    返回：
        tuple[str | None, str | None, list[str]]
            三元组 (field_path, lookup, segments)：
            - 解析成功时，field_path 和 lookup 均为非空字符串
            - 解析失败时，field_path=None, lookup=None
            - segments 始终为 key.split('__') 的分段列表
    """
    segments = key.split('__')

    # 从末尾向前尝试：优先匹配最长的合法 lookup
    for i in range(len(segments) - 1, 0, -1):
        candidate = '__'.join(segments[i:])
        if candidate in SAFE_LOOKUPS:
            field_path = '__'.join(segments[:i])
            return field_path, candidate, segments

    # 未匹配到任何合法 lookup — 该参数将被上层跳过
    return None, None, segments


def validate_first_field(model, segments):
    """
    校验字段路径中的首段字段名是否真实存在于模型上。

    ─────────────────────────────────────────────────────────────────────
    为什么只校验首段？
    ─────────────────────────────────────────────────────────────────────

    Django 的 model._meta.get_field() 只能解析单层字段名（如 "name"、
    "author"），不支持跨双下划线的路径（如 "author__name" 会引发
    FieldDoesNotExist）。

    对于跨表路径，我们信任 Django ORM 在查询执行时自行验证：
    - 中间字段不存在 → ORM 抛出 FieldError（被上层 try/except 捕获）
    - 本校验的作用：尽早过滤掉首段就非法的参数，减少无效查询日志

    参数：
        model : django.db.models.Model
            Django Model 类。
        segments : list[str]
            key.split('__') 的分段列表，segments[0] 即为首段字段名。

    返回：
        bool
            True  — 首段字段在模型元信息中存在，参数合法。
            False — 首段字段不存在，该参数将被上层跳过。
    """
    try:
        model._meta.get_field(segments[0])
        return True
    except FieldDoesNotExist:
        logger.warning(
            "字段校验失败：模型 %s 不存在字段 %s",
            model.__name__, segments[0]
        )
        return False


def parse_query_params(data, declared_filters, model):
    """
    统一解析 URL 查询参数，按字段名分组返回结构化条件。

    本函数是 URL 参数 → ORM 条件的核心桥梁，将扁平的 QueryDict 转换为
    CustomFilter.filter_queryset() 可直接消费的结构化数据。

    ─────────────────────────────────────────────────────────────────────
    处理流程
    ─────────────────────────────────────────────────────────────────────

        URL 参数 (QueryDict)
            │
            ▼
        for key, values in data.lists():   ← 展开重复 key 的多个值
            for value in values:
            │
            │  1. 跳过空值                       → continue
            │  2. 跳过不含 __ 的普通参数          → continue
            │  3. 跳过已由父类声明的 filter       → continue
            │  4. extract_lookup_from_key 提取   → field_path + lookup
            │  5. validate_first_field 校验字段  → 不存在则跳过
            │  6. 追加到 conditions_by_field[field_path]
            ▼
        conditions_by_field
            {field_path: [(lookup, value, segments), ...]}

    ─────────────────────────────────────────────────────────────────────
    输出格式示例
    ─────────────────────────────────────────────────────────────────────

    输入 URL：
        ?name__icontains=张&age__gte=20&age__lte=40

    conditions_by_field：
        {
            'name': [('icontains', '张', ['name', 'icontains'])],
            'age': [
                ('gte', '20', ['age', 'gte']),
                ('lte', '40', ['age', 'lte']),
            ],
        }

    参数：
        data : django.http.request.QueryDict
            请求的查询参数字典，即 FilterSet 的 self.data。
        declared_filters : dict
            FilterSet 已声明的 filter（self.filters），这些参数已由父类
            filter_queryset 处理，需要跳过。
        model : django.db.models.Model
            当前 FilterSet 绑定的模型类。

    返回：
        dict
            conditions_by_field：{field_path: [(lookup, value, segments), ...]}
            同一字段的多个条件（如 gte + lte 范围区间）按 URL 顺序收集，
            由上层按 AND 关系合并应用。
    """
    conditions_by_field = {}

    # 使用 lists() 而非 items()：QueryDict 对重复 key 只保留最后一个值，
    # 用 lists() 可展开同一 key 的多个值（如 ?name__contains=罗&name__contains=吴）；
    # 普通 dict 输入（非 QueryDict）按单值处理
    key_values = (
        data.lists()
        if hasattr(data, 'lists')
        else ((k, [v]) for k, v in data.items())
    )
    for key, values in key_values:
        for value in values:
            # ── 跳过空值：无意义的筛选参数 ──────────────────────────
            if not value:
                continue

            # ── 跳过不含 __ 的普通参数及已声明的 filter ───────────
            # 不含 __ 表示是普通参数（如 ?page=1），非 lookup 格式；
            # 已声明的 filter（如 creator_name）由父类 filter_queryset 处理
            if '__' not in key or key in declared_filters:
                continue

            # ── 提取 field_path + lookup（无法解析的参数跳过） ─────
            field_path, lookup, segments = extract_lookup_from_key(key)
            if field_path is None:
                logger.debug("跳过无法解析的参数: key=%s", key)
                continue

            # ── 校验首段字段存在性 ────────────────────────────────
            if not validate_first_field(model, segments):
                continue

            # ── 按字段名分组收集条件 ──────────────────────────────
            conditions_by_field.setdefault(field_path, []).append(
                (lookup, value, segments)
            )

            logger.debug(
                "解析条件: field_path=%s lookup=%s value=%s",
                field_path, lookup, value
            )

    return conditions_by_field


def split_in_values(raw_value):
    """
    将 in 查询的原始字符串值按分隔符拆分为列表。

    支持的三种分隔符（可混用）：
        - 逗号 ,   （中文或英文逗号）
        - 分号 ;
        - 竖线 |

    每种分隔符两侧的空白字符会被自动去除（strip）。

    参数：
        raw_value : str
            原始的逗号/分号/竖线分隔字符串，如 "男,女"。

    返回：
        list[str]
            去除空白后的值列表。

    示例：
        >> split_in_values("男,女")
        ['男', '女']
        >> split_in_values("1;2;3")
        ['1', '2', '3']
        >> split_in_values("a|b|c")
        ['a', 'b', 'c']
        >> split_in_values("x")
        ['x']
        >> split_in_values(" 苹果 , 香蕉 , 橘子 ")
        ['苹果', '香蕉', '橘子']
    """
    return [x.strip() for x in re.split(VALUE_SPLIT_PATTERN, raw_value)]


def parse_isnull_flag(value):
    """
    将 isnull 查询的参数值解析为布尔标志。

    真值（表示 IS NULL，查询空值记录）：
        - "true"  （不区分大小写：True、TRUE 均可）
        - "1"
        - "是"

    其他所有值均视为假值（表示 IS NOT NULL，查询非空记录）。
    如 "false"、"0"、"否"、"" 等均返回 False。

    参数：
        value : str
            前端传入的 isnull 参数值。

    返回：
        bool
            True  → 查询 NULL 值记录（IS NULL）
            False → 查询非 NULL 值记录（IS NOT NULL）

    示例：
        >> parse_isnull_flag("true")
        True
        >> parse_isnull_flag("1")
        True
        >> parse_isnull_flag("是")
        True
        >> parse_isnull_flag("false")
        False
        >> parse_isnull_flag("0")
        False
    """
    return str(value).lower() in ('true', '1', '是')
