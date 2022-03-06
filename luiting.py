# -*- coding: utf-8 -*-
"""
Created on Sat Aug 22 18:30:06 2020

@author: ken tang
"""
import re, sxtwl, itertools
from config import *


class Luiting():
    def __init__(self, year, month, day, hour, minute):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.cnum = "一二三四五六七八九十"
        self.tiangan = '甲乙丙丁戊己庚辛壬癸'
        self.dizhi = '子丑寅卯辰巳午未申酉戌亥'
        self.su = '角亢氐房心尾箕斗牛女虛危室壁奎婁胃昴畢觜參井鬼柳星張翼軫'
        self.ymc = [u"十一", u"十二", u"正", u"二", u"三", u"四", u"五", u"六", u"七", u"八", u"九", u"十" ]
        self.rmc = [u"初一", u"初二", u"初三", u"初四", u"初五", u"初六", u"初七", u"初八", u"初九", u"初十",
                 u"十一", u"十二", u"十三", u"十四", u"十五", u"十六", u"十七", u"十八", u"十九",
                  u"二十", u"廿一", u"廿二", u"廿三", u"廿四", u"廿五", u"廿六", u"廿七", u"廿八", u"廿九", u"三十", u"卅一"]
        self.starlist = re.findall("..","太陽血刃紫炁水潦丙乙燥火奇羅土溽天罡台將金水月孛")
        self.chinese_months = [i+"月" for i in list("正二三四五六七八九十")+["十一","十二"]]
        self.tiangangdizimix = list("子癸丑艮寅甲卯乙辰巽巳丙午丁未坤申庚酉辛戌乾亥壬")
        self.arrow = re.findall("..","風雲太陽雷母吉祥鬼火飛劍血刃火烈木神雷公旺相亡沒")
        
    def multi_key_dict_get(self, d, k):
        for keys, v in d.items():
            if k in keys:
                return v
        return None
    
    #找節氣
    def find_jieqi(self):
        jieqi_list = twentyfourjieqi(self.year)
        s_date = list(jieqi_list.keys())
        date = datetime.strptime(str(self.year)+"-"+str(self.month)+"-"+str(self.day), '%Y-%m-%d').date()
        closest = sorted(s_date, key=lambda d: abs( date  - d))[0]
        test = {True:jieqi_list.get(s_date[s_date.index(closest) - 1]), False:jieqi_list.get(closest)}
        return test.get(closest>date)
    
    def find_season(self):
        jq = re.findall('..','立春雨水驚蟄春分清明穀雨立夏小滿芒種夏至小暑大暑立秋處暑白露秋分寒露霜降立冬小雪大雪冬至小寒大寒')
        season = list("春春春春春春夏夏夏夏夏夏秋秋秋秋秋秋冬冬冬冬冬冬")
        return dict(zip(jq, season)).get(self.find_jieqi())
    
    def yingyang(self, dg): 
        yy = {tuple(list(self.tiangan)[0::2]):"陽日", tuple(list(self.tiangan)[1::2]):"陰日"}
        return self.multi_key_dict_get(yy, dg)

    def nlist(self, newlist ,o):
        zhihead_code = newlist.index(o)
        res1 = []
        for i in range(len(newlist)):
            res1.append(newlist[zhihead_code % len(newlist)])
            zhihead_code = zhihead_code + 1
        return res1

    def repeat_list(self, n, thelist):
        return [repetition for i in thelist for repetition in itertools.repeat(i,n) ]
    
    def jiazi(self):
        jiazi = [self.tiangan[x % len(self.tiangan)] + self.dizhi[x % len(self.dizhi)] for x in range(60)]
        return jiazi

    def find_shun(self, gangzhi):
        liujiashun_dict = {tuple(self.jiazi()[0:10]):"甲子", tuple(self.jiazi()[10:20]):"甲戌", tuple(self.jiazi()[20:30]):"甲申", tuple(self.jiazi()[30:40]):"甲午", tuple(self.jiazi()[40:50]):"甲辰", tuple(self.jiazi()[50:60]):"甲寅"}
        return self.multi_key_dict_get(liujiashun_dict, gangzhi)
    
    def minutes_jiazi_d(self):
        t = []
        for h in range(0,24):
            for m in range(0,60):
                b = str(h)+":"+str(m)
                t.append(b)
        minutelist = dict(zip(t, itertools.cycle(self.repeat_list(2, self.jiazi()))))
        return minutelist

    def lunar_date(self):
        day = sxtwl.fromSolar(self.year, self.month, self.day)
        s = "%d年%s%d月%d日" % (day.getLunarYear(), 
        '閏' if day.isLunarLeap() else '', day.getLunarMonth(), day.getLunarDay())
        return s

    def lunar_date_d(self):
        day = sxtwl.fromSolar(self.year, self.month, self.day)
        return {"月": str(day.getLunarMonth())+"月", "日":str(day.getLunarDay())}
    
    def month_element(self):
        MonthFiveElements = {tuple(list("248")):"水動", tuple(list("369")):"木動", tuple(list("157")):"水土", tuple("10,11,12".split(",")):"金動"}
        return self.multi_key_dict_get(MonthFiveElements, self.lunar_date_d().get("月").replace("月", ""))
    
    def gangzhi(self):
        cdate = sxtwl.fromSolar(self.year, self.month, self.day)
        Gan = self.tiangan
        Zhi = self.dizhi
        yTG = Gan[cdate.getYearGZ().tg] + Zhi[cdate.getYearGZ().dz]
        mTG = Gan[cdate.getMonthGZ().tg] + Zhi[cdate.getMonthGZ().dz]
        dTG  = Gan[cdate.getDayGZ().tg] + Zhi[cdate.getDayGZ().dz]
        hTG = Gan[cdate.getHourGZ(self.hour).tg] + Zhi[cdate.getHourGZ(self.hour).dz]
        gangzhi_minute = self.minutes_jiazi_d().get(str(self.hour)+":"+str(self.minute))
        return [yTG, mTG, dTG, hTG, gangzhi_minute]
    
    def find_three_uncle(self):
        dshun = self.find_shun(self.gangzhi()[2])
        shun = re.findall("..","甲子甲寅甲辰甲午甲申甲戌")
        ThunderStorm = {"雷公":dict(zip(shun,list("午申戌子寅辰"))), "風伯":dict(zip(shun,list("寅子寅寅午申"))), "雨伯":dict(zip(shun,list("戌辰午辰戌子")))}
        return {"雷公": ThunderStorm.get("雷公").get(dshun), "風伯": ThunderStorm.get("風伯").get(dshun), "雨伯": ThunderStorm.get("雨伯").get(dshun)}
    
    def luitingyear(self):
        yg = self.gangzhi()[0][0]
        a = re.findall("..","血刃太陽月孛金水台將天罡溽土奇羅燥火")
        dlist = [tuple(i) for i in re.findall("..","甲己乙庚丙辛丁壬戊癸")]
        b = [list("兌艮離坎坤震巽中乾"), list("坤震巽中乾兌艮離坎"), list("震巽中乾兌艮離坎坤"), list("震巽中乾兌艮離坎坤"), list("離坎坤震巽中乾兌艮")]
        c = [dict(zip(a, i)) for i in b ]
        return self.multi_key_dict_get(dict(zip(dlist, c)), yg)
    
    
    def luitingmonth(self):
        ygz = self.gangzhi()[0]
        luiting_month = self.multi_key_dict_get({tuple(re.findall("..","甲子庚午乙亥辛巳丙戌丁酉壬辰戊申癸丑己未")): dict(zip(self.nlist(self.dizhi, "亥"),self.nlist(self.starlist, "月孛"))),
        tuple(re.findall("..","己巳甲戌庚辰乙酉辛卯丙申壬寅丁未戊午癸亥")): dict(zip(self.nlist(self.dizhi,"寅"), self.nlist(self.starlist, "紫炁"))),
        tuple(re.findall("..","辛丑壬子")): dict(zip(self.nlist(self.dizhi,"卯"), self.nlist(self.starlist, "水潦"))),
        tuple(re.findall("..","戊辰癸酉己卯甲申庚寅乙未丙午丁巳")): dict(zip(self.nlist(self.dizhi,"辰"), self.nlist(self.starlist, "丙乙"))),
        tuple(re.findall("..","己丑庚子辛亥壬戌")):dict(zip(self.nlist(self.dizhi, "巳"), self.nlist(self.starlist, "燥火"))),
        tuple(re.findall("..","丁卯戊寅癸未申午乙巳丙辰")):dict(zip(self.nlist(self.dizhi, "午"), self.nlist(self.starlist, "奇羅"))),
        tuple(re.findall("..","壬申丁丑戊子己亥庚戌辛酉")): dict(zip(self.nlist(self.dizhi, "未"), self.nlist(self.starlist, "土溽"))),
        tuple(re.findall("..","丙寅癸巳甲辰乙卯")):dict(zip(self.nlist(self.dizhi, "申"), self.nlist(self.starlist, "天罡"))) ,
        tuple(re.findall("..","乙丑辛未丙子壬午丁亥戊戌己酉庚申")):dict(zip(self.nlist(self.dizhi,  "酉"), self.nlist(self.starlist, "台將"))),
        tuple(re.findall("..","癸卯甲寅")): dict(zip(self.nlist(self.dizhi,  "戌"), self.nlist(self.starlist, "金水")))}, ygz)
        cnum_dict = dict(zip(range(1,13), list("正二三四五六七八九十")+["十一", "十二"]))
        lmonth = dict(zip(range(1,13),list(luiting_month.values()))).get(int(self.lunar_date_d().get("月").replace("月", "")))
        return lmonth
    
    def luitingday_ninegong(self):
        a = self.nlist(self.starlist, "丙乙")
        b = [self.nlist(self.starlist, i)[0:8] for i in a]
        c = [tuple(list("巽辛")), tuple(list("震庚亥未")),  tuple(list("坤乙")),  tuple(list("坎癸申辰")), tuple(list("離壬寅戌")), tuple(list("艮丙")),  tuple(list("兌丁己丑")), tuple(list("乾甲")), tuple(list("中"))]
        e = list("巽震坤坎離艮兌乾中")
        d = {}
        for i in b:
            flist = dict(zip(e, i))
            d.update(flist)
        return d
    
    def luitingmonth_ninegong(self):
        a = self.nlist(self.starlist, "水潦")
        b = [self.nlist(self.starlist, i)[0:8] for i in a]
        c = [tuple(list("巽辛")), tuple(list("震庚亥未")),  tuple(list("坤乙")),  tuple(list("坎癸申辰")), tuple(list("離壬寅戌")), tuple(list("艮丙")),  tuple(list("兌丁己丑")), tuple(list("乾甲")), tuple(list("中"))]
        e = list("巽震坤坎離艮兌乾中")
        d = {}
        for i in b:
            flist = dict(zip(e, i))
            d.update(flist)
        return d

    def luitinghour(self):
        dgz = self.gangzhi()[2]
        hgz = self.gangzhi()[3]
        a = re.findall("..","金水燥火血刃丙乙土溽")
        dlist = re.findall("..","甲己乙庚丙辛丁壬戊癸") 
        b = [self.nlist(self.starlist, i)[0:8] for i in a]
        c = [tuple(list("卯庚亥未")), tuple(list("坤乙")),  tuple(list("巽辛")),  tuple(list("子癸申辰")), tuple(list("午壬寅戌")), tuple(list("艮丙")),  tuple(list("酉丁巳丑")), tuple(list("乾甲")), tuple(list("巽辛"))]
        d = {}
        for g in range(0, len(b)):
            alist = {tuple(dlist[g]): dict(zip(c,b[g]))}
            d.update(alist)
        return self.multi_key_dict_get(self.multi_key_dict_get(d, dgz[0]), hgz[1])
           
    def year_arrow_round(self):
        ylist = [tuple(list(i)) for i in re.findall("..","甲己乙庚丙辛丁壬戊癸")]
        order = [re.findall("..","風雲太陽雷母吉祥鬼火飛劍血刃火烈木神雷公旺相亡沒亡沒旺相雷公木神火烈血刃飛劍鬼火吉祥雷母太陽風雲"), 
                re.findall("..","旺相亡沒亡沒旺相雷公木神火烈血刃飛劍鬼火吉祥雷母太陽風雲風雲太陽雷母吉祥鬼火飛劍血刃火烈木神雷公"),
                re.findall("..","飛劍鬼火吉祥雷母太陽風雲風雲太陽雷母吉祥鬼火飛劍血刃火烈木神雷公旺相亡沒亡沒旺相雷公木神火烈血刃"),
                re.findall("..","亡沒旺相雷公木神火烈血刃飛劍鬼火吉祥雷母太陽風雲風雲太陽雷母吉祥鬼火飛劍血刃火烈木神雷公旺相亡沒"),
                re.findall("..","血刃火烈木神雷公旺相亡沒亡沒旺相雷公木神火烈血刃飛劍鬼火吉祥雷母太陽風雲風雲太陽雷母吉祥鬼火飛劍")]
        a = []
        for i in order:
            b = dict(zip(self.tiangangdizimix, i))
            a.append(b)
        return self.multi_key_dict_get(dict(zip(ylist, a)), self.gangzhi()[0][0]).get(self.gangzhi()[0][1])
    
    def month_day_hour_arrow_round(self):
        ylist = [tuple(list(i)) for i in re.findall("..","甲己乙庚丙辛丁壬戊癸")]
        order = [re.findall("..","鬼火飛劍血刃火烈木神雷公旺相亡沒亡沒旺相雷公木神火烈血刃飛劍鬼火吉祥雷母太陽風雲風雲太陽雷母吉祥"),
                re.findall("..","雷公木神火烈血刃飛劍鬼火吉祥雷母太陽風雲風雲太陽雷母吉祥鬼火飛劍血刃火烈木神雷公旺相亡沒亡沒旺相"),
                re.findall("..","太陽風雲風雲太陽雷母吉祥鬼火飛劍血刃火烈木神雷公旺相亡沒亡沒旺相雷公木神火烈血刃飛劍鬼火吉祥雷母"),
                re.findall("..","火烈血刃飛劍鬼火吉祥雷母太陽風雲風雲太陽雷母吉祥鬼火飛劍血刃火烈木神雷公旺相亡沒亡沒旺相雷公木神"),
                re.findall("..","旺相亡沒亡沒旺相雷公木神火烈血刃飛劍鬼火吉祥雷母太陽風雲風雲太陽雷母吉祥鬼火飛劍血刃火烈木神雷公")]
        a = []
        for i in order:
            b = dict(zip(self.tiangangdizimix, i))
            a.append(b)
        return dict(zip(ylist, a))
    
    def month_arrow(self):
        return self.multi_key_dict_get(self.month_day_hour_arrow_round(), self.gangzhi()[1][0]).get(self.gangzhi()[1][1])
    
    def day_arrow(self):
        return self.multi_key_dict_get(self.month_day_hour_arrow_round(), self.gangzhi()[2][0]).get(self.gangzhi()[2][1])
    
    def hour_arrow(self):
        return self.multi_key_dict_get(self.month_day_hour_arrow_round(), self.gangzhi()[3][0]).get(self.gangzhi()[3][1])
    
    
    def result(self):
        chinesemonth = list("正二三四五六七八九十")+["十一","十二"]
        #MonthHourLightning = {tuple(re.findall("..","正丑二寅三卯四巳五午六未七申八酉九戌十亥")):"雷動"}
        ygz = self.gangzhi()[0]
        dgz = self.gangzhi()[2]
        hgz = self.gangzhi()[3]
        
        #金虎大煞定例
        GoldenTigerLocation = self.multi_key_dict_get({tuple(re.findall("..","甲辰乙酉戊申壬寅")):"乾",
        tuple(re.findall("..","甲寅乙亥丙申丁卯戊午己巳庚申壬子癸酉")):"兌",
        tuple(re.findall("..","甲戌乙卯丁巳戊寅己未庚午辛卯壬申癸亥")):"震",
        tuple(re.findall("..","甲申乙巳戊子辛巳壬午")):"巽",
        tuple(re.findall("..","甲午乙未丙辰戊戌辛未壬辰")):"中",
        tuple(re.findall("..","丙寅丁酉己亥庚寅辛亥癸卯")):"坎",
        tuple(re.findall("..","乙丑丙戌丁丑己卯庚戌壬戌癸未")):"艮",
        tuple(re.findall("..","甲子丁未戊辰己酉庚辰辛丑癸丑")):"坤",
        tuple(re.findall("..","丙子丙午丁亥己丑庚子辛酉癸巳")):"離"}, dgz)
        
        #流火凶星定例
        LiuFireBadStarLocation = self.multi_key_dict_get({tuple(re.findall("..","甲辰乙亥丁未戊申壬午")):"乾",
        tuple(re.findall("..","甲寅乙丑丁巳戊午庚申壬辰")):"兌",
        tuple(re.findall("..","甲戌乙巳丁丑戊申己亥庚辰辛巳壬申癸丑")):"震",
        tuple(re.findall("..","甲申乙未丙寅丁亥戊午己酉庚午辛未癸亥")):"巽",
        tuple(re.findall("..","甲午乙酉丁酉戊戌己未辛未壬申癸卯")):"中",
        tuple(re.findall("..","丙申丁酉戊子己卯庚子辛丑壬戌癸巳")):"坎",
        tuple(re.findall("..","乙丑丙辰戊辰庚戌辛酉壬寅癸酉")):"艮",
        tuple(re.findall("..","甲子乙卯丙戌丁卯戊戌己丑庚戌辛卯")):"坤",
        tuple(re.findall("..","丙午丁亥戊寅己巳庚子辛亥壬子癸未")):"離"}, dgz)
        
        #值符定例
        ZhiFuLocation = self.multi_key_dict_get({tuple(re.findall("..","丁卯")):"乾",
        tuple(re.findall("..","甲戌乙酉乙未丙申丙午丙辰丁丑戊寅戊子戊戌己酉己未庚午庚申")):"兌",
        tuple(re.findall("..","戊午庚子辛酉壬午癸卯")):"震",
        tuple(re.findall("..","丁未丁巳戊辰己卯己丑己亥庚戌辛未辛巳壬辰癸丑")):"巽",
        tuple(re.findall("..","")):"中",
        tuple(re.findall("..","甲辰丙戌丁亥庚辰辛丑壬戌癸未")):"坎",
        tuple(re.findall("..","甲申乙巳丙寅丁酉戊申壬寅")):"艮",
        tuple(re.findall("..","甲子甲寅乙丑乙亥己巳庚寅辛亥壬申癸巳癸亥")):"坤",
        tuple(re.findall("..","甲午乙卯丙子辛卯壬子癸酉")):"離"}, dgz)
        
        #傳音定例
        PassVoiceLocation = self.multi_key_dict_get({tuple(re.findall("..","甲子戊午己酉庚子辛卯壬午癸酉")):"乾",
        tuple(re.findall("..","甲戌乙丑己未庚戌辛丑壬辰癸未")):"兌",
        tuple(re.findall("..","乙卯丙午丁酉戊子己卯庚午")):"震",
        tuple(re.findall("..","丙辰丁未戊戌己丑庚辰辛未")):"巽",
        tuple(re.findall("..","丁巳戊申己亥庚寅辛巳壬申")):"中",
        tuple(re.findall("..","甲辰乙未丙戌丁丑戊辰壬戌癸丑")):"坎",
        tuple(re.findall("..","甲申乙亥丙寅庚申辛亥壬寅癸巳")):"艮",
        tuple(re.findall("..","甲寅乙巳丙申丁亥戊寅己巳癸亥")):"坤",
        tuple(re.findall("..","甲午乙酉丙子丁卯辛酉壬子癸卯")):"離"}, dgz)
        
        #帝星定例
        KingStarLocation = self.multi_key_dict_get({tuple(re.findall("..","甲申甲午乙亥乙酉丙申丙午戊子戊戌庚申壬午壬辰癸卯")):"乾",
        tuple(re.findall("..","甲辰乙丑丙戌戊申庚戌")):"兌",
        tuple(re.findall("..","甲子乙巳丁未戊辰己酉辛巳癸丑")):"震",
        tuple(re.findall("..","甲戌乙未丙辰丁巳戊寅己未辛未壬申癸亥")):"巽",
        tuple(re.findall("..","")):"中",
        tuple(re.findall("..","丁亥己丑庚辰辛丑")):"坎",
        tuple(re.findall("..","甲寅丙子丁卯戊午己巳庚子辛酉壬寅壬子癸酉")):"艮",
        tuple(re.findall("..","乙卯丁酉己亥庚午辛卯")):"坤",
        tuple(re.findall("..","丙寅丁丑己卯庚寅辛亥壬戌癸未癸巳")):"離"}, dgz)
    
        #月帝星
        KingStar = {tuple(list("乙庚")):dict(zip(range(1,13),list("子丑午卯辰巳午亥子酉戌亥"))),
        tuple(list("丁壬")):dict(zip(range(1,13),list("子丑寅未申巳午未子丑戌亥"))),
        tuple(list("戊癸")):dict(zip(range(1,13),list("子巳午卯辰巳戌亥申酉戌卯"))),
        tuple(list("甲己")):dict(zip(range(1,13),list("辰丑寅卯申酉午未申丑寅亥"))),
        tuple(list("丙辛")):dict(zip(range(1,13),list("辰巳寅卯辰酉戌未申酉寅卯")))}
        try:
            b = self.multi_key_dict_get(KingStar, ygz[0]).get(int(self.lunar_date_d().get("月").replace("月", "")))
        except IndexError:
            b = self.multi_key_dict_get(KingStar, ygz[1]).get(int(self.lunar_date_d().get("月").replace("月", "")))
        
        #飛定星宿主事法 十干起時例
        hourstar = {"甲":{"天遁":{"子":"女一", "丑":"虛二", "寅":"危三", "卯":"室四" , "辰":"壁五", "巳":"奎六", "午":"婁七", "未":"胃八", "申":"昴九", "酉":"畢十", "戌":"觜一", "亥":"參二"}}, 
         "乙":{"地遁":{"子":"氐六", "丑":"亢五", "寅":"角四", "卯":"軫三" , "辰":"翼二", "巳":"張一", "午":"午十", "未":"柳九", "申":"鬼八", "酉":"井七", "戌":"參六", "亥":"觜五"}},
         "丙":{"地遁":{"子":"斗二", "丑":"箕一", "寅":"尾十", "卯":"心九" , "辰":"房八", "巳":"氐七", "午":"亢六", "未":"角五", "申":"軫四", "酉":"翼三", "戌":"張二", "亥":"星一"}},
         "丁":{"天遁":{"子":"婁七", "丑":"胃八", "寅":"昴九", "卯":"畢十" , "辰":"觜一", "巳":"參二", "午":"井三", "未":"鬼四", "申":"柳五", "酉":"星六", "戌":"張七", "亥":"翼八"}},
         "戊":{"天遁":{"子":"危三", "丑":"室四", "寅":"壁五", "卯":"奎六" , "辰":"婁七", "巳":"胃八", "午":"昴九", "未":"畢十", "申":"觜一", "酉":"參二", "戌":"井三", "亥":"鬼四"}},
         "己":{"地遁":{"子":"胃八", "丑":"婁七", "寅":"奎六", "卯":"壁五" , "辰":"辰四", "巳":"危三", "午":"虛二", "未":"女一", "申":"牛十", "酉":"斗九", "戌":"箕八", "亥":"尾十"}},
         "庚":{"地遁":{"子":"尾四", "丑":"心三", "寅":"房二", "卯":"氐一" , "辰":"亢十", "巳":"角九", "午":"軫八", "未":"翼七", "申":"張六", "酉":"星五", "戌":"柳四", "亥":"鬼三"}},
         "辛":{"天遁":{"子":"奎九", "丑":"婁十", "寅":"胃一", "卯":"昴二" , "辰":"畢三", "巳":"觜四", "午":"參五", "未":"井六", "申":"鬼七", "酉":"柳八", "戌":"星九", "亥":"張十"}},
         "壬":{"天遁":{"子":"壁五", "丑":"奎六", "寅":"婁七", "卯":"胃八" , "辰":"昴九", "巳":"畢十", "午":"觜一", "未":"參二", "申":"井三", "酉":"鬼四", "戌":"柳五", "亥":"星六"}},
         "癸":{"地遁":{"子":"軫十", "丑":"翼九", "寅":"張八", "卯":"星七" , "辰":"柳六", "巳":"鬼五", "午":"井四", "未":"參三", "申":"觜二", "酉":"畢一", "戌":"昴十", "亥":"胃九"}}
        }.get(dgz[0])
        
     
        
        
        StarElementsWeather = {tuple(re.findall("..","角木心金心木心水尾木箕金斗土牛水女水虛水危水室金壁金奎水奎火婁金婁水婁火胃土胃金胃水胃火畢土畢木參金參木參水井火")):"風",
        tuple(re.findall("..","角金亢木氐金氐水氐土房金房木房土尾金牛火女土危金危火危木")): "陰", 
        tuple(re.findall("..","角火亢水氐火氐木箕土斗木牛金室火壁火婁土畢金畢水觜金觜水觜土井金井水井土鬼金鬼水柳金柳水")):"雨", 
        tuple(re.findall("..","角土角水亢金亢火亢土房水房火心火心土尾水尾火尾土箕水箕火箕木斗水斗金斗火牛木牛土女金女火女木虛金虛木虛火虛土危土婁木胃木昴金昴木昴水昴火昴土星金星木星水星火星土張金張木張水張火張土畢火參火參土井木鬼土鬼火翼火翼土")):"晴",
        tuple(re.findall("..","室水室土室木壁木壁土壁水奎土觜火觜木柳火柳土柳木")):"日昏",
        tuple(re.findall("..","奎金奎木翼金翼水翼木")):"風霧",
        tuple(re.findall("..","軫金軫木軫水軫火軫土")):"雨則晴，晴則雨"}
        hstar = list(hourstar.values())[0].get(hgz[1])
        weather = self.multi_key_dict_get(StarElementsWeather, hstar[0] + self.month_element()[0])
        leyin = self.multi_key_dict_get({tuple(re.findall("..","甲子乙丑壬申癸酉庚辰辛巳甲午乙未壬寅癸卯庚戌辛亥")):"金遁",
        tuple(re.findall("..","丙寅丁卯甲戌乙亥戊子己丑丙申丁酉甲辰乙巳戊午己未")):"火遁",
        tuple(re.findall("..","戊辰己巳壬午癸未庚寅辛卯戊戌己亥壬子癸丑庚申辛酉")):"木遁",
        tuple(re.findall("..","庚午辛未戊寅己卯丙戌丁亥庚子辛丑戊申己酉丙辰丁巳")):"土遁",
        tuple(re.findall("..","丙子丁丑甲申乙酉壬辰癸巳甲寅乙卯丙午丁未壬戌癸亥")):"水遁"}, dgz)
        fiveelementdun = {"金遁":13, "水遁":7, "土遁":15, "火遁":9, "木遁":11}
        dun_num = dict(zip(list(self.cnum), range(1,11))).get(hstar[1]) 
        dun_second = dict(zip(range(1,29), self.nlist(self.su, hstar[0]))).get(dun_num)
        dun_star = dict(zip(range(1,29), self.nlist(self.su, dun_second)[1:])).get(fiveelementdun.get(leyin))
        
        #星禽應事
        chinyy = dict(zip(list("婁畢井星軫參房亢牛壁危胃女奎斗虛張危昴箕角心氐鬼尾柳室觜"), list("陽"*14+"陰"*14))).get(dun_star)
        chinw = self.multi_key_dict_get(dict(zip( [tuple(i) for i in "婁畢斗虛,井星張危,軫參昴箕,房亢角心,牛壁氐鬼,危胃尾柳,女奎室觜".split(",")], "應雨,應電,應風,應雷,應雲,應罡,應遁".split(","))), dun_star)
        
        #四季禽
        season_chin = {"春":dict(zip([tuple(list(i)) for i in "室壁,奎,婁胃,昴畢,觜參井,鬼,柳星,張翼,軫角,亢,氐房心尾,箕斗,牛女,虛危".split(",")],  "多風雨,天大晴,雨風陰凍冷,登高天轉晴,遇大風起,星沉日月昏,雲霧起四山皎潔天還晴,風大發,夜雨日開晴,大風沙石起,雨風聲,朦朧天欲雨,微微濕雨形當到,大風起直至三更雲".split(","))),
        "夏":dict(zip([tuple(list(i)) for i in "虛危室壁,奎婁胃昴,畢,觜參井,鬼柳,星張翼軫,角亢,氐房,心尾,箕斗牛女".split(",")], "半晴,雨霖霖,帶黃色,雨微聲,降大雨,更開晴,太陽現,雨風鳴,大降雨, 復天晴".split(","))),
        "秋":dict(zip([tuple(list(i)) for i in "虛危室壁,奎婁胃昴,畢觜參井,鬼柳,星張翼軫,角亢,氐房心尾,箕斗牛女".split(",")], 
        "大天晴,雨零零,天陰雨無雨有雲雲霧形,溫溫天色黃，客逃大路盡堪行,原無雨,雨奔程,微微雨,倚山行".split(","))),
        "冬":dict(zip([tuple(list(i)) for i in "虛危室壁,奎,婁胃昴畢,觜參井,鬼柳星張,氐,翼軫,角亢,房心尾,箕斗牛女".split(",")], "天陰陰有雲無雨雨如金,微見大風起,半天晴,有雲雨或解為雲倚山行,天氣朗,還教有雨形,天陰凍,雨無傾,零零雨,空雨聲".split(",")))}
                 
        schin = self.multi_key_dict_get(season_chin.get(self.find_season()),dun_star)
        
        luiday = self.multi_key_dict_get({tuple(list("甲庚")):"血刃",
        tuple(list("丙壬")):"金水",
        tuple(list("丁癸")):"月孛",
        "己":"台將",
        "戊":"紫炁",
        tuple(list("乙辛")):"太陽"}, dgz[0])
    
        return {**{"日期時間":str(self.year)+"年"+str(self.month)+"月"+str(self.day)+"日"+str(self.hour)+"時"+str(self.minute)+"分", "干支":''.join([self.gangzhi()[i] + list("年月日時分")[i] for i in range(5)]), "節氣": self.find_jieqi(), "雷霆年月日時箭":[self.year_arrow_round(), self.month_arrow(), self.day_arrow(), self.hour_arrow()], "雷霆月":self.luitingmonth(), "雷霆日方合炁":luiday, "雷霆時":self.luitinghour(),"雷霆年局":self.luitingyear(),"雷霆月局":self.luitingmonth_ninegong() ,"雷霆日局":self.luitingday_ninegong(),"月五行":self.month_element(), "農曆":self.lunar_date(), "日干支": dgz, "日陰陽":self.yingyang(dgz[0]) ,"日干支納音":leyin, "金虎大煞": GoldenTigerLocation, "流火凶星":LiuFireBadStarLocation, "值符":ZhiFuLocation, "傳音":PassVoiceLocation, "月帝星": b, "日帝星":KingStarLocation, "時星遁":list(hourstar.keys())[0], "時星":hstar[0], "遁數":hstar[1], "天氣":weather,"星禽應事":chinyy+"日"+chinw, "四季禽星應事":schin  ,"遁星":dun_star}, **self.find_three_uncle()} 
    
if __name__ == "__main__":
    print(Luiting(2022,3,6,2,0).result())






