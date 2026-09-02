#!/usr/bin/env python3
"""Build Chinese, English and Japanese pages, posters, manifests and SVGs."""

from __future__ import annotations

import copy
import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHARTS = ROOT / "charts"
BASE_MANIFEST = CHARTS / "manifest.json"


FAMILY_TRANSLATIONS = [
    ("Change over time", "What are the trend, rhythm, turning points and duration?", "時間変化", "傾向、周期、転換点、継続時間はどうなっているか？"),
    ("Ranking", "Who is highest or lowest, and how large are the gaps?", "ランキング", "最高・最低はどれで、順位差はどの程度か？"),
    ("Deviation", "How far does each value diverge from the same benchmark?", "偏差", "同じ基準からどの程度離れているか？"),
    ("Magnitude", "How different are the absolute sizes of the objects?", "規模", "対象ごとの絶対的な大きさはどの程度違うか？"),
    ("Distribution", "How are values concentrated, dispersed or skewed?", "分布", "値はどこに集中し、どの程度ばらつき、偏っているか？"),
    ("Correlation", "Do two or three variables move together?", "相関", "二つまたは三つの変数は連動しているか？"),
    ("Part to whole", "How do the parts make up a whole?", "部分と全体", "各部分は全体をどのように構成しているか？"),
    ("Flow and relationships", "How do things move between states, places or actors?", "フローと関係", "状態、場所、主体の間をどのように移動するか？"),
    ("Spatial", "Is location or geographic pattern more important than an exact value?", "空間", "正確な数値より位置や地理的パターンが重要か？"),
]


CHART_TRANSLATIONS = [
    ("Line chart", "What are the shape and turning points of a continuous trend?", "折れ線グラフ", "連続する傾向の形と転換点はどこか？"),
    ("Time column chart", "How much occurred in each discrete period?", "時系列縦棒グラフ", "各期間にどの程度発生したか？"),
    ("Time line + column chart", "Do a total and a rate change together?", "時系列折れ線＋縦棒", "総量と比率は同時に変化しているか？"),
    ("OHLC range chart", "What are each period's open, high, low, close and range?", "OHLCレンジチャート", "各期の始値・高値・安値・終値と変動幅は？"),
    ("Time slope chart", "What changed between two key moments?", "時点スロープチャート", "二つの重要時点の間で何が変化したか？"),
    ("Area chart", "How does filled area convey changing or accumulating magnitude?", "面グラフ", "時間とともに変化・蓄積する規模をどう示すか？"),
    ("Fan forecast chart", "How do a central forecast and its uncertainty expand?", "ファンチャート", "中心予測と不確実性の範囲はどう広がるか？"),
    ("Connected time scatter", "How does the joint state of two measures move over time?", "時系列接続散布図", "二指標の組み合わせは時間とともにどう移動するか？"),
    ("Calendar heatmap", "On which dates do high or low values cluster?", "カレンダーヒートマップ", "高値・低値は一年のどの日に集中するか？"),
    ("Priestley timeline", "How long do multiple events last and overlap?", "プリーストリー・タイムライン", "複数事象の期間と重なりはどうなっているか？"),
    ("Circular time cycle", "Does an event repeat by day, week or year?", "円形周期チャート", "事象は日・週・年の周期で繰り返すか？"),
    ("Seismic event plot", "When are high-frequency events dense and how strong are they?", "地震波型イベント図", "高頻度事象はいつ集中し、強度はどの程度か？"),
    ("Ranked bar chart", "What is the order among categories with long labels?", "順位横棒グラフ", "長い名称のカテゴリをどの順に並べるか？"),
    ("Ranked column chart", "What are the rank and gaps among short-label categories?", "順位縦棒グラフ", "短い名称のカテゴリの順位と差は？"),
    ("Ranked proportional symbols", "How can rank and magnitude be read when sizes differ greatly?", "順位比例シンボル", "規模差が大きいとき順位と量をどう同時に読むか？"),
    ("Ranked strip plot", "How are many objects arranged along one scale?", "順位ストリッププロット", "多数の対象は一つの尺度上でどう並ぶか？"),
    ("Slopegraph", "Who rises or falls, and do ranks reverse between two moments?", "スロープグラフ", "二時点で誰が上昇・下降し、順位は逆転するか？"),
    ("Lollipop chart", "Which ranked values deserve emphasis?", "ロリポップチャート", "順位の中でどの値を強調すべきか？"),
    ("Diverging bar chart", "Which categories are above or below one benchmark?", "発散横棒グラフ", "どのカテゴリが共通基準を上回る・下回るか？"),
    ("Diverging stacked bar", "How are negative and positive responses composed?", "発散積み上げ棒", "否定側と肯定側の構成はどうなっているか？"),
    ("Spine chart", "Do two shares cross a 50% dividing line?", "スパインチャート", "二つの比率は50％の境界を越えるか？"),
    ("Surplus / deficit area", "When does a series cross its benchmark, and by how much?", "黒字／赤字面グラフ", "いつ基準線を越え、偏差はどの程度か？"),
    ("Column chart", "How do absolute values compare across short-label categories?", "縦棒グラフ", "短い名称のカテゴリ間で絶対量をどう比較するか？"),
    ("Bar chart", "How do absolute values compare across long-label categories?", "横棒グラフ", "長い名称のカテゴリ間で絶対量をどう比較するか？"),
    ("Paired columns", "How do two same-unit values compare within each category?", "ペア縦棒", "各カテゴリの同単位二値をどう比較するか？"),
    ("Paired bars", "How far apart are two values for long-label categories?", "ペア横棒", "長い名称のカテゴリで二値の差はどの程度か？"),
    ("Proportional stacked bars", "How can magnitude and share be read within one total?", "比例積み上げ棒", "一つの総量の中で規模と比率をどう読むか？"),
    ("Proportional symbols", "How can very large size differences be compressed?", "比例シンボル", "大きな規模差をどう圧縮して示すか？"),
    ("Unit pictogram", "Can whole or approximate amounts be shown with a fixed unit?", "単位ピクトグラム", "整数や概数を固定単位で直感的に示せるか？"),
    ("Lollipop comparison", "How can visual ink be reduced while preserving comparison?", "ロリポップ比較", "比較を保ちながら描画量を減らすには？"),
    ("Radar chart", "What are the profiles of a few objects across standardised measures?", "レーダーチャート", "少数対象の標準化指標プロフィールは？"),
    ("Parallel coordinates", "What patterns and outliers appear across many measures?", "平行座標", "複数指標にどんなパターンや外れ値があるか？"),
    ("Histogram", "What are the shape and peaks of a continuous distribution?", "ヒストグラム", "連続分布の形とピークはどこか？"),
    ("Box plot", "How do medians, quartiles and outliers compare?", "箱ひげ図", "中央値、四分位、外れ値をどう比較するか？"),
    ("Violin plot", "Is the density multi-modal or skewed?", "バイオリンプロット", "密度は多峰性または偏りを持つか？"),
    ("Population pyramid", "How do two exclusive groups distribute across ordered ages?", "人口ピラミッド", "二つの排他的集団は年齢層別にどう分布するか？"),
    ("Strip distribution", "Where is every observation and where are clusters?", "ストリップ分布", "各観測値はどこにあり、集中域はどこか？"),
    ("Dot stack", "How do frequencies accumulate at discrete values?", "ドットスタック", "離散値の頻度はどう積み上がるか？"),
    ("Barcode plot", "Where is one-dimensional data dense or sparse?", "バーコードプロット", "一次元データはどこで密・疎になるか？"),
    ("Cumulative distribution", "What share of observations falls below a threshold?", "累積分布曲線", "ある閾値以下の観測は何割か？"),
    ("Scatter plot", "Are two continuous variables related?", "散布図", "二つの連続変数に関係はあるか？"),
    ("Line + column combination", "Does one measure move with another?", "折れ線＋縦棒", "一つの量の変化は別の量と連動するか？"),
    ("Connected scatter", "How does a joint two-variable position move over time?", "接続散布図", "二変数の位置は時間とともにどう動くか？"),
    ("Bubble chart", "Does a third measure change the reading of a 2D relationship?", "バブルチャート", "第三の量は二次元関係の解釈を変えるか？"),
    ("2D heatmap", "Where do two ordered dimensions concentrate?", "二次元ヒートマップ", "二つの順序尺度はどの組み合わせに集中するか？"),
    ("Stacked columns", "How do total and composition change together by period?", "積み上げ縦棒", "期ごとの総量と構成はどう同時に変わるか？"),
    ("100% stacked bars", "How do proportional compositions compare across groups?", "100％積み上げ横棒", "グループ間で構成比をどう比較するか？"),
    ("Pie chart", "What are the rough shares of a few parts?", "円グラフ", "少数の部分は全体の何割か？"),
    ("Donut chart", "How much do the main parts occupy within one whole?", "ドーナツチャート", "一つの全体で主要部分はどの程度か？"),
    ("Treemap", "What are the largest area shares in a hierarchy?", "ツリーマップ", "階層内の面積構成と大項目は？"),
    ("Voronoi composition", "Can irregular regions express shares of a whole?", "ボロノイ構成図", "不規則領域で全体の比率を表せるか？"),
    ("Arc composition", "How complete is a total or staged progress?", "円弧構成図", "総量の達成度や段階進捗は？"),
    ("Waffle chart", "How can a percentage become 100 countable units?", "ワッフルチャート", "百分率を数えられる100単位にどう変換するか？"),
    ("Set relationship", "What is unique to, or shared by, two sets?", "集合関係図", "二集合の固有部分と重複部分は？"),
    ("Waterfall chart", "How do additions and subtractions bridge a start to an end?", "ウォーターフォール", "増減項は起点から終点へどう累積するか？"),
    ("Sankey diagram", "How is an additive total allocated from sources to destinations?", "サンキー図", "加算可能な総量は出所から行先へどう配分されるか？"),
    ("Waterfall bridge", "How do successive changes push a start to an end?", "ウォーターフォール・ブリッジ", "連続する増減は起点を終点へどう動かすか？"),
    ("Chord diagram", "How large are two-way links among a few groups?", "コード図", "少数グループ間の双方向関係はどの程度か？"),
    ("Network graph", "Who connects to whom, and where are hubs, communities and bridges?", "ネットワーク図", "誰と誰がつながり、中心・群落・橋渡しはどこか？"),
    ("Choropleth map", "How do rates or standardised measures vary across regions?", "階級区分図", "率や標準化指標は地域間でどう変わるか？"),
    ("Proportional symbol map", "How large is an absolute amount at each place?", "比例シンボル地図", "各地点の絶対量や規模はどの程度か？"),
    ("Flow map", "Where do objects move from and to?", "フロー地図", "対象はどこからどこへ移動するか？"),
    ("Contour map", "Where does a continuous surface reach equal values?", "等値線図", "連続面上で同じ値に達する場所は？"),
    ("Equal-area cartogram", "How can real area be removed from regional comparison?", "等面積カルトグラム", "実面積が地域比較へ与える影響をどう除くか？"),
    ("Area cartogram", "How can region area directly encode an amount?", "面積カルトグラム", "地域面積で数量を直接表すには？"),
    ("Dot-density map", "Where is an amount roughly concentrated within a region?", "ドット密度地図", "数量は地域内のどこに概ね集中するか？"),
    ("Spatial heatmap", "Where are continuous high-density hotspots?", "空間ヒートマップ", "連続空間の高密度ホットスポットはどこか？"),
]


TEXT_TRANSLATIONS = {
    "甲": ("A", "A"), "乙": ("B", "B"), "丙": ("C", "C"), "丁": ("D", "D"), "戊": ("E", "E"),
    "甲组": ("Group A", "グループA"), "乙组": ("Group B", "グループB"), "丙组": ("Group C", "グループC"), "丁组": ("Group D", "グループD"), "戊组": ("Group E", "グループE"),
    "甲 38": ("A 38", "A 38"), "乙 27": ("B 27", "B 27"), "丙 18": ("C 18", "C 18"), "丁 11": ("D 11", "D 11"),
    "甲 38%": ("A 38%", "A 38%"), "乙 27%": ("B 27%", "B 27%"), "丙 18%": ("C 18%", "C 18%"), "丁及其他 17%": ("D + other 17%", "D・その他 17%"), "其余 35%": ("Other 35%", "その他 35%"),
    "一": ("Mon", "月"), "二": ("Tue", "火"), "三": ("Wed", "水"), "四": ("Thu", "木"), "五": ("Fri", "金"), "六": ("Sat", "土"), "日": ("Sun", "日"),
    "北": ("N", "北"), "南": ("S", "南"), "东": ("E", "東"), "西": ("W", "西"), "中": ("Central", "中央"), "海": ("Coast", "沿岸"),
    "北区": ("North", "北部"), "南区": ("South", "南部"), "东区": ("East", "東部"), "西区": ("West", "西部"), "中区": ("Central", "中央部"), "海区": ("Coast", "沿岸部"),
    "月份": ("Month", "月"), "1月": ("Jan", "1月"), "4月": ("Apr", "4月"), "7月": ("Jul", "7月"), "10月": ("Oct", "10月"), "12月": ("Dec", "12月"), "12月 68": ("Dec 68", "12月 68"),
    "1期": ("P1", "第1期"), "2期": ("P2", "第2期"), "3期": ("P3", "第3期"), "4期": ("P4", "第4期"), "5期": ("P5", "第5期"), "时期": ("Period", "期間"),
    "第1周": ("Week 1", "第1週"), "第12周": ("Week 12", "第12週"), "年度周期": ("Annual cycle", "年間周期"),
    "起点": ("Start", "起点"), "终点": ("End", "終点"), "开始": ("Start", "開始"), "结束": ("End", "終了"),
    "总量": ("Total", "総量"), "数量": ("Amount", "数量"), "数量（件）": ("Count", "件数"), "指数": ("Index", "指数"), "比率": ("Rate", "比率"), "总量／比率": ("Total / rate", "総量／比率"),
    "类别": ("Category", "カテゴリ"), "观察值": ("Observation", "観測値"), "中位数": ("Median", "中央値"), "变量X": ("Variable X", "変数X"), "变量Y": ("Variable Y", "変数Y"), "变量X（%）": ("Variable X (%)", "変数X（%）"), "变量Y（%）": ("Variable Y (%)", "変数Y（%）"),
    "维度X": ("Dimension X", "次元X"), "维度Y": ("Dimension Y", "次元Y"), "取值": ("Value", "値"), "数值区间": ("Value bin", "値の区間"), "频数": ("Frequency", "度数"), "累计占比": ("Cumulative share", "累積比率"), "约50%": ("About 50%", "約50%"),
    "低": ("Low", "低"), "高": ("High", "高"), "规模最大": ("Largest", "最大"), "圆面积对应数量": ("Circle area = amount", "円面積＝数量"), "最大事件": ("Largest event", "最大事象"), "重点观察": ("Focus", "注目点"),
    "交易期": ("Trading period", "取引期間"), "价格": ("Price", "価格"), "时间": ("Time", "時間"), "预测值": ("Forecast", "予測値"), "预测起点": ("Forecast begins", "予測開始"),
    "项目甲": ("Project A", "プロジェクトA"), "调查乙": ("Inquiry B", "調査B"), "审理丙": ("Review C", "審理C"), "行动丁": ("Action D", "行動D"), "计划戊": ("Plan E", "計画E"),
    "群体甲": ("Group A", "集団A"), "群体乙": ("Group B", "集団B"), "集合甲": ("Set A", "集合A"), "集合乙": ("Set B", "集合B"), "交集 18": ("Overlap 18", "共通 18"),
    "已完成": ("Complete", "完了"), "每格=1%": ("Each cell = 1%", "1マス＝1%"), "每点=1个观察": ("1 dot = 1 observation", "1点＝1観測"), "● = 10个单位": ("● = 10 units", "●＝10単位"),
    "证据": ("Evidence", "証拠"), "速度": ("Speed", "速度"), "覆盖": ("Coverage", "網羅性"), "透明": ("Transparency", "透明性"), "影响": ("Impact", "影響"),
    "住房": ("Housing", "住宅"), "交通": ("Transport", "交通"), "医疗": ("Health", "医療"), "教育": ("Education", "教育"), "负向": ("Negative", "否定側"), "正向": ("Positive", "肯定側"),
    "来源": ("Source", "出所"), "过程": ("Process", "過程"), "去向": ("Destination", "行先"), "桥梁节点": ("Bridge node", "橋渡しノード"), "热点": ("Hotspot", "ホットスポット"),
    "抽象空间单元 · 正式图须换权威边界": ("Schematic units · replace with authoritative boundaries", "模式単位・正式版では公的境界に置換"),
    "每点=100单位 · 点位非精确地址": ("1 dot = 100 units · locations are approximate", "1点＝100単位・位置は概略"),
}


UI = {
    "zh": {
        "lang": "zh-CN", "label": "中文", "title": "金碧浮世 · 图表词汇", "description": "九类信息关系、67种可编辑图形，以及融合金碧屏风结构与浮世绘套色语法的现代数据视觉系统。",
        "eyebrow": "KINPEKI UKIYO CHART VOCABULARY · V1.0", "hero1": "金碧浮世", "hero2": "图表词汇", "lede": "用狩野派金碧屏风的空间秩序，承载浮世绘套色木版的图形语法。九类信息关系、六十七种图形，让风格服务于判断，而不是遮住数据。",
        "download": "下载高清总表", "browse": "浏览全部图形", "source": "查看总表源文件", "stat1": "信息关系", "stat2": "可编辑SVG", "stat3": "类别色上限",
        "nav": ["原作参考", "设计语言", "配色", "67种图形", "使用边界"],
        "art_kicker": "ORIGINAL PRINT · PUBLIC DOMAIN", "art_title": "从《神奈川冲浪里》看见图表语言", "art_caption": "葛饰北斋《神奈川冲浪里》，约1830—1832年，彩色木版画，大都会艺术博物馆藏，馆藏编号JP2972。Public Domain，数字图像来自The Met Open Access。",
        "art_points": [["主版线", "墨色轮廓让浪、船与富士山在复杂画面中仍然清楚。"], ["藍色层次", "有限色版通过深浅而不是无限色相建立空间与力量。"], ["斜向构图", "浪峰、船身与山体形成方向，视觉路径明确。"], ["负空间", "天空与浪心的留白让富士山成为稳定的判断锚点。"]],
        "idea_kicker": "A CONTEMPORARY SYNTHESIS", "idea_title": "不是复古装饰，是一套可以执行的视觉合同",
        "ideas": [["金碧屏风组织页面", "金色只用于分扇、标题与基准，小面积建立节奏；胡粉纸保留绘图区的清晰和呼吸。"], ["主版线约束数据", "数据标记统一保留墨色轮廓，坐标、基线和参考线使用同一套线宽体系。"], ["套色必须有职责", "新摺普蓝承担主数据，鲜朱只标重点；多类别最多五色，并用实虚线、空实心和直接标签补足。"], ["装饰不得改变尺度", "斜切、印章和分扇停留在绘图区外；柱长、面积、线宽和地图位置仍严格对应数据。"]],
        "palette_kicker": "NEW-IMPRESSION HIGH-CHROMA PALETTE", "palette_title": "九个角色，不是九种随意使用的颜色", "palette_note": "单序列优先只用普蓝；二元对比最多两个非中性色；类别身份确实重要时才放宽到五色。鲜色用于数据图形，小字使用同色相深阶色，图形内部不使用渐变。",
        "chart_kicker": "9 FAMILIES · 67 EDITABLE SVGS", "chart_title": "先选择关系，再选择图形", "chart_intro": "所有示例均保留墨色主版线。多序列折线同时改变线型，填充图形保留直接标注或轮廓；灰度和低亮度屏幕下仍能辨认结构。", "all": "全部", "download_svg": "下载 SVG",
        "license_kicker": "USE WITH ATTRIBUTION · BRAND RESERVED", "license_title": "图表可以复用，品牌不能被误用", "license_items": [["代码", "HTML、CSS、JSON和构建脚本采用MIT License。"], ["设计", "总表、SVG图形和说明文档采用CC BY 4.0，可修改和再发布，但需署名。"], ["原作", "《神奈川冲浪里》参考图为Public Domain，须保留作品与来源说明。"], ["品牌", "AI记者名称与Logo不包含在开放许可中，不得暗示合作。"]],
        "footer": "金碧屏风结构 × 浮世绘木版语法 × 现代数据规范", "local": "中文版本"
    },
    "en": {
        "lang": "en", "label": "English", "title": "Kinpeki Ukiyo Chart Vocabulary", "description": "Nine information relationships, 67 editable charts, and a modern data-visualisation system joining kinpeki screen structure with ukiyo-e print grammar.",
        "eyebrow": "KINPEKI UKIYO CHART VOCABULARY · V1.0", "hero1": "Kinpeki Ukiyo", "hero2": "Chart Vocabulary", "lede": "Kano-school kinpeki screens provide spatial order; ukiyo-e colour woodblocks provide graphic grammar. Nine information relationships and 67 forms let style serve judgement instead of obscuring data.",
        "download": "Download poster", "browse": "Browse all charts", "source": "View poster source", "stat1": "information families", "stat2": "editable SVGs", "stat3": "maximum category colours",
        "nav": ["Original print", "Design language", "Palette", "67 charts", "Use and licence"],
        "art_kicker": "ORIGINAL PRINT · PUBLIC DOMAIN", "art_title": "See the chart language in The Great Wave", "art_caption": "Katsushika Hokusai, Under the Wave off Kanagawa (The Great Wave), ca. 1830–32, colour woodblock print. The Metropolitan Museum of Art, JP2972. Public Domain image via The Met Open Access.",
        "art_points": [["Keyline", "Ink contours keep wave, boats and Fuji legible inside a complex scene."], ["Blue hierarchy", "A limited set of blue tones creates depth and force without unlimited hues."], ["Oblique movement", "Wave crest, boats and mountain establish a clear directional reading path."], ["Negative space", "Sky and the hollow of the wave make Fuji a stable visual anchor."]],
        "idea_kicker": "A CONTEMPORARY SYNTHESIS", "idea_title": "Not retro decoration: an executable visual contract",
        "ideas": [["Screen rhythm organises the page", "Gold is reserved for seams, headings and references; shell-white paper keeps the plot quiet."], ["Keylines discipline the data", "Filled marks retain ink outlines; axes, baselines and references share one stroke system."], ["Every colour has a job", "New-impression Prussian blue carries primary data and vivid vermilion marks focus; multi-category charts stop at five roots."], ["Decoration never changes scale", "Cuts, seals and screen seams stay outside the plot; length, area, width and map position remain truthful."]],
        "palette_kicker": "NEW-IMPRESSION HIGH-CHROMA PALETTE", "palette_title": "Nine roles, not nine arbitrary colours", "palette_note": "Prefer one Prussian-blue root for a single series, cap binary comparison at two non-neutral roots, and use up to five only when category identity matters. Vivid colours belong to data marks; small text uses darker tonal partners. Never use gradients inside marks.",
        "chart_kicker": "9 FAMILIES · 67 EDITABLE SVGS", "chart_title": "Choose the relationship, then the form", "chart_intro": "Every example retains an ink keyline. Multi-series lines also change dash pattern; filled forms use outlines or direct labels so structure survives grayscale and low-brightness screens.", "all": "All", "download_svg": "Download SVG",
        "license_kicker": "USE WITH ATTRIBUTION · BRAND RESERVED", "license_title": "Reuse the charts; do not misuse the brand", "license_items": [["Code", "HTML, CSS, JSON and build scripts use the MIT License."], ["Design", "Posters, SVG charts and documentation use CC BY 4.0 with attribution."], ["Original print", "The Great Wave reference image is Public Domain; retain artwork and source information."], ["Brand", "The AI Reporter name and logo are excluded from the open licences and cannot imply endorsement."]],
        "footer": "Kinpeki screen structure × ukiyo-e print grammar × modern data rules", "local": "English edition"
    },
    "ja": {
        "lang": "ja", "label": "日本語", "title": "金碧浮世・チャート語彙", "description": "九つの情報関係、67種類の編集可能な図表、金碧屏風の構成と浮世絵の版画文法を結ぶ現代データ可視化システム。",
        "eyebrow": "KINPEKI UKIYO CHART VOCABULARY · V1.0", "hero1": "金碧浮世", "hero2": "チャート語彙", "lede": "狩野派の金碧屏風が空間の秩序を、浮世絵の多色木版が図形の文法を与える。九つの情報関係と67種類の図表で、様式をデータ判断に従わせる。",
        "download": "高解像度ポスター", "browse": "全図表を見る", "source": "ポスター原稿を見る", "stat1": "情報関係", "stat2": "編集可能SVG", "stat3": "カテゴリ色の上限",
        "nav": ["原作参照", "デザイン言語", "配色", "67図表", "利用条件"],
        "art_kicker": "ORIGINAL PRINT · PUBLIC DOMAIN", "art_title": "『神奈川沖浪裏』から図表言語を見る", "art_caption": "葛飾北斎『神奈川沖浪裏』、1830～32年頃、多色木版画。メトロポリタン美術館蔵、JP2972。The Met Open AccessによるPublic Domain画像。",
        "art_points": [["主版線", "墨の輪郭が、複雑な画面でも波、舟、富士を明確に保つ。"], ["藍の階層", "限られた藍の濃淡が、無数の色相に頼らず奥行きと力をつくる。"], ["斜めの動勢", "波頭、舟、山体が方向をつくり、視線の経路を明確にする。"], ["余白", "空と波の内側の余白が、富士を安定した視覚の錨にする。"]],
        "idea_kicker": "A CONTEMPORARY SYNTHESIS", "idea_title": "懐古的な装飾ではなく、実行できる視覚契約",
        "ideas": [["屏風のリズムでページを組む", "金は継ぎ目、見出し、基準だけに使い、胡粉紙の描画域を静かに保つ。"], ["主版線でデータを律する", "塗りのあるマークにも墨の輪郭を残し、軸・基線・参照線を同じ線体系にそろえる。"], ["色には役割を与える", "新摺のベロ藍を主データ、鮮朱を焦点に限定し、多カテゴリでも五色を上限とする。"], ["装飾で尺度を変えない", "切り込み、印、屏風の継ぎ目は描画域の外に置き、長さ、面積、線幅、地図位置を正確に保つ。"]],
        "palette_kicker": "NEW-IMPRESSION HIGH-CHROMA PALETTE", "palette_title": "九つの役割。九色を自由に使うのではない", "palette_note": "単系列はベロ藍一色を優先し、二項比較は非中性色を二色までにする。鮮色はデータ図形に使い、小さな文字には同系の濃色を使う。カテゴリ識別が重要な場合だけ五色まで使い、マーク内のグラデーションは禁止。",
        "chart_kicker": "9 FAMILIES · 67 EDITABLE SVGS", "chart_title": "関係を選び、その後に図形を選ぶ", "chart_intro": "すべての例に墨の主版線を残す。複数系列の線は線種も変え、塗りの図形は輪郭または直接ラベルを持つため、グレースケールでも構造が読める。", "all": "すべて", "download_svg": "SVGをダウンロード",
        "license_kicker": "USE WITH ATTRIBUTION · BRAND RESERVED", "license_title": "図表は再利用できる。ブランドは誤用しない", "license_items": [["コード", "HTML、CSS、JSON、ビルドスクリプトはMIT License。"], ["デザイン", "ポスター、SVG図表、文書はCC BY 4.0。表示を付けて改変・再配布できる。"], ["原作", "『神奈川沖浪裏』参照画像はPublic Domain。作品名と出典を保持する。"], ["ブランド", "AI記者の名称とロゴはオープンライセンスに含まれず、提携を示唆できない。"]],
        "footer": "金碧屏風の構成 × 浮世絵版画の文法 × 現代データ規範", "local": "日本語版"
    },
}


PALETTE = [
    ("#fbf3de", ("胡粉纸", "Shell-white paper", "胡粉紙")),
    ("#181a1b", ("墨", "Ink", "墨")),
    ("#0069a6", ("普蓝", "Prussian blue", "ベロ藍")),
    ("#e24832", ("鲜朱", "Vivid vermilion", "鮮朱")),
    ("#3a8a5c", ("緑青", "Rokusho", "緑青")),
    ("#e2a228", ("明黄", "Bright yellow", "明黄")),
    ("#8d4b8e", ("藤紫", "Fuji purple", "藤紫")),
    ("#e0b53a", ("亮金", "Bright gold", "明金")),
    ("#c8b990", ("薄墨", "Pale ink", "薄墨")),
]


def localised_manifest(base: dict, locale: str) -> dict:
    result = copy.deepcopy(base)
    result["locale"] = {"zh": "zh-CN", "en": "en", "ja": "ja"}[locale]
    result["project"] = UI[locale]["title"]
    chart_offset = 0
    for family_index, family in enumerate(result["families"]):
        en_name, en_q, ja_name, ja_q = FAMILY_TRANSLATIONS[family_index]
        if locale == "en": family["name"], family["question"] = en_name, en_q
        elif locale == "ja": family["name"], family["question"] = ja_name, ja_q
        for chart in family["charts"]:
            en_c, en_cq, ja_c, ja_cq = CHART_TRANSLATIONS[chart_offset]
            if locale == "en": chart["name"], chart["question"] = en_c, en_cq
            elif locale == "ja": chart["name"], chart["question"] = ja_c, ja_cq
            if locale in {"en", "ja"}:
                relative = chart["file"].removeprefix("charts/")
                chart["file"] = f"charts/{locale}/{relative}"
            chart_offset += 1
    return result


def replace_text_nodes(source: str, locale: str, chart: dict) -> str:
    source = re.sub(r'aria-labelledby="[^"]+"', f'aria-labelledby="chart-{chart["id"]}-title chart-{chart["id"]}-desc"', source, count=1)
    source = re.sub(r'<title[^>]*>.*?</title>', f'<title id="chart-{chart["id"]}-title">{html.escape(chart["name"])}</title>', source, count=1, flags=re.S)
    source = re.sub(r'<desc[^>]*>.*?</desc>', f'<desc id="chart-{chart["id"]}-desc">{html.escape(chart["question"])}</desc>', source, count=1, flags=re.S)

    def translate(match: re.Match[str]) -> str:
        opening, value, closing = match.groups()
        plain = html.unescape(value.strip())
        if plain in TEXT_TRANSLATIONS:
            translated = TEXT_TRANSLATIONS[plain][0 if locale == "en" else 1]
            return opening + html.escape(translated) + closing
        return match.group(0)

    return re.sub(r'(<text\b[^>]*>)([^<>]*)(</text>)', translate, source)


def build_svg_locales(manifests: dict[str, dict]) -> None:
    base_by_id = {c["id"]: c for f in manifests["zh"]["families"] for c in f["charts"]}
    for locale in ("en", "ja"):
        local_by_id = {c["id"]: c for f in manifests[locale]["families"] for c in f["charts"]}
        for chart_id, base_chart in base_by_id.items():
            source_path = ROOT / base_chart["file"]
            target_path = ROOT / local_by_id[chart_id]["file"]
            target_path.parent.mkdir(parents=True, exist_ok=True)
            transformed = replace_text_nodes(source_path.read_text(encoding="utf-8"), locale, local_by_id[chart_id])
            target_path.write_text(transformed, encoding="utf-8")


def language_links(locale: str, css_class: str = "lang-switch") -> str:
    files = {"zh": "index.html", "en": "index-en.html", "ja": "index-ja.html"}
    return f'<nav class="{css_class}" aria-label="Language">' + "".join(
        f'<a href="{filename}" lang="{UI[key]["lang"]}"' + (' aria-current="page"' if key == locale else '') + f'>{UI[key]["label"]}</a>'
        for key, filename in files.items()
    ) + "</nav>"


def page_template(locale: str, manifest_filename: str, poster_filename: str, poster_source: str) -> str:
    u = UI[locale]
    names = [p[1][{"zh": 0, "en": 1, "ja": 2}[locale]] for p in PALETTE]
    swatches = "".join(f'<div style="--swatch:{colour}"><i></i><strong>{html.escape(name)}</strong><code>{colour.upper()}</code></div>' for (colour, _), name in zip(PALETTE, names))
    ideas = "".join(f'<article><span>{i}</span><h3>{html.escape(title)}</h3><p>{html.escape(body)}</p></article>' for i, (title, body) in enumerate(u["ideas"], 1))
    art_points = "".join(f'<article><h3>{html.escape(title)}</h3><p>{html.escape(body)}</p></article>' for title, body in u["art_points"])
    licences = "".join(f'<p><strong>{html.escape(title)}</strong>{html.escape(body)}</p>' for title, body in u["license_items"])
    nav_targets = ["#art", "#idea", "#palette", "#charts", "#license"]
    nav = "".join(f'<a href="{target}">{html.escape(label)}</a>' for target, label in zip(nav_targets, u["nav"]))
    return f'''<!doctype html>
<html lang="{u['lang']}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{html.escape(u['description'])}"><meta property="og:title" content="{html.escape(u['title'])}"><meta property="og:description" content="{html.escape(u['description'])}"><meta property="og:image" content="assets/{poster_filename.replace('poster','preview').replace('.png','.jpg')}"><title>{html.escape(u['title'])}｜AI Reporter</title><link rel="stylesheet" href="styles.css"></head>
<body><header class="site-head"><a class="brand" href="#top" aria-label="AI Reporter"><img src="assets/ai-reporter-logo.png" alt="AI Reporter"></a><nav class="main-nav" aria-label="Sections">{nav}</nav>{language_links(locale)}</header>
<main id="top"><section class="hero screen-grid"><div class="hero-copy"><p class="eyebrow">{u['eyebrow']}</p><h1><span>{u['hero1']}</span><br><em>{u['hero2']}</em></h1><p class="lede">{u['lede']}</p><div class="actions"><a class="primary" href="assets/{poster_filename}" download>{u['download']}</a><a href="#charts">{u['browse']}</a><a href="src/{poster_source}">{u['source']}</a></div></div><div class="hero-mark" aria-hidden="true"><i>図</i><b></b><span>KEYLINE<br>FLAT COLOUR<br>DIRECT LABEL</span></div><dl class="stats"><div><dt>9</dt><dd>{u['stat1']}</dd></div><div><dt>67</dt><dd>{u['stat2']}</dd></div><div><dt>5</dt><dd>{u['stat3']}</dd></div></dl></section>
<figure class="art-reference" id="art"><div class="art-frame"><img src="assets/hokusai-great-wave-reference.jpg" alt="{html.escape(u['art_title'])}"></div><figcaption><p class="section-kicker">{u['art_kicker']}</p><h2>{u['art_title']}</h2><p class="art-caption">{u['art_caption']} <a href="https://www.metmuseum.org/art/collection/search/56353">The Met</a></p><div class="art-insights">{art_points}</div></figcaption></figure>
<section class="idea" id="idea"><div><p class="section-kicker">{u['idea_kicker']}</p><h2>{u['idea_title']}</h2></div><div class="idea-grid">{ideas}</div></section>
<section class="palette-section" id="palette"><p class="section-kicker">{u['palette_kicker']}</p><h2>{u['palette_title']}</h2><div class="palette">{swatches}</div><p class="palette-note">{u['palette_note']}</p></section>
<section class="charts-section" id="charts"><div class="section-title"><div><p class="section-kicker">{u['chart_kicker']}</p><h2>{u['chart_title']}</h2></div><p>{u['chart_intro']}</p></div><div class="filters" id="filters"><button class="active" data-family="all">{u['all']} 67</button></div><div class="chart-grid" id="chart-grid" aria-live="polite"></div></section>
<section class="license-section" id="license"><p class="section-kicker">{u['license_kicker']}</p><h2>{u['license_title']}</h2><div class="license-grid">{licences}</div></section></main>
<footer><p>AI记者 · AI REPORTER</p><p>{u['footer']}</p><p>{u['local']}</p></footer>
<script>const manifestPath='charts/{manifest_filename}',downloadLabel={json.dumps(u['download_svg'],ensure_ascii=False)};</script><script src="scripts/site.js"></script></body></html>'''


def poster_template(locale: str, manifest_filename: str, poster_filename: str) -> str:
    u = UI[locale]
    palette_names = [p[1][{"zh": 0, "en": 1, "ja": 2}[locale]] for p in PALETTE]
    swatches = "".join(f'<div class="swatch" style="--c:{colour}"><i></i><strong>{html.escape(name)}</strong><code>{colour.upper()}</code></div>' for (colour, _), name in zip(PALETTE, palette_names))
    art_points = "".join(f'<p><strong>{html.escape(title)}</strong>{html.escape(body)}</p>' for title, body in u["art_points"])
    steps = {
        "zh": [("先问关系", "变化、排名、偏差、量级、分布、相关、整体、流动还是空间？"), ("再定颜色", "单序列一色，二元最多两色；多类别只有身份重要时才放宽到五色。"), ("最后检查", "零基线、单位、来源、灰度区分、手机字号和装饰边界全部通过再发布。")],
        "en": [("Ask the relationship", "Change, rank, deviation, magnitude, distribution, correlation, composition, flow or space?"), ("Assign colour roles", "One root for one series; two for binary comparison; up to five only for real category identity."), ("Check before release", "Verify baseline, unit, source, grayscale distinction, mobile type and the decoration boundary.")],
        "ja": [("関係を問う", "変化、順位、偏差、規模、分布、相関、構成、フロー、空間のどれか？"), ("色の役割を決める", "単系列は一色、二項比較は二色まで。カテゴリ識別が重要な場合だけ五色まで。"), ("公開前に確認", "基線、単位、出典、グレースケール、モバイル文字、装飾境界を確認する。")],
    }[locale]
    reading = "".join(f'<article><i>{i}</i><h2>{html.escape(t)}</h2><p>{html.escape(b)}</p></article>' for i,(t,b) in enumerate(steps,1))
    return f'''<!doctype html><html lang="{u['lang']}"><head><meta charset="utf-8"><meta name="viewport" content="width=2400,initial-scale=1"><title>{html.escape(u['title'])}</title><link rel="stylesheet" href="poster.css"></head><body><main class="poster">
<header class="masthead"><div><div class="eyebrow">{u['eyebrow']}</div><h1>{u['hero1']}<em>{u['hero2']}</em></h1><p class="dek">{u['lede']}</p></div><div class="seal-column"><img class="brand-logo" src="../assets/ai-reporter-logo.png" alt="AI Reporter"><span class="seal">図</span><b></b><p>KEYLINE<br>FLAT COLOUR<br>HONEST SCALE</p></div><div class="contract"><div><strong>KEYLINE</strong><span>Ink defines structure</span></div><div><strong>FLAT COLOUR</strong><span>Every colour has a role</span></div><div><strong>DIRECT LABEL</strong><span>Meaning stays close to marks</span></div><div><strong>HONEST SCALE</strong><span>Style never bends data</span></div></div></header>
<section class="palette-band"><div class="palette-title"><b>{u['palette_title']}</b><span>DIGITAL PALETTE</span></div>{swatches}</section>
<section class="poster-art"><div class="poster-art-image"><img src="../assets/hokusai-great-wave-reference.jpg" alt="{html.escape(u['art_title'])}"></div><div class="poster-art-copy"><p class="section-kicker">{u['art_kicker']}</p><h2>{u['art_title']}</h2><p class="caption">{u['art_caption']}</p><div>{art_points}</div></div></section>
<section class="reading-key">{reading}</section><div class="families" id="families"></div><footer class="footer"><div><h2>{u['title']}</h2></div><p>{u['footer']}. The Great Wave image: Public Domain, The Metropolitan Museum of Art, JP2972.</p><div class="end"><strong>9 × 67</strong><span>{u['local']} · AI Reporter brand reserved</span></div></footer></main>
<script>const posterManifest='../charts/{manifest_filename}';</script><script src="poster.js"></script></body></html>'''


def write_shared_scripts() -> None:
    (ROOT / "scripts" / "site.js").write_text(r'''const grid=document.querySelector('#chart-grid');const filters=document.querySelector('#filters');let families=[];function render(selected='all'){grid.innerHTML='';families.filter(f=>selected==='all'||f.directory===selected).forEach(f=>f.charts.forEach(c=>{const article=document.createElement('article');article.className='chart-card';article.innerHTML=`<div class="chart-image"><img src="${c.file}" alt="${c.name}"></div><div class="chart-copy"><span>${String(c.id).padStart(2,'0')} · ${f.name}</span><h3>${c.name}</h3><p>${c.question}</p><a href="${c.file}" download>${downloadLabel}</a></div>`;grid.appendChild(article)}))}fetch(manifestPath).then(r=>r.json()).then(data=>{families=data.families;families.forEach(f=>{const b=document.createElement('button');b.dataset.family=f.directory;b.textContent=`${f.name} ${f.charts.length}`;filters.appendChild(b)});filters.addEventListener('click',e=>{if(e.target.tagName!=='BUTTON')return;filters.querySelectorAll('button').forEach(b=>b.classList.remove('active'));e.target.classList.add('active');render(e.target.dataset.family)});render()}).catch(()=>{grid.innerHTML='<p>Chart manifest could not be loaded.</p>'});
''', encoding="utf-8")
    (ROOT / "src" / "poster.js").write_text(r'''const accents=['#e0b53a','#8cc7df','#f5a08b','#9ed0ab','#c7a0cf','#ead49a','#84bcd5','#efaa91','#9bc9a4'];fetch(posterManifest).then(r=>r.json()).then(data=>{const host=document.querySelector('#families');data.families.forEach((family,index)=>{const section=document.createElement('section');section.className='family-panel';section.style.setProperty('--family',accents[index]);section.innerHTML=`<header class="family-head"><span class="family-number">${String(family.id).padStart(2,'0')}</span><div><h2>${family.name}</h2><p>${family.question}</p></div><b>${family.charts.length}</b></header><div class="mini-grid">${family.charts.map(c=>`<article class="mini-card"><header class="mini-head"><span>${String(c.id).padStart(2,'0')}</span><div><h3>${c.name}</h3><p>${c.question}</p></div></header><div class="chart-shell"><img src="../${c.file}" alt="${c.name}"></div></article>`).join('')}</div>`;host.appendChild(section)})});
''', encoding="utf-8")


def main() -> None:
    base = json.loads(BASE_MANIFEST.read_text(encoding="utf-8"))
    if len(CHART_TRANSLATIONS) != 67:
        raise RuntimeError(f"Expected 67 chart translations, found {len(CHART_TRANSLATIONS)}")
    manifests = {locale: localised_manifest(base, locale) for locale in ("zh", "en", "ja")}
    (ROOT / "locales").mkdir(exist_ok=True)
    for locale, manifest in manifests.items():
        filename = {"zh": "manifest.json", "en": "manifest-en.json", "ja": "manifest-ja.json"}[locale]
        (CHARTS / filename).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (ROOT / "locales" / f"{locale}.json").write_text(json.dumps(UI[locale], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    build_svg_locales(manifests)
    write_shared_scripts()
    page_specs = {
        "zh": ("index.html", "manifest.json", "kinpeki-ukiyo-poster.png", "kinpeki-ukiyo-chart-vocabulary.html"),
        "en": ("index-en.html", "manifest-en.json", "kinpeki-ukiyo-poster-en.png", "kinpeki-ukiyo-chart-vocabulary-en.html"),
        "ja": ("index-ja.html", "manifest-ja.json", "kinpeki-ukiyo-poster-ja.png", "kinpeki-ukiyo-chart-vocabulary-ja.html"),
    }
    for locale, (page_file, manifest_file, poster_file, poster_source) in page_specs.items():
        (ROOT / page_file).write_text(page_template(locale, manifest_file, poster_file, poster_source), encoding="utf-8")
        (ROOT / "src" / poster_source).write_text(poster_template(locale, manifest_file, poster_file), encoding="utf-8")
    print("Built 3 pages, 3 posters, 3 manifests and 201 localised SVGs.")


if __name__ == "__main__":
    main()
