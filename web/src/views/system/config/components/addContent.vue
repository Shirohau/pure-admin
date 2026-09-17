<template>
  <div style="padding: 20px">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
      <el-form-item label="所属分组" prop="parent">
        <el-select v-model="form.parent" placeholder="请选择分组" clearable>
          <el-option
            v-for="(item, index) in tabs.slice(0, -1)"
            :key="index"
            :label="item.title"
            :value="item.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="标题" prop="title">
        <el-input v-model="form.title" placeholder="请输入" clearable />
      </el-form-item>
      <el-form-item label="key值" prop="key">
        <el-input v-model="form.key" placeholder="请输入" clearable />
      </el-form-item>
      <el-form-item label="表单类型" prop="form_item_type">
        <el-select v-model="form.form_item_type" placeholder="请选择" clearable>
          <el-option label="单行文本" :value="0" />
          <el-option label="多行文本" :value="1" />
          <el-option label="数字" :value="2" />
          <el-option label="日期" :value="3" />
          <el-option label="时间" :value="4" />
          <el-option label="日期时间" :value="5" />
          <el-option label="单选" :value="6" />
          <el-option label="多选" :value="7" />
          <el-option label="开关" :value="8" />
        </el-select>
      </el-form-item>

      <el-form-item label="校验规则">
        <el-select
          v-model="form.rule"
          multiple
          placeholder="请选择(可多选)"
          clearable
        >
          <el-option
            v-for="(item, index) in ruleOptions"
            :key="index"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="提示信息" prop="placeholder">
        <el-input v-model="form.placeholder" placeholder="请输入" clearable />
      </el-form-item>
      <el-form-item label="排序" prop="sort">
        <el-input-number v-model="form.sort" :min="0" :max="99" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="onSubmit(formRef)">
          立即创建
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { api } from "../api";
import { ref, reactive } from "vue";
import type { FormInstance, FormRules } from "element-plus";
import { useConfig } from "../hooks/useConfig";
const { tabs } = useConfig();
const form: any = reactive({
  parent: null,
  title: null,
  key: null,
  form_item_type: "",
  rule: null,
  placeholder: null
});
const formRef = ref<FormInstance>();
const rules = reactive<FormRules>({
  parent: [{ required: true, message: "请选择" }],
  title: [{ required: true, message: "请输入" }],
  key: [
    { required: true, message: "请输入" },
    { pattern: /^[A-Za-z0-9_]+$/, message: "请输入数字、字母或下划线" }
  ],
  form_item_type: [{ required: true, message: "请输入" }]
});

let ruleOptions = ref([
  {
    label: "必填项",
    value: '{"required": true, "message": "必填项不能为空"}'
  },
  {
    label: "邮箱",
    value: '{ "type": "email", "message": "请输入正确的邮箱地址"}'
  },
  {
    label: "URL地址",
    value: '{ "type": "url", "message": "请输入正确的URL地址"}'
  }
]);

const onSubmit = async (formEl: FormInstance | undefined) => {
  if (!formEl) return;
  await formEl.validate((valid, fields) => {
    if (valid) {
      api.CreateObj(form).then((res: ApiResponse) => {
        if (res.code == 2000) {
        }
      });
    } else {
      console.log("error submit!", fields);
    }
  });
};
</script>
