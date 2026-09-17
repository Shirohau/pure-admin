import { CreateApi } from "@/api/base";

export const apiPrefix = "/api/celery/crontab_schedule/";
export const api = {
  ...CreateApi(apiPrefix)
};
