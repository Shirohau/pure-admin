import { ElMessageBox, type FormInstance, type FormRules } from "element-plus";
import { reactive, ref } from "vue";
import { useMenuTree } from "./useMenuTree";
import { openExportDialog } from "@/components/ReExport";
import { openImportDialog } from "@/components/ReImport";
import { api, apiPrefix } from "../api";
const { setTreeData, selectTreeNode } = useMenuTree();
interface MenuForm {
  id?: number;
  /** 父级菜单 */
  parent?: number;
  /** 菜单名称（兼容国际化、非国际化，如何用国际化的写法就必须在根目录的`locales`文件夹下对应添加） `必填` */
  title?: string;
  /** 菜单图标 `可选` */
  icon?: string;
  /** 菜单名称右侧的额外图标 */
  extraIcon?: string;

  /** 路由地址 `必填` */
  path?: string;
  /** 路由名字（保持唯一）`可选` */
  name?: string;
  /** `Layout`组件 `可选` */
  component?: string;

  /** 是否在菜单中显示（默认`true`）`可选` */
  showLink?: boolean;
  /** 是否显示父级菜单 `可选` */
  showParent?: boolean;
  /** 路由组件缓存（开启 `true`、关闭 `false`）`可选` */
  keepAlive?: boolean;
  /** 当前菜单名称或自定义信息禁止添加到标签页（默认`false`） */
  hiddenTag?: boolean;
  /** 当前菜单名称是否固定显示在标签页且不可关闭（默认`false`） */
  fixedTag?: boolean;

  /** 内嵌的`iframe`链接 `可选` */
  frameSrc?: string;
  /** `iframe`页是否开启首次加载动画（默认`true`）`可选` */
  frameLoading?: boolean;

  /** 页面加载动画
   * 两种模式:
   * - 第二种权重更高
   * - 第一种直接采用`vue`内置的`transitions`动画
   * - 第二种是使用`animate.css`编写进、离场动画
   * 平台更推荐使用第二种模式，已经内置了`animate.css`，直接写对应的动画名即可）`可选` */
  transitionName?: string;
  /** 组件进场动画 */
  enterTransition?: string;
  /** 组件离场动画 */
  leaveTransition?: string;
  /** 关联角色 */
  role?: number[];
  /** 排序 */
  sort?: number;
}

const initialFormData: MenuForm = {
  id: undefined,
  parent: undefined,
  title: undefined,
  icon: undefined,
  extraIcon: undefined,
  path: undefined,
  name: undefined,
  component: undefined,
  showLink: true,
  showParent: true,
  keepAlive: true,
  hiddenTag: false,
  fixedTag: false,
  frameSrc: undefined,
  frameLoading: true,
  transitionName: undefined,
  enterTransition: undefined,
  leaveTransition: undefined,
  role: [],
  sort: undefined
};

/**
 * 菜单表单数据
 */
const formData = reactive({ ...initialFormData });

/*  校验规则 */
const formRules = reactive<FormRules<MenuForm>>({
  title: [{ required: true, message: "请输入菜单名称", trigger: "blur" }],
  name: [{ required: true, message: "请输入路由名字", trigger: "blur" }],
  path: [
    { required: true, message: "请输入路由地址", trigger: "blur" },
    {
      validator: (rule: any, value: string, callback: any) => {
        if (!value) {
          callback();
          return;
        }

        const isInternal = value.startsWith("/");
        const isExternal = /^https?:\/\//i.test(value);

        if (!isInternal && !isExternal) {
          callback(
            new Error(
              '路由地址必须以 "/" 开头（内部路径）或以 "http://" / "https://" 开头（外部链接）'
            )
          );
        } else {
          callback();
        }
      },
      trigger: "blur"
    }
  ],
  component: [{ required: true, message: "请输入组件地址", trigger: "blur" }]
});

/**
 * @description 菜单表单弹窗显示控制
 */
const formDialogShow = ref(false);
/**
 * @description 菜单表单模式
 */
const openFormDialogMod = ref("add");
/**
 * @description 打开菜单表单
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
 * @description 新增菜单表单打开
 */
const addOpenFormDialog = () => {
  setFormData({
    parent: selectTreeNode.value?.id,
    path: selectTreeNode.value?.path
  });
};

/**
 * @description 编辑菜单表单打开
 */
const editOpenFormDialog = () => {
  setFormData(selectTreeNode.value);
};

/**
 * @description 菜单表单数据设置
 */
const setFormData = (data: MenuForm) => {
  Object.assign(formData, initialFormData, data);
};

/**
 * @description 菜单表单提交
 */
const formSubmit = (formEl: FormInstance) => {
  formEl.validate(valid => {
    if (valid) {
      switch (openFormDialogMod.value) {
        case "add":
          addMenu();
          break;
        case "edit":
          editMenu();
          break;
      }
    }
  });
};
/**
 * 修正路由 path：如果路径以 "/" 结尾且不是根路径 "/"，则移除末尾的 "/"
 * @param path 原始路径
 * @returns 修正后的路径
 */
function normalizePath(path: string): string {
  if (!path || path === "/") {
    return path;
  }
  // 移除末尾的斜杠（但保留根路径 "/"）
  return path.endsWith("/") ? path.slice(0, -1) : path;
}

/**
 * @description 新增菜单
 */
const addMenu = async () => {
  formData.path = normalizePath(formData.path);
  await api.CreateObj(formData);
  await setTreeData();
  formDialogShow.value = false;
};

/**
 * @description 修改菜单
 */
const editMenu = async () => {
  if (!formData.parent) {
    formData.parent = null;
  }
  formData.path = normalizePath(formData.path);
  const { data } = await api.UpdateObj(formData.id, formData);
  await setTreeData();
  formDialogShow.value = false;
  selectTreeNode.value = data;
};

/**
 * @description 删除菜单
 */
const delMenu = async () => {
  ElMessageBox.confirm(`确定要删除这个菜单吗?`, "删除提示")
    .then(async () => {
      await api.DeleteObj(selectTreeNode.value.id);
      await setTreeData();
      selectTreeNode.value = null;
      formDialogShow.value = false;
    })
    .catch(() => {});
};

/**
 * @description 导出菜单
 */
const exportMenu = () => {
  openExportDialog(apiPrefix);
};
/**
 * @description 导入菜单
 */
const importMenu = async () => {
  openImportDialog(apiPrefix);
};
export function useMenuForm() {
  return {
    formData,
    formRules,
    formDialogShow,
    openFormDialogMod,
    openFormDialog,
    formSubmit,
    addMenu,
    editMenu,
    delMenu,
    setFormData,
    exportMenu,
    importMenu
  };
}
