import { CreateApi } from "@/api/base";

export const apiPrefix = "/api/system/log_request/";
export const api = {
  ...CreateApi(apiPrefix)
};
