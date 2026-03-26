<div align="center">

# ⚡ Luitingyaoqi 雷霆曜氣排盤

### Daoist Thunder Qi Divination Chart Generator | 以雷為主題、藏於道藏里的擇吉排盤系統

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://luiting.streamlit.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](http://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![GitHub stars](https://img.shields.io/github/stars/kentang2017/luiting?style=social)](https://github.com/kentang2017/luiting/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/kentang2017/luiting?style=social)](https://github.com/kentang2017/luiting/network/members)
[![Telegram Chat](https://img.shields.io/badge/Telegram-Chat-blue?logo=telegram)](https://t.me/haizhonggum)
[![Telegram Channel](https://img.shields.io/badge/Telegram-Channel-blue?logo=telegram)](https://t.me/numerology_coding)

**[🌐 Try the Live App 在線體驗](https://luiting.streamlit.app)** · **[📖 Documentation 文檔](#1-introduction-導讀)** · **[💖 Donate 捐贈](#6-support--donate-支持與捐贈)**

---

*An open-source Python library and web application for Luiting (雷霆曜氣) — an ancient Daoist thunder-method date-selection system rooted in the Five Elements, 28 Lunar Mansions, and Nine Palace flying-star theory.*

*一款開源 Python 庫及 Web 應用程式，用於雷霆曜氣排盤——源自道教雷法體系的古代擇日術數，融合五行運化、二十八宿、九宮飛布等理論。*

</div>

---

## ✨ Features 功能特色

| Feature | Description | 功能說明 |
| :--- | :--- | :--- |
| ⚡ Thunder Qi Chart | Full year / month / day / hour chart generation | 年、月、日、時完整排盤 |
| 🔮 Heqi Calculation | Luiting Heqi (合炁) directional analysis | 雷霆合炁到向分析 |
| 🌟 Shengxuan Direction | Ascending Mysterious value & direction | 昇玄值向推算 |
| 🐯 Golden Tiger Sha | Golden Tiger Great Sha positioning | 金虎大煞方位 |
| 🔥 Flowing Fire Star | Inauspicious Flowing Fire star tracking | 流火凶星追蹤 |
| 📡 Value Talisman & Sound | Zhifu (值符) and Chuanyin (傳音) | 值符與傳音 |
| ⭐ Emperor Star | Monthly & daily Emperor Star positions | 月帝星、日帝星 |
| 🏹 Thunder Arrows | Year / month / day / hour arrow indicators | 雷霆年月日時箭 |
| 🌤️ Weather Forecast | Traditional weather prediction via star-birds | 天氣預測、星禽應事 |
| 🌐 Web Interface | Interactive Streamlit-based web UI | 互動式 Streamlit 網頁介面 |

---

## 1. Introduction 導讀

**English**

Luiting (雷霆曜氣) is a date-selection method from the Daoist Thunder Rites tradition, documented in the *Daofa Huiyuan* (道法會元). It is a unique branch of ancient Chinese date-selection science whose theoretical foundation lies in the transformation of Yin-Yang and the Five Elements, combined with the 28 Lunar Mansions, Nine Palace flying-star distribution, Heavenly Stems and Earthly Branches, to calculate auspicious and inauspicious directions for each year, month, day, and hour — primarily for construction and burial date selection.

As recorded in Volume 129 of the *Daofa Huiyuan*: *"The mysteries of thunder emerge from the creation of the cosmic pivot, reaching into the dark depths of profound principles. The workings of the Five Elements do not depart from Yin and Yang."* The method designates Mao (卯) as the Thunder Gate, Zi (子) as the Thunder Cave, Xun (巽) as the Thunder Door, and Li (離) as the Thunder Place. The Yi and Zhen mansions govern thunder; Xu and Wei govern snow; Ji star favors wind; Bi star favors rain; and the Xing mansion governs clear skies.

This program combines classical texts with modern astronomical calculations to provide comprehensive Luiting charts, including Heqi, Shengxuan direction, Golden Tiger Sha, Flowing Fire inauspicious star, Value Talisman, Sound Transmission, Emperor Star, and more.

**中文**

雷霆曜氣乃造葬擇吉之法，載於道法會元之中。雷霆曜氣源於道教雷法體系，是古代擇日學中一門獨特的術數。其理論根基在於天地陰陽五行之運化，結合二十八宿、九宮飛布、天干地支等要素，推算年月日時之吉凶方位，以供造葬擇吉之用。

道法會元卷一百二十九載：「雷霆玄妙，出乎樞機之造化，達乎奧理之冥途。五行運用，不出陰陽。至道之內，樞陽機陰，雷善霆惡，萬物厥有至符。」其法以卯為雷門，子為雷穴，巽為雷戶，離為雷所，運乎坤，傍乎乾，藏乎子，出乎震。翼軫主雷，虛危主雪，箕星好風，畢星好雨，星宿主晴，各得所在之方，以觀天象、測氣候、定吉凶。

本程式依據古籍記載，結合現代天文曆法計算，提供雷霆曜氣年、月、日、時之排盤，包括雷霆合炁、昇玄值向、金虎大煞、流火凶星、值符、傳音、帝星等諸項推算，以便用者查閱參考。

---

## 2. Quickstart 快速開始

### Installation 安裝

```bash
pip install -r requirements.txt
```

### Python API Usage 程式調用

```python
from luiting import Luiting

year = 1984
month = 5
day = 5
hour = 21
minute = 0

result = Luiting(year, month, day, hour, minute).pan()
print(result)
```

### Web Application 網頁應用

Run the Streamlit app locally — 本地啟動 Streamlit 應用：

```bash
streamlit run app.py
```

Or visit the live deployment — 或訪問在線部署：**https://luiting.streamlit.app**

---

## 3. Project Structure 項目結構

```
luiting/
├── app.py           # Streamlit web UI / 網頁介面
├── luiting.py       # Core calculation engine / 核心計算引擎
├── config.py        # Astronomical helpers / 天文輔助函數
├── requirements.txt # Dependencies / 依賴包
└── README.md
```

---

## 4. Bibliography 古今書目列表

| 年份 Year | 作者 Author | 書名 Title | 備註 Notes |
| :--- | :--- | :--- | :--- |
| 宋元年間 | 佚名 | 雨暘氣候親機 | 約出於宋元，一卷，收入《正統道藏》正一部。本篇言雷法，主要講述如何觀察氣候變化。全篇包括《諸雷氣侯》、《妙洞引》、《先天一炁雷霆玉章》等詩文。以及「雷牌」等三十九圖；主要根據上天雲氣在日月星辰及天河間運行之時間、位置，方向，以及其顏色、形狀等情況，預測旱澇陰晴和風雨雷霪，為供施行雷法的道士觀察天象、預測雷雨之書。其中包含古人觀測氣象之經驗，如書中有「石潤水流天欲雨」， 「螻蟻封穴雨時行」，「冬月南風天有雪」，「久雨西風又放晴」等，皆為民間氣象諺語。 |
| 1444 | 佚名 | 雷霆箭煞年月樞機 | 收錄於道法會元卷一百二十九，雷霆玄妙，出乎樞機之造化，達乎奧理之冥途。五行運用，不出陰陽。至道之內，樞陽機陰，雷善霆惡，萬物厥有至符。生煞之用，卯為雷門，子為雷穴，巽為雷戶，離為雷所，運乎坤，傍乎乾，藏乎子，出乎震，是也。凡欲起雷，興雲呼風，致雨掣電，須得旺地相衝，則易為驅召，符合則應驗速矣。且起雷之時，先尋雷公在何處，軫宿在何方。翼軫主雷，虛危主雪，箕星好風，畢星好雨，星宿主晴，各得所在之方，毋落休囚之地。若得威星大躍，猛將毒雷，臨其宮分之間，管取雷轟電掣。雷公在卯，若得太乙臨宮，軫宿相會，煞氣同到，天罡到宮，時辰一定，陞壇告召，無有不應。雷居旺地，宜在卯辰巽離坤兌戌七宮。若居亥子丑寅四宮，則伏藏不為動用。若得星辰衝動，則微有響應。 |
| | 吳國仕 | 造命宗鏡集卷六雷霆曜氣 | |
| | 熊宗立 | 鰲頭通書卷六雷霆曜氣 | |
| | 佚名 | 九天碧潭雷禱雨大法 | 收錄於道法會元內。 |
| | 佚名 | 九州社令陽雷大法 | 收錄於道法會元內。 |
| | 魏明遠 | 修訂增補《雷霆曜氣》 | 收錄在象吉通書內。 |
| | 佚名 | 尅擇璇璣經 | 收錄在五要奇書內。 |
| | 佚名 | 佐元直指 | 收錄在五要奇書內。 |
| | 佚名 | 雷機玄祕 | 收錄在法海遺珠內。 |
| | 佚名 | 雷霆妙契 | 收錄在道法會元內。 |
| | 佚名 | 新鍥全補發微曆正通書大全乾集 | 書內卷二記載雷霆白虎大殺入中宮 |
| | 佚名 | 雷門秘訣歌 | 收錄於新刻萬法歸宗內。 |
| | 佚名 | 雷霆日期秘要 | 清末民國間朱墨雙色精寫本，一函一冊。紙捻毛裝。共計81頁162面。此為占卜術數類著作，查無著錄，極為稀見。朱墨雙色手書，首書"玄機妙訣"繪制各式不同"掌訣"，後用墨色、朱色筆書寫真經秘訣，書法精整，非凡儒為之。內有圖繪人像三幅，掛相圖十幅，皆精工。頗為難得，識者寶之。末尾兩三頁有修，如圖，無大礙。八品。 |
| | 佚名 | 祈禱全書雷霆合氣 : 3卷 | 藏於華東師範大學的圖書館內。 |

---

## 5. WeChat 微信公眾號

![微信公眾號二維碼](https://raw.githubusercontent.com/kentang2017/kinliuren/refs/heads/master/pic/%E5%9C%96%E7%89%87_20260316084147.jpg)

---

## 6. Support & Donate 支持與捐贈

If you find this project useful, please consider:

如果您覺得本項目有用，歡迎：

- ⭐ **Star this repo** — it helps others discover this project! 點亮 Star，讓更多人看到本項目！
- 🔀 **Fork & contribute** — PRs and issues are welcome! 歡迎 Fork、提交 PR 或 Issue！
- 💖 **Donate** — support continued development! 捐贈支持持續開發！

[![Donate with PayPal](https://img.shields.io/badge/Donate-PayPal-green.svg?logo=paypal&style=for-the-badge)](https://www.paypal.me/kinyeah)

---

## 7. License 許可證

[MIT License](http://opensource.org/licenses/MIT) © Ken Tang

Please feel free to use and contribute to the development.

歡迎自由使用並參與開發貢獻。
