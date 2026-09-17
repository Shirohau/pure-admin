import { CreateApi } from "@/api/base";

export const apiPrefix = "/api/system/user/";
export const api = {
  ...CreateApi(apiPrefix)
};
