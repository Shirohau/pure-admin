#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：serializers.py
@Author  ：李小涛
@Date    ：2025/11/26 下午3:16 
@Explain : 自定义序列化器：统一审计字段写入与字段级权限过滤
"""

from django_restql.mixins import DynamicFieldsMixin
from rest_framework import serializers

from apps.system.models.role_menu_field.models import RoleMenuFieldModel

# 禁止访问的字段权限等级（permission_level=0 表示该字段对当前角色不可见）
PERMISSION_LEVEL_FORBIDDEN = 0


class CustomSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    """
    自定义模型序列化器基类：
        - 创建/更新时自动填充 creator / updater / dept_belong 审计字段
        - 序列化输出时按字段级权限过滤禁止访问的字段（可跳过）
        - 提供只读关联展示字段：creator_name / updater_name / dept_belong_name

    N+1 查询优化：
        - 类级缓存 _forbidden_fields_class_cache：{(user_id, model_name): set[str]}
          同一请求内，同一用户对同一模型的禁止字段集合只查询一次；
          列表序列化时子序列化器实例共享缓存，查询次数从 O(N) 降为 O(1)；
        - select_related("menu_field")：避免 values_list 通过 FK 访问 MenuFieldModel
          时产生额外查询；
        - creator_name / updater_name / dept_belong_name 的 FK 关联：
          由 CrudViewSet.get_queryset() 中的 select_related 统一预加载。
    """

    # 跳过字段权限过滤：子类可置 True 以禁用字段级权限控制
    skip_field_permissions = False

    # 字段权限类级缓存：{(user_id, model_name): set[str]}，所有子类共享
    _forbidden_fields_class_cache = {}

    # 只读展示字段：显示用户名或真实姓名（不参与写入）
    creator_name = serializers.CharField(read_only=True, source="creator.name", label="创建者")
    updater_name = serializers.CharField(read_only=True, source="updater.name", label="更新者")
    dept_belong_name = serializers.CharField(read_only=True, source="dept_belong.name", label="数据归属部门")

    def create(self, validated_data):
        """
        创建数据：智能填充审计字段（创建者、更新者、数据归属部门）

        字段填充策略：
            - 优先使用前端传递的值（允许前端指定 creator/updater/dept_belong）
            - 前端未传递时，使用当前登录用户的信息作为默认值
            - 支持两种字段格式：对象字段（creator）和ID字段（creator_id）

        使用场景：
            - 常规创建：前端不传审计字段，自动使用当前用户信息
            - 代录场景：前端传入指定的 creator/dept_belong，实现数据代录功能
            - 数据导入：批量导入时保留原始数据的创建者和部门信息

        Args:
            validated_data: 序列化器校验通过的数据，可能包含：
                - creator/creator_id: 创建者（用户对象或用户ID）
                - updater/updater_id: 更新者（用户对象或用户ID）
                - dept_belong/dept_belong_id: 数据归属部门（部门对象或部门ID）

        Returns:
            创建后的模型实例
        """
        user = self._get_user()
        if user:
            # 创建者字段：优先使用前端传递值，未传递则使用当前用户
            # 同时检查 creator（对象）和 creator_id（ID）两种格式
            if validated_data.get("creator") is None and validated_data.get("creator_id") is None:
                validated_data["creator"] = user

            # 更新者字段：优先使用前端传递值，未传递则使用当前用户
            # 同时检查 updater（对象）和 updater_id（ID）两种格式
            if validated_data.get("updater") is None and validated_data.get("updater_id") is None:
                validated_data["updater"] = user

            # 数据归属部门：优先使用前端传递值，未传递则使用当前用户的部门
            # 同时检查 dept_belong（对象）和 dept_belong_id（ID）两种格式
            if validated_data.get("dept_belong") is None and validated_data.get("dept_belong_id") is None:
                validated_data["dept_belong_id"] = user.dept_id

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        更新数据：智能填充更新者字段

        字段填充策略：
            - 优先使用前端传递的值（允许前端指定 updater）
            - 前端未传递时，使用当前登录用户作为默认值
            - 支持两种字段格式：对象字段（updater）和ID字段（updater_id）

        使用场景：
            - 常规更新：前端不传 updater 字段，自动使用当前用户
            - 代录场景：前端传入指定的 updater，实现数据代录功能
            - 数据导入：批量更新时保留原始数据的更新者信息

        Args:
            instance: 待更新的模型实例
            validated_data: 序列化器校验通过的数据，可能包含：
                - updater/updater_id: 更新者（用户对象或用户ID）

        Returns:
            更新后的模型实例
        """
        user = self._get_user()
        if user:
            # 更新者字段：优先使用前端传递值，未传递则使用当前用户
            # 同时检查 updater（对象）和 updater_id（ID）两种格式
            if "updater" not in validated_data and "updater_id" not in validated_data:
                validated_data["updater"] = user

        return super().update(instance, validated_data)

    def _get_user(self):
        """
        从序列化上下文获取当前登录用户

        安全判断：request 存在 → 包含 user 属性 → 已认证，三者缺一不可，
        确保审计字段的写入只针对已认证用户。

        Returns:
            User | None: 当前登录用户；无 request 或未认证时返回 None
        """
        request = self.context.get("request")
        if request and hasattr(request, "user") and request.user.is_authenticated:
            return request.user
        return None

    def _get_forbidden_fields(self, user):
        """
        查询当前用户对该模型无权访问的字段集合（类级缓存，避免 N+1 查询）

        优化说明：
            - 类级缓存（key = user_id + model_name）：同一请求内，同一用户对同一模型
              的禁止字段集合只查询一次，列表序列化时为每个对象创建的子序列化器实例
              共享同一份缓存结果，查询次数从 O(N) 降为 O(1)；
            - select_related("menu_field")：避免 values_list 通过 FK 访问 MenuFieldModel
              时额外产生 JOIN 查询。

        Args:
            user: 当前登录用户

        Returns:
            set[str]: 禁止访问的字段名集合
        """
        model_name = self.Meta.model._meta.label_lower
        cache_key = (user.pk, model_name)
        if cache_key not in self._forbidden_fields_class_cache:
            self._forbidden_fields_class_cache[cache_key] = set(
                RoleMenuFieldModel.objects
                .select_related("menu_field")
                .filter(
                    role__in=user.role.all(),
                    menu_field__model=model_name,
                    permission_level=PERMISSION_LEVEL_FORBIDDEN,
                )
                .values_list("menu_field__field_name", flat=True)
            )
        return self._forbidden_fields_class_cache[cache_key]

    @property
    def fields(self):
        """
        动态字段集合：在序列化输出阶段按字段级权限过滤禁止字段

        过滤时机说明：
            - is_ready_to_use_dynamic_fields 为 False（反序列化/校验阶段）→ 不过滤；
            - 子类 skip_field_permissions = True → 跳过过滤；
            - 未登录用户 → 直接返回空字典（无任何字段可见）。
        """
        all_fields = super().fields

        # 仅在序列化输出（to_representation）时执行字段权限过滤，反序列化校验时不执行
        if not self.is_ready_to_use_dynamic_fields:
            return all_fields

        # 子类可通过 skip_field_permissions = True 跳过字段权限过滤
        if getattr(self, "skip_field_permissions", False):
            return all_fields

        user = self._get_user()
        if user is None:
            return {}

        forbidden = self._get_forbidden_fields(user)
        if not forbidden:
            return all_fields
        return {k: v for k, v in all_fields.items() if k not in forbidden}

    @property
    def errors(self):
        """
        重写父类的 errors 属性，将验证错误信息中的字段名（英文/数据库字段）
        替换为对应的 verbose_name（中文/可读名称），以便前端或用户看到更友好的提示。

        Returns:
            dict: 键为字段可读名称（verbose_name），值为对应错误信息的字典。
                  若字段没有 verbose_name，则保留原始字段名作为键。
        """
        # 调用父类（如 DRF Serializer 或 Django Form）的 errors 属性，获取原始验证错误
        # 原始错误的格式通常为 {field_name: [error_messages]}
        errors = super().errors

        # 用于存储转换后的"可读字段名 -> 错误信息"映射
        verbose_errors = {}

        # 构建当前模型所有字段的 {字段名: verbose_name} 映射字典
        # - self.Meta.model._meta.get_fields(): 获取模型定义的所有字段对象
        # - hasattr(field, 'verbose_name'): 过滤掉反向关系、ManyToManyRel 等没有 verbose_name 的属性
        #   （这些非实体字段不需要做名称转换）
        fields = {
            field.name: field.verbose_name
            for field in self.Meta.model._meta.get_fields()
            if hasattr(field, 'verbose_name')
        }

        # 遍历原始错误字典，逐一将字段名替换为 verbose_name
        for field_name, error in errors.items():
            if field_name in fields:
                # 字段存在于模型中且有 verbose_name，使用 verbose_name 作为键
                # str() 确保键为字符串类型（防止 lazy translation 对象导致序列化问题）
                verbose_errors[str(fields[field_name])] = error
            else:
                # 字段不在模型字段映射中（如 non_field_errors、自定义校验字段等），
                # 保留原始字段名不做转换
                verbose_errors[field_name] = error

        return verbose_errors
