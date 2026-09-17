import { CreateApi } from "@/api/base";

export const apiPrefix = "/api/system/log_export/";
export const api = {
  ...CreateApi(apiPrefix)
};
