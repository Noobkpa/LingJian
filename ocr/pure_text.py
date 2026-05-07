import os

# 1. 配置路径
input_file = r"D:\Project_Root\PaddleOCR\train_data\test\batch_result.txt" # 你的原文件
output_file = r"D:\Project_Root\PaddleOCR\train_data\test\pure_text.txt" # 输出的纯文本文件

# 2. 清洗逻辑
with open(input_file, 'r', encoding='utf-8') as f_in, \
     open(output_file, 'w', encoding='utf-8') as f_out:

    for line_num, line in enumerate(f_in):
        # 跳过第一行（标题行）
        if line_num == 0:
            continue
            
        # 跳过空行
        if not line.strip():
            continue
            
        # 分割图片名和文本（基于制表符 \t 分割）
        parts = line.split('\t', 1) # 只分割一次，防止文本里有空格
        
        if len(parts) == 2:
            # 取第二部分（文本部分）
            text = parts[1].strip()
            # 写入文件
            f_out.write(text + '\n') # 每行一个样本

print(f"清洗完成！纯文本已保存至：{output_file}")