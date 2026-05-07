<template>
  <div class="home-container">
    <div class="home-banner">
      <h2 class="banner-title">多模态伪科普内容智能识别</h2>
      <p class="banner-desc">
        基于大语言模型，支持<strong>文本</strong>、<strong>图片</strong>、<strong>图文混合</strong>提交；研判侧<strong>重点覆盖医疗、养生、科技</strong>三大类伪科普高发语境，由系统自动匹配提示与结论取向，无需手动选类。
      </p>
      <div class="domain-chips" aria-label="识别侧重类别">
        <span class="domain-chips-label">识别侧重</span>
        <el-tag type="danger" effect="plain" round>医疗类</el-tag>
        <el-tag type="warning" effect="plain" round>养生类</el-tag>
        <el-tag type="primary" effect="plain" round>科技类</el-tag>
      </div>
    </div>

    <div class="upload-card base-card">
      <ContentUpload />
    </div>

    <div class="feature-card base-card">
      <h3 class="feature-title">系统核心能力</h3>
      <div class="feature-list">
        <div class="feature-item">
          <div class="feature-icon">
            <el-icon size="32"><Document /></el-icon>
          </div>
          <h4>多模态内容识别</h4>
          <p>支持文本、图片、图文混合；结合<strong>医疗 / 养生 / 科技</strong>三类语境自动研判，覆盖社交平台常见伪科普形态</p>
        </div>
        <div class="feature-item">
          <div class="feature-icon">
            <el-icon size="32"><Cpu /></el-icon>
          </div>
          <h4>大模型深度推理</h4>
          <p>基于BERT+LLM双模型协同推理，精准识别逻辑谬误、科学事实错误、术语堆砌等伪科普特征</p>
        </div>
        <div class="feature-item">
          <div class="feature-icon">
            <el-icon size="32"><Share /></el-icon>
          </div>
          <h4>一键分享辟谣</h4>
          <p>识别结果一键生成分享图片与链接，适配主流社交平台，助力科学辟谣传播</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import ContentUpload from '@/components/ContentUpload.vue'
import { Document, Cpu, Share } from '@element-plus/icons-vue'
</script>

<style scoped>
.home-container {
  width: 100%;
}
.home-banner {
  text-align: center;
  padding: 32px 16px;
  margin-bottom: 24px;
}
.banner-title {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 12px;
}
.banner-desc {
  font-size: 16px;
  color: #606266;
  max-width: 800px;
  margin: 0 auto;
  line-height: 1.6;
}
.banner-desc strong {
  color: #303133;
  font-weight: 600;
}
.domain-chips {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 10px 12px;
  margin-top: 18px;
}
.domain-chips-label {
  font-size: 14px;
  font-weight: 600;
  color: #606266;
  margin-right: 4px;
}
.feature-title {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 24px;
  text-align: center;
}
.feature-list {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}
.feature-item {
  padding: 20px;
  border-radius: 8px;
  background: #f8f9fa;
  text-align: center;
}
.feature-icon {
  color: #4080FF;
  margin-bottom: 12px;
}
.feature-item h4 {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
}
.feature-item p {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  margin: 0;
}

@media (max-width: 768px) {
  .feature-list {
    grid-template-columns: 1fr;
  }
  .banner-title {
    font-size: 22px;
  }
}
</style>