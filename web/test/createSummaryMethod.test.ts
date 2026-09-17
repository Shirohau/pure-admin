import { nextTick, type VNode } from "vue";
import { describe, expect, it, vi } from "vitest";
import {
  SUMMARY_AGGREGATE_FNS,
  TABLE_SUMMARY_KEY,
  createSummaryMethod,
  formatSummaryValue,
  normalizeSummary,
  pickSummaryNumbers,
  processSummaryFooter,
  resolveColumnValue
} from "@/utils/crud/createSummaryMethod";

/** 取单元格（VNode）内每行合计文本（.crud-summary-line 的文本） */
function cellTexts(cell: string | VNode): string[] {
  if (typeof cell === "string") return [cell];
  return ((cell.children ?? []) as any[]).map(line =>
    String(line?.children ?? "")
  );
}

/** 表格列（首列展示标签，其余列按 property 匹配 sumColumns） */
const COLUMNS = [
  { property: "name" },
  { property: "amount" },
  { property: "rate" },
  { property: "pages" }
];

describe("formatSummaryValue", () => {
  it("默认：千分位 + 最多保留 3 位小数", () => {
    expect(formatSummaryValue(1234.5678)).toBe("1,234.568");
  });

  it("integer：整数显示（无小数）", () => {
    expect(formatSummaryValue(1000.6, { type: "integer" })).toBe("1,001");
  });

  it("decimal + decimals：固定小数位补零", () => {
    expect(formatSummaryValue(1000.5, { type: "decimal", decimals: 2 })).toBe(
      "1,000.50"
    );
  });

  it("percent：值 ×100 且默认带 %", () => {
    expect(formatSummaryValue(0.1234, { type: "percent" })).toBe("12.34%");
    expect(formatSummaryValue(0.1234, { type: "percent", decimals: 1 })).toBe(
      "12.3%"
    );
  });

  it("thousands=false：不带千分位", () => {
    expect(formatSummaryValue(1234.5, { thousands: false })).toBe("1234.5");
  });

  it("unit：追加单位符号", () => {
    expect(formatSummaryValue(1000, { unit: " 元" })).toBe("1,000 元");
    expect(formatSummaryValue(9, { type: "integer", unit: " 件" })).toBe(
      "9 件"
    );
  });

  it("percent + 自定义 unit：覆盖默认 %", () => {
    expect(formatSummaryValue(0.5, { type: "percent", unit: " 个" })).toBe(
      "50 个"
    );
  });

  it("空字符串：原样显示", () => {
    expect(formatSummaryValue("")).toBe("");
  });

  it("非数字文本：原样显示", () => {
    expect(formatSummaryValue("暂无")).toBe("暂无");
  });

  it("数字字符串：正常格式化", () => {
    expect(formatSummaryValue("1234.5")).toBe("1,234.5");
  });

  it("负数：保留符号与千分位", () => {
    expect(formatSummaryValue(-1234.5)).toBe("-1,234.5");
  });
});

describe("pickSummaryNumbers", () => {
  it("跳过空值与非数字，保留数字与数字字符串", () => {
    const rows = [
      { v: 1 },
      { v: "2" },
      { v: "" },
      { v: null },
      { v: undefined },
      { v: "abc" },
      { v: 3.5 }
    ];
    expect(pickSummaryNumbers(rows, "v")).toEqual([1, 2, 3.5]);
  });

  it("字段缺失：视为空值跳过", () => {
    expect(pickSummaryNumbers([{}, { v: 1 }], "v")).toEqual([1]);
  });
});

describe("SUMMARY_AGGREGATE_FNS", () => {
  const rows = [{ v: 1 }, { v: "2" }, { v: "" }, { v: 4 }, { v: "abc" }];

  it("sum：有效值求和（跳过空值与非法文本）", () => {
    expect(SUMMARY_AGGREGATE_FNS.sum(rows, "v")).toBe(7);
  });

  it("sum：空数据显示 0", () => {
    expect(SUMMARY_AGGREGATE_FNS.sum([], "v")).toBe(0);
  });

  it("avg：除以有效值个数", () => {
    expect(SUMMARY_AGGREGATE_FNS.avg(rows, "v")).toBeCloseTo(7 / 3);
  });

  it("avg：无有效值显示空", () => {
    expect(SUMMARY_AGGREGATE_FNS.avg([{ v: "x" }], "v")).toBe("");
  });

  it("max / min：取有效值最值", () => {
    expect(SUMMARY_AGGREGATE_FNS.max(rows, "v")).toBe(4);
    expect(SUMMARY_AGGREGATE_FNS.min(rows, "v")).toBe(1);
  });

  it("max / min：无有效值显示空", () => {
    expect(SUMMARY_AGGREGATE_FNS.max([], "v")).toBe("");
    expect(SUMMARY_AGGREGATE_FNS.min([{ v: "" }], "v")).toBe("");
  });

  it("count：统计行数（不受值影响）", () => {
    expect(SUMMARY_AGGREGATE_FNS.count(rows, "v")).toBe(5);
  });
});

describe("normalizeSummary", () => {
  it("单行对象：补默认标签，整体作为 sums", () => {
    expect(normalizeSummary({ amount: 888 }, "合计")).toEqual([
      { label: "合计", sums: { amount: 888 } }
    ]);
  });

  it("多行数组：逐行 label + 平铺值", () => {
    const groups = normalizeSummary(
      [
        { label: "绩效A", total: 1 },
        { label: "绩效B", total: 2 }
      ],
      "合计"
    );
    expect(groups.map(group => group.label)).toEqual(["绩效A", "绩效B"]);
    expect(groups[0].sums).toEqual({ label: "绩效A", total: 1 });
  });

  it("数组项含 sums：原样使用", () => {
    const groups = normalizeSummary(
      [{ label: "A", sums: { total: 1 } }],
      "合计"
    );
    expect(groups[0].sums).toEqual({ total: 1 });
  });

  it("行标签缺失：回退默认标签", () => {
    const groups = normalizeSummary([{ total: 1 }], "合计");
    expect(groups[0].label).toBe("合计");
  });

  it("数组项含 rows：保留挂载", () => {
    const rows = [{ v: 1 }];
    const groups = normalizeSummary([{ label: "A", rows }], "合计");
    expect(groups[0].rows).toBe(rows);
  });
});

describe("resolveColumnValue", () => {
  const column = { property: "v" };

  it("sums 直传优先于前端计算", () => {
    const group = { label: "x", sums: { v: 99 }, rows: [{ v: 1 }] };
    expect(resolveColumnValue(group, column, { aggregate: "sum" })).toBe(99);
  });

  it("直传值为 0：正常返回（不被空值跳过）", () => {
    expect(resolveColumnValue({ label: "x", sums: { v: 0 } }, column, {})).toBe(
      0
    );
  });

  it("未直传且配置 aggregate：前端计算", () => {
    const group = { label: "x", rows: [{ v: 1 }, { v: 2 }] };
    expect(resolveColumnValue(group, column, { aggregate: "sum" })).toBe(3);
  });

  it("未直传且未配置 aggregate：默认前端求和", () => {
    expect(
      resolveColumnValue({ label: "x", rows: [{ v: 1 }, { v: 2 }] }, column, {})
    ).toBe(3);
  });

  it("source=backend：前端不计算，显示空（配了 aggregate 同样不计算）", () => {
    expect(
      resolveColumnValue({ label: "x", rows: [{ v: 1 }] }, column, {}, "backend")
    ).toBe("");
    expect(
      resolveColumnValue(
        { label: "x", rows: [{ v: 1 }] },
        column,
        { aggregate: "sum" },
        "backend"
      )
    ).toBe("");
  });

  it("source=backend 且直传值：照常返回直传值", () => {
    expect(
      resolveColumnValue(
        { label: "x", sums: { v: 9 }, rows: [{ v: 1 }] },
        column,
        {},
        "backend"
      )
    ).toBe(9);
  });

  it("无数据行：前端不计算，显示空", () => {
    expect(
      resolveColumnValue({ label: "x" }, column, { aggregate: "sum" })
    ).toBe("");
  });

  it("自定义 aggregate 函数：返回其计算结果", () => {
    const group = { label: "x", rows: [{ v: 1 }, { v: 2 }] };
    const config = { aggregate: (rows: any[]) => `${rows.length} 条` };
    expect(resolveColumnValue(group, column, config)).toBe("2 条");
  });

  it("自定义函数返回 null/undefined：显示空", () => {
    expect(
      resolveColumnValue({ label: "x", rows: [] }, column, {
        aggregate: () => null
      })
    ).toBe("");
    expect(
      resolveColumnValue({ label: "x", rows: [] }, column, {
        aggregate: () => undefined
      })
    ).toBe("");
  });
});

describe("processSummaryFooter", () => {
  /** 构造 el-table 结构（含数据行与表尾） */
  function buildTable() {
    const root = document.createElement("div");
    root.className = "el-table";
    root.innerHTML = `
      <div class="el-table__body">
        <table><tbody>
          <tr class="el-table__row">
            <td><div class="cell">a</div></td>
            <td><div class="cell">b</div></td>
            <td><div class="cell">c</div></td>
          </tr>
        </tbody></table>
      </div>
      <div class="el-table__footer">
        <table><tfoot>
          <tr>
            <td><div class="cell">合计</div></td>
            <td><div class="cell"><div class="crud-summary-line">1</div></div></td>
            <td><div class="cell"><div class="crud-summary-line">2</div></div></td>
          </tr>
        </tfoot></table>
      </div>
    `;
    return {
      root,
      tfoot: root.querySelector(".el-table__footer tfoot") as HTMLElement
    };
  }

  it("传入 tfoot：td 与 .cell 内边距归零", () => {
    const { tfoot } = buildTable();
    tfoot.querySelectorAll("td").forEach(td => (td.style.padding = "12px"));
    processSummaryFooter(tfoot, 1);
    tfoot
      .querySelectorAll("td")
      .forEach(td => expect(td.style.padding).toBe("0px"));
    tfoot
      .querySelectorAll(".cell")
      .forEach(cell => expect((cell as HTMLElement).style.padding).toBe("0px"));
  });

  it("传入表格根元素：自动定位表尾", () => {
    const { root, tfoot } = buildTable();
    processSummaryFooter(root, 1);
    expect(tfoot.querySelectorAll("td")[0].style.padding).toBe("0px");
  });

  it("auto 布局（表尾在 body 内）：同样生效", () => {
    const root = document.createElement("div");
    root.className = "el-table";
    root.innerHTML = `
      <div class="el-table__body">
        <table><tfoot>
          <tr>
            <td><div class="cell">合计</div></td>
            <td><div class="cell"><div class="crud-summary-line">1</div></div></td>
          </tr>
        </tfoot></table>
      </div>
    `;
    processSummaryFooter(root, 1);
    expect(root.querySelector<HTMLElement>("tfoot td")?.style.padding).toBe(
      "0px"
    );
  });

  it("firstCellSpan=2：首列 colSpan 合并并隐藏被合并单元格", () => {
    const { root, tfoot } = buildTable();
    processSummaryFooter(root, 2);
    const cells = tfoot.querySelectorAll("td");
    expect((cells[0] as HTMLTableCellElement).colSpan).toBe(2);
    expect(cells[1].style.display).toBe("none");
    expect(cells[2].style.display).not.toBe("none");
  });

  it("首格（合计标签）统一左对齐：不跟随第一列的居中 align", () => {
    const { root, tfoot } = buildTable();
    processSummaryFooter(root, 2);
    const firstTd = tfoot.querySelectorAll("td")[0] as HTMLElement;
    expect(firstTd.style.textAlign).toBe("left");
  });

  it("firstCellSpan=1（不合并）：首格同样左对齐", () => {
    const { tfoot } = buildTable();
    processSummaryFooter(tfoot, 1);
    const firstTd = tfoot.querySelectorAll("td")[0] as HTMLElement;
    expect(firstTd.style.textAlign).toBe("left");
  });

  it("firstCellSpan 超过列数：跳过合并", () => {
    const { tfoot } = buildTable();
    processSummaryFooter(tfoot, 9);
    const cells = tfoot.querySelectorAll("td");
    expect((cells[0] as HTMLTableCellElement).colSpan).toBe(1);
    expect(cells[1].style.display).not.toBe("none");
  });

  it("存在数据行：合计行高按实测数据行高度对齐", () => {
    const { root, tfoot } = buildTable();
    const dataCell = root.querySelector<HTMLElement>(
      ".el-table__body tr.el-table__row td"
    )!;
    Object.defineProperty(dataCell, "offsetHeight", {
      value: 44,
      configurable: true
    });
    processSummaryFooter(root, 1);
    tfoot.querySelectorAll(".crud-summary-line").forEach(line => {
      expect((line as HTMLElement).style.height).toBe("44px");
      expect((line as HTMLElement).style.lineHeight).toBe("44px");
    });
  });

  it("容器为空或无表尾行：静默返回不报错", () => {
    expect(() => processSummaryFooter(null, 2)).not.toThrow();
    expect(() => processSummaryFooter(undefined, 2)).not.toThrow();
    const empty = document.createElement("div");
    empty.innerHTML = `<div class="el-table__footer"><table><tfoot></tfoot></table></div>`;
    expect(() => processSummaryFooter(empty, 2)).not.toThrow();
  });
});

describe("createSummaryMethod", () => {
  it("数组简写：等效前端求和（默认配置），默认标签“合计”", () => {
    const method = createSummaryMethod({ sumColumns: ["pages"] });
    const cells = method({
      columns: COLUMNS,
      data: [{ pages: 1.6 }, { pages: 2 }]
    });
    expect(cellTexts(cells[0])).toEqual(["合计"]);
    expect(cellTexts(cells[1])).toEqual([""]); // 未配置列不显示
    expect(cellTexts(cells[3])).toEqual(["3.6"]); // 1.6 + 2
  });

  it("对象配置：逐列 aggregate 与 format（小数位/百分比/单位/整数）", () => {
    const method = createSummaryMethod({
      sumColumns: {
        amount: {
          aggregate: "sum",
          format: { type: "decimal", decimals: 2, unit: " 元" }
        },
        rate: { aggregate: "avg", format: { type: "percent", decimals: 1 } },
        pages: { aggregate: "sum", format: { type: "integer" } }
      }
    });
    const cells = method({
      columns: COLUMNS,
      data: [
        { amount: 1000.456, rate: 0.1234, pages: 1024.6 },
        { amount: 2000.544, rate: 0.2346, pages: 2048.4 }
      ]
    });
    expect(cellTexts(cells[1])).toEqual(["3,001.00 元"]);
    expect(cellTexts(cells[2])).toEqual(["17.9%"]);
    expect(cellTexts(cells[3])).toEqual(["3,073"]);
  });

  it("对象配置不配 aggregate：默认前端求和", () => {
    const method = createSummaryMethod({
      sumColumns: {
        amount: { format: { type: "integer" } },
        pages: { format: { type: "integer" } }
      }
    });
    const cells = method({
      columns: COLUMNS,
      data: [
        { amount: 1, pages: 1 },
        { amount: 2, pages: 2 }
      ]
    });
    expect(cellTexts(cells[1])).toEqual(["3"]); // 未配 aggregate → 默认 sum
    expect(cellTexts(cells[3])).toEqual(["3"]);
  });

  it("source=backend：整表前端不计算，仅显示后端直传值（未传为空）", () => {
    const method = createSummaryMethod({
      source: "backend",
      sumColumns: {
        amount: { format: { type: "integer" } },
        pages: { format: { type: "integer" } }
      }
    });
    const cells = method({
      columns: COLUMNS,
      data: [
        { amount: 1, pages: 1 },
        { amount: 2, pages: 2 }
      ]
    });
    expect(cellTexts(cells[1])).toEqual([""]); // 无直传 → 前端不兜底
    expect(cellTexts(cells[3])).toEqual([""]);
    const data: any[] = [{ amount: 1, pages: 1 }];
    data[TABLE_SUMMARY_KEY] = { amount: 88, pages: 99 };
    const presetCells = method({ columns: COLUMNS, data });
    expect(cellTexts(presetCells[1])).toEqual(["88"]);
    expect(cellTexts(presetCells[3])).toEqual(["99"]);
  });

  it("全局 format 生效，列级 format 优先覆盖", () => {
    const method = createSummaryMethod({
      sumColumns: {
        amount: { aggregate: "sum" },
        pages: { aggregate: "sum", format: { type: "integer" } }
      },
      format: { type: "decimal", decimals: 1 }
    });
    const cells = method({
      columns: COLUMNS,
      data: [
        { amount: 1000.2, pages: 3 },
        { amount: 0.1, pages: 2 }
      ]
    });
    expect(cellTexts(cells[1])).toEqual(["1,000.3"]);
    expect(cellTexts(cells[3])).toEqual(["5"]);
  });

  it("buildGroups：前端分组逐行渲染", () => {
    const buildGroups = vi.fn((data: any[]) => [
      { label: "组A", rows: data.filter(row => row.group === "A") },
      { label: "组B", rows: data.filter(row => row.group === "B") }
    ]);
    const method = createSummaryMethod({
      sumColumns: {
        amount: { aggregate: "sum", format: { type: "integer" } }
      },
      buildGroups
    });
    const cells = method({
      columns: COLUMNS,
      data: [
        { group: "A", amount: 1 },
        { group: "A", amount: 2 },
        { group: "B", amount: 5 }
      ]
    });
    expect(cellTexts(cells[0])).toEqual(["组A", "组B"]);
    expect(cellTexts(cells[1])).toEqual(["3", "5"]);
  });

  it("sumText 函数：按数据动态生成标签", () => {
    const method = createSummaryMethod({
      sumColumns: ["pages"],
      sumText: data => `共 ${data.length} 条`
    });
    const cells = method({
      columns: COLUMNS,
      data: [{ pages: 1 }, { pages: 2 }]
    });
    expect(cellTexts(cells[0])).toEqual(["共 2 条"]);
  });

  it("后端直传单行：自动读取挂载 summary，直传值优先于前端计算", () => {
    const method = createSummaryMethod({
      sumColumns: {
        amount: { aggregate: "sum", format: { type: "integer" } },
        pages: { format: { type: "integer" } }
      }
    });
    const data: any[] = [
      { amount: 1, pages: 1 },
      { amount: 2, pages: 2 }
    ];
    data[TABLE_SUMMARY_KEY] = { amount: 8888, pages: 999 };
    const cells = method({ columns: COLUMNS, data });
    expect(cellTexts(cells[0])).toEqual(["合计"]);
    expect(cellTexts(cells[1])).toEqual(["8,888"]); // 直传优先（前端 sum 为 3）
    expect(cellTexts(cells[3])).toEqual(["999"]); // 直传优先（前端 sum 为 3）
  });

  it("后端直传未覆盖列：未直传的列按默认 sum 前端兜底", () => {
    const method = createSummaryMethod({
      sumColumns: {
        amount: { aggregate: "sum", format: { type: "integer" } },
        rate: { format: { type: "decimal" } }
      }
    });
    const data: any[] = [
      { amount: 1, rate: 0.1 },
      { amount: 2, rate: 0.2 }
    ];
    data[TABLE_SUMMARY_KEY] = { pages: 7 };
    const cells = method({ columns: COLUMNS, data });
    expect(cellTexts(cells[1])).toEqual(["3"]); // 未直传 → 前端 sum
    expect(cellTexts(cells[2])).toEqual(["0.3"]); // 未直传 → 默认前端 sum
    expect(cellTexts(cells[3])).toEqual([""]); // 不在白名单 → 不显示
  });

  it("后端直传多行数组：逐行 label 与值", () => {
    const method = createSummaryMethod({
      sumColumns: { amount: { format: { type: "integer" } } }
    });
    const data: any[] = [];
    data[TABLE_SUMMARY_KEY] = [
      { label: "绩效A", amount: 1 },
      { label: "绩效B", amount: 2 }
    ];
    const cells = method({ columns: COLUMNS, data });
    expect(cellTexts(cells[0])).toEqual(["绩效A", "绩效B"]);
    expect(cellTexts(cells[1])).toEqual(["1", "2"]);
  });

  it("后端多行数组含 sums 字段：原样使用", () => {
    const method = createSummaryMethod({
      sumColumns: { amount: { format: { type: "integer" } } }
    });
    const data: any[] = [];
    data[TABLE_SUMMARY_KEY] = [{ label: "A", sums: { amount: 3 } }];
    const cells = method({ columns: COLUMNS, data });
    expect(cellTexts(cells[1])).toEqual(["3"]);
  });

  it("getSummary 手动配置优先于响应挂载", () => {
    const method = createSummaryMethod({
      sumColumns: { pages: { format: { type: "integer" } } },
      getSummary: () => ({ pages: 100 })
    });
    const data: any[] = [];
    data[TABLE_SUMMARY_KEY] = { pages: 999 };
    const cells = method({ columns: COLUMNS, data });
    expect(cellTexts(cells[3])).toEqual(["100"]);
  });

  it("空 summary（空对象/空数组）：回退前端计算", () => {
    const method = createSummaryMethod({
      sumColumns: { pages: { aggregate: "sum", format: { type: "integer" } } }
    });
    const data: any[] = [{ pages: 5 }];
    data[TABLE_SUMMARY_KEY] = {};
    expect(cellTexts(method({ columns: COLUMNS, data })[3])).toEqual(["5"]);
    data[TABLE_SUMMARY_KEY] = [];
    expect(cellTexts(method({ columns: COLUMNS, data })[3])).toEqual(["5"]);
  });

  it("后端 summary 非空：buildGroups 不生效", () => {
    const buildGroups = vi.fn(() => [{ label: "组A", rows: [] }]);
    const method = createSummaryMethod({ sumColumns: ["pages"], buildGroups });
    const data: any[] = [{ pages: 3 }];
    data[TABLE_SUMMARY_KEY] = { pages: 3 };
    const cells = method({ columns: COLUMNS, data });
    expect(buildGroups).not.toHaveBeenCalled();
    expect(cellTexts(cells[0])).toEqual(["合计"]);
  });

  it("空数据：sum 显示 0、avg 显示空", () => {
    const method = createSummaryMethod({
      sumColumns: {
        amount: { aggregate: "sum" },
        rate: { aggregate: "avg" }
      }
    });
    const cells = method({ columns: COLUMNS, data: [] });
    expect(cellTexts(cells[1])).toEqual(["0"]);
    expect(cellTexts(cells[2])).toEqual([""]);
  });

  it("内置 count 与自定义 aggregate 函数", () => {
    const countMethod = createSummaryMethod({
      sumColumns: { pages: { aggregate: "count" } }
    });
    expect(
      cellTexts(
        countMethod({
          columns: COLUMNS,
          data: [{ pages: 1 }, {}, { pages: "" }]
        })[3]
      )
    ).toEqual(["3"]);

    const fnMethod = createSummaryMethod({
      sumColumns: {
        pages: { aggregate: rows => `${rows.length * 2} 条` }
      }
    });
    expect(
      cellTexts(fnMethod({ columns: COLUMNS, data: [{ pages: 1 }, {}] })[3])
    ).toEqual(["4 条"]);
  });

  it("后端直传非数字文本：原样显示", () => {
    const method = createSummaryMethod({
      sumColumns: { pages: { format: { type: "integer" } } }
    });
    const data: any[] = [];
    data[TABLE_SUMMARY_KEY] = { pages: "暂无" };
    expect(cellTexts(method({ columns: COLUMNS, data })[3])).toEqual(["暂无"]);
  });

  it("单元格结构：.crud-summary-cell / .crud-summary-line 与 title", () => {
    const method = createSummaryMethod({
      sumColumns: { pages: { aggregate: "sum", format: { type: "integer" } } }
    });
    const cells = method({ columns: COLUMNS, data: [{ pages: 3 }] });
    const cell = cells[3] as VNode;
    expect(cell.props?.class).toBe("crud-summary-cell");
    const line = (cell.children as any[])[0] as VNode;
    expect(line.props?.class).toBe("crud-summary-line");
    expect(line.props?.title).toBe("3");
  });

  it("空文本单元格：title 为空", () => {
    const method = createSummaryMethod({ sumColumns: ["pages"] });
    const cells = method({ columns: COLUMNS, data: [] });
    const cell = cells[1] as VNode; // amount 未配置 → 空文本
    const line = (cell.children as any[])[0] as VNode;
    expect(line.props?.title).toBeUndefined();
  });

  it("样式注入：重复渲染仅注入一次", () => {
    document.getElementById("crud-summary-method-style")?.remove();
    const method = createSummaryMethod({ sumColumns: ["pages"] });
    method({ columns: COLUMNS, data: [] });
    method({ columns: COLUMNS, data: [] });
    expect(document.querySelectorAll("#crud-summary-method-style").length).toBe(
      1
    );
  });

  it("getTableContainer：nextTick 后回调兜底定位", async () => {
    const container = document.createElement("div");
    const getTableContainer = vi.fn(() => container);
    const method = createSummaryMethod({
      sumColumns: ["pages"],
      getTableContainer
    });
    method({ columns: COLUMNS, data: [] });
    await nextTick();
    expect(getTableContainer).toHaveBeenCalled();
  });
});
