import { beforeEach, describe, expect, it, vi } from "vitest";
import type { DynamicallyCrudOptions } from "@fast-crud/fast-crud";

// mock 弹窗函数：捕获/断言 cellRender 点击后传递给详情弹窗的配置
const { dialogAsideTableMock } = vi.hoisted(() => ({
  dialogAsideTableMock: vi.fn()
}));
vi.mock("@/components/ReAsideTable", () => ({
  dialogAsideTable: dialogAsideTableMock
}));

import { createColumnCellRender } from "@/utils/crud/createColumnCellRender";

/** 构造 cellRender（出版社关联列常用配置） */
const createRender = (crudOptionsOverride?: DynamicallyCrudOptions) =>
  createColumnCellRender({
    componentName: "PublisherView",
    createCrudOptions: (() => ({})) as any,
    fkField: "publisher",
    columnLabel: "publisher_name",
    crudOptionsOverride
  });

/** 取 vnode 内文本（原生标签 children 为数组） */
const textOf = (vnode: any) =>
  Array.isArray(vnode.children) ? vnode.children.join("") : vnode.children;

/** 取链接默认插槽内的首个节点（未解析组件时内联插槽已被展开为数组） */
const linkChild = (vnode: any) =>
  Array.isArray(vnode.children)
    ? vnode.children[0]
    : vnode.children.default()[0];

/** 点击最新一次渲染出的链接，返回传给详情弹窗的配置 */
const clickAndGetDialogOptions = (
  crudOptionsOverride?: DynamicallyCrudOptions
) => {
  const vnode: any = createRender(crudOptionsOverride)({
    row: { id: 5, publisher_name: "人民邮电出版社" }
  } as any);
  vnode.props.onClick();
  return dialogAsideTableMock.mock.calls.at(-1)![0];
};

describe("createColumnCellRender 关联列详情链接", () => {
  beforeEach(() => {
    dialogAsideTableMock.mockClear();
  });

  it("未关联（id 为 null/undefined）：渲染纯文本，不渲染可点击链接", () => {
    const render = createRender();
    for (const row of [
      { id: null, publisher_name: "A" },
      { publisher_name: "B" }
    ]) {
      const vnode: any = render({ row } as any);
      expect(vnode.type).toBe("span");
      expect(vnode.props?.onClick).toBeUndefined();
      expect(textOf(vnode)).toBe(row.publisher_name);
    }
    expect(dialogAsideTableMock).not.toHaveBeenCalled();
  });

  it("已关联：渲染详情链接（主色链接，文本沿用省略样式）", () => {
    const vnode: any = createRender()({
      row: { id: 5, publisher_name: "人民邮电出版社" }
    } as any);
    expect(vnode.type).toBe("el-link");
    expect(vnode.props.type).toBe("primary");
    expect(vnode.props.onClick).toBeTypeOf("function");
    expect(textOf(linkChild(vnode))).toBe("人民邮电出版社");
  });

  it("点击链接：以详情弹窗（dialogAsideTable）打开，携带模块标识与自动搜索", () => {
    const options: any = clickAndGetDialogOptions();
    expect(dialogAsideTableMock).toHaveBeenCalledTimes(1);
    expect(options.title).toBe("详情");
    expect(options.props.componentName).toBe("PublisherView");
    expect(options.props.autoSearch).toBe(true);
    expect(options.props.createCrudOptions).toBeTypeOf("function");
  });

  it("点击链接：固化详情默认覆盖配置（按外键精确过滤单条，隐藏查询区/动作条/勾选列/行操作）", () => {
    const { crudOptionsOverride } = clickAndGetDialogOptions().props;
    expect(crudOptionsOverride.search).toEqual({
      show: false,
      initialForm: { publisher__exact: 5 }
    });
    expect(crudOptionsOverride.form).toEqual({ initialForm: { publisher: 5 } });
    expect(crudOptionsOverride.actionbar).toEqual({ show: false });
    expect(crudOptionsOverride.rowHandle).toEqual({
      width: 80,
      buttons: { view: { show: false }, remove: { show: false } }
    });
    expect(crudOptionsOverride.columns.$checked.column.show).toBe(false);
  });

  it("调用方覆盖配置优先：覆盖默认值，未覆盖项保留默认值", () => {
    const { crudOptionsOverride } = clickAndGetDialogOptions({
      actionbar: { show: true },
      rowHandle: { buttons: { view: { show: true } } }
    }).props;
    expect(crudOptionsOverride.actionbar).toEqual({ show: true });
    expect(crudOptionsOverride.rowHandle.buttons.view).toEqual({ show: true });
    // 未覆盖项保留默认值
    expect(crudOptionsOverride.rowHandle.width).toBe(80);
    expect(crudOptionsOverride.rowHandle.buttons.remove).toEqual({
      show: false
    });
    expect(crudOptionsOverride.search.show).toBe(false);
  });

  it("多次点击：按当前行外键独立生成过滤条件（不同行互不影响）", () => {
    const render = createRender();
    (
      render({ row: { id: 1, publisher_name: "A" } } as any) as any
    ).props.onClick();
    (
      render({ row: { id: 2, publisher_name: "B" } } as any) as any
    ).props.onClick();
    const [first, second] = dialogAsideTableMock.mock.calls;
    expect(first[0].props.crudOptionsOverride.search.initialForm).toEqual({
      publisher__exact: 1
    });
    expect(second[0].props.crudOptionsOverride.search.initialForm).toEqual({
      publisher__exact: 2
    });
  });
});
