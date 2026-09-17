<template>
  <el-drawer
    v-model="formDialogShow"
    title="菜单配置"
    size="500px"
    draggable
    destroy-on-close
  >
    <el-scrollbar class="h-[calc(100vh-100px)]">
      <el-form
        ref="formRef"
        class="menu-form"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="父级菜单">
          <el-tree-select
            v-model="formData.parent"
            value-key="id"
            check-strictly
            show-checkbox
            clearable
            :data="treeData"
            :render-after-expand="false"
            :props="treeProps"
            @clear="formData.parent = null"
          />
        </el-form-item>

        <el-form-item label="菜单名称" prop="title">
          <el-input v-model="formData.title" />
        </el-form-item>
        <el-form-item label="菜单图标">
          <IconSelect v-model="formData.icon" class="w-full" />
        </el-form-item>
        <el-form-item>
          <template #label>
            <div class="slot-label">
              <el-tooltip content="菜单名称右侧的额外图标">
                <component :is="useRenderIcon('ep:info-filled')" />
              </el-tooltip>
              <span>右侧图标</span>
            </div>
          </template>
          <IconSelect v-model="formData.extraIcon" class="w-full" />
        </el-form-item>

        <el-form-item prop="path">
          <template #label>
            <div class="slot-label">
              <el-tooltip content="内部路径和外部链接">
                <component :is="useRenderIcon('ep:info-filled')" />
              </el-tooltip>
              <span>路由地址</span>
            </div>
          </template>
          <el-input v-model="formData.path" />
        </el-form-item>

        <el-form-item prop="name">
          <template #label>
            <div class="slot-label">
              <el-tooltip
                content="路由名称（必须保持唯一）,最好直接用组件称名，如：`MenuView`"
              >
                <component :is="useRenderIcon('ep:info-filled')" />
              </el-tooltip>
              <span>路由名字</span>
            </div>
          </template>
          <el-input v-model="formData.name" />
        </el-form-item>
        <el-form-item label="组件地址">
          <el-autocomplete
            v-model="formData.component"
            class="w-full"
            :fetch-suggestions="queryComponent"
            :trigger-on-focus="false"
            clearable
            :debounce="100"
            placeholder="输入组件地址"
          />
        </el-form-item>

        <el-form-item label="关联角色">
          <fs-table-select
            v-model="formData.role"
            :multiple="true"
            :createCrudOptions="roleCrudOptions"
            :crudOptionsOverride="crudOptionsOverride"
            :dict="roleDict"
          />
        </el-form-item>

        <el-form-item label="排序">
          <el-input-number v-model="formData.sort" />
        </el-form-item>

        <el-divider />
        <el-row>
          <el-col :span="12">
            <el-form-item label="侧边显示">
              <el-switch v-model="formData.showLink" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="是否缓存">
              <el-switch v-model="formData.keepAlive" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row>
          <el-col :span="12">
            <el-form-item label="">
              <template #label>
                <div class="slot-label">
                  <el-tooltip
                    content="当前菜单名称或自定义信息禁止添加到标签页（默认`false`）"
                  >
                    <component :is="useRenderIcon('ep:info-filled')" />
                  </el-tooltip>
                  <span>是否禁止</span>
                </div>
              </template>
              <el-switch v-model="formData.hiddenTag" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="">
              <template #label>
                <div class="slot-label">
                  <el-tooltip
                    content="当前菜单名称是否固定显示在标签页且不可关闭（默认`false`）"
                  >
                    <component :is="useRenderIcon('ep:info-filled')" />
                  </el-tooltip>
                  <span>是否固定</span>
                </div>
              </template>
              <el-switch v-model="formData.fixedTag" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row>
          <el-col :span="12">
            <el-form-item label="显示父级">
              <el-switch v-model="formData.showParent" />
            </el-form-item>
          </el-col>
          <el-col :span="12" />
        </el-row>

        <el-divider />
        <el-form-item>
          <template #label>
            <div class="slot-label">
              <el-tooltip
                content="`iframe`页是否开启首次加载动画（默认`true`）"
              >
                <component :is="useRenderIcon('ep:info-filled')" />
              </el-tooltip>
              <span>内嵌动画</span>
            </div>
          </template>
          <el-switch v-model="formData.frameLoading" />
        </el-form-item>
        <el-form-item label="内嵌链接">
          <el-input v-model="formData.frameSrc" />
        </el-form-item>

        <el-divider />
        <el-form-item label="组件动画">
          <template #label>
            <div class="slot-label">
              <el-tooltip
                content="页面加载动画（两种模式，第二种权重更高，第一种直接采用`vue`内置的`transitions`动画，第二种是使用`animate.css`编写进、离场动画，平台更推荐使用第二种模式，已经内置了`animate.css`，直接写对应的动画名即可）"
              >
                <component :is="useRenderIcon('ep:info-filled')" />
              </el-tooltip>
              <span>组件动画</span>
            </div>
          </template>
          <el-input v-model="formData.transitionName" />
        </el-form-item>
        <el-form-item label="组件进场动画">
          <el-input v-model="formData.enterTransition" />
        </el-form-item>
        <el-form-item label="组件离场动画">
          <el-input v-model="formData.leaveTransition" />
        </el-form-item>
      </el-form>
    </el-scrollbar>
    <template #footer>
      <el-button type="primary" @click="formSubmit(formRef)"> 保存 </el-button>
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { IconSelect } from "@/components/ReIcon";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";
import { FormInstance } from "element-plus";
import { useMenuForm } from "../../hooks/useMenuForm";
import { useMenuTree } from "../../hooks/useMenuTree";
import { useFetchSuggestions } from "../../hooks/useFetchSuggestions";
import { dict } from "@fast-crud/fast-crud";
import { api as role_api } from "@/views/system/role/api";
import roleCrudOptions from "@/views/system/role/crud";
const { formDialogShow, formRules, formData, formSubmit } = useMenuForm();
const { treeData, treeProps } = useMenuTree();
const { queryComponent } = useFetchSuggestions();

const formRef = ref<FormInstance>();

const roleDict = dict({
  value: "id",
  label: "name",
  getNodesByValues: async (values: any[]) => {
    const query = ["id", "name"];
    const params = {
      id__in: values.join(","),
      limit: values.length,
      paginate: false,
      query: `{${query.join(",")}}`
    };
    const { data } = await role_api.GetList(params);
    return data;
  }
});

const crudOptionsOverride = {
  toolbar: { show: false },
  actionbar: { show: false },
  rowHandle: { show: false }
};
</script>

<style scoped lang="scss">
.menu-form {
  padding: 5px 20px;
}

.slot-label {
  display: flex;
  gap: 3px;
  align-items: center;
  justify-content: center;
}
</style>
