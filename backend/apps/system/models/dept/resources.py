#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
部门导入导出资源：
    - DeptExportResource：导出部门（含上级部门编号列）
    - DeptImportResource：导入部门（拓扑排序 + 精确错误定位）

N+1 查询优化说明：
    1. 导出「上级部门编号」列：原实现每行 get_parent() 触发 1 次查询
       （N 行 = N 次查询）。现改为懒加载批量缓存：导出过程首次调用时
       一次性查询全表 path → code 映射（1 次查询），后续仅内存查找；
    2. 导入创建部门时查找数据库中的父节点：原实现每行 1 次
       DeptModel.objects.get(code=...)（N 行 = N 次查询）。现改为
       批量预取全部可能成为父节点的数据库部门（1 次查询）。
"""

from collections import defaultdict, deque

from import_export.fields import Field
from import_export.results import RowResult, Result
from rest_framework.exceptions import ValidationError

from extends.drf.resources import CustomCeleryResource
from .filters import DeptFilter
from .models import DeptModel, STEPLEN


class DeptExportResource(CustomCeleryResource):
    """部门导出资源：导出部门树快照，含路径字符串、深度、子节点数与上级部门编号。"""

    filterset_class = DeptFilter
    path = Field(attribute='path', column_name="路径字符串")
    depth = Field(attribute='depth', column_name="深度")
    numchild = Field(attribute='numchild', column_name="子节点数量")

    parent_name = Field(column_name='上级部门编号')

    def dehydrate_parent_name(self, instance):
        """
        导出「上级部门编号」列（父部门的 code）。

        N+1 优化：原实现每行调用 get_parent() 触发 1 次数据库查询，
        导出 N 行需要 N 次查询。现改为懒加载批量缓存：
            - 首次调用时一次性查询全表 path → code 映射（1 次查询）；
            - 整个导出过程资源实例复用，后续行仅做内存字典查找；
            - 通过 path 前缀截断（去掉末尾 STEPLEN 位）定位父级，
              与 get_parent() 的结果完全等价（treebeard 物化路径编码）。

        Args:
            instance: 当前导出的部门实例

        Returns:
            str | None: 上级部门编号；根节点（无父级）返回 None（导出为空单元格）
        """
        # 懒加载：仅在首次调用时构建缓存，避免导出空表时无谓查询
        if not hasattr(self, "_parent_code_map"):
            self._parent_code_map = dict(
                DeptModel.objects.values_list("path", "code")
            )
        # 根节点（depth=1）没有父级，path 截断后为 ''，字典中不存在 → 返回 None
        parent_path = instance.path[:-STEPLEN]
        return self._parent_code_map.get(parent_path)

    class Meta:
        model = DeptModel
        fields = ('id', 'name', 'code', 'status', 'path', 'depth', 'parent_name', 'numchild')


def parse_status(value):
    """
    安全解析「部门状态」字段，兼容多种输入格式：
    - 数字：1 / 0 → True / False
    - 布尔：True / False
    - 字符串：'1', 'true', 'yes', 'on'（不区分大小写和前后空格）→ True
    - 其他（包括 None、空字符串、'0'、'false' 等）→ False

    Args:
        value: 原始导入值（任意类型）

    Returns:
        bool: 解析后的布尔状态
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in ('1', 'true', 'yes', 'on', 't', 'y')
    return False


class DeptImportResource(CustomCeleryResource):
    """
    部门导入资源。

    导入策略：
        1. 跳过已存在的部门编号（不更新，防止误覆盖线上数据）；
        2. 上级部门可来自：数据库、本文件、或为空（顶级）；
        3. 自动处理依赖顺序（拓扑排序）：保证子部门在其父部门之后创建，
           因为 treebeard 的 add_child 依赖父节点已存在；
        4. 精确错误定位（行号 + 原因），并检测循环依赖。
    """

    parent_code = Field(column_name='上级部门编号')

    def import_data(self, dataset, dry_run=False, raise_errors=False, **kwargs):
        """
        自定义导入逻辑。

        Args:
            dataset: tablib 数据集（表头：id/部门名称/部门编号/部门状态/上级部门编号）
            dry_run: 试运行模式（只校验不落库）
            raise_errors: 是否抛出错误（默认 False，本实现直接抛出 ValidationError）

        Returns:
            import_export_extensions 兼容的 Result 对象（含 totals/skipped_rows 等）
        """
        # === Step 1: 安全解析原始数据 ===
        all_rows = []
        for i, raw_row in enumerate(dataset.dict, start=1):
            # 安全提取并清理字段（防止 None.strip() 报错）
            _id = raw_row.get('id')
            name = (raw_row.get('部门名称') or '').strip()
            code = (raw_row.get('部门编号') or '').strip()
            status_raw = raw_row.get('部门状态')
            # 上级部门：空值转为 None，非空则去空格
            parent_code = (raw_row.get('上级部门编号') or '').strip() or None
            if not code:
                raise ValidationError(f"第 {i} 行：部门编号不能为空")

            all_rows.append({
                'id': _id,
                'name': name,
                'code': code,
                'status': parse_status(status_raw),  # 统一转为 bool
                'parent_code': parent_code,
                'line_number': i
            })

        if not all_rows:
            result = Result()
            result.total_rows = 0
            return result

        all_codes_in_file = {r['code'] for r in all_rows}

        # === Step 2: 过滤已存在的部门（跳过）===
        # 一次性查询文件中所有 code 是否已存在，避免逐行判断
        existing_codes = set(
            DeptModel.objects.filter(code__in=all_codes_in_file).values_list('code', flat=True)
        )
        new_rows = [r for r in all_rows if r['code'] not in existing_codes]
        skipped_count = len(existing_codes)

        if not new_rows:
            result = Result()
            result.total_rows = len(all_rows)
            result.totals[RowResult.IMPORT_TYPE_SKIP] = skipped_count
            return result

        # === Step 3: 构建依赖图并拓扑排序 ===
        code_to_row = {r['code']: r for r in new_rows}
        in_degree = {r['code']: 0 for r in new_rows}  # 入度：子节点依赖父节点的数量
        children_map = defaultdict(list)  # 父 -> 子列表

        # 预加载数据库中所有部门编号（避免多次查询）
        db_codes = set(DeptModel.objects.values_list('code', flat=True))

        # 分析每个新部门的父节点来源
        for row in new_rows:
            pcode = row['parent_code']
            if pcode:
                if pcode in code_to_row:
                    # 父节点在本次导入文件中 → 建立内部依赖（拓扑排序约束）
                    in_degree[row['code']] += 1
                    children_map[pcode].append(row['code'])
                elif pcode not in db_codes:
                    # 父节点既不在文件也不在数据库 → 悬空，报错
                    raise ValidationError(
                        f"第 {row['line_number']} 行：上级部门 '{pcode}' 不存在于数据库，且未在本文件中定义"
                    )
                # else: 父节点在数据库中 → 无内部依赖，入度为 0（可最先创建）

        # Kahn 算法进行拓扑排序：保证父节点总是先于子节点被创建
        queue = deque([code for code in in_degree if in_degree[code] == 0])
        sorted_codes = []
        while queue:
            code = queue.popleft()
            sorted_codes.append(code)
            for child in children_map[code]:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)

        # 检查是否所有节点都被排序（未被排序说明存在循环依赖：A 是 B 的父、B 又是 A 的父）
        if len(sorted_codes) != len(new_rows):
            raise ValidationError("部门层级存在循环依赖，无法导入")

        # === Step 4: 按拓扑顺序创建部门 ===
        # 批量预取数据库中可能成为父节点的部门（1 次查询替代逐行 get）
        db_parent_codes = {
            r['parent_code'] for r in new_rows
            if r['parent_code'] and r['parent_code'] not in code_to_row
        }
        db_parent_map = {
            p.code: p
            for p in DeptModel.objects.filter(code__in=db_parent_codes)
        }

        created_count = 0
        created_codes = {}  # 记录已创建的新部门实例（code -> obj）

        if not dry_run:
            for code in sorted_codes:
                row = code_to_row[code]
                pcode = row['parent_code']

                if pcode is None:
                    # 创建顶级节点
                    obj = DeptModel.add_root(
                        id=row['id'],
                        name=row['name'],
                        code=row['code'],
                        status=row['status']
                    )
                else:
                    # 父节点要么在已创建的新部门中，要么在数据库中（均已预取）
                    parent = created_codes.get(pcode) or db_parent_map.get(pcode)
                    obj = parent.add_child(
                        id=row['id'],
                        name=row['name'],
                        code=row['code'],
                        status=row['status']
                    )

                created_codes[code] = obj
                created_count += 1

        # === Step 5: 返回结果（兼容 import_export_extensions）===
        result = Result()
        result.total_rows = len(all_rows)
        result.totals[RowResult.IMPORT_TYPE_NEW] = created_count
        result.totals[RowResult.IMPORT_TYPE_SKIP] = skipped_count

        # 添加 import_export_extensions 需要的属性（供前端展示导入明细）
        result.skipped_rows = []  # 已跳过的行（可收集跳过的行）
        result.invalid_rows = []  # 无效行（字段校验已在解析阶段完成，无额外无效行）
        result.created_rows = []  # 成功创建的行（可选）
        result.failed_rows = []  # 失败行（异常已抛出，正常路径为空）
        return result

    class Meta:
        model = DeptModel
        fields = ('id', 'name', 'code', 'status', 'parent_code')
