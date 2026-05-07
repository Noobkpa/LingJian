<template>
  <div class="home-container">
    <div class="home-banner">
      <h2 class="banner-title">多模态伪科普内容智能识别</h2>
      <p class="banner-desc">基于大语言模型，精准识别文本、图片、图文混合类伪科普内容，守护科学真相</p>
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
          <p>支持文本、图片、图文混合三类主流模态内容，全场景覆盖社交媒体伪科普识别需求</p>
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
import ContentUpload from '@/components/user/ContentUpload.vue'
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