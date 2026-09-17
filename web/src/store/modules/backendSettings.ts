import { http } from "@/utils/http";
import { storageSession } from "@pureadmin/utils";
import { defineStore } from "pinia";
import { ref } from "vue";
import { responsiveStorageNameSpace } from "../utils";
import XEUtils from "xe-utils";

export const useBackendSettings = defineStore("bacnekd-settings", () => {
  // State
  const config = ref([]);

  /**
   * 从后端获取配置
   */
  const fetchConfig = async () => {
    config.value = storageSession().getItem(
      `${responsiveStorageNameSpace()}banckedConfig`
    );
    const params = {
      query: "{id,title,key,value,form_type}"
    };
    const apiPrefix = "/api/system/config/get_config/";
    if (!config.value) {
      const { data }: ApiResponse = await http.get(apiPrefix, { params });
      storageSession().setItem(
        `${responsiveStorageNameSpace()}banckedConfig`,
        data
      );
      config.value = data;
    }
  };

  const getKeyConfig = (key: string) => {
    const item = XEUtils.find(config.value, item => item.key === key);
    switch (item?.form_type) {
      case "image":
        return item?.value?.path;
      default:
        return item?.value;
    }
  };

  return {
    config,
    fetchConfig,
    getKeyConfig
  };
});
