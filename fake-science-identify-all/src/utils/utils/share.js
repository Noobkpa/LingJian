import html2canvas from 'html2canvas'
import QRCode from 'qrcode'

// 生成分享二维码
export const generateQRCode = async (url, canvasId, width = 120, height = 120) => {
  try {
    await QRCode.toCanvas(document.getElementById(canvasId), url, {
      width,
      height,
      margin: 1,
      color: {
        dark: '#4080FF',
        light: '#ffffff'
      }
    })
  } catch (error) {
    console.error('二维码生成失败', error)
  }
}

// 生成分享图片
export const generateShareImage = async (elementId) => {
  const element = document.getElementById(elementId)
  if (!element) return null

  try {
    const canvas = await html2canvas(element, {
      useCORS: true,
      scale: 2,
      backgroundColor: '#ffffff',
      logging: false
    })
    // 转成blob文件
    const blob = await new Promise((resolve) => {
      canvas.toBlob((blob) => resolve(blob), 'image/png', 1.0)
    })
    // 生成下载链接
    const downloadUrl = URL.createObjectURL(blob)
    return {
      blob,
      downloadUrl
    }
  } catch (error) {
    console.error('分享图片生成失败', error)
    return null
  }
}

// 复制分享链接
export const copyShareLink = async (link) => {
  try {
    await navigator.clipboard.writeText(link)
    return true
  } catch (error) {
    // 降级方案
    const input = document.createElement('input')
    input.value = link
    document.body.appendChild(input)
    input.select()
    document.execCommand('copy')
    document.body.removeChild(input)
    return true
  }
}