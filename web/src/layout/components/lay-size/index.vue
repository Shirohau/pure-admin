<script setup lang="ts">
import { useRenderIcon } from "@/components/ReIcon/src/hooks";
import { ref, toRaw } from "vue";
import { useI18n } from "vue-i18n";
import { useComponentSize } from "../../hooks/useComponentSize";

import Check from "~icons/ep/check";
const { t } = useI18n();
const { size, getDropdownItemStyle, getDropdownItemClass, setSize } =
  useComponentSize();
</script>

<template>
  <el-dropdown id="header-size" trigger="click">
    <component
      :is="useRenderIcon(toRaw('ri:font-size-2'))"
      class="navbar-bg-hover w-10 h-12 p-2.75 cursor-pointer outline-hidden"
    />
    <template #dropdown>
      <el-dropdown-menu class="translation">
        <el-dropdown-item
          :style="getDropdownItemStyle(size, 'large')"
          :class="['dark:text-white!', getDropdownItemClass(size, 'large')]"
          @click="setSize('large')"
        >
          <span v-show="size === 'large'" class="check">
            <IconifyIconOffline :icon="Check" />
          </span>
          {{ t("size.large") }}
        </el-dropdown-item>
        <el-dropdown-item
          :style="getDropdownItemStyle(size, 'default')"
          :class="['dark:text-white!', getDropdownItemClass(size, 'default')]"
          @click="setSize('default')"
        >
          <span v-show="size === 'default'" class="check">
            <IconifyIconOffline :icon="Check" />
          </span>
          {{ t("size.default") }}
        </el-dropdown-item>
        <el-dropdown-item
          :style="getDropdownItemStyle(size, 'small')"
          :class="['dark:text-white!', getDropdownItemClass(size, 'small')]"
          @click="setSize('small')"
        >
          <span v-show="size === 'small'" class="check">
            <IconifyIconOffline :icon="Check" />
          </span>
          {{ t("size.small") }}
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>
<style scoped lang="scss">
.translation {
  ::v-deep(.el-dropdown-menu__item) {
    padding: 5px 40px;
  }

  .check {
    position: absolute;
    left: 20px;
  }
}
</style>
