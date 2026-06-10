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
        f"## 雷霆年月日時箭",
    ]

    arrows = pan.get("雷霆年月日時箭", [])
    labels = ["年箭", "月箭", "日箭", "時箭"]
    for label, arrow in zip(labels, arrows):
        meaning = ARROW_MEANINGS.get(arrow, "")
        lines.append(f"- **{label}**：{arrow} {meaning}")

    lines.extend([
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
        f"- **雷公**：{pan.get('雷公')}",
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
PALACE_ELEMENTS = {
    "乾": "金", "兌": "金",
    "艮": "土", "坤": "土",
    "震": "木", "巽": "木",
    "離": "火",
    "坎": "水",
    "中": "土",
}

ELEMENT_COLORS = {
    "木": "#228B22",   # 森林綠
    "火": "#DC143C",   # 深紅
    "土": "#DAA520",   # 黃金土
    "金": "#C0C0C0",   # 銀白
    "水": "#4682B4",   # 鋼藍
}

STAR_ELEMENTS = {
    "血刃": "金",
    "金水": "水",
    "水潦": "水",
    "天罡": "金",
    "月孛": "火",
    "土溽": "土",
    "奇羅": "木",
    "燥火": "火",
    "丙乙": "土",
    "太陽": "火",
    "紫炁": "木",
    "台將": "土",
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

    # 金虎大煞
    with cols[1]:
        gt = pan.get("金虎大煞", "—")
        st.metric("金虎大煞", gt, help="金火大煞例")

    # 停處（嚴格計算）
    with cols[2]:
        stop = strict.get("stop_branch") or "—"
        st.metric("合炁停處", stop, help="雷霆合炁停年歌 + 逆數")

    # 天氣
    with cols[3]:
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


# create_plotly_nine_palace 已移除（盤式改用 SVG，不再使用 Plotly 建構九宮格）


def add_history_entry(pan: Dict, gz: str, year: int, month: int, day: int, hour: int, minute: int):
    """簡單歷史記錄（session_state）"""
    if "history" not in st.session_state:
        st.session_state.history = []
    entry = {
        "time": f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}",
        "gz": gz,
        "main_sha": pan.get("金虎大煞"),
        "arrow": pan.get("雷霆年月日時箭", [None])[0],
    }
    # 避免重複
    if not st.session_state.history or st.session_state.history[0]["time"] != entry["time"]:
        st.session_state.history.insert(0, entry)
    st.session_state.history = st.session_state.history[:8]  # 限 8 筆


def render_history():
    """顯示可點擊的歷史"""
    if st.session_state.get("history"):
        st.markdown("**最近排盤歷史（點擊可參考，實際需重新輸入日期）**")
        for h in st.session_state.history[:5]:
            st.caption(f"{h['time']} | {h['gz']} | 主煞:{h.get('main_sha')} | 年箭:{h.get('arrow')}")


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

# 主 Tabs：總覽 / 詳情 / 古籍 / 工具（已移除視覺化 sub-tab）
main_tabs = st.tabs([
    "📊 總覽 Overview",
    "📜 年月日時詳情",
    "📖 古籍對照 & 原文依據",
    "🛠️ 工具與匯出"
])

# 重新計算一次以取得最新 results（r_year 等已在 sidebar 後統一定義）
try:
    final_results = gen_results(r_year, r_month, r_day, r_hour, r_minute)
    pan = final_results["pan"]
    strict = final_results.get("strict", {})
    gz = final_results["gz"]

    # 記錄歷史
    add_history_entry(pan, gz, r_year, r_month, r_day, r_hour, r_minute)

    ui_mode = st.session_state.get("ui_mode", "新手模式（推薦）")
    is_advanced = "進階" in ui_mode

    # ===================== 總覽 Tab =====================
    with main_tabs[0]:
        st.subheader(f"📋 {pan.get('日期時間')}")
        st.markdown(f"**{gz}**")

        st.divider()

        # 合炁排盤 - 使用純 SVG（不使用 Plotly），並以分頁呈現年月日時四版
        st.markdown("**合炁排盤**")

        # 準備四個層級的資料（盡量相容現有 pan 結構）
        year_heqi = pan.get("雷霆年合炁", {}) or {}
        month_heqi = pan.get("雷霆月合炁", {}) or {}
        day_heqi = pan.get("雷霆日局", {}) or final_results.get("clockwise", {}) or {}
        hour_raw = pan.get("雷霆時合炁值山向定局", {}) or {}
        hour_heqi = {}
        if isinstance(hour_raw, dict):
            for k, v in hour_raw.items():
                if isinstance(v, dict):
                    hour_heqi.update({kk: str(vv) for kk, vv in v.items() if not isinstance(vv, (dict, list))})
                else:
                    hour_heqi[str(k)] = str(v)

        heqi_subtabs = st.tabs(["年合炁", "月合炁", "日合炁", "時合炁"])

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
            svg = build_nine_palace_svg(hour_heqi)
            st.markdown(svg, unsafe_allow_html=True)

        st.divider()
        render_key_metrics(pan, strict)

        render_history()

    # ===================== 年月日時詳情 Tab =====================
    with main_tabs[1]:
        st.subheader("年月日時層級合炁（嚴格依歌訣計算）")

        # 雷霆年
        with st.container(border=True):
            st.markdown("### 📅 雷霆年")
            if is_advanced:
                st.caption("據「雷霆合炁停年歌」及「昇玄上局年起例」")
                render_source_box("雷霆合炁停年歌", HEQI_STOP_YEAR_RHYME)
            st.markdown(f"**停處（嚴格計算）**：{strict.get('stop_branch', '—')}")
            st.markdown(f"**年中心星（起年例）**：{strict.get('year_center_star', '—')}")
            if is_advanced:
                st.markdown("**雷霆年昇玄值向**：")
                st.json(pan.get("雷霆年昇玄值向", {}))
                st.markdown("**雷霆年合炁**：")
                st.json(pan.get("雷霆年合炁", {}))

        # 雷霆月
        with st.container(border=True):
            st.markdown("### 🌙 雷霆月")
            if is_advanced:
                render_source_box("起月例", HEQI_MONTH_RHYME)
            st.markdown(f"**月中心星**：{strict.get('month_center_star', pan.get('雷霆月', '—'))}")
            if is_advanced:
                st.markdown("**雷霆月局 / 合炁**：")
                st.json({"月局": pan.get("雷霆月局"), "月合炁": pan.get("雷霆月合炁")})

        # 雷霆日 + 時（進階顯示更多）
        with st.container(border=True):
            st.markdown("### ☀️ 雷霆日 / ⏰ 雷霆時")
            if is_advanced:
                render_source_box("起日例", HEQI_DAY_RHYME)
                render_source_box("起時例", HEQI_HOUR_RHYME)
            st.markdown(f"**日方合炁**：{pan.get('雷霆日方合炁')}")
            st.markdown(f"**雷霆時**：{pan.get('雷霆時')}")
            if is_advanced:
                st.json({"日局": pan.get("雷霆日局"), "時合炁": pan.get("雷霆時合炁值山向定局")})

        if not is_advanced:
            st.success("新手模式已簡化層級細節。如需完整歌訣與多宮飛遁資料，請切換進階模式。")

    # ===================== 古籍對照 & 原文依據 Tab =====================
    with main_tabs[2]:
        st.subheader("📖 古籍對照與 verbatim 歌訣（100% 原文 traceability）")

        st.markdown("### 核心歌訣（直接來自 rules.py）")
        render_source_box("雷霆合炁停年歌 + 停年立成局", HEQI_STOP_YEAR_RHYME, "原文第91-101行")
        render_source_box("起年例（日夏太陽方合炁）", "甲庚血刃丙壬金丁癸，還從月孛尋六己。台將紫炁戊乙辛，偏向日邊臨收入中宮飛出。")
        render_source_box("昇玄上局年起例（起雷公）", "甲己順羊逆巽宮乙庚順虎逆壬同丙辛順犬逆坤位丁壬順丑逆乾中戊癸順辰逆艮上此為年例起行蹤。")
        render_source_box("起月例", HEQI_MONTH_RHYME)
        render_source_box("起日例", HEQI_DAY_RHYME)
        render_source_box("起時例", HEQI_HOUR_RHYME)

        st.divider()
        st.markdown("### 完整術語解釋（含原文片段）")
        search = st.text_input("🔍 搜尋術語或關鍵字", key="full_glossary_search")
        for term, desc in TERM_GLOSSARY.items():
            if not search or search.lower() in term.lower() or search.lower() in desc.lower():
                with st.expander(term, expanded=False):
                    st.markdown(desc)
                    st.caption("（以上解釋已附原文依據片段，完整歌訣見上方及 rules.py）")

    # ===================== 工具與匯出 Tab =====================
    with main_tabs[3]:
        st.subheader("🛠️ 工具與匯出")

        # 匯出
        md_text = generate_markdown_export(
            pan, gz,
            final_results.get("clockwise", {}),
            final_results.get("anticlockwise", {}),
        )
        st.download_button(
            "⬇️ 下載 Markdown 排盤報告",
            data=md_text.encode("utf-8"),
            file_name=f"雷霆曜氣_{r_year}{r_month:02d}{r_day:02d}_{r_hour:02d}{r_minute:02d}.md",
            mime="text/markdown",
            use_container_width=True
        )

        if is_advanced:
            st.code(md_text, language="markdown")

        st.divider()
        render_history()

        if is_advanced:
            with st.expander("原始計算資料（進階）"):
                st.json(pan)

except Exception as e:
    st.error(f"生成盤局時發生錯誤：{str(e)}")
    st.exception(e)

# ── 書目 Tab（保留舊的第二個 tab 作為參考） ──
with st.expander("📚 專案書目與說明（舊版內容）", expanded=False):
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            readme_content = f.read()
        st.markdown(readme_content, unsafe_allow_html=True)
    except FileNotFoundError:
        st.info("README.md 未找到。")


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

    @media (max-width: 768px) {
        .stApp { font-size: 1.08em; line-height: 1.4; }
        .nine-palace-svg { max-width: 100%; }  /* 手機填滿 */
        .stTabs [data-baseweb="tab-list"] { flex-wrap: wrap; font-size: 1.05em; }
        .stContainer, .result-card { padding: 16px 12px; margin-bottom: 14px; }
        .stMarkdown h3, .stSubheader { font-size: 1.15em; }
        .stTabs [data-baseweb="tab"] { padding: 8px 4px; }
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
