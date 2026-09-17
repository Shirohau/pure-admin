import { CreateApi } from "@/api/base";

export const apiPrefix = "/api/celery/task_result/";
export const api = {
  ...CreateApi(apiPrefix)
};
