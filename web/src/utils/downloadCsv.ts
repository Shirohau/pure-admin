/**
 * CSV 导出公共工具（RFC 4180 转义、CRLF 行分隔、UTF-8 BOM，Excel 兼容）
 * 纯前端本地生成下载，不依赖第三方库
 * 用法：exportCsv([{ key: "name", title: "名称" }], rows, { filename: "导出数据" })
 */

/** CSV 行分隔符（CRLF，兼容 Excel） */
const CSV_LINE_BREAK = "\r\n";
/** UTF-8 BOM（带 BOM 的 CSV 在 Excel 中正确识别中文） */
const UTF8_BOM = "\uFEFF";

/** CSV 导出列（key 为行对象取值字段，title 为导出表头） */
export interface CsvColumn {
  /** 字段名（行对象取值键） */
  key: string;
  /** 列标题（导出表头） */
  title: string;
}

/** CSV 导出配置 */
export interface CsvExportOptions {
  /** 文件名（不含扩展名），默认"导出数据" */
  filename?: string;
  /** 数据分隔符，默认 "," */
  separator?: string;
  /** 每个单元格是否加引号，默认 false */
  quoted?: boolean;
}

/** CSV 单元格转义：含分隔符/引号/换行时以双引号包裹（内部引号翻倍） */
export const escapeCsvCell = (
  value: any,
  separator = ",",
  quoted = false
): string => {
  const text =
    value === null || value === undefined
      ? ""
      : typeof value === "object"
        ? JSON.stringify(value)
        : String(value);
  if (
    quoted ||
    text.includes(separator) ||
    text.includes('"') ||
    text.includes("\n") ||
    text.includes("\r")
  ) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
};

/** 生成 CSV 文本（含表头行；行以 CRLF 分隔，值直接使用源数据原始值） */
export const buildCsvText = (
  columns: CsvColumn[],
  rows: any[],
  options?: Pick<CsvExportOptions, "separator" | "quoted">
): string => {
  const { separator = ",", quoted = false } = options ?? {};
  const lines = [
    columns
      .map(column => escapeCsvCell(column.title, separator, quoted))
      .join(separator)
  ];
  for (const row of rows) {
    const cells = columns.map(({ key }) =>
      escapeCsvCell(row?.[key], separator, quoted)
    );
    lines.push(cells.join(separator));
  }
  return lines.join(CSV_LINE_BREAK);
};

/** 触发浏览器下载 CSV 文件（UTF-8 BOM 头，本地生成不请求后端） */
export const downloadCsv = (filename: string, csvText: string) => {
  const blob = new Blob([UTF8_BOM + csvText], {
    type: "text/csv;charset=utf-8;"
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${filename}.csv`;
  link.style.display = "none";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

/** 一步导出 CSV：生成文本并触发浏览器下载（filename 缺省"导出数据"） */
export const exportCsv = (
  columns: CsvColumn[],
  rows: any[],
  options?: CsvExportOptions
) => {
  downloadCsv(
    options?.filename || "导出数据",
    buildCsvText(columns, rows, options)
  );
};
