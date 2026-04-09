# -*- coding: utf-8 -*-
"""
天文曆法輔助模組 — Astronomical Calendar Helpers

提供節氣計算、六十甲子生成、列表循環排列等基礎工具函數。
基於 PyEphem 天文計算庫，用於推算太陽黃經以確定節氣。

Created on Sat Jan 18 11:32:50 2020
@author: hooki
"""

import datetime
import math
import re
from typing import Any, Dict, List, Optional, Sequence, TypeVar

import ephem

T = TypeVar("T")

# ---------------------------------------------------------------------------
# 基礎常量 — Fundamental Constants
# ---------------------------------------------------------------------------

TIANGAN: str = "甲乙丙丁戊己庚辛壬癸"
DIZHI: str = "子丑寅卯辰巳午未申酉戌亥"

JIEQI: List[str] = re.findall(
    "..",
    "春分清明穀雨立夏小滿芒種夏至小暑大暑立秋處暑白露秋分寒露霜降立冬小雪大雪冬至小寒大寒立春雨水驚蟄",
)

# ---------------------------------------------------------------------------
# 通用工具函數 — Utility Functions
# ---------------------------------------------------------------------------


def jiazi() -> List[str]:
    """生成六十甲子列表。

    Returns:
        60 個天干地支組合，從「甲子」到「癸亥」。
    """
    return [
        TIANGAN[x % len(TIANGAN)] + DIZHI[x % len(DIZHI)]
        for x in range(60)
    ]


def new_list(olist: Sequence[T], start: T) -> List[T]:
    """從 *olist* 中以 *start* 為起點，順序循環生成等長列表。

    Args:
        olist: 原始序列。
        start: 起始元素（必須存在於 *olist* 中）。

    Returns:
        以 *start* 開頭的循環排列列表。
    """
    idx = olist.index(start)
    length = len(olist)
    return [olist[(idx + i) % length] for i in range(length)]


def new_list_r(olist: Sequence[T], start: T) -> List[T]:
    """從 *olist* 中以 *start* 為起點，逆序循環生成等長列表。

    Args:
        olist: 原始序列。
        start: 起始元素（必須存在於 *olist* 中）。

    Returns:
        以 *start* 開頭的逆序循環排列列表。
    """
    idx = olist.index(start)
    length = len(olist)
    return [olist[(idx - i) % length] for i in range(length)]


def multi_key_dict_get(d: Dict, k: Any) -> Any:
    """在鍵為 tuple 的字典中查找包含 *k* 的鍵並返回對應值。

    Args:
        d: 鍵為 tuple 的字典。
        k: 要查找的元素。

    Returns:
        匹配的值，若無匹配則返回 ``None``。
    """
    for keys, v in d.items():
        if k in keys:
            return v
    return None


# ---------------------------------------------------------------------------
# 天文計算 — Astronomical Calculations
# ---------------------------------------------------------------------------


def ecliptic_lon(jd_utc: float) -> float:
    """計算給定儒略日的太陽黃經（弧度）。"""
    s = ephem.Sun(jd_utc)
    equ = ephem.Equatorial(s.ra, s.dec, epoch=jd_utc)
    e = ephem.Ecliptic(equ)
    return float(e.lon)


def _solar_term_index(jd: float) -> int:
    """返回給定儒略日對應的節氣索引（0–23）。"""
    lon = ecliptic_lon(jd)
    return int(lon * 180.0 / math.pi / 15)


def _iterate_to_next_term(jd: float) -> float:
    """以二分法迭代找到下一個節氣交界的儒略日。"""
    s1 = _solar_term_index(jd)
    s0 = s1
    dt = 1.0
    while True:
        jd += dt
        s = _solar_term_index(jd)
        if s0 != s:
            s0 = s
            dt = -dt / 2
        if abs(dt) < 0.0000001 and s != s1:
            break
    return jd


def jq(year: int, month: int, day: int, hour: int) -> str:
    """計算指定日期時間所處的節氣名稱。

    Args:
        year, month, day, hour: 公曆日期時間。

    Returns:
        節氣名稱（如「春分」「清明」等）。
    """
    date_str = f"{year}/{month:02d}/{day:02d} {hour:02d}:00:00.00"
    jd = ephem.Date(date_str)
    lon = ecliptic_lon(jd)
    n = int(lon * 180.0 / math.pi / 15) + 1
    if n >= 24:
        n -= 24
    jd = _iterate_to_next_term(jd)
    d1 = ephem.Date(jd + 1 / 3)
    if d1 - jd > 0:
        return JIEQI[n - 1]
    else:
        return JIEQI[n]


def find_jq_date(
    year: int, month: int, day: int, hour: int, target_jq: str
) -> datetime.datetime:
    """查找從指定日期起，目標節氣的精確日期時間。

    Args:
        year, month, day, hour: 起始公曆日期時間。
        target_jq: 目標節氣名稱。

    Returns:
        目標節氣的 ``datetime.datetime``。
    """
    date_str = f"{year}/{month:02d}/{day:02d} {hour:02d}:00:00.00"
    jd = ephem.Date(date_str)
    lon = ecliptic_lon(jd)
    n = int(lon * 180.0 / math.pi / 15) + 1
    dzlist: List[Dict[str, datetime.datetime]] = []
    for _ in range(24):
        if n >= 24:
            n -= 24
        jd = _iterate_to_next_term(jd)
        d = ephem.Date(jd + 1 / 3).tuple()
        entry = {JIEQI[n]: datetime.datetime(d[0], d[1], d[2], d[3], d[4], int(d[5]))}
        n += 1
        dzlist.append(entry)
    names = [list(item.keys())[0] for item in dzlist]
    idx = names.index(target_jq)
    return list(dzlist[idx].values())[0]
