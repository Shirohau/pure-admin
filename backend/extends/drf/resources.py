#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：resources.py
@Author  ：李小涛
@Date    ：2025/11/30 下午3:40 
@Explain : 自定义导入导出资源：CSV 编码兼容、中文字段名、数据权限过滤
"""

import codecs
import logging
from functools import cached_property
from types import SimpleNamespace

import tablib
from django.contrib.auth import get_user_model
from django.core.exceptions import FieldDoesNotExist
from django.http import HttpRequest
from django.utils.encoding import force_bytes
from import_export.fields import Field
from import_export.formats import base_formats
from import_export.formats.base_formats import CSV
from import_export.widgets import ManyToManyWidget, ForeignKeyWidget
from import_export_extensions.resources import CeleryModelResource
from rest_framework.filters import SearchFilter
from rest_framework.request import Request as DRFRequest

from extends.drf.permissions import DataScopeFilter

User = get_user_model()
logger = logging.getLogger(__name__)

# 错误日志数量限制（避免大数据量时日志过多）
MAX_ERROR_LOGS = 10


class CSVWithBOM(CSV):
    """
    CSV 格式导出类：自动在文件开头添加 UTF-8 BOM

    用途：Windows Excel 通过 UTF-8 编码打开 CSV 时依赖 BOM 识别编码，
    无 BOM 会导致中文乱码。
    """

    def export_data(self, dataset, **kwargs):
        """
        导出 CSV 数据并添加 UTF-8 BOM

        Args:
            dataset: tablib 数据集
            **kwargs: 透传给父类的额外参数

        Returns:
            bytes: 带 BOM 的 CSV 字节数据
        """
        # 父类可能返回 str（tablib 的 CSV 导出）或 bytes（较少见），统一转为 bytes
        data_bytes = force_bytes(super().export_data(dataset, **kwargs), encoding="utf-8")
        # 在文件开头添加 UTF-8 BOM
        return codecs.BOM_UTF8 + data_bytes

    def get_extension(self):
        """返回扩展名 "csv"，与原始 CSV 格式一致，保证 API 能正常匹配格式"""
        return "csv"


# 全局替换 base_formats 中的 CSV 格式，使所有导入导出默认携带 BOM
base_formats.CSV = CSVWithBOM


class CreatedForeignKeyWidget(ForeignKeyWidget):
    """导入 ForeignKey 外键并自动新增"""

    def clean(self, value, row=None, **kwargs):
        lookup = {self.field: value}
        obj, created = self.model.objects.get_or_create(**lookup)
        return obj


class CreatedManyToManyWidget(ManyToManyWidget):
    """导入 ManyToMany 外键并自动新增"""

    def clean(self, value, row=None, **kwargs):
        if not value:
            return self.model.objects.none()

        if isinstance(value, (float, int)):
            ids = [int(value)]
        else:
            ids = value.split(self.separator)
            ids = filter(None, [i.strip() for i in ids])
        ids = list(ids)

        created_objects = []
        for key in ids:
            lookup = {self.field: key}
            try:
                obj, created = self.model.objects.get_or_create(**lookup)
                created_objects.append(obj)
            except Exception:
                continue
        return self.model.objects.filter(pk__in=[o.pk for o in created_objects])


class CustomCeleryResource(CeleryModelResource):
    """
    自定义异步导入导出资源（基于 django-import-export-extensions）：
        - 处理 CSV 乱码问题（配合 CSVWithBOM）
        - 导出中文字段名（优先取模型 verbose_name）
        - 提供导入模板示例数据（examples_data）
        - 支持搜索过滤与数据权限过滤（is_filter）
        - 支持字段级下载权限（_permitted_attrs）
        - 保存前自动填充创建者/更新者/归属部门
    """

    creator = Field(attribute="creator", column_name="创建者")
    updater = Field(attribute="updater", column_name="更新者")
    search_fields = []  # 导出时应用的搜索字段列表
    examples_data = []  # 导入模板示例数据（每个元素为一行数据的 dict）
    import_column_widths = None  # 导入模板列宽配置：{"列名": 宽度}，仅对 xlsx 格式生效

    def __init__(self, *args, **kwargs):
        """
        初始化资源实例：从 kwargs 中弹出自定义参数

        兼容两种调用方式：
            1. 用户显式选择的导出字段（attribute 或 column_name 列表）；
            2. 字段级下载权限系统计算的允许导出字段 attribute 集合
               （None 表示不限制；未显式分配默认全部权限，已分配则仅可下载字段可导出）。

        过滤控制（隐式判断）：
            - 传入 api_path + query_params 时，自动应用搜索与数据权限过滤（异步导出场景）
            - 未传入时跳过过滤（同步导出已由视图层过滤，导入场景无需过滤）
        """
        self._selected_fields = kwargs.pop("_selected_fields", None)
        self._permitted_attrs = kwargs.pop("_permitted_attrs", None)
        self.user_id = kwargs.pop("user_id", None)
        self.dept_id = kwargs.pop("dept_id", None)
        self.api_path = kwargs.pop("api_path", None)
        self.query_params = kwargs.pop("query_params", None)
        super().__init__(*args, **kwargs)

    @cached_property
    def _request(self):
        """
        构造伪 request 对象（懒加载 + 缓存），用于在导出任务中复用搜索与数据权限过滤

        Returns:
            DRFRequest: 携带用户、路径、方法、查询参数信息的伪请求
        """
        # 用户可能已被删除，缺失时置 None（数据权限过滤会按未登录处理）
        try:
            user = User.objects.get(id=self.user_id)
        except User.DoesNotExist:
            user = None

        django_request = HttpRequest()
        django_request.method = "GET"  # 异步导出场景始终为 GET 请求
        django_request.path = self.api_path
        django_request.GET = self.query_params

        drf_request = DRFRequest(django_request)
        drf_request.user = user
        # 安全起见，清空 parser_context 避免过滤器访问时抛 KeyError
        drf_request.parser_context = {"kwargs": {}}
        return drf_request

    def get_queryset(self):
        """
        重写查询集获取：根据请求上下文决定是否应用搜索与数据权限过滤

        过滤逻辑（隐式判断）：
            - 有 api_path + query_params 时，构造伪请求并应用过滤（异步导出场景）
            - 无请求上下文时，直接返回原始 queryset（导入场景 / 同步导出场景）

        Returns:
            QuerySet: 过滤后的查询集（或原始查询集）
        """
        queryset = super().get_queryset()
        # 隐式判断：有 api_path 和 query_params 才需要过滤
        if self.api_path and self.query_params is not None:
            request = self._request
            # 1. 搜索过滤（使用定义的 search_fields）
            dummy_view = SimpleNamespace(search_fields=self.search_fields)
            queryset = SearchFilter().filter_queryset(request, queryset, dummy_view)
            # 2. 数据权限过滤
            queryset = DataScopeFilter().filter_queryset(request, queryset, None)
        return queryset

    def get_export_fields(self, selected_fields=None):
        """
        返回要导出的字段列表（先按显式选择过滤，再按字段下载权限过滤）

        过滤顺序：
            1. 用户显式选择的字段：优先按 attribute（模型字段名）匹配，
               其次按 column_name（显示名）；
            2. 字段级下载权限：无 attribute 的自定义导出列（如 creator/updater）
               默认放行，模型字段必须位于 _permitted_attrs 允许集合内。

        Args:
            selected_fields: 前端选择的字段列表（attribute 或 column_name）

        Returns:
            list[Field]: 过滤后的导出字段列表
        """
        fields = super().get_export_fields()

        # 1. 用户显式选择的字段
        if self._selected_fields:
            selected_set = set(self._selected_fields)
            fields = [
                f for f in fields
                if f.attribute in selected_set or f.column_name in selected_set
            ]

        # 2. 字段级下载权限过滤（_permitted_attrs=None 表示不限制，保持原有行为）
        if self._permitted_attrs is not None:
            fields = [
                f for f in fields
                if not f.attribute or f.attribute in self._permitted_attrs
            ]
        return fields

    def get_export_headers(self, selected_fields=None):
        """
        生成导出表头：优先使用模型字段的中文 verbose_name

        规则：
            - 字段已设置自定义 column_name（如"路径字符串"）→ 直接使用；
            - 字段为默认字段（column_name == attribute）→ 取模型 verbose_name，
              模型字段不存在时回退为 attribute 本身。

        优化：一次性构建 model_field_name → verbose_name 映射，避免逐字段调用
        _meta.get_field() 的重复属性查找。

        Args:
            selected_fields: 兼容父类签名，本实现未使用

        Returns:
            list[str]: 导出表头列表
        """
        export_fields = self.get_export_fields()
        # 批量构建模型字段名 → verbose_name 映射（仅对默认列名字段生效）
        field_name_to_verbose = {}
        for field in export_fields:
            attr = field.attribute
            if attr and field.column_name == attr:
                try:
                    model_field = self._meta.model._meta.get_field(attr)
                    field_name_to_verbose[attr] = str(getattr(model_field, "verbose_name", attr))
                except FieldDoesNotExist:
                    field_name_to_verbose[attr] = str(attr)

        headers = []
        for field in export_fields:
            attribute_name = field.attribute
            column_name = field.column_name

            # column_name 等于 attribute 说明是默认字段，从预构建映射取中文名
            if column_name == attribute_name and attribute_name:
                headers.append(field_name_to_verbose.get(attribute_name, str(attribute_name)))
            else:
                # 已设置自定义 column_name，直接使用
                headers.append(str(column_name))
        return headers

    def before_save_instance(self, instance, row, **kwargs):
        """
        保存实例前自动填充创建者、更新者与归属部门

        Args:
            instance: 待保存的模型实例
            row: 当前导入行数据
            **kwargs: 透传参数（dry_run 表示是否为试运行）
        """
        dry_run = kwargs.get("dry_run", False)
        if not dry_run:
            instance.dept_belong_id = self.dept_id
            instance.creator_id = self.user_id
            instance.updater_id = self.user_id
        super().before_save_instance(instance, row, **kwargs)

    def import_data(self, dataset, dry_run=False, raise_errors=False, **kwargs):
        """
        重写导入：保留父类逻辑，仅记录导入错误的日志

        优化说明：
            移除字段级错误收集（逐字段调用 field.clean 模拟解析），避免影响导入效率
            仅保留行级错误日志记录，便于运维排查问题

        Args:
            dataset: tablib 数据集
            dry_run: 是否为试运行（默认 False）
            raise_errors: 是否抛出错误（默认 False）
            **kwargs: 透传给父类的额外参数

        Returns:
            ImportResult: 导入结果对象
        """
        result = super().import_data(dataset, dry_run, raise_errors, **kwargs)
        # === 记录导入错误日志（django-import-export 的标准错误） ===
        if result.has_errors():
            error_count = 0
            for row_num, errors in result.row_errors():
                for error_info in errors:
                    error_count += 1
                    if error_count <= MAX_ERROR_LOGS:
                        error_msg = str(error_info.error) if hasattr(error_info, "error") else str(error_info)
                        logger.error("导入行错误 [行号=%d]: %s", row_num, error_msg)

            if error_count > MAX_ERROR_LOGS:
                logger.warning(
                    "导入行错误日志已截断，共 %d 条，仅记录前 %d 条",
                    error_count,
                    MAX_ERROR_LOGS,
                )

        return result

    @classmethod
    def get_import_template_dataset(cls):
        """
        生成用于导入模板的 Dataset（含中文表头与示例数据）

        Returns:
            tablib.Dataset: 表头为字段 column_name、行为 examples_data 的数据集
        """
        resource = cls()
        # 使用 get_import_fields() 获取导入字段，避免 _meta.fields 为 None（未声明）时无法迭代
        headers = [field.column_name for field in resource.get_import_fields()]
        data = tablib.Dataset()
        data.headers = headers
        # 将每个示例字典按表头顺序转为行数据
        for example in cls.examples_data:
            row = [example.get(header, "") for header in headers]
            data.append(row)
        return data
