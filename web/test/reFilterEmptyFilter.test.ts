import { describe, expect, it } from "vitest";
import {
  parseIsnullFlag,
  resolveIsnullLabel,
  resolveNextEmptyMode,
  toIsnullResult
} from "@/components/ReFilter/src/emptyFilter";

describe("ReFilter 空值筛选语义（emptyFilter）", () => {
  describe("resolveNextEmptyMode 勾选标签切换（互斥 + 可取消）", () => {
    it("未选中时点击标签：选中该模式", () => {
      expect(resolveNextEmptyMode("", "isnull")).toBe("isnull");
      expect(resolveNextEmptyMode("", "notnull")).toBe("notnull");
      expect(resolveNextEmptyMode(undefined, "isnull")).toBe("isnull");
    });

    it("点击已选中的标签：取消勾选（返回空模式）", () => {
      expect(resolveNextEmptyMode("isnull", "isnull")).toBe("");
      expect(resolveNextEmptyMode("notnull", "notnull")).toBe("");
    });

    it("点击另一标签：互斥切换（不同时选中）", () => {
      expect(resolveNextEmptyMode("isnull", "notnull")).toBe("notnull");
      expect(resolveNextEmptyMode("notnull", "isnull")).toBe("isnull");
    });

    it("切换后仅存在单一模式：不会出现同时选中的状态", () => {
      // 连续操作：为空 → 不为空 → 取消 → 为空
      let mode = resolveNextEmptyMode("", "isnull");
      expect(mode).toBe("isnull");
      mode = resolveNextEmptyMode(mode, "notnull");
      expect(mode).toBe("notnull");
      mode = resolveNextEmptyMode(mode, "notnull");
      expect(mode).toBe("");
      mode = resolveNextEmptyMode(mode, "isnull");
      expect(mode).toBe("isnull");
    });

    it("round-trip：切换结果可直接提交 isnull 荷载", () => {
      const mode = resolveNextEmptyMode("", "notnull");
      expect(mode).not.toBe("");
      expect(toIsnullResult(mode as "isnull" | "notnull")).toEqual({
        cond1Operator: "isnull",
        cond1Value: false
      });
    });
  });
  describe("toIsnullResult 提交荷载", () => {
    it("为空：提交 isnull=true（NULL + 空字符串）", () => {
      expect(toIsnullResult("isnull")).toEqual({
        cond1Operator: "isnull",
        cond1Value: true
      });
    });

    it("不为空：提交 isnull=false（非 NULL 且非空字符串）", () => {
      expect(toIsnullResult("notnull")).toEqual({
        cond1Operator: "isnull",
        cond1Value: false
      });
    });

    it("两种模式操作符均为 isnull（后端否定语义由值区分）", () => {
      expect(toIsnullResult("isnull").cond1Operator).toBe("isnull");
      expect(toIsnullResult("notnull").cond1Operator).toBe("isnull");
    });
  });

  describe("parseIsnullFlag 值解析（与后端 parse_isnull_flag 对齐）", () => {
    it("布尔值直接返回", () => {
      expect(parseIsnullFlag(true)).toBe(true);
      expect(parseIsnullFlag(false)).toBe(false);
    });

    it("真值字符串：true / 1 / 是（大小写不敏感）", () => {
      expect(parseIsnullFlag("true")).toBe(true);
      expect(parseIsnullFlag("True")).toBe(true);
      expect(parseIsnullFlag("1")).toBe(true);
      expect(parseIsnullFlag("是")).toBe(true);
    });

    it("其他值均视为不为空（false / 0 / 否 / 空串 / 空值）", () => {
      expect(parseIsnullFlag("false")).toBe(false);
      expect(parseIsnullFlag("0")).toBe(false);
      expect(parseIsnullFlag("否")).toBe(false);
      expect(parseIsnullFlag("")).toBe(false);
      expect(parseIsnullFlag(undefined)).toBe(false);
      expect(parseIsnullFlag(null)).toBe(false);
    });
  });

  describe("resolveIsnullLabel 标签文案", () => {
    it("真值 → 为空", () => {
      expect(resolveIsnullLabel(true)).toBe("为空");
      expect(resolveIsnullLabel("true")).toBe("为空");
    });

    it("假值 → 不为空", () => {
      expect(resolveIsnullLabel(false)).toBe("不为空");
      expect(resolveIsnullLabel("false")).toBe("不为空");
    });

    it("round-trip：提交值与标签文案一一对应", () => {
      expect(resolveIsnullLabel(toIsnullResult("isnull").cond1Value)).toBe(
        "为空"
      );
      expect(resolveIsnullLabel(toIsnullResult("notnull").cond1Value)).toBe(
        "不为空"
      );
    });
  });
});
