#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：models.py
@Author  ：李小涛
@Date    ：2025/11/28 下午3:28 
@Explain : 自定义抽象模型：统一审计字段与排序维护逻辑
"""

from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.db import models, transaction
from django.db.models import F, Max


class CustomModel(models.Model):
    """
    自定义标准抽象模型：统一添加审计字段（创建者/更新者/时间/归属部门）。

    所有业务模型应继承本类，以保证审计字段与数据权限过滤的一致性。
    """

    id = models.BigAutoField(verbose_name="id", db_comment="id", primary_key=True)
    dept_belong = models.ForeignKey(
        settings.DEPT_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="数据归属部门",
        db_comment="数据归属部门",
        related_name="dept_belong%(class)s_set",
        db_constraint=False,
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,  # 用户删除时置 NULL，保留历史数据
        null=True,
        blank=True,
        verbose_name="创建者",
        db_comment="创建者",
        related_name="created_%(class)s_set",
        db_constraint=False,
    )
    create_dt = models.DateTimeField(verbose_name="创建时间", db_comment="创建时间", auto_now_add=True)
    updater = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="更新者",
        db_comment="更新者",
        related_name="updated_%(class)s_set",
        db_constraint=False,
    )
    update_dt = models.DateTimeField(verbose_name="更新时间", db_comment="更新时间", auto_now=True)

    class Meta:
        abstract = True  # 抽象模型：不创建数据库表
        verbose_name = "核心模型"


class CustomSortModel(CustomModel):
    """
    带排序功能的自定义抽象模型：在 CustomModel 基础上增加 sort 排序字段，
    并提供移动、新增/更新/删除时的排序自动维护。

    约定：
        - sort 字段：显示排序值，同一作用域内从 1 递增；
        - 作用域：子类配置 parent 外键字段时为"同级记录"，
          未配置时作用域为全表；
        - 子类可通过 parent_name 属性指定父级字段名（默认 "parent"）。
    """

    parent_name = "parent"  # 指定父级字段名

    sort = models.IntegerField(verbose_name="显示排序", db_comment="显示排序", default=1)

    def _get_parent_field_name(self):
        """
        获取表示父级的字段名（约定为 'parent'，子类可用 parent_name 覆盖）

        Returns:
            str | None: 父级外键字段名；模型不存在该字段时返回 None
        """
        field_name = getattr(self, "parent_name", "parent")
        try:
            field = self._meta.get_field(field_name)
            if isinstance(field, models.ForeignKey):
                return field_name
        except FieldDoesNotExist:
            return None
        return None

    def _get_scope_queryset(self):
        """
        获取当前排序作用域内的所有记录（即"同级"记录）

        - 有 parent 字段：按 parent 分组（包括 parent=None 的顶级记录）
        - 无 parent 字段：作用域为全表

        Returns:
            QuerySet: 同级记录查询集
        """
        parent_field = self._get_parent_field_name()
        if parent_field is None:
            return self.__class__.objects.all()

        parent_value = getattr(self, parent_field)
        if parent_value is None:
            return self.__class__.objects.filter(**{f"{parent_field}__isnull": True})
        return self.__class__.objects.filter(**{parent_field: parent_value})

    def _max_sort(self):
        """
        获取当前作用域内的最大 sort 值 + 1（用于新增记录时分配排序值）

        Returns:
            int: 下一个可用排序值
        """
        max_sort = self._get_scope_queryset().aggregate(max_sort=Max("sort"))["max_sort"]
        return (max_sort or 0) + 1

    @transaction.atomic
    def move_up(self):
        """
        在当前作用域内上移一位（与上一条记录交换 sort 值）

        Returns:
            bool: True 表示移动成功；已在最顶部时返回 False
        """
        siblings = self._get_scope_queryset().exclude(id=self.id)
        prev_item = siblings.filter(sort__lt=self.sort).order_by("-sort").first()
        if not prev_item:
            return False
        # 与上一条记录交换排序值
        prev_item.sort, self.sort = self.sort, prev_item.sort
        prev_item.save(update_fields=["sort"])
        self.save(update_fields=["sort"])
        return True

    @transaction.atomic
    def move_down(self):
        """
        在当前作用域内下移一位（与下一条记录交换 sort 值）

        Returns:
            bool: True 表示移动成功；已在最底部时返回 False
        """
        siblings = self._get_scope_queryset().exclude(id=self.id)
        next_item = siblings.filter(sort__gt=self.sort).order_by("sort").first()
        if not next_item:
            return False
        # 与下一条记录交换排序值
        next_item.sort, self.sort = self.sort, next_item.sort
        next_item.save(update_fields=["sort"])
        self.save(update_fields=["sort"])
        return True

    def _handle_create_sort(self):
        """新增时自动分配排序值：当前作用域最大 sort + 1"""
        self.sort = self._max_sort()

    @transaction.atomic
    def _handle_update_sort(self):
        """
        更新时调整排序：sort 值变化时移动其他记录的排序值，保持连续性

        移动规则：
            - sort 变小（向前移）：[新值, 旧值-1] 区间的记录 sort + 1
            - sort 变大（向后移）：[旧值+1, 新值] 区间的记录 sort - 1
        """
        old_sort = self.__class__.objects.filter(pk=self.pk).values_list("sort", flat=True).first()
        # 记录不存在或排序值未变化 → 无需调整
        if old_sort is None or old_sort == self.sort:
            return

        # 限制新 sort 不超过合理上限，避免产生排序空洞：
        # 向后移动时上限取"当前作用域最大值"，但至少允许 old_sort + 1，
        # 避免当前记录已是最大值（或作用域内 sort 全部相同）时无法向后移动
        current_max = self._get_scope_queryset().aggregate(max_sort=Max("sort"))["max_sort"] or 0
        if self.sort > old_sort:
            max_allowed = max(current_max, old_sort + 1)
            if self.sort > max_allowed:
                self.sort = max_allowed
        scope_queryset = self._get_scope_queryset().exclude(pk=self.pk)
        if self.sort < old_sort:
            # 向前移动：[新值, 旧值-1] 区间的记录 +1
            scope_queryset.filter(sort__gte=self.sort, sort__lt=old_sort).update(sort=F("sort") + 1)
        elif self.sort > old_sort:
            # 向后移动：[旧值+1, 新值] 区间的记录 -1
            scope_queryset.filter(sort__gt=old_sort, sort__lte=self.sort).update(sort=F("sort") - 1)

    def save(self, *args, **kwargs):
        """
        重写 save：保存前自动维护排序值

        - 新增：分配当前作用域最大 sort + 1
        - 更新：sort 变化时移动其他记录保持连续

        批量导入排序等场景需要完全遵循外部传入的排序值
        （不截断、不移动其他记录、不自动分配），
        可通过 skip_sort_auto=True 跳过自动维护。
        """
        if not kwargs.get("skip_sort_auto"):
            if self._state.adding:
                self._handle_create_sort()
            else:
                self._handle_update_sort()

        # 最终统一保存（避免多次 save）
        super().save(*args, **kwargs)

    @transaction.atomic
    def delete(self, *args, **kwargs):
        """
        重写 delete：删除后调整后续记录排序，保持连续性

        删除记录后，同一作用域内所有 sort 大于被删记录的记录 sort - 1。
        """
        old_sort = self.sort
        # 先执行父类 delete（从数据库删除）
        result = super().delete(*args, **kwargs)

        # 再调整同一作用域内排序值更大的记录
        parent_field = self._get_parent_field_name()
        if parent_field:
            parent_value = getattr(self, parent_field)
            # 确定父级过滤条件：顶级记录（parent 为空）用 IS NULL
            scope_filter = (
                {parent_field: parent_value}
                if parent_value is not None
                else {f"{parent_field}__isnull": True}
            )
            self.__class__.objects.filter(sort__gt=old_sort, **scope_filter).update(sort=F("sort") - 1)
        else:
            # 全局模式：直接调整全表中排序值更大的记录
            self.__class__.objects.filter(sort__gt=old_sort).update(sort=F("sort") - 1)

        return result

    class Meta:
        abstract = True  # 抽象模型：不创建数据库表
        verbose_name = "带有排序的核心模型"
