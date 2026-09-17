/**
 * 表格选择器字典工厂
 * @description 生成 table-select 选择器 dict 配置（按 id 列表回显名称），
 */
import { dict } from "@fast-crud/fast-crud";

/** 表格选择器字典工厂配置 */
export interface CreateTableSelectDictOptions {
  /** 字典 label 字段（下拉回显字段，默认 "name"） */
  dictLabel: string;
  /** 字典查询字段（含自身展示字段与全部上级外键，默认 ["id", "name"]） */
  queryFields: string[];
  /** 模块 api（按 id 列表查询回显数据） */
  api: {
    GetList(params?: object): Promise<ApiResponse>;
  };
}

/**
 * 生成 table-select 选择器 dict 配置
 * @param {CreateTableSelectDictOptions} config - 模块 api 与字典字段配置
 * @returns {ReturnType<typeof dict>} 字典配置对象
 */
export function createTableSelectDict(config: CreateTableSelectDictOptions) {
  const { api, dictLabel = "name", queryFields = ["id", "name"] } = config;
  return dict({
    value: "id",
    label: dictLabel,
    /**
     * 根据值列表获取节点数据
     * @param {any[]} values - 需要查询的值数组（外键 ID 列表）
     * @returns {Promise<any>} 返回匹配的数据列表
     */
    getNodesByValues: async (values: any[]): Promise<any> => {
      const params = {
        id__in: values.join(","),
        limit: values.length,
        paginate: false,
        query: `{${queryFields.join(",")}}`
      };
      const { data } = (await api.GetList(params)) as ApiResponse;
      return data || [];
    }
  });
}
