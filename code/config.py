# -*- coding: utf-8 -*-
"""
Global configuration: paths, seed characters, exclusions, word lists.
=====================================================================
To adjust any result in the paper, edit this file only and re-run the
corresponding task script.
"""
import os

# ==================== Paths (normally no need to change) ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, 'input')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

CORPUS_FILE = os.path.join(INPUT_DIR, 'tang_poems_cleaned.txt')      # format: author#title#text, one poem per line
POET_YEAR_FILE = os.path.join(INPUT_DIR, 'poet_years_detailed.xlsx') # required columns: poet, birth/death years, work count, period
CHAR_DICT_FILE = os.path.join(INPUT_DIR, 'char_values_extended.txt')
BIGRAM_DICT_FILE = os.path.join(INPUT_DIR, 'imagery_values_extended.txt')
CANON_FILE = os.path.join(INPUT_DIR, 'textbook_items_110.csv')

# ==================== Poets and periods ====================
POETS = ['李白', '王维', '杜甫', '白居易']
POET_EN = {'李白': 'Li Bai', '王维': 'Wang Wei', '杜甫': 'Du Fu', '白居易': 'Bai Juyi'}
PERIODS = ['初唐', '盛唐', '中唐', '晚唐']
PERIOD_EN = {'初唐': 'Early', '盛唐': 'High', '中唐': 'Mid', '晚唐': 'Late'}

# ==================== Seed characters (identical to Supplementary Appendix A; do not change) ====================
POS_SEEDS = {'欢','乐','喜','笑','欣','愉','悦','畅','骄','怡','悠','旷','兴','安','和','暖','晴','芳','馨',
             '壮','豪','雄','奔','腾','飞','扬','驰','跃','清','明','朗','秀','丽','艳','华','荣','茂','盛',
             '圆','满','聚','合','逢','遇','成','功','春','花','新','佳'}
NEG_SEEDS = {'愁','悲','哀','泣','泪','苦','恨','伤','惨','戚','寂','寞','孤','独','憔','悴','倦','疲','惆','怅',
             '冷','凉','萧','瑟','凋','零','落','枯','死','黯','淡','昏','暗','断','绝','离','别','散','逝',
             '亡','惊','恐','惧','忧','痛','怨','寒','凄','惶','惘'}
ALL_SEEDS = POS_SEEDS | NEG_SEEDS

# ==================== Non-poetic function words (removed by the poeticity screen; extendable) ====================
# Negation/interrogative/auxiliary bigrams: frequent but not imageries; removed from all teaching lists
EXCLUDE = {'不见', '不知', '何处', '唯有', '沈沈', '须臾', '次第', '安可',
           '不可', '无所', '不得', '便是', '应是', '如何', '可以', '无以', '安得','一杯','不能','不可','谁与','何以','何用','何妨','自从',
           '无定','自从','未曾','不待','谁知','不胜','不忍','何须','胡为','谁怜','自怜','使我','未必','岂是','一曲','多少','今已','疑是','不识','古来','一身',
           '那堪','何由','何足'}

# ==================== Thresholds (identical to Section 4 of the paper; do not change) ====================
MIN_CHAR_FREQ = 50      # characters below this window count get value 0
MIN_BIGRAM_FREQ = 10    # bigrams below this in-window count get context score 0
DOUBLE_EVIDENCE_VAL = 0.3    # double-evidence filter: lower bound on |imagery value|
DOUBLE_EVIDENCE_CHAR = 0.2   # double-evidence filter: lower bound on |sum of constituent character values|

# ==================== Word lists for the figures (edit here to change words) ====================
# Task 4: shared-imagery matrix (paper Figure 4)
MATRIX_WORDS = ['春风', '少年', '青山', '天子', '天地', '长安', '洛阳', '落日', '故人', '惆怅', '寂寞']
# Task 4: ego networks (paper Figure 6): centre word and poets (all four poets, 2×2 panels)
EGO_TARGET = '故人'
EGO_POETS = ['李白', '王维', '杜甫', '白居易']
EGO_TOP_K = 8          # number of neighbours displayed
EGO_MIN_CO = 2          # neighbours must share at least this many poems with the centre
# Task 3: imagery trajectories (positive-leaning group):
TRAJ_POS_WORDS = ['英雄', '莲花', '花开', '杨柳', '春色']
# Task 3: negative-leaning group:
TRAJ_NEG_WORDS = ['白发', '夕阳', '伤心', '凄凉', '憔悴']
TRAJ_WORDS = TRAJ_POS_WORDS + TRAJ_NEG_WORDS   # internal use

# Task 6: character-level co-occurrence comparison (paper Figure 5) target characters
CHAR_TARGETS = ['酒', '雨', '花', '月']
CHAR_TOP_K = 8        # neighbours shown per poet per character
CHAR_MIN_CO = 2        # neighbours must share at least this many poems with the target
CHAR_EXCLUDE_CONTAINS = True   # True = drop bigrams containing the target character itself
                               # (trivial co-occurrence); set False to inspect word formation

# Dynasty-curve palette: 'classic' blue / 'warm' ochre / 'forest' teal-gold
FIG6_PALETTE = 'warm'
PALETTES = {
    'classic': {'line': '#2e5d8a', 'err': '#9dbfd9', 'band': '#f6d5d5', 'label': '#b03a30'},
    'warm':    {'line': '#8c3b2e', 'err': '#d9a583', 'band': '#e8e3cf', 'label': '#6b4f2a'},
    'forest':  {'line': '#1f5f5b', 'err': '#8fb8ad', 'band': '#efe0c0', 'label': '#7a4a1e'},
}

# ==================== Chinese-to-English gloss table (used by figures and tables; add new words here) ====================
# Keys are the Chinese imagery words under study (the data objects themselves);
# values are their English glosses. Do not translate the keys.

# ==================== Chinese-English gloss table (used by figures and tables; add new words here) ====================

TRANS = {
    '瑶台':'Jasper Terrace','九天':'Ninth Heaven','梦魂':'Dreaming Soul','梦里':'In Dreams','谢公':'Lord Xie',
    '东海':'Eastern Sea','湘水':'River Xiang','明主':'Enlightened Sovereign','秋月':'Autumn Moon','功成':'Accomplishment',
    '苍梧':'Cangwu','落叶':'Falling Leaves','焚香':'Burning Incense','云霞':'Clouds and Mist','才子':'Talented Scholar',
    '陌上':'By the Path','桃源':'Peach Blossom Spring','汉家':'Han Court','苍茫':'Boundless','日暮':'At Dusk',
    '落日':'Setting Sun','衣冠':'Capped and Gowned','旌旗':'Banners','君王':'The Sovereign','故国':'Homeland',
    '巫峡':'Wu Gorge','他乡':'Foreign Land','孤城':'Lonely City','乾坤':'Heaven and Earth','英雄':'Hero',
    '昆仑':'Kunlun','多病':'Sickly','圣朝':'Sage Dynasty','蛟龙':'Flood Dragon','鸿雁':'Swan Goose','万国':'Myriad States',
    '思量':'Pondering','枕上':'On the Pillow','园林':'Gardens','琵琶':'Pipa Lute','玲珑':'Exquisite','笙歌':'Songs and Pipes',
    '今宵':'Tonight','名利':'Fame and Gain','寒食':'Cold Food Festival','回头':'Looking Back','池上':'By the Pond',
    '踟蹰':'Lingering Steps','春风':'Spring Wind','黄金':'Gold','天地':'Heaven and Earth','桃李':'Peach and Plum',
    '浮云':'Floating Clouds','长安':"Chang'an",'故人':'Old Friend','金陵':'Jinling','天子':'Son of Heaven',
    '洛阳':'Luoyang','惆怅':'Melancholy','寂寞':'Loneliness','天下':'All under Heaven','颜色':'Countenance',
    '秋风':'Autumn Wind','萧萧':'Rustling Bleak','一杯':'A Cup','富贵':'Wealth and Honor','凉风':'Cool Breeze',
    '萧条':'Bleakness','风景':'Scenery','杯酒':'A Cup of Wine','少年':'Youth','青山':'Green Hills','悠悠':'Leisurely',
    '一杯酒':'A Cup of Wine','劝君':'I Urge You','不能':'Cannot','门前':'Before the Gate','青青':'Green and Fresh',
    '夫子':'The Master','谁与':'With Whom','双阙':'Twin Watchtowers','天涯':'Edge of the Sky','游子':'Wanderer',
    '相逢':'Meeting','何以':'By What','新诗':'New Poems','苍苍':'Vast Gray',
    # trajectory words for the paper figures
    '凤凰':'Phoenix','莲花':'Lotus','春色':'Spring Scenery','花开':'Flowers Blooming','酒杯':'Wine Cup',
    '白发':'White Hair','杨柳':'Willows','烽火':'Beacon Fire','夕阳':'Evening Sun','孤舟':'Lonely Boat',
    '伤心':'Wounded Heart','凄凉':'Desolation','憔悴':'Haggard',
    # target characters for the character-level co-occurrence task
    '酒':'Wine','雨':'Rain','花':'Flowers','月':'Moon',
    # words used in the textbook-canon section
    '万里':'Ten Thousand Miles','黄河':'The Yellow River','桃花':'Peach Blossom','白云':'White Clouds',
    '芙蓉':'Lotus Hibiscus','可怜':'Pitiable','江南':'Jiangnan','江水':'River Water','纷纷':'One after Another',
    '明月':'Bright Moon',
    # additional imagery glosses (batch 1)
    '主人':'Host','生死':'Life and Death','男儿':'True Man','芳菲':'Flowers and Fragrance','三月':'Third Month',
    '帝乡':'Imperial Capital','三尺':'Three-foot Sword','南国':'Southern Land','高楼':'High Tower','十里':'Ten Leagues',
    '关山':'Mountain Passes','咸阳':'Xianyang','今日':'Today','走马':'Galloping Horse','单于':'Chanyu',
    '他人':'Others','骑马':'Riding Horse','公卿':'Nobles and Ministers','朱门':'Red Gates','二十':'Twenty Years',
    '花落':'Falling Flowers','世间':'Mortal World','梅花':'Plum Blossom','吟诗':'Chanting Poetry','绿苔':'Green Moss',
    '莺啼':'Orioles Singing','欢娱':'Joy and Pleasure','四邻':'Four Neighbors','忘机':'Free from Mundane Cares',
    '太平':'Great Peace','年少':'Tender Youth','东西':'East and West','巫山':'Mount Wu','阳台':'Lover\'s Balcony',
    '尘埃':'Dust and Dirt','行乐':'Pursuing Pleasure','阑干':'Tear-stained Railing','四十':'Forty Years',
    '凄凄':'Dreary and Sad','潺湲':'Gurgling Stream','马嘶':'Horse\'s Neigh','断续':'Broken and Intermittent',
    '芳草':'Fragrant Grass','飞去':'Flying Away','溪水':'Mountain Stream','冥冥':'Dim and Dark','几时':'When',
    '杜陵':'Duling Mound','翡翠':'Jade-green Kingfisher','佳期':'Happy Rendezvous','萧索':'Desolate and Bleak',
    '独坐':'Sitting Solitary','淹留':'Long Lingering','同心':'Like-minded Hearts','叹息':'Heavy Sighing',
    '意气':'Lofty Spirits','青苔':'Mossy Green','婵娟':'Lovely Moon','鸳鸯':'Mandarin Ducks','暮雨':'Dusk Rain',
    '经过':'Passing By','三十':'Thirty Years','相随':'Following Together','江头':'Riverbank','满眼':'Filling the Eye',
    '神仙':'Immortals','细雨':'Misty Drizzle','宫殿':'Palace Halls','门外':'Outside the Gate','佳人':'Beautiful Lady',
    '尽日':'Whole Day Long','百战':'Hundred Battles','重重':'Layered upon Layered','楚客':'Exile of Chu',
    '红粉':'Rosy-cheeked Beauties','春色':'Spring Radiance','到处':'Everywhere','芙蓉':'Hibiscus','青楼':'Azure Bower',
    '年华':'Youthful Years','中原':'Central Plain','翠微':'Green Mountain Haze','河汉':'Silver River (Milky Way)',
    '昨日':'Yesterday','相忆':'Mutual Longing','边城':'Frontier Town','长沙':'Changsha','风吹':'Wind Blowing',
    '山水':'Mountains and Waters','王孙':'Noble Scion','竹林':'Bamboo Grove','猿声':'Gibbon\'s Cry','知音':'True Bosom Friend',
    '悠然':'Carefree and Leisurely','秋草':'Autumn Grasses','封侯':'Earldom and Title','苦辛':'Toil and Bitterness',
    '望乡':'Gazing Homeland','霓裳':'Rainbow Garments','清光':'Pure Moonlight','宫中':'Within the Palace','微雨':'Light Rain',
    '秋声':'Sounds of Autumn',
    # additional imagery glosses (batch 2)
    '高阁':'Lofty Pavilion','东海':'Eastern Sea','鱼龙':'Fish and Dragon','红粉':'Rosy Cheeks','山水':'Mountains and Waters',
    '南国':'Southern Realm','昨日':'Yesterdays','三月':'Third Month','丈夫':'Great Man','歌舞':'Song and Dance',
    '劝君':'I Urge You','杯酒':'Cup of Wine','黄金':'Yellow Gold','门前':'Before the Gate','洛阳':'Luoyang',
    '青青':'Lush and Green','苍茫':'Vast and Boundless','送君':'Farewell to You','飞鸟':'Soaring Bird','寂寞':'Loneliness',
    '夫子':'The Master','双阙':'Twin Watchtowers','天涯':'The Sky\'s Edge','苍苍':'Vast and Gray',
    '游子':'Wandering Traveler','相逢':'Encounter','新诗':'New Verse','读书':'Reading Books','从容':'Composed and Unhurried',
    '花枝':'Blossom-laden Bough','眼前':'Before the Eyes','桃花':'Peach Blossom','江水':'River Waters','携手':'Hand in Hand',
    '所思':'The Beloved','蹉跎':'Wasted Years','相思':'Mutual Longing','千里':'A Thousand Miles','花落':'Falling Blossoms',
    # additional imagery glosses (batch 3)
    '吾师':'My Master','紫微':'Purple Tenuity (Star of the Emperor)','将军':'General','流水':'Flowing Streams',
    '谁家':'Whose House','辛苦':'Hardship and Toil','故乡':'Hometown'
}
