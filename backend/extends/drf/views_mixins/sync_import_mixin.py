#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：sync_import_mixin.py
@Author  ：李小涛
@Date    ：2026/8/3
@Explain : 同步导入混入（基于 django-import-export）
          独立管理导入相关逻辑：
          文件解析、同步导入、导入模板生成。
"""
import codecs
import os
from datetime import datetime

from django.db.models import Max
from django.template.defaultfilters import capfirst
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from tablib import Dataset

from apps.system.models.menu_field.models import MenuFieldModel
from apps.system.models.role_menu_field.models import RoleMenuFieldModel
from extends.drf.response import error_response, success_response

from .sync_export_mixin import SUPPORTED_EXPORT_FORMATS, file_download_response


def _get_permitted_import_field_attrs(model_class, user):
    """
    根据当前用户的字段级权限，返回"字段是否允许导入"的判定函数

    权限判定规则（与导出链路 _get_permitted_export_field_attrs 对齐）：
      1. 非模型字段（自定义导入列）→ 不受字段权限管理，默认放行；
      2. 模型字段未被 MenuFieldModel 管理 → 不受字段权限管理，默认放行；
      3. 模型字段受管理但用户角色未显式分配（无 RoleMenuFieldModel 记录）
         → 遵循"未显式分配权限，则默认拥有全部权限"，放行；
      4. 模型字段受管理且已显式分配 → permission_level 必须为 2（可读写）才允许导入，
         0（禁止访问）或 1（只读）均不可导入。

    多角色合并策略（用户可拥有多个角色，取最宽松）：
      - permission_level 取最大值（Max）。

    Args:
        model_class: 导入资源对应的 Django 模型类
        user: 当前请求用户（需含 role 关联）

    Returns:
        可调用对象 is_permitted(attr) -> bool；返回 None 表示不限制（无角色体系等）。
    """
    if not hasattr(user, "role"):
        return None  # 无角色体系，不限制

    role_ids = list(user.role.values_list("id", flat=True))
    if not role_ids:
        return None

    model_label = model_class._meta.label_lower

    # 模型自身字段名（用于区分自定义导入列与真实模型字段）
    model_field_names = set(f.name for f in model_class._meta.get_fields())

    # 查询哪些字段被 MenuFieldModel 管理（未管理的字段不受字段权限体系约束）
    managed_fields = set(
        MenuFieldModel.objects.filter(model=model_label).values_list("field_name", flat=True)
    )

    # 查询当前用户对这些受管字段的显式分配记录（多角色取最宽松：等级取 Max）
    explicit_perms = RoleMenuFieldModel.objects.filter(
        role_id__in=role_ids,
        menu_field__model=model_label
    ).values(
        "menu_field__field_name"
    ).annotate(
        max_level=Max("permission_level"),
    )

    # 字段名 → 合并后的权限等级
    field_perms = {
        item["menu_field__field_name"]: item["max_level"]
        for item in explicit_perms
    }

    def is_permitted(attr):
        """判断单个字段（attribute）是否允许导入"""
        # 自定义导入列（不在模型中）→ 不受字段权限管理，放行
        if attr not in model_field_names:
            return True

        # 模型字段：未纳入权限体系 → 放行
        if attr not in managed_fields:
            return True

        # 受管字段：未显式分配 → 默认拥有全部权限，放行
        level = field_perms.get(attr)
        if level is None:
            return True

        # 已显式分配 → 仅可读写（2）允许导入
        return level == 2

    return is_permitted


def _compute_permitted_import_field_attrs(resource_class, user):
    """
    根据当前用户的字段级权限，计算允许导入的字段 attribute 列表

    供同步导入（sync_import）与导入模板下载（import_template）共用，
    保证两条链路的字段权限规则完全一致。

    实现说明：
    - 返回 None 表示不限制（无角色体系或未分配任何角色）。

    Args:
        resource_class: 导入资源类（import_export.Resource 子类）
        user: 当前请求用户

    Returns:
        允许导入的字段 attribute 列表；None 表示不限制
    """
    is_permitted = _get_permitted_import_field_attrs(
        model_class=resource_class._meta.model,
        user=user,
    )
    if is_permitted is None:
        return None

    all_fields = resource_class().get_import_fields()
    return [
        f.attribute for f in all_fields
        if not f.attribute or is_permitted(f.attribute)
    ]


def _filter_dataset_by_import_perms(dataset, resource_class, permitted_attrs):
    """
    根据允许导入的字段 attribute 列表，过滤数据集中不可导入的列

    将数据集的列（按 header/column_name 匹配）限制在 permitted_attrs 范围内，
    返回新的 Dataset。供 sync_import 和 import_template 共用，
    确保模板与实际导入使用相同的过滤逻辑。

    Args:
        dataset: 原始 tablib Dataset
        resource_class: 导入资源类
        permitted_attrs: 允许导入的字段 attribute 列表（None 表示不限制）

    Returns:
        过滤后的 tablib Dataset
    """
    if permitted_attrs is None:
        return dataset

    permitted_set = set(permitted_attrs)
    resource_instance = resource_class()

    # 构建 column_name → 是否允许 的映射
    allowed_headers = set()
    for field_name, field in resource_instance.fields.items():
        attr = field.attribute
        # 无 attribute 的自定义列默认放行，有 attribute 的需在允许集合内
        if not attr or attr in permitted_set:
            allowed_headers.add(field.column_name)

    # 找出需要保留的列索引
    keep_indices = [
        i for i, h in enumerate(dataset.headers or [])
        if h in allowed_headers
    ]

    if not keep_indices:
        # 所有列都被过滤掉，返回空数据集
        return Dataset()

    # 构建新数据集，仅保留有权限的列
    new_headers = [dataset.headers[i] for i in keep_indices]
    new_data = Dataset()
    new_data.headers = new_headers
    for row in dataset.dict:
        new_data.append([row[dataset.headers[i]] for i in keep_indices])
    return new_data


class ImportMixin:
    """
    同步导入混入：
        - sync_import: 同步导入数据（先模拟校验，再实际导入）
        - import_template: 获取导入模板文件

    可配置属性（子类需按需配置）：
        - import_resource_class: 导入资源类（必配）
        - import_max_rows: 同步导入最大行数限制，默认 100
    """

    import_resource_class = None  # 同步导入资源类
    import_max_rows = 100  # 同步导入最大行数

    def get_resource_class(self, prefix):
        """
        根据动作前缀获取对应的资源类

        Args:
            prefix: 动作前缀，如 "export" / "import"

        Returns:
            资源类（未配置时抛出断言异常提示）
        """
        action_resource_name = f"{prefix}_resource_class"
        action_resource_class = getattr(self, action_resource_name, None)
        assert action_resource_class, f"{self.__class__.__name__} 请配置对应的 {prefix}_resource_class"
        return action_resource_class

    def _read_uploaded_content(self, file, file_format):
        """
        读取上传文件内容：
        CSV 需去除 BOM 并解码为文本，Excel 保持二进制，其他格式返回 None

        Args:
            file: 上传文件对象
            file_format: 文件格式字符串

        Returns:
            文件内容（str / bytes / None）
        """
        raw_content = file.read()
        if file_format == "csv":
            # 自动检测并去除 UTF-8 BOM
            if raw_content.startswith(codecs.BOM_UTF8):
                raw_content = raw_content[len(codecs.BOM_UTF8):]
            return raw_content.decode("utf-8")
        if file_format == "xlsx":
            return raw_content
        return None

    @extend_schema(summary="导入", extensions={"x-function": "SyncImport"})
    @action(methods=["post"], detail=False)
    def sync_import(self, request, *args, **kwargs):
        """
        同步导入数据功能

        请求参数：multipart/form-data，file 字段为上传文件（csv / xlsx）

        处理流程：
            1. 校验上传文件与格式；
            2. 解析文件为 Dataset；
            3. 行数超限时提示改用异步导入；
            4. 先模拟导入（dry_run=True）检查错误，无错误才执行实际导入。

        Args:
            request: 请求对象，FILES 需携带 file 字段

        Returns:
            - 成功：导入成功响应（含 totals 统计）
            - 失败：导入失败响应（含逐行错误信息）
        """
        file = request.FILES.get("file")
        if file is None:
            return error_response(message="未获取到上传文件，请携带 file 字段")

        # 获取文件扩展名作为格式，如 .csv → csv
        file_format = os.path.splitext(file.name)[1].lower().lstrip(".")
        format_class = SUPPORTED_EXPORT_FORMATS.get(file_format)
        if format_class is None:
            return error_response(message=f"不支持的文件格式：{file_format}，仅支持 csv / xlsx")
        # 读取内容（CSV 需去除 BOM 并解码为文本，Excel 保持二进制）
        file_content = self._read_uploaded_content(file, file_format)
        dataset = format_class().create_dataset(file_content)

        if len(dataset) > self.import_max_rows:
            return error_response(
                message=f"文件行数超过{self.import_max_rows}行，请使用后台导入",
                data={"max_rows": self.import_max_rows, "actual_rows": len(dataset)},
            )

        # 根据当前用户的字段级权限，计算允许导入的字段 attribute 集合
        resource_class = self.get_resource_class("import")
        permitted_attrs = _compute_permitted_import_field_attrs(
            resource_class=resource_class,
            user=request.user,
        )
        # 过滤掉无写权限的列（permission_level != 2 的字段列被移除）
        dataset = _filter_dataset_by_import_perms(dataset, resource_class, permitted_attrs)

        if not dataset.headers or len(dataset) == 0:
            return success_response(message="导入成功", data={"new": 0, "update": 0, "delete": 0, "skip": 0, "error": 0, "tot": 0})

        # 实例化导入资源类（传入当前用户信息，供资源类记录导入人/所属部门）
        # 无 api_path/query_params，资源类自动跳过搜索与数据权限过滤
        resource = resource_class(
            user_id=request.user.id,
            dept_id=getattr(request.user, "dept_id", None),
        )
        # dry_run=True 模拟导入校验数据；collect_failed_rows=True 收集失败行数据
        result = resource.import_data(dataset, dry_run=True, collect_failed_rows=True)
        if result.has_errors():
            # 提取逐行错误信息，返回给前端定位问题
            row_errors = []
            for row_num, errors in result.row_errors():
                row_errors.append({
                    "row": row_num,
                    "errors": [str(e.error) if hasattr(e, "error") else str(e) for e in errors],
                })
            # 提取字段级解析错误（来自 resources.py 的 import_data 增强）
            field_errors = getattr(result, "field_errors", None)
            # 构造统一的错误响应格式（与异步导入对齐）
            error_data = {
                "totals": result.totals,  # 统计信息
                "row_errors": row_errors,  # 逐行错误
                "field_errors": field_errors,  # 字段级解析错误
                "error_message": "数据校验失败，请检查错误详情",
            }
            # 错误截断信息（大数据量时仅展示部分错误）
            if getattr(result, "has_more_errors", False):
                error_data["has_more_errors"] = True
                error_data["error_rows_shown"] = result.error_rows_shown
                error_data["error_rows_total"] = result.error_rows_total
                error_data["error_message"] = (
                    f"数据校验失败，共 {result.error_rows_total} 行错误，"
                    f"仅展示前 {result.error_rows_shown} 行"
                )
            return error_response(message="导入失败", data=error_data)

        # 模拟校验通过后，执行实际导入
        result = resource.import_data(dataset, dry_run=False)
        return success_response(message="导入成功", data=result.totals)

    @extend_schema(summary="导入模板", extensions={"x-function": "ImportTemplate", "x-assign_permission": False})
    @action(methods=["GET"], detail=False, permission_classes=[IsAuthenticated])
    def import_template(self, request, *args, **kwargs):
        """
        获取导入模板文件

        请求参数：
            - file_format: 模板格式，如 csv / xlsx，默认 csv

        Args:
            request: 请求对象

        Returns:
            模板文件下载响应
        """
        file_format = request.query_params.get("file_format", "csv").lower()
        # 边界处理：白名单校验，非法格式直接返回错误提示，避免格式类为 None 时抛 TypeError
        if file_format not in SUPPORTED_EXPORT_FORMATS:
            return error_response(
                message=f"不支持的文件格式：{file_format}，仅支持 {', '.join(SUPPORTED_EXPORT_FORMATS.keys())}"
            )
        # 获取导入资源类
        resource_class = self.get_resource_class("import")
        # 直接调用类方法获取完整 Dataset（含表头与示例数据）
        dataset = resource_class.get_import_template_dataset()

        # 根据当前用户的字段级写权限过滤模板列
        # （与 sync_import 使用相同的权限过滤逻辑，确保模板与实际导入一致）
        permitted_attrs = _compute_permitted_import_field_attrs(
            resource_class=resource_class,
            user=request.user,
        )
        dataset = _filter_dataset_by_import_perms(dataset, resource_class, permitted_attrs)

        if not dataset.headers:
            return error_response(message="当前用户无任何字段的导入写权限")

        # 获取 Resource 类中定义的导入模板列宽配置
        column_widths = getattr(resource_class, "import_column_widths", None)

        # 构造模板文件名：模型名_导入模板_时间戳.格式
        model_name = capfirst(resource_class._meta.model._meta.verbose_name.replace(" ", ""))
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{model_name}_导入模板_{timestamp}.{file_format}"

        # 返回文件下载响应（传递列宽配置，xlsx 格式会自动设置列宽）
        return file_download_response(data=dataset, file_format=file_format, filename=filename, column_widths=column_widths)
