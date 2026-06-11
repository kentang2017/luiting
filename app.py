# -*- coding: utf-8 -*-
"""
堅雷霆曜氣 Streamlit 介面 — Thunder Qi Divination Web UI

提供互動式網頁介面，讓使用者輸入日期時間後生成堅雷霆曜氣排盤。
包含九宮格排盤、吉凶神煞、天氣預測等視覺化呈現，
並提供術語說明和 Markdown 匯出功能。
"""

import datetime
from io import StringIO
from contextlib import contextmanager, redirect_stdout
from typing import Any, Dict, List, Optional

import streamlit as st
import pytz
import pandas as pd  # 僅用於箭頭表格等非盤式視覺化

from luiting import Luiting

# 嚴格從 rules 匯入原文歌訣與資料（用於「原文依據」展示）
try:
    from rules import (
        HEQI_STOP_YEAR_RHYME,
        HEQI_MONTH_RHYME,
        HEQI_DAY_RHYME,
        HEQI_HOUR_RHYME,
        SHENGXUAN_UPPER_JU,
        LIUJIA_SHUN_STAR,
        STAR_12,
        HEQI_YEAR_START,
        HEQI_STOP_BRANCH_BY_JIA_SHUN,
    )
except ImportError:
    HEQI_STOP_YEAR_RHYME = "（rules.py 未載入，無法顯示完整歌訣）"
    # ... 其他回退為空字串
    HEQI_MONTH_RHYME = HEQI_DAY_RHYME = HEQI_HOUR_RHYME = ""
    SHENGXUAN_UPPER_JU = LIUJIA_SHUN_STAR = {}
    STAR_12 = []
    HEQI_YEAR_START = {}
    HEQI_STOP_BRANCH_BY_JIA_SHUN = {}

# ===========================================================================
# 常量與配置
# ===========================================================================

PALACE_NAMES = frozenset("巽離坤震中兌艮坎乾")

# 術語解釋（依《道法會元》卷一百二十九《雷霆箭煞年月樞機》）
TERM_GLOSSARY: Dict[str, str] = {
    "金虎大煞": "金虎大煞為雷法中主兇之煞星，金火相剋，應時雷火俱發。據文：「先於輪盤上輪日看是甚星，將日星入中宮飛看燥火到何方位，此名金火大煞。」",
    "流火凶星": "流火凶星為雷霆正然之氣，與金虎相配合可引發大雷雨。據文：「雷霆流火號凶星，但把支干自內尋。順走九宮尋戊子，納音之火剋其金。」",
    "值符": "值符為雷法中執法之神，主管雷霆號令。據文：「凡召雷行事，先召直符召雷公。」「直符事應疾如飛，天門甲子起星移順走九宮。」",
    "傳音": "傳音乃雷神，負責傳遞雷霆號令。據文：「先遣傳音報犯神，興雷致雨滿天雲。」",
    "帝星": "帝星為紫微帝星，主管吉凶。據文：「帝星動處發天罡」，帝星臨照處不宜步罡掐訣。",
    "昇玄值向": "昇玄為雷霆合炁停年法，據文：「甲子尋豬甲戌寅，甲申辰上好安身。甲午本宮扶上馬，甲辰申上妙推輪。」以年天干決定九宮飛布起始。",
    "合炁": "合炁為雷霆曜氣的核心概念，指星辰之氣會合。據文：「雷霆合炁要星同，有炁方能達上穹。」",
    "雷箭": "雷霆箭法為雷法中判斷方位吉凶的關鍵。據文：「看他發其箭定日時煞，此日雷箭非特動雷，亦能料理諸事，可以伐神壇社廟。」",
    "天遁": "天遁為陽日飛星法，陽順行。據「飛定星宿主事法」。",
    "地遁": "地遁為陰日飛星法，陰逆行。據「飛定星宿主事法」。",
    "雷公": "雷公主司雷鳴，起雷之時先尋雷公在何處。據文：「翼軫主雷，虛危主雪，箕星好風，畢星好雨，星宿主晴。」",
    "風伯": "風伯主司風，與箕星相會則風起。據文：「風伯與箕星相會則無不應也。」",
    "雨伯": "雨伯主司雨，與畢星同宮則致雨。據文：「尋雨師與畢星同宮或衝或合之地。」",
}

# 雷箭吉凶詩斷
ARROW_MEANINGS: Dict[str, str] = {
    "太陽": "☀️ 吉 — 「太陽星吉照人間，百口人家自等閑，官職高遷盈駟馬。」",
    "吉祥": "🌟 大吉 — 「吉祥之星大吉祥，內外人家便吉昌，喜氣萬重生貴子。」",
    "風雲": "🌤️ 半吉 — 「風雲半吉半為凶，射外和平不箭衝。」",
    "旺相": "💪 吉 — 「旺相來臨，富貴家紫袍金帶便榮華。」",
    "雷公": "⚡ 凶 — 「雷公一動震天庭，射外須教百里驚，射內定應雷打死。」",
    "鬼火": "👻 凶 — 「鬼火生災發大瘟，一年半載絕除根。」",
    "血刃": "🩸 凶 — 「血刃星凶六畜當，父南子北血星光。」",
    "火烈": "🔥 凶 — 「火烈雷神便火光，同年月日一般裝。」",
    "飛劍": "⚔️ 凶 — 「飛劍之星主血光，殺人流血主官方。」",
    "木神": "🌳 吉 — 「木星一位最強動，射外修營主百口。」",
    "雷母": "⛈️ 凶 — 「電母毫光射小兒，不過半月見悲啼。」",
    "亡沒": "💀 凶 — 「春一月還他死，內外人家月月愁。」",
}


# ===========================================================================
# 工具函數
# ===========================================================================


def format_dict(d: Dict, indent: int = 0) -> str:
    """格式化字典為可讀的 Markdown 文本。"""
    items: List[str] = []
    prefix = "　" * indent
    for k, v in d.items():
        if isinstance(v, dict):
            items.append(f"{prefix}**{k}**：")
            items.append(format_dict(v, indent + 1))
        elif isinstance(v, list):
            items.append(f"{prefix}**{k}**：{'、'.join(str(i) for i in v)}")
        else:
            items.append(f"{prefix}**{k}**：{v}")
    return "\n\n".join(items)


@contextmanager
def st_capture(output_func):
    """捕獲 stdout 並將其傳遞給指定的輸出函數。"""
    with StringIO() as stdout, redirect_stdout(stdout):
        old_write = stdout.write

        def new_write(string):
            ret = old_write(string)
            output_func(stdout.getvalue())
            return ret

        stdout.write = new_write
        yield


def generate_markdown_export(pan: Dict, gz: str, clockwise: Dict, anticlockwise: Dict) -> str:
    """生成 Markdown 格式的排盤結果，供匯出使用。"""
    lines = [
        f"# ⚡ 堅雷霆曜氣排盤結果",
        f"",
        f"## 基本資訊",
        f"- **日期時間**：{pan.get('日期時間')}",
        f"- **干支**：{gz}",
        f"- **農曆**：{pan.get('農曆')}",
        f"- **節氣**：{pan.get('節氣')}",
        f"- **月五行**：{pan.get('月五行')}",
        f"- **日干支**：{pan.get('日干支')}（{pan.get('日陰陽')}）",
        f"- **日干支納音**：{pan.get('日干支納音')}",
        f"",
        f"## 雷霆年月日時箭 + 雷公箭",
    ]

    arrows = pan.get("雷霆年月日時箭", [])
    labels = ["年箭", "月箭", "日箭", "時箭"]
    for label, arrow in zip(labels, arrows):
        meaning = ARROW_MEANINGS.get(arrow, "")
        lines.append(f"- **{label}**：{arrow} {meaning}")

    leigong_arrow = pan.get("雷公箭", "")
    if leigong_arrow:
        meaning = ARROW_MEANINGS.get(leigong_arrow, "")
        lines.append(f"- **雷公箭**：{leigong_arrow} {meaning}")

    lines.extend([
        f"",
        f"## 雷霆合炁（含旬合炁）",
        f"- **雷霆旬**：{pan.get('雷霆旬')}",
        f"- **雷霆旬合炁**：{pan.get('雷霆旬合炁')}",
        f"- **雷霆年合炁**（中宮起星）：{pan.get('雷霆年合炁', {}).get('中', '')}",
        f"- **雷霆月合炁**（中宮起星）：{pan.get('雷霆月合炁', {}).get('中', '')}",
        f"",
        f"## 吉凶神煞",
        f"- **金虎大煞**：{pan.get('金虎大煞')}",
        f"- **流火凶星**：{pan.get('流火凶星')}",
        f"- **值符**：{pan.get('值符')}",
        f"- **傳音**：{pan.get('傳音')}",
        f"- **月帝星**：{pan.get('月帝星')}",
        f"- **日帝星**：{pan.get('日帝星')}",
        f"",
        f"## 天氣預測",
        f"- **天氣**：{pan.get('天氣')}",
        f"- **星禽應事**：{pan.get('星禽應事')}",
        f"- **四季禽星應事**：{pan.get('四季禽星應事')}",
        f"",
        f"## 雷公風伯雨伯",
        f"- **雷公**：{pan.get('雷公')}（雷公箭：{pan.get('雷公箭', '—')}）",
        f"- **風伯**：{pan.get('風伯')}",
        f"- **雨伯**：{pan.get('雨伯')}",
        f"",
        f"---",
        f"*排盤依據：《道法會元》卷一百二十九《雷霆箭煞年月樞機》*",
    ])
    return "\n".join(lines)


# ===========================================================================
# Streamlit 頁面配置
# ===========================================================================

st.set_page_config(
    layout="wide",
    page_title="堅雷霆曜氣 — Luitingyaoqi",
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

# 頂部標題
st.title("⚡ 堅雷霆曜氣")

# 初始化 session state（用於即時盤等）
if "render_default" not in st.session_state:
    st.session_state.render_default = True


# ===========================================================================
# 側邊欄輸入
# ===========================================================================

with st.sidebar:
    st.header("📅 排盤參數設置")

    # 使用者模式（新手 vs 進階）
    ui_mode = st.radio(
        "使用模式",
        ["新手模式（推薦）", "進階模式（完整資料+原文）"],
        horizontal=True,
        help="新手模式會簡化顯示並加強白話解釋；進階模式顯示所有原始計算與 verbatim 歌訣。"
    )
    st.session_state.ui_mode = ui_mode

    now = datetime.datetime.now(pytz.timezone("Asia/Hong_Kong"))

    # 改善輸入：提供日期 + 時間 widget + 手動數字
    st.subheader("日期時間")
    default_date = now.date()
    default_time = now.time()

    col_date, col_time = st.columns(2)
    with col_date:
        selected_date = st.date_input("日期", value=default_date, key="date_input")
    with col_time:
        selected_time = st.time_input("時間", value=default_time, key="time_input", step=60)

    # 手動微調（進階）
    if "進階" in ui_mode:
        with st.expander("手動微調年月日時分", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                my = st.number_input("年", 1, 2100, selected_date.year, key="year")
                mm = st.number_input("月", 1, 12, selected_date.month, key="month")
                md = st.number_input("日", 1, 31, selected_date.day, key="day")
            with c2:
                mh = st.number_input("時", 0, 23, selected_time.hour, key="hour")
                mmin = st.number_input("分", 0, 59, selected_time.minute, key="minute")
    else:
        my, mm, md = selected_date.year, selected_date.month, selected_date.day
        mh, mmin = selected_time.hour, selected_time.minute

    # 快速範例按鈕（立即可用）
    st.subheader("⚡ 快速範例")
    preset_cols = st.columns(3)
    with preset_cols[0]:
        if st.button("今日即時", use_container_width=True):
            now = datetime.datetime.now(pytz.timezone("Asia/Hong_Kong"))
            st.session_state["date_input"] = now.date()
            st.session_state["time_input"] = now.time()
            st.rerun()
    with preset_cols[1]:
        if st.button("甲子年範例\n(1984-05-05 21:00)", use_container_width=True):
            st.session_state["date_input"] = datetime.date(1984, 5, 5)
            st.session_state["time_input"] = datetime.time(21, 0)
            st.rerun()
    with preset_cols[2]:
        if st.button("經典測試\n(其他甲子)", use_container_width=True):
            # 另一個易記的甲子日範例
            st.session_state["date_input"] = datetime.date(2000, 1, 1)
            st.session_state["time_input"] = datetime.time(0, 0)
            st.rerun()

    instant = st.button("⏱️ 計算當前輸入", type="primary", use_container_width=True)

    st.divider()

    # 術語區移到這裡或保留，後續優化成可搜尋
    with st.expander("📖 快速術語參考（點擊展開）", expanded=False):
        search_term = st.text_input("搜尋術語", placeholder="金虎、合炁...", key="glossary_search")
        filtered = {k: v for k, v in TERM_GLOSSARY.items() if not search_term or search_term.lower() in k.lower() or search_term.lower() in v.lower()}
        for term, desc in filtered.items():
            st.markdown(f"**{term}**")
            st.caption(desc[:120] + "..." if len(desc) > 120 else desc)


# 統一在此計算當前要用的年月日時分（sidebar 結束後立即執行，保證 r_* 變數存在）
if 'instant' in globals() and instant:
    now = datetime.datetime.now(pytz.timezone("Asia/Hong_Kong"))
    r_year, r_month, r_day = now.year, now.month, now.day
    r_hour, r_minute = now.hour, now.minute
else:
    try:
        r_year = selected_date.year
        r_month = selected_date.month
        r_day = selected_date.day
        r_hour = selected_time.hour
        r_minute = selected_time.minute
    except Exception:
        now = datetime.datetime.now(pytz.timezone("Asia/Hong_Kong"))
        r_year, r_month, r_day = now.year, now.month, now.day
        r_hour, r_minute = now.hour, now.minute


# ===========================================================================
# 計算引擎
# ===========================================================================


@st.cache_data
def gen_results(year: int, month: int, day: int, hour: int, minute: int) -> Dict:
    """生成雷霆曜氣計算結果（包含嚴格歌訣計算）。"""
    lt = Luiting(year, month, day, hour, minute)
    pan = lt.pan()
    gangzhi = lt.gangzhi()
    gz = f"{gangzhi[0]}年 {gangzhi[1]}月 {gangzhi[2]}日 {gangzhi[3]}時 {gangzhi[4]}分"
    clockwise = lt.luitingheqiday_clockwise()
    anticlockwise = lt.luitingheqiday_anticlockwise()

    # 額外暴露嚴格 API（用於原文依據展示）
    strict = {
        "stop_branch": getattr(lt, 'heqi_stop_branch', lambda: None)(),
        "shengxuan_upper": getattr(lt, 'shengxuan_upper_ju', lambda: {})(),
        "year_center_star": getattr(lt, 'heqi_year_center_star', lambda: "")(),
        "month_center_star": getattr(lt, 'heqi_month_center_star', lambda: "")(),
    }

    return {
        "pan": pan,
        "gz": gz,
        "clockwise": clockwise,
        "anticlockwise": anticlockwise,
        "strict": strict,
        "lt": lt,  # 注意：cache 時物件會被序列化限制，僅供當下使用
    }


# ===========================================================================
# 傳統九宮格 HTML 函數已移除（依使用者要求「不顯示傳統九宮格（HTML）」）
# 如需恢復，請告知。
# ===========================================================================

# 五行著色邏輯（美學主義，傳統風水配色）
# 最新星曜五行歸屬（使用者指定）：
# 木: 太陽, 奇羅, 紫炁
# 水: 金水, 水潦, 月孛
# 土: 台將, 土溽
# 金: 天罡, 血刃
# 火: 燥火, 丙乙
PALACE_ELEMENTS = {
    "乾": "金", "兌": "金",
    "艮": "土", "坤": "土",
    "震": "木", "巽": "木",
    "離": "火",
    "坎": "水",
    "中": "土",
}

ELEMENT_COLORS = {
    # 傳統五行文字配色（適合深色背景的高對比度）
    "木": "#22c55e",   # 鮮木綠（鮮明、生命力）
    "火": "#f43f5e",   # 火紅 / 玫瑰紅（醒目、熱烈）
    "土": "#eab308",   # 土黃 / 琥珀黃（穩重、溫暖）
    "金": "#e0e7ff",   # 金屬銀白光（高亮、冷冽）
    "水": "#38bdf8",   # 水藍 / 天青（清澈、流動）
}

STAR_ELEMENTS = {
    # 按五行重新配置（使用者指定最新版）
    # 木: 太陽, 奇羅, 紫炁
    # 水: 金水, 水潦, 月孛
    # 土: 台將, 土溽
    # 金: 天罡, 血刃
    # 火: 燥火, 丙乙
    "太陽": "木",
    "奇羅": "木",
    "紫炁": "木",
    "金水": "水",
    "水潦": "水",
    "月孛": "水",
    "台將": "土",
    "土溽": "土",
    "天罡": "金",
    "血刃": "金",
    "燥火": "火",
    "丙乙": "火",
}

# ===========================================================================
# 新 UI 輔助函數（現代卡片 + 原文依據 + Plotly 視覺化）
# ===========================================================================

def render_source_box(title: str, verbatim_text: str, location: str = "《雷霆箭煞年月樞機》"):
    """顯示原文歌訣卡片（強制 traceability）"""
    with st.container(border=True):
        st.markdown(f"**📖 原文依據 — {title}**")
        st.code(verbatim_text, language="text")
        st.caption(f"出處：{location}（詳見 rules.py 對應常數與 book/雷霆箭煞年月樞機.txt）")


def render_key_metrics(pan: Dict, strict: Dict):
    """總覽關鍵指標卡片（新手友好）"""
    cols = st.columns(4)

    # 年箭
    arrows = pan.get("雷霆年月日時箭", ["", "", "", ""])
    with cols[0]:
        st.metric("年箭", arrows[0] or "—", help="據雷霆箭法詩斷")

    # 雷公箭 (新增)
    leigong_a = pan.get("雷公箭", "") or ""
    with cols[1]:
        st.metric("雷公箭", leigong_a or "—", help="先召直符召雷公，然後使雷箭")

    # 合炁停處（嚴格計算）
    with cols[2]:
        stop = strict.get("stop_branch") or "—"
        st.metric("合炁停處", stop, help="雷霆合炁停年歌 + 逆數")

    # 金虎大煞
    with cols[3]:
        gt = pan.get("金虎大煞", "—")
        st.metric("金虎大煞", gt, help="金火大煞例")

    # 第二排：天氣 + 其他
    cols2 = st.columns(4)
    with cols2[3]:
        weather = pan.get("天氣", "—")
        st.metric("天氣預測", weather, help="星禽應事")

    # 第二列
    cols2 = st.columns(4)
    with cols2[0]:
        st.metric("主煞流火", pan.get("流火凶星", "—"))
    with cols2[1]:
        center = strict.get("year_center_star") or pan.get("雷霆日方合炁", "—")
        st.metric("年中心星", center)
    with cols2[2]:
        st.metric("雷霆月", pan.get("雷霆月", "—"))
    with cols2[3]:
        st.metric("值符 / 傳音", f"{pan.get('值符','—')} / {pan.get('傳音','—')}")

    # 額外一行顯示旬合炁中心星（主頁排盤明顯反映）
    cols3 = st.columns(4)
    with cols3[0]:
        xun_info = pan.get("雷霆旬", {}) or {}
        st.metric("旬合炁", f"{xun_info.get('旬首','—')} → {xun_info.get('旬星','—')}", help="依起旬例")


# create_plotly_nine_palace 已移除（盤式改用 SVG，不再使用 Plotly 建構九宮格）

def build_nine_palace_svg(heqi: dict, level: str = "") -> str:
    """純 SVG 九宮格盤式（不使用 Plotly）。五行著色，傳統美學。響應式滿版。"""
    layout = [
        ["巽", "離", "坤"],
        ["震", "中", "兌"],
        ["艮", "坎", "乾"],
    ]
    cell_w, cell_h = 105, 88
    svg_w = cell_w * 3 + 10
    svg_h = cell_h * 3 + 10
    margin = 5

    elements = []
    # 外框（模擬羅盤/盤式外圍）
    elements.append(
        f'<rect x="{margin-2}" y="{margin-2}" width="{svg_w-6}" height="{svg_h-6}" '
        f'fill="none" stroke="#b8860b" stroke-width="3" rx="8"/>'
    )
    elements.append(
        f'<rect x="{margin}" y="{margin}" width="{svg_w-10}" height="{svg_h-10}" '
        f'fill="#0f172a" stroke="#9f1239" stroke-width="1.5" rx="6"/>'
    )

    y = margin + 2
    for row in layout:
        x = margin + 2
        for p in row:
            val = str(heqi.get(p, "") or heqi.get(p[0], "") or "-")
            p_elem = PALACE_ELEMENTS.get(p, "土")
            p_color = ELEMENT_COLORS.get(p_elem, "#CD853F")
            # 宮格背景按五行淺色
            bg_color = p_color + "22"  # 22 = ~13% opacity
            star_elem = STAR_ELEMENTS.get(val, "土")
            star_color = ELEMENT_COLORS.get(star_elem, "#f1f5f9")
            # 單格背景（五行色調）
            elements.append(
                f'<rect x="{x}" y="{y}" width="{cell_w}" height="{cell_h}" '
                f'fill="{bg_color}" stroke="{p_color}" stroke-width="1.5" rx="3"/>'
            )
            # 宮位名（五行色）
            elements.append(
                f'<text x="{x + cell_w/2}" y="{y + 24}" font-size="14" font-weight="700" '
                f'fill="{p_color}" text-anchor="middle" dominant-baseline="middle">{p}</text>'
            )
            # 星宿值（五行色）
            elements.append(
                f'<text x="{x + cell_w/2}" y="{y + 52}" font-size="11" font-weight="600" '
                f'fill="{star_color}" text-anchor="middle" dominant-baseline="middle">{val}</text>'
            )
            x += cell_w
        y += cell_h

    # 響應式：width 100% + viewBox 讓它跟隨容器尺寸自動縮放，盡可能放大
    svg = (
        f'<svg width="100%" height="auto" viewBox="0 0 {svg_w} {svg_h}" '
        f'preserveAspectRatio="xMidYMid meet" '
        f'xmlns="http://www.w3.org/2000/svg" class="nine-palace-svg">'
        + "".join(elements) +
        '</svg>'
    )
    return svg


# ===========================================================================
# 主要內容
# ===========================================================================

# 直接顯示排盤（已移除頂部 Tabs，頁首直接呈現合炁排盤）
# 重新計算一次以取得最新 results（r_year 等已在 sidebar 後統一定義）
try:
    final_results = gen_results(r_year, r_month, r_day, r_hour, r_minute)
    pan = final_results["pan"]
    strict = final_results.get("strict", {})
    gz = final_results["gz"]

    # ===================== 直接顯示排盤 =====================
    st.subheader(f"📋 {pan.get('日期時間')}")
    st.markdown(f"**{gz}**")

    # 直接在主頁排盤區文字反映新增的旬合炁與雷公箭
    xun = pan.get("雷霆旬", {}) or {}
    xun_center = xun.get("旬星", "")
    leigong_arrow_val = pan.get("雷公箭", "")
    if xun or leigong_arrow_val:
        st.markdown(
            f"**旬合炁**：{xun.get('旬首', '—')}旬（中宮起星：**{xun_center or '—'}**）　"
            f"**雷公箭**：**{leigong_arrow_val or '—'}**"
        )

    st.divider()

    # 合炁排盤 - 使用純 SVG（不使用 Plotly），並以分頁呈現年月日旬時
    st.markdown("**合炁排盤**（年→月→日→旬→時）")

    # 準備層級的資料（盡量相容現有 pan 結構）
    xun_heqi = pan.get("雷霆旬合炁", {}) or {}
    year_heqi = pan.get("雷霆年合炁", {}) or {}
    month_heqi = pan.get("雷霆月合炁", {}) or {}
    day_heqi = final_results.get("clockwise", {}) or pan.get("雷霆日局", {}) or {}
    hour_raw = pan.get("雷霆時合炁值山向定局", {}) or {}

    # 確保各合炁 中宮有起星
    year_center = strict.get("year_center_star", "") or ""
    if year_center:
        year_heqi["中"] = year_center

    # 旬合炁中心星（直接來自新實作）
    xun_center = pan.get("雷霆旬", {}).get("旬星", "") or ""
    if xun_center:
        xun_heqi["中"] = xun_center

    # 修正時合炁：加入起星（雷霆時）到中宮，並從時合炁山向對應宮位填星
    hour_heqi = {}
    起時星 = pan.get("雷霆時") or "-"
    hour_heqi["中"] = 起時星

    gong_to_branch = {
        "乾": "戌", "兌": "酉", "艮": "丑", "離": "午",
        "坎": "子", "坤": "未", "震": "卯", "巽": "辰",
    }
    時山向 = hour_raw.get("時合炁山向", {}) if isinstance(hour_raw, dict) else {}
    for p, br in gong_to_branch.items():
        if br and br in 時山向:
            hour_heqi[p] = 時山向[br]
        elif p not in hour_heqi:
            hour_heqi[p] = "-"

    heqi_subtabs = st.tabs(["年合炁", "月合炁", "日合炁", "旬合炁", "時合炁"])

    with heqi_subtabs[0]:
        svg = build_nine_palace_svg(year_heqi)
        st.markdown(svg, unsafe_allow_html=True)

    with heqi_subtabs[1]:
        svg = build_nine_palace_svg(month_heqi)
        st.markdown(svg, unsafe_allow_html=True)

    with heqi_subtabs[2]:
        svg = build_nine_palace_svg(day_heqi)
        st.markdown(svg, unsafe_allow_html=True)

    with heqi_subtabs[3]:
        svg = build_nine_palace_svg(xun_heqi)
        st.markdown(svg, unsafe_allow_html=True)
        st.caption("依《雷霆箭煞年月樞機》「起旬例」：甲子奇羅甲戌罡，甲申金水甲午陽。甲辰紫炁甲寅分丙乙，定布吉凶方。")

    with heqi_subtabs[4]:
        svg = build_nine_palace_svg(hour_heqi)
        st.markdown(svg, unsafe_allow_html=True)

    st.divider()
    # 關鍵指標區塊（手機已透過 CSS 調整為細字 + 較好排版）
    render_key_metrics(pan, strict)

except Exception as e:
    st.error(f"生成盤局時發生錯誤：{str(e)}")
    st.exception(e)


# ===========================================================================
# Custom CSS
# ===========================================================================

st.markdown(
    """
    <style>
    :root {
        --vermilion: #9f1239;
        --gold: #b8860b;
        --navy: #0f172a;
        --card-bg: #1e2937;
    }

    .stApp {
        background-color: #0f172a;
    }

    /* 專業傳統卡片 */
    .result-card, .stContainer {
        background: var(--card-bg);
        border-left: 5px solid var(--vermilion);
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.4);
    }

    .gold-accent { color: var(--gold) !important; font-weight: 600; }
    .vermilion-text { color: var(--vermilion) !important; }

    /* 舊九宮格 HTML 樣式已移除，盤式改用內嵌 SVG */
    .nine-palace-svg {
        width: 100%;
        max-width: 1100px;   /* 盡可能放大，適合大螢幕仍清晰 */
        height: auto;
        display: block;
        margin: 0 auto;
    }

    /* 按鈕與互動 */
    .stButton button {
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.12s ease;
        background: linear-gradient(90deg, #4e7496, #3a5a78);
        color: white;
        border: none;
    }
    .stButton button:hover:enabled {
        transform: translateY(-1px);
        box-shadow: 0 2px 6px rgba(159, 18, 57, 0.3);
    }

    /* 響應式 - 依網頁界面尺寸自動調整，盡可能放到最大 */
    .nine-palace-svg {
        width: 100% !important;
        height: auto !important;
        max-width: 1400px;   /* 大螢幕盡可能放大 */
        margin: 0 auto;
        display: block;
    }

    /* 關鍵指標 (st.metric) 手機優化：字體細小、排版好看、兩欄 */
    .stMetric {
        padding: 0.15rem 0.25rem !important;
        margin-bottom: 0.1rem !important;
    }
    .stMetricValue {
        font-size: 0.9rem !important;
        line-height: 1.1 !important;
    }
    .stMetricLabel {
        font-size: 0.6rem !important;
        line-height: 1.0 !important;
        white-space: nowrap;
    }

    @media (max-width: 768px) {
        .stApp { font-size: 1.0em; line-height: 1.3; }
        .nine-palace-svg { max-width: 100%; }  /* 手機填滿 */
        .stTabs [data-baseweb="tab-list"] { flex-wrap: wrap; font-size: 1.0em; }
        .stContainer, .result-card { padding: 10px 8px; margin-bottom: 8px; }
        .stMarkdown h3, .stSubheader { font-size: 1.0em; }

        /* 手機上關鍵指標：4欄變成 2欄 (每欄 50%)，字體再細 */
        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
            flex: 0 0 50% !important;
            max-width: 50% !important;
            padding: 0 2px !important;
        }
        .stMetric {
            padding: 0.1rem 0.15rem !important;
        }
        .stMetricValue {
            font-size: 0.82rem !important;
        }
        .stMetricLabel {
            font-size: 0.55rem !important;
        }
    }

    @media (min-width: 1600px) {
        .nine-palace-svg { max-width: 1600px; }  /* 超寬螢幕最大化 */
    }

    /* 來源框 */
    .stCodeBlock {
        background: #1e2937 !important;
        border: 1px dashed #64748b;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
