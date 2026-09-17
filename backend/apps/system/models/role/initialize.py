#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：initialize.py
@Author  ：李小涛
@Date    ：2025/12/14 上午11:31 
@Explain : 角色初始化
"""

from pathlib import Path

from extends.drf.initialize import CustomInitialize
from .resources import RoleExportResource, RoleImportResource


class Initialize(CustomInitialize):
    # 获取当前 initialize.py 所在目录的绝对路径
    initialize_dir = Path(__file__).parent.resolve()
    export_file = initialize_dir / "init_json/export_data.json"
    import_file = initialize_dir / "init_json/import_data.json"
    export_resource_class = RoleExportResource  # 同步导出资源类实例
    import_resource_class = RoleImportResource  # 同步导入资源类实例
