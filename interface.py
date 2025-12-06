# ==================== 等比例縮放 CSS ====================
# 把原本 interface.py 中的 CSS 區塊替換成以下內容

st.markdown("""
<style>
/* ==================== 基礎設定 ==================== */
/* 背景圖片 */
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
div[class*="viewerBadge"], div[class*="StatusWidget"] {
    display: none !important;
}
.block-container { padding-top: 1rem !important; }

/* 隱藏側邊欄控制按鈕 */
button[data-testid="collapsedControl"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] {
    display: none !important;
}

/* ==================== 等比例縮放核心（用 vmin）==================== */

/* 自訂側邊欄標籤 */
#sidebar-toggle-label {
    position: fixed;
    top: 1vmin;
    left: 0;
    background: #4A6B8A;
    color: white;
    writing-mode: vertical-rl;
    padding: 1.5vmin 0.8vmin;
    border-radius: 0 1vmin 1vmin 0;
    font-size: 2.2vmin;
    font-weight: bold;
    z-index: 999999;
    cursor: pointer;
    box-shadow: 2px 0 8px rgba(0,0,0,0.15);
    transition: all 0.3s ease;
}
#sidebar-toggle-label:hover {
    padding-left: 1.5vmin;
    background: #5C8AAD;
}

/* 主內容區 */
[data-testid="stMain"] {
    margin-left: 0 !important;
    width: 100% !important;
}

/* 側邊欄 */
[data-testid="stSidebar"] {
    position: fixed !important;
    left: 0 !important;
    top: 0 !important;
    height: 100vh !important;
    width: 22vmin !important;
    min-width: 180px !important;
    max-width: 280px !important;
    z-index: 999 !important;
    transition: transform 0.3s ease !important;
    transform: translateX(-100%);
    background: linear-gradient(180deg, #d8cfc4 0%, #c9bfb3 100%) !important;
    box-shadow: 4px 0 15px rgba(0,0,0,0.2) !important;
}
[data-testid="stSidebar"].sidebar-open {
    transform: translateX(0) !important;
}
[data-testid="stSidebar"] * { color: #443C3C !important; }
[data-testid="stSidebar"] h3 { font-size: 3.5vmin !important; color: #4A6B8A !important; }
[data-testid="stSidebar"] strong { font-size: 2.2vmin !important; }
[data-testid="stSidebar"] details summary span { font-size: 2.2vmin !important; }
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] .stSelectbox div { font-size: 1.8vmin !important; }
[data-testid="stSidebar"] button span { font-size: 1.8vmin !important; }

/* ==================== 首頁樣式（等比例）==================== */
.welcome-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 2vh;
    text-align: center;
    margin-bottom: 4vmin;
    margin-top: 6vmin;
}

.welcome-title {
    font-size: 6vmin;
    font-weight: bold;
    margin-bottom: 4vmin;
    letter-spacing: 0.15em;
    padding-left: 0.2em;
    white-space: nowrap;
    background: linear-gradient(135deg, #4A6B8A 0%, #7D5A6B 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* 動畫卡片（等比例）*/
.anim-card {
    width: 90%;
    max-width: 42vmin;
    min-height: 32vmin;
    padding: 3vmin 4vmin;
    border-radius: 2vmin;
    text-align: center;
    cursor: pointer;
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    position: relative;
    overflow: hidden;
    margin: 0 auto;
    box-shadow: 0.8vmin 0.8vmin 0 0 rgba(60, 80, 100, 0.4);
}
.anim-card:hover {
    transform: translateY(-0.8vmin) scale(1.02);
    box-shadow: 1.2vmin 1.2vmin 0 0 rgba(60, 80, 100, 0.5);
}
.anim-card-embed {
    background: linear-gradient(145deg, #7BA3C4 0%, #5C8AAD 100%);
}
.anim-card-extract {
    background: linear-gradient(145deg, #C4A0AB 0%, #A67B85 100%);
}

/* 動畫圖示流程（等比例）*/
.anim-flow {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1.2vmin;
    margin-bottom: 2.5vmin;
    font-size: 4vmin;
    height: 10vmin;
}
.anim-flow .anim-icon,
.anim-flow img {
    width: 8vmin !important;
    height: 8vmin !important;
}
.anim-flow .anim-icon-arrow {
    width: 6vmin !important;
    height: 6vmin !important;
}

/* 動畫效果 */
.anim-card-embed .anim-icon-secret { animation: embedPulse 2s ease-in-out infinite; }
.anim-card-embed .anim-icon-arrow { animation: arrowBounce 1.5s ease-in-out infinite; }
.anim-card-embed .anim-icon-result { animation: resultGlow 2s ease-in-out infinite; }
.anim-card-extract .anim-icon-source { animation: sourcePulse 2s ease-in-out infinite; }
.anim-card-extract .anim-icon-arrow { animation: arrowBounce 1.5s ease-in-out infinite; }
.anim-card-extract .anim-icon-result { animation: extractReveal 2s ease-in-out infinite; }

@keyframes embedPulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.15); } }
@keyframes arrowBounce { 0%, 100% { transform: translateX(0); } 50% { transform: translateX(0.8vmin); } }
@keyframes resultGlow { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.1); } }
@keyframes sourcePulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.1); } }
@keyframes extractReveal { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.2) rotate(5deg); } }

/* 卡片文字（等比例）*/
.anim-title {
    font-size: 5.5vmin;
    font-weight: bold;
    color: #FFFFFF;
    margin-bottom: 1.5vmin;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
}
.anim-desc {
    font-size: 3.8vmin;
    color: rgba(255,255,255,0.9);
    line-height: 1.6;
}

/* 底部組員文字（等比例）*/
.footer-credits {
    position: fixed;
    bottom: 3vmin;
    left: 0;
    right: 0;
    text-align: center;
    color: #5D5D5D;
    font-size: 2.8vmin;
    font-weight: 500;
    z-index: 10;
}

/* 首頁按鈕隱藏 */
.home-page-btn + div {
    position: fixed !important;
    top: -9999px !important;
    opacity: 0 !important;
}

/* ==================== 功能頁面樣式（等比例）==================== */
.page-title-embed, .page-title-extract {
    font-size: 4.5vmin;
    font-weight: bold;
}
.page-title-embed {
    background: linear-gradient(135deg, #4A6B8A 0%, #5C8AAD 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.page-title-extract {
    background: linear-gradient(135deg, #7D5A6B 0%, #A67B85 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* 成功/資訊框（等比例）*/
.success-box {
    background: linear-gradient(135deg, #4A6B8A 0%, #5C8AAD 100%);
    color: white;
    padding: 2vmin 3vmin;
    border-radius: 1.2vmin;
    margin: 1vmin 0;
    display: inline-block;
    font-size: 2.8vmin;
    min-width: 30vmin;
}
.info-box {
    background: linear-gradient(135deg, #4A6B8A 0%, #5C8AAD 100%);
    color: white;
    padding: 2vmin 3vmin;
    border-radius: 1.2vmin;
    margin: 1vmin 0;
    display: inline-block;
    font-size: 2.4vmin;
    line-height: 1.9;
    min-width: 30vmin;
}
.error-box {
    background: linear-gradient(135deg, #8B5A5A 0%, #A67B7B 100%);
    color: white;
    padding: 2vmin 3vmin;
    border-radius: 1.2vmin;
    margin: 1vmin 0;
    display: inline-block;
    font-size: 2.4vmin;
    min-width: 30vmin;
}

/* 主區域文字（等比例）*/
[data-testid="stMain"] .stMarkdown p,
[data-testid="stMain"] .stText p {
    font-size: 2.4vmin !important;
    font-weight: bold !important;
}
[data-testid="stMain"] h3 {
    font-size: 3vmin !important;
    font-weight: bold !important;
}

/* 標籤和輸入框（等比例）*/
[data-testid="stWidgetLabel"] p {
    font-size: 2.4vmin !important;
    font-weight: bold !important;
}
.stRadio [role="radiogroup"] label,
.stRadio [role="radiogroup"] label p {
    font-size: 2.8vmin !important;
}
.stTextArea textarea {
    font-size: 2.6vmin !important;
}
.stSelectbox div,
[data-baseweb="select"] input,
[data-baseweb="select"] span {
    font-size: 2.4vmin !important;
    color: #333 !important;
}
[data-baseweb="popover"] li {
    font-size: 2.2vmin !important;
}

/* 圖片 caption（等比例）*/
[data-testid="stImage"] figcaption,
.stCaption {
    font-size: 2vmin !important;
    color: #443C3C !important;
}

/* 按鈕（等比例）*/
.stButton button span,
.stButton button p {
    font-size: 2vmin !important;
    font-weight: bold !important;
}
[data-testid="stMain"] .stButton button[kind="primary"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 1vmin !important;
}
[data-testid="stMain"] .stButton button[kind="secondary"] {
    background: white !important;
    color: #333 !important;
    border: 2px solid #ccc !important;
    border-radius: 1vmin !important;
}

/* 下載按鈕 */
.stDownloadButton button span {
    font-size: 2vmin !important;
    font-weight: bold !important;
}

/* Alert 訊息 */
div[data-testid="stAlert"] p {
    font-size: 2.2vmin !important;
}

/* 上傳框 */
.stFileUploader [data-testid="stFileUploaderFile"] span {
    font-size: 2vmin !important;
}

/* 減少間距 */
.block-container {
    padding-top: 0.5rem !important;
    padding-bottom: 8vmin !important;
}
.stSelectbox, .stTextArea, .stFileUploader, .stRadio {
    margin-bottom: 0.5vmin !important;
}

/* ==================== 固定按鈕（等比例）==================== */
#next-step-fixed {
    position: fixed !important;
    bottom: 2vmin !important;
    right: 12vmin !important;
    z-index: 1000 !important;
    min-width: 12vmin !important;
    max-width: 20vmin !important;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 1vmin !important;
    box-shadow: 0 0.5vmin 1.5vmin rgba(102, 126, 234, 0.4) !important;
}
#next-step-fixed span { font-size: 2vmin !important; font-weight: bold !important; }
#next-step-fixed:hover:not(:disabled) {
    transform: translateY(-0.3vmin) !important;
}
#next-step-fixed:disabled {
    background: #ccc !important;
    color: #888 !important;
}

#back-step-fixed {
    position: fixed !important;
    bottom: 2vmin !important;
    left: 3vmin !important;
    z-index: 1000 !important;
    min-width: 10vmin !important;
    max-width: 16vmin !important;
    background: white !important;
    color: #333 !important;
    border: 2px solid #ccc !important;
    border-radius: 1vmin !important;
    box-shadow: 0 0.5vmin 1.5vmin rgba(0, 0, 0, 0.1) !important;
}
#back-step-fixed span { font-size: 2vmin !important; font-weight: bold !important; }
#back-step-fixed:hover {
    transform: translateY(-0.3vmin) !important;
    background: #f5f5f5 !important;
}

/* 強制 columns 橫向排列 */
[data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    gap: 1vmin !important;
}

/* ==================== 極端情況保護 ==================== */
/* 極小螢幕（手機）- 設定最小值 */
@media (max-width: 480px) {
    .welcome-title { font-size: 24px !important; }
    .anim-card { max-width: 280px !important; min-height: 140px !important; }
    .anim-title { font-size: 22px !important; }
    .anim-desc { font-size: 16px !important; }
    .anim-flow img { width: 40px !important; height: 40px !important; }
    .footer-credits { font-size: 14px !important; }
    [data-testid="stMain"] .stMarkdown p { font-size: 16px !important; }
    .stButton button span { font-size: 14px !important; }
}

/* 極小高度（筆電 + 工具列）*/
@media (max-height: 500px) {
    .welcome-container { margin-top: 1vmin !important; margin-bottom: 1vmin !important; }
    .welcome-title { margin-bottom: 1vmin !important; }
    .anim-card { min-height: 20vmin !important; padding: 1.5vmin 2vmin !important; }
    .anim-flow { margin-bottom: 1vmin !important; height: auto !important; }
    .footer-credits { bottom: 0.5vmin !important; }
}
</style>
""", unsafe_allow_html=True)
