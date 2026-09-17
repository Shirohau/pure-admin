import { CreateApi } from "@/api/base";

export const apiPrefix = "/api/system/config/";
export const api = {
  ...CreateApi(apiPrefix)
};
