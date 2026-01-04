Python 3.14.0 (tags/v3.14.0:ebf955d, Oct  7 2025, 10:15:03) [MSC v.1944 64 bit (AMD64)] on win32
Enter "help" below or click "Help" above for more information.
# embed.py → 全位元映射版本

import numpy as np

from config import Q_LENGTH, TOTAL_AVERAGES_PER_UNIT, BLOCK_SIZE, BITS_PER_AVERAGE, calculate_capacity
from permutation import generate_Q_from_block, apply_Q_three_rounds
from image_processing import calculate_hierarchical_averages
from binary_operations import get_all_bits_list
from mapping import map_to_z
from secret_encoding import text_to_binary, image_to_binary

def embed_secret(cover_image, secret, secret_type='text', contact_key=None):
    """
    功能:
        將機密內容嵌入無載體圖片，產生 Z 碼（全位元映射版本）
    
    參數:
        cover_image: numpy array，灰階圖片 (H×W) 或彩色圖片 (H×W×3)
        secret: 機密內容（字串或 PIL Image）
        secret_type: 'text' 或 'image'
        contact_key: 對象專屬密鑰（字串），用於加密
    
    返回:
        z_bits: Z 碼位元列表
        capacity: 圖片的總容量
        info: 額外資訊（機密內容的相關資訊）
    
    流程:
        1. 圖片預處理（彩色轉灰階、檢查尺寸）
        2. 計算容量並檢查
        3. 對每個 8×8 區塊進行嵌入（使用 contact_key 生成 Q）
        4. ✨ 新增：每個平均值使用全部 8 個位元進行映射
    
    格式:
        [1 bit 類型標記] + [機密內容]
        類型標記: 0 = 文字, 1 = 圖片
    """
    cover_image = np.array(cover_image)
    
    # ========== 步驟 1：圖片預處理 ==========
    # 1.1 若為彩色圖片，轉成灰階
    if len(cover_image.shape) == 3:
        cover_image = (
            0.299 * cover_image[:, :, 0] + 
            0.587 * cover_image[:, :, 1] + 
            0.114 * cover_image[:, :, 2]
        ).astype(np.uint8)
    
    height, width = cover_image.shape
    
    # 1.2 檢查圖片大小是否為 8 的倍數
    if height % 8 != 0 or width % 8 != 0:
        raise ValueError(f"圖片大小必須是 8 的倍數！當前大小: {width}×{height}")
    
    # ========== 步驟 2：計算容量並檢查 ==========
    # 2.1 計算 8×8 區塊數量
    num_rows = height // BLOCK_SIZE
    num_cols = width // BLOCK_SIZE
    num_units = num_rows * num_cols
    
    # 2.2 計算容量（全位元版本：容量 × 8）
    capacity = num_units * TOTAL_AVERAGES_PER_UNIT * BITS_PER_AVERAGE
    
    # 2.3 將機密內容轉成二進位（加入類型標記）
    if secret_type == 'text':
        type_marker = [0]  # 0 = 文字
        content_bits = text_to_binary(secret)
        info = {'type': 'text', 'length': len(secret), 'bits': len(content_bits) + 1}
    else:
        type_marker = [1]  # 1 = 圖片
        content_bits, orig_size, mode = image_to_binary(secret, capacity - 1)  # 預留 1 bit 給類型標記
        info = {'type': 'image', 'size': orig_size, 'mode': mode, 'bits': len(content_bits) + 1}
    
    # 2.4 組合完整的 secret_bits
    secret_bits = type_marker + content_bits
    
    # 2.5 檢查容量是否足夠
    if len(secret_bits) > capacity:
        raise ValueError(
            f"機密內容太大！需要 {len(secret_bits)} bits，但容量只有 {capacity} bits"
        )
    
    # ========== 步驟 3：對每個 8×8 區塊進行嵌入（全位元映射）==========
    z_bits = []
    secret_bit_index = 0
    finished = False
    
    for i in range(num_rows):
        if finished:
            break
...         
...         for j in range(num_cols):
...             # 檢查是否所有 secret_bits 已處理完
...             if secret_bit_index >= len(secret_bits):
...                 finished = True
...                 break
...             
...             # 3.1 提取這個 8×8 區塊
...             start_row = i * BLOCK_SIZE
...             end_row = start_row + BLOCK_SIZE
...             start_col = j * BLOCK_SIZE
...             end_col = start_col + BLOCK_SIZE
...             block = cover_image[start_row:end_row, start_col:end_col]
...             
...             # 3.2 生成這個區塊專屬的排列密鑰 Q（加入 contact_key）
...             Q = generate_Q_from_block(block, Q_LENGTH, contact_key=contact_key)
...             
...             # 3.3 計算 21 個多層次平均值
...             averages_21 = calculate_hierarchical_averages(block)
...             
...             # 3.4 用 Q 重新排列 21 個平均值
...             reordered_averages = apply_Q_three_rounds(averages_21, Q)
...             
...             # ✨ 3.5 提取排列後的 21 個平均值的全部位元（168 bits）
...             all_bits = get_all_bits_list(reordered_averages)
...             
...             # ✨ 3.6 映射產生 Z 碼（每個位元獨立映射）
...             for k in range(len(all_bits)):
...                 if secret_bit_index >= len(secret_bits):
...                     finished = True
...                     break
...                 
...                 secret_bit = secret_bits[secret_bit_index]
...                 cover_bit = all_bits[k]  # 使用載體圖的對應位元
...                 z_bit = map_to_z(secret_bit, cover_bit)
...                 z_bits.append(z_bit)
...                 
...                 secret_bit_index += 1
...     
