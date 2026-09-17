import { CreateApi } from "@/api/base";

export const apiPrefix = "/api/celery/periodic_task/";
export const api = {
  ...CreateApi(apiPrefix)
};
