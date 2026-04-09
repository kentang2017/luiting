# -*- coding: utf-8 -*-
"""
雷霆曜氣排盤 Streamlit 介面 — Thunder Qi Divination Web UI

提供互動式網頁介面，讓使用者輸入日期時間後生成雷霆曜氣排盤。
包含九宮格排盤、吉凶神煞、天氣預測等視覺化呈現，
並提供術語說明和 Markdown 匯出功能。
"""

import html
import datetime
from io import StringIO
from contextlib import contextmanager, redirect_stdout
from typing import Any, Dict, List, Optional

import streamlit as st
import pytz

from luiting import Luiting

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
        f"# ⚡ 雷霆曜氣排盤結果",
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

st.set_page_config(layout="wide", page_title="雷霆曜氣排盤", page_icon="⚡")

st.title("⚡ 堅雷霆曜氣")
st.caption("依《道法會元》卷一百二十九《雷霆箭煞年月樞機》推算")

# 初始化 session state
if "render_default" not in st.session_state:
    st.session_state.render_default = True


# ===========================================================================
# 側邊欄輸入
# ===========================================================================

with st.sidebar:
    st.header("📅 排盤參數設置")

    now = datetime.datetime.now(pytz.timezone("Asia/Hong_Kong"))
    col1, col2 = st.columns(2)
    with col1:
        my = st.number_input("年", min_value=1, max_value=2100, value=now.year, key="year")
        mm = st.number_input("月", min_value=1, max_value=12, value=now.month, key="month")
        md = st.number_input("日", min_value=1, max_value=31, value=now.day, key="day")
    with col2:
        mh = st.number_input("時", min_value=0, max_value=23, value=now.hour, key="hour")
        mmin = st.number_input("分", min_value=0, max_value=59, value=now.minute, key="minute")

    instant = st.button("⏱️ 即時盤", use_container_width=True)

    st.divider()
    st.subheader("📖 術語說明")
    with st.expander("查看術語解釋", expanded=False):
        for term, desc in TERM_GLOSSARY.items():
            st.markdown(f"**{term}**：{desc}")


# ===========================================================================
# 計算引擎
# ===========================================================================


@st.cache_data
def gen_results(year: int, month: int, day: int, hour: int, minute: int) -> Dict:
    """生成雷霆曜氣計算結果。"""
    lt = Luiting(year, month, day, hour, minute)
    pan = lt.pan()
    gangzhi = lt.gangzhi()
    gz = f"{gangzhi[0]}年 {gangzhi[1]}月 {gangzhi[2]}日 {gangzhi[3]}時 {gangzhi[4]}分"
    clockwise = lt.luitingheqiday_clockwise()
    anticlockwise = lt.luitingheqiday_anticlockwise()
    return {
        "pan": pan,
        "gz": gz,
        "clockwise": clockwise,
        "anticlockwise": anticlockwise,
    }


# ===========================================================================
# 九宮格排盤
# ===========================================================================


def build_nine_palace_html(
    pan: Dict, clockwise: Optional[Dict], anticlockwise: Optional[Dict]
) -> str:
    """構建九宮格排盤 HTML。"""
    palace_order = [
        ["巽", "離", "坤"],
        ["震", "中", "兌"],
        ["艮", "坎", "乾"],
    ]

    # 特殊標記映射到宮位
    marker_keys = ["金虎大煞", "流火凶星", "值符", "傳音", "日帝星"]
    palace_markers: Dict[str, List[str]] = {}
    for key in marker_keys:
        val = pan.get(key)
        if val:
            palace_markers.setdefault(val, []).append(key)

    year_heqi = pan.get("雷霆年合炁") or {}
    month_heqi = pan.get("雷霆月合炁") or {}
    month_ju = pan.get("雷霆月局") or {}
    day_ju = pan.get("雷霆日局") or {}
    cw = clockwise or {}
    acw = anticlockwise or {}

    # 年昇玄值向（取首字對應宮位）
    year_sx: Dict[str, str] = {}
    for k, v in (pan.get("雷霆年昇玄值向") or {}).items():
        if k and k[0] in PALACE_NAMES:
            year_sx[k[0]] = v

    cells_html = ""
    for row in palace_order:
        for p in row:
            lines: List[str] = []

            data_pairs = [
                ("年值", year_sx.get(p, "")),
                ("年合", year_heqi.get(p, "")),
                ("月合", month_heqi.get(p, "")),
                ("月局", month_ju.get(p, "")),
                ("日局", day_ju.get(p, "")),
                ("順局", cw.get(p, "")),
                ("逆局", acw.get(p, "")),
            ]

            for label, val in data_pairs:
                if val:
                    lines.append(
                        f'<div class="np-item">'
                        f'<span class="np-lbl">{label}</span> {html.escape(str(val))}'
                        f"</div>"
                    )

            marks = palace_markers.get(p, [])
            mark_html = "".join(
                f'<div class="np-mark">⚠ {html.escape(m)}</div>' for m in marks
            )

            cells_html += (
                f'<div class="np-cell">'
                f'<div class="np-title">{p}</div>'
                f'<div class="np-data">{"".join(lines)}</div>'
                f"{mark_html}"
                f"</div>"
            )

    return f'<div class="np-grid">{cells_html}</div>'


# ===========================================================================
# 主要內容
# ===========================================================================

tabs = st.tabs(["⚡ 雷霆曜氣排盤", "📚 書目"])

with tabs[0]:
    output = st.empty()
    with st_capture(output.code):
        try:
            if instant:
                now = datetime.datetime.now(pytz.timezone("Asia/Hong_Kong"))
                r_year, r_month, r_day = now.year, now.month, now.day
                r_hour, r_minute = now.hour, now.minute
            else:
                r_year, r_month, r_day, r_hour, r_minute = my, mm, md, mh, mmin

            results = gen_results(r_year, r_month, r_day, r_hour, r_minute)
            st.session_state.render_default = False

            if results:
                pan = results["pan"]

                # ── 基本資訊 ──
                with st.expander("📋 基本資訊", expanded=True):
                    st.markdown(f"**日期時間**：{pan.get('日期時間')}")
                    st.markdown(f"**干支**：{results['gz']}")
                    st.markdown(f"**農曆**：{pan.get('農曆')}")
                    st.markdown(f"**節氣**：{pan.get('節氣')}")
                    st.markdown(f"**月五行**：{pan.get('月五行')}")
                    st.markdown(f"**日干支**：{pan.get('日干支')}（{pan.get('日陰陽')}）")
                    st.markdown(f"**日干支納音**：{pan.get('日干支納音')}")

                # ── 九宮格排盤 ──
                with st.expander("🏛️ 雷霆曜氣綜合排盤", expanded=True):
                    grid_html = build_nine_palace_html(
                        pan,
                        results.get("clockwise", {}),
                        results.get("anticlockwise", {}),
                    )
                    st.markdown(grid_html, unsafe_allow_html=True)

                # ── 雷霆箭 ──
                with st.expander("🏹 雷霆年月日時箭", expanded=True):
                    st.caption(
                        "據《雷霆箭煞年月樞機》：「看他發其箭定日時煞，"
                        "此日雷箭非特動雷，亦能料理諸事。」"
                    )
                    arrows = pan.get("雷霆年月日時箭", [])
                    labels = ["年箭", "月箭", "日箭", "時箭"]
                    for label, arrow in zip(labels, arrows):
                        meaning = ARROW_MEANINGS.get(arrow, "")
                        st.markdown(f"**{label}**：{arrow}　{meaning}")

                # ── 雷霆年 ──
                with st.expander("📅 雷霆年", expanded=False):
                    st.caption("據「雷霆合炁停年歌」及「昇玄上局年起例」推算")
                    st.markdown("**雷霆年昇玄值向**：")
                    st.markdown(format_dict(pan.get("雷霆年昇玄值向", {}), 1))
                    st.markdown("---")
                    st.markdown("**雷霆年合炁到向**：")
                    st.markdown(format_dict(pan.get("雷霆年合炁到向", {}), 1))
                    st.markdown("---")
                    st.markdown("**雷霆年合炁**：")
                    st.markdown(format_dict(pan.get("雷霆年合炁", {}), 1))

                # ── 雷霆月 ──
                with st.expander("🌙 雷霆月", expanded=False):
                    st.caption("據「起月例」：「太歲常將遁甲停，更將停處起元正。」")
                    st.markdown(f"**雷霆月**：{pan.get('雷霆月')}")
                    st.markdown("---")
                    st.markdown("**雷霆月局**：")
                    st.markdown(format_dict(pan.get("雷霆月局", {}), 1))
                    st.markdown("---")
                    st.markdown("**雷霆月合炁**：")
                    st.markdown(format_dict(pan.get("雷霆月合炁", {}), 1))

                # ── 雷霆日 ──
                with st.expander("☀️ 雷霆日", expanded=False):
                    st.caption(
                        "據「起日例」：「丑日元來是刃星，到頭逆轉卻分明。"
                        "常將本日依元位，飛入中宮卻順行。」"
                    )
                    st.markdown(f"**雷霆日方合炁**：{pan.get('雷霆日方合炁')}")
                    st.markdown("---")
                    st.markdown("**雷霆日局**：")
                    st.markdown(format_dict(pan.get("雷霆日局", {}), 1))

                # ── 雷霆時 ──
                with st.expander("⏰ 雷霆時", expanded=False):
                    st.caption(
                        "據「起時例」：「求時一法少人知，甲己先從燥火推。"
                        "乙庚太陽為定例，丙辛還向天罡期。」"
                    )
                    st.markdown(f"**雷霆時**：{pan.get('雷霆時')}")
                    st.markdown("---")
                    st.markdown("**雷霆時合炁值山向定局**：")
                    heqi_hour = pan.get("雷霆時合炁值山向定局", {})
                    for k, v in heqi_hour.items():
                        st.markdown(f"**{k}**：")
                        if isinstance(v, dict):
                            st.markdown(format_dict(v, 1))
                        else:
                            st.markdown(f"　{v}")

                # ── 吉凶神煞 ──
                with st.expander("⚠️ 吉凶神煞", expanded=True):
                    st.caption(
                        "據《雷霆箭煞年月樞機》：「凡召雷行事，先召直符召雷公，"
                        "次行天罡號，然後使雷箭。」"
                    )
                    col1, col2 = st.columns(2)
                    with col1:
                        gt = pan.get("金虎大煞")
                        st.markdown(f"**金虎大煞**：{gt}")
                        if gt:
                            st.caption(TERM_GLOSSARY.get("金虎大煞", "")[:60] + "…")
                        lh = pan.get("流火凶星")
                        st.markdown(f"**流火凶星**：{lh}")
                        zf = pan.get("值符")
                        st.markdown(f"**值符**：{zf}")
                        cy = pan.get("傳音")
                        st.markdown(f"**傳音**：{cy}")
                    with col2:
                        st.markdown(f"**月帝星**：{pan.get('月帝星')}")
                        st.markdown(f"**日帝星**：{pan.get('日帝星')}")

                # ── 時星遁 ──
                with st.expander("⭐ 時星遁", expanded=True):
                    st.caption("據「飛定星宿主事法」「十干起時例（陽順陰逆）」推算")
                    st.markdown(f"**時星遁**：{pan.get('時星遁')}")
                    st.markdown(f"**時星**：{pan.get('時星')}")
                    st.markdown(f"**遁數**：{pan.get('遁數')}")
                    st.markdown(f"**遁星**：{pan.get('遁星')}")

                # ── 天氣 ──
                with st.expander("🌤️ 天氣預測", expanded=True):
                    st.caption("據「星禽應事」及二十八宿四季禽星推算")
                    st.markdown(f"**天氣**：{pan.get('天氣')}")
                    st.markdown(f"**星禽應事**：{pan.get('星禽應事')}")
                    st.markdown(f"**四季禽星應事**：{pan.get('四季禽星應事')}")

                # ── 三伯 ──
                with st.expander("🌩️ 雷公風伯雨伯", expanded=True):
                    st.caption(
                        "據「起雷次舍」：「翼軫主雷，虛危主雪，箕星好風，畢星好雨，星宿主晴。」"
                    )
                    st.markdown(f"**雷公**：{pan.get('雷公')}")
                    st.markdown(f"**風伯**：{pan.get('風伯')}")
                    st.markdown(f"**雨伯**：{pan.get('雨伯')}")

                # ── 日合炁順逆局 ──
                with st.expander("🔄 雷霆日合炁順逆局", expanded=False):
                    st.markdown("**順局**：")
                    st.markdown(format_dict(results.get("clockwise", {}), 1))
                    st.markdown("---")
                    st.markdown("**逆局**：")
                    st.markdown(format_dict(results.get("anticlockwise", {}), 1))

                # ── Markdown 匯出 ──
                with st.expander("📥 匯出排盤結果", expanded=False):
                    md_text = generate_markdown_export(
                        pan, results["gz"],
                        results.get("clockwise", {}),
                        results.get("anticlockwise", {}),
                    )
                    st.download_button(
                        label="⬇️ 下載 Markdown 檔案",
                        data=md_text.encode("utf-8"),
                        file_name=f"雷霆曜氣_{r_year}{r_month:02d}{r_day:02d}_{r_hour:02d}{r_minute:02d}.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )
                    st.code(md_text, language="markdown")

                # 控制台摘要
                print(
                    f"{pan.get('日期時間')} |\n"
                    f"農曆︰{pan.get('農曆')} | {pan.get('節氣')} |\n"
                    f"{results['gz']} |\n"
                    f"日干支︰{pan.get('日干支')} ({pan.get('日陰陽')}) |\n"
                    f"日干支納音︰{pan.get('日干支納音')} |\n"
                    f"雷霆年月日時箭︰{'、'.join(str(a) for a in pan.get('雷霆年月日時箭', []))} |\n"
                    f"雷霆月︰{pan.get('雷霆月')} | 雷霆時︰{pan.get('雷霆時')} |\n"
                    f"天氣︰{pan.get('天氣')} | {pan.get('星禽應事')} |\n"
                    f"金虎大煞︰{pan.get('金虎大煞')} | 流火凶星︰{pan.get('流火凶星')} |"
                )

        except Exception as e:
            st.error(f"生成盤局時發生錯誤：{str(e)}")

# ── 書目 ──
with tabs[1]:
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
    .np-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 6px;
        margin: 8px 0;
    }
    .np-cell {
        background: #252730;
        border: 1px solid #4a4a5a;
        border-radius: 6px;
        padding: 8px 6px;
        text-align: center;
    }
    .np-title {
        font-size: 1.2em;
        font-weight: bold;
        color: #FF4B4B;
        border-bottom: 1px solid #4a4a5a;
        padding-bottom: 4px;
        margin-bottom: 4px;
    }
    .np-item {
        font-size: 0.85em;
        color: #E0E0E0;
        margin: 2px 0;
    }
    .np-lbl {
        color: #8899aa;
        margin-right: 2px;
    }
    .np-mark {
        font-size: 0.8em;
        color: #FFD700;
        font-weight: bold;
        margin-top: 3px;
    }
    .stExpander {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        margin-top: 5px;
        margin-bottom: 10px;
    }
    html[data-theme="dark"] .stExpander {
        border: 1px solid #3d3d3d;
    }
    .stButton button {
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.15s ease-in-out;
        background-color: #4e7496;
        color: white;
    }
    .stButton button:hover:enabled {
        background-color: #3a5a78;
        transform: translateY(-1px);
    }
    </style>
    """,
    unsafe_allow_html=True,
)
