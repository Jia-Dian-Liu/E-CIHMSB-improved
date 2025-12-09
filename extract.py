# extract.py → 提取模組（支援文字和圖片，含對象密鑰與驗證碼）

import numpy as np
import hashlib

from config import Q_LENGTH, TOTAL_AVERAGES_PER_UNIT, BLOCK_SIZE
from permutation import generate_Q_from_block, apply_Q_three_rounds
from image_processing import calculate_hierarchical_averages
from binary_operations import get_msbs
from mapping import map_from_z
from secret_encoding import binary_to_text, binary_to_image

# 驗證碼長度（bits）- 必須和 embed.py 一致
CHECKSUM_BITS = 8


def generate_checksum(contact_key, cover_image):
    """
    功能:
        生成驗證碼（8 bits）- 和 embed.py 完全相同
    
    參數:
        contact_key: 對象專屬密鑰
        cover_image: 載體圖片（numpy array）
    
    返回:
        checksum_bits: 8 個 bit 的列表
    """
    image_feature = int(np.sum(cover_image)) % (2**32)
    
    if contact_key:
        combined = f"{contact_key}_{image_feature}"
    else:
        combined = f"default_{image_feature}"
    
    hash_bytes = hashlib.sha256(combined.encode('utf-8')).digest()
    first_byte = hash_bytes[0]
    checksum_bits = [int(b) for b in format(first_byte, '08b')]
    
    return checksum_bits


def unshuffle_bits(bits, key):
    """
    功能:
        用密鑰還原位元順序（shuffle_bits 的逆操作）
    
    參數:
        bits: 打亂後的位元列表
        key: 密鑰字串（必須和嵌入時用的相同）
    
    返回:
        還原順序後的位元列表
    """
    if not key or len(bits) == 0:
        return bits
    
    seed = hash(key) % 2147483647
    np.random.seed(seed)
    order = np.random.permutation(len(bits))
    restore_order = np.argsort(order)
    
    return [bits[i] for i in restore_order]


def extract_secret(cover_image, z_bits, secret_type='text', contact_key=None):
    """
    功能:
        從 Z 碼和無載體圖片提取機密內容
    
    參數:
        cover_image: numpy array，灰階圖片 (H×W) 或彩色圖片 (H×W×3)
        z_bits: Z 碼位元列表
        secret_type: 'text' 或 'image'
        contact_key: 對象專屬密鑰（字串），用於解密
    
    返回:
        secret: 還原的機密內容（字串或 PIL Image）
        info: 額外資訊
    
    格式:
        [8 bits 驗證碼] + [1 bit 類型標記] + [機密內容]
    
    會先驗證驗證碼，如果不正確會拋出錯誤
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
    
    # ========== 步驟 2：計算 8×8 區塊數量 ==========
    num_rows = height // BLOCK_SIZE
    num_cols = width // BLOCK_SIZE
    
    # ========== 步驟 3：對每個 8×8 區塊進行提取 ==========
    secret_bits_shuffled = []
    z_bit_index = 0
    finished = False
    
    for i in range(num_rows):
        if finished:
            break
        
        for j in range(num_cols):
            if z_bit_index >= len(z_bits):
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
                if z_bit_index >= len(z_bits):
                    finished = True
                    break
                
                z_bit = z_bits[z_bit_index]
                msb = msbs[k]
                secret_bit = map_from_z(z_bit, msb)
                secret_bits_shuffled.append(secret_bit)
                
                z_bit_index += 1
    
    # ========== 步驟 4：用 contact_key 還原位元順序 ==========
    secret_bits = unshuffle_bits(secret_bits_shuffled, contact_key)
    
    # ========== 步驟 5：驗證驗證碼（新增！）==========
    if len(secret_bits) < CHECKSUM_BITS + 1:
        raise ValueError("提取的位元數不足")
    
    extracted_checksum = secret_bits[:CHECKSUM_BITS]
    expected_checksum = generate_checksum(contact_key, cover_image)
    
    if extracted_checksum != expected_checksum:
        raise ValueError("驗證失敗：對象或載體圖像不正確！")
    
    # ========== 步驟 6：跳過驗證碼和類型標記，解碼內容 ==========
    type_marker = secret_bits[CHECKSUM_BITS]
    content_bits = secret_bits[CHECKSUM_BITS + 1:]
    
    if secret_type == 'text':
        secret = binary_to_text(content_bits)
        info = {
            'type': 'text', 
            'length': len(secret),
            'type_marker': type_marker,
            'total_bits': len(secret_bits),
            'content_bits': len(content_bits)
        }
    else:
        secret, orig_size, is_color = binary_to_image(content_bits)
        info = {
            'type': 'image', 
            'size': orig_size, 
            'is_color': is_color,
            'type_marker': type_marker,
            'total_bits': len(secret_bits),
            'content_bits': len(content_bits)
        }
    
    return secret, info


def detect_and_extract(cover_image, z_bits, contact_key=None):
    """
    功能:
        自動偵測機密類型並提取（含驗證碼快速檢查）
    
    參數:
        cover_image: 無載體圖片
        z_bits: Z 碼
        contact_key: 對象專屬密鑰（字串），用於解密
    
    返回:
        secret: 機密內容
        secret_type: 'text' 或 'image'
        info: 額外資訊
    
    流程:
        1. 先提取所有 bits
        2. 用 contact_key 還原順序
        3. 驗證驗證碼（快速失敗！）
        4. 讀取類型標記並解碼
    """
    cover_image = np.array(cover_image)
    
    if len(cover_image.shape) == 3:
        cover_image = (
            0.299 * cover_image[:, :, 0] + 
            0.587 * cover_image[:, :, 1] + 
            0.114 * cover_image[:, :, 2]
        ).astype(np.uint8)
    
    height, width = cover_image.shape
    num_rows = height // BLOCK_SIZE
    num_cols = width // BLOCK_SIZE
    
    secret_bits_shuffled = []
    z_bit_index = 0
    finished = False
    
    for i in range(num_rows):
        if finished:
            break
        for j in range(num_cols):
            if z_bit_index >= len(z_bits):
                finished = True
                break
            
            block = cover_image[i*BLOCK_SIZE:(i+1)*BLOCK_SIZE, j*BLOCK_SIZE:(j+1)*BLOCK_SIZE]
            Q = generate_Q_from_block(block, Q_LENGTH, contact_key=contact_key)
            averages_21 = calculate_hierarchical_averages(block)
            reordered = apply_Q_three_rounds(averages_21, Q)
            msbs = get_msbs(reordered)
            
            for k in range(TOTAL_AVERAGES_PER_UNIT):
                if z_bit_index >= len(z_bits):
                    finished = True
                    break
                secret_bits_shuffled.append(map_from_z(z_bits[z_bit_index], msbs[k]))
                z_bit_index += 1
    
    # ========== 用 contact_key 還原位元順序 ==========
    secret_bits = unshuffle_bits(secret_bits_shuffled, contact_key)
    
    # ========== 驗證驗證碼（新增！）==========
    if len(secret_bits) < CHECKSUM_BITS + 1:
        raise ValueError("Z 碼太短，無法提取")
    
    extracted_checksum = secret_bits[:CHECKSUM_BITS]
    expected_checksum = generate_checksum(contact_key, cover_image)
    
    if extracted_checksum != expected_checksum:
        raise ValueError("驗證失敗：對象或載體圖像不正確！")
    
    # ========== 讀取類型標記並解碼 ==========
    type_marker = secret_bits[CHECKSUM_BITS]
    content_bits = secret_bits[CHECKSUM_BITS + 1:]
    
    if type_marker == 0:
        # 文字類型
        try:
            text = binary_to_text(content_bits)
            return text, 'text', {
                'type': 'text', 
                'length': len(text),
                'type_marker': type_marker,
                'total_bits': len(secret_bits),
                'content_bits': len(content_bits)
            }
        except Exception as e:
            raise ValueError(f"文字解碼失敗: {e}")
    else:
        # 圖片類型
        try:
            img, orig_size, is_color = binary_to_image(content_bits)
            if img is not None:
                return img, 'image', {
                    'type': 'image', 
                    'size': orig_size, 
                    'is_color': is_color,
                    'type_marker': type_marker,
                    'total_bits': len(secret_bits),
                    'content_bits': len(content_bits)
                }
            else:
                raise ValueError("圖片解碼返回 None")
        except Exception as e:
            raise ValueError(f"圖片解碼失敗: {e}")
