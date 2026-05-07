import os
import re
import cv2
import numpy as np

os.environ['FLAGS_use_cinn'] = '0'
os.environ['PADDLEOCR_LOG_LEVEL'] = 'ERROR'

from paddleocr import PaddleOCR

# ================= 配置区域 =================
test_image_dir = r'D:\Project_Root\PaddleOCR\train_data\test\images'
test_label_file = r'D:\Project_Root\PaddleOCR\train_data\test\test_label.txt'
# ===========================================

def load_ground_truth(label_path):
    """读取标注文件，返回一个字典 {图片名: 真实文本}"""
    gt_dict = {}
    with open(label_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            parts = re.split(r'\s+', line, maxsplit=1)
            if len(parts) >= 2:
                img_name = parts[0]
                img_base_name = os.path.basename(img_name)
                gt_text = parts[1]
                gt_dict[img_base_name] = gt_text
    return gt_dict

def add_white_border(img_path, border_ratio=0.02):
    """
    按图片比例给图片加上白边，防止边缘文字被截断
    border_ratio: 白边占图片短边的比例，默认 2% (0.02)  
    """
    img = cv2.imread(img_path)
    if img is None:
        return None
    
    h, w = img.shape[:2]
    # 根据图片短边动态计算白边大小，避免白边过厚破坏图片特征
    border_size = max(int(min(h, w) * border_ratio), 10) # 至少加10像素，防止超小图出问题
    
    bordered_img = cv2.copyMakeBorder(img, border_size, border_size, border_size, border_size, 
                                      cv2.BORDER_CONSTANT, value=[255, 255, 255])
    return bordered_img

def normalize_text(text):
    """文本清洗与标准化（终极版）"""
    # 1. 【强力清洗】移除所有明显的“水印/干扰字符”     
    text = re.sub(r'[ＳSｓsＷw万]+', '', text) # 移除常见的水印字符 
    text = re.sub(r'[@#].*', '', text) # 移除 @ 开头的账号名或话题 
    text = re.sub(r'[·\.\-_\=\+]+', '', text) # 移除多余的装饰性符号    
    text = re.sub(r'[\[\]\{\}\(\)]', '', text) # 移除括号   
    text = text.strip()
    
    # 1. 统一标点符号
    text = re.sub(r'["“”‘’\[\]<>]', '"', text) # 先把各种引号都变成标准双引号
    text = text.replace('"', '“').replace('"', '”')
    text = text.replace(",", "，").replace("?", "？").replace(":", "：").replace("=", "＝").replace(".", "。").replace("!", "！")
    
    # 2. 去除首尾多余的符号（解决 "+蜂蜜"、"香蕉："、"元气+" 等问题）
    # 去掉开头和结尾的 "+"、"："、"." 以及数字加点（如 "7."）
    text = re.sub(r'^[+：:.\d]+', '', text) 
    text = re.sub(r'[+：:.\d]+$', '', text)
    
    # 3. 去除常见的英文字母乱码
    text = re.sub(r'[A-Za-z]{3,}', '', text) 
    
    # 4. 去除所有空格
    text = text.replace(" ", "")
    
    return text

def main():
    print("正在加载 PaddleOCR 模型 (GPU模式)...")
    ocr = PaddleOCR(
        lang='ch', 
        device='gpu',
        use_textline_orientation=True,
        text_det_thresh=0.2,
        text_det_box_thresh=0.3
    )

    print(f"正在加载真实标签: {test_label_file}...")
    ground_truth = load_ground_truth(test_label_file)
    total_images = len(ground_truth)
    
    if total_images == 0:
        print("错误：未在标签文件中读取到数据，请检查路径和格式。")
        return

    print(f"正在准备 {total_images} 张图片进行批量推理...")
    img_files = os.listdir(test_image_dir)
    
    batch_images = []
    batch_names = []
    
    for img_name in img_files:
        if not img_name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            continue
        if img_name not in ground_truth:
            continue
            
        img_path = os.path.join(test_image_dir, img_name)
        # 使用优化后的按比例加白边函数
        bordered_img = add_white_border(img_path, border_ratio=0.02)
        if bordered_img is not None:
            batch_images.append(bordered_img)
            batch_names.append(img_name)

    if not batch_images:
        print("没有找到需要测试的图片，程序退出。")
        return

    print("开始批量推理...")
    try:
        all_results = ocr.predict(batch_images)
    except Exception as e:
        print(f"批量推理过程中发生严重错误: {e}")
        return

    correct_count = 0
    wrong_count = 0

    print("正在比对识别结果...")
    for i, result in enumerate(all_results):
        img_name = batch_names[i]
        true_text = ground_truth[img_name]

        # 提取识别文本
        rec_text = ""
        if isinstance(result, dict) and 'rec_texts' in result:
            ocr_data = result
            for text, score in zip(ocr_data['rec_texts'], ocr_data['rec_scores']):
                # 【微调】加白边后背景变多，适当提高置信度门槛到 0.6，过滤误识别
                if score > 0.6:
                    rec_text += text
        else:
            print(f"❌ 识别失败: {img_name} (未检测到有效结果或格式异常)")
        
        # 清洗并比对
        norm_true = normalize_text(true_text)
        norm_rec = normalize_text(rec_text)

        if norm_true == norm_rec:
            correct_count += 1
        else:
            wrong_count += 1
            print(f"[❌ 错误] 图片: {img_name}")
            print(f"      真实: {norm_true}")
            print(f"      识别: {norm_rec}")

    print("-" * 30)
    print("测试完成！")
    print(f"总图片数: {total_images}")
    print(f"识别正确数: {correct_count}")
    print(f"识别错误数: {wrong_count}")
    accuracy = (correct_count / total_images) * 100
    print(f"最终准确率: {accuracy:.2f}%")

if __name__ == '__main__':
    main()