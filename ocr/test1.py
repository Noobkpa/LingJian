import paddle
print("GPU 是否可用:", paddle.device.is_compiled_with_cuda())

from paddleocr import PaddleOCR

# 1. 初始化模型 (使用默认模型，去掉那些复杂的参数)
# PaddleOCR 3.0.0 不支持 det_model_name 这种写法了
ocr = PaddleOCR(use_textline_orientation=True)

# 2. 图片路径
img_path = r"D:\Project_Root\PaddleOCR\train_data\test\images\004_pseudoscience.jpg"

# 3. 执行识别
result = ocr.predict(img_path)

# 4. 打印结果
print("\n--- 提取到的文本内容如下 ---")

if result:
    ocr_data = result[0]
    for text, score in zip(ocr_data['rec_texts'], ocr_data['rec_scores']):
        print(f"文本: {text} | 置信度: {score:.4f}")
else:
    print("未识别到任何文字，请检查图片路径或图片内容。")