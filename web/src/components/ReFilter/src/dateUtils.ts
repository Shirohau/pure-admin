import dayjs from "dayjs";

/** 单位日期范围（YYYY-MM-DD） */
export interface UnitDateRange {
  /** 单位起始日期 */
  start: string;
  /** 单位结束日期 */
  end: string;
}

/**
 * 将 date/week/month/year 单位值扩展为完整日期区间
 * （date 为单日；year/month 为整年/整月；week 为周一 ~ 周日），返回 null 表示值无效
 */
export const getUnitDateRange = (
  value: any,
  type: string
): UnitDateRange | null => {
  if (value === null || value === undefined || value === "") return null;
  const d = dayjs(value);
  if (!d.isValid()) return null;
  switch (type) {
    case "date":
      return {
        start: d.format("YYYY-MM-DD"),
        end: d.format("YYYY-MM-DD")
      };
    case "year":
      return {
        start: d.startOf("year").format("YYYY-MM-DD"),
        end: d.endOf("year").format("YYYY-MM-DD")
      };
    case "month":
      return {
        start: d.startOf("month").format("YYYY-MM-DD"),
        end: d.endOf("month").format("YYYY-MM-DD")
      };
    case "week":
      return {
        start: d.format("YYYY-MM-DD"),
        end: d.add(6, "day").format("YYYY-MM-DD")
      };
    default:
      return null;
  }
};
