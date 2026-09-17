import { CreateApi } from "@/api/base";

export const apiPrefix = "/api/example/author/";
export const api = {
  ...CreateApi(apiPrefix)
};
