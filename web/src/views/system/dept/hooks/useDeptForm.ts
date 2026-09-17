/**
 * 部门表单 hooks：管理部门新增/编辑/删除表单弹窗，以及导入导出入口。
 *
 * 职责划分：
 *  - 表单弹窗开关与模式切换（openFormDialog / openFormDialogMod / formDialogShow）
 *  - 新增/编辑表单初始化（addOpenFormDialog / editOpenFormDialog）
 *  - 表单校验与提交（formSubmit → addDept / editDept）
 *  - 删除部门（delDept）
 *  - 导入导出入口（exportDept / importDept）
 */
import { ElMessageBox, type FormInstance, type FormRules } from "element-plus";
import { reactive, ref } from "vue";
import { api, apiPrefix } from "../api";
import { useDeptTree } from "./useDeptTree";
import { openExportDialog } from "@/components/ReExport";
import { openImportDialog } from "@/components/ReImport";
const { setTreeData, selectTreeNode } = useDeptTree();
/**
 * @description 部门表单数据
 */
interface DeptForm {
  id?: number | undefined;
  /** 父级部门ID */
  parentId: number | undefined;
  /** 部门名称 */
  name: string;
  /** 部门编码 */
  code: string;
  /** 部门状态 */
  status: boolean;
  /** 负责人（关联用户ID，空为未设置） */
  owner?: number | null;
}

/**
 * @description 部门表单弹窗显示控制
 */
const formDialogShow = ref(false);
/**
 * @description 部门表单模式
 */
const openFormDialogMod = ref("add");
/**
 * @description 打开部门表单弹窗
 * @param mod "add" 新增（父级默认为当前选中部门）/ "edit" 编辑（回填当前选中部门）
 */
const openFormDialog = (mod: string) => {
  switch (mod) {
    case "add":
      addOpenFormDialog();
      break;
    case "edit":
      editOpenFormDialog();
      break;
  }
  openFormDialogMod.value = mod;
  formDialogShow.value = true;
};

/**
 * @description 新增部门表单初始化：父部门为当前选中节点，默认名称为"xx 子部门"
 */
const addOpenFormDialog = () => {
  setFormData({
    parentId: selectTreeNode.value?.id,
    name: selectTreeNode.value?.name + " 子部门",
    code: "",
    status: true,
    owner: null
  });
};

/**
 * @description 编辑部门表单初始化：回填当前选中部门的详情数据
 */
const editOpenFormDialog = () => {
  const node = selectTreeNode.value;
  setFormData({
    ...node,
    // 树节点详情返回的 owner 是用户对象，表单需要用户ID
    owner: node.owner?.id ?? null
  });
};

/**
 * @description 部门表单弹数据
 */
const formData = reactive<DeptForm>({
  id: undefined,
  parentId: undefined,
  name: "",
  code: "",
  status: true,
  owner: null
});

/**
 * @description 部门表单数据设置
 */
const setFormData = (data: DeptForm) => {
  Object.assign(formData, data);
};
/**
 * @description 部门表单验证规则
 */
const formRules = reactive<FormRules<DeptForm>>({
  name: [{ required: true, message: "请输入部门名称", trigger: "blur" }],
  code: [{ required: true, message: "请输入部门编号", trigger: "blur" }]
});
/**
 * @description 部门表单提交入口：先校验，再按当前弹窗模式分发新增/编辑
 * @param formEl 表单实例（el-form），用于触发 validate 校验
 */
const formSubmit = (formEl: FormInstance) => {
  formEl.validate(valid => {
    if (valid) {
      switch (openFormDialogMod.value) {
        case "add":
          addDept();
          break;
        case "edit":
          editDept();
          break;
      }
    }
  });
};

/**
 * @description 提交新增部门：成功后刷新树并关闭弹窗
 */
const addDept = async () => {
  await api.CreateObj(formData);
  await setTreeData();
  formDialogShow.value = false;
};

/**
 * @description 提交修改部门：parentId 为空时转为 null（即根部门）；
 * 成功后刷新树、关闭弹窗，并将最新数据同步为选中部门（保证右侧详情一致）
 */
const editDept = async () => {
  if (!formData.parentId) {
    formData.parentId = null;
  }
  const { data } = await api.UpdateObj(formData.id, formData);
  await setTreeData();
  formDialogShow.value = false;
  selectTreeNode.value = data;
};

/**
 * @description 删除部门：二次确认后调用删除接口，成功后刷新树并清空选中部门
 */
const delDept = async () => {
  ElMessageBox.confirm(`确定要删除这个部门吗?`, "删除提示")
    .then(async () => {
      await api.DeleteObj(selectTreeNode.value.id);
      await setTreeData();
      selectTreeNode.value = null;
      formDialogShow.value = false;
    })
    .catch(() => {});
};

/**
 * @description 打开部门导出对话框（支持字段选择，导出后端生成的文件）
 */
const exportDept = () => {
  openExportDialog(apiPrefix);
};
/**
 * @description 打开部门导入对话框（按模板上传文件批量导入）
 */
const importDept = async () => {
  openImportDialog(apiPrefix);
};
/**
 * 部门表单 hooks 统一出口：返回全部状态与操作方法供页面组件使用
 */
export function useDeptForm() {
  return {
    formDialogShow,
    openFormDialogMod,
    openFormDialog,
    formRules,
    formData,
    formSubmit,
    addDept,
    editDept,
    delDept,
    setFormData,
    exportDept,
    importDept
  };
}
