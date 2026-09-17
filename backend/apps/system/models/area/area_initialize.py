# 城市联动
"""
到乡级 使用方法
1. https://gitee.com/modood/Administrative-divisions-of-China 下载数据，把对应的json放入对应目录
2. 修改此文件中对应json名
3. 右击执行此py文件进行初始化
"""

from pathlib import Path
from extends.drf.initialize import CustomInitialize
from .resources import AreaExportResource, AreaImportResource


class Initialize(CustomInitialize):
    # 获取当前 initialize.py 所在目录的绝对路径
    initialize_dir = Path(__file__).parent.resolve()
    export_file = initialize_dir / "init_json/export_data.json"
    import_file = initialize_dir / "init_json/import_data.json"
    export_resource_class = AreaExportResource  # 同步导出资源类实例
    import_resource_class = AreaImportResource  # 同步导入资源类实例
