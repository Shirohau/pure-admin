#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：base.py
@Author  ：李小涛
@Date    ：2026/7/30
@Explain : 自定义筛选基类 — 自动支持 ?field__lookup=value 动态查询参数

本模块提供两类组件：

1. Q 对象构建工具函数（模块级，无状态，可独立测试）：
   - build_q_for_condition()  将单个筛选条件转为 Q 对象
   - _build_isnull_q()        处理 isnull 的特殊逻辑（NULL + 空字符串）
   - _resolve_field_type()    按跨表路径解析终点字段类型
   - _coerce_boolean()        布尔字段文本值 → Python bool

2. CustomFilter 增强 FilterSet（类级，供业务 ViewSet 继承）：
   - filter_queryset()             核心过滤入口，协调父类过滤和动态过滤
   - _apply_dynamic_conditions()   遍历分组条件并批量应用
   - _apply_single_field_conditions() 对单个字段执行条件过滤
   - Meta                           全局默认配置（fields/overrides）

数据流向：
    HTTP Request
        │
        ▼
    CustomFilter.filter_queryset()
        ├── super().filter_queryset()   ← 处理已声明的 filter
        ├── parse_query_params()        ← 解析动态参数
        ├── _apply_dynamic_conditions()  ← 逐字段应用
        │       └── _apply_single_field_conditions()
        │               ├── build_q_for_condition()
        │               └── queryset.filter(q)
        └── queryset.distinct()         ← 关联查询去重
"""

import logging

import django_filters
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models import Q

from .constants import (
    NEGATE_PREFIX,
)
from .parser import (
    parse_query_params,
    split_in_values,
    parse_isnull_flag,
)

logger = logging.getLogger(__name__)


# ===========================================================================
# Q 对象构建工具函数（模块级，无状态，可独立测试）
# ===========================================================================


def build_q_for_condition(field_path, lookup, value, segments, model):
    """
    将单个筛选条件转换为 Django Q 对象。

    根据 lookup 类型分发到不同的构建策略：

        ┌──────────────────┬──────────────────────────────────────────┐
        │ lookup 类型       │ 处理策略                                  │
        ├──────────────────┼──────────────────────────────────────────┤
        │ in / not_in      │ 值拆分为列表，构造 field__in 查询          │
        │ not_*（否定）     │ 去掉 not_ 前缀，对剩余条件取反（~Q）      │
        │ isnull           │ 委托 _build_isnull_q 处理 NULL+空字符串   │
        │ 其他（普通）      │ 直接映射为 Q(field__lookup=value)         │
        └──────────────────┴──────────────────────────────────────────┘

    特殊处理：
        BooleanField 的值会先经 _coerce_boolean 做类型化转换，
        将前端文本（'true'/'false'/'1'/'0'/'是'/'否'）转为 Python bool，
        避免字符串被数据库隐式转为 0 导致布尔筛选失效。
        跨表路径（如 author__status）会逐段解析字段类型（见 _resolve_field_type）。

    参数：
        field_path : str
            字段路径，可能包含跨表双下划线，如 "name" 或 "author__name"。
        lookup : str
            Django ORM 查询表达式（如 "icontains"、"gte"、"in"），
            必须是 SAFE_LOOKUPS 白名单中的值。
        value : str | list | any
            前端传入的筛选值（原始字符串或已转换值）。
        segments : list[str]
            key.split('__') 的原始分段列表，用于 isnull 时获取首段字段信息。
        model : django.db.models.Model
            当前 FilterSet 绑定的模型类，用于 isnull 时判断字段类型。

    返回：
        django.db.models.Q
            构造好的 Q 对象，可直接用于 queryset.filter(q)。

    示例：
        >> build_q_for_condition('name', 'icontains', '张', ['name', 'icontains'], User)
        <Q: (AND: ('name__icontains', '张'))>
        >> build_q_for_condition('name', 'not_exact', '张三', ['name', 'not_exact'], User)
        <Q: (NOT (AND: ('name__exact', '张三')))>
    """
    # ── 解析字段类型（支持跨表路径），供布尔值类型化转换使用 ────────
    # BooleanField 的文本值若不转为 Python bool，会被数据库隐式
    # 转成 0，导致 true/false 筛选结果相同（详见 _coerce_boolean）
    field = _resolve_field_type(model, segments)

    # ── 统一值转换：in/not_in 先拆分列表，其余按原值转换 ──────────
    # not_in 的值拆分必须发生在这里，否则取反查询会拿未拆分的
    # 字符串直接构造 field__in，导致单个值被误当整个列表
    if lookup in ('in', 'not_in'):
        value = _coerce_boolean(field, split_in_values(value))
    else:
        value = _coerce_boolean(field, value)

    # ── not_* 否定查询：去掉 not_ 前缀得到真实 lookup（如
    #    not_exact → exact），再对原条件取反：~Q(field__exact=value)
    if lookup.startswith(NEGATE_PREFIX):
        real_lookup = lookup[len(NEGATE_PREFIX):]
        return ~Q(**{f'{field_path}__{real_lookup}': value})

    # ── in 查询：值已拆分为列表，构造 field__in 查询 ──────────────
    if lookup == 'in':
        return Q(**{f'{field_path}__in': value})

    # ── isnull 查询：需同时处理 NULL 和空字符串（见 _build_isnull_q） ──
    if lookup == 'isnull':
        return _build_isnull_q(field_path, value, segments, model)

    # ── 普通查询：直接映射为 Django 关键字参数 ──────────────────────
    return Q(**{f'{field_path}__{lookup}': value})


def _build_isnull_q(field_path, value, segments, model):
    """
    构建 isnull 查询的 Q 对象，同时处理 NULL 与空字符串。

    ─────────────────────────────────────────────────────────────────────
    背景：为什么需要同时处理 NULL 和空字符串？
    ─────────────────────────────────────────────────────────────────────

    用户未填写的字符串字段可能以两种形式存储：
    - NULL（数据库 NULL 值，由 blank=True, null=True 产生）
    - 空字符串 ''（表单提交空值时产生）

    前端表格中两者都表现为"空值"，因此：
    - isnull=true  需要同时匹配 NULL 和空字符串
    - isnull=false 需要同时排除 NULL 和空字符串

    ─────────────────────────────────────────────────────────────────────
    处理规则
    ─────────────────────────────────────────────────────────────────────

        ┌──────────────────┬────────────────────────────────────────┐
        │ 字段类型           │ isnull=true 行为                       │
        ├──────────────────┼────────────────────────────────────────┤
        │ CharField/TextField│ NULL OR 空字符串 ''                   │
        │ （非关系字段）      │                                        │
        ├──────────────────┼────────────────────────────────────────┤
        │ 关系字段           │ 仅 IS NULL（无空字符串歧义）           │
        ├──────────────────┼────────────────────────────────────────┤
        │ 其他类型           │ 仅 IS NULL（非字符串无空字符串概念）   │
        └──────────────────┴────────────────────────────────────────┘

    参数：
        field_path : str
            字段路径，如 "name" 或 "author__name"。
        value : str
            前端传入的值，由 parse_isnull_flag 解析为布尔值。
        segments : list[str]
            key.split('__') 的分段列表，segments[0] 为首段字段名。
        model : django.db.models.Model
            当前模型类，用于通过 _meta.get_field() 获取字段元信息。

    返回：
        django.db.models.Q
            组合后的 Q 对象。
    """
    is_null = parse_isnull_flag(value)

    # ── 首段字段元信息：判断是否为字符串字段（跨表路径仅校验首段） ──
    first_field = model._meta.get_field(segments[0])
    is_string_field = (
        not first_field.is_relation
        and isinstance(first_field, (models.CharField, models.TextField))
    )

    # ── 基础条件：IS NULL / IS NOT NULL ──────────────────────────────
    q = Q(**{f'{field_path}__isnull': is_null})

    # ── 非关系字符串字段：追加空字符串匹配 ────────────────────────────
    if is_string_field:
        if is_null:
            # isnull=true：匹配 NULL 或空字符串 ''（使用 OR）
            q |= Q(**{f'{field_path}__exact': ''})
        else:
            # isnull=false：同时排除 NULL 和空字符串（AND + 取反）
            q &= ~Q(**{f'{field_path}__exact': ''})

    return q


def _resolve_field_type(model, segments):
    """
    按字段路径分段解析终点字段类型（支持跨表路径）。

    ─────────────────────────────────────────────────────────────────────
    背景：为什么需要解析字段类型？
    ─────────────────────────────────────────────────────────────────────

    URL 参数中布尔字段的值是文本（如 ?status__in=true），构造 Q 对象
    前需要判断字段是否为 BooleanField，从而将文本转为 Python bool，
    否则字符串会被数据库隐式转为 0，导致布尔筛选失效（详见
    _coerce_boolean）。

    ─────────────────────────────────────────────────────────────────────
    跨表路径的解析方式
    ─────────────────────────────────────────────────────────────────────

    segments 可能包含跨表分段和 lookup 后缀段，例如：
        ['status', 'in']                  → 直接解析模型字段
        ['author', 'status', 'exact']     → 沿 author 外键进入关联模型，
                                             再解析 status

    遇到非字段段（lookup 后缀，如 in、exact）时解析终止，
    返回最后一个成功解析的字段对象。

    参数：
        model : django.db.models.Model
            当前 FilterSet 绑定的模型类。
        segments : list[str]
            key.split('__') 的分段列表。

    返回：
        django.db.models.Field | None
            路径终点字段对象；首段即非法或解析失败时返回 None。
    """
    current_model = model
    field = None
    for segment in segments:
        try:
            field = current_model._meta.get_field(segment)
        except FieldDoesNotExist:
            # lookup 后缀段（如 in、exact）不是字段名，终止解析
            break
        # 关系字段继续向下钻取关联模型，逐段逼近终点字段
        if field.is_relation:
            current_model = field.related_model
    return field


def _coerce_boolean(field, value):
    """
    布尔字段值转换：将前端文本布尔值转为 Python bool。

    ─────────────────────────────────────────────────────────────────────
    背景：为什么需要转换？
    ─────────────────────────────────────────────────────────────────────

    ReFilter 前端传参时布尔值以文本形式提交（?status__in=false）。
    若不转换，Q(status__in=['false']) 会把字符串原样交给数据库，
    MySQL 对数字列做字符串→数字隐式转换时 'true' 和 'false' 都会被
    转成 0，导致布尔筛选结果错误（True 记录永远筛不出来）。

    转换为 Python bool 后，Django 驱动会正确渲染为 1/0，
    筛选语义与前端展示完全一致。

    识别的文本值（不区分大小写、自动去空白）：
        True  → 'true'、'1'、'yes'、'是'
        False → 'false'、'0'、'no'、'否'

    参数：
        field : django.db.models.Field
            字段对象，仅 BooleanField 参与转换。
        value : str | list
            前端传入的原始值，或 in 查询拆分后的值列表。

    返回：
        转换后的布尔值（列表输入返回布尔列表）；
        非布尔字段或无法识别的值原样返回，交由 ORM 处理。
    """
    # 仅 BooleanField 参与转换，其余字段类型直接透传
    if not isinstance(field, models.BooleanField):
        return value

    def _to_bool(item):
        # 统一转小写并去空白后按白名单匹配
        text = str(item).strip().lower()
        if text in ('true', '1', 'yes', '是'):
            return True
        if text in ('false', '0', 'no', '否'):
            return False
        # 无法识别的值原样保留，避免误伤已有查询
        return item

    # 列表（in/not_in 查询）逐元素转换，标量（exact 等）单值转换
    if isinstance(value, (list, tuple)):
        return [_to_bool(v) for v in value]
    return _to_bool(value)


# ===========================================================================
# CustomFilter — 增强 FilterSet 基类
# ===========================================================================


class CustomFilter(django_filters.FilterSet):
    """
    增强型 FilterSet 基类，自动处理动态 __lookup 查询参数。

    ─────────────────────────────────────────────────────────────────────
    设计动机
    ─────────────────────────────────────────────────────────────────────

    django-filter 默认要求每个 lookup 变体都在 FilterSet 子类中显式声明：
        name__icontains = CharFilter(lookup_expr='icontains')
        name__exact = CharFilter(lookup_expr='exact')
        name__startswith = CharFilter(lookup_expr='startswith')
        ...

    当模型有几十个字段时，这种方式会产生大量样板代码。本基类通过自动
    解析 URL 参数中的 __lookup 后缀，实现零声明动态筛选。

    ─────────────────────────────────────────────────────────────────────
    核心能力
    ─────────────────────────────────────────────────────────────────────

    1. 动态 lookup 识别
       自动从 ?field__lookup=value 格式的 URL 参数中提取 lookup 后缀，
       无需在子类 FilterSet 中逐个声明。支持的 lookup 白名单见
       constants.SAFE_LOOKUPS。

    2. 同字段多条件 AND（范围区间）
       同一字段的多个条件按 AND 合并：?age__gte=20&age__lte=40
       表示 age ∈ [20, 40]，由前端"范围"筛选产生。

    3. 关联字段链式 JOIN（多对多 AND 查询的正确实现）
       对于关联字段（ForeignKey、ManyToManyField）的多个 AND 条件，
       使用链式 filter() 而非合并到单个 Q 对象，确保每个条件产生
       独立的 SQL JOIN，正确表达"同时关联了多个匹配对象"的语义。
       详见 _apply_single_field_conditions 的文档。

    4. 容错处理
       无法解析的参数被跳过并记录日志，不会中断整个请求处理。

    5. 自动去重
       涉及关联字段查询后自动追加 distinct()，防止 JOIN 产生重复行。

    ─────────────────────────────────────────────────────────────────────
    URL 参数格式速查
    ─────────────────────────────────────────────────────────────────────

    # ── 单条件筛选 ───────────────────────────────────────────────────
    ?name__icontains=张           → name LIKE '%张%'
    ?birth_date__gte=2024-01-01   → birth_date >= '2024-01-01'
    ?gender__in=男,女              → gender IN ('男', '女')

    # ── 父表关联查询（通过 FK/O2O 向上导航） ────────────────────────
    ?author__name__icontains=张    → author.name LIKE '%张%'

    # ── 子表关联查询（通过 related_name 反向导航） ──────────────────
    ?author_books__id__exact=159   → 关联的 books 中 id=159

    # ── 同字段多条件 AND（范围区间，前端"范围"筛选产生） ──────────
    ?age__gte=20&age__lte=40       → age >= 20 AND age <= 40

    # ── 空值筛选 ────────────────────────────────────────────────────
    ?email__isnull=true             → email IS NULL OR email = ''
    ?email__isnull=false            → email IS NOT NULL AND email != ''

    # ── 否定筛选 ────────────────────────────────────────────────────
    ?name__not_contains=test        → NOT (name LIKE '%test%')

    ─────────────────────────────────────────────────────────────────────
    前端配合说明
    ─────────────────────────────────────────────────────────────────────

    本基类专为 ReFilter 组件设计，前端提交格式：
        - 单值：fieldName__lookup=value（如 name__contains=张三）
        - 范围：fieldName__gte=start&fieldName__lte=end
        - 多选：fieldName__in=v1,v2
        - 为空：fieldName__isnull=true

    useFilter.applyFilter() 将面板结果转为上述 URL 参数后发起请求。

    ─────────────────────────────────────────────────────────────────────
    子类使用方式
    ─────────────────────────────────────────────────────────────────────

        from extends.drf.filters import CustomFilter

        class UserFilter(CustomFilter):
            '''用户模型筛选器'''
            class Meta(CustomFilter.Meta):
                model = UserModel
                # fields 默认为 "__all__"，可按需覆盖为指定字段列表
    """

    # ===================================================================
    # 公用筛选字段（所有子类自动继承，无需重复声明）
    # ===================================================================
    # 几乎所有业务模型都有 creator / updater 审计字段，在此统一声明。
    # 使用 CharFilter + 跨表路径（creator__name），支持按创建者/更新者
    # 的名称进行模糊搜索。

    creator_name = django_filters.CharFilter(
        label='创建者名称',
        field_name='creator__name',
        lookup_expr='icontains',
    )
    updater_name = django_filters.CharFilter(
        label='更新者名称',
        field_name='updater__name',
        lookup_expr='icontains',
    )

    # ===================================================================
    # filter_queryset — 核心过滤入口（唯一对外暴露的过滤方法）
    # ===================================================================

    def filter_queryset(self, queryset):
        """
        重写父类 filter_queryset，实现动态 __lookup 参数解析与多条件组合。

        处理流程（按顺序执行）：
            1. 调用 super().filter_queryset() 处理已显式声明的 filter
               （如 creator_name、updater_name）。
            2. 通过 parse_query_params 解析请求参数中未声明的 __lookup
               动态参数，按字段名分组。
            3. 调用 _apply_dynamic_conditions 遍历每个字段组，
               构造 Q 对象并应用到查询集。
            4. 如果涉及关系字段查询，追加 distinct() 防止 JOIN 产生重复行。
            5. 过程中出错的参数被跳过并记录日志，不中断请求。

        参数：
            queryset : django.db.models.query.QuerySet
                当前查询集，通常由 ViewSet 的 get_queryset() 提供。

        返回：
            django.db.models.query.QuerySet
                应用所有筛选条件（已声明 + 动态）后的查询集。
        """
        # ── 第1步：父类处理已显式声明的 filter（creator_name 等）─
        queryset = super().filter_queryset(queryset)
        model = self._meta.model

        # ── 第2步：解析 URL 中未声明的动态 __lookup 参数，按字段分组 ──
        conditions_by_field = parse_query_params(
            data=self.data,
            declared_filters=self.filters,
            model=model,
        )
        # ── 第3步：遍历字段组，逐个应用动态筛选条件 ──────────────
        queryset, requires_distinct = self._apply_dynamic_conditions(
            queryset, conditions_by_field, model
        )

        # ── 第4步：关联字段 JOIN 可能产生重复行，追加去重 ────────
        if requires_distinct:
            queryset = queryset.distinct()

        return queryset

    # ===================================================================
    # _apply_dynamic_conditions — 批量应用动态筛选条件
    # ===================================================================

    def _apply_dynamic_conditions(self, queryset, conditions_by_field, model):
        """
        遍历分组后的动态条件，逐个字段应用到查询集。

        对每个 field_path 执行：
            1. 判断是否为跨表关联字段（field_path 含 '__'）
            2. 委托 _apply_single_field_conditions 执行具体过滤
            3. 任一字段涉及关联查询时标记需要 distinct
            4. 异常捕获：单个字段出错时记录日志并继续处理后续字段

        参数：
            queryset : QuerySet
                当前查询集。
            conditions_by_field : dict
                按字段名分组后的条件，由 parse_query_params 生成。
                格式：{field_path: [(lookup, value, segments), ...]}
            model : django.db.models.Model
                当前 FilterSet 绑定的模型。

        返回：
            tuple[QuerySet, bool]
                (queryset, requires_distinct) 二元组：
                - queryset：更新后的查询集
                - requires_distinct：是否需要追加 distinct()
        """
        requires_distinct = False

        for field_path, conditions in conditions_by_field.items():
            # 字段路径中含 '__' 表示跨越了表关系（如 author__name）
            is_relation = '__' in field_path

            try:
                queryset, field_distinct = self._apply_single_field_conditions(
                    queryset, field_path, conditions, is_relation, model
                )
                requires_distinct = requires_distinct or field_distinct

                logger.debug(
                    "应用筛选: field=%s conditions=%d",
                    field_path, len(conditions),
                )

            except Exception as e:
                # 单个字段过滤失败不应中断整个请求，
                # 记录错误日志后继续处理后续字段
                logger.error(
                    "筛选参数错误 field=%s conditions=%d: %s",
                    field_path, len(conditions), e,
                )
                continue

        return queryset, requires_distinct

    # ===================================================================
    # _apply_single_field_conditions — 对单个字段应用条件组
    # ===================================================================

    def _apply_single_field_conditions(
            self, queryset, field_path, conditions, is_relation, model
    ):
        """
        对单个字段的条件组执行查询过滤。

        ─────────────────────────────────────────────────────────────────
        关键决策：关联字段的多条件 AND 必须使用链式 filter()
        ─────────────────────────────────────────────────────────────────

        为什么关联字段的 AND 不能用单 Q 合并？

        假设模型 Book 与 Author 是多对多关系，查询"作者名包含'罗贯中'
        且作者名包含'吴承恩'的图书"：

        错误做法 — 单 Q 合并（会导致空结果）：
            Q(author__name__contains='罗贯中') &
            Q(author__name__contains='吴承恩')
            → Django 生成单个 INNER JOIN，要求同一条 author 记录
              的 name 字段同时包含两个值（逻辑上不可能）
            → 结果始终为空

        正确做法 — 链式 filter()：
            queryset.filter(author__name__contains='罗贯中')
                    .filter(author__name__contains='吴承恩')
            → 每个 .filter() 产生独立的 SQL JOIN
            → 语义为"图书关联的作者中，有人叫罗贯中，有人叫吴承恩"
            → 正确返回同时关联了两位作者的图书

        其余情况（单条件、非关联字段）使用 Q 合并后一次性 filter()，
        性能更优且语义正确。

        ─────────────────────────────────────────────────────────────────
        参数
        ─────────────────────────────────────────────────────────────────

        queryset : QuerySet
            当前查询集。
        field_path : str
            字段路径（如 "name" 或 "author__name"）。
        conditions : list[tuple]
            条件列表，每个元素为 (lookup, value, segments) 三元组。
        is_relation : bool
            是否为跨表关联字段（field_path 中含 '__'）。
        model : django.db.models.Model
            当前模型类，传递给 Q 构建函数。

        返回：
            tuple[QuerySet, bool]
                (queryset, requires_distinct) 二元组：
                - queryset：更新后的查询集
                - requires_distinct：该字段是否涉及关联查询（需要去重）
        """
        requires_distinct = False

        if is_relation and len(conditions) > 1:
            # ── 关联字段多条件 AND：链式 filter，每个条件独立 JOIN ──
            # 这是处理多对多/外键关联 AND 查询的唯一正确方式
            for lookup, value, segments in conditions:
                q = build_q_for_condition(
                    field_path, lookup, value, segments, model
                )
                # 链式调用：每次 filter() 产生新的 JOIN
                queryset = queryset.filter(q)
                # 多个 JOIN 必然产生重复行，标记需要 distinct
                requires_distinct = True
        else:
            # ── 其余情况：所有条件 AND 合并为单个 Q 后一次 filter() ──
            # 适用于：单条件、非关联字段的多条件（如 gte + lte 范围）
            merged_q = Q()
            for lookup, value, segments in conditions:
                merged_q &= build_q_for_condition(
                    field_path, lookup, value, segments, model
                )
            queryset = queryset.filter(merged_q)
            # 跨表查询会引入 JOIN，可能产生重复行
            if is_relation:
                requires_distinct = True

        return queryset, requires_distinct

    # ===================================================================
    # Meta — 全局默认配置
    # ===================================================================

    class Meta:
        """
        CustomFilter 的默认元配置，所有子类自动继承。

        属性说明：
            fields = "__all__"
                自动为模型的所有字段生成默认 filter。
                子类可通过 fields = ['field1', 'field2'] 覆盖以限定筛选范围。

            filter_overrides
                覆盖特定字段类型的默认 filter 行为。

                背景：django-filter 默认不会为 ImageField、FileField、
                JSONField 等特殊类型生成 filter。通过 filter_overrides
                为这些字段强制启用文本筛选。

                具体覆盖：
                - ImageField：CharFilter + icontains，按图片路径文本模糊匹配
                - FileField：CharFilter + contains，按文件路径文本包含匹配
                - JSONField：CharFilter + contains，按 JSON 序列化文本包含匹配
        """
        fields = "__all__"
        filter_overrides = {
            # 图片字段：按路径文本包含匹配（不区分大小写）
            models.ImageField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
            # JSON 字段：按序列化文本包含匹配
            models.JSONField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'contains',
                },
            },
            # 文件字段：按路径文本包含匹配
            models.FileField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'contains',
                },
            },
        }
