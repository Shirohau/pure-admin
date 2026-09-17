import { getCurrentInstance, h, nextTick, type VNode } from "vue";
import XEUtils from "xe-utils";

/**
 * 表尾合计工具：生成 el-table / fast-crud 的 summaryMethod
 *
 * 职责分工：
 * - 数据来源：后端直传（响应 summary 自动挂载 / getSummary 手动）优先，前端兜底（buildGroups 分组 / 当前页整体）
 * - 列计算：整表可配 source（默认 frontend 前端合计，可配 backend 仅后端传值）、逐列可配 aggregate（默认 sum，支持 sum/avg/max/min/count 或自定义函数）
 * - 显示格式：列级 format 优先于全局 format，控制整数/小数/百分比、千分位、小数位、单位
 */

/* ---------- 常量 ---------- */

/**
 * 后端 summary 响应挂载键：全局 transformRes 把接口响应的 summary 挂到 records 数组上
 * （fast-crud 只消费 records/currentPage/pageSize/total，其余字段会被丢弃），
 * 表尾渲染时从 data 自动读取，调用方无需手动接住
 */
export const TABLE_SUMMARY_KEY = "__fsSummary";

/* ---------- 类型 ---------- */

/** 表尾一行合计：label + 值来源（sums 直传优先；未直传的列按 source 决定是否前端计算，backend 列与无数据行显示空） */
export interface SummaryGroup {
  /** 首列标签（多业绩场景逐行不同，如各绩效名称） */
  label: string;
  /** 后端直传值：列 property → 合计值（分页场景全量合计；未直传的列回退前端计算） */
  sums?: Record<string, number | string>;
  /** 前端计算的数据行（该行合计归属的行；分页场景通常不传） */
  rows?: any[];
}

/** 合计值来源：frontend 前端合计（默认）/ backend 后端传值 */
export type SummarySource = "frontend" | "backend";

/** 内置计算方式：sum 求和 / avg 平均值 / max 最大值 / min 最小值 / count 计数（行数） */
export type SummaryAggregate = "sum" | "avg" | "max" | "min" | "count";

/** 自定义计算方式：按分组行与列字段返回合计值（返回空显示为空） */
export type SummaryAggregateFn = (
  rows: any[],
  property: string
) => number | string | null | undefined;

/** 数值显示配置：整数/小数/百分比、千分位、小数位、单位符号（内部统一由 formatSummaryValue 执行，字段均可选） */
export interface SummaryFormatConfig {
  /** 数值类型：integer 整数 / decimal 小数（默认）/ percent 百分比（值 ×100 后显示） */
  type?: "integer" | "decimal" | "percent";
  /** 千分位分隔（默认 true） */
  thousands?: boolean;
  /** 小数位（默认按原值，最多保留 3 位；type=integer 时固定 0） */
  decimals?: number;
  /** 单位符号（追加在值末尾，如 " 元"；percent 默认 "%"） */
  unit?: string;
}

/** 单列合计配置 */
export interface SumColumnConfig {
  /**
   * 前端计算方式（source 为 frontend 时生效，默认 "sum"）：内置 sum/avg/max/min/count 或自定义函数
   * - 后端直传了该列合计值时以直传为准（仍按 format 格式化）
   */
  aggregate?: SummaryAggregate | SummaryAggregateFn;
  /** 列级数值格式：{ type, thousands, decimals, unit }，如 { type: "integer" }、{ type: "percent", decimals: 1 }（优先于全局 format） */
  format?: SummaryFormatConfig;
}

/** 合计列配置：对象逐列配置计算方式与格式，或字符串数组简写（等效每列默认配置：前端求和） */
export type SummaryColumns = string[] | Record<string, SumColumnConfig>;

/** createSummaryMethod 配置 */
export interface CreateSummaryMethodOptions {
  /** 合计白名单列：数组为默认配置简写（等效前端求和）；对象逐列配置：aggregate 定算法（默认 sum）、format 定显示 */
  sumColumns: SummaryColumns;
  /**
   * 整表合计来源（默认 "frontend"）：
   * - "frontend"：前端合计（未直传的列按 aggregate 计算，默认 sum；后端直传值仍优先）
   * - "backend"：仅后端传值（前端不计算，未传显示空，aggregate 不生效）
   */
  source?: SummarySource;
  /** 前端分组：按当前表格数据拆分多行（后端 summary 非空时不生效） */
  buildGroups?: (data: any[]) => SummaryGroup[];
  /**
   * 手动接入后端合计（兜底，一般无需配置——响应中的 summary 已自动挂载读取，见 TABLE_SUMMARY_KEY）：
   * - 单行：键值对象，如 { total_weight: 999, amount: 888 }，标签取 sumText
   * - 多行：数组，如 [{ label: "绩效A", total_weight: 1 }]，标签逐行取自 label
   * - 适用场景：页面自定义了 transformRes，或需对 summary 做变换；返回空时回退前端
   */
  getSummary?: () =>
    | Record<string, any>[]
    | Record<string, number | string>
    | null
    | undefined;
  /** 默认单行首列标签（默认"合计"）：常量或动态函数；多行标签由各行自行提供 */
  sumText?: string | ((data: any[]) => string);
  /** 全局数值格式配置（列级 format 优先；均未配置时数值默认千分位、非数字原样） */
  format?: SummaryFormatConfig;
  /** 首列跨列数（默认 1 不合并） */
  firstCellSpan?: number;
  /** 表尾容器兜底（一般无需传，工具自动定位表尾） */
  getTableContainer?: () => HTMLElement | null | undefined;
}

/* ---------- 数值格式化 ---------- */

/** 数值格式化：整数/小数/百分比（×100）、千分位、小数位、单位（空值与非法数字原样；不传配置默认千分位） */
export function formatSummaryValue(
  value: number | string,
  config?: SummaryFormatConfig
): string {
  if (value === "") return "";
  const num = Number(value);
  if (Number.isNaN(num)) return String(value);
  const type = config?.type ?? "decimal";
  const decimals = type === "integer" ? 0 : config?.decimals;
  const text = (num * (type === "percent" ? 100 : 1)).toLocaleString(
    undefined,
    {
      useGrouping: config?.thousands !== false,
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }
  );
  return `${text}${config?.unit ?? (type === "percent" ? "%" : "")}`;
}

/* ---------- 聚合计算 ---------- */

/** 取列有效数值（跳过空值与非数字文本）：聚合计算共用 */
export function pickSummaryNumbers(rows: any[], property: string): number[] {
  return rows
    .map(row => row[property])
    .filter(value => value !== "" && value !== null && value !== undefined)
    .map(value => Number(value))
    .filter(value => !Number.isNaN(value));
}

/** 内置计算方式：sum/avg/max/min 基于列有效数值计算（avg/max/min 无有效值显示空），count 统计行数 */
export const SUMMARY_AGGREGATE_FNS: Record<
  SummaryAggregate,
  (rows: any[], property: string) => number | string
> = {
  sum: (rows, property) => XEUtils.sum(pickSummaryNumbers(rows, property)),
  avg: (rows, property) => {
    const nums = pickSummaryNumbers(rows, property);
    return nums.length ? XEUtils.sum(nums) / nums.length : "";
  },
  max: (rows, property) => {
    const nums = pickSummaryNumbers(rows, property);
    return nums.length ? nums.reduce((a, b) => Math.max(a, b)) : "";
  },
  min: (rows, property) => {
    const nums = pickSummaryNumbers(rows, property);
    return nums.length ? nums.reduce((a, b) => Math.min(a, b)) : "";
  },
  count: rows => rows.length
};

/* ---------- 合计行解析 ---------- */

/** 后端 summary 归一化：单行对象补默认标签；数组逐项转 { label, sums }（已含 sums 的原样使用） */
export function normalizeSummary(
  summary: Record<string, any>[] | Record<string, number | string>,
  fallbackLabel: string
): SummaryGroup[] {
  const toGroup = (item: Record<string, any>): SummaryGroup => ({
    label: String(item.label ?? fallbackLabel),
    sums: item.sums ?? item,
    rows: item.rows
  });
  return Array.isArray(summary)
    ? summary.map(toGroup)
    : [{ label: fallbackLabel, sums: summary }];
}

/** 取合计行某列值：sums 直传优先；未直传时 source（默认 frontend）为 frontend 的列按 aggregate（默认 sum）前端计算，backend 显示空 */
export function resolveColumnValue(
  group: SummaryGroup,
  column: any,
  config: SumColumnConfig,
  source: SummarySource = "frontend"
): number | string {
  const preset = group.sums?.[column.property];
  if (preset !== undefined && preset !== null) {
    return preset;
  }
  // source=backend（整表仅后端传值）或无数据行：前端不计算，显示空
  if (source === "backend" || !group.rows) {
    return "";
  }
  const aggregate = config.aggregate ?? "sum";
  return typeof aggregate === "function"
    ? (aggregate(group.rows, column.property) ?? "")
    : SUMMARY_AGGREGATE_FNS[aggregate](group.rows, column.property);
}

/* ---------- 渲染 ---------- */

/** 多行合计样式：每行与数据行单元格等高（40px 仅为兜底，渲染后按实测高度覆盖），非末行绘制分隔线 */
const SUMMARY_STYLE_ID = "crud-summary-method-style";
const SUMMARY_STYLE = `
.crud-summary-line {
  box-sizing: border-box;
  height: 40px;
  line-height: 40px;
  padding: 0 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.crud-summary-line:not(:last-child) {
  box-shadow: inset 0 -1px 0 var(--el-table-border-color);
}
`;

/** 注入多行合计样式（幂等，仅一次） */
function ensureSummaryStyle() {
  if (
    typeof document === "undefined" ||
    document.getElementById(SUMMARY_STYLE_ID)
  ) {
    return;
  }
  const style = document.createElement("style");
  style.id = SUMMARY_STYLE_ID;
  style.textContent = SUMMARY_STYLE;
  document.head.appendChild(style);
}

/** 渲染合计单元格：每个合计行一个 .crud-summary-line */
function renderSummaryCell(lines: string[]): VNode {
  return h(
    "div",
    { class: "crud-summary-cell" },
    lines.map((text, index) =>
      h(
        "div",
        { class: "crud-summary-line", key: index, title: text || undefined },
        text
      )
    )
  );
}

/* ---------- 表尾 DOM 后处理 ---------- */

/**
 * 表尾渲染后处理（Element Plus 表尾不支持 colspan 配置，只能渲染后操作 DOM）：
 * td 与 .cell 内边距归零、合计标签列左对齐、合计行高对齐数据行、首列设置 colSpan 并隐藏被合并的后续 td
 * @param container - 表尾 tfoot（自动获取）或表格根元素（兜底）
 * @param firstCellSpan - 首列跨列数
 */
export function processSummaryFooter(
  container: HTMLElement | null | undefined,
  firstCellSpan: number
) {
  if (!container) {
    return;
  }
  // fixed 布局表尾在 .el-table__footer，auto 布局在 .el-table__body
  const tfoot =
    container.tagName === "TFOOT"
      ? container
      : container.querySelector<HTMLElement>(
          ".el-table__footer tfoot, .el-table__body tfoot"
        );
  const row = tfoot?.querySelector<HTMLElement>("tr");
  const cells = Array.from(row?.children ?? []) as HTMLElement[];
  if (!cells.length) {
    return;
  }
  // 内边距归零：单元格内边距由 .crud-summary-line 接管
  for (const td of cells) {
    td.style.padding = "0";
    const cell = td.querySelector<HTMLElement>(".cell");
    if (cell) {
      cell.style.padding = "0";
    }
  }
  // 合计标签（首格）统一左对齐：不跟随第一列 align（如居中的选择列会让标签居中）
  cells[0].style.textAlign = "left";
  // 合计行与数据行等高：实测首个数据行单元格高度（自动适配表格 size 与自定义行高；无数据行时保持样式兜底）
  const cellHeight = tfoot
    ?.closest(".el-table")
    ?.querySelector<HTMLElement>(
      ".el-table__body tbody tr.el-table__row td"
    )?.offsetHeight;
  const lines = tfoot?.querySelectorAll<HTMLElement>(".crud-summary-line");
  if (cellHeight && lines) {
    lines.forEach(line => {
      line.style.height = `${cellHeight}px`;
      line.style.lineHeight = `${cellHeight}px`;
    });
  }
  // 首列跨列：列数不足时跳过
  if (firstCellSpan <= 1 || cells.length <= firstCellSpan) {
    return;
  }
  (cells[0] as HTMLTableCellElement).colSpan = firstCellSpan;
  for (let index = 1; index < firstCellSpan; index++) {
    cells[index].style.display = "none";
  }
}

/* ---------- 主入口 ---------- */

/**
 * 创建表尾合计方法（生成 el-table / fast-crud 的 summaryMethod）
 *
 * 合计行来源优先级：getSummary（手动兜底）> 后端 summary（响应自动挂载，非空时）> buildGroups（前端分组）> 默认单行（前端按当前页求和）
 *
 * @example
 * ```ts
 * // 1. 前端单行合计（默认）：按当前页数据求和；数组为简写（等效每列默认配置：前端求和）
 * createSummaryMethod({ sumColumns: ["total_weight", "amount"] })
 *
 * // 1.1 逐列配置：aggregate 定算法（默认 "sum" 前端求和）、format 定显示
 * createSummaryMethod({
 *   sumColumns: {
 *     amount: { format: { type: "decimal", decimals: 2, unit: " 元" } }, // 金额：前端求和（默认），后端直传值始终优先
 *     rate: { aggregate: "avg", format: { type: "percent", decimals: 1 } }, // 占比：前端平均，×100 显示如 12.5%
 *     pages: { format: { type: "integer", thousands: false } } // 页数：前端求和，整数不带千分位
 *   }
 * })
 *
 * // 2. 前端多行合计：buildGroups 按数据分组，每组一行（如多绩效来源）
 * createSummaryMethod({
 *   sumColumns: ["total_weight", "amount"],
 *   buildGroups: data =>
 *     sources.map(source => ({
 *       label: source.name,
 *       rows: data.filter(row => row.source_id === source.id)
 *     })),
 *   firstCellSpan: 2
 * })
 *
 * // 3. 后端直传合计（分页场景全量合计）：pageRequest 返回体带 summary 即自动生效，无需配置。
 * //    标准页面（pageRequest 原样返回接口响应）零代码；自定义返回体的页面多加一个字段：
 * //    return { data, paginated, summary }（summary 形如 { total_weight: 999, amount: 888 }）
 * createSummaryMethod({ sumColumns: ["total_weight", "amount"] })
 *
 * // 4. 后端多行合计：summary 为数组（每项 label + 各列值）时自动逐行渲染
 * //    形如 [{ label: "绩效A", total_weight: 1 }, { label: "绩效B", total_weight: 2 }]
 * //    后端建议直接用 label 字段；字段名不同先映射再返回，如 { label: s.category_name, ...s }
 *
 * // 5. 手动兜底：页面自定义了 transformRes 或需变换 summary 时用 getSummary
 * createSummaryMethod({
 *   sumColumns: ["total_weight", "amount"],
 *   getSummary: () => summary.value
 * })
 *
 * // 6. 整表后端传值：source: "backend" 时全部列前端不计算，仅显示后端直传值（未传显示空）
 * createSummaryMethod({
 *   source: "backend",
 *   sumColumns: ["total_weight", "amount"]
 * })
 * ```
 */
export function createSummaryMethod(options: CreateSummaryMethodOptions) {
  const {
    sumColumns,
    source = "frontend",
    buildGroups,
    getSummary,
    sumText = "合计",
    format,
    firstCellSpan = 1,
    getTableContainer
  } = options;

  // 列配置归一化：数组简写 → 前端求和（source/aggregate 全默认）；Map 查询避免与列 property 的原型属性冲突
  const columnConfigs = new Map<string, SumColumnConfig>(
    Array.isArray(sumColumns)
      ? sumColumns.map(property => [property, { aggregate: "sum" }] as const)
      : Object.entries(sumColumns)
  );

  /** 默认标签（支持动态函数，每次渲染求值） */
  const resolveLabel = (data: any[]) =>
    typeof sumText === "function" ? sumText(data) : sumText;

  /** 解析合计行：手动 getSummary 优先 → 响应挂载的 summary → buildGroups → 默认单行 */
  const resolveGroups = (data: any[]): SummaryGroup[] => {
    // getSummary 为显式配置优先；其次读后端响应自动挂载的 summary（见 TABLE_SUMMARY_KEY）
    const summary = getSummary?.() ?? (data as any)?.[TABLE_SUMMARY_KEY];
    // 后端合计非空时优先直传（单行对象或多行数组）
    if (
      summary &&
      (Array.isArray(summary)
        ? summary.length > 0
        : Object.keys(summary).length > 0)
    ) {
      const groups = normalizeSummary(summary, resolveLabel(data));
      // 单行合计挂当前数据行：source 为 frontend 时未直传的列回退前端计算
      if (!Array.isArray(summary) && groups[0]) {
        groups[0].rows = data;
      }
      return groups;
    }
    // 空值回退前端：buildGroups 多行或默认整表一行
    return buildGroups
      ? buildGroups(data)
      : [{ label: resolveLabel(data), rows: data }];
  };

  return ({ columns, data }: { columns: any[]; data: any[] }) => {
    ensureSummaryStyle();
    const groups = resolveGroups(data);
    const sums: (string | VNode)[] = [];
    columns.forEach((column: any, index: number) => {
      const config = columnConfigs.get(column.property);
      if (index === 0) {
        sums[index] = renderSummaryCell(groups.map(group => group.label));
      } else if (config) {
        sums[index] = renderSummaryCell(
          groups.map(group =>
            formatSummaryValue(
              resolveColumnValue(group, column, config, source),
              config.format ?? format
            )
          )
        );
      } else {
        sums[index] = renderSummaryCell(groups.map(() => ""));
      }
    });
    // summaryMethod 处于 ElTableFooter 渲染中，getCurrentInstance() 即表尾组件实例，
    // nextTick 后其 $el 为标准 tfoot，可精确定位本次渲染的表尾行
    const footerInstance = getCurrentInstance();
    nextTick(() => {
      const footerEl = footerInstance?.proxy?.$el as
        | HTMLElement
        | null
        | undefined;
      processSummaryFooter(footerEl ?? getTableContainer?.(), firstCellSpan);
    });
    return sums;
  };
}
