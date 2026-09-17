import ContextMenu from "@imengyu/vue3-context-menu";
import type { CrudExpose } from "@fast-crud/fast-crud";
// https://docs.imengyu.top/vue3-context-menu-docs/
/**
 * 创建 FastCrud 表格右键菜单处理函数
 *
 * 将 FastCrud rowHandle.buttons 中的行操作按钮转换为右键菜单项，
 * 并自动注入 FastCrud 所需的完整上下文（key / row / btn / index）。
 *
 * @param crudExpose - FastCrud 的 crudExpose 实例，用于获取按钮配置和表格数据
 * @param rowKey    - 行主键字段名，默认 "id"，用于在表格数据中定位行索引
 * @returns 表格 row-contextmenu 事件处理函数，可直接赋给 table.onRowContextmenu
 */
export function createRowContextmenu(crudExpose: CrudExpose, rowKey = "id") {
  return (row: any, _column: any, e: PointerEvent) => {
    // 阻止浏览器默认右键菜单
    e.preventDefault();

    // 1. 获取 FastCrud 处理后的行操作按钮配置
    const buttons = crudExpose.crudBinding.value.rowHandle?.buttons ?? {};

    // 2. 通过主键匹配，在表格数据中查找当前行的索引
    //    FastCrud 内置按钮（view / edit / remove）内部依赖 index 调用 openView / openEdit / doRemove
    const tableData = crudExpose.getTableData();
    const index =
      tableData?.findIndex((item: any) => item[rowKey] === row[rowKey]) ?? -1;

    // 3. 将按钮配置转换为右键菜单项，链式处理：过滤 → 排序 → 映射
    const menuItems = Object.entries(buttons)
      // 3.1 过滤：排除 show === false 的按钮（未配置 show 时默认为 true，即显示）
      .filter(([, btn]: [string, any]) => btn.show !== false)
      // 3.2 排序：按 order 升序排列，未配置 order 的默认视为 0
      .sort(
        ([, a]: [string, any], [, b]: [string, any]) =>
          (a.order ?? 0) - (b.order ?? 0)
      )
      // 3.3 映射：构造右键菜单所需的 { label, onClick } 结构
      .map(([key, btn]: [string, any]) => ({
        label: btn.text,
        // 包装 onClick，手动注入 FastCrud 完整的按钮回调上下文
        // 内置按钮需要 key 判断操作类型，row/index 定位数据，btn 提供配置信息
        onClick: () =>
          btn.click({ key: btn.key || key, row, btn, index } as any)
      }));

    // 4. 根据当前主题动态设置右键菜单主题
    const isDark = document.documentElement.classList.contains("dark");

    ContextMenu.showContextMenu({
      theme: isDark ? "dark" : "default",
      x: e.x,
      y: e.y,
      items: menuItems
    });
  };
}
