<template>
  <div class="help-container">
    <div class="page-header">
      <h2 class="page-title">帮助中心</h2>
      <p class="page-desc">常见问题解答，帮助您快速上手系统使用</p>
    </div>

    <div class="faq-card base-card">
      <el-collapse v-model="activeNames" accordion>
        <el-collapse-item title="什么是多模态伪科普识别？支持哪些内容类型？" name="1">
          <div class="faq-content">
            <p>本系统的多模态伪科普识别，是指支持对文本、图片、图文混合三类社交媒体主流内容形式进行伪科普智能识别，具体支持类型如下：</p>
            <ul>
              <li><strong>文本识别</strong>：支持纯文本内容的伪科普识别，最大支持5000字文本内容</li>
              <li><strong>图片识别</strong>：支持单张/多张图片识别，通过OCR技术提取图片中的文字内容，分析图片中的伪科普信息</li>
              <li><strong>图文混合识别</strong>：同时支持文本+图片上传，系统将综合分析图文内容，精准识别图文不符、文本真图片假等复杂伪科普场景</li>
            </ul>
          </div>
        </el-collapse-item>

        <el-collapse-item title="系统的风险等级是如何划分的？" name="2">
          <div class="faq-content">
            <p>系统将伪科普风险划分为三个等级，不同等级的判定标准如下：</p>
            <ul>
              <li><strong class="risk-high">高风险（疑似伪科普）</strong>：内容存在多处明确的科学事实错误、逻辑谬误、虚假疗效宣传，具备典型的伪科普特征，误导性极强</li>
              <li><strong class="risk-middle">中风险（需谨慎阅读）</strong>：内容存在部分不严谨表述、片面化结论、疑似科学事实错误，存在一定的误导性，需谨慎辨别</li>
              <li><strong class="risk-low">低风险（可信科普内容）</strong>：内容科学严谨、事实准确、逻辑通顺，无伪科普特征，属于正规可信的科普内容</li>
            </ul>
          </div>
        </el-collapse-item>

        <el-collapse-item title="识别结果的判定依据是什么？" name="3">
          <div class="faq-content">
            <p>系统基于BERT+LLM双模型协同推理，从多个维度对内容进行综合判定，核心判定依据包括：</p>
            <ul>
              <li><strong>科学事实校验</strong>：校验内容中的科学知识点是否符合客观科学事实，是否存在篡改数据、歪曲科学结论的情况</li>
              <li><strong>逻辑谬误识别</strong>：识别内容中是否存在因果谬误、权威伪造、以偏概全、偷换概念等常见逻辑错误</li>
              <li><strong>显性特征匹配</strong>：识别内容中的绝对化用语、术语堆砌、虚假疗效宣传、违规承诺等典型伪科普显性特征</li>
              <li><strong>图文一致性校验</strong>：针对图文混合内容，校验文本与图片内容是否一致，是否存在图文不符、图片误导等情况</li>
            </ul>
          </div>
        </el-collapse-item>

        <el-collapse-item title="上传的内容和识别结果会被泄露吗？" name="4">
          <div class="faq-content">
            <p>我们严格遵守《网络安全法》《个人信息保护法》相关法律法规，全力保护您的隐私与数据安全：</p>
            <ul>
              <li>您上传的内容仅用于本次伪科普识别，不会用于任何其他商业用途，不会向第三方泄露</li>
              <li>所有上传内容、识别结果仅您本人可查看，系统采用严格的权限管控与数据加密措施</li>
              <li>您可以随时在识别历史中删除单条或全部识别记录，删除后数据将彻底清除，无法恢复</li>
              <li>注销账号后，您的所有个人信息、上传内容、识别记录将被全部清空，无任何数据残留</li>
            </ul>
          </div>
        </el-collapse-item>

        <el-collapse-item title="识别结果不准确怎么办？" name="5">
          <div class="faq-content">
            <p>如果您对识别结果有异议，可通过以下方式反馈，帮助我们持续优化系统识别能力：</p>
            <ul>
              <li>在识别结果页面，点击「反馈」按钮，填写您的异议内容与正确结论，我们将由专业审核人员对内容进行复核</li>
              <li>您的反馈数据将进入模型优化任务池，用于优化Prompt模板与模型微调，持续提升系统识别准确率</li>
              <li>系统会定期针对高发场景、识别短板进行专项优化，针对养生、医疗、科技三类高发伪科普场景，专项识别准确率已达92%以上</li>
            </ul>
          </div>
        </el-collapse-item>

        <el-collapse-item title="分享功能如何使用？支持哪些分享方式？" name="6">
          <div class="faq-content">
            <p>系统提供了便捷的识别结果分享功能，助力科学辟谣传播，具体使用方式如下：</p>
            <ul>
              <li>在识别结果页面，点击「分享结果」按钮，即可打开分享弹窗</li>
              <li><strong>链接分享</strong>：点击「复制分享链接」，即可复制识别结果详情页链接，可粘贴至微信、微博等社交平台分享</li>
              <li><strong>图片分享</strong>：点击「下载分享图片」，系统将自动生成带二维码的辟谣图片，保存到本地后可直接发布至各大社交平台</li>
              <li>分享图片包含核心风险等级、判定依据与详情二维码，他人扫码即可查看完整识别结果</li>
            </ul>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>

    <div class="guide-card base-card">
      <h3 class="guide-title">新手操作指南</h3>
      <div class="guide-steps">
        <div class="step-item">
          <div class="step-num">1</div>
          <div class="step-content">
            <h4>登录账号</h4>
            <p>注册并登录系统账号，即可使用全部识别功能，系统会自动保存您的识别历史</p>
          </div>
        </div>
        <div class="step-item">
          <div class="step-num">2</div>
          <div class="step-content">
            <h4>选择内容类型</h4>
            <p>在首页选择文本、图片或图文混合识别类型，上传需要识别的内容</p>
          </div>
        </div>
        <div class="step-item">
          <div class="step-num">3</div>
          <div class="step-content">
            <h4>提交识别</h4>
            <p>点击「立即识别」按钮，系统将自动完成内容分析与伪科普识别，等待数秒即可获取结果</p>
          </div>
        </div>
        <div class="step-item">
          <div class="step-num">4</div>
          <div class="step-content">
            <h4>查看结果</h4>
            <p>查看详细的风险等级、综合得分与判定依据，可对结果进行收藏、分享、反馈操作</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const activeNames = ref(['1'])
</script>

<style scoped>
.help-container {
  width: 100%;
  max-width: 900px;
  margin: 0 auto;
}
.page-header {
  text-align: center;
  margin-bottom: 32px;
}
.page-title {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
}
.page-desc {
  font-size: 14px;
  color: #606266;
  margin: 0;
}
.faq-content p {
  margin-bottom: 12px;
  line-height: 1.6;
}
.faq-content ul {
  padding-left: 20px;
  margin: 0;
}
.faq-content li {
  line-height: 1.8;
  margin-bottom: 8px;
}
.guide-title {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 24px;
}
.guide-steps {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.step-item {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}
.step-num {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #4080FF;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.step-content h4 {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 4px;
}
.step-content p {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  margin: 0;
}
</style>