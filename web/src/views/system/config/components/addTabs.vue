<template>
  <div style="padding: 20px">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
      <el-form-item label="标题" prop="title">
        <el-input v-model="form.title" />
      </el-form-item>
      <el-form-item label="key值" prop="key">
        <el-input v-model="form.key" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="onSubmit(formRef)"> 创建 </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from "vue";
import type { FormInstance, FormRules } from "element-plus";

let form = reactive({
  title: null,
  key: null,
  closable: true
});
const formRef = ref<FormInstance>();
const rules = reactive<FormRules>({
  title: [{ required: true, message: "请输入" }],
  key: [
    { required: true, message: "请输入" },
    { pattern: /^[A-Za-z0-9]+$/, message: "只能是英文和数字" }
  ]
});
import { useConfig } from "../hooks/useConfig";
const { addTabs } = useConfig();
const onSubmit = async (formEl: FormInstance | undefined) => {
  if (!formEl) return;
  await formEl.validate((valid, fields) => {
    if (valid) {
      addTabs(form);
    } else {
      console.log("error submit!", fields);
    }
  });
};
</script>
