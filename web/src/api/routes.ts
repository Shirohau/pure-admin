import { http } from "@/utils/http";
import XEUtils from "xe-utils";

export const getAsyncRoutes = async () => {
  const res: ApiResponse = await http.request(
    "get",
    "/api/system/menu/routes/"
  );
  // 响应拦截器已返回 body，res 即 { success, data: [...] }
  const rawData: any[] = (res as any)?.data ?? [];
  // 过滤掉原始类型值（如数字、字符串等），避免 toArrayTree 内部尝试在原始类型上创建 id 属性时报错
  const validData = Array.isArray(rawData)
    ? rawData.filter((item: any) => item !== null && typeof item === "object")
    : [];
  const data = XEUtils.toArrayTree(validData, {
    parentKey: "parent",
    strict: true
  });
  return { data };
};

/** 按菜单 name 获取当前用户的按钮权限 + 字段权限（统一接口） */
export const getPagePerms = async (
  name: string
): Promise<{
  buttons: string[];
  fields: Array<{
    field_name: string;
    permission_level: number;
    /** 功能权限集（可配置扩展，key 见后端 FUNC_PERMISSION_DEFINITIONS，如 can_download/can_print） */
    func_permissions?: Record<string, boolean>;
  }>;
}> => {
  const res: ApiResponse = await http.request(
    "get",
    "/api/system/menu/page-perms/",
    { params: { name } }
  );
  return (res as any)?.data ?? { buttons: [], fields: [] };
};
