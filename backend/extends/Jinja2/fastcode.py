#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：fastcode.py
@Author  ：李小涛
@Date    ：2025/12/1 下午3:09 
@Explain :
"""

from pathlib import PurePath

from jinja2 import Environment, FileSystemLoader
import os
import django
from django.apps import apps

from application import settings
from extends.drf.utils.models_utils import get_app_model_fields, model_to_api_path

# 设置 Django 配置模块
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "application.settings")  # ← 改成你的 settings 模块
# 启动 Django
django.setup()

# 获取当前文件所在目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# 模板 templates 文件夹和 fastcode.py 在同一级目录
TEMPLATES_DIR = os.path.join(CURRENT_DIR, 'templates')
# 结果 result 文件夹 放到根目录下目录
RESULT_DIR = os.path.join(settings.BASE_DIR, 'Jinja2_result')


def create_code(app_model_name):
    """
    创建 resource 文件
    @param app_model_name: Django模型类 => 输入格式应为 'app.ModelNameModel'，例如 'system.DeptModel'
    @return:
    """
    try:
        model = apps.get_model(app_model_name)  # model_class 应为 'system.DeptModel' 形式
    except LookupError:
        raise ValueError(f"模型 '{app_model_name}' 未注册，请检查是否在 INSTALLED_APPS 中或拼写是否正确。")
    model_prefix = model.__name__.removesuffix("Model")  # 模型前缀：Dept
    model_verbose_name = model._meta.verbose_name  # 模型中文名：部门
    # 获取模型字段信息
    model_fields = get_app_model_fields(app_model_name)
    api_prefix = model_to_api_path(app_model_name)  # api前缀：/api/system/dept/
    # #  使用绝对路径的Jinja2模板加载器
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    # # 引用模板文件
    template_list = [
        # 后端
        {"template": "backend/filters.j2", "output": "backend/filters.py"},
        # {"template": "backend/initialize.j2", "output": "backend/initialize.py"},
        {"template": "backend/resources.j2", "output": "backend/resources.py"},
        {"template": "backend/serializers.j2", "output": "backend/serializers.py"},
        {"template": "backend/urls.j2", "output": "backend/urls.py"},
        {"template": "backend/views.j2", "output": "backend/views.py"},
        # 前端
        {"template": "web/api.j2", "output": "web/api.ts"},
        {"template": "web/crud.j2", "output": "web/crud.tsx"},
        {"template": "web/index.j2", "output": "web/index.vue"},
    ]
    for item in template_list:
        template = env.get_template(item["template"])
        # 传给模板的参数
        output_content = template.render(
            model_prefix=model_prefix,
            model_verbose_name=model_verbose_name,
            model_fields=model_fields,
            api_prefix=api_prefix,
        )

        # 构建最终保存路径：result/{model_prefix}/{output}
        final_path = os.path.join(RESULT_DIR, model_prefix, item["output"])
        os.makedirs(os.path.dirname(final_path), exist_ok=True)  # 确保父目录存在
        # 写入到文件
        with open(final_path, "w", encoding="utf-8") as f:
            f.write(output_content)
        print(f"✅ 已生成: {PurePath(final_path).as_posix()}")


if __name__ == '__main__':
    create_code("recruitment.ScheduleModel")
