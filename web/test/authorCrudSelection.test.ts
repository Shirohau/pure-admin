/**
 * author crud 选择列测试（selectedData 统一数组口径）
 * 模块默认只有 $checked 多选列（单选 $selected radio 列由 ReAsideTable 按需注入）：
 * 覆盖行高亮 + 单选整行写入数组 + 多选整组写入与 $checked 列定义。
 */
import { describe, expect, it, vi } from "vitest";
import { reactive } from "vue";

// mock 视图依赖：仅保留 crud 配置组装逻辑
vi.mock("@/views/example/author/api", () => ({
  api: {
    GetList: vi.fn(),
    CreateObj: vi.fn(),
    UpdateObj: vi.fn(),
    DeleteObj: vi.fn(),
    BatchDelete: vi.fn()
  },
  apiPrefix: "/api/example/author/"
}));
vi.mock("@/views/example/book/api", () => ({ api: { GetList: vi.fn() } }));
vi.mock("@/views/example/book/crud", () => ({
  bookSelect: () => ({}),
  bookTable: () => ({})
}));
vi.mock("@/views/example/publisher/crud", () => ({
  publisherDialogTable: vi.fn()
}));
vi.mock("@/components/ReExport", () => ({ openExportDialog: vi.fn() }));
vi.mock("@/components/ReImport", () => ({ openImportDialog: vi.fn() }));
vi.mock("@/components/ReHistory", () => ({
  historyTable: () => ({}),
  openHistoryDialog: vi.fn()
}));
vi.mock("@/utils/crud/createCrudPerms", () => ({
  createCrudPerms: () => ({
    add: { value: true },
    view: { value: true },
    edit: { value: true },
    remove: { value: true },
    export: { value: true },
    import: { value: true },
    print: { value: true },
    historyRecover: { value: true },
    batchDestroy: { value: true }
  })
}));
vi.mock("@/utils/crud/createRowContextmenu", () => ({
  createRowContextmenu: () => vi.fn()
}));
vi.mock("@/components/ReFilter/src/useFilter", () => ({
  useFilter: () => ({
    createFilterHeader: () => () => null,
    FilterTags: {},
    clearAllFilters: vi.fn()
  })
}));
vi.mock("@/views/system/dictionary/api", () => ({
  getDictData: () => ({ data: [] })
}));
vi.mock("@/views/system/area/api", () => ({
  getAreaData: () => ({ data: [] })
}));
vi.mock("@/utils/crud/createFormAfterSubmit", () => ({
  createFormAfterSubmit: () => vi.fn()
}));
vi.mock("@/utils/crud/createFormWrapper", () => ({
  createFormWrapper: () => vi.fn()
}));
vi.mock("@/utils/crud/createRelation", () => ({
  createRelation: () => ({
    createSelect: () => ({}),
    createForm: () => ({}),
    createTable: () => ({})
  })
}));
vi.mock("@/utils/crud/createSummaryMethod", () => ({
  createSummaryMethod: () => vi.fn()
}));

import createCrudOptions from "@/views/example/author/crud";

/** 构造 createCrudOptions 参数：mock crudExpose */
const createOptions = () => {
  const crudExpose = {
    getBaseTableRef: () => ({}),
    doRefresh: vi.fn()
  };
  return createCrudOptions({ crudExpose, context: {} }) as any;
};

describe("author crud 选择列（selectedData 统一数组口径）", () => {
  it("表格配置：行高亮 + 单选整行写入数组 + 多选整组写入", () => {
    const ret = createOptions();
    const { crudOptions, selectedData } = ret;

    // 行高亮与 current-change 事件已配置
    expect(crudOptions.table.rowKey).toBe("id");
    expect(crudOptions.table.highlightCurrentRow).toBe(true);
    expect(typeof crudOptions.table.onCurrentChange).toBe("function");

    // 模块默认只有 $checked 多选列（单选 $selected 列由 ReAsideTable 按需注入）
    expect(crudOptions.columns.$selected).toBeUndefined();
    expect(crudOptions.columns.$checked.column.type).toBe("selection");
    expect(crudOptions.columns.$checked.column.show.value).toBe(true);

    // （行对象经 ref 响应式包装，与真实链路一致：传入 reactive 代理时保持同一引用）
    const row = reactive({ id: 1, name: "A" });
    const rowB = reactive({ id: 2, name: "B" });

    // 单选（点击行）：整行包成数组写入，引用不变
    crudOptions.table.onCurrentChange(row);
    expect(selectedData.value.length).toBe(1);
    expect(selectedData.value[0]).toBe(row);

    // 清空当前行（row 为 null）：selectedData 重置为空数组
    crudOptions.table.onCurrentChange(null);
    expect(selectedData.value.length).toBe(0);

    // 多选（复选框列）：选中行整组写入（不只取首行）
    crudOptions.table.onSelectionChange([row, rowB]);
    expect(selectedData.value.length).toBe(2);
    expect(selectedData.value[0]).toBe(row);
    expect(selectedData.value[1]).toBe(rowB);

    // 取消全部勾选：selectedData 为空数组
    crudOptions.table.onSelectionChange([]);
    expect(selectedData.value.length).toBe(0);
  });
});
