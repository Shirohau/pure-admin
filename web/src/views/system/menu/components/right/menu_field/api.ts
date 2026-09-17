import { CreateApi } from "@/api/base";
import { http } from "@/utils/http";

export const apiPrefix = "/api/system/menufield/";
export const api = {
  ...CreateApi(apiPrefix),
  /**
   * 批量创建对象（自动匹配模型表：将模型表的全部字段批量写入菜单字段）
   * @param data 包含 app_model 与 menu_id 的数据对象
   * @returns 返回创建结果的Promise对象
   */
  async BatchCreateObj(data: object) {
    const res: ApiResponse = await http.post(`${apiPrefix}batch_create/`, {
      data
    });
    return res;
  },
  /**
   * 获取应用模型列表
   * @returns 返回应用模型数据的Promise对象
   */
  async GetAppModels(params: object) {
    const res: ApiResponse = await http.get(`${apiPrefix}app_models/`, {
      params
    });
    return res;
  },
  /**
   * 获取应用模型字段列表
   * @param params 查询参数对象
   * @returns 返回应用模型字段数据的Promise对象
   */
  async GetAppModelFields(params: object) {
    const res: ApiResponse = await http.get(`${apiPrefix}app_model_fields/`, {
      params
    });
    return res;
  }
};
