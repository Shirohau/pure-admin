<template>
  <el-form>
    <el-form-item class="pb-2">
      <el-radio v-model="formValue.radioValue" :label="1">
        每小时，允许的通配符[, - * /]
      </el-radio>
    </el-form-item>

    <el-form-item class="pb-2">
      <el-radio v-model="formValue.radioValue" :label="2">
        周期：从第
        <el-input-number
          v-model="formValue.cycle01"
          class="w-120"
          :min="0"
          :max="formValue.cycle02 - 1"
          :precision="0"
        />
        小时，到第
        <el-input-number
          v-model="formValue.cycle02"
          class="w-120"
          :min="formValue.cycle01 + 1"
          :max="23"
          :precision="0"
        />
        小时
      </el-radio>
    </el-form-item>

    <el-form-item class="pb-2">
      <el-radio v-model="formValue.radioValue" :label="3">
        间隔：每隔
        <el-input-number
          v-model="formValue.interval"
          class="w-120"
          :min="1"
          :max="23"
          :precision="0"
        />
        小时
      </el-radio>
    </el-form-item>

    <el-form-item class="pb-2">
      <el-radio v-model="formValue.radioValue" :label="4">
        指定：
        <el-select
          v-model="formValue.checkboxList"
          clearable
          placeholder="可多选"
          multiple
          style="width: 90%; min-width: 200px"
        >
          <el-option v-for="item in 24" :key="item" :value="item - 1">
            {{ item - 1 }}
          </el-option>
        </el-select>
      </el-radio>
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { onMounted, reactive, watch } from "vue";
const emit = defineEmits(["update:modelValue"]);

const props = defineProps({
  defaultValue: ""
} as any);

const formValue = reactive({
  radioValue: 1,
  cycle01: 1,
  cycle02: 2,
  interval: 1,
  checkboxList: [] as number[]
});
// 监听modelValue对象的变化
watch(
  () => ({ ...formValue }),
  newVal => {
    emit("update:modelValue", dumpCron(newVal));
  },
  { deep: true }
);
//解析Cron的小时
function dumpCron(value: typeof formValue): string {
  switch (value.radioValue) {
    case 1:
      return "*";
    case 2:
      return value.cycle01 + "-" + value.cycle02;
    case 3:
      return "*/" + value.interval;
    case 4:
      return value.checkboxList.length == 0
        ? "*"
        : value.checkboxList.join(",");
    default:
      return "*";
  }
}
// 反解析Cron的小时
function loadCron(value?: string) {
  if (value) {
    if (value == "*") {
      formValue.radioValue = 1;
    } else if (typeof value === "string" && value.indexOf("-") > -1) {
      formValue.radioValue = 2;
      const [start, end] = value.split("-").map(Number);
      formValue.cycle01 = start;
      formValue.cycle02 = end;
    } else if (typeof value === "string" && value.indexOf("/") > -1) {
      formValue.radioValue = 3;
      const [start, end] = value.split("/").map(Number);
      formValue.interval = end;
    } else {
      formValue.radioValue = 4;
      formValue.checkboxList = value.split(",").map(Number);
    }
  }
}
onMounted(() => {
  loadCron(props.defaultValue);
});
</script>
<style lang="scss" scoped>
.w-120 {
  width: 120px !important;
}
</style>
