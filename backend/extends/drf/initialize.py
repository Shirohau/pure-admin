#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：initialize.py
@Author  ：李小涛
@Date    ：2025/12/14 上午11:31 
@Explain : 自定义初始化：种子数据的导出/导入/复制/重置
"""

import json
from pathlib import Path

import tablib
from django.db import transaction


class CustomInitialize:
    """
    自定义数据初始化基类：通过资源类实现种子数据的导出、导入、复制与重置。

    子类需配置：
        - export_file / import_file: 导出/导入文件路径
        - export_resource_class / import_resource_class: 同步导入导出资源类
    """

    export_file = None  # 导出文件路径
    import_file = None  # 导入文件路径
    export_resource_class = None  # 同步导出资源类
    import_resource_class = None  # 同步导入资源类
    model_verbose_name = ""  # 模型中文名（用于日志输出）

    def __init__(self):
        """初始化：自动从导出资源类中提取模型中文名"""
        if self.export_resource_class:
            self.model_verbose_name = self.export_resource_class.Meta.model._meta.verbose_name

    def get_resource_class(self, prefix):
        """
        根据前缀获取对应的资源类实例

        Args:
            prefix: 资源前缀，'export' 或 'import'

        Returns:
            资源类实例（已实例化）
        """
        resource_attr_name = f"{prefix}_resource_class"
        resource_class = getattr(self, resource_attr_name, None)
        assert resource_class, f"{self.__class__.__name__} 请配置对应的 {prefix}_resource_class"
        return resource_class()

    def export_data(self):
        """导出所有数据为 JSON 文件"""
        print(f"ℹ️ 开始导出{self.model_verbose_name}数据...")
        resource = self.get_resource_class("export")
        dataset = resource.export()
        assert self.export_file, "请配置导出文件路径：export_file"
        # 确保父目录存在
        export_path = Path(self.export_file)
        export_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.export_file, "w", encoding="utf-8") as file:
            file.write(dataset.json)  # dataset.json 是格式化好的 JSON 字符串
        print(f"✅ 导出成功{self.model_verbose_name}数据： {self.export_file}")

    @transaction.atomic
    def import_data(self):
        """从 JSON 文件导入数据"""
        print(f"ℹ️ 开始导入{self.model_verbose_name}数据...")
        assert self.import_file, "请配置导入文件路径：import_file"

        # 1. 读取 JSON 文件
        if not self.import_file.exists():
            print(f"❌ 导入文件不存在: {self.import_file}")
            return

        with open(self.import_file, "r", encoding="utf-8") as file:
            json_data = json.load(file)

        # 2. 将 JSON 数据转换为 tablib Dataset（按扁平结构处理）
        resource = self.get_resource_class("import")
        dataset = tablib.Dataset()
        dataset.json = json.dumps(json_data, ensure_ascii=False)

        # 3. 执行导入
        try:
            result = resource.import_data(
                dataset,
                dry_run=False,
                raise_errors=True,  # 出错立即抛异常
            )
            print(f"✅ 导入成功 {result.total_rows} 条{self.model_verbose_name}数据！")
        except Exception as e:
            print(f"❌ 导入失败！错误详情:", str(e))

    def copy_data(self):
        """
        将 export_file 对应的导出文件内容复制到 import_file 中

        用途：导出后快速生成对应的导入文件，便于初始化流程复用。
        """
        print("🔄 开始复制数据...")
        assert self.export_file, "请配置导出文件路径：export_file"
        assert self.import_file, "请配置导入文件路径：import_file"

        export_path = Path(self.export_file)
        import_path = Path(self.import_file)

        # 确保目标目录存在
        import_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(export_path, "r", encoding="utf-8") as src:
                file_content = src.read()
            with open(import_path, "w", encoding="utf-8") as dst:
                dst.write(file_content)
            print(f"✅ 数据已成功复制到: {import_path}")
        except Exception as e:
            print(f"❌ 复制失败！错误详情: {str(e)}")

    @transaction.atomic
    def reset_data(self):
        """
        重置数据：先清空表数据，再执行 import_data 重新导入
        """
        print(f"🔄 开始重置{self.model_verbose_name}数据...")
        assert self.import_file, "请配置导入文件路径：import_file"

        # 获取导入资源类，从而拿到对应的模型
        resource = self.get_resource_class("import")
        model = resource.Meta.model

        # 删除所有数据
        deleted_count, _ = model.objects.all().delete()
        print(f"🗑️ 已删除 {deleted_count} 条{self.model_verbose_name}数据")

        # 执行导入
        self.import_data()
        print(f"✅ {self.model_verbose_name}数据重置完成！")
