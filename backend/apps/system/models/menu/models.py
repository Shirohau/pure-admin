from django.db import models

from apps.system.models import table_prefix
from extends.drf.models import CustomSortModel


class MenuModel(CustomSortModel):
    parent = models.ForeignKey(
        to="MenuModel",
        related_name="children",
        verbose_name="父级菜单",
        db_comment="父级菜单",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        db_constraint=False,
    )
    title = models.CharField(verbose_name="菜单名称", db_comment="菜单名称", max_length=128)
    icon = models.CharField(verbose_name="菜单图标", db_comment="菜单图标", max_length=128, null=True, blank=True)
    extraIcon = models.CharField(verbose_name="右侧图标", db_comment="右侧图标", max_length=128, null=True, blank=True)

    path = models.CharField(verbose_name="路由地址", db_comment="路由地址", unique=True, max_length=128)
    name = models.CharField(verbose_name="路由名字", db_comment="路由名字", unique=True, max_length=255)
    component = models.CharField(verbose_name="组件地址", db_comment="组件地址", max_length=255, null=True, blank=True)

    # 以下是路由的meta
    showLink = models.BooleanField(verbose_name="侧边显示", db_comment="侧边显示", default=True)
    showParent = models.BooleanField(verbose_name="显示父级", db_comment="显示父级", default=True)
    keepAlive = models.BooleanField(verbose_name="是否缓存", db_comment="是否缓存", default=True)
    hiddenTag = models.BooleanField(verbose_name="是否禁止", db_comment="是否禁止", default=False)
    fixedTag = models.BooleanField(verbose_name="是否固定", db_comment="是否固定", default=False)

    frameSrc = models.CharField(verbose_name="内嵌链接", db_comment="内嵌链接", max_length=128, null=True, blank=True)
    frameLoading = models.BooleanField(verbose_name="内嵌动画", db_comment="内嵌动画", default=True)

    transitionName = models.CharField(verbose_name="组件动画", db_comment="组件动画", max_length=255, null=True, blank=True)
    enterTransition = models.CharField(verbose_name="组件进场动画", db_comment="组件进场动画", max_length=255, null=True, blank=True)
    leaveTransition = models.CharField(verbose_name="组件离场动画", db_comment="组件离场动画", max_length=255, null=True, blank=True)

    role = models.ManyToManyField(
        to="RoleModel",
        related_name="menu",
        blank=True,
        db_constraint=False,
        verbose_name="关联角色"
    )

    class Meta:
        db_table = table_prefix + "menu"
        verbose_name = "菜单"
        verbose_name_plural = verbose_name
        db_table_comment = verbose_name
        ordering = ("sort",)
