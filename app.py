# -*- coding: utf-8 -*-
import html
import streamlit as st
import datetime
import pytz
from contextlib import contextmanager, redirect_stdout
from io import StringIO
from luiting import Luiting

PALACE_NAMES = frozenset('巽離坤震中兌艮坎乾')

# Initialize session state to control rendering
if 'render_default' not in st.session_state:
    st.session_state.render_default = True


def format_dict(d, indent=0):
    """格式化字典為可讀的文本"""
    items = []
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
    """捕獲 stdout 並將其傳遞給指定的輸出函數"""
    with StringIO() as stdout, redirect_stdout(stdout):
        old_write = stdout.write
        def new_write(string):
            ret = old_write(string)
            output_func(stdout.getvalue())
            return ret
        stdout.write = new_write
        yield


# Streamlit 頁面配置
st.set_page_config(
    layout="wide",
    page_title="雷霆曜氣排盤",
    page_icon="⚡"
)

# 側邊欄輸入
with st.sidebar:
    st.header("排盤參數設置")

    now = datetime.datetime.now(pytz.timezone('Asia/Hong_Kong'))
    col1, col2 = st.columns(2)
    with col1:
        my = st.number_input('年', min_value=1, max_value=2100, value=now.year, key="year")
        mm = st.number_input('月', min_value=1, max_value=12, value=now.month, key="month")
        md = st.number_input('日', min_value=1, max_value=31, value=now.day, key="day")
    with col2:
        mh = st.number_input('時', min_value=0, max_value=23, value=now.hour, key="hour")
        mmin = st.number_input('分', min_value=0, max_value=59, value=now.minute, key="minute")

    instant = st.button('即時盤', use_container_width=True)


@st.cache_data
def gen_results(year, month, day, hour, minute):
    """生成雷霆曜氣計算結果"""
    lt = Luiting(year, month, day, hour, minute)
    pan = lt.pan()
    gangzhi = lt.gangzhi()
    gz = f"{gangzhi[0]}年 {gangzhi[1]}月 {gangzhi[2]}日 {gangzhi[3]}時 {gangzhi[4]}分"
    clockwise = lt.luitingheqiday_clockwise()
    anticlockwise = lt.luitingheqiday_anticlockwise()
    return {"pan": pan, "gz": gz, "clockwise": clockwise, "anticlockwise": anticlockwise}


def build_nine_palace_html(pan, clockwise, anticlockwise):
    """構建九宮格排盤HTML"""
    palace_order = [
        ['巽', '離', '坤'],
        ['震', '中', '兌'],
        ['艮', '坎', '乾'],
    ]

    # Map special markers to palaces
    marker_keys = ['金虎大煞', '流火凶星', '值符', '傳音', '日帝星']
    palace_markers = {}
    for key in marker_keys:
        val = pan.get(key)
        if val:
            palace_markers.setdefault(val, []).append(key)

    year_heqi = pan.get('雷霆年合炁') or {}
    month_heqi = pan.get('雷霆月合炁') or {}
    month_ju = pan.get('雷霆月局') or {}
    day_ju = pan.get('雷霆日局') or {}
    cw = clockwise or {}
    acw = anticlockwise or {}

    # Extract year shengxuan values by palace (first char of key)
    year_sx = {}
    for k, v in (pan.get('雷霆年昇玄值向') or {}).items():
        if k and k[0] in PALACE_NAMES:
            year_sx[k[0]] = v

    cells_html = ""
    for row in palace_order:
        for p in row:
            lines = []

            data_pairs = [
                ('年值', year_sx.get(p, '')),
                ('年合', year_heqi.get(p, '')),
                ('月合', month_heqi.get(p, '')),
                ('月局', month_ju.get(p, '')),
                ('日局', day_ju.get(p, '')),
                ('順局', cw.get(p, '')),
                ('逆局', acw.get(p, '')),
            ]

            for label, val in data_pairs:
                if val:
                    lines.append(
                        f'<div class="np-item">'
                        f'<span class="np-lbl">{label}</span> {html.escape(str(val))}'
                        f'</div>'
                    )

            marks = palace_markers.get(p, [])
            mark_html = ''.join(
                f'<div class="np-mark">⚠ {html.escape(m)}</div>' for m in marks
            )

            cells_html += (
                f'<div class="np-cell">'
                f'<div class="np-title">{p}</div>'
                f'<div class="np-data">{"".join(lines)}</div>'
                f'{mark_html}'
                f'</div>'
            )

    return f'<div class="np-grid">{cells_html}</div>'


# 創建標籤頁
tabs = st.tabs(['⚡雷霆曜氣排盤', '📚書目'])

# 雷霆曜氣排盤
with tabs[0]:
    output = st.empty()
    with st_capture(output.code):
        try:
            if instant:
                now = datetime.datetime.now(pytz.timezone('Asia/Hong_Kong'))
                r_year, r_month, r_day, r_hour, r_minute = now.year, now.month, now.day, now.hour, now.minute
            else:
                r_year, r_month, r_day, r_hour, r_minute = my, mm, md, mh, mmin
            results = gen_results(r_year, r_month, r_day, r_hour, r_minute)
            st.session_state.render_default = False

            if results:
                pan = results["pan"]

                # 基本信息
                with st.expander("基本資訊", expanded=True):
                    st.markdown(f"**日期時間**：{pan.get('日期時間')}")
                    st.markdown(f"**干支**：{results['gz']}")
                    st.markdown(f"**農曆**：{pan.get('農曆')}")
                    st.markdown(f"**節氣**：{pan.get('節氣')}")
                    st.markdown(f"**月五行**：{pan.get('月五行')}")
                    st.markdown(f"**日干支**：{pan.get('日干支')}")
                    st.markdown(f"**日陰陽**：{pan.get('日陰陽')}")
                    st.markdown(f"**日干支納音**：{pan.get('日干支納音')}")

                # 九宮格排盤
                with st.expander("九宮格排盤", expanded=True):
                    grid_html = build_nine_palace_html(
                        pan, results.get("clockwise", {}), results.get("anticlockwise", {})
                    )
                    st.markdown(grid_html, unsafe_allow_html=True)

                # 雷霆箭
                with st.expander("雷霆年月日時箭", expanded=True):
                    arrows = pan.get('雷霆年月日時箭', [])
                    labels = ['年箭', '月箭', '日箭', '時箭']
                    for label, arrow in zip(labels, arrows):
                        st.markdown(f"**{label}**：{arrow}")

                # 雷霆年
                with st.expander("雷霆年", expanded=False):
                    st.markdown("**雷霆年昇玄值向**：")
                    st.markdown(format_dict(pan.get('雷霆年昇玄值向', {}), 1))
                    st.markdown("---")
                    st.markdown("**雷霆年合炁到向**：")
                    st.markdown(format_dict(pan.get('雷霆年合炁到向', {}), 1))
                    st.markdown("---")
                    st.markdown("**雷霆年合炁**：")
                    st.markdown(format_dict(pan.get('雷霆年合炁', {}), 1))

                # 雷霆月
                with st.expander("雷霆月", expanded=False):
                    st.markdown(f"**雷霆月**：{pan.get('雷霆月')}")
                    st.markdown("---")
                    st.markdown("**雷霆月局**：")
                    st.markdown(format_dict(pan.get('雷霆月局', {}), 1))
                    st.markdown("---")
                    st.markdown("**雷霆月合炁**：")
                    st.markdown(format_dict(pan.get('雷霆月合炁', {}), 1))

                # 雷霆日
                with st.expander("雷霆日", expanded=False):
                    st.markdown(f"**雷霆日方合炁**：{pan.get('雷霆日方合炁')}")
                    st.markdown("---")
                    st.markdown("**雷霆日局**：")
                    st.markdown(format_dict(pan.get('雷霆日局', {}), 1))

                # 雷霆時
                with st.expander("雷霆時", expanded=False):
                    st.markdown(f"**雷霆時**：{pan.get('雷霆時')}")
                    st.markdown("---")
                    st.markdown("**雷霆時合炁值山向定局**：")
                    heqi_hour = pan.get('雷霆時合炁值山向定局', {})
                    for k, v in heqi_hour.items():
                        st.markdown(f"**{k}**：")
                        if isinstance(v, dict):
                            st.markdown(format_dict(v, 1))
                        else:
                            st.markdown(f"　{v}")

                # 吉凶神煞
                with st.expander("吉凶神煞", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**金虎大煞**：{pan.get('金虎大煞')}")
                        st.markdown(f"**流火凶星**：{pan.get('流火凶星')}")
                        st.markdown(f"**值符**：{pan.get('值符')}")
                        st.markdown(f"**傳音**：{pan.get('傳音')}")
                    with col2:
                        st.markdown(f"**月帝星**：{pan.get('月帝星')}")
                        st.markdown(f"**日帝星**：{pan.get('日帝星')}")

                # 時星遁
                with st.expander("時星遁", expanded=True):
                    st.markdown(f"**時星遁**：{pan.get('時星遁')}")
                    st.markdown(f"**時星**：{pan.get('時星')}")
                    st.markdown(f"**遁數**：{pan.get('遁數')}")
                    st.markdown(f"**遁星**：{pan.get('遁星')}")

                # 天氣
                with st.expander("天氣預測", expanded=True):
                    st.markdown(f"**天氣**：{pan.get('天氣')}")
                    st.markdown(f"**星禽應事**：{pan.get('星禽應事')}")
                    st.markdown(f"**四季禽星應事**：{pan.get('四季禽星應事')}")

                # 三伯
                with st.expander("雷公風伯雨伯", expanded=True):
                    st.markdown(f"**雷公**：{pan.get('雷公')}")
                    st.markdown(f"**風伯**：{pan.get('風伯')}")
                    st.markdown(f"**雨伯**：{pan.get('雨伯')}")

                # 日合炁順逆局
                with st.expander("雷霆日合炁順逆局", expanded=False):
                    st.markdown("**順局**：")
                    st.markdown(format_dict(results.get("clockwise", {}), 1))
                    st.markdown("---")
                    st.markdown("**逆局**：")
                    st.markdown(format_dict(results.get("anticlockwise", {}), 1))

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

# 書目
with tabs[1]:
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            readme_content = f.read()
        st.markdown(readme_content, unsafe_allow_html=True)
    except FileNotFoundError:
        st.info("README.md 未找到。")

# Custom CSS
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
    unsafe_allow_html=True
)
