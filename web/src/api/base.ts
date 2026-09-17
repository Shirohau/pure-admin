import { http } from "@/utils/http";
import { ElMessage } from "element-plus";

export function CreateApi(apiPrefix: string) {
  return {
    /**
     * 列表
     * @param params 查询参数
     * @returns 接口请求结果
     */
    async GetList(params?: object) {
      const res: ApiResponse = await http.request("get", apiPrefix, { params });
      return res;
    },
    /**
     * 详情
     * @param id ID
     * @returns 接口请求结果
     */
    async GetObj(id: number) {
      const res: ApiResponse = await http.request("get", `${apiPrefix}${id}/`);
      return res;
    },
    /**
     * 创建
     * @param data 菜单数据对象
     * @returns 接口请求结果
     */
    async CreateObj(data: object, msg: boolean = true) {
      const res: ApiResponse = await http.request("post", apiPrefix, {
        data
      });
      if (msg) ElMessage({ message: res.message, type: "success" });
      return res;
    },
    /**
     * 更新
     * @param id ID
     * @param data 数据对象
     * @returns 接口请求结果
     */
    async UpdateObj(id: number, data: object, msg: boolean = true) {
      const res: ApiResponse = await http.request("put", `${apiPrefix}${id}/`, {
        data
      });
      if (msg) ElMessage({ message: res.message, type: "success" });
      return res;
    },
    /**
     * 删除
     * @param id ID
     * @returns 接口请求结果
     */
    async DeleteObj(id: number, msg: boolean = true) {
      const res: ApiResponse = await http.request(
        "delete",
        `${apiPrefix}${id}/`
      );
      if (msg) ElMessage({ message: res.message, type: "success" });
      return res;
    },
    /**
     * 批量删除
     * @param ids IDS
     * @returns 接口请求结果
     */
    async BatchDelete(ids: number[], msg: boolean = true) {
      const res: ApiResponse = await http.request(
        "delete",
        `${apiPrefix}batch_destroy/`,
        {
          data: { ids }
        }
      );
      if (msg) ElMessage({ message: res.message, type: "success" });
      return res;
    }
  };
}
