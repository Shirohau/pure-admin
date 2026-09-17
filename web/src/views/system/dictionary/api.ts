import { CreateApi } from "@/api/base";
import { http } from "@/utils/http";

import { dict, type DictOptions } from "@fast-crud/fast-crud";

export const apiPrefix = "/api/system/dictionary/";
export const api = {
  ...CreateApi(apiPrefix),
  MoveObj(id: number, direction?: string) {
    return http.request("get", `${apiPrefix}${id}/move/`, {
      params: { direction }
    });
  }
};
/**
 * 获取字典项数据
 */
export const getDictData = (
  parentValue: string,
  dict_options?: DictOptions
) => {
  const res = dict({
    url: `${apiPrefix}?parent_value=${parentValue}&status=true&query={label,value,color,children}`,
    ...dict_options
  });
  res.loadDict();
  return res;
};
