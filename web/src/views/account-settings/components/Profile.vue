<script setup lang="ts">
import { reactive, ref } from "vue";
import { message } from "@/utils/message";
import { formUpload } from "@/api/user";
import type { FormInstance, FormRules } from "element-plus";
import ReCropperPreview from "@/components/ReCropperPreview";
import { createFormData, deviceDetection } from "@pureadmin/utils";
import uploadLine from "~icons/ri/upload-line";

import { api } from "../api";
import { validateEmail, validateMobile } from "@/utils/validators";
import { useUserInfo } from "../hooks/useUserInfo";
const { userInfo, set_avatar_path } = useUserInfo();

defineOptions({
  name: "Profile"
});

const imgSrc = ref("");
const cropperBlob = ref();
const cropRef = ref();
const uploadRef = ref();
const isShow = ref(false);
const userInfoFormRef = ref<FormInstance>();

const rules = reactive<FormRules>({
  name: [{ required: true, message: "昵称必填", trigger: "blur" }],
  email: [
    { required: true, message: "邮箱必填", trigger: "blur" },
    { validator: validateEmail, trigger: "blur" }
  ],
  mobile: [
    { required: true, message: "电话必填", trigger: "blur" },
    { validator: validateMobile, trigger: "blur" }
  ]
});

/**
 * 查询并过滤邮箱域名建议列表
 * 根据用户输入的邮箱字符串，匹配常见的邮箱域名后缀（@qq.com、@126.com、@163.com），
 * 返回以输入内容开头的完整邮箱建议列表
 * @param {string} queryString - 用户输入的邮箱查询字符串（如 "test@qq"）
 * @param {Function} callback - 回调函数，接收过滤后的邮箱建议数组参数，数组元素格式为 { value: string }
 */
function queryEmail(queryString: string, callback: Function) {
  const emailList = [
    { value: "@qq.com" },
    { value: "@126.com" },
    { value: "@163.com" }
  ];
  let results = [];
  let queryList = [];
  emailList.map(item =>
    queryList.push({ value: queryString.split("@")[0] + item.value })
  );
  results = queryString
    ? queryList.filter(
        item =>
          item.value.toLowerCase().indexOf(queryString.toLowerCase()) === 0
      )
    : queryList;
  callback(results);
}

/**
 * 处理文件上传变更事件，读取上传的图片文件并转换为 Data URL 格式
 * @param {Object} uploadFile - 上传的文件对象
 * @param {File} uploadFile.raw - 原始文件对象
 */
const onChange = uploadFile => {
  const reader = new FileReader();
  reader.onload = e => {
    imgSrc.value = e.target.result as string;
    isShow.value = true;
  };
  reader.readAsDataURL(uploadFile.raw);
};

/**
 * 关闭处理函数
 * 用于隐藏裁剪弹窗、清空上传文件并关闭显示状态
 */
const handleClose = () => {
  cropRef.value.hidePopover();
  uploadRef.value.clearFiles();
  isShow.value = false;
};

/**
 * 图片裁剪完成后的回调处理函数
 * @param {Object} options - 裁剪结果对象
 * @param {Blob} options.blob - 裁剪后生成的图片 Blob 数据
 */
const onCropper = ({ blob }) => (cropperBlob.value = blob);

/**
 * 提交裁剪后的头像图片进行上传处理
 * 创建包含裁剪后图片的文件对象，通过表单上传接口提交，并根据上传结果显示成功或失败消息
 */
const handleSubmitImage = () => {
  // 构建包含裁剪后图片文件的表单数据对象
  // 确保 MIME 类型正确
  const mimeType = cropperBlob.value.type || "image/png"; // fallback to png
  const fileName = `${userInfo.value.name || "avatar"}.png`;

  const file = new File([cropperBlob.value], fileName, { type: mimeType });

  const data = createFormData({
    file,
    folder: "avatar"
  });
  // 调用表单上传接口提交头像图片，根据响应结果显示对应的操作反馈
  formUpload(data)
    .then(({ success, data }) => {
      if (success) {
        // 图片上传成功之后,需要绑定到业务对象上
        message("更新头像成功", { type: "success" });
        set_avatar_path(data.data.path);
        api.UpdateObj(userInfo.value.id, { avatar_id: data.data.id });
        handleClose();
      } else {
        message("更新头像失败");
      }
    })
    .catch(error => {
      message(`提交异常 ${error}`, { type: "error" });
    });
};

/**
 * 提交表单处理函数，验证表单数据并在验证通过后更新用户信息
 * @param {FormInstance} formEl - Element Plus 表单实例对象，用于执行表单验证操作
 */
const onSubmit = async (formEl: FormInstance) => {
  // 执行表单验证，回调函数接收验证结果和错误字段信息
  await formEl.validate(async (valid, fields) => {
    // 验证通过时调用 API 更新用户信息
    if (valid) {
      await api.UpdateObj(userInfo.value.id, userInfo.value);
    } else {
      console.log("error submit!", fields);
    }
  });
};

const pwdShow = ref(false);
const pwdFormRef = ref();
const pwdLoading = ref(false);
const pwdInfo = reactive({
  oldPassword: "",
  newPassword: "",
  newPassword2: ""
});

const validatePass = (rule, value, callback) => {
  const pwdRegex = new RegExp("(?=.*[0-9])(?=.*[a-zA-Z]).{8,30}");
  if (value === "") {
    callback(new Error("请输入密码"));
  } else if (value === pwdInfo.oldPassword) {
    callback(new Error("原密码与新密码一致"));
  } else if (!pwdRegex.test(value)) {
    callback(new Error("您的密码复杂度太低(密码中必须包含数字，大小写字母)"));
  } else {
    if (pwdInfo.newPassword2 !== "") {
      pwdFormRef.value.validateField("newPassword2");
    }
    callback();
  }
};
const validatePass2 = (rule, value, callback) => {
  if (value === "") {
    callback(new Error("请再次输入密码"));
  } else if (value !== pwdInfo.newPassword) {
    callback(new Error("两次输入密码不一致!"));
  } else {
    callback();
  }
};
const pwdRules = reactive({
  oldPassword: [
    {
      required: true,
      message: "请输入原密码",
      trigger: "blur"
    }
  ],
  newPassword: [{ validator: validatePass, trigger: "blur" }],
  newPassword2: [{ validator: validatePass2, trigger: "blur" }]
});
const pwdOpen = () => {
  pwdShow.value = true;
};
const pwdSave = () => {
  pwdFormRef.value.validate(async isValid => {
    if (!isValid) return;
    pwdLoading.value = true;
    try {
      const res = await api.UpdatePassword(userInfo.value.id, pwdInfo);
      message(res.message, { type: "success" });
      pwdShow.value = false;
    } catch (error) {
      console.error("密码修改失败:", error);
    } finally {
      pwdLoading.value = false;
    }
  });
};
</script>

<template>
  <div :class="['min-w-45', deviceDetection() ? 'max-w-full' : 'max-w-[70%]']">
    <h3 class="my-8!">个人信息</h3>
    <el-form
      ref="userInfoFormRef"
      label-position="top"
      :rules="rules"
      :model="userInfo"
    >
      <el-form-item label="头像">
        <el-avatar :size="80" :src="userInfo.avatar_path" />
        <el-upload
          ref="uploadRef"
          accept="image/*"
          action="#"
          :limit="1"
          :auto-upload="false"
          :show-file-list="false"
          :on-change="onChange"
        >
          <el-button plain class="ml-4!">
            <IconifyIconOffline :icon="uploadLine" />
            <span class="ml-2">更新头像</span>
          </el-button>
        </el-upload>
      </el-form-item>
      <el-form-item label="昵称" prop="name">
        <el-input v-model="userInfo.name" placeholder="请输入昵称" />
      </el-form-item>
      <el-form-item label="邮箱" prop="email">
        <el-autocomplete
          v-model="userInfo.email"
          :fetch-suggestions="queryEmail"
          :trigger-on-focus="false"
          placeholder="请输入邮箱"
          clearable
          class="w-full"
        />
      </el-form-item>
      <el-form-item label="联系电话" prop="mobile">
        <el-input
          v-model="userInfo.mobile"
          placeholder="请输入联系电话"
          clearable
        />
      </el-form-item>
      <!-- <el-form-item label="简介">
        <el-input
          v-model="userInfo.description"
          placeholder="请输入简介"
          type="textarea"
          :autosize="{ minRows: 6, maxRows: 8 }"
          maxlength="56"
          show-word-limit
        />
      </el-form-item> -->
      <el-button type="primary" @click="onSubmit(userInfoFormRef)">
        更新信息
      </el-button>
    </el-form>
    <el-dialog
      v-model="isShow"
      width="40%"
      title="编辑头像"
      destroy-on-close
      :closeOnClickModal="false"
      :before-close="handleClose"
      :fullscreen="deviceDetection()"
    >
      <ReCropperPreview ref="cropRef" :imgSrc="imgSrc" @cropper="onCropper" />
      <template #footer>
        <div class="dialog-footer">
          <el-button bg text @click="handleClose">取消</el-button>
          <el-button bg text type="primary" @click="handleSubmitImage">
            确定
          </el-button>
        </div>
      </template>
    </el-dialog>

    <div>
      <el-divider />
      <div class="flex items-center">
        <div class="flex-1">
          <p>账户密码</p>
        </div>
        <el-button type="primary" text @click="pwdOpen()"> 修改 </el-button>
      </div>
    </div>

    <!--    密码修改-->
    <el-dialog v-model="pwdShow" title="密码修改">
      <el-form
        ref="pwdFormRef"
        :model="pwdInfo"
        required-asterisk
        label-width="100px"
        label-position="left"
        :rules="pwdRules"
        center
      >
        <el-form-item label="原密码">
          <el-input
            v-model="pwdInfo.oldPassword"
            type="password"
            placeholder="请输入原始密码"
            show-password
            clearable
          />
        </el-form-item>
        <el-form-item required prop="newPassword" label="新密码">
          <el-input
            v-model="pwdInfo.newPassword"
            type="password"
            placeholder="请输入新密码"
            show-password
            clearable
          />
        </el-form-item>
        <el-form-item required prop="newPassword2" label="确认密码">
          <el-input
            v-model="pwdInfo.newPassword2"
            type="password"
            placeholder="请再次输入新密码"
            show-password
            clearable
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button type="primary" :loading="pwdLoading" @click="pwdSave">
            <i class="fa fa-check" />提交
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>
