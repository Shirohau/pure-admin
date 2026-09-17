import { ref } from "vue";
import { api } from "../api";

const tabs = ref<any[]>([]);
const tabsValue = ref();
const getTabs = () => {
  api
    .GetList({
      paginate: false,
      parent__isnull: true
    })
    .then((res: any) => {
      const data = res.data || [];
      tabs.value = data;
      if (tabsValue.value) return;
      tabsValue.value = data[0].id;
    });
};

const addTabs = (form: any) => {
  api.CreateObj(form).then(() => {
    getTabs();
  });
};
const removeTabs = (key: number) => {
  api.DeleteObj(key).then(() => {
    getTabs();
  });
};
export function useConfig() {
  return { tabs, tabsValue, getTabs, addTabs, removeTabs };
}
