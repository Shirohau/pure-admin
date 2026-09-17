<template>
  <div>
    <!-- 文件上传 -->
    <input type="file" accept=".pdf" @change="handleFileUpload" />

    <!-- 解析结果展示 -->
    <div v-if="parsedResume" class="resume-content">
      <h2>结构化简历信息</h2>
      <div class="info-section">
        <h3>基本信息</h3>
        <p><strong>姓名：</strong>{{ parsedResume.basicInfo.name }}</p>
        <p><strong>性别：</strong>{{ parsedResume.basicInfo.gender }}</p>
        <p><strong>民族：</strong>{{ parsedResume.basicInfo.nationality }}</p>
        <p><strong>出生年月：</strong>{{ parsedResume.basicInfo.birthDate }}</p>
        <p><strong>联系电话：</strong>{{ parsedResume.basicInfo.phone }}</p>
        <p><strong>电子邮箱：</strong>{{ parsedResume.basicInfo.email }}</p>
        <p>
          <strong>现居地：</strong>{{ parsedResume.basicInfo.currentLocation }}
        </p>
        <p><strong>籍贯：</strong>{{ parsedResume.basicInfo.hometown }}</p>
        <p>
          <strong>政治面貌：</strong
          >{{ parsedResume.basicInfo.politicalStatus }}
        </p>
        <p><strong>宗教信仰：</strong>{{ parsedResume.basicInfo.religion }}</p>
        <p><strong>身份证号码：</strong>{{ parsedResume.basicInfo.idCard }}</p>
        <p>
          <strong>工作状态：</strong>{{ parsedResume.basicInfo.workStatus }}
        </p>
      </div>

      <div v-if="parsedResume.education.length" class="info-section">
        <h3>教育背景</h3>
        <div
          v-for="(edu, index) in parsedResume.education"
          :key="index"
          class="edu-item"
        >
          <p><strong>时间：</strong>{{ edu.period }}</p>
          <p><strong>学校：</strong>{{ edu.school }}</p>
          <p><strong>专业：</strong>{{ edu.major }}</p>
          <p><strong>学位：</strong>{{ edu.degree }}</p>
          <p><strong>培养方式：</strong>{{ edu.studyMode }}</p>
        </div>
      </div>

      <div v-if="parsedResume.workExperience.length" class="info-section">
        <h3>工作经历</h3>
        <div
          v-for="(job, index) in parsedResume.workExperience"
          :key="index"
          class="job-item"
        >
          <p><strong>时间：</strong>{{ job.period }}</p>
          <p><strong>公司：</strong>{{ job.company }}</p>
          <p><strong>职务：</strong>{{ job.position }}</p>
          <p><strong>职责：</strong>{{ job.responsibilities }}</p>
        </div>
      </div>

      <div v-if="parsedResume.summary.length" class="info-section">
        <h3>主要工作经历总结</h3>
        <ol>
          <li v-for="(item, index) in parsedResume.summary" :key="index">
            {{ item }}
          </li>
        </ol>
      </div>
    </div>
    <div>
      <p>{{ fullText }}</p>
    </div>
    <!-- PDF 预览（可选） -->
    <div v-if="pdfUrl" class="pdf-preview">
      <iframe :src="pdfUrl" width="100%" height="600px" />
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import * as pdfjsLib from "pdfjs-dist";
import pdfWorker from "pdfjs-dist/build/pdf.worker.min?url";

// 设置匹配的 worker
pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorker;

const parsedResume = ref(null);
const pdfUrl = ref("");
const fullText = ref("");

// 处理文件上传
const handleFileUpload = async event => {
  const file = event.target.files[0];
  if (!file || !file.type.includes("pdf")) {
    alert("请上传有效的 PDF 文件！");
    return;
  }

  // 重置上一次结果
  parsedResume.value = null;
  pdfUrl.value = URL.createObjectURL(file);

  try {
    const arrayBuffer = await file.arrayBuffer();
    const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;

    // 提取所有页面文本
    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i);
      const textContent = await page.getTextContent();
      const pageText = textContent.items.map(item => item.str).join(" ");
      fullText.value += pageText + "\n";
    }

    // 清理并标准化文本
    const text = fullText.value
      .replace(/\s+/g, " ") // 合并多余空白
      .replace(/d59028f516f8721a1HZ43dy4EFFUxYu8VPmYWOarmfXYMRdh/g, "") // 移除水印
      .trim();

    // 初始化结构化数据
    const resumeData = {
      basicInfo: {},
      education: [],
      workExperience: [],
      summary: []
    };

    // === 基本信息解析 ===
    const basicInfoRegexes = {
      name: /姓名\s*([^\s]+)/,
      gender: /性别\s*([男女])/,
      nationality: /民族\s*([^\s]+)/,
      phone: /联系电话(1[3-9]\d{9})/,
      idCard: /身份证号\s*码?\s*(\d{17}[\dXx])/,
      birthDate: /出生年月\s*([\d.]+)/,
      email: /电子邮箱\s*([^\s@]+@[^\s@]+\.[^\s@]+)/,
      currentLocation: /现居地\s*([^\s]+)/,
      hometown: /籍贯\s*([^\s]+)/,
      politicalStatus: /政治面貌\s*([^\s]+)/,
      religion: /宗教信仰\s*([^\s]+)/,
      workStatus:
        /目前工作状态\s*[□☑]离职:\s*(\d{4}年\d{1,2}月\d{1,2}日正式离职)/
    };

    for (const [key, regex] of Object.entries(basicInfoRegexes)) {
      const match = text.match(regex);
      resumeData.basicInfo[key] = match ? match[1] : "";
    }

    // === 教育背景解析 ===
    const eduMatch = text.match(
      /教育经历.*?(\d{4}\.\d+\s*至\s*\d{4}\.\d+)\s+([^\s]+大学|学院).*?([^\s]+技术|[^，。]+专业).*?(大专|本科|硕士|博士).*?[□☑]非全日制/
    );
    if (eduMatch) {
      resumeData.education.push({
        period: eduMatch[1].replace(/\s+/g, ""),
        school: eduMatch[2],
        major: eduMatch[3],
        degree: eduMatch[4],
        studyMode: "非全日制"
      });
    }

    // === 工作经历解析 ===
    // 匹配工作经历模式：时间 公司 职务 职责
    const workRegex =
      /(\d{4}\.\d+\s*至\s*-?\d{4}\.\d+)\s+([^(]+?\([^)]+\))\s+([弱电主管|暖通主管|弱电]+)\s+(负责.*?)(?=\d{4}\.|主要经历工作|$)/g;
    let workMatch;
    while ((workMatch = workRegex.exec(text)) !== null) {
      resumeData.workExperience.push({
        period: workMatch[1].replace(/\s+/g, ""),
        company: workMatch[2].trim(),
        position: workMatch[3],
        responsibilities: workMatch[4].replace(/\s+/g, " ").trim()
      });
    }

    // === 主要工作经历总结解析 ===
    const summaryMatch = text.match(
      /主要经历工作.*?1\s*、(.*?)2\s*、(.*?)3\s*、(.*?)4\s*、(.*?)5\s*、(.*?)(?=\d{4}\.|$)/
    );
    if (summaryMatch) {
      resumeData.summary = [
        summaryMatch[1].trim(),
        summaryMatch[2].trim(),
        summaryMatch[3].trim(),
        summaryMatch[4].trim(),
        summaryMatch[5].trim()
      ];
    }

    parsedResume.value = resumeData;
  } catch (error) {
    console.error("PDF 解析失败:", error);
    alert("PDF 解析失败，请检查文件是否损坏。");
  }
};
</script>

<style scoped>
.resume-content {
  padding: 15px;
  margin-top: 20px;
  background: #f9f9f9;
  border: 1px solid #ddd;
  border-radius: 8px;
}

.info-section {
  padding: 10px;
  margin-bottom: 20px;
  background: white;
  border-radius: 6px;
}

.info-section h3 {
  margin-bottom: 10px;
  color: #2c3e50;
}

.job-item,
.edu-item {
  padding: 10px;
  margin-bottom: 15px;
  background: #f0f8ff;
  border-left: 3px solid #3498db;
}

.pdf-preview {
  margin-top: 20px;
}
</style>
