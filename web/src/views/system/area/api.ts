import { CreateApi } from "@/api/base";
import { dict, useMerge, type DictOptions } from "@fast-crud/fast-crud";
const { merge } = useMerge();

export const apiPrefix = "/api/system/area/";
export const api = {
  ...CreateApi(apiPrefix)
};

/**
 * 获取地区树形结构数据
 * @param max_level 最大层级数，默认为 4（省/市/县/乡四级）
 * @param options 可选的自定义配置选项，用于覆盖默认配置
 */
export const getAreaData = (max_level = 4, options?: DictOptions) => {
  const defaultOptions = {
    url: `${apiPrefix}get_tree/?max_level=${max_level}`,
    value: "code",
    label: "name",
    isTree: true,
    cache: true
  };
  const res = dict({ ...merge(defaultOptions, options) });
  res.loadDict();
  return res;
};
