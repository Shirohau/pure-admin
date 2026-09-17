import { computed, onBeforeMount, ref } from "vue";
import { useEpThemeStoreHook } from "@/store/modules/epTheme";
import { storageLocal, useGlobal } from "@pureadmin/utils";
import { responsiveStorageNameSpace } from "@/store/utils";

/** 设置组件尺寸选中后的样式 */
const getDropdownItemStyle = computed(() => {
  return (size, t) => {
    return {
      background: size === t ? useEpThemeStoreHook().epThemeColor : "",
      color: size === t ? "#f4f4f5" : "#000"
    };
  };
});
const getDropdownItemClass = computed(() => {
  return (size, t) => {
    return size === t ? "" : "dark:hover:text-primary!";
  };
});

export function useComponentSize() {
  const { $storage } = useGlobal<GlobalPropertiesApi>();
  const size = ref("");
  function setSize(t: string) {
    const layout = storageLocal().getItem<StorageConfigs>(
      `${responsiveStorageNameSpace()}layout`
    );
    layout.componentSize = t;
    size.value = t;
    storageLocal().setItem(`${responsiveStorageNameSpace()}layout`, layout);
    window.location.reload();
  }

  onBeforeMount(() => {
    size.value = $storage.layout.componentSize ?? "small";
  });
  return {
    size,
    getDropdownItemStyle,
    getDropdownItemClass,
    setSize
  };
}
