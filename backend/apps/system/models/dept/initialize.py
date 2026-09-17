#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：initialize.py
@Author  ：李小涛
@Date    ：2025/12/14 上午11:31 
@Explain : 部门初始化
"""

from pathlib import Path
from extends.drf.initialize import CustomInitialize
from .resources import DeptExportResource, DeptImportResource


class Initialize(CustomInitialize):
    # 获取当前 initialize.py 所在目录的绝对路径
    initialize_dir = Path(__file__).parent.resolve()
    export_file = initialize_dir / "init_json/export_data.json"
    import_file = initialize_dir / "init_json/import_data.json"
    export_resource_class = DeptExportResource  # 同步导出资源类实例
    import_resource_class = DeptImportResource  # 同步导入资源类实例
