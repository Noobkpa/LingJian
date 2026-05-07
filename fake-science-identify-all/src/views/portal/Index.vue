<template>
  <div class="portal-page">
    <div class="portal-bg" aria-hidden="true" />
    <div class="portal-orb portal-orb--1" aria-hidden="true" />
    <div class="portal-orb portal-orb--2" aria-hidden="true" />

    <header class="portal-hero">
      <p class="portal-eyebrow">LingJian</p>
      <h1 class="portal-title">灵鉴</h1>
      <p class="portal-tagline">多模态伪科普内容 · 智能识别与研判</p>
      <p class="portal-lead">
        OCR 提取 · BERT 初判 · 大模型综合输出 — 请选择身份进入对应子系统（新标签页打开）
      </p>
    </header>

    <section class="portal-grid" aria-label="子系统入口">
      <article
        class="entry entry--user"
        role="button"
        tabindex="0"
        @click="goToSystem('user')"
        @keydown.enter.prevent="goToSystem('user')"
      >
        <div class="entry__accent" aria-hidden="true" />
        <div class="entry__icon" aria-hidden="true">
          <el-icon :size="40"><User /></el-icon>
        </div>
        <h2 class="entry__title">普通用户</h2>
        <p class="entry__text">上传文本 / 图片 / 图文，获取结构化研判与历史记录。</p>
        <el-button type="primary" class="entry__btn" round @click.stop="goToSystem('user')">
          进入用户端
        </el-button>
      </article>

      <article
        class="entry entry--admin"
        role="button"
        tabindex="0"
        @click="goToSystem('admin')"
        @keydown.enter.prevent="goToSystem('admin')"
      >
        <div class="entry__accent" aria-hidden="true" />
        <div class="entry__icon" aria-hidden="true">
          <el-icon :size="40"><Setting /></el-icon>
        </div>
        <h2 class="entry__title">平台管理员</h2>
        <p class="entry__text">用户与权限、审核队列、数据统计与模型与系统配置。</p>
        <el-button type="danger" class="entry__btn" round @click.stop="goToSystem('admin')">
          进入管理端
        </el-button>
      </article>

      <article
        class="entry entry--audit"
        role="button"
        tabindex="0"
        @click="goToSystem('audit')"
        @keydown.enter.prevent="goToSystem('audit')"
      >
        <div class="entry__accent" aria-hidden="true" />
        <div class="entry__icon" aria-hidden="true">
          <el-icon :size="40"><DocumentChecked /></el-icon>
        </div>
        <h2 class="entry__title">专业审核员</h2>
        <p class="entry__text">领取任务、查看 AI 辅助结论并提交复核意见。</p>
        <el-button type="success" class="entry__btn" round @click.stop="goToSystem('audit')">
          进入审核端
        </el-button>
      </article>
    </section>

    <footer class="portal-foot">
      各端地址可在 <code class="portal-code">fake-science-identify-all/.env.development</code> 中调整
    </footer>
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { User, Setting, DocumentChecked } from '@element-plus/icons-vue'

const userOrigin = import.meta.env.VITE_USER_APP_ORIGIN || 'http://127.0.0.1:3000'
const adminOrigin = import.meta.env.VITE_ADMIN_APP_ORIGIN || 'http://127.0.0.1:3001'
const auditOrigin = import.meta.env.VITE_AUDIT_APP_ORIGIN || 'http://127.0.0.1:3002'

const goToSystem = (role) => {
  const urlMap = {
    user: `${userOrigin.replace(/\/$/, '')}/login`,
    admin: `${adminOrigin.replace(/\/$/, '')}/login`,
    audit: `${auditOrigin.replace(/\/$/, '')}/login`
  }
  const url = urlMap[role]
  const w = window.open(url, '_blank')
  if (w) {
    w.opener = null
  } else {
    ElMessage.warning('浏览器拦截了新窗口，请允许本站弹出窗口，或按住 Ctrl 再点击。')
  }
}
</script>

<style scoped>
.portal-page {
  position: relative;
  min-height: 100vh;
  width: 100%;
  overflow-x: hidden;
  padding: clamp(2.5rem, 6vw, 4.5rem) clamp(1.25rem, 4vw, 2rem) 2.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  font-family:
    'Segoe UI',
    system-ui,
    -apple-system,
    'PingFang SC',
    'Microsoft YaHei',
    sans-serif;
  color: #3d3a36;
}

.portal-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  background:
    linear-gradient(180deg, #fdfcfa 0%, #f5f2ed 42%, #efeae3 100%);
}

.portal-bg::before {
  content: '';
  position: absolute;
  inset: 0;
  opacity: 0.45;
  background-image: radial-gradient(circle at 1px 1px, rgba(120, 100, 80, 0.07) 1px, transparent 0);
  background-size: 28px 28px;
  pointer-events: none;
}

.portal-bg::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(115deg, transparent 40%, rgba(255, 255, 255, 0.65) 48%, transparent 56%);
  pointer-events: none;
}

.portal-orb {
  position: fixed;
  border-radius: 50%;
  filter: blur(72px);
  opacity: 0.55;
  pointer-events: none;
  z-index: 0;
}

.portal-orb--1 {
  width: min(480px, 85vw);
  height: min(480px, 85vw);
  top: -8%;
  right: -5%;
  background: #d4e4f7;
}

.portal-orb--2 {
  width: min(380px, 70vw);
  height: min(380px, 70vw);
  bottom: 5%;
  left: -6%;
  background: #e8e0d4;
}

@media (prefers-reduced-motion: reduce) {
  .entry {
    transition: none;
  }
}

.portal-hero {
  position: relative;
  z-index: 1;
  text-align: center;
  max-width: 40rem;
  margin-bottom: clamp(2rem, 5vw, 3.25rem);
}

.portal-eyebrow {
  margin: 0 0 0.5rem;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.35em;
  text-transform: uppercase;
  color: #8a8278;
}

.portal-title {
  margin: 0 0 0.35rem;
  font-size: clamp(2.5rem, 7vw, 3.35rem);
  font-weight: 700;
  letter-spacing: 0.18em;
  color: #2c2825;
  line-height: 1.15;
}

.portal-tagline {
  margin: 0 0 1rem;
  font-size: 0.95rem;
  font-weight: 500;
  color: #6b6560;
  letter-spacing: 0.12em;
}

.portal-lead {
  margin: 0;
  font-size: 0.875rem;
  line-height: 1.75;
  color: #7a736c;
  max-width: 34rem;
  margin-left: auto;
  margin-right: auto;
}

.portal-grid {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 68rem;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: clamp(1.25rem, 2.5vw, 1.75rem);
}

.entry {
  position: relative;
  padding: 2rem 1.5rem 1.65rem;
  border-radius: 1.125rem;
  cursor: pointer;
  text-align: center;
  outline: none;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(62, 56, 48, 0.08);
  box-shadow:
    0 1px 2px rgba(62, 56, 48, 0.04),
    0 12px 40px -12px rgba(62, 56, 48, 0.12);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  transition:
    transform 0.32s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.32s ease,
    border-color 0.25s ease;
}

.entry:focus-visible {
  border-color: rgba(180, 160, 130, 0.55);
  box-shadow: 0 0 0 3px rgba(200, 180, 150, 0.35);
}

.entry:hover {
  transform: translateY(-5px);
  border-color: rgba(62, 56, 48, 0.12);
  box-shadow:
    0 2px 4px rgba(62, 56, 48, 0.06),
    0 24px 48px -16px rgba(62, 56, 48, 0.14);
}

.entry__accent {
  position: absolute;
  top: 0;
  left: 1.25rem;
  right: 1.25rem;
  height: 3px;
  border-radius: 0 0 4px 4px;
  opacity: 0.85;
}

.entry--user .entry__accent {
  background: linear-gradient(90deg, #5b9bd5, #7eb8e8);
}
.entry--admin .entry__accent {
  background: linear-gradient(90deg, #c45c4a, #e07a66);
}
.entry--audit .entry__accent {
  background: linear-gradient(90deg, #5a9e6f, #7ab88c);
}

.entry__icon {
  width: 4.25rem;
  height: 4.25rem;
  margin: 0 auto 1.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: #fff;
  box-shadow: 0 8px 24px -6px rgba(62, 56, 48, 0.2);
}

.entry--user .entry__icon {
  background: linear-gradient(145deg, #5b9bd5, #3d7ab8);
}
.entry--admin .entry__icon {
  background: linear-gradient(145deg, #c45c4a, #a34438);
}
.entry--audit .entry__icon {
  background: linear-gradient(145deg, #5a9e6f, #3d7a52);
}

.entry__title {
  margin: 0 0 0.65rem;
  font-size: 1.15rem;
  font-weight: 700;
  color: #2c2825;
  letter-spacing: 0.06em;
}

.entry__text {
  margin: 0 0 1.35rem;
  font-size: 0.8125rem;
  line-height: 1.65;
  color: #6b6560;
  min-height: 2.75em;
}

.entry__btn {
  width: 100%;
  max-width: 14rem;
  font-weight: 600;
}

.portal-foot {
  position: relative;
  z-index: 1;
  margin-top: auto;
  padding-top: 2.75rem;
  font-size: 0.72rem;
  color: #9a928a;
  text-align: center;
  line-height: 1.6;
}

.portal-code {
  padding: 0.12rem 0.45rem;
  font-size: 0.68rem;
  font-family: ui-monospace, Consolas, monospace;
  color: #5c5650;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(62, 56, 48, 0.1);
  border-radius: 0.35rem;
}

@media (max-width: 900px) {
  .portal-grid {
    grid-template-columns: 1fr;
    max-width: 22rem;
  }

  .entry__text {
    min-height: unset;
  }
}
</style>
