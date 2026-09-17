import { CreateApi } from "@/api/base";

export const apiPrefix = "/api/celery/clocked_schedule/";
export const api = {
  ...CreateApi(apiPrefix)
};
