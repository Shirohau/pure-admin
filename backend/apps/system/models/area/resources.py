from import_export.results import Result
from extends.drf.resources import CustomCeleryResource
from .filters import AreaFilter
from .models import AreaModel


class AreaExportResource(CustomCeleryResource):
    filterset_class = AreaFilter

    class Meta:
        model = AreaModel


class AreaImportResource(CustomCeleryResource):
    def import_data(self, dataset, dry_run=False, raise_errors=False, **kwargs):
        """
        自定义导入逻辑
        """
        result = Result()
        result.total_rows = 0

        for province_node in dataset.dict:
            self._import_area_recursive(
                node=province_node,
                parent_code=None,
                level=1,
                dry_run=dry_run,
                result=result
            )
        return result

    def _import_area_recursive(self, node, parent_code, level, dry_run, result):
        result.total_rows += 1
        code = node["code"]
        name = node["name"]

        # 非 dry_run：写入数据库
        if not dry_run:
            area, created = AreaModel.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "level": level,
                    "enable": True,
                    "parent": None,
                }
            )
            # 更新
            if not created:
                area.name = name
                area.level = level
                area.enable = True
                area.save()
            # 设置 parent（必须在 area 保存后）
            if parent_code:
                parent = AreaModel.objects.get(code=parent_code)
                if area.parent != parent:
                    area.parent = parent
                    area.save(update_fields=["parent"])

        # 递归子节点
        for child in node.get("children", []):
            self._import_area_recursive(
                node=child,
                parent_code=code,
                level=level + 1,
                dry_run=dry_run,
                result=result
            )

    class Meta:
        model = AreaModel
