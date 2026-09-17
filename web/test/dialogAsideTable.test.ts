/**
 * dialogAsideTable 子表弹窗单元测试
 * 覆盖：选择模式内置默认配置、多选（复用模块 $checked 选择列与 onSelectionChange、
 * 不注入行选择插件）、单选（注入 $selected radio 列并隐藏 $checked，回显读模块
 * selectedData）、调用方覆盖优先合并、确认取数、展示模式默认配置与 selectedData 注入
 */
import { describe, expect, it, vi } from "vitest";
import { ElRadio } from "element-plus";
import { uiContext } from "@fast-crud/ui-interface";
import type { DynamicallyCrudOptions } from "@fast-crud/fast-crud";
import { dialogAsideTable } from "@/components/ReAsideTable";

// 弹窗打开函数：捕获传给 addDialog 的完整弹窗配置（断言内置默认值与合并结果）
const addDialogMock = vi.hoisted(() => vi.fn());

vi.mock("@/components/ReDialog", () => ({
  addDialog: addDialogMock
}));

// 子表组件（.vue）占位：弹窗配置断言不依赖组件实现
vi.mock("@/components/ReAsideTable/src/index.vue", () => ({
  default: { name: "mock-aside-table" }
}));

// 注册假 ui：避免 fast-crud 内部按需读取 UI 接口时报错（测试不触发表格渲染）
uiContext.set({ table: {}, tableV2: {} } as any);

/** 弹窗内表格组件的默认属性 */
const baseProps = {
  componentName: "publisher",
  createCrudOptions: (() => ({ crudOptions: {} })) as any
};

/** 打开一次选择模式弹窗（默认多选），返回捕获的弹窗配置 */
const openSelectDialog = (options: Record<string, any> = {}) => {
  addDialogMock.mockClear();
  dialogAsideTable({
    props: { ...baseProps },
    selection: {},
    ...options
  });
  expect(addDialogMock).toHaveBeenCalledTimes(1);
  return addDialogMock.mock.calls[0][0] as any;
};

/** 内容渲染函数返回的 vnode：props 为传给子表组件的属性，ref 为弹窗内表格实例 */
const getVNode = (dialogOptions: any) => dialogOptions.contentRenderer();

/** 取合并后的列表覆盖配置 */
const getOverride = (dialogOptions: any) =>
  getVNode(dialogOptions).props.crudOptionsOverride;

describe("dialogAsideTable 选择模式（多选）", () => {
  it("弹窗默认配置：默认标题「选择」、保留底部按钮并开启确定按钮 loading", () => {
    const dialogOptions = openSelectDialog();
    expect(dialogOptions.title).toBe("选择");
    expect(dialogOptions.hideFooter).toBe(false);
    expect(dialogOptions.sureBtnLoading).toBe(true);
    expect(dialogOptions.width).toBe("70%");
  });

  it("不使用行选择插件：$checked 选择列沿用模块配置，叠加跨页保留选中", () => {
    const override = getOverride(openSelectDialog());
    // 不注入行选择插件：选中事件完全由模块 crud.tsx 的 table.onSelectionChange 承接
    expect(override.settings?.plugins?.rowSelection).toBeUndefined();
    // 跨页保留选中：el-table 原生 reserve-selection（依赖模块 table.rowKey）
    expect(override.columns.$checked.column.reserveSelection).toBe(true);
  });

  it("crossPage=false：不叠加 reserve-selection（翻页后选中清空）", () => {
    const override = getOverride(
      openSelectDialog({ selection: { crossPage: false } })
    );
    expect(override.columns.$checked.column.reserveSelection).toBe(false);
  });

  it("内置默认覆盖配置：隐藏查询区/动作条/工具栏/行操作，多选显示复选框列并隐藏 radio 列", () => {
    const override = getOverride(openSelectDialog());
    expect(override.search.show).toBe(false);
    expect(override.actionbar.show).toBe(false);
    expect(override.toolbar.show).toBe(false);
    expect(override.rowHandle.show).toBe(false);
    expect(override.columns.$checked.column.show).toBe(true);
    expect(override.columns.$selected.column.show).toBe(false);
  });

  it("调用方覆盖配置优先：覆盖项生效，未覆盖项保留内置默认", () => {
    const dialogOptions = openSelectDialog({
      props: {
        ...baseProps,
        crudOptionsOverride: {
          search: { show: true }
        } as DynamicallyCrudOptions
      }
    });
    const override = getOverride(dialogOptions);
    expect(override.search.show).toBe(true);
    expect(override.actionbar.show).toBe(false);
  });

  it("多选确认取数：读取弹窗内表格实例的 selectedData（模块 onSelectionChange 写入）", () => {
    const onSure = vi.fn();
    const dialogOptions = openSelectDialog({ selection: { onSure } });
    const vnode = getVNode(dialogOptions);
    // vnode.props.ref 为 h() 传入的原始 ref（即弹窗内部表格实例）；vnode.ref 是 Vue 内部包装对象，每次渲染不同
    const tableRef = vnode.props.ref ?? vnode.ref;
    // 未选中（组件实例未暴露 selectedData）：确认回传空数组
    tableRef.value = {};
    dialogOptions.beforeSure(vi.fn(), { closeLoading: vi.fn() });
    expect(onSure.mock.calls[0][0]).toEqual([]);
    // 模拟模块 onSelectionChange 写入选中数据：确认回传该数据
    const selectedRows = [
      { id: 1, name: "A" },
      { id: 2, name: "B" }
    ];
    tableRef.value = { selectedData: selectedRows };
    dialogOptions.beforeSure(vi.fn(), { closeLoading: vi.fn() });
    expect(onSure.mock.calls[1][0]).toEqual(selectedRows);
  });
});

describe("dialogAsideTable 选择模式（单选）", () => {
  it("注入 radio 单选列并隐藏 $checked：不注入 table 事件与行选择插件", () => {
    const dialogOptions = openSelectDialog({ selection: { multiple: false } });
    const override = getOverride(dialogOptions);
    // 单选不走行选择插件：无插件配置注入
    expect(override.settings?.plugins?.rowSelection).toBeUndefined();
    // 注入 $selected radio 列（模块 crud.tsx 默认只有 $checked 列）
    const selected = override.columns.$selected;
    expect(selected.form.show).toBe(false);
    expect(selected.column.show).toBe(true);
    expect(selected.column.title).toBe("单选");
    expect(selected.column.align).toBe("center");
    expect(selected.column.width).toBe("55px");
    expect(selected.column.columnSetShow).toBe(false);
    expect(typeof selected.column.cellRender).toBe("function");
    // 单选隐藏复选框列（选中态由 radio 列表达）
    expect(override.columns.$checked.column.show).toBe(false);
    // 点击行/radio 选中与回显由模块自身配置承接（highlightCurrentRow/onCurrentChange/selectedData），不再注入
    expect(override.table).toBeUndefined();
  });

  it("radio 列回显：读弹窗实例 selectedData（点击行/radio 由模块 onCurrentChange 整行写入）", () => {
    const dialogOptions = openSelectDialog({ selection: { multiple: false } });
    const vnode = getVNode(dialogOptions);
    const tableRef = vnode.props.ref ?? vnode.ref;
    const cellRender =
      getOverride(dialogOptions).columns.$selected.column.cellRender;

    const rowA = { id: 1, name: "A" };
    const rowB = { id: 2, name: "B" };

    // 弹窗实例未挂载（selectedData 不可读）：不选中，且不抛错
    tableRef.value = {};
    let vnodeA: any = cellRender({ row: rowA });
    expect(vnodeA.type).toBe(ElRadio);
    expect(vnodeA.props.modelValue).toBe(false);
    expect(vnodeA.props.value).toBe(true);

    // 模块 onCurrentChange 整行写入 selectedData：对应行 radio 回显选中
    tableRef.value = { selectedData: [rowA] };
    vnodeA = cellRender({ row: rowA });
    expect(vnodeA.props.modelValue).toBe(true);
    expect(cellRender({ row: rowB }).props.modelValue).toBe(false);
    // radio 无 onUpdate:modelValue 回调（点击 radio 冒泡触发行点击，由 onCurrentChange 承接）
    expect(vnodeA.props["onUpdate:modelValue"]).toBeUndefined();
  });

  it("单选确认取数：读取模块 selectedData（数组口径，未选为空数组）", () => {
    const onSure = vi.fn();
    const dialogOptions = openSelectDialog({
      selection: { multiple: false, onSure }
    });
    const vnode = getVNode(dialogOptions);
    const tableRef = vnode.props.ref ?? vnode.ref;
    // 未选中（组件实例未暴露 selectedData）：确认回传空数组
    tableRef.value = {};
    dialogOptions.beforeSure(vi.fn(), { closeLoading: vi.fn() });
    expect(onSure.mock.calls[0][0]).toEqual([]);
    // 点击 radio/行经模块 onCurrentChange 整行写入 selectedData（数组口径）：确认回传 0~1 行
    const rowA = { id: 1, name: "A" };
    tableRef.value = { selectedData: [rowA] };
    dialogOptions.beforeSure(vi.fn(), { closeLoading: vi.fn() });
    expect(onSure.mock.calls[1][0]).toEqual([rowA]);
  });
});

describe("dialogAsideTable 展示模式", () => {
  it("未传 selection：纯展示弹窗（默认隐藏底部按钮，不注入选择配置）", () => {
    addDialogMock.mockClear();
    dialogAsideTable({ props: { ...baseProps } });
    expect(addDialogMock).toHaveBeenCalledTimes(1);
    const dialogOptions = addDialogMock.mock.calls[0][0] as any;
    expect(dialogOptions.title).toBe("函数式弹框");
    expect(dialogOptions.hideFooter).toBe(true);
    const vnode = getVNode(dialogOptions);
    expect(vnode.props.crudOptionsOverride).toBeUndefined();
  });

  it("展示模式确认：beforeSure 注入表格实例的 selectedData", () => {
    addDialogMock.mockClear();
    const onBeforeSure = vi.fn();
    dialogAsideTable({ props: { ...baseProps }, beforeSure: onBeforeSure });
    const dialogOptions = addDialogMock.mock.calls[0][0] as any;
    const vnode = getVNode(dialogOptions);
    const tableRef = vnode.props.ref ?? vnode.ref;
    tableRef.value = { selectedData: [{ id: 9 }] };
    const done = vi.fn();
    dialogOptions.beforeSure(done, { closeLoading: vi.fn() });
    expect(onBeforeSure.mock.calls[0][0]).toBe(done);
    expect(onBeforeSure.mock.calls[0][1].selectedData).toEqual([{ id: 9 }]);
  });
});
