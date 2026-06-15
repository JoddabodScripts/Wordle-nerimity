"""Word lists and solution selectors for the Wordle bot."""

WORDS = [
    "APPLE","ROUTE","CHAIR","BRICK","PLANT","MOUSE","TRACK","LIGHT","SOUND","CLOUD",
    "WATER","STONE","FRAME","FABLE","FAINT","FAIRY","FANCY","FERAL","FERNS","FJORD",
    "FLAIR","FLINT","FLOUR","FLUKE","FOAMY","FORGE","FROST","GAZER","GHOUL","GLADE",
    "GLINT","GRAZE","GRIME","GUSTO","HABIT","HAVEN","HAZEL","HINGE","HUMID","HUSKY",
    "IVORY","JOLLY","JUMBO","KNEAD","LATCH","LILAC","LITHE","MANGO","MAPLE","MARSH",
    "MIRTH","MISTY","MOCHA","MOSSY","NAVAL","NEXUS","NUDGE","OAKEN","OLIVE","ONSET",
    "OPERA","ORBIT","OTTER","PADDY","PARCH","PASTA","PECAN","PERCH","PETAL","PHONE",
    "PLAZA","PLEAT","PLUME","POISE","POLAR","POPPY","PULSE","QUART","QUEST","RANCH",
    "RAVEN","RELIC","RHYME","RIPEN","ROAST","ROBIN","ROGUE","SALSA","SATIN","SAVOR",
    "SCALD","SCOUT","SHALE","SHEEN","SHORE","SMILE","SNARE","SOLAR","SPARK","SPICE",
    "SPORE","SPRIG","SQUID","STAIR","STEAM","STING","SWIRL","TANGO","THORN","TIDAL",
    "TEMPO","TOPAZ","TORCH","TRAIL","TULIP","TWEAK","UMBRA","VAPOR","VELDT","VELUM",
    "VERGE","VIGOR","VINYL","VISTA","WAFER","WALTZ","WIDEN","WILDS","WOVEN","YACHT",
    "CRANE","BREAD","SUGAR","METAL","SHINE","FLAME","GRASS","ROUND","SHARP","DRINK",
    "WRITE","WORLD","PEARL","RIVER","ABOUT","ABOVE","ACTOR","ACUTE","ADAPT","ADULT",
    "AFTER","AGAIN","AGREE","AHEAD","ALARM","ALBUM","ALERT","ALIEN","ALIVE","ALLOW",
    "ALONE","ALONG","ALTER","AMONG","ANGEL","ANGER","ANGLE","ANGRY","APART","APPLY",
    "ARENA","ARGUE","ARISE","ARMOR","ARRAY","ASIDE","ASSET","AUDIO","AWARE","AWFUL",
    "BADGE","BAKER","BASIC","BEACH","BEGAN","BEGIN","BEGUN","BEING","BELOW","BENCH",
    "BERRY","BIRTH","BLACK","BLAME","BLIND","BLOCK","BLOOD","BOARD","BOOST","BOUND",
    "BRAIN","BRAND","BRAVE","BREAK","BRIEF","BRING","BROAD","BROWN","BUILD","BUYER",
    "CABLE","CARRY","CATCH","CAUSE","CHAIN","CHART","CHASE","CHEAP","CHECK","CHEER",
    "CHEST","CHIEF","CHILD","CIVIL","CLAIM","CLASS","CLEAN","CLEAR","CLERK","CLICK",
    "CLIMB","CLOCK","CLOSE","COACH","COAST","COLOR","COULD","COUNT","COURT","COVER",
    "CRAFT","CRASH","CREAM","CRIME","CROSS","CROWD","CROWN","CURVE","CYCLE","DANCE",
    "DATED","DEALT","DEATH","DEBUT","DELAY","DEPTH","DOING","DOUBT","DOZEN","DRAFT",
    "DRAMA","DRAWN","DREAM","DRESS","DRIVE","EARLY","EARTH","EIGHT","ELITE","EMPTY",
    "ENJOY","ENTER","ENTRY","EQUAL","ERROR","EVENT","EVERY","EXACT","EXTRA","FAITH",
    "FALSE","FAULT","FIBER","FIELD","FIFTH","FIFTY","FIGHT","FINAL","FIRST","FIXED",
    "FLASH","FLEET","FLOOR","FOCUS","FORCE","FORTH","FORTY","FOUND","FRANK","FRESH",
    "FRONT","FRUIT","FULLY","FUNNY","GIANT","GIVEN","GLASS","GLOBE","GOING","GRAND",
    "GRANT","GREAT","GREEN","GROSS","GROUP","GUARD","GUESS","GUEST","GUIDE","HAPPY",
    "HARRY","HEART","HEAVY","HENCE","HONEY","HORSE","HOTEL","HOUSE","HUMAN","IDEAL",
    "IMAGE","INDEX","INNER","INPUT","ISSUE","JEANS","JOINT","JUDGE","KNOWN","LABEL",
    "LARGE","LASER","LATER","LAUGH","LAYER","LEARN","LEAST","LEAVE","LEGAL","LEVEL",
    "LIMIT","LOCAL","LOGIC","LOOSE","LOWER","LUCKY","LUNCH","MAJOR","MAKER","MARCH",
    "MATCH","MAYBE","MEANT","MEDIA","MIGHT","MINOR","MODEL","MONEY","MONTH","MORAL",
    "MOTOR","MOUNT","MOUTH","MOVED","MOVIE","MUSIC","NEEDS","NEVER","NEWLY","NIGHT",
    "NINTH","NOBLE","NOISE","NORTH","NOTED","NOVEL","NURSE","OCCUR","OCEAN","OFFER",
    "OFTEN","OLDER","ONION","ORDER","OTHER","OUGHT","PAINT","PANEL","PAPER","PARTY",
    "PEACE","PHASE","PIANO","PILOT","PITCH","PLACE","PLAIN","PLANE","POINT","POWER",
    "PRESS","PRICE","PRIDE","PRIME","PRINT","PRIOR","PRIZE","PROOF","PROUD","QUEEN",
    "QUICK","QUIET","QUITE","RADIO","RAISE","RANGE","RAPID","RATIO","REACH","READY",
    "REFER","RIGHT","RISKY","RIVAL","RULER","RURAL","SCALE","SCENE","SCOPE","SCORE",
    "SENSE","SERVE","SEVEN","SHARE","SHIFT","SHOCK","SHOOT","SHORT","SHOWN","SIGHT",
    "SINCE","SIXTH","SKILL","SLEEP","SMALL","SMART","SMOKE","SOLID","SOLVE","SORRY",
    "SOUTH","SPEAK","SPEED","SPEND","SPENT","SPLIT","SPORT","STAFF","STAGE","STAKE",
    "STAND","START","STATE","STEEL","STICK","STILL","STOCK","STORE","STORM","STORY",
    "STRIP","STUCK","STUDY","STYLE","SWEET","TABLE","TAKEN","TASTE","TEACH","TEETH",
    "THANK","THEME","THERE","THICK","THING","THINK","THIRD","THOSE","THREE","THREW",
    "THROW","TIGHT","TIMES","TIRED","TITLE","TODAY","TOPIC","TOTAL","TOUCH","TOUGH",
    "TOWER","TRADE","TRAIN","TREAT","TRIAL","TRIED","TRUCK","TRULY","TRUST","TRUTH",
    "TWICE","UNDER","UNION","UNITY","UNTIL","UPPER","UPSET","URBAN","USAGE","USUAL",
    "VALUE","VIDEO","VISIT","VITAL","VOICE","WASTE","WATCH","WHEEL","WHERE","WHILE",
    "WHITE","WHOLE","WHOSE","WOMAN","WOMEN","WORRY","WORTH","WOULD","WRONG","YIELD","YOUNG",
]

_GENSHIN_PLAYABLE = [
    "Aino","Albedo","Alhaitham","Aloy","Amber","Arataki Itto","Arlecchino","Baizhu",
    "Barbara","Beidou","Bennett","Candace","Charlotte","Chasca","Chevreuse","Chiori",
    "Chongyun","Citlali","Clorinde","Collei","Columbina","Cyno","Dahlia","Dehya",
    "Diluc","Diona","Dori","Durin","Emilie","Escoffier","Eula","Faruzan","Fischl",
    "Flins","Freminet","Furina","Gaming","Ganyu","Gorou","Hu Tao","Iansan","Ifa",
    "Illuga","Ineffa","Jahoda","Jean","Kachina","Kaedehara Kazuha","Kaeya",
    "Kamisato Ayaka","Kamisato Ayato","Kaveh","Keqing","Kinich","Kirara","Klee",
    "Kujou Sara","Kuki Shinobu","Lan Yan","Lauma","Layla","Lisa","Lynette","Lyney",
    "Mavuika","Mika","Mona","Mualani","Nahida","Navia","Nefer","Neuvillette","Nilou",
    "Ningguang","Noelle","Ororon","Qiqi","Raiden Shogun","Razor","Rosaria",
    "Sangonomiya Kokomi","Sayu","Sethos","Shenhe","Shikanoin Heizou","Sigewinne",
    "Skirk","Sucrose","Tartaglia","Thoma","Tighnari","Traveler","Varesa","Varka",
    "Venti","Wanderer","Wonderland Manekin","Wriothesley","Xiangling","Xianyun",
    "Xiao","Xilonen","Xingqiu","Xinyan","Yae Miko","Yanfei","Yaoyao","Yelan",
    "Yoimiya","Yumemizuki Mizuki","Yun Jin","Zhongli","Zibai",
]

_GENSHIN_HARBINGERS = [
    "Capitano","Dottore","Pantalone","Pierro","Pulcinella","Sandrone","Scaramouche","Signora",
]

_GENSHIN_ALIAS_OVERRIDES = {
    "AINO": "AINOO","ALOY": "ALOYY","ARATAKIITTO": "ITTOO","CYNO": "CYNOO",
    "DORI": "DORII","EULA": "EULAA","HUTAO": "HUTAO","IFA": "IFAAA",
    "JEAN": "JEANN","KAEDEHARAKAZUHA": "KAZUH","KAMISATOAYAKA": "AYAKA",
    "KAMISATOAYATO": "AYATO","KLEE": "KLEEE","KUJOUSARA": "SARAA",
    "KUKISHINOBU": "SHINO","LANYAN": "LANYA","LISA": "LISAA","MIKA": "MIKAA",
    "MONA": "MONAA","QIQI": "QIQII","RAIDENSHOGUN": "SHOGU",
    "SANGONOMIYAKOKOMI": "KOKOM","SHIKANOINHEIZOU": "HEIZO","VENTI": "VENTI",
    "XIAO": "XIAOO","YAEMIKO": "MIKOO","YUMEMIZUKIMIZUKI": "MIZUK","YUNJIN": "YUNJI",
}


def _normalize_genshin(name: str) -> str:
    import re
    return re.sub(r"[^A-Za-z]", "", name).upper()


def _to_five_letter_alias(name: str) -> str:
    normalized = _normalize_genshin(name)
    override = _GENSHIN_ALIAS_OVERRIDES.get(normalized)
    if override:
        return override
    if len(normalized) >= 5:
        return normalized[:5]
    return normalized.ljust(5, normalized[-1] if normalized else "X")


def _build_unique_pool(names: list) -> list:
    used: set = set()
    pool = []
    for name in names:
        alias = _to_five_letter_alias(name)
        if not alias.isalpha() or len(alias) != 5:
            raise ValueError(f"Invalid alias for {name}: {alias}")
        if alias in used:
            raise ValueError(f"Duplicate alias for {name}: {alias}")
        used.add(alias)
        pool.append(alias)
    return pool


GENSHIN_WORDS = _build_unique_pool(_GENSHIN_PLAYABLE + _GENSHIN_HARBINGERS)

_VOCALOID_NAMES = [
    "Hatsune Miku", "Kagamine Rin", "Kagamine Len", "Megurine Luka",
    "KAITO", "MEIKO", "Gumi", "IA", "Neru", "Fukase",
    "Oliver", "Lily", "Otomatay", "Yukari", "Gakupoid",
    "Nekomura Iroha", "Kasane Teto", "Miki", "VY1",
]

_VOCALOID_ALIAS_OVERRIDES = {
    "HATSUNEMIKU": "MIKUU", "KAGAMINERIN": "RINNN", "KAGAMINELEN": "LENNN",
    "MEGURINELUKA": "LUKAA", "KAITO": "KAITO", "MEIKO": "MEIKO",
    "GUMI": "GUMII", "IA": "IAAAA", "NERU": "NERUU",
    "FUKASE": "FUKAS", "OLIVER": "OLIVE", "LILY": "LILYY",
    "OTOMATAY": "OTOMA", "YUKARI": "YUKAR", "GAKUP": "GAKUP",
    "NEKOMURAIROHA": "IROHA", "KASANETETO": "TETOO",
    "MIKI": "MIKII", "VY1": "VY1YY",
}

def _normalize_vocaloid(name: str) -> str:
    import re
    return re.sub(r"[^A-Za-z]", "", name).upper()

def _to_five_letter_vocaloid(name: str) -> str:
    normalized = _normalize_vocaloid(name)
    override = _VOCALOID_ALIAS_OVERRIDES.get(normalized)
    if override:
        return override
    if len(normalized) >= 5:
        return normalized[:5]
    return normalized.ljust(5, normalized[-1] if normalized else "X")

def _build_vocaloid_pool(names: list) -> list:
    used: set = set()
    pool = []
    for name in names:
        alias = _to_five_letter_vocaloid(name)
        if not alias.isalpha() or len(alias) != 5:
            raise ValueError(f"Invalid alias for {name}: {alias}")
        if alias in used:
            raise ValueError(f"Duplicate alias for {name}: {alias}")
        used.add(alias)
        pool.append(alias)
    return pool

VOCALOID_WORDS = _build_vocaloid_pool(_VOCALOID_NAMES)

EVENT_WORDS: dict = {
    "undertale": ["FRISK","CHARA","TORIE","ASRIE","ASGOR","SANSS","PAPYR","UNDYN",
                  "ALPHY","TEMMI","METAT","FROGG","OZONE","RESET","GENOC","MERCY","SOULS","FLOWE"],
    "deltarune": ["KRISS","RALSE","SUSIE","LANCE","NOELL","QUEEN","ROUXL","JEVIL",
                  "SPADE","HEART","LIGHT","DARKN","CYBER","CASTL","PIANO","KNIGH"],
    "forsaken":  ["NOOBB","007N7","VERON","SHEDL","G1337","TWOTM","CHANC","ELLOT",
                  "DUSEK","BUILD","TAPHS","JANEE","SLASH","C00LK","JOHND","NOLII",
                  "1X1X1","G0666","NOSFE"],
    "genshin":   GENSHIN_WORDS,
    "minecraft": ["STEVE","CREEP","ENDER","BLOCK","DIRT!","GRASS","SWORD","PICKX",
                  "BIOME","VILLG","CRAFT","SMELT","SHOVL","REDST"],
    "newyear":   ["HAPPY","CHEER","PARTY","SPARK","CIDER","TOAST","RESOL","CLOCK",
                  "COUNT","NOISE","LIGHT"],
    "vocaloid":  VOCALOID_WORDS,
}


def _fnv1a32(s: str) -> int:
    h = 0x811C9DC5
    for ch in s:
        h ^= ord(ch)
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h


def get_daily_index(date=None) -> int:
    from datetime import date as _date, timezone
    import datetime
    if date is None:
        date = datetime.datetime.now(timezone.utc).date()
    epoch = _date(2022, 1, 1)
    diff = (date - epoch).days
    return (diff % len(WORDS) + len(WORDS)) % len(WORDS)


def get_today_solution(date=None) -> str:
    return WORDS[get_daily_index(date)]


def get_user_daily_solution(user_id: str, date_key: str, run_id: int = 0) -> str:
    seed = f"{date_key}:{user_id}:{run_id}"
    idx = _fnv1a32(seed) % len(WORDS)
    return WORDS[idx]


def get_user_event_solution(user_id: str, date_key: str, run_id: int = 0, event_key: str = "") -> str:
    pool = EVENT_WORDS.get(event_key, [])
    if not pool:
        return get_user_daily_solution(user_id, date_key, run_id)
    seed = f"{date_key}:{user_id}:{run_id}:{event_key}"
    idx = _fnv1a32(seed) % len(pool)
    return pool[idx]

def is_valid_word(word: str) -> bool:
    """Check if a word is valid for Wordle gameplay."""
    return word.upper() in WORDS
