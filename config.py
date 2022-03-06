# -*- coding: utf-8 -*-
"""
Created on Sat Jan 18 11:32:50 2020

@author: hooki
"""

from datetime import datetime
import re


START_YEAR = 1901
stc= '小寒大寒立春雨水驚蟄春分清明穀雨立夏小滿芒種夏至小暑大暑立秋處暑白露秋分寒露霜降立冬小雪大雪冬至'
solarTermsNameList=re.findall('..',stc)

# 1901-2100年二十节气最小公差数序列 向量压缩法
encryptionVectorList=[4, 19, 3, 18, 4, 19, 4, 19, 4, 20, 4, 20, 6, 22, 6, 22, 6, 22, 7, 22, 6, 21, 6, 21]
# 1901-2100年二十节气数据 每个元素的存储格式如下：
# 1-24
# 节气所在天（减去节气最小公约数）
# 1901-2100年香港天文台公布二十四节气按年存储16进制，1个16进制为4个2进制
solarTermsData=[
    0x6aaaa6aa9a5a, 0xaaaaaabaaa6a, 0xaaabbabbafaa, 0x5aa665a65aab, 0x6aaaa6aa9a5a, # 1901 ~ 1905
    0xaaaaaaaaaa6a, 0xaaabbabbafaa, 0x5aa665a65aab, 0x6aaaa6aa9a5a, 0xaaaaaaaaaa6a,
    0xaaabbabbafaa, 0x5aa665a65aab, 0x6aaaa6aa9a56, 0xaaaaaaaa9a5a, 0xaaabaabaaeaa,
    0x569665a65aaa, 0x5aa6a6a69a56, 0x6aaaaaaa9a5a, 0xaaabaabaaeaa, 0x569665a65aaa,
    0x5aa6a6a65a56, 0x6aaaaaaa9a5a, 0xaaabaabaaa6a, 0x569665a65aaa, 0x5aa6a6a65a56,
    0x6aaaa6aa9a5a, 0xaaaaaabaaa6a, 0x555665665aaa, 0x5aa665a65a56, 0x6aaaa6aa9a5a,
    0xaaaaaabaaa6a, 0x555665665aaa, 0x5aa665a65a56, 0x6aaaa6aa9a5a, 0xaaaaaaaaaa6a,
    0x555665665aaa, 0x5aa665a65a56, 0x6aaaa6aa9a5a, 0xaaaaaaaaaa6a, 0x555665665aaa,
    0x5aa665a65a56, 0x6aaaa6aa9a5a, 0xaaaaaaaaaa6a, 0x555665655aaa, 0x569665a65a56,
    0x6aa6a6aa9a56, 0xaaaaaaaa9a5a, 0x5556556559aa, 0x569665a65a55, 0x6aa6a6a65a56,
    0xaaaaaaaa9a5a, 0x5556556559aa, 0x569665a65a55, 0x5aa6a6a65a56, 0x6aaaa6aa9a5a,
    0x5556556555aa, 0x569665a65a55, 0x5aa665a65a56, 0x6aaaa6aa9a5a, 0x55555565556a,
    0x555665665a55, 0x5aa665a65a56, 0x6aaaa6aa9a5a, 0x55555565556a, 0x555665665a55,
    0x5aa665a65a56, 0x6aaaa6aa9a5a, 0x55555555556a, 0x555665665a55, 0x5aa665a65a56,
    0x6aaaa6aa9a5a, 0x55555555556a, 0x555665655a55, 0x5aa665a65a56, 0x6aa6a6aa9a5a,
    0x55555555456a, 0x555655655a55, 0x5a9665a65a56, 0x6aa6a6a69a5a, 0x55555555456a,
    0x555655655a55, 0x569665a65a56, 0x6aa6a6a65a56, 0x55555155455a, 0x555655655955,
    0x569665a65a55, 0x5aa6a5a65a56, 0x15555155455a, 0x555555655555, 0x569665665a55,
    0x5aa665a65a56, 0x15555155455a, 0x555555655515, 0x555665665a55, 0x5aa665a65a56,
    0x15555155455a, 0x555555555515, 0x555665665a55, 0x5aa665a65a56, 0x15555155455a,
    0x555555555515, 0x555665665a55, 0x5aa665a65a56, 0x15555155455a, 0x555555555515,
    0x555655655a55, 0x5aa665a65a56, 0x15515155455a, 0x555555554515, 0x555655655a55,
    0x5a9665a65a56, 0x15515151455a, 0x555551554515, 0x555655655a55, 0x569665a65a56,
    0x155151510556, 0x555551554505, 0x555655655955, 0x569665665a55, 0x155110510556,
    0x155551554505, 0x555555655555, 0x569665665a55, 0x55110510556, 0x155551554505,
    0x555555555515, 0x555665665a55, 0x55110510556, 0x155551554505, 0x555555555515,
    0x555665665a55, 0x55110510556, 0x155551554505, 0x555555555515, 0x555655655a55,
    0x55110510556, 0x155551554505, 0x555555555515, 0x555655655a55, 0x55110510556,
    0x155151514505, 0x555555554515, 0x555655655a55, 0x54110510556, 0x155151510505,
    0x555551554515, 0x555655655a55, 0x14110110556, 0x155110510501, 0x555551554505,
    0x555555655555, 0x14110110555, 0x155110510501, 0x555551554505, 0x555555555555,
    0x14110110555, 0x55110510501, 0x155551554505, 0x555555555555, 0x110110555,
    0x55110510501, 0x155551554505, 0x555555555515, 0x110110555, 0x55110510501,
    0x155551554505, 0x555555555515, 0x100100555, 0x55110510501, 0x155151514505,
    0x555555555515, 0x100100555, 0x54110510501, 0x155151514505, 0x555551554515,
    0x100100555, 0x54110510501, 0x155150510505, 0x555551554515, 0x100100555,
    0x14110110501, 0x155110510505, 0x555551554505, 0x100055, 0x14110110500,
    0x155110510501, 0x555551554505, 0x55, 0x14110110500, 0x55110510501,
    0x155551554505, 0x55, 0x110110500, 0x55110510501, 0x155551554505,
    0x15, 0x100110500, 0x55110510501, 0x155551554505,0x555555555515]

def new_list(olist, o):
    zhihead_code = olist.index(o)
    res1 = []
    for i in range(len(olist)):
        res1.append( olist[zhihead_code % len(olist)])
        zhihead_code = zhihead_code + 1
    return res1


# 采集压缩用
def zipSolarTermsList(inputList,charCountLen=2):
    tempList=abListMerge(inputList, type=-1)
    data=0
    num=0
    for i in tempList:
        data+=i << charCountLen*num
        num+=1
    return hex(data),len(tempList)

        
def twentyfourjieqi(year):
    day = getTheYearAllSolarTermsList(year)
    month = [ele for ele in [i for i in range(1,13)] for b in range(2)]
    new_date_list = []
    for i in range(0,23):
        new_date = str(year)+"/"+str(month[i])+"/"+str(day[i])   
        date_format = datetime.strptime(new_date , "%Y/%m/%d").date()
        new_date_list.append(date_format)
    return dict(zip(new_date_list,solarTermsNameList))
# 两个List合并对应元素相加或者相减，a[i]+b[i]:tpye=1 a[i]-b[i]:tpye=-1

def abListMerge(a, b=encryptionVectorList, type=1):
    c = []
    for i in range(len(a)):
        c.append(a[i]+b[i]*type)
    return c

def unZipSolarTermsList(data,rangeEndNum=24,charCountLen=2):
    list2 = []
    for i in range(1,rangeEndNum+1):
        right=charCountLen*(rangeEndNum-i)
        if type(data).__name__=='str':
            data= int(data, 16)
        x=data >> right
        c=2**charCountLen
        list2=[(x % c)]+list2
    return abListMerge(list2)
    
def getTheYearAllSolarTermsList(year):
    return unZipSolarTermsList(solarTermsData[year-START_YEAR])
