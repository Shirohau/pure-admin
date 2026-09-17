<!--
  审批流程设计器 - 主页面（三步向导：基础设置 → 表单设计 → 流程设计）
  来源：AntFlow-Designer（https://gitee.com/ldhnet/AntFlow-Designer）
  迁移适配：
  1. import 路径由 @/utils/workflow/、@/api/workflow/mock.js 调整为 @/views/workflow/... 下对应路径
  2. 去掉原页面的 Gitee/GitHub 仓库链接
  3. handleBack 改为 router.back()（无历史记录时提示）
  4. 发布逻辑保留：Promise.all 汇总三步数据、validatePublish 错误弹窗、控制台输出 JSON（不调后端）
  作用：页面加载时通过 getWorkFlowData 拉取 mock 流程数据并解析为三步配置；
       顶部导航支持三步切换与发布；发布前校验流程设计节点配置完整性，
       通过后将基础设置/表单设计/流程设计数据组装为完整流程 JSON 输出到控制台。
-->
<template>
	<div class="workflow-shell">
		<header class="top-nav">
			<div class="nav-left">
				<el-button text class="back-btn" @click="handleBack">
					<el-icon>
						<ArrowLeft />
					</el-icon>
				</el-button>
				<span class="process-title">请假申请流程</span>
			</div>

			<div class="nav-steps" :class="`step-${currentStep}`" role="list" aria-label="流程步骤">
				<div class="step-active-bg" aria-hidden="true"></div>
				<div v-for="(step, index) in steps" :key="step.value" class="step-item"
					:class="{ active: currentStep === index }" @click="currentStep = index">
					<span class="step-index">{{ index + 1 }}</span>
					<span class="step-text">{{ step.label }}</span>
				</div>
			</div>

			<div class="nav-right">
				<el-button class="publish-btn" @click="handlePublish">发布</el-button>
			</div>
		</header>

		<section class="content-panel">
			<div v-show="currentStep === 0" class="step-page">
				<BasicSetting ref="basicSettingRef" v-if="basicSettingDataConf" :data="basicSettingDataConf" />
			</div>
			<div v-show="currentStep === 1" class="step-page">
				<DynamicForm ref="dynamicFormRef" v-if="dynamicFormDataConf" :lfFormData="dynamicFormDataConf" />
			</div>
			<div v-show="currentStep === 2" class="step-page">
				<FlowDesign ref="flowDesignRef" v-if="nodesDataConf" :data="nodesDataConf" />
			</div>
		</section>

		<ErrorDialog v-model:visible="publishErrorVisible" :items="publishErrors" @edit="handlePublishEdit" />
	</div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import BasicSetting from "./components/basicSetting/index.vue";
import DynamicForm from "./components/dynamicForm/index.vue";
import FlowDesign from "./components/flowDesign/index.vue";
import ErrorDialog from "./components/flowDesign/drawer/dialog/errorDialog.vue";
import { FormatDisplayUtils } from '@/views/workflow/utils/workflow/formatDisplayData';
import { NodeUtils } from "@/views/workflow/utils/workflow/nodeUtils";
import { getWorkFlowData, setWorkFlowData } from "@/views/workflow/api/workflow/mock.js";

const router = useRouter()
/** 三步向导配置 */
const steps = [
	{ value: 'basic', label: '基础设置' },
	{ value: 'form', label: '表单设计' },
	{ value: 'flow', label: '流程设计' }
]

const currentStep = ref(0)
const basicSettingRef = ref(null)
const dynamicFormRef = ref(null)
const flowDesignRef = ref(null)
const basicSettingDataConf = ref(null)
const dynamicFormDataConf = ref(null)
const nodesDataConf = ref(null)

onMounted(async () => {
	await init();
});
/** 初始化：拉取 mock 流程数据并解析为三步配置 */
const init = async () => {
	// var nodeDemo = NodeUtils.initNode();
	// var workflowResult = FormatDisplayUtils.getToTree(nodeDemo);
	// const { nodeConfig, frmValue, ...restData } = workflowResult;
	// nodesDataConf.value = nodeConfig;
	// dynamicFormDataConf.value = frmValue;
	// basicSettingDataConf.value = restData;

	await getWorkFlowData().then((res) => {
		const workflowResult = FormatDisplayUtils.getToTree(res.data);
		const { nodeConfig, frmValue, ...restData } = workflowResult;
		nodesDataConf.value = nodeConfig;
		dynamicFormDataConf.value = frmValue;
		basicSettingDataConf.value = restData;
	})

	//console.log("dynamicFormDataConf.value=====", dynamicFormDataConf.value);
};
/** 发布：汇总三步数据并输出完整流程 JSON 到控制台（对接后端处见 setWorkFlowData） */
const publish = () => {
	const step1 = basicSettingRef.value.getData();
	const step2 = dynamicFormRef.value.getData();
	const step3 = flowDesignRef.value.getData();
	Promise.all([step1, step2, step3])
		.then((res) => {
			ElMessage.success("流程发布成功,F12控制台查看数据");
			const basicData = res[0].formData;
			const dynamicFormData = res[1].formData;
			const flowDesignData = res[2].formData;
			Object.assign(basicData, { frmValue: JSON.stringify(dynamicFormData) });
			Object.assign(basicData, {
				nodes: flowDesignData.map(item => {
					return { ...item, definitionKey: basicData.key || '' }
				})
			});
			return basicData;
		})
		.then((data) => {
			console.log("格式化后对接后端api================", JSON.stringify(data));
			// setWorkFlowData(data).then((resLog) => {
			// 	if (resLog.code == 200) {
			// 		console.log("提交到API返回成功");
			// 	} else {
			// 		console.log("提交到API返回失败=", JSON.stringify(resLog));
			// 	}
			// });
		})
		.catch((err) => {
			if (err) {
				console.log("设置失败" + JSON.stringify(err));
				ElMessage.error("至少配置一个有效审批人节点");
			}
		});
};

const publishErrorVisible = ref(false)
const publishErrors = ref([])
/** 发布入口：先校验流程节点配置完整性，有错误弹窗提示，无错误执行发布 */
const handlePublish = () => {
	const errors = flowDesignRef.value?.validatePublish() || []
	if (errors.length > 0) {
		publishErrors.value = errors
		publishErrorVisible.value = true
		return
	} else {
		publish();
	}
}

/** 错误弹窗"前往修改"：跳转到流程设计步骤 */
const handlePublishEdit = () => {
	currentStep.value = 2
}

/** 返回上一页（无历史记录时提示） */
const handleBack = () => {
	if (window.history.length > 1) {
		router.back()
	} else {
		ElMessage.info('没有可返回的页面')
	}
}

</script>

<style scoped>
.workflow-shell {
	min-height: 100vh;
	background: linear-gradient(180deg, #eef4ff 0%, #f9fbff 56%, #ffffff 100%);
}

.top-nav {
	position: sticky;
	top: 0;
	z-index: 30;
	height: 65px;
	display: grid;
	grid-template-columns: minmax(160px, 260px) minmax(420px, 1fr) auto;
	align-items: center;
	gap: 16px;
	padding: 0 18px;
	background: linear-gradient(90deg, #2d82da 0%, #3f97eb 100%);
	box-shadow: 0 6px 16px rgba(34, 101, 189, 0.24);
	overflow-x: auto;
	overflow-y: hidden;
}

.nav-left {
	display: flex;
	align-items: center;
	gap: 6px;
	color: #fff;
	white-space: nowrap;
}

.back-btn {
	color: #d6e9ff;
	padding: 6px;
}

.process-title {
	font-size: 18px;
	font-weight: 600;
	letter-spacing: 0.5px;
	max-width: 200px;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.nav-steps {
	position: relative;
	width: min(480px, 100%);
	min-width: 420px;
	height: 65px;
	margin: 0 auto;
	display: flex;
	justify-content: space-between;
	align-items: stretch;
	overflow: hidden;
}

.step-active-bg {
	position: absolute;
	left: 0;
	top: 0;
	width: calc(100% / 3);
	height: 100%;
	background: rgba(76, 118, 230, 0.36);
	transition: transform 0.28s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.nav-steps.step-1 .step-active-bg {
	transform: translateX(100%);
}

.nav-steps.step-2 .step-active-bg {
	transform: translateX(200%);
}

.step-active-bg::after {
	content: '';
	position: absolute;
	left: 50%;
	bottom: -1px;
	transform: translateX(-50%);
	width: 0;
	height: 0;
	border-left: 7px solid transparent;
	border-right: 7px solid transparent;
	border-bottom: 8px solid #dfe7f6;
}

.step-item {
	position: relative;
	z-index: 1;
	flex: 1;
	display: flex;
	flex-direction: row;
	align-items: center;
	justify-content: center;
	gap: 6px;
	cursor: pointer;
	transition: color 0.22s;
}

.step-index {
	width: 24px;
	height: 24px;
	border-radius: 50%;
	border: 1px solid #ffffff;
	color: #fff;
	display: inline-flex;
	align-items: center;
	justify-content: center;
	font-size: 14px;
	line-height: 1;
	background: rgba(255, 255, 255, 0.08);
	transition: background-color 0.22s;
}

.step-text {
	color: #fff;
	font-size: 25px;
	transform: scale(0.56);
	transform-origin: left center;
	font-weight: 500;
	line-height: 1;
	white-space: nowrap;
	transition: opacity 0.22s;
}

.step-item.active .step-index {
	background: rgba(255, 255, 255, 0.24);
}

.nav-right {
	display: flex;
	align-items: center;
	justify-content: flex-end;
	gap: 10px;
	white-space: nowrap;
}

.publish-btn {
	min-width: 82px;
	color: #2f87df;
	background: #f4f8ff;
	border: none;
	border-radius: 6px;
	font-weight: 600;
}

.content-panel {
	position: relative;
}

.step-page {
	width: 100%;
}


@media (max-width: 1100px) {
	.top-nav {
		height: 56px;
		grid-template-columns: minmax(120px, 200px) minmax(360px, 1fr) auto;
		gap: 10px;
		padding: 0 12px;
	}

	.nav-left {
		min-width: 0;
	}

	.nav-right {
		justify-content: flex-end;
		gap: 8px;
	}

	.process-title {
		font-size: 16px;
		max-width: 160px;
	}

	.nav-steps {
		width: min(520px, 100%);
		min-width: 360px;
		height: 56px;
		border-radius: 4px;
		overflow: hidden;
	}

	.step-active-bg::after {
		bottom: -1px;
	}

	.step-text {
		font-size: 25px;
		transform: scale(0.52);
	}
}

@media (max-width: 860px) {
	.top-nav {
		height: 56px;
		row-gap: 6px;
		overflow: hidden;
	}

	.brand-btn {
		display: none;
	}

	.publish-btn {
		min-width: 72px;
		height: 30px;
		padding: 0 14px;
	}

	.nav-steps {
		height: 56px;
	}

	.step-item {
		gap: 4px;
	}

	.step-index {
		width: 20px;
		height: 20px;
		font-size: 12px;
	}

	.step-text {
		font-size: 25px;
		transform: scale(0.5);
	}
}

@media (max-width: 560px) {
	.top-nav {
		/* padding: 6px 8px 8px; */
		overflow: hidden;
	}

	.back-btn {
		padding: 4px;
	}

	.nav-steps {
		height: 56px;
	}

	.step-text {
		font-size: 25px;
	}
}
</style>
