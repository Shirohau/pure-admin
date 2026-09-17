#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：models_utils.py
@Author  ：李小涛
@Date    ：2025/11/17 上午8:42 
@Explain : 模型工具：模型/字段信息查询与 API 路径转换
"""

from typing import Optional

from django.apps import apps

# App 白名单（app_label 集合）：仅查询这些应用下的模型
APP_WHITELIST = {"system", "example", "recruitment", "laying_off"}

# 字段黑名单（field_name 集合）：剔除无需前端处理的系统/审计字段
# 审计字段由前端 AuditField 统一渲染，主键 id 由 fast-crud 自动处理
FIELD_BLACKLIST = {"id", "dept_belong", "creator", "create_dt", "updater", "update_dt"}


def get_app_models(search: Optional[str] = None):
    """
    获取白名单 App 下的所有模型（可选按名称模糊搜索）

    - 白名单过滤：仅保留 APP_WHITELIST 中应用的模型；
    - 历史模型排除：忽略类名以 'Historical' 开头的模型
      （由 django-simple-history 自动生成，无业务意义）；
    - 搜索匹配：对模型的 verbose_name 与完整模型名（app.ModelName）
      做大小写不敏感的模糊匹配。

    Args:
        search: 搜索关键字（可选），为空时返回全部模型

    Returns:
        list[dict]: [{"name": 模型中文名, "model": "app.ModelName"}, ...]
    """
    search_lower = search.lower() if search else None
    model_list = []

    for model in apps.get_models():
        app_label = model._meta.app_label

        # 白名单过滤
        if APP_WHITELIST and app_label not in APP_WHITELIST:
            continue

        # 排除 django-simple-history 生成的 Historical 模型
        if model.__name__.startswith("Historical"):
            continue

        verbose_name = str(model._meta.verbose_name)
        full_model_name = f"{app_label}.{model.__name__}"

        # 搜索过滤（大小写不敏感）
        if search_lower is not None:
            if (
                search_lower not in verbose_name.lower()
                and search_lower not in full_model_name.lower()
            ):
                continue

        model_list.append({
            "name": verbose_name,
            "model": full_model_name,
        })

    return model_list


# Django 字段类型 → 前端字段类型映射表
FIELD_TYPE_MAP = {
    # 文本类
    "CharField": "text",
    "TextField": "textarea",
    "EmailField": "text",
    "URLField": "text",
    "SlugField": "text",
    "GenericIPAddressField": "text",

    # 数值类
    "IntegerField": "number",
    "BigIntegerField": "number",
    "SmallIntegerField": "number",
    "PositiveIntegerField": "number",
    "PositiveSmallIntegerField": "number",
    "FloatField": "number",
    "DecimalField": "number",

    # 日期时间类
    "DateField": "date",
    "DateTimeField": "datetime",
    "TimeField": "time",

    # 布尔类
    "BooleanField": "switch",
    "NullBooleanField": "select",

    # 文件类
    "FileField": "file",
    "ImageField": "file",

    # 其他
    "UUIDField": "text",
    "JSONField": "json",
}


def get_app_model_fields(app_model_name: str):
    """
    获取 'app.ModelNameModel' 模型的所有字段信息（供前端动态表单使用）

    - 黑名单过滤：剔除 FIELD_BLACKLIST 中的字段（审计字段/主键由前端统一处理）

    示例: 'system.DeptModel' →
        [
            {"field_name": "name", "verbose_name": "名称", "field_type": "CharField", "web_type": "text"},
        ]

    Args:
        app_model_name: 模型路径，如 "system.DeptModel"

    Returns:
        list[dict]: 字段信息列表（field_name / verbose_name / field_type / web_type）
    """
    model_cls = apps.get_model(app_model_name)
    field_list = []

    for field in model_cls._meta.fields:
        # 黑名单过滤：剔除审计字段与主键（前端 AuditField / fast-crud 已统一处理）
        if field.name in FIELD_BLACKLIST:
            continue
        field_type = field.get_internal_type()
        web_type = FIELD_TYPE_MAP.get(field_type, "text")  # 未映射的字段类型默认 text
        field_list.append({
            "field_name": field.name,
            "verbose_name": str(field.verbose_name) if field.verbose_name else field.name,
            "field_type": field_type,
            "web_type": web_type,
        })

    return field_list


def model_to_api_path(app_model_name: str) -> str:
    """
    将 'app.ModelNameModel' 转换为 API 路径 '/api/app/modelname/'

    示例: 'system.DeptModel' → '/api/system/dept/'

    Args:
        app_model_name: 模型路径，如 "system.DeptModel"

    Returns:
        str: 对应的 API 路径
    """
    app_label, model_name = app_model_name.rsplit(".", 1)

    # 移除结尾的 'Model' 后缀（不区分大小写，但通常首字母大写）
    if model_name.endswith("Model"):
        base_name = model_name[:-5]  # 去掉 'Model'
    else:
        base_name = model_name  # 未带 Model 后缀则保留原样

    # 转为小写
    return f"/api/{app_label}/{base_name.lower()}/"
