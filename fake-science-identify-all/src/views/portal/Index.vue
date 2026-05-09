<template>
  <div class="portal-page">
    <nav class="portal-nav" aria-label="门户导航">
      <div class="brand-lockup">
        <span class="brand-mark">灵</span>
        <span class="brand-text">灵鉴</span>
      </div>
      <span class="nav-badge">Public Science Risk Platform</span>
    </nav>

    <header class="portal-hero">
      <p class="portal-eyebrow">LingJian</p>
      <h1 class="portal-title">灵鉴伪科普内容识别平台</h1>
      <p class="portal-tagline">多模态识别 · 结构化研判 · 人工复核协同</p>
      <p class="portal-lead">
        面向公众、管理员与专业审核员的统一入口。请选择身份进入对应子系统，系统将在新标签页打开。
      </p>
      <div class="portal-highlights" aria-label="平台能力">
        <span>OCR 图文提取</span>
        <span>BERT 风险初判</span>
        <span>外部大模型研判</span>
      </div>
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
        <p class="entry__kicker">Public Portal</p>
        <h2 class="entry__title">普通用户</h2>
        <p class="entry__text">上传文本 / 图片 / 图文，获取结构化研判与历史记录。</p>
        <el-button type="primary" class="entry__btn" @click.stop="goToSystem('user')">
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
        <p class="entry__kicker">Admin Console</p>
        <h2 class="entry__title">平台管理员</h2>
        <p class="entry__text">用户与权限、审核队列、数据统计与模型与系统配置。</p>
        <el-button type="danger" class="entry__btn" @click.stop="goToSystem('admin')">
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
        <p class="entry__kicker">Review Workspace</p>
        <h2 class="entry__title">专业审核员</h2>
        <p class="entry__text">领取任务、查看 AI 辅助结论并提交复核意见。</p>
        <el-button type="success" class="entry__btn" @click.stop="goToSystem('audit')">
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

const sameSiteOrigin = window.location.origin
const userOrigin = import.meta.env.VITE_USER_APP_ORIGIN || `${sameSiteOrigin}/user`
const adminOrigin = import.meta.env.VITE_ADMIN_APP_ORIGIN || `${sameSiteOrigin}/admin`
const auditOrigin = import.meta.env.VITE_AUDIT_APP_ORIGIN || `${sameSiteOrigin}/audit`

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
  padding: 1.5rem clamp(1.25rem, 4vw, 2rem) 2.5rem;
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
  color: #172033;
  background:
    linear-gradient(180deg, rgba(246, 251, 255, 0.96) 0%, rgba(255, 255, 255, 0.94) 56%, #f5f8fb 100%),
    url('https://images.unsplash.com/photo-1581093458791-9d42e4e4dc46?auto=format&fit=crop&w=1800&q=80') center/cover fixed;
}

.portal-page::before {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(90deg, rgba(23, 123, 116, 0.06) 1px, transparent 1px),
    linear-gradient(rgba(22, 119, 168, 0.05) 1px, transparent 1px);
  background-size: 80px 80px;
  opacity: 0.45;
}

.portal-nav {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 70rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 0;
  margin-bottom: clamp(2rem, 5vw, 3.5rem);
}

.brand-lockup {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
}

.brand-mark {
  display: inline-flex;
  width: 2.25rem;
  height: 2.25rem;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: #177b74;
  color: #fff;
  font-weight: 800;
  box-shadow: 0 10px 24px rgba(23, 123, 116, 0.22);
}

.brand-text {
  font-size: 1.05rem;
  font-weight: 800;
  color: #172033;
}

.nav-badge {
  padding: 0.45rem 0.7rem;
  border: 1px solid #d9e8ee;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.78);
  color: #54707a;
  font-size: 0.75rem;
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
  max-width: 50rem;
  margin-bottom: clamp(2rem, 5vw, 3rem);
}

.portal-eyebrow {
  margin: 0 0 0.5rem;
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0;
  text-transform: uppercase;
  color: #1677a8;
}

.portal-title {
  margin: 0 0 0.75rem;
  font-size: clamp(2.25rem, 6vw, 4rem);
  font-weight: 800;
  letter-spacing: 0;
  color: #13202b;
  line-height: 1.12;
}

.portal-tagline {
  margin: 0 0 1rem;
  font-size: clamp(1rem, 2vw, 1.25rem);
  font-weight: 700;
  color: #177b74;
  letter-spacing: 0;
}

.portal-lead {
  margin: 0;
  font-size: 0.95rem;
  line-height: 1.75;
  color: #5c6b75;
  max-width: 42rem;
  margin-left: auto;
  margin-right: auto;
}

.portal-highlights {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 0.65rem;
  margin-top: 1.4rem;
}

.portal-highlights span {
  padding: 0.5rem 0.75rem;
  border: 1px solid #d8e9ee;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.82);
  color: #3d6670;
  font-size: 0.78rem;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.04);
}

.portal-grid {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 70rem;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: clamp(1.25rem, 2.5vw, 1.75rem);
}

.entry {
  position: relative;
  padding: 1.75rem 1.5rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  text-align: left;
  outline: none;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid #e3edf2;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 18px 48px -28px rgba(15, 23, 42, 0.24);
  transition:
    transform 0.32s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.32s ease,
    border-color 0.25s ease;
}

.entry:focus-visible {
  border-color: rgba(22, 119, 168, 0.55);
  box-shadow: 0 0 0 3px rgba(22, 119, 168, 0.16);
}

.entry:hover {
  transform: translateY(-5px);
  border-color: rgba(22, 119, 168, 0.2);
  box-shadow:
    0 2px 4px rgba(15, 23, 42, 0.06),
    0 26px 52px -22px rgba(15, 23, 42, 0.2);
}

.entry__accent {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  border-radius: 8px 8px 0 0;
  opacity: 1;
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
  width: 3.75rem;
  height: 3.75rem;
  margin: 0 0 1.1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: #fff;
  box-shadow: 0 10px 24px -10px rgba(15, 23, 42, 0.32);
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

.entry__kicker {
  margin: 0 0 0.35rem;
  color: #7a8a94;
  font-size: 0.72rem;
  font-weight: 700;
}

.entry__title {
  margin: 0 0 0.65rem;
  font-size: 1.15rem;
  font-weight: 700;
  color: #172033;
  letter-spacing: 0;
}

.entry__text {
  margin: 0 0 1.35rem;
  font-size: 0.8125rem;
  line-height: 1.65;
  color: #60717c;
  min-height: 2.75em;
}

.entry__btn {
  width: 100%;
  max-width: 14rem;
  font-weight: 600;
  border-radius: 6px;
}

.portal-foot {
  position: relative;
  z-index: 1;
  margin-top: auto;
  padding-top: 2.75rem;
  font-size: 0.72rem;
  color: #80909a;
  text-align: center;
  line-height: 1.6;
}

.portal-code {
  padding: 0.12rem 0.45rem;
  font-size: 0.68rem;
  font-family: ui-monospace, Consolas, monospace;
  color: #42606b;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #d8e9ee;
  border-radius: 0.35rem;
}

@media (max-width: 900px) {
  .portal-grid {
    grid-template-columns: 1fr;
    max-width: 22rem;
  }

  .portal-nav {
    align-items: flex-start;
    flex-direction: column;
    margin-bottom: 2rem;
  }

  .entry__text {
    min-height: unset;
  }
}
</style>
