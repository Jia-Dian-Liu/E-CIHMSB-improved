# embed.py → 嵌入模組（支援文字和圖片，含對象密鑰與驗證碼）

import numpy as np
import hashlib

from config import Q_LENGTH, TOTAL_AVERAGES_PER_UNIT, BLOCK_SIZE, calculate_capacity
from permutation import generate_Q_from_block, apply_Q_three_rounds
from image_processing import calculate_hierarchical_averages
from binary_operations import get_msbs
from mapping import map_to_z
from secret_encoding import text_to_binary, image_to_binary

# 驗證碼長度（bits）
CHECKSUM_BITS = 8


def generate_checksum(contact_key, cover_image):
    """
    功能:
        生成驗證碼（8 bits）
    
    參數:
        contact_key: 對象專屬密鑰
        cover_image: 載體圖片（numpy array）
    
    返回:
        checksum_bits: 8 個 bit 的列表
    
    原理:
        結合 contact_key 和載體圖片特徵，生成唯一的驗證碼
        - 對象錯 → 驗證碼錯
        - 載體錯 → 驗證碼錯
    """
    # 計算載體圖片的特徵（像素總和）
    image_feature = int(np.sum(cover_image)) % (2**32)
    
    # 組合 key 和圖片特徵
    if contact_key:
        combined = f"{contact_key}_{image_feature}"
    else:
        combined = f"default_{image_feature}"
    
    # 用 SHA256 生成 hash
    hash_bytes = hashlib.sha256(combined.encode('utf-8')).digest()
    
    # 取前 1 個 byte，轉成 8 bits
    first_byte = hash_bytes[0]
    checksum_bits = [int(b) for b in format(first_byte, '08b')]
    
    return checksum_bits


def shuffle_bits(bits, key):
    """
    功能:
        用密鑰打亂位元順序
    
    參數:
        bits: 位元列表
        key: 密鑰字串
    
    返回:
        打亂後的位元列表
    
    原理:
        用 key 的 hash 值作為 seed，生成固定的打亂順序
        同樣的 key 永遠產生同樣的打亂順序
    """
    if not key or len(bits) == 0:
        return bits
    
    seed = hash(key) % 2147483647
    np.random.seed(seed)
    order = np.random.permutation(len(bits))
    
    return [bits[i] for i in order]


def embed_secret(cover_image, secret, secret_type='text', contact_key=None):
    """
    功能:
        將機密內容嵌入無載體圖片，產生 Z 碼
    
    參數:
        cover_image: numpy array，灰階圖片 (H×W) 或彩色圖片 (H×W×3)
        secret: 機密內容（字串或 PIL Image）
        secret_type: 'text' 或 'image'
        contact_key: 對象專屬密鑰（字串），用於加密
    
    返回:
        z_bits: Z 碼位元列表
        capacity: 圖片的總容量
        info: 額外資訊（機密內容的相關資訊）
    
    格式:
        [8 bits 驗證碼] + [1 bit 類型標記] + [機密內容]
        驗證碼: 用於快速檢查對象/載體是否正確
        類型標記: 0 = 文字, 1 = 圖片
    
    安全機制:
        1. 驗證碼：快速檢查對象/載體是否正確
        2. Q 密鑰：保護每個區塊的「值」
        3. Seed 打亂：保護機密的「位置」
    """
    cover_image = np.array(cover_image)
    
    # ========== 步驟 1：圖片預處理 ==========
    if len(cover_image.shape) == 3:
        cover_image = (
            0.299 * cover_image[:, :, 0] + 
            0.587 * cover_image[:, :, 1] + 
            0.114 * cover_image[:, :, 2]
        ).astype(np.uint8)
    
    height, width = cover_image.shape
    
    if height % 8 != 0 or width % 8 != 0:
        raise ValueError(f"圖片大小必須是 8 的倍數！當前大小: {width}×{height}")
    
    # ========== 步驟 2：計算容量並檢查 ==========
    num_rows = height // BLOCK_SIZE
    num_cols = width // BLOCK_SIZE
    num_units = num_rows * num_cols
    capacity = num_units * TOTAL_AVERAGES_PER_UNIT
    
    # ========== 步驟 3：生成驗證碼（新增！）==========
    checksum_bits = generate_checksum(contact_key, cover_image)
    
    # ========== 步驟 4：將機密內容轉成二進位 ==========
    if secret_type == 'text':
        type_marker = [0]
        content_bits = text_to_binary(secret)
        info = {'type': 'text', 'length': len(secret), 'bits': len(content_bits) + 1 + CHECKSUM_BITS}
    else:
        type_marker = [1]
        content_bits, orig_size, mode = image_to_binary(secret, capacity - 1 - CHECKSUM_BITS)
        info = {'type': 'image', 'size': orig_size, 'mode': mode, 'bits': len(content_bits) + 1 + CHECKSUM_BITS}
    
    # ========== 步驟 5：組合完整的 secret_bits ==========
    # 格式：[驗證碼 8 bits] + [類型 1 bit] + [內容]
    secret_bits = checksum_bits + type_marker + content_bits
    
    if len(secret_bits) > capacity:
        raise ValueError(
            f"機密內容太大！需要 {len(secret_bits)} bits，但容量只有 {capacity} bits"
        )
    
    # ========== 步驟 6：用 contact_key 打亂機密位元順序 ==========
    secret_bits = shuffle_bits(secret_bits, contact_key)
    
    # ========== 步驟 7：對每個 8×8 區塊進行嵌入 ==========
    z_bits = []
    secret_bit_index = 0
    finished = False
    
    for i in range(num_rows):
        if finished:
            break
        
        for j in range(num_cols):
            if secret_bit_index >= len(secret_bits):
                finished = True
                break
            
            start_row = i * BLOCK_SIZE
            end_row = start_row + BLOCK_SIZE
            start_col = j * BLOCK_SIZE
            end_col = start_col + BLOCK_SIZE
            block = cover_image[start_row:end_row, start_col:end_col]
            
            Q = generate_Q_from_block(block, Q_LENGTH, contact_key=contact_key)
            averages_21 = calculate_hierarchical_averages(block)
            reordered_averages = apply_Q_three_rounds(averages_21, Q)
            msbs = get_msbs(reordered_averages)
            
            for k in range(TOTAL_AVERAGES_PER_UNIT):
                if secret_bit_index >= len(secret_bits):
                    finished = True
                    break
                
                secret_bit = secret_bits[secret_bit_index]
                msb = msbs[k]
                z_bit = map_to_z(secret_bit, msb)
                z_bits.append(z_bit)
                
                secret_bit_index += 1
    
    return z_bits, capacity, info
