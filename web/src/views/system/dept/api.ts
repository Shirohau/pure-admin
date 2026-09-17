/**
 * 部门模块 API：继承通用 CRUD 接口（CreateApi 生成的增删改查），
 * 并扩展部门独有的"上移/下移"移动接口。
 */
import { CreateApi } from "@/api/base";
import { http } from "@/utils/http";

/** 部门接口前缀（对应后端 system/dept 路由） */
export const apiPrefix = "/api/system/dept/";

export const api = {
  ...CreateApi(apiPrefix),
  /**
   * 部门节点上移/下移（与兄弟节点交换顺序）
   * @param id 部门ID
   * @param direction 移动方向："up" 上移 / "down" 下移，边界情况由后端忽略处理
   */
  MoveObj(id: number, direction?: string) {
    return http.request("get", `${apiPrefix}${id}/move/`, {
      params: { direction }
    });
  }
};
