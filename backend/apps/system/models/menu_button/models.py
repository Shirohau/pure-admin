from django.db import models

from apps.system.models import table_prefix
from extends.drf.models import CustomSortModel


class MenuButtonModel(CustomSortModel):
    parent_name = 'menu'  # 排序时候的父级字段
    menu = models.ForeignKey(
        to="MenuModel",
        related_name="menu_button",
        db_constraint=False,
        verbose_name="关联菜单",
        db_comment="关联菜单",
        on_delete=models.CASCADE
    )
    button_type = models.CharField(max_length=20, verbose_name="按钮类型", db_comment="按钮类型")
    name = models.CharField(max_length=64, verbose_name="按钮名称", db_comment="按钮名称")
    key = models.CharField(unique=True, max_length=64, verbose_name="权限值", db_comment="权限值")
    api = models.CharField(max_length=200, blank=True, null=True, verbose_name="接口地址", db_comment="接口地址")
    method = models.CharField(max_length=10, blank=True, null=True, verbose_name="接口请求方法", db_comment="接口请求方法")
    # 是否需要数据访问权限：False 时不做数据范围设置，权限默认为全部数据
    # 如导入按钮无需按数据范围过滤，可直接关闭
    need_data_scope = models.BooleanField(
        default=True,
        verbose_name="是否需要数据权限",
        db_comment="是否需要数据权限",
    )

    class Meta:
        db_table = table_prefix + "menu_button"
        verbose_name = "菜单按钮"
        verbose_name_plural = verbose_name
        db_table_comment = verbose_name
        ordering = ("sort",)
