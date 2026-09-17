<!-- 绑定第三方账号 -->

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { deviceDetection } from "@pureadmin/utils";
import { useI18n } from "vue-i18n";

import { useUserStoreHook } from "@/store/modules/user";
import { thirdParty } from "@/views/login/utils/enums";
import { api } from "./api";
import { thirdLogin } from ".";

defineOptions({
  name: "Oauth2"
});

const { t } = useI18n();

// 取消绑定
const handleUnbind = async (providerInfo: any) => {
  await api.DeleteObj(providerInfo);
  get_data(); // 重新获取绑定状态
};

// 初始化列表，确保保留原始 thirdParty 中的所有字段（包括 provider）
const provider_list = ref(
  thirdParty.map((item: any) => ({
    ...item,
    provider_info: null as any
  }))
);
// 初始化：获取已绑定账号
const get_data = async () => {
  try {
    const { data } = await api.GetList({
      paginate: false,
      user: useUserStoreHook().id
    });

    const boundAccounts = data || [];

    provider_list.value.forEach(item => {
      const matched = boundAccounts.find(
        (acc: any) => acc.platform === item.platform
      );
      item.provider_info = matched || null;
    });
  } catch (error) {
    console.error("获取绑定账号失败", error);
  }
};
onMounted(() => {
  //初始化crud
  get_data();
});
</script>

<template>
  <div :class="['min-w-45', deviceDetection() ? 'max-w-full' : 'max-w-[70%]']">
    <h3 class="my-8!">绑定第三方账号</h3>
    <h4>使用以下任一方式都可以登录，避免由于某个帐号失效导致无法登录</h4>
    <el-divider />
    <div
      v-for="(item, index) in provider_list"
      :key="index"
      :title="t(item.title)"
      class="flex items-center mb-4"
    >
      <div class="flex-1">
        <div class="flex">
          <div class="mr-5">
            <IconifyIconOnline
              :icon="`${item.icon}`"
              width="50"
              :style="{ color: item.color }"
            />
          </div>
          <el-text>{{ t(item.title) }}</el-text>
        </div>
      </div>
      <div>
        <template v-if="item.provider_info">
          <span class="mr-2 text-green-500">
            已绑定：{{ item.provider_info?.uname }}
          </span>
          <el-button type="danger" @click="handleUnbind(item.provider_info.id)">
            取消
          </el-button>
        </template>
        <template v-else>
          <el-button type="primary" @click="thirdLogin(item, 'binding')">
            绑定
          </el-button>
        </template>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.el-divider--horizontal {
  border-top: 0.1px var(--el-border-color) var(--el-border-style);
}
</style>
