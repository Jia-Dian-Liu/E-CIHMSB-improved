"""
E-CIHMSB 高效能無載體之機密編碼技術
Gradio 版本 - 響應式設計
"""

import gradio as gr
import numpy as np
from PIL import Image
from io import BytesIO
import requests
import math
import time

# ==================== 核心邏輯導入 ====================
from embed import embed_secret
from extract import detect_and_extract

# ==================== 圖片庫 ====================
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

# 圖片尺寸選項
SIZE_OPTIONS = {
    "小 (256×256)": 256,
    "中 (512×512)": 512,
    "大 (768×768)": 768,
    "特大 (1024×1024)": 1024,
}

# ==================== 輔助函數 ====================
def download_image(pexels_id, size):
    """下載 Pexels 圖片"""
    url = f"https://images.pexels.com/photos/{pexels_id}/pexels-photo-{pexels_id}.jpeg?auto=compress&cs=tinysrgb&w={size}&h={size}&fit=crop"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content)).convert('RGB')
            if img.size[0] != size or img.size[1] != size:
                img = img.resize((size, size), Image.LANCZOS)
            return img, img.convert('L')
    except Exception as e:
        print(f"下載圖片失敗: {e}")
    return None, None


def calculate_capacity(size):
    """計算圖片容量（bits）"""
    blocks = (size // 8) ** 2
    return blocks * 21  # 每個 8x8 區塊 21 bits


def encode_z_as_image(z_bits, img_num, img_size):
    """將 Z 碼編碼成圖片"""
    # Header: 32 bits (長度) + 16 bits (編號) + 16 bits (尺寸)
    length = len(z_bits)
    header_bits = [int(b) for b in format(length, '032b')]
    header_bits += [int(b) for b in format(img_num, '016b')]
    header_bits += [int(b) for b in format(img_size, '016b')]
    full_bits = header_bits + z_bits
    
    # 補齊到 8 的倍數
    if len(full_bits) % 8 != 0:
        padding = 8 - (len(full_bits) % 8)
        full_bits = full_bits + [0] * padding
    
    # 每 8 bits 轉成像素
    pixels = []
    for i in range(0, len(full_bits), 8):
        byte = full_bits[i:i+8]
        pixels.append(int(''.join(map(str, byte)), 2))
    
    # 建立圖片
    num_pixels = len(pixels)
    width = int(math.sqrt(num_pixels))
    height = math.ceil(num_pixels / width)
    while len(pixels) < width * height:
        pixels.append(0)
    
    image = Image.new('L', (width, height))
    image.putdata(pixels[:width * height])
    return image


def decode_z_from_image(image):
    """從圖片解碼 Z 碼"""
    if image.mode != 'L':
        image = image.convert('L')
    
    pixels = list(image.getdata())
    bits = []
    for p in pixels:
        bits.extend([int(b) for b in format(p, '08b')])
    
    # 讀取 header
    length = int(''.join(map(str, bits[:32])), 2)
    img_num = int(''.join(map(str, bits[32:48])), 2)
    img_size = int(''.join(map(str, bits[48:64])), 2)
    z_bits = bits[64:64+length]
    
    return z_bits, img_num, img_size


def get_image_choices(category):
    """取得指定分類的圖片選項"""
    images = IMAGE_LIBRARY.get(category, [])
    return [f"{i+1}. {img['name']}" for i, img in enumerate(images)]


# ==================== 嵌入功能 ====================
def do_embed(category, image_choice, size_choice, secret_type, secret_text, secret_image):
    """執行嵌入"""
    if not category or not image_choice:
        return None, None, "❌ 請選擇載體圖像"
    
    # 解析選擇
    try:
        img_idx = int(image_choice.split(".")[0]) - 1
        images = IMAGE_LIBRARY.get(category, [])
        if img_idx >= len(images):
            return None, None, "❌ 圖片選擇無效"
        
        pexels_id = images[img_idx]["id"]
        size = SIZE_OPTIONS.get(size_choice, 512)
        
        # 下載載體圖像
        img_color, img_gray = download_image(pexels_id, size)
        if img_gray is None:
            return None, None, "❌ 無法下載載體圖像"
        
        # 準備機密內容
        if secret_type == "文字":
            if not secret_text or not secret_text.strip():
                return None, None, "❌ 請輸入機密文字"
            secret_content = secret_text.strip()
            secret_flag = 'text'
        else:
            if secret_image is None:
                return None, None, "❌ 請上傳機密圖片"
            secret_content = Image.fromarray(secret_image)
            secret_flag = 'image'
        
        # 執行嵌入
        start = time.time()
        z_bits, used_capacity, info = embed_secret(img_gray, secret_content, secret_type=secret_flag)
        elapsed = time.time() - start
        
        # 產生 Z-code 圖片
        z_image = encode_z_as_image(z_bits, img_idx + 1, size)
        
        # 計算容量
        capacity = calculate_capacity(size)
        usage = info['bits'] * 100 / capacity
        
        result_text = f"""✅ 嵌入成功！

⏱ 耗時：{elapsed:.2f} 秒
📊 容量使用：{info['bits']:,} / {capacity:,} bits ({usage:.1f}%)
🖼 載體：{category} - {images[img_idx]['name']} ({size}×{size})
🔐 機密：{'文字' if secret_flag == 'text' else '圖片'}

📋 提取資訊：
- 分類：{category}
- 圖片：{image_choice}
- 尺寸：{size_choice}
"""
        
        return img_color, z_image, result_text
        
    except Exception as e:
        return None, None, f"❌ 嵌入失敗：{str(e)}"


# ==================== 提取功能 ====================
def do_extract(category, image_choice, size_choice, z_image):
    """執行提取"""
    if not category or not image_choice:
        return None, None, "❌ 請選擇載體圖像"
    
    if z_image is None:
        return None, None, "❌ 請上傳 Z-code 圖片"
    
    try:
        # 解析選擇
        img_idx = int(image_choice.split(".")[0]) - 1
        images = IMAGE_LIBRARY.get(category, [])
        if img_idx >= len(images):
            return None, None, "❌ 圖片選擇無效"
        
        pexels_id = images[img_idx]["id"]
        size = SIZE_OPTIONS.get(size_choice, 512)
        
        # 下載載體圖像
        img_color, img_gray = download_image(pexels_id, size)
        if img_gray is None:
            return None, None, "❌ 無法下載載體圖像"
        
        # 解碼 Z-code
        z_pil = Image.fromarray(z_image) if isinstance(z_image, np.ndarray) else z_image
        z_bits, _, _ = decode_z_from_image(z_pil)
        
        # 執行提取
        start = time.time()
        secret, secret_type, info = detect_and_extract(img_gray, z_bits)
        elapsed = time.time() - start
        
        if secret_type == 'text':
            result_text = f"""✅ 提取成功！

⏱ 耗時：{elapsed:.2f} 秒
📝 類型：文字
📄 內容：

{secret}
"""
            return img_color, None, result_text
        else:
            result_text = f"""✅ 提取成功！

⏱ 耗時：{elapsed:.2f} 秒
🖼 類型：圖片
📐 尺寸：{info.get('size', 'N/A')}
"""
            return img_color, secret, result_text
        
    except Exception as e:
        return None, None, f"❌ 提取失敗：{str(e)}"


def update_image_choices(category):
    """更新圖片選項"""
    choices = get_image_choices(category)
    return gr.Dropdown(choices=choices, value=choices[0] if choices else None)


# ==================== Gradio 介面 ====================
def create_app():
    """建立 Gradio 應用"""
    
    # 自定義 CSS
    custom_css = """
    .gradio-container {
        font-family: 'Noto Sans TC', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    .main-title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(135deg, #4A6B8A 0%, #7D5A6B 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    """
    
    with gr.Blocks(css=custom_css, title="E-CIHMSB 機密編碼系統") as app:
        
        # 標題
        gr.HTML("""
        <div class="main-title">高效能無載體之機密編碼技術</div>
        <div class="subtitle">E-CIHMSB (Enhanced Coverless Information Hiding using Multi-level Steganography with Binary encoding)</div>
        """)
        
        with gr.Tabs():
            # ==================== 嵌入頁面 ====================
            with gr.TabItem("🔒 嵌入機密", id="embed"):
                gr.Markdown("### 步驟 1：選擇載體圖像")
                
                with gr.Row():
                    embed_category = gr.Dropdown(
                        choices=list(IMAGE_LIBRARY.keys()),
                        value="建築",
                        label="圖片分類"
                    )
                    embed_image = gr.Dropdown(
                        choices=get_image_choices("建築"),
                        value="1. 哈里發塔",
                        label="選擇圖片"
                    )
                    embed_size = gr.Dropdown(
                        choices=list(SIZE_OPTIONS.keys()),
                        value="中 (512×512)",
                        label="圖片尺寸"
                    )
                
                gr.Markdown("### 步驟 2：輸入機密內容")
                
                with gr.Row():
                    secret_type = gr.Radio(
                        choices=["文字", "圖片"],
                        value="文字",
                        label="機密類型"
                    )
                
                with gr.Row():
                    secret_text = gr.Textbox(
                        label="機密文字",
                        placeholder="請輸入要隱藏的機密訊息...",
                        lines=4,
                        visible=True
                    )
                    secret_image = gr.Image(
                        label="機密圖片",
                        type="numpy",
                        visible=False
                    )
                
                def toggle_secret_input(choice):
                    return gr.update(visible=(choice == "文字")), gr.update(visible=(choice == "圖片"))
                
                secret_type.change(toggle_secret_input, secret_type, [secret_text, secret_image])
                
                embed_btn = gr.Button("🚀 開始嵌入", variant="primary", size="lg")
                
                gr.Markdown("### 結果")
                
                with gr.Row():
                    embed_carrier_output = gr.Image(label="載體圖像", type="pil")
                    embed_zcode_output = gr.Image(label="Z-code 編碼圖", type="pil")
                
                embed_result_text = gr.Textbox(label="嵌入結果", lines=10, interactive=False)
                
                # 綁定事件
                embed_category.change(update_image_choices, embed_category, embed_image)
                embed_btn.click(
                    do_embed,
                    inputs=[embed_category, embed_image, embed_size, secret_type, secret_text, secret_image],
                    outputs=[embed_carrier_output, embed_zcode_output, embed_result_text]
                )
            
            # ==================== 提取頁面 ====================
            with gr.TabItem("🔓 提取機密", id="extract"):
                gr.Markdown("### 步驟 1：選擇載體圖像（與嵌入時相同）")
                
                with gr.Row():
                    extract_category = gr.Dropdown(
                        choices=list(IMAGE_LIBRARY.keys()),
                        value="建築",
                        label="圖片分類"
                    )
                    extract_image = gr.Dropdown(
                        choices=get_image_choices("建築"),
                        value="1. 哈里發塔",
                        label="選擇圖片"
                    )
                    extract_size = gr.Dropdown(
                        choices=list(SIZE_OPTIONS.keys()),
                        value="中 (512×512)",
                        label="圖片尺寸"
                    )
                
                gr.Markdown("### 步驟 2：上傳 Z-code 編碼圖")
                
                extract_zcode = gr.Image(label="上傳 Z-code 圖片", type="numpy")
                
                extract_btn = gr.Button("🔍 開始提取", variant="primary", size="lg")
                
                gr.Markdown("### 結果")
                
                with gr.Row():
                    extract_carrier_output = gr.Image(label="載體圖像", type="pil")
                    extract_secret_output = gr.Image(label="提取的機密圖片", type="pil")
                
                extract_result_text = gr.Textbox(label="提取結果", lines=10, interactive=False)
                
                # 綁定事件
                extract_category.change(update_image_choices, extract_category, extract_image)
                extract_btn.click(
                    do_extract,
                    inputs=[extract_category, extract_image, extract_size, extract_zcode],
                    outputs=[extract_carrier_output, extract_secret_output, extract_result_text]
                )
        
        # 頁尾
        gr.HTML("""
        <div style="text-align: center; margin-top: 2rem; color: #888;">
            組員：鄭凱譽、劉佳典、王于婕
        </div>
        """)
    
    return app


# ==================== 啟動應用 ====================
if __name__ == "__main__":
    app = create_app()
    app.launch(
        share=False,
        server_name="0.0.0.0",
        server_port=7860
    )
