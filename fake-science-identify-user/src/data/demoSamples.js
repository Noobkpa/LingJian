/**
 * 首页「一键体验」示例来源说明：
 * - 文案：摘自仓库 Bert/hf/train.jsonl（BERT 多标签训练集）
 * - 图片：`public/demo-samples/` 下 JPEG；图中语句选自 ocr/test/test_label.txt（OCR 评测列表常见伪科普主题），由构建脚本本地渲染生成，便于无原始图片仓库时仍可演示 OCR。
 */

/** @type {{ id: string, title: string, text: string }[]} */
export const DEMO_TEXT_SAMPLES = [
  {
    id: 'bert-train-1',
    title: '痛风谣言',
    text:
      '最新提醒：痛风人群注意，所谓内部经验称该方案能快速调理，很多人跟风。'
  },
  {
    id: 'bert-train-2',
    title: '纳米续航',
    text: '纳米电池涂层可让手机续航翻倍。'
  },
  {
    id: 'bert-train-5',
    title: '规范用药',
    text:
      '慢病患者按医嘱规范用药通常更安全，应根据个人情况调整方案。'
  },
  {
    id: 'bert-train-4',
    title: '抗癌传言',
    text:
      '哈佛大学研究团队发现某食材可100%抑制癌症复发。'
  },
  {
    id: 'bert-train-13',
    title: '适度运动',
    text:
      '高血压患者每周适度有氧运动有助于心血管健康，应根据个人情况调整方案。'
  },
  {
    id: 'bert-train-15',
    title: '控盐饮食',
    text:
      '高血压患者控盐饮食有助于血压管理，不建议自行停药或换药。'
  },
  {
    id: 'bert-train-28',
    title: '佩戴口罩',
    text: '口罩不会导致缺氧，正确佩戴可降低呼吸道传播风险。'
  },
  {
    id: 'bert-train-29',
    title: '定期体检',
    text:
      '普通人群定期体检有助于早期识别风险因素，应以循证医学证据为依据。'
  },
  {
    id: 'bert-train-26',
    title: '体温解读',
    text: '体温正常不代表没有感染，应结合症状和检测结果评估。'
  }
]

/** @type {{ id: string, title: string, src: string, note: string }[]} */
export const DEMO_IMAGE_SAMPLES = [
  {
    id: 'ocr-test-080',
    title: '剩饭致癌',
    src: '/demo-samples/ocr_sample_1.jpg',
    note: '文案条目见 ocr/test/test_label.txt → images/080_pseudoscience.jpg'
  },
  {
    id: 'ocr-test-278',
    title: '饮水量',
    src: '/demo-samples/ocr_sample_2.jpg',
    note: '文案条目见 ocr/test/test_label.txt → images/278_pseudoscience.jpg'
  },
  {
    id: 'ocr-test-230',
    title: '土鸡蛋',
    src: '/demo-samples/ocr_sample_3.jpg',
    note: '文案条目见 ocr/test/test_label.txt → images/230_pseudoscience.jpg'
  }
]
