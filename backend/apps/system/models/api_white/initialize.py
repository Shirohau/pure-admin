from pathlib import Path
from extends.drf.initialize import CustomInitialize
from .resources import ApiWhiteResource


class Initialize(CustomInitialize):
    # 获取当前 initialize.py 所在目录的绝对路径
    initialize_dir = Path(__file__).parent.resolve()
    export_file = initialize_dir / "init_json/export_data.json"
    import_file = initialize_dir / "init_json/import_data.json"
    export_resource_class = ApiWhiteResource  # 导入导出资源类（同步/异步通用）
    import_resource_class = ApiWhiteResource
