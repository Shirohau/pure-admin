from django.core.management import BaseCommand

from apps.system.models.area.area_initialize import Initialize


class Command(BaseCommand):
    help = "项目初始化地区命令: python manage.py init_area"

    def handle(self, *args, **options):
        print(f"正在准备初始化省份数据...")
        initializer = Initialize()
        initializer.import_data()
        print("省份数据初始化数据完成！")
