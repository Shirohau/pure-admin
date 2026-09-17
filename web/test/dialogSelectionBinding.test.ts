/**
 * 选择模式选中链路集成测试（真实 fast-crud 初始化）
 * 覆盖：选择模式不注入 rowSelection 插件——模块 crud.tsx 自身配置的
 * $checked 选择列（type: "selection"）与 table.onSelectionChange 不被弹窗
 * 覆盖配置替换；勾选后模块 selectedData 承接选中数据，确认时可取回。
 */
import { beforeAll, describe, expect, it, vi } from "vitest";
import { createApp, h, ref } from "vue";
import ui from "@fast-crud/ui-element";
import { FastCrud, useFs } from "@fast-crud/fast-crud";
import { dialogAsideTable } from "@/components/ReAsideTable";

// 弹窗打开函数：捕获传给 addDialog 的完整弹窗配置
const addDialogMock = vi.hoisted(() => vi.fn());

vi.mock("@/components/ReDialog", () => ({
  addDialog: addDialogMock
}));

vi.mock("@/components/ReAsideTable/src/index.vue", () => ({
  default: { name: "mock-aside-table" }
}));

beforeAll(() => {
  // 安装真实 ui 与 FastCrud：useFs 初始化依赖
  createApp({ render: () => null })
    .use(ui)
    .use(FastCrud, {
      dictRequest: async () => [],
      commonOptions: () => ({}),
      logger: { off: { tableColumns: false } }
    } as any);
});

describe("选择模式选中链路（真实 crud 初始化）", () => {
  it("模块选中事件与选择列保留：勾选写入 selectedData，确认取回选中行", () => {
    /** 模块 crud 自有配置（模拟 publisher/author 模块） */
    const selectedData = ref<any[]>([]);
    const moduleHandler = (rows: any[]) => {
      selectedData.value = rows;
    };
    const moduleCreateCrudOptions = (() => ({
      selectedData,
      crudOptions: {
        request: {
          pageRequest: async () => ({ records: [], total: 0 }),
          addRequest: async () => ({}),
          editRequest: async () => ({}),
          delRequest: async () => ({})
        },
        table: { rowKey: "id", onSelectionChange: moduleHandler },
        columns: {
          $checked: {
            title: "选择",
            form: { show: false },
            column: { type: "selection", align: "center", width: "55px" }
          }
        }
      }
    })) as any;

    // 1. 打开弹窗，取弹窗内置的覆盖配置
    addDialogMock.mockClear();
    const onSure = vi.fn();
    dialogAsideTable({
      props: {
        componentName: "publisher",
        createCrudOptions: moduleCreateCrudOptions
      },
      selection: { onSure }
    });
    const dialogConfig = addDialogMock.mock.calls[0][0] as any;
    const vnode = dialogConfig.contentRenderer();
    const override = vnode.props.crudOptionsOverride;

    // 2. 以真实 useFs 初始化（模块配置 + 弹窗覆盖配置）
    let binding: any = null;
    const app = createApp({
      setup() {
        const crudRef = ref(null);
        const crudBinding = ref<any>({});
        useFs({
          crudRef,
          crudBinding,
          context: {} as any,
          createCrudOptions: moduleCreateCrudOptions,
          crudOptionsOverride: override
        });
        binding = crudBinding.value;
        return () => h("div");
      }
    });
    app.mount(document.createElement("div"));

    // 选中事件绑定保持模块自身的处理函数（覆盖配置未注入插件、未覆盖该事件）
    expect(binding.table.onSelectionChange).toBe(moduleHandler);
    // $checked 选择列沿用模块的 type: "selection"，并叠加弹窗的跨页保留选中
    expect(binding.columns.$checked.column.type).toBe("selection");
    expect(binding.columns.$checked.column.show).toBe(true);
    expect(binding.columns.$checked.column.reserveSelection).toBe(true);

    // 3. 注入弹窗内部表格实例（getter 模拟组件 expose 的 ref 解包：实时读取 selectedData）
    const tableRef = vnode.props.ref ?? vnode.ref;
    tableRef.value = {
      crudExpose: { crudBinding: { value: binding } },
      get selectedData() {
        return selectedData.value;
      }
    };

    // 4. 未选中确认：回传空数组
    dialogConfig.beforeSure(vi.fn(), { closeLoading: vi.fn() });
    expect(onSure.mock.calls[0][0]).toEqual([]);

    // 5. 模拟勾选两行：模块 onSelectionChange 写入 selectedData，确认取回
    const rows = [
      { id: 7, name: "G" },
      { id: 8, name: "H" }
    ];
    binding.table.onSelectionChange(rows);
    dialogConfig.beforeSure(vi.fn(), { closeLoading: vi.fn() });
    expect(onSure.mock.calls[1][0]).toEqual(rows);

    // 6. 取消一行后再次确认：回传剩余选中行
    binding.table.onSelectionChange([rows[0]]);
    dialogConfig.beforeSure(vi.fn(), { closeLoading: vi.fn() });
    expect(onSure.mock.calls[2][0]).toEqual([rows[0]]);
  });
});
