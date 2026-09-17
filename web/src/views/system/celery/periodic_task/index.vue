<template>
  <div>
    <fs-crud ref="crudRef" v-bind="crudBinding">
      <div>
        <el-row
          v-if="crudBinding?.data"
          :gutter="15"
          style="width: 100%; height: 100%; overflow: auto"
        >
          <span v-if="crudBinding?.data.length === 0" style="width: 100%">
            <el-empty description="暂无数据请添加" />
          </span>
          <el-col
            v-for="item of crudBinding?.data"
            :key="item.id"
            :xl="4"
            :lg="6"
            :md="8"
            :sm="12"
            :xs="24"
            :span="6"
            style="margin-bottom: 10px"
          >
            <el-card class="task task-item" shadow="hover">
              <h2>{{ item.name }}</h2>
              <ul>
                <li>
                  <h4>执行任务</h4>
                  <el-text>{{ item.task }}</el-text>
                </li>
                <li>
                  <h4>执行规则</h4>
                  <el-text>
                    {{
                      item.clocked_obj?.clocked_time ||
                      item.interval_obj?.described ||
                      cronstrue.toString(item.crontab_obj?.cron, {
                        locale: "zh_CN"
                      }) ||
                      "--"
                    }}
                  </el-text>
                </li>
              </ul>
              <div class="bottom w-full">
                <div class="state flex flex-wrap items-center">
                  <el-switch
                    v-model="item.enabled"
                    class="ml-2"
                    inline-prompt
                    style="
                      --el-switch-on-color: #13ce66;
                      --el-switch-off-color: #ff4949;
                    "
                    :disabled="item.name == '周期任务'"
                    active-text="启用"
                    inactive-text="停用"
                    :before-change="handleSwithBeforeChange.bind(this, item)"
                    @change="handleSwithChange(item)"
                  />
                </div>
                <div class="taskName">
                  <el-button
                    circle
                    plain
                    size="small"
                    type="primary"
                    :icon="Edit"
                    @click="openEdit(item)"
                  />
                  <el-button
                    circle
                    plain
                    size="small"
                    type="danger"
                    :icon="Delete"
                    :disabled="item.name == '周期任务'"
                    @click="doRemove(item)"
                  />
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </fs-crud>
  </div>
</template>
<script lang="ts" setup>
import cronstrue from "cronstrue";
import "cronstrue/locales/zh_CN";

import { onMounted } from "vue";
import { useFs, useFsRef } from "@fast-crud/fast-crud";
import { ElMessageBox } from "element-plus";

import { Delete, Edit } from "@element-plus/icons-vue";

import createCrudOptions, { componentName } from "./crud";
import { api } from "./api";

defineOptions({
  name: componentName
});

const { crudRef, crudBinding, crudExpose } = useFsRef();
//同步初始化crud
useFs({
  crudRef,
  crudBinding,
  crudExpose,

  createCrudOptions
});

/**
 * 打开编辑
 * @param item 当前行数据
 */
const openEdit = (item: any) => {
  crudExpose.openEdit({ row: item });
};
/**
 * 删除
 * @param item 当前行数据
 */
const doRemove = (item: any) => {
  ElMessageBox.confirm("确认删除该任务？", {
    confirmButtonText: "确定",
    cancelButtonText: "取消"
  }).then(async () => {
    await api.DeleteObj(item.id);
    crudExpose.doRefresh();
  });
};

/**
 * 启动项目前置校验逻辑
 * @param item 当前行数据
 */
const handleSwithBeforeChange = async (item: any) => {
  const title = item.enabled ? "确认停用该任务？" : "确认启用该任务？";
  return await ElMessageBox.confirm(title, {
    confirmButtonText: "确定",
    cancelButtonText: "取消"
  })
    .then(() => true)
    .catch(() => false);
};

/**
 * 修改状态
 * @param item 当前行数据
 */
const handleSwithChange = async (item: any) => {
  // 构造一个 JS 对象
  const kwargsObj = { periodic_task_id: item.id };
  // 转为标准 JSON 字符串（双引号）
  item.kwargs = JSON.stringify(kwargsObj);
  await api.UpdateObj(item.id, item);
};
// 页面打开后获取列表数据
onMounted(async () => {
  crudExpose.doRefresh();
});
</script>

<style lang="scss" scoped>
.task {
  height: 220px;
}

.task-item h2 {
  padding-bottom: 10px;
  font-size: 15px;
  color: #3c4a54;
}

.task-item li {
  margin-bottom: 10px;
  list-style-type: none;
}

.task-item li h4 {
  font-size: 12px;
  font-weight: normal;
  color: #999;
}

.task-item li p {
  margin-top: 5px;
}

.task-item .bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 10px;
  text-align: right;
  border-top: 1px solid #ebeef5;
}

.task-add {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #999;
  text-align: center;
  cursor: pointer;
}

.task-add:hover {
  color: #409eff;
}

.task-add i {
  font-size: 30px;
}

.task-add p {
  margin-top: 20px;
  font-size: 12px;
}

.dark .task-item .bottom {
  border-color: var(--el-border-color-light);
}

.el-card {
  overflow: hidden;
  border-radius: 3%;
}

.el-dialog {
  overflow: hidden;
  border-radius: 3%;
}
</style>
