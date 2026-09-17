from import_export.fields import Field
from import_export.widgets import CharWidget

from extends.drf.resources import CustomCeleryResource
from .filters import RoleFilter
from .models import RoleModel
from ..dept.models import DeptModel
from ..menu_button.models import MenuButtonModel
from ..menu_field.models import MenuFieldModel
from ..role_menu_button.models import RoleMenuButtonModel
from ..role_menu_field.models import FUNC_PERMISSION_DEFINITIONS, RoleMenuFieldModel


class RoleExportResource(CustomCeleryResource):
    filterset_class = RoleFilter
    status = Field(attribute='status', column_name="状态", widget=CharWidget(coerce_to_string=False))
    buttons = Field(column_name="关联菜单按钮")
    fields = Field(column_name="关联菜单字段")

    @staticmethod
    def dehydrate_buttons(instance):
        data = [
            {
                "关联角色": item.role.code,
                "关联菜单按钮": item.menu_button.key,
                "权限范围": item.permission_range,
                "关联部门": [dept.code for dept in item.dept.all()]
            }
            for item in instance.role_menu_button.all()
        ]
        return data

    @staticmethod
    def dehydrate_fields(instance):
        data = [
            {
                "关联角色": item.role.code,
                "菜单路由名字": item.menu_field.menu.name,
                "模型表": item.menu_field.model,
                "字段名": item.menu_field.field_name,
                "权限等级": item.permission_level,
                # 功能权限动态导出：每个功能权限一列（“是否可下载”/“是否可打印”…），
                # 列名由 FUNC_PERMISSION_DEFINITIONS 自动生成，新增功能权限无需改动此处
                **{
                    f"是否{label}": bool((item.func_permissions or {}).get(key))
                    for key, label in FUNC_PERMISSION_DEFINITIONS.items()
                },
            }
            for item in instance.role_menu_field.all()
        ]
        return data

    class Meta:
        model = RoleModel
        fields = ("name", "code", "status", "buttons", "fields")


class RoleImportResource(CustomCeleryResource):
    examples_data = [
        {
            "名称": "系统管理员",
            "编号": "ADMIN",
            "状态": 1,
        },
        {
            "名称": "普通用户",
            "编号": "USER",
            "状态": 0,
        }
    ]

    name = Field(attribute="name", column_name="名称")
    code = Field(attribute="code", column_name="编号")
    status = Field(attribute="status", column_name="状态")
    buttons = Field(column_name="关联菜单按钮")
    fields = Field(column_name="关联菜单字段")

    @staticmethod
    def save_buttons(buttons):
        """
        自定义保存 关联菜单按钮
        """
        for item in buttons:
            role = RoleModel.objects.get(code=item.get("关联角色"))
            menu_button = MenuButtonModel.objects.get(key=item.get("关联菜单按钮"))
            permission_range = item.get("权限范围")
            dept_codes = item.get("关联部门", [])

            # 获取或创建 RoleMenuButtonModel 实例（不处理 dept）
            btn, btn_created = RoleMenuButtonModel.objects.get_or_create(
                role=role,
                menu_button=menu_button,
                defaults={"permission_range": permission_range}
            )

            # 如果已存在，更新 permission_range
            if not btn_created:
                btn.permission_range = permission_range
                btn.save(update_fields=["permission_range"])

            # 处理多对多字段 dept：必须用 .set()
            if dept_codes:
                dept = DeptModel.objects.filter(code__in=dept_codes)
                btn.dept.set(dept)
            else:
                btn.dept.clear()  # 清空关联

    @staticmethod
    def save_fields(fields):
        """
        自定义保存 关联菜单字段
        """
        for item in fields:
            role = RoleModel.objects.get(code=item.get("关联角色"))
            menu_field = MenuFieldModel.objects.get(
                menu__name=item.get("菜单路由名字"),
                model=item.get("模型表"),
                field_name=item.get("字段名")
            )
            permission_level = item.get("权限等级")
            # 功能权限动态解析：按 FUNC_PERMISSION_DEFINITIONS 读取各“是否xxx”列并写入 func_permissions JSON；
            # 兼容旧导出数据：缺少某功能权限列时默认为 False（显式关闭）。
            # 新增功能权限无需改动此处，列自动参与导入。
            func_permissions = {
                key: bool(item.get(f"是否{label}", False))
                for key, label in FUNC_PERMISSION_DEFINITIONS.items()
            }

            # 获取或创建 RoleMenuFieldModel 实例
            instance, created = RoleMenuFieldModel.objects.get_or_create(
                role=role,
                menu_field=menu_field,
                defaults={
                    "permission_level": permission_level,
                    "func_permissions": func_permissions,
                }
            )

            # 如果已存在，更新字段权限
            if not created:
                instance.permission_level = permission_level
                instance.func_permissions = func_permissions
                instance.save(update_fields=["permission_level", "func_permissions"])

    def after_save_instance(self, instance, row, **kwargs):
        """
        在实例保存完成后执行的后处理操作。
        用于保存与角色关联的菜单按钮和菜单字段信息。
        """
        self.save_buttons(row.get("关联菜单按钮"))
        self.save_fields(row.get("关联菜单字段"))

    class Meta:
        model = RoleModel
        fields = ("id", "name", "code", "status", "buttons", "fields")
        import_id_fields = ("code",)
