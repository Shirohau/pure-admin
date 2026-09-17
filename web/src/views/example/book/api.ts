import { CreateApi } from "@/api/base";

export const apiPrefix = "/api/example/book/";
export const api = {
  ...CreateApi(apiPrefix)
};
