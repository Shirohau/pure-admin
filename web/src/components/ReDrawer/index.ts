import { ref } from "vue";
import reDrawer from "./index.vue";
import { useTimeoutFn } from "@vueuse/core";
import { withInstall } from "@pureadmin/utils";
import type { DrawerOptions } from "./type";

const drawerStore = ref<Array<DrawerOptions>>([]);

/** 打开抽屉 */
const addDrawer = (options: DrawerOptions) => {
  const open = () =>
    drawerStore.value.push(Object.assign(options, { visible: true }));
  if (options?.openDelay) {
    useTimeoutFn(() => {
      open();
    }, options.openDelay);
  } else {
    open();
  }
};

/** 关闭抽屉 */
const closeDrawer = (options: DrawerOptions, index: number, args?: any) => {
  drawerStore.value[index].visible = false;
  options.closeCallBack && options.closeCallBack({ options, index, args });

  const closeDelay = options?.closeDelay ?? 200;
  useTimeoutFn(() => {
    drawerStore.value.splice(index, 1);
  }, closeDelay);
};

/**
 * @description 更改抽屉自身属性值
 * @param value 属性值
 * @param key 属性，默认`title`
 * @param index 抽屉索引（默认`0`，代表只有一个抽屉，对于嵌套抽屉要改哪个抽屉的属性值就把该抽屉索引赋给`index`）
 */
const updateDrawer = (value: any, key = "title", index = 0) => {
  drawerStore.value[index][key] = value;
};

/** 关闭所有抽屉 */
const closeAllDrawer = () => {
  drawerStore.value = [];
};

/** 千万别忘了在下面这三处引入并注册下，放心注册，不使用`addDrawer`调用就不会被挂载
 * https://github.com/pure-admin/vue-pure-admin/blob/main/src/App.vue#L4
 * https://github.com/pure-admin/vue-pure-admin/blob/main/src/App.vue#L12
 * https://github.com/pure-admin/vue-pure-admin/blob/main/src/App.vue#L22
 */
const ReDrawer = withInstall(reDrawer);

export type { DrawerOptions };
export {
  ReDrawer,
  drawerStore,
  addDrawer,
  closeDrawer,
  updateDrawer,
  closeAllDrawer
};
