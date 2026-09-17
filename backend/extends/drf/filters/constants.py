#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：constants.py
@Author  ：李小涛
@Date    ：2026/7/30
@Explain : 查询表达式白名单及分类常量

本模块定义：
    - SAFE_LOOKUPS：允许前端使用的所有 Django ORM 查询表达式白名单
    - NEGATE_PREFIX：否定查询的前缀标识
    - VALUE_SPLIT_PATTERN：in 查询值分隔符正则

安全原则：
    仅开放只读查询表达式，不包含任何写操作或危险查找类型
    （如 regex、search 等）。如需扩展，请评估安全性后再添加。
"""

# ===========================================================================
# SAFE_LOOKUPS — Django ORM 查询表达式白名单
# ===========================================================================
#
# 用途：
#   用于 filter_queryset() 中验证前端传入的 __lookup 后缀是否合法，
#   防止攻击者通过构造 ?field__custom_lookup=value 注入非预期查询。
#
# 安全原则：
#   仅开放只读查询表达式，不包含任何写操作或危险操作（如 regex、search）。
#   如需扩展，请评估新 lookup 的安全性后再添加。
#
# 分类说明：
#   - 精确匹配：exact / iexact
#   - 模糊匹配：contains / icontains / startswith / istartswith / endswith / iendswith
#   - 范围比较：gt / gte / lt / lte
#   - 集合运算：in
#   - 空值判断：isnull
#   - 日期提取：year / month / day
#   - 否定运算：not_exact / not_contains / not_in
# ===========================================================================
SAFE_LOOKUPS = {
    # ── 精确匹配 ────────────────────────────────────────────────────────────
    'exact',      # 精确等于（默认 lookup，可省略 __exact，直接用字段名）
    'iexact',     # 不区分大小写的精确等于

    # ── 模糊匹配 ────────────────────────────────────────────────────────────
    'contains',   # 包含子串（区分大小写，MySQL 默认不区分，SQLite/PostgreSQL 区分）
    'icontains',  # 包含子串（不区分大小写）
    'startswith', # 以某字符串开头（区分大小写）
    'istartswith',# 以某字符串开头（不区分大小写）
    'endswith',   # 以某字符串结尾（区分大小写）
    'iendswith',  # 以某字符串结尾（不区分大小写）

    # ── 范围比较 ────────────────────────────────────────────────────────────
    'gt',         # 大于（greater than）
    'gte',        # 大于等于（greater than or equal）
    'lt',         # 小于（less than）
    'lte',        # 小于等于（less than or equal）

    # ── 集合运算 ────────────────────────────────────────────────────────────
    'in',         # 值在给定列表中（值用逗号/分号/竖线分隔）

    # ── 空值判断 ────────────────────────────────────────────────────────────
    'isnull',     # 是否为 NULL（true/1/是 表示 IS NULL，否则 IS NOT NULL）

    # ── 日期提取 ────────────────────────────────────────────────────────────
    'year',       # 按年份筛选
    'month',      # 按月份筛选（1-12）
    'day',        # 按日期筛选（1-31）

    # ── 否定运算 ────────────────────────────────────────────────────────────
    'not_exact',      # 精确不等于（等价于 ~Q(field__exact=value)）
    'not_contains',   # 不包含子串（区分大小写，等价于 ~Q(field__contains=value)）
    'not_in',         # 值不在给定列表中（等价于 ~Q(field__in=[...]))
}
# 否定前缀
# 前端传入 not_exact 时，后端自动去除 not_ 前缀，
# 对剩余部分构造取反查询：~Q(field__exact=value)
NEGATE_PREFIX = 'not_'

# 值分隔符正则（用于 in 查询的值拆分）
# 支持逗号、分号、竖线作为分隔符，允许分隔符两侧有空白
VALUE_SPLIT_PATTERN = r'[,;|]+'
