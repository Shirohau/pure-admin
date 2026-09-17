"""
查询所有的模型

"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "application.settings")
django.setup()

from extends.Jinja2.management.commands.fastcode import get_model_choices

if __name__ == "__main__":
    models = get_model_choices()
    for i in models:
        print(i)
