"""
Bot System Constants

定数とグローバル設定値を集約
"""

# API Endpoints
BASE_URL = "https://drrrkari.com"
LOGIN_URL = f"{BASE_URL}/"
LOUNGE_URL = f"{BASE_URL}/lounge/"

# Bot Configuration
MAX_SEARCH_RETRIES = 10
ACTIVITY_TIMEOUT = 300  # 5 minutes

# Available bot icons (26 unique icons for parallel bots)
AVAILABLE_ICONS = [
    "girl", "moza", "tanaka", "kanra", "usa", "gg", "orange", "zaika", "setton", "zawa",
    "bakyura", "mika", "numabuto", "numabuto_B", 
    "muffler_girl", "muffler_moza", "muffler_tanaka", "muffler_kanra", "muffler_usa", 
    "muffler_gg", "muffler_orange", "muffler_zaika", "muffler_setton", "muffler_zawa", 
    "muffler_bakyura", "muffler_mika"
]

# SNS-style natural names for bots
SNS_NAMES = [
    "ゆうき", "あおい", "はるか", "りょう", "さくら", "まな", "ゆい", "そら",
    "ひなた", "りく", "めい", "あかり", "そうた", "はると", "ゆうま", "ゆうと",
    "れん", "かい", "こはる", "ひまり", "さな", "ももか", "りお",
    "まゆ", "のん", "りん", "えみ", "なつ", "みお", "あい", "ゆき", "さき",
    "ちひろ", "かえで", "まい", "なな", "ゆな", "あやか", "ゆうこ", "れいな",
    "Rui", "Kai", "Ren", "Mio", "Rio", "Leo", "Sora", "Luna",
    "Haru", "Yuki", "Nana", "Rin", "Mei", "Aoi", "Rei", "Saki",
    "ゆうちゃん", "りーちゃん", "あおくん", "まなみん", "そらさん", "めいめい",
    "ゆいぴ", "はるぴ", "まゆゆ", "りんりん", "なっちゃん", "さっちゃん"
]

# Bot Status States
STATUS_SEARCHING = "Searching"
STATUS_IN_ROOM = "In Room"
STATUS_FAILED = "Failed"
