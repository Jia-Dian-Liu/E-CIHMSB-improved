
import streamlit as st
import streamlit.components.v1 as components
import numpy as np
from PIL import Image, ImageDraw
import requests
from io import BytesIO
import os
import math
import time
import random
import base64
import qrcode

# 延遲載入 pyzbar（較慢的套件）
@st.cache_resource
def load_pyzbar():
    from pyzbar.pyzbar import decode as decode_qr
    return decode_qr

from config import *
from embed import embed_secret
from extract import detect_and_extract
from secret_encoding import text_to_binary, image_to_binary, binary_to_image

# ==================== 生成高質量圖片函數 ====================
def generate_gradient_image(size, color1, color2, direction='horizontal'):
    img = Image.new('RGB', (size, size))
    for i in range(size):
        ratio = i / size
        r = int(color1[0] + (color2[0] - color1[0]) * ratio)
        g = int(color1[1] + (color2[1] - color1[1]) * ratio)
        b = int(color1[2] + (color2[2] - color1[2]) * ratio)
        for j in range(size):
            if direction == 'horizontal':
                img.putpixel((i, j), (r, g, b))
            else:
                img.putpixel((j, i), (r, g, b))
    return img

def generate_pattern_image(size, pattern_type):
    img = Image.new('RGB', (size, size), 'white')
    draw = ImageDraw.Draw(img)
    if pattern_type == 'gradient_blue':
        return generate_gradient_image(size, (30, 60, 114), (42, 157, 143), 'horizontal')
    return img

# ==================== Icon 圖片轉 Base64 ====================
def get_icon_base64(icon_name):
    """讀取 icons 資料夾的圖片並轉成 base64"""
    icon_path = os.path.join("icons", f"{icon_name}.png")
    if os.path.exists(icon_path):
        with open(icon_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        return f"data:image/png;base64,{data}"
    return ""

# ==================== 全局緩存 ====================
if 'embed_result' not in st.session_state:
    st.session_state.embed_result = None
if 'extract_result' not in st.session_state:
    st.session_state.extract_result = None

# ==================== 對象管理 ====================
import json

CONTACTS_FILE = "contacts.json"

def load_contacts():
    """讀取對象資料"""
    try:
        if os.path.exists(CONTACTS_FILE):
            with open(CONTACTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_contacts(contacts):
    """儲存對象資料"""
    with open(CONTACTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(contacts, f, ensure_ascii=False, indent=2)

if 'contacts' not in st.session_state:
    st.session_state.contacts = load_contacts()

# ==================== 圖片庫設定 ====================
STYLE_CATEGORIES = {
    "建築": "建築", "動物": "動物", "植物": "植物",
    "食物": "食物", "交通": "交通",
}

# 可用尺寸列表
AVAILABLE_SIZES = [64, 128, 256, 512, 1024, 2048, 4096]

# 圖片庫：風格 -> 圖片列表（每張圖片記錄 picsum id）
IMAGE_LIBRARY = {
    "建築": [
        {"id": 29493117, "name": "哈里發塔"},
        {"id": 34132869, "name": "比薩斜塔"},
        {"id": 16457365, "name": "埃菲爾鐵塔"},
        {"id": 236294, "name": "聖彼得大教堂"},
        {"id": 16681013, "name": "謝赫扎耶德大清真寺"},
        {"id": 29144355, "name": "熨斗大樓"},
        {"id": 1650904, "name": "泰坦尼克博物館"},
    ],
    "動物": [
        {"id": 1108099, "name": "拉布拉多"},
        {"id": 568022, "name": "白羊"},
        {"id": 19613749, "name": "兔子"},
        {"id": 7060929, "name": "刺蝟"},
        {"id": 19597261, "name": "松鼠"},
        {"id": 10386190, "name": "梅花鹿"},
        {"id": 34954771, "name": "栗頭蜂虎"},
    ],
    "植物": [
        {"id": 1048024, "name": "仙人掌"},
        {"id": 11259955, "name": "雛菊"},
        {"id": 6830332, "name": "櫻花"},
        {"id": 7048610, "name": "鬱金香"},
        {"id": 18439973, "name": "洋牡丹"},
        {"id": 244796, "name": "木槿花"},
        {"id": 206837, "name": "勿忘我"},
    ],
    "食物": [
        {"id": 28503601, "name": "海鮮燉飯"},
        {"id": 32538755, "name": "紅醬義大利麵"},
        {"id": 1566837, "name": "比薩"},
        {"id": 7245468, "name": "壽司"},
        {"id": 4110272, "name": "水果拼盤"},
        {"id": 6441084, "name": "草莓蛋糕"},
        {"id": 7144558, "name": "鬆餅"},
    ],
    "交通": [
        {"id": 33435422, "name": "摩托車"},
        {"id": 1595483, "name": "自行車"},
        {"id": 2263673, "name": "巴士"},
        {"id": 33519108, "name": "火車"},
        {"id": 33017407, "name": "飛機"},
        {"id": 843633, "name": "遊艇"},
        {"id": 586040, "name": "火箭"},
    ],
}

def get_recommended_size(secret_bits):
    """根據機密大小推薦最小適合尺寸"""
    for size in AVAILABLE_SIZES:
        capacity = calculate_image_capacity(size)
        if capacity >= secret_bits:
            return size
    return AVAILABLE_SIZES[-1]  # 最大尺寸

def get_image_url(pexels_id, size):
    """取得 Pexels 指定尺寸的圖片 URL"""
    return f"https://images.pexels.com/photos/{pexels_id}/pexels-photo-{pexels_id}.jpeg?auto=compress&cs=tinysrgb&w={size}&h={size}&fit=crop"

@st.cache_data(ttl=86400, show_spinner=False)  # 快取 24 小時
def download_image_cached(pexels_id, size):
    """下載並快取圖片（持久化）"""
    url = f"https://images.pexels.com/photos/{pexels_id}/pexels-photo-{pexels_id}.jpeg?auto=compress&cs=tinysrgb&w={size}&h={size}&fit=crop"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.content
    except:
        pass
    return None

def download_image_by_id(pexels_id, size):
    """下載指定 ID 和尺寸的圖片"""
    # 使用持久化快取
    image_data = download_image_cached(pexels_id, size)
    
    if image_data:
        img = Image.open(BytesIO(image_data)).convert('RGB')
        # 確保是正方形
        if img.size[0] != size or img.size[1] != size:
            img = img.resize((size, size), Image.LANCZOS)
        img_gray = img.convert('L')  # 灰階版本供處理用
        return img, img_gray
    
    # 失敗時生成預設圖片
    img = generate_gradient_image(size, (100, 150, 200), (150, 200, 250))
    return img, img.convert('L')

# ==================== 輔助函數 ====================
def calculate_remaining_capacity(capacity_bits, used_bits):
    remaining_bits = capacity_bits - used_bits
    if remaining_bits <= 0:
        return 0, 0
    return remaining_bits // 24, remaining_bits // 8

def calculate_image_capacity(size):
    return (size * size) // 64 * 21

def calculate_required_bits_for_image(image, target_capacity=None):
    original_size, original_mode = image.size, image.mode
    
    # 模擬 image_to_binary_full 的轉換行為
    is_color = original_mode not in ['L', '1', 'LA']
    
    if not is_color:
        has_alpha = False
    elif original_mode == 'P':
        # P 模式：實際轉換後檢查是否有 alpha
        temp_img = image.convert('RGBA')
        # 檢查是否真的有透明像素
        if temp_img.mode == 'RGBA':
            alpha_channel = temp_img.split()[-1]
            has_alpha = alpha_channel.getextrema()[0] < 255  # 有任何透明像素
        else:
            has_alpha = False
    elif original_mode in ['RGBA', 'PA']:
        has_alpha = True
    elif original_mode not in ['RGB', 'RGBA']:
        has_alpha = False  # 會被轉成 RGB
    else:
        has_alpha = False
    
    if is_color:
        header_bits = 66  # 彩色圖片都是 66（原始尺寸32 + 2 + 縮放後尺寸32）
        bits_per_pixel = 32 if has_alpha else 24
    else:
        header_bits, bits_per_pixel = 66, 8  # 灰階也改成 66 bits header（縮放尺寸改用 16 bits）
    
    if target_capacity is None:
        w, h = original_size[0], original_size[1]
        return header_bits + w * h * bits_per_pixel, (w, h)
    
    max_pixels = (target_capacity - header_bits) // bits_per_pixel
    current_pixels = original_size[0] * original_size[1]
    if current_pixels <= max_pixels:
        scaled = original_size
    else:
        ratio = math.sqrt(max_pixels / current_pixels)
        scaled = (max(8, (int(original_size[0] * ratio) // 8) * 8), max(8, (int(original_size[1] * ratio) // 8) * 8))
    return header_bits + scaled[0] * scaled[1] * bits_per_pixel, scaled

def get_size_from_name(image_name):
    return PUBLIC_IMAGES.get(image_name, (512, None))[0]

@st.cache_data(ttl=3600)
def download_public_image_v2(image_name):
    try:
        size, url = PUBLIC_IMAGES[image_name]
        if url.startswith("resize:"):
            actual_url = url.split(":", 2)[2]
            response = requests.get(actual_url, timeout=10)
            image = Image.open(BytesIO(response.content))
            return image.convert('RGB'), image.resize((size, size), Image.Resampling.LANCZOS).convert('L')
        else:
            response = requests.get(url, timeout=10)
            image = Image.open(BytesIO(response.content))
            if image.size != (size, size):
                image = image.resize((size, size), Image.Resampling.LANCZOS)
            return image.convert('RGB'), image.convert('L')
    except Exception as e:
        size = PUBLIC_IMAGES.get(image_name, (512, None))[0]
        return Image.new('RGB', (size, size), (128, 128, 128)), Image.new('L', (size, size), 128)

# ==================== Z碼圖編碼/解碼（正確版：8 bits = 1 pixel）====================

def encode_z_as_image_auto(z_bits):
    """
    Z碼圖編碼：8 bits = 1 pixel
    格式：32 bits (長度) + Z碼內容 + 補齊到 8 的倍數
    """
    # 加入長度 header (32 bits)
    length = len(z_bits)
    length_bits = [int(b) for b in format(length, '032b')]
    full_bits = length_bits + z_bits
    
    # 補齊到 8 的倍數
    if len(full_bits) % 8 != 0:
        padding = 8 - (len(full_bits) % 8)
        full_bits = full_bits + [0] * padding
    
    # 每 8 bits 轉成一個像素值 (0-255)
    pixels = []
    for i in range(0, len(full_bits), 8):
        byte = full_bits[i:i+8]
        pixel_value = int(''.join(map(str, byte)), 2)
        pixels.append(pixel_value)
    
    # 計算圖片尺寸 (盡量接近正方形)
    num_pixels = len(pixels)
    width = int(math.sqrt(num_pixels))
    height = math.ceil(num_pixels / width)
    
    # 補齊像素
    while len(pixels) < width * height:
        pixels.append(0)
    
    # 建立灰階圖片
    image = Image.new('L', (width, height))
    image.putdata(pixels[:width * height])
    
    return image, length


def encode_z_as_image_with_header(z_bits, img_num, img_size):
    """
    Z碼圖編碼（含編號和尺寸）：8 bits = 1 pixel
    格式：32 bits (Z長度) + 16 bits (編號) + 16 bits (尺寸) + Z碼 + 補齊到 8 的倍數
    """
    # 加入 header: 32 bits (Z長度) + 16 bits (編號) + 16 bits (尺寸) = 64 bits
    length = len(z_bits)
    header_bits = [int(b) for b in format(length, '032b')]
    header_bits += [int(b) for b in format(img_num, '016b')]
    header_bits += [int(b) for b in format(img_size, '016b')]
    full_bits = header_bits + z_bits
    
    # 補齊到 8 的倍數
    if len(full_bits) % 8 != 0:
        padding = 8 - (len(full_bits) % 8)
        full_bits = full_bits + [0] * padding
    
    # 每 8 bits 轉成一個像素值 (0-255)
    pixels = []
    for i in range(0, len(full_bits), 8):
        byte = full_bits[i:i+8]
        pixel_value = int(''.join(map(str, byte)), 2)
        pixels.append(pixel_value)
    
    # 計算圖片尺寸 (盡量接近正方形)
    num_pixels = len(pixels)
    width = int(math.sqrt(num_pixels))
    height = math.ceil(num_pixels / width)
    
    # 補齊像素
    while len(pixels) < width * height:
        pixels.append(0)
    
    # 建立灰階圖片
    image = Image.new('L', (width, height))
    image.putdata(pixels[:width * height])
    
    return image, length


def decode_image_to_z_with_header(image):
    """
    Z碼圖解碼（含編號和尺寸）：1 pixel = 8 bits
    格式：32 bits (Z長度) + 16 bits (編號) + 16 bits (尺寸) + Z碼
    """
    # 轉成灰階
    if image.mode != 'L':
        image = image.convert('L')
    
    # 取得所有像素
    pixels = list(image.getdata())
    
    # 每個像素轉成 8 bits
    all_bits = []
    for pixel in pixels:
        bits = [int(b) for b in format(pixel, '08b')]
        all_bits.extend(bits)
    
    # 檢查長度（至少需要 64 bits header）
    if len(all_bits) < 64:
        raise ValueError("Z碼圖片格式錯誤：太小")
    
    # 讀取 header
    z_length = int(''.join(map(str, all_bits[:32])), 2)
    img_num = int(''.join(map(str, all_bits[32:48])), 2)
    img_size = int(''.join(map(str, all_bits[48:64])), 2)
    
    # 驗證長度
    if z_length <= 0 or z_length > len(all_bits) - 64:
        raise ValueError(f"Z碼長度無效：{z_length}")
    
    # 提取 Z碼
    z_bits = all_bits[64:64 + z_length]
    
    return z_bits, img_num, img_size


def decode_image_to_z_auto(image):
    """
    Z碼圖解碼：1 pixel = 8 bits
    格式：32 bits (長度) + Z碼內容
    """
    # 轉成灰階
    if image.mode != 'L':
        image = image.convert('L')
    
    # 取得所有像素
    pixels = list(image.getdata())
    
    # 每個像素轉成 8 bits
    all_bits = []
    for pixel in pixels:
        bits = [int(b) for b in format(pixel, '08b')]
        all_bits.extend(bits)
    
    # 檢查長度
    if len(all_bits) < 32:
        raise ValueError("Z碼圖片格式錯誤：太小")
    
    # 讀取長度 header
    length_bits = all_bits[:32]
    actual_length = int(''.join(map(str, length_bits)), 2)
    
    # 驗證長度
    if actual_length <= 0 or actual_length > len(all_bits) - 32:
        raise ValueError(f"Z碼長度無效：{actual_length}")
    
    # 提取 Z碼
    z_bits = all_bits[32:32 + actual_length]
    
    return z_bits, actual_length

# ==================== Streamlit 頁面配置 ====================
st.set_page_config(page_title="🔐 高效能無載體之機密編碼技術", page_icon="🔐", layout="wide", initial_sidebar_state="collapsed")

# ==================== CSS 樣式（響應式設計）====================
# 調整說明：
# 1) 將 .block-container padding-top 調高，讓標題與卡片往下移動（解決「往上一點」的需求）
# 2) 減少 .anim-card 的 min-height 與 margin-bottom，避免卡片下方過多空白
# 3) 新增通用規則隱藏右下角固定定位的浮動元素（常見為分享/徽章/浮動按鈕）
st.markdown("""
<style>
/* 背景圖片 - 復古紙張紋理 */
.stApp {
    background-image: url('https://i.pinimg.com/1200x/03/c9/99/03c999e78415b51ad02b3d4e92942bcd.jpg');
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
}

/* 隱藏 Streamlit 預設元素 */
header[data-testid="stHeader"],
#MainMenu, footer, .stDeployButton, div[data-testid="stToolbar"] { 
    display: none !important; 
    visibility: hidden !important;
}

/* 增加上方內距，讓標題與卡片往下 */
.block-container { padding-top: 4rem !important; }

/* ==================== 響應式設計核心 ==================== */
/* 限制最大寬度，讓內容不會在大螢幕上拉太開 */
[data-testid="stMain"] > div {
    max-width: 1400px !important;
    margin: 0 auto !important;
}

.block-container {
    max-width: 1400px !important;
    margin: 0 auto !important;
    padding-left: clamp(1rem, 3vw, 3rem) !important;
    padding-right: clamp(1rem, 3vw, 3rem) !important;
}

/* 完全隱藏 Streamlit 所有側邊欄控制按鈕 */
button[data-testid="collapsedControl"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"],
button[data-testid="baseButton-header"],
[data-testid="stSidebarNavCollapseIcon"],
[data-testid="stSidebar"] > button,
[data-testid="stSidebarNav"] button,
[data-testid="stSidebarNavSeparator"],
[data-testid="stSidebarCollapseButton"],
section[data-testid="stSidebar"] > div > button,
section[data-testid="stSidebar"] button[kind="header"],
.st-emotion-cache-1rtdyuf,
.st-emotion-cache-eczf16 {
    display: none !important;
    visibility: hidden !important;
    width: 0 !important;
    height: 0 !important;
    opacity: 0 !important;
    pointer-events: none !important;
}

/* 自訂標籤：可點擊 */
#sidebar-toggle-label {
    position: fixed;
    top: 8px;
    left: 0;
    background: #4A6B8A;
    color: white;
    writing-mode: vertical-rl;
    padding: clamp(12px, 1.5vw, 16px) clamp(6px, 0.8vw, 8px);
    border-radius: 0 8px 8px 0;
    font-size: clamp(18px, 2vw, 24px);
    font-weight: bold;
    z-index: 999999;
    cursor: pointer;
    box-shadow: 2px 0 8px rgba(0,0,0,0.15);
    transition: all 0.3s ease;
}
#sidebar-toggle-label:hover {
    padding-left: 12px;
    background: #5C8AAD;
}

/* 確保主內容區不受側邊欄影響 */
[data-testid="stMain"] {
    margin-left: 0 !important;
    width: 100% !important;
}

/* 側邊欄樣式：固定定位，不影響主內容 */
[data-testid="stSidebar"] {
    position: fixed !important;
    left: 0 !important;
    top: 0 !important;
    height: 100vh !important;
    width: 18rem !important;
    min-width: 18rem !important;
    z-index: 999 !important;
    transition: transform 0.3s ease !important;
    transform: translateX(-100%);
    background: #f5f5f0 !important;
    box-shadow: 4px 0 15px rgba(0,0,0,0.2) !important;
}

[data-testid="stSidebar"].sidebar-open {
    transform: translateX(0) !important;
}

/* 側邊欄標題字體放大 */
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
    font-size: 38px !important;
    font-weight: bold !important;
}

[data-testid="stSidebar"] strong,
[data-testid="stSidebar"] b,
[data-testid="stSidebar"] p strong,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] strong {
    font-size: 24px !important;
}

/* 下拉式選單（Expander）字體放大 */
[data-testid="stSidebar"] [data-testid="stExpander"] summary,
[data-testid="stSidebar"] [data-testid="stExpander"] summary span,
[data-testid="stSidebar"] [data-testid="stExpander"] summary p,
[data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] details summary span {
    font-size: 24px !important;
}

[data-testid="stSidebar"] .stExpander,
[data-testid="stSidebar"] details {
    font-size: 22px !important;
}

[data-testid="stSidebar"] input,
[data-testid="stSidebar"] select,
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label {
    font-size: 18px !important;
}

[data-testid="stSidebar"] button {
    font-size: 18px !important;
}

/* 隱藏側邊欄頂部的 < 收合按鈕 */
[data-testid="stSidebar"] [data-testid="stBaseButton-header"],
[data-testid="stSidebar"] button[kind="header"],
[data-testid="stSidebar"] > div:first-child > button,
[data-testid="stSidebarContent"] > div:first-child button {
    display: none !important;
}

/* ==================== 首頁按鈕隱藏（CSS 備用）==================== */
.home-page-btn + div {
    position: fixed !important;
    top: -9999px !important;
    left: -9999px !important;
    opacity: 0 !important;
}

/* ==================== 全屏選擇頁面樣式（響應式）==================== */
.welcome-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 2vh;
    text-align: center;
    margin-bottom: 1rem;
    /* 將標題往下移動（原本 -2rem，改為正值） */
    margin-top: 2rem;
}

.welcome-title {
    font-size: clamp(36px, 4vw, 60px);
    font-weight: bold;
    margin-bottom: 2rem;
    letter-spacing: clamp(0.15em, 2vw, 0.3em);
    padding-left: clamp(0.15em, 2vw, 0.3em);
    white-space: nowrap;
    background: linear-gradient(135deg, #4A6B8A 0%, #7D5A6B 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.welcome-subtitle {
    font-size: 1rem;
    color: #5D5D5D;
    margin-bottom: 3rem;
}

/* ==================== 動畫卡片樣式（響應式）==================== */
/* 減少卡片最小高度與底部間距，避免卡片下方過多空白 */
.anim-card {
    width: 90%;
    max-width: 450px;
    min-height: clamp(160px, 18vw, 220px);
    padding: clamp(20px, 2.5vw, 30px) clamp(16px, 2vw, 24px);
    border-radius: 20px;
    text-align: center;
    cursor: pointer;
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    position: relative;
    overflow: visible;
    margin: 0 auto;
    margin-bottom: clamp(12px, 1.5vw, 16px);
    box-shadow: 8px 8px 0px 0px rgba(60, 80, 100, 0.4);
}

.anim-card:hover {
    transform: translateY(-6px) scale(1.02);
    box-shadow: 10px 10px 0px 0px rgba(60, 80, 100, 0.45);
}

.anim-card-embed {
    background: linear-gradient(145deg, #7BA3C4 0%, #5C8AAD 100%);
}

.anim-card-extract {
    background: linear-gradient(145deg, #C4A0AB 0%, #A67B85 100%);
}

/* 動畫圖示流程（響應式）*/
.anim-flow {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: clamp(10px, 1.5vw, 18px);
    margin-bottom: clamp(16px, 2vw, 22px);
    font-size: clamp(40px, 5vw, 58px);
    height: clamp(60px, 8vw, 90px);
}

.anim-flow img {
    width: clamp(60px, 8vw, 95px) !important;
    height: clamp(60px, 8vw, 95px) !important;
}

.anim-flow img.anim-icon-arrow {
    width: clamp(50px, 6vw, 75px) !important;
    height: clamp(50px, 6vw, 75px) !important;
}

.anim-icon {
    transition: all 0.3s ease;
}

/* 嵌入動畫效果 */
.anim-card-embed .anim-icon-secret {
    animation: embedPulse 2s ease-in-out infinite;
}

.anim-card-embed .anim-icon-arrow {
    animation: arrowBounce 1.5s ease-in-out infinite;
}

.anim-card-embed .anim-icon-result {
    animation: resultGlow 2s ease-in-out infinite;
}

@keyframes embedPulse {
    0%, 100% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.15); opacity: 0.8; }
}

@keyframes arrowBounce {
    0%, 100% { transform: translateX(0); }
    50% { transform: translateX(8px); }
}

@keyframes resultGlow {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.1); }
}

/* 提取動畫效果 */
.anim-card-extract .anim-icon-source {
    animation: sourcePulse 2s ease-in-out infinite;
}

.anim-card-extract .anim-icon-arrow {
    animation: arrowBounce 1.5s ease-in-out infinite;
}

.anim-card-extract .anim-icon-result {
    animation: extractReveal 2s ease-in-out infinite;
}

@keyframes sourcePulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.1); }
}

@keyframes extractReveal {
    0%, 100% { transform: scale(1) rotate(0deg); opacity: 1; }
    50% { transform: scale(1.2) rotate(5deg); opacity: 0.9; }
}

/* 卡片文字（響應式）*/
.anim-title {
    font-size: clamp(36px, 4vw, 52px);
    font-weight: bold;
    color: #FFFFFF;
    margin-bottom: clamp(12px, 1.5vw, 20px);
    text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
}

.anim-desc {
    font-size: clamp(28px, 3.5vw, 42px);
    color: rgba(255,255,255,0.9);
    line-height: 1.7;
    margin-bottom: 0;
}

.anim-flow-text {
    font-size: 13px;
    color: rgba(255,255,255,0.75);
    font-family: monospace;
    background: rgba(255,255,255,0.15);
    padding: 6px 14px;
    border-radius: 15px;
    display: inline-block;
    margin-top: 8px;
}

/* ==================== 功能頁面樣式（響應式）==================== */
.page-title-embed {
    font-size: clamp(2rem, 4vw, 3rem);
    font-weight: bold;
    background: linear-gradient(135deg, #4A6B8A 0%, #5C8AAD 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.page-title-extract {
    font-size: clamp(2rem, 4vw, 3rem);
    font-weight: bold;
    background: linear-gradient(135deg, #7D5A6B 0%, #A67B85 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* 成功/錯誤框（響應式）*/
.success-box {
    background: linear-gradient(135deg, #4A6B8A 0%, #5C8AAD 100%);
    color: white; 
    padding: clamp(15px, 2vw, 20px) clamp(20px, 2.5vw, 30px); 
    border-radius: 10px;
    margin: 10px 0; 
    display: inline-block; 
    font-size: clamp(22px, 2.5vw, 28px); 
    min-width: min(350px, 90%);
}
.info-box {
    background: linear-gradient(135deg, #4A6B8A 0%, #5C8AAD 100%);
    color: white; 
    padding: clamp(15px, 2vw, 20px) clamp(20px, 2.5vw, 30px); 
    border-radius: 10px;
    margin: 10px 0; 
    display: inline-block; 
    font-size: clamp(20px, 2.2vw, 26px); 
    line-height: 1.9; 
    min-width: min(350px, 90%);
}
.info-tip-box {
    background: linear-gradient(135deg, #5C8AAD 0%, #7BA3C4 100%);
    color: white; 
    padding: clamp(15px, 2vw, 20px) clamp(20px, 2.5vw, 30px); 
    border-radius: 10px;
    margin: 10px 0; 
    display: inline-block; 
    font-size: clamp(20px, 2.2vw, 26px); 
    min-width: min(350px, 90%);
}
.error-box {
    background: linear-gradient(135deg, #8B5A5A 0%, #A67B7B 100%);
    color: white; 
    padding: clamp(15px, 2vw, 20px) clamp(20px, 2.5vw, 30px); 
    border-radius: 10px;
    margin: 10px 0; 
    display: inline-block; 
    font-size: clamp(20px, 2.2vw, 26px); 
    min-width: min(350px, 90%);
}

/* 下載按鈕字體 */
.stDownloadButton button span,
.stDownloadButton button p {
    font-size: 18px !important;
    font-weight: bold !important;
}

/* 結果頁置中容器 */
.result-center-wrapper {
    display: flex;
    justify-content: center;
    align-items: flex-start;
    gap: clamp(30px, 5vw, 60px);
    margin: 20px auto;
    max-width: 900px;
}
.result-left-box, .result-right-box {
    flex: 0 0 auto;
}

/* 功能頁面全域字體放大加粗 - 只針對主區域（響應式）*/
[data-testid="stMain"] .stMarkdown, 
[data-testid="stMain"] .stText, 
[data-testid="stMain"] .stTextArea, 
[data-testid="stMain"] .stRadio, 
[data-testid="stMain"] .stFileUploader {
    font-size: clamp(24px, 2.8vw, 32px) !important;
    font-weight: bold !important;
}
[data-testid="stMain"] .stMarkdown p, 
[data-testid="stMain"] .stText p {
    font-size: clamp(22px, 2.6vw, 30px) !important;
    font-weight: bold !important;
}

/* 側邊欄保持正常大小 */
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] .stText,
[data-testid="stSidebar"] .stSelectbox,
[data-testid="stSidebar"] .stTextInput {
    font-size: 16px !important;
    font-weight: normal !important;
}
[data-testid="stSidebar"] h3 {
    font-size: 1.3rem !important;
}
[data-testid="stSidebar"] .stMarkdown p {
    font-size: 14px !important;
    font-weight: normal !important;
}

h3 {
    font-size: clamp(1.6rem, 3vw, 2.2rem) !important;
    font-weight: bold !important;
}

/* ==================== 通用按鈕樣式 ==================== */
.stButton button span,
.stButton button p,
[data-testid="stButton"] button span,
[data-testid="stButton"] button p,
[data-testid="baseButton-primary"] span,
[data-testid="baseButton-secondary"] span,
[data-testid="baseButton-primary"] p,
[data-testid="baseButton-secondary"] p,
button[kind="primary"] span,
button[kind="secondary"] span,
button[kind="primary"] p,
button[kind="secondary"] p {
    font-size: 18px !important;
    font-weight: bold !important;
}

/* 主頁面的主要操作按鈕 */
[data-testid="stMain"] .stButton button[kind="primary"],
[data-testid="stMain"] [data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
}
[data-testid="stMain"] .stButton button[kind="secondary"],
[data-testid="stMain"] [data-testid="baseButton-secondary"] {
    background: white !important;
    color: #333 !important;
    border: 2px solid #ccc !important;
    border-radius: 8px !important;
}

/* 首頁 Tab 按鈕特別樣式 */
.home-page-btn .stButton button,
.home-page-btn .stButton button span,
.home-page-btn .stButton button p,
.home-page-btn + div .stButton button,
.home-page-btn + div .stButton button span,
.home-page-btn + div .stButton button p {
    background: transparent !important;
    background-color: transparent !important;
    color: #4A6B8A !important;
    border: none !important;
    border-bottom: 4px solid #4A6B8A !important;
    border-radius: 0 !important;
    font-weight: 700 !important;
    font-size: 18px !important;
}

/* 側邊欄的按鈕 */
[data-testid="stSidebar"] .stButton button span,
[data-testid="stSidebar"] .stButton button p {
    font-size: 16px !important;
    font-weight: bold !important;
}
[data-testid="stSidebar"] .stButton button[kind="primary"] {
    background: linear-gradient(135deg, #4A6B8A 0%, #5C8AAD 100%) !important;
    color: white !important;
    border: none !important;
    border-bottom: none !important;
    border-radius: 8px !important;
}
[data-testid="stSidebar"] .stButton button[kind="secondary"] {
    background: #E8E0E3 !important;
    color: #7D5A6B !important;
    border: 1px solid #C4A0AB !important;
    border-bottom: 1px solid #C4A0AB !important;
    border-radius: 8px !important;
}
.stCaption {
    font-size: clamp(18px, 2vw, 24px) !important;
}

/* ==================== 隱藏右下角浮動元素（通用規則）==================== */
/* 針對常見的固定定位浮動按鈕、徽章或分享元件進行隱藏 */
div[style*="position: fixed"][style*="right"] {
    display: none !important;
    visibility: hidden !important;
    pointer-events: none !important;
    opacity: 0 !important;
}

/* 另外再針對常見的 a 標籤徽章做隱藏（保險） */
a[href*="streamlit"] {
    display: none !important;
    visibility: hidden !important;
    pointer-events: none !important;
    opacity: 0 !important;
}
</style>
""", unsafe_allow_html=True)

# ==================== 簡單的 UI 範例（首頁） ====================
# 這段建立一個簡單的首頁，展示標題與兩張卡片（嵌入 / 提取）
def show_home():
    st.markdown('<div class="welcome-container">', unsafe_allow_html=True)
    st.markdown(f'<div class="welcome-title">🔐 高效能無載體之機密編碼技術</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="welcome-subtitle">嵌入與提取機密資訊的高效流程示意</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown('<div class="anim-card anim-card-embed">', unsafe_allow_html=True)
        st.markdown('<div class="anim-flow">', unsafe_allow_html=True)
        # 圖示可以改成 base64 圖片或 emoji
        st.markdown('<div class="anim-icon anim-icon-secret">📦</div><div class="anim-icon anim-icon-arrow">➡️</div><div class="anim-icon anim-icon-result">🖼️</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="anim-title">嵌入機密</div>', unsafe_allow_html=True)
        st.markdown('<div class="anim-desc">將機密編碼為 Z 碼並嵌入載體圖像</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="anim-card anim-card-extract">', unsafe_allow_html=True)
        st.markdown('<div class="anim-flow">', unsafe_allow_html=True)
        st.markdown('<div class="anim-icon anim-icon-source">🖼️</div><div class="anim-icon anim-icon-arrow">➡️</div><div class="anim-icon anim-icon-result">📦</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="anim-title">提取機密</div>', unsafe_allow_html=True)
        st.markdown('<div class="anim-desc">從載體圖像中偵測並還原 Z 碼</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 團隊資訊置底（置中）
    st.markdown('<div style="text-align:center; margin-top:18px; color:#333; font-weight:600;">組員：鄭凱馨、劉佳典、王于婕</div>', unsafe_allow_html=True)

# 主流程
def main():
    show_home()

    # 這裡保留原本的功能入口（簡化示範）
    st.markdown("---")
    st.markdown("**操作說明**")
    st.write("請使用側邊欄或下方按鈕進入嵌入 / 提取功能（此示範頁面僅顯示首頁樣式）。")

if __name__ == "__main__":
    main()
