import type { CrudExpose, FormScopeContext } from "@fast-crud/fast-crud";

/**
 * 创建"保存成功后留在抽屉继续编辑"的 afterSubmit 处理函数
 *
 * 行为：新增保存成功后切换为编辑模式继续编辑（不关闭抽屉），
 * 并将后端返回的数据全部回写当前表单（含 id、外键 ID 及后端自动生成的字段）；
 * 编辑保存成功后保持编辑模式继续编辑（当前已在编辑模式，无需重新 openEdit）并刷新列表。
 * 返回 false 阻止提交后自动关闭抽屉。
 *
 * 安全说明：新增接口返回的是 CreateSerializer（fields="__all__" 纯模型字段，
 * 不含 xxx_name 等只读计算字段）；审计字段后端 create/update 时强制覆盖，
 * 回写后再次提交不会造成数据污染。
 *
 * @param crudExpose - FastCrud 的 crudExpose 实例
 * @param refreshColumn - 刷新列表时需要刷新的列
 * @returns afterSubmit 处理函数，可直接配置到 form.afterSubmit
 */
export function createFormAfterSubmit(
  crudExpose: CrudExpose,
  refreshColumn?: string[]
) {
  return async ({ mode, form, res }: FormScopeContext) => {
    // 新增保存成功：切换为编辑模式（不关闭抽屉），回写后端返回的全部数据
    if (mode === "add" && res?.data?.id) {
      await crudExpose.openEdit({
        row: { ...form, ...res.data }
      });
      // 将后端返回数据写入当前表单，后续编辑保存可正常携带
      crudExpose.setFormData(res.data);
    }
    // 编辑保存成功：当前已在编辑模式，表单数据保留，无需重新 openEdit，仅刷新列表
    await crudExpose.doRefresh();
    // 刷新指定列的列表
    for (const key of refreshColumn) {
      const tableRef = crudExpose.getFormComponentRef(key);
      tableRef.crudExpose.doRefresh();
    }
    // 返回 false 阻止提交后自动关闭抽屉
    return false;
  };
}
