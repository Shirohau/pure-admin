import json
from import_export.results import Result
from tablib import Dataset

from extends.drf.resources import CustomCeleryResource
from .filters import MenuFilter
from .models import MenuModel
from ..menu_button.models import MenuButtonModel
from ..menu_field.models import MenuFieldModel


def build_menu_tree(menus_dict, parent_id=None):
    """
    递归构建菜单树
    :param menus_dict: 所有菜单的字典 {id: menu}
    :param parent_id: 当前父级 ID
    :return: list of tree nodes
    """
    tree = []
    # 获取当前层级的所有子菜单（按 sort 排序）
    children = [m for m in menus_dict.values() if m.parent_id == parent_id]
    children.sort(key=lambda x: x.sort)  # 确保排序

    for menu in children:
        node = {
            "菜单名称": menu.title,
            "菜单图标": menu.icon,
            "右侧图标": menu.extraIcon,
            "路由地址": menu.path,
            "路由名字": menu.name,
            "组件地址": menu.component,
            "侧边显示": menu.showLink,
            "显示父级": menu.showParent,
            "是否缓存": menu.keepAlive,
            "是否禁止": menu.hiddenTag,
            "是否固定": menu.fixedTag,
            "内嵌链接": menu.frameSrc,
            "内嵌动画": menu.frameLoading,
            "组件动画": menu.transitionName,
            "组件进场动画": menu.enterTransition,
            "组件离场动画": menu.leaveTransition,
            "子菜单": build_menu_tree(menus_dict, menu.id),
            "菜单按钮": [
                {
                    "按钮名称": btn.name,
                    "按钮类型": btn.button_type,
                    "权限值": btn.key,
                    "接口地址": btn.api,
                    "接口请求方法": btn.method,
                }
                for btn in getattr(menu, 'prefetched_buttons', [])
            ],
            "菜单字段": [
                {
                    "模型表": field.model,
                    "字段名": field.field_name,
                    "字段显示名": field.verbose_name
                }
                for field in getattr(menu, 'prefetched_fields', [])
            ],
        }
        tree.append(node)
    return tree


class MenuExportResource(CustomCeleryResource):
    filterset_class = MenuFilter

    def export(self, queryset=None, *args, **kwargs):
        """
        重写 export 方法，返回树形结构的 JSON Dataset
        """
        if queryset is None:
            queryset = self.get_queryset()

        # 优化查询：预加载按钮和排序
        menus = queryset.select_related('parent').prefetch_related('menu_button', 'menu_field').order_by('sort')

        # 转为字典便于快速查找
        menus_dict = {menu.id: menu for menu in menus}

        # 为每个菜单注入预取的按钮（避免 N+1）
        for menu in menus_dict.values():
            # 将 buttons fields 绑定到实例上，供 build_menu_tree 使用
            menu.prefetched_buttons = list(menu.menu_button.all())
            menu.prefetched_fields = list(menu.menu_field.all())

        # 构建树（根节点 parent_id=None）
        tree_data = build_menu_tree(menus_dict, parent_id=None)

        # 创建 tablib Dataset（JSON 格式要求 data 是 list 或 dict）
        dataset = Dataset()
        dataset.json = json.dumps(tree_data, ensure_ascii=False, indent=2)
        return dataset

    class Meta:
        model = MenuModel
        # fields 不再重要，因为我们完全自定义了 export 但建议保留以兼容框架
        fields = ('id', 'title', 'parent')


class MenuImportResource(CustomCeleryResource):
    def import_data(self, dataset, dry_run=False, raise_errors=False, use_transactions=False, collect_failed_rows=False, **kwargs):
        """
        完全接管导入：dataset tree 树形结构数据
        """
        result = Result()
        # 递归导入整棵树
        self._import_menu_tree(dataset.dict, result, parent=None)
        return result

    def _import_menu_tree(self, nodes, result, parent=None):
        """
        递归导入菜单树
        :param nodes: 当前层级的菜单列表
        :param parent: 父级 MenuModel 实例
        """
        for sort_index, node in enumerate(nodes, start=1):
            result.total_rows += 1
            # 1. 处理菜单主表
            menu = self._import_menu(sort_index, node, parent)
            # 2. 处理菜单按钮
            self._import_menu_button(node, menu)
            # 3. 处理菜单字段
            self._import_menu_field(node, menu)
            # 4. 递归处理子菜单
            children = node.get("子菜单", [])
            self._import_menu_tree(children, result, parent=menu)

    def _import_menu(self, sort_index, node, parent=None):
        # === 1. 处理菜单主表 ===
        menu, created = MenuModel.objects.get_or_create(
            name=node["路由名字"],
            defaults={
                "title": node["菜单名称"],
                "icon": node.get("菜单图标") or "",
                "extraIcon": node.get("右侧图标"),
                "path": node["路由地址"],
                "component": node.get("组件地址") or "",
                "showLink": node.get("侧边显示", True),
                "showParent": node.get("显示父级", True),
                "keepAlive": node.get("是否缓存", True),
                "hiddenTag": node.get("是否禁止", False),
                "fixedTag": node.get("是否固定", False),
                "frameSrc": node.get("内嵌链接"),
                "frameLoading": node.get("内嵌动画", True),
                "transitionName": node.get("组件动画"),
                "enterTransition": node.get("组件进场动画"),
                "leaveTransition": node.get("组件离场动画"),
                "parent": parent,
                "sort": sort_index,
            }
        )
        if not created:
            # 更新字段
            menu.title = node["菜单名称"]
            menu.icon = node.get("菜单图标") or menu.icon
            menu.extraIcon = node.get("右侧图标")
            menu.path = node["路由地址"]
            menu.component = node.get("组件地址") or menu.component
            menu.showLink = node.get("侧边显示", menu.showLink)
            menu.showParent = node.get("显示父级", menu.showParent)
            menu.keepAlive = node.get("是否缓存", menu.keepAlive)
            menu.hiddenTag = node.get("是否禁止", menu.hiddenTag)
            menu.fixedTag = node.get("是否固定", menu.fixedTag)
            menu.frameSrc = node.get("内嵌链接")
            menu.frameLoading = node.get("内嵌动画", menu.frameLoading)
            menu.transitionName = node.get("组件动画")
            menu.enterTransition = node.get("组件进场动画")
            menu.leaveTransition = node.get("组件离场动画")
            menu.parent = parent
            menu.sort = sort_index
            menu.save()

        return menu

    def _import_menu_button(self, node, menu):
        # === 2. 处理菜单按钮 ===
        buttons = node.get("菜单按钮", [])
        for btn_data in buttons:
            btn_key = btn_data.get("权限值")
            if not btn_key:
                continue
            btn, btn_created = MenuButtonModel.objects.get_or_create(
                menu=menu,
                key=btn_key,
                defaults={
                    "name": btn_data.get("按钮名称", ""),
                    "button_type": btn_data.get("按钮类型", ""),
                    "api": btn_data.get("接口地址"),
                    "method": btn_data.get("接口请求方法"),
                }
            )
            if not btn_created:
                btn.name = btn_data.get("按钮名称", btn.name)
                btn.button_type = btn_data.get("按钮类型", btn.button_type)
                btn.api = btn_data.get("接口地址")
                btn.method = btn_data.get("接口请求方法")
                btn.save()

    def _import_menu_field(self, node, menu):
        # === 3. 处理菜单字段 ===
        fields = node.get("菜单字段", [])
        for field_data in fields:
            model_name = field_data.get("模型表")
            field_name = field_data.get("字段名")
            if not (model_name and field_name):
                continue
            field_obj, field_created = MenuFieldModel.objects.get_or_create(
                menu=menu,
                model=model_name,
                field_name=field_name,
                defaults={
                    "verbose_name": field_data.get("字段显示名", ""),
                }
            )
            if not field_created:
                field_obj.verbose_name = field_data.get("字段显示名", field_obj.verbose_name)
                field_obj.save()

    class Meta:
        model = MenuModel
        # 这些字段仅用于兼容，实际不使用
        fields = ('name',)
