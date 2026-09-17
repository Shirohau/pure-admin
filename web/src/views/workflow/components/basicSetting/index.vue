<!--
  审批流程设计器 - 基础设置（第一步）
  来源：AntFlow-Designer（https://gitee.com/ldhnet/AntFlow-Designer）
  迁移适配：import 路径由 @/utils/workflow/ 调整为 @/views/workflow/utils/workflow/
  作用：配置流程的基础信息（流程编号/分组/审批名称/审批人去重/模板图标/审批说明），
       并通过 defineExpose 暴露 getData 供父级在"发布"时统一收集数据。
-->
<template>
	<section class="basic-setting-page">
		<div class="basic-setting-wrap">
			<el-form ref="formRef" :model="basicForm" :rules="rules" label-position="right" label-width="90px"
				class="setting-form">
				<el-form-item label="流程编号" prop="flowCode" required>
					<!-- 流程编号：由父级数据带入，设计器内不可修改 -->
					<el-input v-model="basicForm.flowCode" disabled />
				</el-form-item>

				<el-form-item label="选择分组" prop="groupId" required>
					<el-select v-model="basicForm.groupId" class="full-width" placeholder="请选择分组">
						<el-option label="总公司流程" value="root-group" />
						<el-option label="分公司流程" value="branch-group" />
					</el-select>
				</el-form-item>

				<el-form-item label="审批名称" prop="name" required>
					<el-input v-model="basicForm.name" placeholder="请输入审批名称" maxlength="20" />
				</el-form-item>

				<el-form-item label="审批人去重" prop="distinctType">
					<el-select v-model="basicForm.distinctType" class="full-width">
						<el-option label="不去重" value="0" />
						<el-option label="前去重" value="1" />
						<el-option label="后去重" value="2" />
					</el-select>
				</el-form-item>

				<el-form-item label="模板图标" prop="flowIcon">
					<div class="icon-row">
						<span class="icon-preview">★</span>
						<el-button plain @click="selectIcon">选择图标</el-button>
					</div>
				</el-form-item>

				<el-form-item label="审批说明" prop="remark">
					<el-input v-model="basicForm.remark" type="textarea" :rows="4" maxlength="100" show-word-limit
						placeholder="请输入审批说明" />
				</el-form-item>
			</el-form>
		</div>
	</section>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { getRandomUniqueCode } from '@/views/workflow/utils/workflow/commonUtils'

/**
 * 父级传入的基础设置数据（流程定义中的基础字段）
 */
let props = defineProps({
	data: {
		type: Object,
		default: () => ({})
	}
});

const formRef = ref(null)

/** 基础设置表单数据（由 props.data 初始化） */
const basicForm = reactive({})

// 监听父级数据变化，同步到表单，并为每个流程生成唯一 key
watch(() => props.data, (value) => {
	const defkey = value.flowCode + getRandomUniqueCode(); // 确保每个流程都有唯一的 key
	Object.assign(basicForm, { ...(value || {}), key: defkey })
}, { immediate: true, deep: true })

/** 表单校验规则（流程编号/审批名称为必填） */
const rules = {
	flowCode: [{ required: true, message: '请输入流程编号', trigger: 'blur' }],
	name: [{ required: true, message: '请输入审批名称', trigger: 'blur' }]
}

/** 选择模板图标（当前为占位实现） */
const selectIcon = () => {
	ElMessage.info('图标选择面板开发中')
}

/**
 * 提供给父级页面的数据获取方法（发布时调用）
 * @returns {Promise<{ formData: Object }>}
 */
const getData = () => {
	try {
		return Promise.resolve({ formData: { ...basicForm } })
	} catch (err) {
		return Promise.reject(new Error('获取基础表单数据失败'))
	}
}

defineExpose({
	getData
})
</script>

<style scoped>
.basic-setting-page {
	min-height: 100%;
	padding: 0 64px;
}

.basic-setting-wrap {
	min-height: calc(100vh - 74px);
	max-width: 760px;
	min-width: 320px;
	margin: 0 auto;
	padding: 26px 64px;
	background: #fff;
	box-sizing: border-box;
}

.setting-form {
	max-width: 520px;
	margin: 0 auto;
}

.full-width {
	width: 100%;
}

.icon-row {
	display: flex;
	align-items: center;
	gap: 10px;
}

.icon-preview {
	width: 26px;
	height: 26px;
	border-radius: 2px;
	display: inline-flex;
	align-items: center;
	justify-content: center;
	color: #ffffff;
	font-size: 13px;
	background: #45c97a;
}

:deep(.el-form-item) {
	margin-bottom: 16px;
}

:deep(.el-form-item__label) {
	color: #4f5b6f;
	font-size: 15px;
}

:deep(.el-input__wrapper),
:deep(.el-textarea__inner),
:deep(.el-select__wrapper) {
	background: #ffffff;
	box-shadow: 0 0 0 1px #d9dde5 inset;
	border-radius: 2px;
}

:deep(.el-input.is-disabled .el-input__wrapper) {
	background: #eef1f5;
	box-shadow: 0 0 0 1px #d9dde5 inset;
}

:deep(.el-textarea .el-input__count) {
	background: transparent;
	right: 8px;
	color: #7d8797;
}

@media (max-width: 900px) {
	.basic-setting-page {
		padding: 0 10px;
	}

	.basic-setting-wrap {
		padding: 16px 12px;
	}

	.setting-form {
		max-width: 100%;
	}
}
</style>
