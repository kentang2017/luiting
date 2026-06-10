# -*- coding: utf-8 -*-
"""
堅雷霆曜氣單元測試 — Luiting Unit Tests

測試核心計算引擎的正確性，包括：
- 干支計算
- 雷霆箭
- 金虎大煞、流火凶星、值符、傳音
- 帝星
- 合炁計算
- 天氣預測

測試案例基於已知的歷史日期及其預期結果。
"""

import pytest
from luiting import Luiting
from rules import STAR_12  # 原文範例測試需直接引用十二星列表驗證 traceability


class TestLuitingBasics:
    """基礎計算功能測試。"""

    def test_gangzhi_1984(self):
        """測試 1984年5月5日21時 的干支計算。"""
        lt = Luiting(1984, 5, 5, 21, 0)
        gz = lt.gangzhi()
        assert gz[0] == "甲子"  # 年干支
        assert gz[2] == "己亥"  # 日干支
        assert len(gz) == 5

    def test_gangzhi_2024(self):
        """測試 2024年3月15日10時 的干支計算。"""
        lt = Luiting(2024, 3, 15, 10, 30)
        gz = lt.gangzhi()
        assert len(gz) == 5
        assert len(gz[0]) == 2  # 年干支應為兩個字符

    def test_yingyang(self):
        """測試日干陰陽判斷。"""
        lt = Luiting(1984, 5, 5, 21, 0)
        assert lt.yingyang("甲") == "陽日"
        assert lt.yingyang("乙") == "陰日"
        assert lt.yingyang("丙") == "陽日"
        assert lt.yingyang("丁") == "陰日"
        assert lt.yingyang("己") == "陰日"

    def test_lunar_date(self):
        """測試農曆日期。"""
        lt = Luiting(1984, 5, 5, 21, 0)
        lunar = lt.lunar_date()
        assert "1984" in lunar
        assert "月" in lunar
        assert "日" in lunar

    def test_season(self):
        """測試季節判斷。"""
        lt = Luiting(1984, 5, 5, 21, 0)
        season = lt.find_season()
        assert season in ["春", "夏", "秋", "冬"]


class TestLuitingPan:
    """排盤結果測試。"""

    @pytest.fixture
    def pan_1984(self):
        """1984年5月5日21時的排盤結果。"""
        return Luiting(1984, 5, 5, 21, 0).pan()

    @pytest.fixture
    def pan_2024(self):
        """2024年3月15日10時的排盤結果。"""
        return Luiting(2024, 3, 15, 10, 30).pan()

    def test_pan_has_all_keys(self, pan_1984):
        """測試排盤結果包含所有必要的鍵。"""
        required_keys = [
            "日期時間", "干支", "農曆", "節氣", "月五行",
            "日干支", "日陰陽", "日干支納音",
            "雷霆年月日時箭", "雷霆年昇玄值向",
            "雷霆年合炁到向", "雷霆年合炁",
            "雷霆月局", "雷霆月合炁", "雷霆月",
            "雷霆日方合炁", "雷霆日局",
            "雷霆時", "雷霆時合炁值山向定局",
            "金虎大煞", "流火凶星", "值符", "傳音",
            "月帝星", "日帝星",
            "太乙真數", "雷分八節", "雷分八節詳細",
            "時星遁", "時星", "遁數", "遁星",
            "天氣", "星禽應事", "四季禽星應事",
            "雷公", "風伯", "雨伯",
        ]
        for key in required_keys:
            assert key in pan_1984, f"排盤結果缺少鍵：{key}"

    def test_golden_tiger_1984(self, pan_1984):
        """測試 1984-05-05 己亥日的金虎大煞方位。"""
        assert pan_1984["金虎大煞"] == "坎"

    def test_liuhuo_1984(self, pan_1984):
        """測試 1984-05-05 己亥日的流火凶星方位。"""
        assert pan_1984["流火凶星"] == "震"

    def test_zhifu_1984(self, pan_1984):
        """測試 1984-05-05 己亥日的值符方位。"""
        assert pan_1984["值符"] == "巽"

    def test_chuanyin_1984(self, pan_1984):
        """測試 1984-05-05 己亥日的傳音方位。"""
        assert pan_1984["傳音"] == "中"

    def test_emperor_star_1984(self, pan_1984):
        """測試 1984-05-05 的日帝星方位。"""
        assert pan_1984["日帝星"] == "坤"

    def test_arrows_1984(self, pan_1984):
        """測試 1984-05-05 的雷霆箭。"""
        arrows = pan_1984["雷霆年月日時箭"]
        assert len(arrows) == 4
        assert arrows[0] == "風雲"  # 年箭
        assert arrows[1] == "雷公"  # 月箭
        assert arrows[2] == "雷母"  # 日箭
        assert arrows[3] == "亡沒"  # 時箭

    def test_weather_1984(self, pan_1984):
        """測試 1984-05-05 的天氣預測。"""
        assert pan_1984["天氣"] == "晴"

    def test_day_heqi_1984(self, pan_1984):
        """測試 1984-05-05 己日的日方合炁。"""
        assert pan_1984["雷霆日方合炁"] == "台將"

    def test_nayin_1984(self, pan_1984):
        """測試 1984-05-05 己亥日的納音。"""
        assert pan_1984["日干支納音"] == "木遁"

    def test_dun_star_1984(self, pan_1984):
        """測試 1984-05-05 的遁星。"""
        assert pan_1984["遁星"] == "張"

    def test_three_uncle_1984(self, pan_1984):
        """測試 1984-05-05 的雷公風伯雨伯。"""
        assert pan_1984["雷公"] == "子"
        assert pan_1984["風伯"] == "寅"
        assert pan_1984["雨伯"] == "辰"

    def test_jieqi_1984(self, pan_1984):
        """測試 1984-05-05 的節氣。"""
        assert pan_1984["節氣"] == "立夏"


class TestLuitingHeqi:
    """合炁計算測試。"""

    def test_year_heqi_1984(self):
        """測試甲子年的年合炁分佈。"""
        lt = Luiting(1984, 5, 5, 21, 0)
        heqi = lt.luitingheqiyear()
        assert isinstance(heqi, dict)
        assert len(heqi) > 0

    def test_month_heqi_1984(self):
        """測試月合炁分佈。"""
        lt = Luiting(1984, 5, 5, 21, 0)
        heqi = lt.luitingheqimonth()
        assert isinstance(heqi, dict)
        assert "中" in heqi

    def test_day_clockwise_1984(self):
        """測試日合炁順局。"""
        lt = Luiting(1984, 5, 5, 21, 0)
        cw = lt.luitingheqiday_clockwise()
        assert isinstance(cw, dict)
        assert "中" in cw

    def test_day_anticlockwise_1984(self):
        """測試日合炁逆局。"""
        lt = Luiting(1984, 5, 5, 21, 0)
        acw = lt.luitingheqiday_anticlockwise()
        assert isinstance(acw, dict)


class TestLuitingConsistency:
    """跨日期一致性測試。"""

    def test_multiple_dates_no_crash(self):
        """測試多個日期都能正常計算不崩潰。"""
        dates = [
            (2000, 1, 1, 0, 0),
            (2024, 3, 15, 10, 30),
            (2026, 4, 9, 8, 16),
            (1990, 6, 15, 12, 0),
            (2050, 12, 31, 23, 59),
        ]
        for year, month, day, hour, minute in dates:
            pan = Luiting(year, month, day, hour, minute).pan()
            assert "日期時間" in pan
            assert "雷霆年月日時箭" in pan
            assert len(pan["雷霆年月日時箭"]) == 4

    def test_gangzhi_caching(self):
        """測試干支計算的緩存機制。"""
        lt = Luiting(1984, 5, 5, 21, 0)
        gz1 = lt.gangzhi()
        gz2 = lt.gangzhi()
        assert gz1 is gz2  # 同一個物件（緩存生效）


class TestConfig:
    """config.py 輔助函數測試。"""

    def test_jiazi_length(self):
        """測試六十甲子生成。"""
        from config import jiazi
        jz = jiazi()
        assert len(jz) == 60
        assert jz[0] == "甲子"
        assert jz[-1] == "癸亥"

    def test_new_list(self):
        """測試循環列表生成。"""
        from config import new_list
        result = new_list(list("ABCD"), "C")
        assert result == ["C", "D", "A", "B"]

    def test_jq(self):
        """測試節氣計算。"""
        from config import jq
        result = jq(1984, 5, 5, 21)
        assert result == "立夏"


# ===========================================================================
# 原文範例測試 — 必須與按《雷霆箭煞年月樞機》歌訣/起例手算結果完全一致
# ===========================================================================

class TestOriginalVerbatim:
    """原文逐條驗證測試。

    所有案例均可手算：
    - 依「雷霆合炁停年歌」+「且如甲子旬，以甲子從亥上逆數」
    - 依「起年例」「昇玄上局年起例」
    - 依「起月例」「起日例」「起時例」
    - 飛遁表格直接對照 HOUR_FLYING_MANSION
    程式結果必須 = 手算結果。
    """

    def test_heqi_stop_甲子年(self):
        """案例1: 甲子年（1984）停處手算。

        原文「雷霆合炁停年歌」：甲子尋豬 → 基本停亥。
        「且如甲子旬，以甲子從亥上逆數，遇太歲是也。」
        甲子年 offset=0 → 從亥逆0步仍為亥。
        """
        lt = Luiting(1984, 5, 5, 21, 0)
        stop = lt.heqi_stop_branch()
        assert stop == "亥", "甲子年停處應為亥（甲子尋豬 + 逆數0）"

    def test_shengxuan_upper_甲(self):
        """案例2: 甲/己 昇玄上局年起例。

        原文：「甲己順羊逆巽宮」
        羊=未，逆巽。
        """
        lt = Luiting(1984, 5, 5, 21, 0)  # 年甲
        sx = lt.shengxuan_upper_ju()
        assert sx["順"] == "未"
        assert sx["逆"] == "巽"
        assert "起雷公" in sx.get("注", "") or sx.get("注") == "起雷公"

    def test_heqi_year_center_起年例(self):
        """案例3: 起年例中宮起星。

        原文「起年例」：甲庚血刃。
        1984甲子年 → 血刃入中宮。
        """
        lt = Luiting(1984, 5, 5, 21, 0)
        center = lt.heqi_year_center_star()
        assert center == "血刃"

    def test_heqi_month_from_stop_起月例(self):
        """案例4: 起月例（停處起元正 + 逆行）。

        以1984年5月（農曆四月？實際依 sxtwl 得月）為例。
        只要 stop + get_heqi_month_from_stop 能產出 STAR_12 中的一星即通過基本 traceability。
        更嚴格案例可手數：停亥，正月=某星，逆行 N 宮得月星。
        """
        lt = Luiting(1984, 5, 5, 21, 0)
        mstar = lt.heqi_month_center_star()
        assert mstar in STAR_12  # 必須是原文十二星之一

    def test_hour_flying_mansion_verbatim(self):
        """案例5: 十干起時例飛遁星宿表格 100% 對照（手算可查表）。

        原文「十干起時例（陽順陰逆）」：
        甲日子女一　丑虛二　寅危三　卯室四　辰壁五　巳奎六　午婁七　未胃八　申昴九　酉畢十　戌觜一　亥參二
        取一具體：甲日申時 → 昴九
        """
        from rules import HOUR_FLYING_MANSION
        # 找一個甲日子
        # 例如 1984-5-5 為己亥日（非甲），我們直接驗證表格內容而非日期
        assert HOUR_FLYING_MANSION["甲"]["子"] == "女一"
        assert HOUR_FLYING_MANSION["甲"]["申"] == "昴九"
        assert HOUR_FLYING_MANSION["壬"]["子"] == "壁五"
        assert HOUR_FLYING_MANSION["癸"]["子"] == "軫十"
        # 乙例子
        assert HOUR_FLYING_MANSION["乙"]["子"] == "氐六"

    def test_liujia_shun_起旬例(self):
        """起旬例直接對照。

        原文：「甲子奇羅甲戌罡...」
        """
        from rules import LIUJIA_SHUN_STAR
        assert LIUJIA_SHUN_STAR["甲子"] == "奇羅"
        assert LIUJIA_SHUN_STAR["甲戌"] == "天罡"
        assert LIUJIA_SHUN_STAR["甲申"] == "金水"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
