from django.apps import apps
from django.core.management import BaseCommand

from extends.Jinja2.fastcode import create_code


def get_model_choices():
    """
    获取所有模型的 'app_label.ModelName' 字符串列表，作为 choices。
    """
    choices = []
    for app_config in apps.get_app_configs():
        for model in app_config.get_models():
            model_name = model.__name__
            choice_str = f"{app_config.label}.{model_name}"
            choices.append(choice_str)
    return sorted(choices)


class Command(BaseCommand):
    help = "快速创建前后端代码"

    def add_arguments(self, parser):
        choices = get_model_choices()
        parser.add_argument(
            '--app_model_name',
            choices=choices,
            help="输入model名称,快速生成相关代码，输入格式应为 'app.ModelNameModel'，例如 'system.DeptModel'",
        )

    def handle(self, *args, **options):
        app_model_name = options['app_model_name']
        create_code(app_model_name)
