import { CreateApi } from "@/api/base";
export const apiPrefix = "/api/example/publisher/";

export const api = {
  ...CreateApi(apiPrefix)
};
