<script setup lang="ts">
import { useI18n } from "vue-i18n";
import { ref, reactive } from "vue";
import Motion from "../utils/motion";
import { message } from "@/utils/message";
import { emailRules } from "../utils/rule";
import type { FormInstance } from "element-plus";
import { useVerifyCode } from "../utils/verifyCode";
import { useUserStoreHook } from "@/store/modules/user";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";
import Email from "~icons/ic/outline-email";
import Keyhole from "~icons/ri/shield-keyhole-line";
import { getTopMenu, initRouter } from "@/router/utils";
import router from "@/router";
import { api } from "../api";
import { setToken } from "@/utils/auth";

const { t } = useI18n();
const loading = ref(false);
const ruleForm = reactive({
  type: "email",
  email: "",
  code: ""
});
const ruleFormRef = ref<FormInstance>();
const { isDisabled, text } = useVerifyCode();

const onLogin = async (formEl: FormInstance | undefined) => {
  if (!formEl) return;

  await formEl.validate(async valid => {
    if (valid) {
      loading.value = true;

      try {
        api.login({ ...ruleForm }).then((res: ApiResponse) => {
          setToken(res.data);
          return initRouter().then(() => {
            router
              .push(getTopMenu(true).path)
              .then(() => {
                message(t("login.pureLoginSuccess"), { type: "success" });
              })
              .finally(() => (loading.value = false));
          });
        });
      } finally {
        loading.value = false;
      }
    }
  });
};

function onBack() {
  useVerifyCode().end();
  useUserStoreHook().SET_CURRENTPAGE(0);
}
</script>

<template>
  <el-form ref="ruleFormRef" :model="ruleForm" :rules="emailRules" size="large">
    <Motion>
      <el-form-item prop="email">
        <el-input
          v-model="ruleForm.email"
          clearable
          :placeholder="t('login.pureEmail')"
          :prefix-icon="useRenderIcon(Email)"
        />
      </el-form-item>
    </Motion>

    <Motion :delay="100">
      <el-form-item prop="code">
        <div class="w-full flex justify-between">
          <el-input
            v-model="ruleForm.code"
            clearable
            :placeholder="t('login.pureSmsVerifyCode')"
            :prefix-icon="useRenderIcon(Keyhole)"
          />
          <el-button
            :disabled="isDisabled"
            class="ml-2!"
            @click="useVerifyCode().start(ruleFormRef, 'email')"
          >
            {{
              text.length > 0
                ? text + t("login.pureInfo")
                : t("login.pureGetVerifyCode")
            }}
          </el-button>
        </div>
      </el-form-item>
    </Motion>

    <Motion :delay="150">
      <el-form-item>
        <el-button
          class="w-full"
          size="default"
          type="primary"
          :loading="loading"
          @click="onLogin(ruleFormRef)"
        >
          {{ t("login.pureLogin") }}
        </el-button>
      </el-form-item>
    </Motion>

    <Motion :delay="200">
      <el-form-item>
        <el-button class="w-full" size="default" @click="onBack">
          {{ t("login.pureBack") }}
        </el-button>
      </el-form-item>
    </Motion>
  </el-form>
</template>
