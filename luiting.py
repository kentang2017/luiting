# -*- coding: utf-8 -*-
"""
雷霆曜氣核心計算引擎 — Luiting (Thunder Qi) Calculation Engine

基於《道法會元》卷一百二十九《雷霆箭煞年月樞機》，實現雷霆曜氣排盤的
年、月、日、時合炁、昇玄值向、金虎大煞、流火凶星、值符、傳音、帝星、
雷箭等各項計算。

典籍出處：
    - 《道法會元》卷一百二十九《雷霆箭煞年月樞機》
    - 《造命宗鏡集》卷六《雷霆曜氣》
    - 《鰲頭通書》卷六《雷霆曜氣》

Created on Sat Aug 22 18:30:06 2020
@author: ken tang
"""

from __future__ import annotations

import itertools
import re
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

import sxtwl

from config import jq, new_list, multi_key_dict_get

# ===========================================================================
# 常量定義 — Constants
# ===========================================================================

TIANGAN: str = "甲乙丙丁戊己庚辛壬癸"
DIZHI: str = "子丑寅卯辰巳午未申酉戌亥"

# 二十八宿
SU_28: str = "角亢氐房心尾箕斗牛女虛危室壁奎婁胃昴畢觜參井鬼柳星張翼軫"

# 六十甲子
JIAZI_60: List[str] = [
    TIANGAN[x % 10] + DIZHI[x % 12] for x in range(60)
]

# 十二曜氣星（雷霆十二星）
# 據《雷霆箭煞年月樞機》：血刃、太陽、月孛、金水、台將、天罡、土溽、奇羅、燥火、丙乙、水潦、紫炁
STAR_12: List[str] = re.findall(
    "..", "太陽血刃紫炁水潦丙乙燥火奇羅土溽天罡台將金水月孛"
)

# 天干地支混合排列（用於雷箭計算：二十四山方位）
TIANGAN_DIZHI_MIX: List[str] = list(
    "子癸丑艮寅甲卯乙辰巽巳丙午丁未坤申庚酉辛戌乾亥壬"
)

# 雷霆十箭名
ARROW_NAMES: List[str] = re.findall(
    "..", "風雲太陽雷母吉祥鬼火飛劍血刃火烈木神雷公旺相亡沒"
)

# 農曆月份名稱
LUNAR_MONTH_NAMES: List[str] = [
    "十一", "十二", "正", "二", "三", "四", "五", "六", "七", "八", "九", "十"
]

# 農曆日名稱
LUNAR_DAY_NAMES: List[str] = [
    "初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十",
    "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九",
    "二十", "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八",
    "廿九", "三十", "卅一",
]

# 中文數字
CNUM: str = "一二三四五六七八九十"

# 六甲旬
LIUJIA_SHUN: Dict[str, str] = {
    "甲子": "甲子", "甲戌": "甲戌", "甲申": "甲申",
    "甲午": "甲午", "甲辰": "甲辰", "甲寅": "甲寅",
}

# 九宮名稱
GONG_9: List[str] = ["中", "乾", "兌", "艮", "離", "坎", "坤", "震", "巽"]
GONG_8: List[str] = ["乾", "兌", "艮", "離", "坎", "坤", "震", "巽"]


# ===========================================================================
# 工具函數 — Utility Functions
# ===========================================================================


def _nlist(seq: list, start: Any) -> list:
    """從序列 *seq* 中以 *start* 為起點，順序循環生成等長列表。"""
    idx = seq.index(start)
    length = len(seq)
    return [seq[(idx + i) % length] for i in range(length)]


def _repeat_each(items: list, n: int) -> list:
    """將列表中每個元素重複 *n* 次。"""
    return [x for item in items for x in itertools.repeat(item, n)]


def _find_shun(gangzhi: str) -> str:
    """查找干支所屬六甲旬首。

    據《雷霆箭煞年月樞機》「起旬例」：
    甲子奇羅甲戌罡，甲申金水甲午陽。甲辰紫炁甲寅分丙乙。
    """
    for i in range(6):
        start = i * 10
        if gangzhi in JIAZI_60[start:start + 10]:
            return JIAZI_60[start]
    return ""


@lru_cache(maxsize=1)
def _minutes_jiazi_map() -> Dict[str, str]:
    """預計算 24h×60min → 干支 的映射表（每 2 分鐘一個干支）。"""
    t = [f"{h}:{m}" for h in range(24) for m in range(60)]
    cycle = _repeat_each(JIAZI_60, 2)
    return dict(zip(t, itertools.cycle(cycle)))


# ===========================================================================
# 雷霆曜氣主類 — Luiting Main Class
# ===========================================================================


class Luiting:
    """雷霆曜氣排盤計算引擎。

    根據《道法會元》卷一百二十九《雷霆箭煞年月樞機》的規則，
    計算指定年月日時的雷霆曜氣盤局，包括：
    - 雷霆合炁（年、月、日、時）
    - 昇玄值向
    - 金虎大煞、流火凶星
    - 值符、傳音
    - 帝星（月帝星、日帝星）
    - 雷霆箭（年、月、日、時箭）
    - 飛星遁宿、天氣預測

    Args:
        year: 公曆年。
        month: 公曆月。
        day: 公曆日。
        hour: 時（0–23）。
        minute: 分（0–59）。
    """

    def __init__(
        self, year: int, month: int, day: int, hour: int, minute: int
    ) -> None:
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute

        # 預計算干支（避免重複調用 sxtwl）
        self._gangzhi: Optional[List[str]] = None

    # ------------------------------------------------------------------
    # 基礎計算 — Basic Calculations
    # ------------------------------------------------------------------

    def gangzhi(self) -> List[str]:
        """計算年、月、日、時、分的干支。

        Returns:
            [年干支, 月干支, 日干支, 時干支, 分干支] 的列表。
        """
        if self._gangzhi is not None:
            return self._gangzhi

        cdate = sxtwl.fromSolar(self.year, self.month, self.day)
        yTG = TIANGAN[cdate.getYearGZ().tg] + DIZHI[cdate.getYearGZ().dz]
        mTG = TIANGAN[cdate.getMonthGZ().tg] + DIZHI[cdate.getMonthGZ().dz]
        dTG = TIANGAN[cdate.getDayGZ().tg] + DIZHI[cdate.getDayGZ().dz]
        hTG = TIANGAN[cdate.getHourGZ(self.hour).tg] + DIZHI[cdate.getHourGZ(self.hour).dz]
        gangzhi_minute = _minutes_jiazi_map().get(f"{self.hour}:{self.minute}", "")
        self._gangzhi = [yTG, mTG, dTG, hTG, gangzhi_minute]
        return self._gangzhi

    def find_jieqi(self) -> str:
        """查找當前日期所處節氣。"""
        return jq(self.year, self.month, self.day, self.hour)

    def find_season(self) -> str:
        """根據節氣判斷當前季節。

        Returns:
            「春」「夏」「秋」「冬」之一。
        """
        jq_names = re.findall(
            "..",
            "立春雨水驚蟄春分清明穀雨立夏小滿芒種夏至小暑大暑"
            "立秋處暑白露秋分寒露霜降立冬小雪大雪冬至小寒大寒",
        )
        seasons = list("春春春春春春夏夏夏夏夏夏秋秋秋秋秋秋冬冬冬冬冬冬")
        return dict(zip(jq_names, seasons)).get(self.find_jieqi(), "春")

    def yingyang(self, day_stem: str) -> str:
        """判斷日干的陰陽屬性。

        Args:
            day_stem: 日天干（單字）。

        Returns:
            「陽日」或「陰日」。
        """
        yang_stems = set(TIANGAN[::2])  # 甲丙戊庚壬
        return "陽日" if day_stem in yang_stems else "陰日"

    def lunar_date(self) -> str:
        """取得農曆日期字串。"""
        day = sxtwl.fromSolar(self.year, self.month, self.day)
        leap = "閏" if day.isLunarLeap() else ""
        return f"{day.getLunarYear()}年{leap}{day.getLunarMonth()}月{day.getLunarDay()}日"

    def lunar_date_detail(self) -> Dict[str, str]:
        """取得農曆月、日的數值字串。"""
        day = sxtwl.fromSolar(self.year, self.month, self.day)
        return {"月": f"{day.getLunarMonth()}月", "日": str(day.getLunarDay())}

    def month_element(self) -> str:
        """根據農曆月份推算月五行。

        據古法，不同月份對應不同五行屬性：
        - 2、4、8月：水動
        - 3、6、9月：木動
        - 1、5、7月：水土
        - 10、11、12月：金動
        """
        month_str = self.lunar_date_detail()["月"].replace("月", "")
        elements = {
            ("2", "4", "8"): "水動",
            ("3", "6", "9"): "木動",
            ("1", "5", "7"): "水土",
            ("10", "11", "12"): "金動",
        }
        return multi_key_dict_get(elements, month_str) or ""

    # ------------------------------------------------------------------
    # 雷公風伯雨伯 — Thunder Lord, Wind Earl, Rain Earl
    # ------------------------------------------------------------------

    def find_three_uncle(self) -> Dict[str, str]:
        """推算雷公、風伯、雨伯所在方位。

        據《雷霆箭煞年月樞機》「起雷次舍」：
        以日干支所屬六甲旬來決定雷公、風伯、雨伯的方位。
        """
        dshun = _find_shun(self.gangzhi()[2])
        shun = re.findall("..", "甲子甲寅甲辰甲午甲申甲戌")
        thunder = dict(zip(shun, list("午申戌子寅辰")))
        wind = dict(zip(shun, list("寅子寅寅午申")))
        rain = dict(zip(shun, list("戌辰午辰戌子")))
        return {
            "雷公": thunder.get(dshun, ""),
            "風伯": wind.get(dshun, ""),
            "雨伯": rain.get(dshun, ""),
        }

    # ------------------------------------------------------------------
    # 雷霆年昇玄值向 — Yearly Shengxuan Direction
    # ------------------------------------------------------------------

    def luitingyear(self) -> Dict[str, str]:
        """計算雷霆年昇玄值向。

        據《雷霆箭煞年月樞機》「雷霆合炁停年歌」：
        「甲子尋豬甲戌寅，甲申辰上好安身。甲午本宮扶上馬，
        甲辰申上妙推輪。甲寅戌上定其位，便知雷處實通神。」

        以年天干決定昇玄九宮飛布的起始位置和星辰排列。
        """
        yg = self.gangzhi()[0][0]
        stars = re.findall("..", "血刃太陽月孛金水台將天罡土溽奇羅燥火")
        stem_groups = [tuple(i) for i in re.findall("..", "甲己乙庚丁壬戊癸")] + ["丙", "辛"]
        gong = list("兌艮離坎坤震巽中乾")
        palace_lists = [
            [i] + new_list(gong, i[0])[1:]
            for i in ["兌丁巳丑", "坎癸辰申", "震亥", "離寅", "坤申", "坎申"]
        ]
        matched = multi_key_dict_get(dict(zip(stem_groups, palace_lists)), yg)
        if matched:
            return dict(zip(matched, stars))
        return {}

    # ------------------------------------------------------------------
    # 雷霆年合炁 — Yearly Heqi
    # ------------------------------------------------------------------

    def luitingheqiyear_mountain(self) -> Dict[str, str]:
        """計算雷霆年合炁到山向。

        以年天干決定中宮起星，順飛九宮。
        據「起年例」：「甲庚血刃丙壬金丁癸，還從月孛尋六己。
        台將紫炁戊乙辛，偏向日邊臨收入中宮飛出。」
        """
        yg = self.gangzhi()[0][0]
        all_stars = re.findall(
            "..", "血刃太陽月孛金水台將天罡土溽奇羅燥火丙乙水潦紫炁"
        )
        stem_groups = [tuple(i) for i in re.findall("..", "丁癸乙辛甲庚")] + ["戊", "己", "丙壬"]
        middle_gong = [new_list(all_stars, i)[0:9] for i in ["月孛", "太陽", "血刃", "紫炁", "台將", "金水"]]
        mountain = [
            "中宮", "乾甲山", "兌丁巳丑山", "艮丙山", "離壬戌寅山",
            "坎癸辰申山", "坤乙山", "震辰未亥山", "巽辛山",
        ]
        ddict = [dict(zip(mountain, i)) for i in middle_gong]
        return multi_key_dict_get(dict(zip(stem_groups, ddict)), yg) or {}

    def luitingheqiyear(self) -> Dict[str, str]:
        """計算雷霆年合炁（八宮分佈）。"""
        yg = self.gangzhi()[0][0]
        all_stars = re.findall(
            "..", "血刃太陽月孛金水台將天罡土溽奇羅燥火丙乙水潦紫炁"
        )
        stem_groups = [tuple(i) for i in re.findall("..", "丁癸乙辛甲庚")] + ["戊", "己", "丙壬"]
        head = [new_list(all_stars, i)[0:9] for i in ["紫炁", "水潦", "丙乙", "燥火", "奇羅", "土溽"]]
        ddict = [dict(zip(GONG_8, i)) for i in head]
        return multi_key_dict_get(dict(zip(stem_groups, ddict)), yg) or {}

    # ------------------------------------------------------------------
    # 雷霆月合炁 — Monthly Heqi
    # ------------------------------------------------------------------

    def luitingheqimonth(self) -> Dict[str, str]:
        """計算雷霆月合炁。

        據「起月例」：
        「太歲常將遁甲停，更將停處起元正。
        直須認取星辰位，飛入中宮次第行。」
        以月天干決定中宮起星。
        """
        mg = self.gangzhi()[1][0]
        stem_groups = [tuple(i) for i in re.findall("..", "甲己乙庚丙辛丁壬癸戊")]
        all_stars = re.findall(
            "..", "血刃太陽月孛金水台將天罡土溽奇羅燥火丙乙水潦紫炁"
        )
        head = [new_list(all_stars, i)[0:9] for i in ["天罡", "血刃", "燥火", "紫炁", "月孛"]]
        ddict = [dict(zip(GONG_9, i)) for i in head]
        return multi_key_dict_get(dict(zip(stem_groups, ddict)), mg) or {}

    def luitingmonth(self) -> Optional[str]:
        """計算雷霆月（當月所值曜氣星）。

        據「停年立成局」及「逐月釣星法」：
        以年干支決定起始星及地支位置，再按農曆月份取對應星辰。
        """
        ygz = self.gangzhi()[0]
        luiting_month_map = multi_key_dict_get({
            tuple(re.findall("..", "甲子庚午乙亥辛巳丙戌丁酉壬辰戊申癸丑己未")):
                dict(zip(_nlist(list(DIZHI), "亥"), _nlist(STAR_12, "月孛"))),
            tuple(re.findall("..", "己巳甲戌庚辰乙酉辛卯丙申壬寅丁未戊午癸亥")):
                dict(zip(_nlist(list(DIZHI), "寅"), _nlist(STAR_12, "紫炁"))),
            tuple(re.findall("..", "辛丑壬子")):
                dict(zip(_nlist(list(DIZHI), "卯"), _nlist(STAR_12, "水潦"))),
            tuple(re.findall("..", "戊辰癸酉己卯甲申庚寅乙未丙午丁巳")):
                dict(zip(_nlist(list(DIZHI), "辰"), _nlist(STAR_12, "丙乙"))),
            tuple(re.findall("..", "己丑庚子辛亥壬戌")):
                dict(zip(_nlist(list(DIZHI), "巳"), _nlist(STAR_12, "燥火"))),
            tuple(re.findall("..", "丁卯戊寅癸未甲午乙巳丙辰")):
                dict(zip(_nlist(list(DIZHI), "午"), _nlist(STAR_12, "奇羅"))),
            tuple(re.findall("..", "壬申丁丑戊子己亥庚戌辛酉")):
                dict(zip(_nlist(list(DIZHI), "未"), _nlist(STAR_12, "土溽"))),
            tuple(re.findall("..", "丙寅癸巳甲辰乙卯")):
                dict(zip(_nlist(list(DIZHI), "申"), _nlist(STAR_12, "天罡"))),
            tuple(re.findall("..", "乙丑辛未丙子壬午丁亥戊戌己酉庚申")):
                dict(zip(_nlist(list(DIZHI), "酉"), _nlist(STAR_12, "台將"))),
            tuple(re.findall("..", "癸卯甲寅")):
                dict(zip(_nlist(list(DIZHI), "戌"), _nlist(STAR_12, "金水"))),
        }, ygz)

        if not luiting_month_map:
            return None

        lunar_month_num = int(self.lunar_date_detail()["月"].replace("月", ""))
        return dict(zip(range(1, 13), list(luiting_month_map.values()))).get(lunar_month_num)

    # ------------------------------------------------------------------
    # 雷霆月局、日局九宮 — Monthly/Daily Nine Palace Layout
    # ------------------------------------------------------------------

    def luitingmonth_ninegong(self) -> Dict[str, str]:
        """計算雷霆月局九宮飛布。

        據「推霆星入中宮飛遁例」：
        月星入中宮順飛八方。
        """
        stars = _nlist(STAR_12, "水潦")
        palace_names = list("巽震坤坎離艮兌乾中")
        result: Dict[str, str] = {}
        for star in stars:
            layout = _nlist(STAR_12, star)[0:8]
            result.update(dict(zip(palace_names, layout)))
        return result

    def luitingday_ninegong(self) -> Dict[str, str]:
        """計算雷霆日局九宮飛布。

        據「起日例」：
        「丑日元來是刃星，到頭逆轉卻分明。
        常將本日依元位，飛入中宮卻順行。」
        """
        stars = _nlist(STAR_12, "丙乙")
        palace_names = list("巽震坤坎離艮兌乾中")
        result: Dict[str, str] = {}
        for star in stars:
            layout = _nlist(STAR_12, star)[0:8]
            result.update(dict(zip(palace_names, layout)))
        return result

    # ------------------------------------------------------------------
    # 雷霆日合炁順逆局 — Daily Heqi Clockwise/Anticlockwise
    # ------------------------------------------------------------------

    def luitingheqiday_clockwise(self) -> Optional[Dict[str, str]]:
        """計算雷霆日合炁值向順局。

        以日地支決定中宮起星，順飛九宮。
        """
        all_stars = re.findall(
            "..", "血刃太陽月孛金水台將天罡土溽奇羅燥火丙乙水潦紫炁"
        )
        dz = self.gangzhi()[2][1]
        star_heads = re.findall(
            "..", "太陽血刃紫炁水潦丙乙燥火奇羅土溽天罡台將金水月孛"
        )
        layouts = [new_list(all_stars, s)[0:9] for s in star_heads]
        mapping = dict(zip(DIZHI, [dict(zip(GONG_9, lay)) for lay in layouts]))
        return mapping.get(dz)

    def luitingheqiday_anticlockwise(self) -> Optional[Dict[str, str]]:
        """計算雷霆日合炁值向逆局。

        以日地支（逆排從丑起）決定中宮起星。
        """
        all_stars = re.findall(
            "..", "血刃太陽月孛金水台將天罡土溽奇羅燥火丙乙水潦紫炁"
        )
        dz = self.gangzhi()[2][1]
        star_heads = re.findall(
            "..", "太陽血刃紫炁水潦丙乙燥火奇羅土溽天罡台將金水月孛"
        )
        layouts = [new_list(all_stars, s)[0:9] for s in star_heads]
        dizhi_from_chou = new_list(list(DIZHI), "丑")
        mapping = dict(zip(dizhi_from_chou, [dict(zip(GONG_9, lay)) for lay in layouts]))
        return mapping.get(dz)

    # ------------------------------------------------------------------
    # 雷霆時合炁 — Hourly Heqi
    # ------------------------------------------------------------------

    def luitingheqihour(self) -> Dict[str, Any]:
        """計算雷霆時合炁值山向定局。

        據「起時例」：
        「求時一法少人知，甲己先從燥火推。乙庚太陽為定例，
        丙辛還向天罡期。丁壬月孛分明數，戊癸紫炁不相離。」
        """
        dg = self.gangzhi()[3][0]  # 時天干
        hg = self.gangzhi()[3][1]  # 時地支

        # 值（斗）盤
        dou = [
            re.findall("..", "太陽奇羅天罡丙乙燥火土溽天罡台將金水太陽台將台將"),
            re.findall("..", "水潦燥火紫炁金水水潦金水土溽水潦丙乙金水太陽天罡"),
            re.findall("..", "台將月孛太陽血刃紫炁丙乙血刃血刃土溽台將奇羅紫炁"),
            re.findall("..", "土溽紫炁月孛土溽天罡紫炁丙乙太陽血刃水潦丙乙燥火"),
            re.findall("..", "奇羅天罡燥火燥火月孛血刃金水奇羅月孛奇羅水潦月孛"),
        ]

        # 方向（線）盤
        xian = [
            re.findall("..", "燥火太陽天罡月孛紫炁燥火太陽天罡月孛紫炁燥火太陽"),
            re.findall("..", "天罡月孛紫炁水潦太陽天罡月孛紫炁燥火太陽天罡月孛"),
            re.findall("..", "紫炁燥火太陽天罡月孛紫炁燥火太陽天罡月孛紫炁燥火"),
            re.findall("..", "太陽天罡月孛紫炁紫炁太陽天罡月孛紫炁燥火太陽天罡"),
            re.findall("..", "月孛紫炁燥火太陽天罡月孛紫炁燥火太陽天罡月孛紫炁"),
        ]

        stem_groups = [tuple(i) for i in re.findall("..", "甲己乙庚丙辛丁壬癸戊")]
        directions = list("癸艮甲乙巽丙丁坤庚辛乾壬")

        bb = [dict(zip(directions, d)) for d in dou]
        cc = [dict(zip(list(DIZHI), x)) for x in xian]
        dd = [{stem_groups[i]: {"值": bb[i], "方向": cc[i]}} for i in range(5)]
        merged = {**dd[0], **dd[1], **dd[2], **dd[3], **dd[4]}

        lui = re.findall(
            "..", "太陽月孛金水台將天罡土溽奇羅燥火丙乙水潦紫炁血刃"
        )

        return {
            "日值時星": multi_key_dict_get(merged, dg),
            "時合炁山向": dict(zip(
                list(DIZHI),
                dict(zip(list(DIZHI), [new_list(lui, s) for s in lui])).get(hg, [])
            )),
        }

    def luitinghour(self) -> Optional[str]:
        """計算雷霆時（當時所值曜氣星）。

        據「起時例」：以日天干和時地支來決定當時所值的曜氣星。
        """
        dgz = self.gangzhi()[2]
        hgz = self.gangzhi()[3]
        stars_start = re.findall("..", "金水燥火血刃丙乙土溽")
        stem_pairs = re.findall("..", "甲己乙庚丙辛丁壬戊癸")

        c = [
            tuple(list("卯庚亥未")), tuple(list("坤乙")), tuple(list("巽辛")),
            tuple(list("子癸申辰")), tuple(list("午壬寅戌")), tuple(list("艮丙")),
            tuple(list("酉丁巳丑")), tuple(list("乾甲")), tuple(list("巽辛")),
        ]

        d: Dict[Any, Dict] = {}
        for g in range(len(stars_start)):
            layout = _nlist(STAR_12, stars_start[g])[0:8]
            d[tuple(stem_pairs[g])] = dict(zip(c, layout))

        inner = multi_key_dict_get(d, dgz[0])
        if inner:
            return multi_key_dict_get(inner, hgz[1])
        return None

    # ------------------------------------------------------------------
    # 雷霆箭 — Thunder Arrows
    # ------------------------------------------------------------------

    def year_arrow_round(self) -> str:
        """計算雷霆年箭。

        據《雷霆箭煞年月樞機》「雷霆箭法詩斷」：
        以年天干分五組，對應天干地支混合方位的箭星排列。
        """
        ylist = [tuple(list(i)) for i in re.findall("..", "甲己乙庚丙辛丁壬戊癸")]
        order = [
            re.findall("..", "風雲太陽雷母吉祥鬼火飛劍血刃火烈木神雷公旺相亡沒亡沒旺相雷公木神火烈血刃飛劍鬼火吉祥雷母太陽風雲"),
            re.findall("..", "旺相亡沒亡沒旺相雷公木神火烈血刃飛劍鬼火吉祥雷母太陽風雲風雲太陽雷母吉祥鬼火飛劍血刃火烈木神雷公"),
            re.findall("..", "飛劍鬼火吉祥雷母太陽風雲風雲太陽雷母吉祥鬼火飛劍血刃火烈木神雷公旺相亡沒亡沒旺相雷公木神火烈血刃"),
            re.findall("..", "亡沒旺相雷公木神火烈血刃飛劍鬼火吉祥雷母太陽風雲風雲太陽雷母吉祥鬼火飛劍血刃火烈木神雷公旺相亡沒"),
            re.findall("..", "血刃火烈木神雷公旺相亡沒亡沒旺相雷公木神火烈血刃飛劍鬼火吉祥雷母太陽風雲風雲太陽雷母吉祥鬼火飛劍"),
        ]
        maps = [dict(zip(TIANGAN_DIZHI_MIX, o)) for o in order]
        gz = self.gangzhi()[0]
        matched = multi_key_dict_get(dict(zip(ylist, maps)), gz[0])
        return matched.get(gz[1], "") if matched else ""

    def _month_day_hour_arrow_maps(self) -> Dict:
        """月/日/時箭的共用映射表（避免重複構建）。

        據「雷霆箭法」：
        年箭起法與月日時箭起法略有不同，月日時箭共用同一組規則。
        """
        ylist = [tuple(list(i)) for i in re.findall("..", "甲己乙庚丙辛丁壬戊癸")]
        order = [
            re.findall("..", "鬼火飛劍血刃火烈木神雷公旺相亡沒亡沒旺相雷公木神火烈血刃飛劍鬼火吉祥雷母太陽風雲風雲太陽雷母吉祥"),
            re.findall("..", "雷公木神火烈血刃飛劍鬼火吉祥雷母太陽風雲風雲太陽雷母吉祥鬼火飛劍血刃火烈木神雷公旺相亡沒亡沒旺相"),
            re.findall("..", "太陽風雲風雲太陽雷母吉祥鬼火飛劍血刃火烈木神雷公旺相亡沒亡沒旺相雷公木神火烈血刃飛劍鬼火吉祥雷母"),
            re.findall("..", "火烈血刃飛劍鬼火吉祥雷母太陽風雲風雲太陽雷母吉祥鬼火飛劍血刃火烈木神雷公旺相亡沒亡沒旺相雷公木神"),
            re.findall("..", "旺相亡沒亡沒旺相雷公木神火烈血刃飛劍鬼火吉祥雷母太陽風雲風雲太陽雷母吉祥鬼火飛劍血刃火烈木神雷公"),
        ]
        maps = [dict(zip(TIANGAN_DIZHI_MIX, o)) for o in order]
        return dict(zip(ylist, maps))

    def month_arrow(self) -> str:
        """計算雷霆月箭。"""
        gz = self.gangzhi()[1]
        matched = multi_key_dict_get(self._month_day_hour_arrow_maps(), gz[0])
        return matched.get(gz[1], "") if matched else ""

    def day_arrow(self) -> str:
        """計算雷霆日箭。"""
        gz = self.gangzhi()[2]
        matched = multi_key_dict_get(self._month_day_hour_arrow_maps(), gz[0])
        return matched.get(gz[1], "") if matched else ""

    def hour_arrow(self) -> str:
        """計算雷霆時箭。"""
        gz = self.gangzhi()[3]
        matched = multi_key_dict_get(self._month_day_hour_arrow_maps(), gz[0])
        return matched.get(gz[1], "") if matched else ""

    # ------------------------------------------------------------------
    # 金虎大煞 — Golden Tiger Great Sha
    # ------------------------------------------------------------------

    def _golden_tiger_location(self, dgz: str) -> Optional[str]:
        """推算金虎大煞方位。

        據《雷霆箭煞年月樞機》「金火大煞例」：
        「甲己龍飛鷄正啼，乙庚虎嘯喜羊肥，丙辛蛇犬同群戲，
        丁壬兔走向猴歸，戊癸馬居豬寄宿。」
        先於輪盤上輪日看是甚星，將日星入中宮飛看燥火到何方位，
        次看時辰遁去得金水與燥火同位方好，此名金火大煞。
        """
        return multi_key_dict_get({
            tuple(re.findall("..", "甲辰乙酉戊申壬寅")): "乾",
            tuple(re.findall("..", "甲寅乙亥丙申丁卯戊午己巳庚申壬子癸酉")): "兌",
            tuple(re.findall("..", "甲戌乙卯丁巳戊寅己未庚午辛卯壬申癸亥")): "震",
            tuple(re.findall("..", "甲申乙巳戊子辛巳壬午")): "巽",
            tuple(re.findall("..", "甲午乙未丙辰戊戌辛未壬辰")): "中",
            tuple(re.findall("..", "丙寅丁酉己亥庚寅辛亥癸卯")): "坎",
            tuple(re.findall("..", "乙丑丙戌丁丑己卯庚戌壬戌癸未")): "艮",
            tuple(re.findall("..", "甲子丁未戊辰己酉庚辰辛丑癸丑")): "坤",
            tuple(re.findall("..", "丙子丙午丁亥己丑庚子辛酉癸巳")): "離",
        }, dgz)

    # ------------------------------------------------------------------
    # 流火凶星 — Flowing Fire Inauspicious Star
    # ------------------------------------------------------------------

    def _liuhuo_location(self, dgz: str) -> Optional[str]:
        """推算流火凶星方位。

        據《雷霆箭煞年月樞機》「流火起例」（陽順陰逆）：
        「甲辛坤位丙壬乾，庚坎乙癸丁艮邊。戊巳都來蛇宮坐，
        一衝流火便驚天。」
        「雷霆流火號凶星，但把支干自內尋。順走九宮尋戊子，
        納音之火剋其金。」
        """
        return multi_key_dict_get({
            tuple(re.findall("..", "甲辰乙亥丁未戊申壬午")): "乾",
            tuple(re.findall("..", "甲寅乙丑丁巳戊午庚申壬辰")): "兌",
            tuple(re.findall("..", "甲戌乙巳丁丑戊申己亥庚辰辛巳壬申癸丑")): "震",
            tuple(re.findall("..", "甲申乙未丙寅丁亥戊午己酉庚午辛未癸亥")): "巽",
            tuple(re.findall("..", "甲午乙酉丁酉戊戌己未辛未壬申癸卯")): "中",
            tuple(re.findall("..", "丙申丁酉戊子己卯庚子辛丑壬戌癸巳")): "坎",
            tuple(re.findall("..", "乙丑丙辰戊辰庚戌辛酉壬寅癸酉")): "艮",
            tuple(re.findall("..", "甲子乙卯丙戌丁卯戊戌己丑庚戌辛卯")): "坤",
            tuple(re.findall("..", "丙午丁亥戊寅己巳庚子辛亥壬子癸未")): "離",
        }, dgz)

    # ------------------------------------------------------------------
    # 值符 — Value Talisman (Zhifu)
    # ------------------------------------------------------------------

    def _zhifu_location(self, dgz: str) -> Optional[str]:
        """推算值符方位。

        據《雷霆箭煞年月樞機》「直符例」（乃震）：
        「直符事應疾如飛。天門甲子起星移順走九宮。
        尋本日吉凶雷雨自然知。」
        甲子起乾、甲戌起兌、甲申起艮、甲午起離、甲寅起坤。
        """
        return multi_key_dict_get({
            tuple(re.findall("..", "丁卯")): "乾",
            tuple(re.findall("..", "甲戌乙酉乙未丙申丙午丙辰丁丑戊寅戊子戊戌己酉己未庚午庚申")): "兌",
            tuple(re.findall("..", "戊午庚子辛酉壬午癸卯")): "震",
            tuple(re.findall("..", "丁未丁巳戊辰己卯己丑己亥庚戌辛未辛巳壬辰癸丑")): "巽",
            tuple(re.findall("..", "")): "中",
            tuple(re.findall("..", "甲辰丙戌丁亥庚辰辛丑壬戌癸未")): "坎",
            tuple(re.findall("..", "甲申乙巳丙寅丁酉戊申壬寅")): "艮",
            tuple(re.findall("..", "甲子甲寅乙丑乙亥己巳庚寅辛亥壬申癸巳癸亥")): "坤",
            tuple(re.findall("..", "甲午乙卯丙子辛卯壬子癸酉")): "離",
        }, dgz)

    # ------------------------------------------------------------------
    # 傳音 — Sound Transmission (Chuanyin)
    # ------------------------------------------------------------------

    def _chuanyin_location(self, dgz: str) -> Optional[str]:
        """推算傳音方位。

        據《雷霆箭煞年月樞機》「傳音例」（乃雷神也）：
        「傳音一訣報君知道：甲從寅子細推，走進九宮尋艮發吉凶，
        逐一莫猜疑。」
        但將本日五虎推遁，假如庚辰日乙庚戊為所，
        戊寅艮、己卯在兌、庚辰乾，此日在乾。
        """
        return multi_key_dict_get({
            tuple(re.findall("..", "甲子戊午己酉庚子辛卯壬午癸酉")): "乾",
            tuple(re.findall("..", "甲戌乙丑己未庚戌辛丑壬辰癸未")): "兌",
            tuple(re.findall("..", "乙卯丙午丁酉戊子己卯庚午")): "震",
            tuple(re.findall("..", "丙辰丁未戊戌己丑庚辰辛未")): "巽",
            tuple(re.findall("..", "丁巳戊申己亥庚寅辛巳壬申")): "中",
            tuple(re.findall("..", "甲辰乙未丙戌丁丑戊辰壬戌癸丑")): "坎",
            tuple(re.findall("..", "甲申乙亥丙寅庚申辛亥壬寅癸巳")): "艮",
            tuple(re.findall("..", "甲寅乙巳丙申丁亥戊寅己巳癸亥")): "坤",
            tuple(re.findall("..", "甲午乙酉丙子丁卯辛酉壬子癸卯")): "離",
        }, dgz)

    # ------------------------------------------------------------------
    # 帝星 — Emperor Star
    # ------------------------------------------------------------------

    def _daily_emperor_star(self, dgz: str) -> Optional[str]:
        """推算日帝星方位。

        據《雷霆箭煞年月樞機》「帝星起例」：
        「甲己順行居震上，乙庚逆向艮方求。丙辛坤位仍逆行，
        逆丁壬順起向中流。戊癸順從艮上起，帝星坐處善緣由。」
        """
        return multi_key_dict_get({
            tuple(re.findall("..", "甲申甲午乙亥乙酉丙申丙午戊子戊戌庚申壬午壬辰癸卯")): "乾",
            tuple(re.findall("..", "甲辰乙丑丙戌戊申庚戌")): "兌",
            tuple(re.findall("..", "甲子乙巳丁未戊辰己酉辛巳癸丑")): "震",
            tuple(re.findall("..", "甲戌乙未丙辰丁巳戊寅己未辛未壬申癸亥")): "巽",
            tuple(re.findall("..", "")): "中",
            tuple(re.findall("..", "丁亥己丑庚辰辛丑")): "坎",
            tuple(re.findall("..", "甲寅丙子丁卯戊午己巳庚子辛酉壬寅壬子癸酉")): "艮",
            tuple(re.findall("..", "乙卯丁酉己亥庚午辛卯")): "坤",
            tuple(re.findall("..", "丙寅丁丑己卯庚寅辛亥壬戌癸未癸巳")): "離",
        }, dgz)

    def _monthly_emperor_star(self) -> Optional[str]:
        """推算月帝星。

        以年天干和農曆月份推算月帝星所在地支。
        """
        ygz = self.gangzhi()[0]
        king_star = {
            tuple(list("乙庚")): dict(zip(range(1, 13), list("子丑午卯辰巳午亥子酉戌亥"))),
            tuple(list("丁壬")): dict(zip(range(1, 13), list("子丑寅未申巳午未子丑戌亥"))),
            tuple(list("戊癸")): dict(zip(range(1, 13), list("子巳午卯辰巳戌亥申酉戌卯"))),
            tuple(list("甲己")): dict(zip(range(1, 13), list("辰丑寅卯申酉午未申丑寅亥"))),
            tuple(list("丙辛")): dict(zip(range(1, 13), list("辰巳寅卯辰酉戌未申酉寅卯"))),
        }
        try:
            month_num = int(self.lunar_date_detail()["月"].replace("月", ""))
            return multi_key_dict_get(king_star, ygz[0]).get(month_num)
        except (IndexError, AttributeError):
            try:
                return multi_key_dict_get(king_star, ygz[1]).get(
                    int(self.lunar_date_detail()["月"].replace("月", ""))
                )
            except (IndexError, AttributeError):
                return None

    # ------------------------------------------------------------------
    # 飛定星宿主事法 — Flying Star Mansion Method
    # ------------------------------------------------------------------

    def _hour_star_mansion(self) -> Tuple[str, Dict[str, str]]:
        """推算飛定星宿（十干起時例）。

        據《雷霆箭煞年月樞機》「飛定星宿主事法」：
        「甲日子一天遁女　乙日子六地遁氐 …」
        「十干起時例（陽順陰逆）」

        Returns:
            (遁法名稱, 時辰→星宿映射) 的元組。
        """
        dgz = self.gangzhi()[2]
        hgz = self.gangzhi()[3]

        hour_star_data = {
            "甲": ("天遁", {"子": "女一", "丑": "虛二", "寅": "危三", "卯": "室四",
                          "辰": "壁五", "巳": "奎六", "午": "婁七", "未": "胃八",
                          "申": "昴九", "酉": "畢十", "戌": "觜一", "亥": "參二"}),
            "乙": ("地遁", {"子": "氐六", "丑": "亢五", "寅": "角四", "卯": "軫三",
                          "辰": "翼二", "巳": "張一", "午": "星十", "未": "柳九",
                          "申": "鬼八", "酉": "井七", "戌": "參六", "亥": "觜五"}),
            "丙": ("地遁", {"子": "斗二", "丑": "箕一", "寅": "尾十", "卯": "心九",
                          "辰": "房八", "巳": "氐七", "午": "亢六", "未": "角五",
                          "申": "軫四", "酉": "翼三", "戌": "張二", "亥": "星一"}),
            "丁": ("天遁", {"子": "婁七", "丑": "胃八", "寅": "昴九", "卯": "畢十",
                          "辰": "觜一", "巳": "參二", "午": "井三", "未": "鬼四",
                          "申": "柳五", "酉": "星六", "戌": "張七", "亥": "翼八"}),
            "戊": ("天遁", {"子": "危三", "丑": "室四", "寅": "壁五", "卯": "奎六",
                          "辰": "婁七", "巳": "胃八", "午": "昴九", "未": "畢十",
                          "申": "觜一", "酉": "參二", "戌": "井三", "亥": "鬼四"}),
            "己": ("地遁", {"子": "胃八", "丑": "婁七", "寅": "奎六", "卯": "壁五",
                          "辰": "辰四", "巳": "危三", "午": "虛二", "未": "女一",
                          "申": "牛十", "酉": "斗九", "戌": "箕八", "亥": "尾十"}),
            "庚": ("地遁", {"子": "尾四", "丑": "心三", "寅": "房二", "卯": "氐一",
                          "辰": "亢十", "巳": "角九", "午": "軫八", "未": "翼七",
                          "申": "張六", "酉": "星五", "戌": "柳四", "亥": "鬼三"}),
            "辛": ("天遁", {"子": "奎九", "丑": "婁十", "寅": "胃一", "卯": "昴二",
                          "辰": "畢三", "巳": "觜四", "午": "參五", "未": "井六",
                          "申": "鬼七", "酉": "柳八", "戌": "星九", "亥": "張十"}),
            "壬": ("天遁", {"子": "壁五", "丑": "奎六", "寅": "婁七", "卯": "胃八",
                          "辰": "昴九", "巳": "畢十", "午": "觜一", "未": "參二",
                          "申": "井三", "酉": "鬼四", "戌": "柳五", "亥": "星六"}),
            "癸": ("地遁", {"子": "軫十", "丑": "翼九", "寅": "張八", "卯": "星七",
                          "辰": "柳六", "巳": "鬼五", "午": "井四", "未": "參三",
                          "申": "觜二", "酉": "畢一", "戌": "昴十", "亥": "胃九"}),
        }

        data = hour_star_data.get(dgz[0])
        if data is None:
            return ("", {})
        dun_name, star_map = data
        return (dun_name, star_map)

    # ------------------------------------------------------------------
    # 日干支納音（五行遁法） — Day Stem-Branch Nayin
    # ------------------------------------------------------------------

    def _day_nayin(self, dgz: str) -> Optional[str]:
        """推算日干支納音遁法。

        據「五星遁數法」：
        金遁十三數、水遁七數、土遁十五數、火遁九數、木遁十一數。
        """
        return multi_key_dict_get({
            tuple(re.findall("..", "甲子乙丑壬申癸酉庚辰辛巳甲午乙未壬寅癸卯庚戌辛亥")): "金遁",
            tuple(re.findall("..", "丙寅丁卯甲戌乙亥戊子己丑丙申丁酉甲辰乙巳戊午己未")): "火遁",
            tuple(re.findall("..", "戊辰己巳壬午癸未庚寅辛卯戊戌己亥壬子癸丑庚申辛酉")): "木遁",
            tuple(re.findall("..", "庚午辛未戊寅己卯丙戌丁亥庚子辛丑戊申己酉丙辰丁巳")): "土遁",
            tuple(re.findall("..", "丙子丁丑甲申乙酉壬辰癸巳甲寅乙卯丙午丁未壬戌癸亥")): "水遁",
        }, dgz)

    # ------------------------------------------------------------------
    # 天氣預測 — Weather Prediction
    # ------------------------------------------------------------------

    def _weather_from_star_element(self, star_element: str) -> Optional[str]:
        """根據星禽和月五行推算天氣。

        據「星禽應事」及二十八宿與五行配合法。
        """
        return multi_key_dict_get({
            tuple(re.findall("..", "角木心金心木心水尾木箕金斗土牛水女水虛水危水室金壁金奎水奎火婁金婁水婁火胃土胃金胃水胃火畢土畢木參金參木參水井火")): "風",
            tuple(re.findall("..", "角金亢木氐金氐水氐土房金房木房土尾金牛火女土危金危火危木")): "陰",
            tuple(re.findall("..", "角火亢水氐火氐木箕土斗木牛金室火壁火婁土畢金畢水觜金觜水觜土井金井水井土鬼金鬼水柳金柳水")): "雨",
            tuple(re.findall("..", "角土角水亢金亢火亢土房水房火心火心土尾水尾火尾土箕水箕火箕木斗水斗金斗火牛木牛土女金女火女木虛金虛木虛火虛土危土婁木胃木昴金昴木昴水昴火昴土星金星木星水星火星土張金張木張水張火張土畢火參火參土井木鬼土鬼火翼火翼土")): "晴",
            tuple(re.findall("..", "室水室土室木壁木壁土壁水奎土觜火觜木柳火柳土柳木")): "日昏",
            tuple(re.findall("..", "奎金奎木翼金翼水翼木")): "風霧",
            tuple(re.findall("..", "軫金軫木軫水軫火軫土")): "雨則晴，晴則雨",
        }, star_element)

    def _season_weather(self, dun_star: str) -> Optional[str]:
        """根據季節和遁星推算四季禽星應事。

        據《雷霆箭煞年月樞機》「春禽」「夏禽」「秋禽」「冬禽」。
        """
        season = self.find_season()
        season_data = {
            "春": dict(zip(
                [tuple(list(i)) for i in "室壁,奎,婁胃,昴畢,觜參井,鬼,柳星,張翼,軫角,亢,氐房心尾,箕斗,牛女,虛危".split(",")],
                "多風雨,天大晴,雨風陰凍冷,登高天轉晴,遇大風起,星沉日月昏,雲霧起四山皎潔天還晴,風大發,夜雨日開晴,大風沙石起,雨風聲,朦朧天欲雨,微微濕雨形當到,大風起直至三更雲".split(","),
            )),
            "夏": dict(zip(
                [tuple(list(i)) for i in "虛危室壁,奎婁胃昴,畢,觜參井,鬼柳,星張翼軫,角亢,氐房,心尾,箕斗牛女".split(",")],
                "半晴,雨霖霖,帶黃色,雨微聲,降大雨,更開晴,太陽現,雨風鳴,大降雨,復天晴".split(","),
            )),
            "秋": dict(zip(
                [tuple(list(i)) for i in "虛危室壁,奎婁胃昴,畢觜參井,鬼柳,星張翼軫,角亢,氐房心尾,箕斗牛女".split(",")],
                "大天晴,雨零零,天陰雨無雨有雲雲霧形,溫溫天色黃，客逃大路盡堪行,原無雨,雨奔程,微微雨,倚山行".split(","),
            )),
            "冬": dict(zip(
                [tuple(list(i)) for i in "虛危室壁,奎,婁胃昴畢,觜參井,鬼柳星張,氐,翼軫,角亢,房心尾,箕斗牛女".split(",")],
                "天陰陰有雲無雨雨如金,微見大風起,半天晴,有雲雨或解為雲倚山行,天氣朗,還教有雨形,天陰凍,雨無傾,零零雨,空雨聲".split(","),
            )),
        }
        data = season_data.get(season)
        if data:
            return multi_key_dict_get(data, dun_star)
        return None

    # ------------------------------------------------------------------
    # 雷霆日方合炁 — Daily Direction Heqi
    # ------------------------------------------------------------------

    def _day_direction_heqi(self, day_stem: str) -> str:
        """推算雷霆日方合炁。

        據「起年例（又名日夏太陽方合炁）」：
        「甲庚血刃丙壬金丁癸，還從月孛尋六己。
        台將紫炁戊乙辛，偏向日邊臨收入中宮飛出。」
        """
        return multi_key_dict_get({
            tuple(list("甲庚")): "血刃",
            tuple(list("丙壬")): "金水",
            tuple(list("丁癸")): "月孛",
            "己": "台將",
            "戊": "紫炁",
            tuple(list("乙辛")): "太陽",
        }, day_stem) or ""

    # ------------------------------------------------------------------
    # 排盤主函數 — Main Chart Generation
    # ------------------------------------------------------------------

    def pan(self) -> Dict[str, Any]:
        """生成完整的雷霆曜氣排盤結果。

        Returns:
            包含所有排盤數據的字典，鍵包括：
            - 日期時間、干支、農曆、節氣
            - 雷霆年/月/日/時合炁
            - 昇玄值向、金虎大煞、流火凶星
            - 值符、傳音、帝星
            - 雷霆箭、飛星遁宿、天氣
            - 雷公、風伯、雨伯
        """
        gz = self.gangzhi()
        ygz, dgz, hgz = gz[0], gz[2], gz[3]

        # 飛定星宿
        dun_name, star_map = self._hour_star_mansion()
        hstar = star_map.get(hgz[1], "")

        # 日干支納音
        leyin = self._day_nayin(dgz) or ""

        # 遁數計算
        su_list = list(SU_28)
        fiveelementdun = {"金遁": 13, "水遁": 7, "土遁": 15, "火遁": 9, "木遁": 11}
        cnum_map = dict(zip(list(CNUM), range(1, 11)))

        dun_star = ""
        chinyy = ""
        chinw = ""
        weather = ""

        if hstar and len(hstar) >= 2:
            dun_num = cnum_map.get(hstar[1])
            if dun_num:
                su_cycle = _nlist(su_list, hstar[0])
                dun_second = dict(zip(range(1, 29), su_cycle)).get(dun_num)
                if dun_second and leyin:
                    su_cycle2 = _nlist(su_list, dun_second)[1:]
                    dun_star = dict(zip(range(1, 29), su_cycle2)).get(
                        fiveelementdun.get(leyin, 0), ""
                    )

            # 星禽應事
            if dun_star:
                yinyang_map = dict(zip(
                    list("婁畢井星軫參房亢牛壁危胃女奎斗虛張翼昴箕角心氐鬼尾柳室觜"),
                    list("陽" * 14 + "陰" * 14),
                ))
                chinyy = yinyang_map.get(dun_star, "")

                chinw = multi_key_dict_get(dict(zip(
                    [tuple(i) for i in "婁畢斗虛,井星張翼,軫參昴箕,房亢角心,牛壁氐鬼,危胃尾柳,女奎室觜".split(",")],
                    "應雨,應電,應風,應雷,應雲,應罡,應遁".split(","),
                )), dun_star) or ""

            # 天氣
            month_elem = self.month_element()
            if hstar and month_elem:
                weather = self._weather_from_star_element(hstar[0] + month_elem[0]) or ""

        # 四季禽星
        schin = self._season_weather(dun_star) if dun_star else ""

        # 組裝結果
        result: Dict[str, Any] = {
            "日期時間": f"{self.year}年{self.month}月{self.day}日{self.hour}時{self.minute}分",
            "干支": "".join(gz[i] + "年月日時分"[i] for i in range(5)),
            "農曆": self.lunar_date(),
            "節氣": self.find_jieqi(),
            "月五行": self.month_element(),
            "日干支": dgz,
            "日陰陽": self.yingyang(dgz[0]),
            "日干支納音": leyin,
            "雷霆年月日時箭": [
                self.year_arrow_round(),
                self.month_arrow(),
                self.day_arrow(),
                self.hour_arrow(),
            ],
            "雷霆年昇玄值向": self.luitingyear(),
            "雷霆年合炁到向": self.luitingheqiyear_mountain(),
            "雷霆年合炁": self.luitingheqiyear(),
            "雷霆月局": self.luitingmonth_ninegong(),
            "雷霆月合炁": self.luitingheqimonth(),
            "雷霆月": self.luitingmonth(),
            "雷霆日方合炁": self._day_direction_heqi(dgz[0]),
            "雷霆日局": self.luitingday_ninegong(),
            "雷霆時": self.luitinghour(),
            "雷霆時合炁值山向定局": self.luitingheqihour(),
            "金虎大煞": self._golden_tiger_location(dgz),
            "流火凶星": self._liuhuo_location(dgz),
            "值符": self._zhifu_location(dgz),
            "傳音": self._chuanyin_location(dgz),
            "月帝星": self._monthly_emperor_star(),
            "日帝星": self._daily_emperor_star(dgz),
            "時星遁": dun_name,
            "時星": hstar[0] if hstar else "",
            "遁數": hstar[1] if len(hstar) >= 2 else "",
            "天氣": weather,
            "星禽應事": f"{chinyy}日{chinw}" if chinyy and chinw else "",
            "四季禽星應事": schin or "",
            "遁星": dun_star,
        }

        # 合併雷公、風伯、雨伯
        result.update(self.find_three_uncle())

        return result


if __name__ == "__main__":
    print(Luiting(1984, 5, 5, 21, 0).pan())
