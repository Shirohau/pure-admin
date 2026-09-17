import { CreateApi } from "@/api/base";

export const apiPrefix = "/api/system/apiwhite/";
export const api = {
  ...CreateApi(apiPrefix)
};
