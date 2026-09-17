#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend
@File    ：dump_init.py
@Author  ：李小涛
@Date    ：2025/12/14 下午2:19
@Explain : 初始化数据
"""

import importlib

from django.apps import apps
from django.core.management import BaseCommand

from extends.Jinja2.management.commands.fastcode import get_model_choices


def get_method_full_path(method):
    """
    获取 bound method 或 unbound function 的完整路径字符串
    例如: 'apps.system.models.role.init.initialize.Initialize.import_data'
    """
    if hasattr(method, '__self__'):
        # 是 bound method（绑定方法）
        cls = method.__self__.__class__
        module = cls.__module__
        qualname = f"{cls.__qualname__}.{method.__name__}"
    else:
        # 可能是普通函数或 staticmethod
        module = method.__module__
        qualname = method.__qualname__

    return f"{module}.{qualname}"


def get_class_full_path(obj):
    """获取对象所属类的完整路径，如 'package.module.ClassName'"""
    cls = obj.__class__
    return f"{cls.__module__}.{cls.__qualname__}"


def run_initialize(app_model_name: str, action: str):
    """动态导入并运行指定 app 的 Initialize 类"""
    try:
        app_label, model_name = app_model_name.rsplit('.', 1)
        # 动态获取模型类
        model_class = apps.get_model(app_label, model_name)
        # 获取定义该类的文件路径
        model_module_full = model_class.__module__
        parts = model_module_full.split('.')
        base_module_path = '.'.join(parts[:-1])
        # 构造初始化模块路径
        init_module_path = f"{base_module_path}.initialize"
        # 动态导入模块：apps.system.models.dept.initialize
        module = importlib.import_module(init_module_path)
        # 获取 Initialize 类
        initialize_class = getattr(module, 'Initialize')
        # 实例化并运行
        initializer = initialize_class()
        method_name = f"{action}_data"
        method = getattr(initializer, method_name, None)
        if method:
            print(f"▶️ 准备执行 {get_method_full_path(method)} 方法")
            method()  # 执行方法
        else:
            print(f"❌ 执行失败 {get_class_full_path(initializer)} 中 没有 {method_name} 方法")
    except Exception as e:
        print(f"❌ 执行失败：{str(e)}")
        return False


class Command(BaseCommand):
    help = "项目初始化命令: python manage.py init system.DeptModel"

    def add_arguments(self, parser):
        choices = get_model_choices()
        parser.add_argument(
            '--app_model_name',
            choices=choices,
            type=str,
            help="可选。格式为 'app_label.ModelName'，例如 'system.DeptModel'。若不传，则初始化所有模型。",
        )
        parser.add_argument(
            '--action',  # 加 -- 表示是选项，不是位置参数
            choices=['import', 'export', 'copy', 'reset'],
            default='import',
            help="操作类型：import（默认）或 export",
        )

    def handle(self, *args, **options):
        app_model_name = options['app_model_name']
        action = options['action']
        if app_model_name:
            # 单模型模式
            run_initialize(app_model_name, action)
        else:
            # 全局模式
            self._init_all_models(action)

    @staticmethod
    def _init_all_models(action):
        """遍历白名单应用下的所有模型"""
        apps_white_list = ['system', 'example']
        for app_name in apps_white_list:
            app_config = apps.get_app_config(app_name)
            # 遍历该 app 下的所有 concrete 模型
            for model_class in app_config.get_models():
                # 跳过抽象模型和自动创建的中间模型
                if model_class._meta.abstract or model_class._meta.auto_created:
                    continue
                app_model_name = f"{app_config.label}.{model_class.__name__}"
                run_initialize(app_model_name, action)
