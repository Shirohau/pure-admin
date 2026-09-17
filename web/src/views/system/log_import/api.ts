import { CreateApi } from "@/api/base";

export const apiPrefix = "/api/system/log_import/";
export const api = {
  ...CreateApi(apiPrefix)
};
