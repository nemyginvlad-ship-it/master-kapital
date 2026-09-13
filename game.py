import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import pandas as pd
import random, json, os, math, base64
from datetime import datetime

st.set_page_config(page_title="Мастер Капитала | Экономический симулятор", page_icon="🪆", layout="wide")

MONTH_SEASON = [0.85, 0.90, 1.00, 1.00, 1.05, 1.00, 0.90, 0.85, 1.10, 1.05, 1.10, 1.25]
MONTH_NAMES = ["Янв", "Фев", "Мар", "Апр", "Май", "Июн", "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"]
BASE_MARKET = 1400
START_OPTIONS = {10000.0: "На грани (10 000 ₽)", 20000.0: "Стандарт (20 000 ₽)", 40000.0: "Комфорт (40 000 ₽)"}
START_CASH = 10000.0
START_ASSETS = 25000.0
CAP_NORM = 100.0
DEPRECIATION = 0.017
STORAGE_COST = 1.5
MATERIAL_UNIT = 6.0
FIXED_COST = 1000.0
DEPOSIT_RATE = 0.008
LOAN_RATE = 0.015
LOAN_LIMIT = 50000.0
START_PRICE = 30.0
QUALITY_DECAY = 3.0
RND_GAIN = 0.001
PATENT_THRESHOLD = 30000.0
PATENT_PITY = 60000.0
PATENT_CHANCE = 0.5
PATENT_QUALITY = 15.0
PATENT_COST_CUT = 0.10
PATENT_MPI_BONUS = 30
ROYALTY_RATE = 0.005
SUBSIDY_MONTHS = [6, 12]
ANNOUNCE_MONTHS = [5, 11]
GRANT_FIXED = 10000.0
CORP_FEE = 5000.0
RESCUE_CASH = 3000.0
BRAND_QUALITY = 120.0
BRAND_REPUTATION = 5.0
BRAND_BONUS = 1.05
DEC_PREMIUM_QUALITY = 110.0
DEC_PREMIUM_MULT = 1.2
REP_ATTRACT = 0.04
REP_MKT = 0.05
REP_MKT_CAP = 0.5
REP_EROSION = 0.01
SOC_DECAY = 0.95
SOC_DIV = 6000.0
CHARITY_RECS = {1: ("Школы и детсады", 1.2), 2: ("Больница и дом престарелых", 1.0),
                3: ("Музей и наследие", 0.8), 4: ("Фестивали и спорт", 0.6)}
CHARITY_TIERS = [(300, "участник"), (1000, "попечитель"), (3000, "меценат")]
SUB_TYPE_NAMES = {1: "бюджетный грант", 2: "софинансирование оборудования", 3: "льготный кредит"}
PAL = ["#462446", "#b05f6d", "#eb6b56", "#ffc153", "#47b39d"]
PROFS = ["assemblers", "turners", "painters", "managers"]
PROF_RU = {"assemblers": "Сборщики", "turners": "Токари", "painters": "Мастера росписи", "managers": "Управленцы"}
LABOR_WAGE = {"assemblers": 80, "turners": 100, "painters": 150, "managers": 250}
POOL_START = {"assemblers": 50, "turners": 30, "painters": 10, "managers": 4}
NOVICE_WAGE = 60
TRAIN_MONTHS = 3
TRAIN_COST = 1200
MENTOR_BONUS = 0.5
MANAGER_SPAN = 8
TENSION_STRIKE = 70
STRIKE_PROD_MULT = 0.40
UNION_WORKERS = 20
UNION_CHANCE = 0.25
UNION_WAGE_UP = 0.10
COALITION_SHARE = 0.35
COALITION_GAP = 1.25
COALITION_CHANCE = 0.20
COALITION_COOLDOWN = 3
TENDER_MONTHS = [3, 6, 9, 12]
TENDER_ADVANCE = 0.30
TENDER_PENALTY = 0.10
TENDER_CUSTOMERS = [("Администрация округа", 0.10, 1.00, 90),
                    ("Минкульт области", 0.16, 1.25, 110),
                    ("Программа «Русский сувенир»", 0.22, 1.10, 100)]

TAX_REGIMES = {"usn6": "УСН «Доходы» 6%", "usn15": "УСН «Доходы-расходы» 15% (мин. 1%)",
               "osno": "ОСНО (НДС 20% + прибыль 25%)"}

# (вероятность, текст, спрос, затраты, ставка, прогноз-оверрайд, спецфлаг)
EVENTS = [
    (0.40, "Обычный месяц: рынок спокоен.", 1.0, 1.0, 0, "stable", None),
    (0.05, "Экономический бум: покупатели активно скупают игрушки!", 1.3, 1.0, 0, None, None),
    (0.05, "Кризис: покупатели экономят на игрушках.", 0.7, 1.0, 0, None, None),
    (0.02, "Стихийное бедствие в регионе: не до игрушек.", 0.5, 1.0, 0, None, None),
    (0.03, "Скачок цен на сырьё: затраты на производство +20%.", 1.0, 1.2, 0, None, None),
    (0.03, "Сырьё подешевело: затраты на производство −10%.", 1.0, 0.9, 0, None, None),
    (0.04, "Ставка ЦБ выросла: кредиты дороже, депозиты выгоднее.", 1.0, 1.0, 1, "negative", None),
    (0.04, "Ставка ЦБ снизилась: кредиты дешевле, депозиты менее выгодны.", 1.0, 1.0, -1, "positive", None),
    (0.03, "Пожар на заводе Hengda Paint (Китай): дефицит лаков и красок — покрытия +15%.", 1.0, 1.15, 0, None, None),
    (0.02, "Обязательная маркировка деревянных игрушек: коды на каждую единицу — затраты +3%.", 1.0, 1.03, 0, None, None),
    (0.03, "Пожары в Красноярском крае и Иркутской области: дефицит липы и берёзы — сырьё +8%.", 1.0, 1.08, 0, None, None),
    (0.03, "Запрет пластиковых игрушек из недружественных стран: покупатели переходят на деревянные!", 1.35, 1.0, 0, "positive", None),
    (0.03, "Рождаемость +8% — максимум за 10 лет: спрос на деревянные игрушки растёт.", 1.25, 1.0, 0, "positive", None),
    (0.03, "Всероссийский фестиваль «Матрёшка-фест» в Нижнем Новгороде: всплеск интереса к сувенирам!", 1.2, 1.0, 0, "positive", None),
    (0.02, "Контрафакт наводнил маркетплейсы дешёвыми подделками матрёшек.", 0.9, 1.0, 0, None, None),
    (0.03, "Экспортный контракт с Китаем на партию «русский сувенир»: спрос ×1.4.", 1.4, 1.0, 0, "positive", None),
    (0.02, "Забастовка перевозчиков: логистика дороже — затраты +10%.", 1.0, 1.10, 0, None, None),
    (0.03, "Мода на экостиль: деревянные игрушки в тренде!", 1.15, 1.0, 0, "positive", None),
    (0.03, "Туристический бум в регион: сувениры расходятся!", 1.12, 1.0, 0, "positive", None),
    (0.02, "Новый ГОСТ на деревянные игрушки: все платят за сертификацию, затраты +5%.", 1.0, 1.05, 0, None, "gost"),
    (0.02, "Сезонный грипп: персонал на больничных, производительность вниз.", 1.0, 1.0, 0, None, "sick"),
    (0.03, "Импортные лаки и краски дорожают из-за курса: покрытия +8%.", 1.0, 1.08, 0, None, None),
    (0.03, "Лесная биржа: штабели липы подешевели — сырьё −10%.", 1.0, 0.90, 0, None, None),
]
PERSONAL_EVENTS = ["recall", "viral", "master_leave", "corp_order", "warehouse_accident", "roscachestvo"]

def roll_event():
    r = random.random(); cum = 0.0
    for ev in EVENTS:
        cum += ev[0]
        if r <= cum:
            return ev
    return EVENTS[0]

BOT_NAMES = ["Альфа", "Бета", "Гамма", "Дельта", "Эпсилон", "Дзета", "Эта", "Тета", "Йота"]
BOT_STRATS = ["conservative", "aggressive", "balanced", "dumper", "niche",
              "financier", "adaptive", "expansionist", "follower"]

ACH_DEFS = [("first_profit", "Первая прибыль"), ("first_patent", "Первый патент"),
            ("first_tender", "Первый госконтракт"), ("survived_strike", "Пережил забастовку"),
            ("mecenate", "Меценат"), ("brand_holder", "Носитель бренда"),
            ("record_setter", "Рекордсмен отрасли"), ("big_employer", "Крупный работодатель"),
            ("master_quality", "Мастер качества (≥120)"),
            ("millionaire", "Миллионер"), ("clean_quarter", "Чистый квартал"),
            ("half_market", "Половина рынка"), ("sold_out", "Всё продано"),
            ("exporter", "Экспортёр"), ("reliable_supplier", "Надёжный поставщик"),
            ("full_staff", "Полный штат"), ("calm_collective", "Спокойный коллектив"),
            ("peoples_love", "Народная любовь"), ("quality_150", "Качество 150"),
            ("fast_start", "Быстрый старт"), ("marathon", "Марафонец")]
    

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Unbounded:wght@600;800&family=Lora:ital,wght@0,400;0,600;1,400&display=swap');
html{font-size:18px;-webkit-font-smoothing:antialiased}
body,.stApp{font-family:'Inter',system-ui,sans-serif;background:#f4f1ee}
h1,h2,h3,h4{font-family:'Unbounded',sans-serif;color:#462446}
table.rt td,.kpi-v,.paper td.num{font-feature-settings:"tnum"}
#MainMenu,footer{visibility:hidden}
section[data-testid="stMain"] label{font-weight:700;color:#462446;font-size:15px}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#462446 0%,#8a4f60 55%,#47b39d 135%)}
section[data-testid="stSidebar"] .stMarkdown,section[data-testid="stSidebar"] label{color:#f6eef2}
section[data-testid="stSidebar"] .stMarkdown h3{color:#ffc153}
section[data-testid="stSidebar"] div[data-testid="stExpander"]{background:#fff;border-radius:12px}
section[data-testid="stSidebar"] div[data-testid="stExpander"] .stMarkdown{color:#33253c}
section[data-testid="stSidebar"] div[data-testid="stExpander"] summary{color:#462446;font-weight:700}
section[data-testid="stMain"] div[data-testid="stExpander"] details{background:#fff8ec;border:2px solid #ffc153;border-radius:14px}
section[data-testid="stMain"] div[data-testid="stExpander"] summary{color:#462446;font-weight:700}
.strip{display:flex;align-items:center;gap:8px;background:var(--c);color:#fff;border-radius:10px;padding:8px 14px;font-weight:800;font-size:15px;margin:14px 0 8px}
.medal{display:inline-flex;width:26px;height:26px;border-radius:50%;align-items:center;justify-content:center;font-weight:800;color:#fff;font-size:14px}
.m1{background:linear-gradient(135deg,#ffd166,#e09f3e)}.m2{background:linear-gradient(135deg,#c0c8d8,#8a94a6)}.m3{background:linear-gradient(135deg,#d99a6c,#a66a44)}
.badge{font-size:10px;font-weight:800;padding:2px 8px;border-radius:999px;color:#fff;margin-left:6px}
.b-bot{background:#8a94a6}.b-dead{background:#c4493a}.b-brand{background:#47b39d}.b-heart{background:#e4579b}
.ach{display:inline-block;background:#eef7f2;border:1px solid #47b39d;color:#1f6f5a;border-radius:999px;padding:3px 10px;font-size:12px;font-weight:700;margin:2px}
.matr{width:64px;height:84px;margin:0 auto 8px;background:linear-gradient(180deg,#eb6b56 0%,#b05f6d 60%,#462446 100%);border-radius:50% 50% 46% 46%/62% 62% 38% 38%;position:relative}
.matr::before{content:'';position:absolute;top:12px;left:50%;transform:translateX(-50%);width:34px;height:30px;background:#f6efdb;border-radius:50%}
.matr::after{content:'';position:absolute;top:46px;left:50%;transform:translateX(-50%);width:26px;height:22px;background:rgba(255,193,83,.85);border-radius:50%}
.avatar{width:76px;height:76px;border-radius:50%;background:#ffc153;color:#462446;font:800 26px 'Unbounded',sans-serif;display:flex;align-items:center;justify-content:center;margin:6px auto 4px}
.avname{text-align:center;font:700 15px 'Unbounded',sans-serif;color:#fff;margin-bottom:12px}
.start-hero{background:linear-gradient(135deg,#462446 0%,#b05f6d 45%,#eb6b56 75%,#ffc153 110%);border-radius:24px;padding:34px 38px;color:#fff;margin-bottom:18px}
.sh-title{font:800 40px 'Unbounded',sans-serif;margin-top:6px}
.sh-sub{opacity:.85;font-size:14px;letter-spacing:.5px;text-transform:uppercase}
.sh-slogan{font:italic 600 18px 'Lora',serif;margin:12px 0 4px}
.sh-chips span{display:inline-block;background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.4);border-radius:999px;padding:6px 14px;margin:8px 8px 0 0;font-weight:600;font-size:14px}
.calcard{background:#fff;border-radius:18px;padding:14px 16px;margin:10px 0 14px;border:1px solid #e7dfe2}
.calhead{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;flex-wrap:wrap;gap:8px}
.calyear{font:800 16px 'Unbounded',sans-serif;color:#462446}
.callegend{font-size:11px;color:#8a7f86;display:flex;gap:12px;align-items:center}
.lg{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:4px;vertical-align:middle}
.lg-past{background:#e3e1de}.lg-cur{background:linear-gradient(135deg,#47b39d,#2b8a76)}.lg-fut{background:#fff3d9;border:1px solid #f0d9a8}
.calgrid{display:grid;grid-template-columns:repeat(12,1fr);gap:6px}
.calcell{border-radius:12px;padding:8px 4px;text-align:center}
.calnum{font:800 13px 'Inter',sans-serif;opacity:.8}
.calname{font:700 12px 'Inter',sans-serif;margin-top:2px}
.calmarks{height:14px;font-size:10px;margin-top:2px}
.cal-mk{color:#b08a2e}.cal-mk-a{color:#b05f6d}.cal-mk-d{color:#eb6b56}
.cal-past{background:#f2f1ef;color:#9a9590}.cal-cur{background:linear-gradient(135deg,#47b39d,#2b8a76);color:#fff}.cal-fut{background:#fff8ec;border:1px solid #f0e3c8;color:#b08a2e}
.kpi-row{display:flex;gap:14px;flex-wrap:wrap;margin:10px 0 16px}
.tile{flex:1;min-width:200px;background:#fff;border-radius:14px;padding:14px 16px;display:flex;gap:12px;align-items:center;border-top:5px solid var(--c)}
.tic{width:48px;height:48px;border-radius:12px;background:var(--c);display:flex;align-items:center;justify-content:center;font-size:23px;color:#fff;flex:none}
.kpi-l{font-size:11px;letter-spacing:.7px;text-transform:uppercase;color:#8a7f86;font-weight:700}
.kpi-v{font-size:25px;font-weight:800;color:#33253c}
.delta{font-size:12px;font-weight:800;padding:2px 9px;border-radius:999px}
.delta.up{background:#e2f4ef;color:#2b8a76}.delta.down{background:#fbe3de;color:#c4493a}
div[data-testid="stTabs"] [data-baseweb="tab"]{border-radius:999px;margin:4px 6px 4px 0;padding:7px 20px;background:#fff;color:#462446;font-weight:800;font-size:16px;border:2px solid #b05f6d}
div[data-testid="stTabs"] [aria-selected="true"]{background:linear-gradient(90deg,#462446,#b05f6d);color:#ffc153;border-color:#462446}
div[data-testid="stTabs"] [data-baseweb="tab-list"]{border-bottom:none}
table.rt{border-collapse:separate;border-spacing:5px;width:100%;font-size:15px}
table.rt th{padding:12px 14px;font-weight:800;text-align:left;font-size:12px;letter-spacing:.4px;text-transform:uppercase}
table.rt td{background:#fbf9f8;padding:11px 14px;color:#33253c}
table.rt td.num,table.rt th.num{text-align:right}
table.rt td.place{color:#fff;font-weight:800;clip-path:polygon(0 0,84% 0,100% 50%,84% 100%,0 100%);padding:10px 30px 10px 12px;font-size:17px}
table.rt tr.me td{background:#fff3d9}
table.rt tr.rt-total td{background:#3d3448;color:#ffc153;font-weight:800}
.you{background:#eb6b56;color:#fff;font-size:10px;font-weight:800;padding:2px 8px;border-radius:999px;margin-left:6px}
.news{display:flex;gap:12px;background:#fff;border-radius:12px;border-left:5px solid #b05f6d;padding:11px 16px;margin:8px 0;font-size:15px;color:#33253c}
.news.ok{border-left-color:#47b39d}.news.warn{border-left-color:#eb6b56}.news.gold{border-left-color:#ffc153}
.banner{background:linear-gradient(90deg,#462446,#b05f6d,#eb6b56);color:#fff;border-radius:16px;padding:16px 20px;font-weight:700;font-size:17px;margin:10px 0}
.chips{display:flex;gap:10px;flex-wrap:wrap;margin:8px 0}
.chip{background:#fff;border:1px solid #e7dfe2;border-radius:999px;padding:5px 14px;font-size:14px;font-weight:700;color:#462446}
.paper{background:#fdfbf5;color:#2a2620;border-radius:10px;padding:20px 24px;margin-bottom:16px;font-family:'Lora',serif;border-left:8px solid var(--pc,#462446)}
.paper-h{font-size:17px;font-weight:600;letter-spacing:.4px}
.paper-s{font-size:13px;color:#6b6252;margin-bottom:10px;font-style:italic}
.paper table{width:100%;border-collapse:collapse}
.paper td{padding:8px 4px;border-bottom:1px dashed #c9bfa8;font-size:15px}
.paper td.num{text-align:right;font-weight:600}
.paper tr.total td{border-bottom:none;border-top:3px double #2a2620;font-weight:700;font-size:16px}
.paper-foot{display:flex;justify-content:space-between;align-items:flex-end;margin-top:16px;gap:12px}
.stamp{width:118px;height:118px;border:3px double rgba(196,44,44,.55);border-radius:50%;color:rgba(196,44,44,.68);font:700 8.5px 'Inter',sans-serif;letter-spacing:.4px;display:flex;align-items:center;justify-content:center;text-align:center;transform:rotate(-12deg);padding:10px;flex:none}
.stamp-b{border-color:rgba(31,111,178,.55) !important;color:rgba(31,111,178,.7) !important}
.sign{font:italic 600 14px 'Lora',serif;color:#4a3b52;text-align:right}
.ct{font:700 15px 'Inter',sans-serif;color:#462446;margin-bottom:2px}
.cs{font-size:12px;color:#8a7f86;margin-bottom:6px}
.dots{letter-spacing:3px;font-size:15px}
.dots .on{color:#ffc153}.dots .off{color:#d8cfd6}
.ribbon{height:30px;width:74px;background:#eb6b56;clip-path:polygon(0 0,100% 0,100% 100%,50% 76%,0 100%);margin:0 0 6px 26px}
.book-page{animation:bookflip .55s ease;transform-origin:left center}
@keyframes bookflip{0%{transform:perspective(1600px) rotateY(-24deg);opacity:.15}100%{transform:perspective(1600px) rotateY(0);opacity:1}}
.mast{border-bottom:3px double #2a2620;margin:6px 0 16px;text-align:center}
.mast-t{font-family:'Unbounded',sans-serif;font-size:36px;font-weight:800;color:#221d15;letter-spacing:1px}
.mast-s{font:italic 400 12px 'Lora',serif;color:#6b6252;margin-top:2px}
.mast-m{display:flex;justify-content:space-between;font-size:12px;color:#6b6252;border-top:1px solid #c9bfa8;margin-top:8px;padding-top:5px;font-family:'Lora',serif;font-style:italic}
.clip{background:#f6efdb;border:1px solid #d8cdb2;padding:18px 20px 14px;margin:0 0 16px;position:relative}
.clip::before{content:'';position:absolute;top:-11px;left:50%;transform:translateX(-50%) rotate(-2deg);width:96px;height:20px;background:rgba(255,193,83,.55)}
.clip.gold{background:#fbeccb;border-color:#d9a441}.clip.warn{background:#f6d9d3;border-color:#c4493a}.clip.ok{background:#e4efe9;border-color:#47b39d}
.clip-head{font:800 10px 'Inter',sans-serif;letter-spacing:1.5px;text-transform:uppercase;color:#8a7f6a;margin-bottom:6px}
.clip-h{font-family:'Lora',serif;font-weight:700;font-size:18px;line-height:1.3;color:#221d15;margin-bottom:8px}
.clip.front .clip-h{font-size:24px}
.clip-photo{font-size:34px;text-align:center;background:#e7dcc0;border:1px solid #c9bfa8;padding:8px;margin:8px 0 4px;filter:sepia(.35)}
.clip-cap{font-size:11px;font-style:italic;color:#6b6252;text-align:center;font-family:'Lora',serif}
.clip-body{columns:2;column-gap:18px;font-family:'Lora',serif;font-size:13.5px;line-height:1.5;color:#33291c;margin-top:8px}
.clip-byline{font-size:11px;color:#8a7f6a;margin-top:10px;font-style:italic;font-family:'Lora',serif;border-top:1px solid #d8cdb2;padding-top:6px}
.print-head{border-bottom:3px double #222;margin:0 0 14px;padding-bottom:8px}
.print-head .ph-t{font:800 20px 'Unbounded',sans-serif;color:#222}
.print-head .ph-s{font:italic 12px 'Lora',serif;color:#555}
.tag{display:inline-flex;align-items:center;gap:10px;background:var(--c);color:#fff;font:800 14px 'Inter',sans-serif;padding:8px 18px;border-radius:12px;margin:2px 0 12px}
.tag-hole{width:12px;height:12px;border-radius:50%;background:#fff;opacity:.9;box-shadow:inset 0 0 0 3px var(--c)}
@media print { section[data-testid="stSidebar"], div[data-testid="stToolbar"], .stButton {display:none !important} .stApp,body{background:#fff !important} }
.mk-hero{background:linear-gradient(135deg,#232329 0%,#2B2B33 55%,#3a3a44 100%);border-radius:24px;padding:36px 40px;color:#f5f2ea;box-shadow:0 14px 44px rgba(0,0,0,.45);margin-bottom:18px;border:1px solid #3a3a44;position:relative;overflow:hidden}
.mk-hero::after{content:'';position:absolute;right:-60px;top:-60px;width:220px;height:220px;border-radius:50%;background:radial-gradient(circle,rgba(255,193,83,.18),transparent 70%)}
.mk-logo{width:130px;height:auto;display:block;margin:0 auto 12px;filter:drop-shadow(0 6px 18px rgba(0,0,0,.5))}
.mk-emblem{width:110px;height:110px;margin:0 auto 12px;border-radius:24px;background:linear-gradient(135deg,#FFC153,#e09f3e);color:#232329;font:800 44px 'Unbounded',sans-serif;display:flex;align-items:center;justify-content:center;box-shadow:0 8px 24px rgba(0,0,0,.5)}
.mk-title{font:800 44px 'Unbounded',sans-serif;color:#FFC153;text-align:center;letter-spacing:1px}
.mk-sub{text-align:center;color:#cfc9bd;font-size:14px;letter-spacing:2px;text-transform:uppercase;margin-top:4px}
.mk-slogan{font:italic 600 18px 'Lora',serif;color:#47B39D;text-align:center;margin:14px 0 4px}
.mk-chips{text-align:center;margin-top:10px}
.mk-chips span{display:inline-block;background:rgba(255,255,255,.08);border:1px solid rgba(255,193,83,.35);color:#e8e2d5;border-radius:999px;padding:6px 14px;margin:6px 6px 0 0;font-weight:600;font-size:14px}
.diploma{background:linear-gradient(135deg,#232329,#2B2B33);border:3px double #FFC153;border-radius:18px;padding:30px 34px;color:#f5f2ea;margin:0 0 22px;position:relative;box-shadow:0 14px 40px rgba(0,0,0,.45)}
.diploma::before{content:'';position:absolute;inset:10px;border:1px solid rgba(255,193,83,.4);border-radius:12px;pointer-events:none}
.dip-emblem{width:90px;height:auto;display:block;margin:0 auto 8px}
.dip-mono{width:80px;height:80px;margin:0 auto 8px;border-radius:18px;background:linear-gradient(135deg,#FFC153,#e09f3e);color:#232329;font:800 34px 'Unbounded',sans-serif;display:flex;align-items:center;justify-content:center}
.dip-title{font:800 30px 'Unbounded',sans-serif;color:#FFC153;text-align:center;letter-spacing:1px}
.dip-sub{text-align:center;color:#cfc9bd;font-size:12px;letter-spacing:2px;text-transform:uppercase;margin:4px 0 14px}
.dip-name{font:800 26px 'Unbounded',sans-serif;color:#fff;text-align:center;margin:6px 0}
.dip-line{text-align:center;color:#e8e2d5;font-size:15px;margin:4px 0}
.dip-titles{margin:12px auto 0;max-width:560px;color:#47B39D;font-size:14px;text-align:center}
.dip-foot{display:flex;justify-content:space-between;align-items:flex-end;margin-top:20px;gap:12px}
.dip-stamp{width:110px;height:110px;border:3px double rgba(255,193,83,.6);border-radius:50%;color:rgba(255,193,83,.75);font:700 8.5px 'Inter',sans-serif;display:flex;align-items:center;justify-content:center;text-align:center;transform:rotate(-12deg);padding:10px;flex:none}
.dip-sign{font:italic 600 14px 'Lora',serif;color:#e8e2d5;text-align:right}
</style>"""
st.markdown(CSS, unsafe_allow_html=True)

components.html("""
<script>
let ctx;
function swish(){
  ctx = ctx || new (window.AudioContext||window.webkitAudioContext)();
  const dur=0.28, sr=ctx.sampleRate, buf=ctx.createBuffer(1, sr*dur, sr), d=buf.getChannelData(0);
  for(let i=0;i<d.length;i++){ const t=i/d.length; d[i]=(Math.random()*2-1)*Math.pow(1-t,2.2)*0.5; }
  const src=ctx.createBufferSource(); src.buffer=buf;
  const f=ctx.createBiquadFilter(); f.type='bandpass'; f.frequency.value=1600; f.Q.value=0.7;
  const g=ctx.createGain(); g.gain.value=0.6;
  src.connect(f); f.connect(g); g.connect(ctx.destination); src.start();
}
document.addEventListener('click', e=>{
  const t = e.target.closest('[data-baseweb="tab"]');
  const b = e.target.closest('button');
  if (t || (b && /Далее|Назад/.test(b.textContent))) swish();
}, true);
const PDOC = window.parent.document;
const CARDS = {'card-finance':['#1f6fb2','#17568c'],'card-price':['#1a7a4a','#135c38'],'card-charity':['#e8b30a','#b0880a'],'card-growth':['#e07b1f','#b05e14'],'card-subsidy':['#462446','#331a33'],'card-hr':['#0e7c86','#0a5a62'],'card-tender':['#7a1f3d','#5a152c']};
const PANELS = {'panel-finance':['#dbe9f6','#17568c'],'panel-price':['#d9ead9','#135c38'],'panel-charity':['#fdf3d0','#8a6d05'],'panel-growth':['#fbe3c8','#b05e14'],'panel-subsidy':['#e6dcec','#462446'],'panel-hr':['#d7ecee','#0a5a62'],'panel-tender':['#f3dce4','#5a152c']};
function paint(){
  for (const id in CARDS){ const m=PDOC.getElementById(id); if(!m) continue; const card=m.closest('[data-testid="stVerticalBlock"]'); if(!card) continue;
    card.style.background=CARDS[id][0]; card.style.border='4px solid '+CARDS[id][1]; card.style.borderRadius='20px'; card.style.padding='14px'; card.style.margin='8px 0'; }
  for (const id in PANELS){ const m=PDOC.getElementById(id); if(!m) continue; const p=m.closest('[data-testid="stVerticalBlock"]'); if(!p) continue;
    p.style.background=PANELS[id][0]; p.style.borderRadius='14px'; p.style.padding='14px 14px 4px'; p.style.margin='4px 0 10px';
    p.querySelectorAll('label').forEach(l=>{l.style.color=PANELS[id][1];});
    p.querySelectorAll('input').forEach(i=>{i.style.background='rgba(255,255,255,.94)';i.style.borderRadius='10px';});
    p.querySelectorAll('div[data-baseweb="select"] > div').forEach(s=>{s.style.background='rgba(255,255,255,.94)';s.style.borderRadius='10px';}); }
}
setInterval(paint, 600); paint();
</script>""", height=0)

SAFE = {"🏆": "★", "💰": "$", "📉": "▼", "🚀": "▲", "👑": "♛", "": "◆", "": "", "": "■",
        "⚠️": "!", "💀": "†", "📯": "♪", "🔮": "◆", "®": "®", "🎄": "◆", "🏅": "★", "♥": "♥", "📊": "◆",
        "👥": "№", "🤝": "◆", "✊": "!", "🏭": "■", "✅": "✓", "⚖️": "!", "🧑🤝‍🧑": "№", "🐉": "◆"}
def ic(x): return SAFE.get(x, "★")

PHOTO_CACHE = {}; PHOTO_DIMS = {}
IMG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")
PHOTO_EXTS = (".jpg", ".jpeg", ".png", ".webp")
PHOTO_MIME = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
PHOTO_KEYS = {
    "photo_matryoshki": ["matryosh", "matresh", "матреш", "игруш", "versta"],
    "photo_merger": ["слияни", "поглощ", "merger", "акцион"],
    "photo_merger_sign": ["ребренд", "новая вывеска", "поглощена"],
    "photo_workshop": ["workshop", "master", "мастер", "роспис", "paint"],
    "photo_market": ["market", "rynok", "рынок", "ярмар", "prilav"],
    "photo_gov": ["gov", "admin", "админ", "здан", "kolonn"],
    "photo_crisis": ["crisis", "sklad", "склад", "криз", "yashch", "stall", "larek", "ларек"],
    "photo_agreement": ["agreement", "dogovor", "соглаш", "подпис", "handshake"],
    "photo_fire": ["fire", "pozh", "пожар", "smoke"],
    "photo_growth": ["growth", "boom", "рост", "бум", "queue", "ochered", "magazin"],
    "photo_rate_up": ["rate_up", "stavka_up", "ставка_верх", "percent_up", "calculator"],
    "photo_rate_down": ["rate_down", "stavka_down", "ставка_низ", "percent_down"],
    "photo_leader": ["leader", "lider", "лидер", "award", "nagrada"],
    "photo_loss": ["loss", "ubytok", "убыт", "debt"],
    "photo_final": ["final", "itog", "итоги", "finish", "prazdnik", "kubok"],
    "photo_hr": ["hr", "birzha", "биржа", "кадр", "найм", "перемани", "ваканс", "обучени"],
    "photo_china": ["китай", "холдинг", "хэнъянь", "henyan", "china"],
    "photo_revenue": ["revenue", "vyrouchka", "выруч", "касса", "profit"],
    "photo_charity": ["charity", "blagotvor", "благотвор", "меценат", "heart"],
    "photo_coalition_start": ["коалици", "coalition", "сговор"],
    "photo_coalition_end": ["коалиция распал", "коалиция прекрат"],
    "photo_strike": ["забастов", "strike", "пикет"],
    "photo_strike_after": ["простой", "последствия забастов"],
    "photo_tender": ["тендер", "госзакуп", "контракт"],
    "photo_union": ["профсоюз", "коллективный договор"],
    "photo_warehouse": ["склад", "warehouse", "запас", "хранение"],
    "photo_wood": ["сырь", "лес", "лип", "берез", "древес", "wood"],
    "photo_eco": ["эко", "eco", "тренд"],
    "photo_tourists": ["турист", "tourist"],
    "photo_cert": ["гост", "сертифика", "роскачеств", "cert"],
    "photo_paint": ["краск", "лак", "paint", "покрыт"],
    "photo_viral": ["вирусн", "ролик", "viral"],
    "photo_master_leave": ["ключевого мастера", "уход мастер"],
    "photo_corp_order": ["корпоратив", "оптов", "corp"],
    "photo_recall": ["отзыв парти", "брак", "recall"],
    "photo_sick": ["больнич", "грипп", "эпидем", "sick"],
}
PHOTO_FALLBACK = {
    "photo_rate_down": "photo_gov", "photo_leader": "photo_market", "photo_loss": "photo_crisis",
    "photo_merger": "photo_agreement", "photo_merger_sign": "photo_merger",
    "photo_agreement": "photo_gov", "photo_fire": "photo_crisis", "photo_growth": "photo_market",
    "photo_rate_up": "photo_gov", "photo_final": "photo_matryoshki",
    "photo_hr": "photo_workshop", "photo_china": "photo_market", "photo_revenue": "photo_market",
    "photo_charity": "photo_gov", "photo_coalition_start": "photo_agreement", "photo_coalition_end": "photo_agreement",
    "photo_strike": "photo_hr", "photo_strike_after": "photo_crisis", "photo_tender": "photo_gov",
    "photo_union": "photo_hr", "photo_warehouse": "photo_crisis", "photo_wood": "photo_market",
    "photo_eco": "photo_growth", "photo_tourists": "photo_market", "photo_cert": "photo_gov",
    "photo_paint": "photo_workshop", "photo_viral": "photo_market", "photo_master_leave": "photo_hr",
    "photo_corp_order": "photo_agreement", "photo_recall": "photo_crisis", "photo_sick": "photo_hr",
}

def _img_files():
    res = {}
    if os.path.isdir(IMG_DIR):
        for fn in os.listdir(IMG_DIR):
            low = fn.lower()
            if not low.endswith(PHOTO_EXTS): continue
            stem = low
            while stem.endswith(PHOTO_EXTS): stem = stem[:stem.rfind(".")]
            res[stem] = fn
    return res

def _find_file(base):
    files = _img_files()
    if base in files: return files[base]
    for stem, fn in files.items():
        if any(k in stem for k in PHOTO_KEYS.get(base, [])): return fn
    return None

def img_dims(path):
    try:
        with open(path, "rb") as f: data = f.read(4096)
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
        if data[:3] == b"\xff\xd8\xff":
            i = 2
            while i < len(data) - 9:
                if data[i] != 0xFF: i += 1; continue
                m = data[i + 1]
                if m in (0xC0,0xC1,0xC2,0xC3,0xC5,0xC6,0xC7,0xC9,0xCA,0xCB,0xCD,0xCE,0xCF):
                    return int.from_bytes(data[i+7:i+9], "big"), int.from_bytes(data[i+5:i+7], "big")
                if m in (0xD8,0x01) or 0xD0 <= m <= 0xD7: i += 2; continue
                ln = int.from_bytes(data[i+2:i+4], "big"); i += 2 + ln
        return None
    except Exception:
        return None

def photo_b64(base, _depth=0):
    if base in PHOTO_CACHE: return PHOTO_CACHE[base]
    val = None
    fn = _find_file(base)
    if fn:
        path = os.path.join(IMG_DIR, fn)
        ext = "." + fn.lower().rsplit(".", 1)[1]
        with open(path, "rb") as f:
            val = f"data:{PHOTO_MIME.get(ext,'image/jpeg')};base64," + base64.b64encode(f.read()).decode()
        PHOTO_DIMS[base] = img_dims(path)
    if val is None and _depth < 2 and base in PHOTO_FALLBACK:
        val = photo_b64(PHOTO_FALLBACK[base], _depth + 1)
    PHOTO_CACHE[base] = val
    return val

def photo_ratio(base):
    d = PHOTO_DIMS.get(base) or PHOTO_DIMS.get(PHOTO_FALLBACK.get(base, ""))
    if not d or not d[1]: return 1.7
    return d[0] / d[1]

def photo_for(n, front=False):
    t = (str(n.get("head", "")) + " " + str(n.get("text", ""))).lower()
    if any(k in t for k in ["отчетный период завершен", "итоги года", "звания года", "отрасль в цифрах"]): return "photo_final"
    if any(k in t for k in ["минпромторг", "субсид", "конкурс"]): return "photo_gov"
    if any(k in t for k in ["китай", "холдинг", "хэнъянь", "henyan"]): return "photo_china"
    if any(k in t for k in ["коалиция распал", "коалиция прекрат"]): return "photo_coalition_end"
    if any(k in t for k in ["коалици", "сговор"]): return "photo_coalition_start"
    if any(k in t for k in ["забастов"]): return "photo_strike"
    if any(k in t for k in ["простой", "последствия забастов"]): return "photo_strike_after"
    if any(k in t for k in ["профсоюз", "коллективный договор"]): return "photo_union"
    if any(k in t for k in ["тендер", "госзакуп", "контракт"]): return "photo_tender"
    if any(k in t for k in ["ключевого мастера", "уход мастер"]): return "photo_master_leave"
    if any(k in t for k in ["отзыв парти", "брак"]): return "photo_recall"
    if any(k in t for k in ["вирусн", "ролик"]): return "photo_viral"
    if any(k in t for k in ["корпоратив", "оптов"]): return "photo_corp_order"
    if any(k in t for k in ["роскачеств", "гост", "сертифика"]): return "photo_cert"
    if any(k in t for k in ["больнич", "грипп", "эпидем"]): return "photo_sick"
    if any(k in t for k in ["биржа труда", "кадр", "перемани", "ваканс", "найм", "обучени"]): return "photo_hr"
    if any(k in t for k in ["патент", "роспис", "мастер", "бренд"]): return "photo_workshop"
    if any(k in t for k in ["ставка цб выросла", "кредиты дороже"]): return "photo_rate_up"
    if any(k in t for k in ["ставка цб снизилась", "кредиты дешевле"]): return "photo_rate_down"
    if any(k in t for k in ["пожар"]): return "photo_fire"
    if any(k in t for k in ["соглашени", "экспортный контракт", "контракт с"]): return "photo_agreement"
    if any(k in t for k in ["крупнейший убыток", "банкрот", "минусе"]): return "photo_loss"
    if any(k in t for k in ["рекорд отрасли", "книга рекордов", "смена лидера"]): return "photo_leader"
    if any(k in t for k in ["бум", "рождаем", "пластиковых игрушек", "фест", "спрос раст", "турист", "эко", "тренд"]): return "photo_growth"
    if any(k in t for k in ["кризис", "экономят", "бедствие", "контрафакт"]): return "photo_crisis"
    if any(k in t for k in ["склад съедает", "избыток склада", "складская авария", "склад"]): return "photo_warehouse"
    if any(k in t for k in ["сырь", "лес", "лип", "берез", "древес"]): return "photo_wood"
    if any(k in t for k in ["краск", "лак", "покрыт"]): return "photo_paint"
    if any(k in t for k in ["рекордная выручка", "выручка месяца"]): return "photo_revenue"
    if any(k in t for k in ["благотворительная ведомость", "щедрость", "меценат"]): return "photo_charity"
    if any(k in t for k in ["ребренд", "новая вывеска"]): return "photo_merger_sign"
    if any(k in t for k in ["слияни", "поглощ", "merger"]): return "photo_merger"
    if any(k in t for k in ["продаж", "выруч", "спрос", "ярмарк", "рынок", "благотвор"]): return "photo_market"
    return "photo_matryoshki"

def img_status():
    files = _img_files()
    found = [b for b in PHOTO_KEYS if _find_file(b)]
    missing = [b for b in PHOTO_KEYS if b not in found]
    txt = f"Фотоархив редакции: найдено {len(found)} из {len(PHOTO_KEYS)}"
    txt += ("; файлы: " + ", ".join(sorted(files.values()))) if files else "; папка img пуста"
    if missing: txt += "; не хватает: " + ", ".join(missing)
    return txt + "."

def logo_b64():
    for fn in ("logo_emblem.png", "logo_emblem.jpg", "logo_emblem.webp"):
        p = os.path.join(IMG_DIR, fn)
        if os.path.exists(p):
            ext = "." + fn.rsplit(".", 1)[1]
            with open(p, "rb") as f:
                return f"data:{PHOTO_MIME.get(ext, 'image/png')};base64," + base64.b64encode(f.read()).decode()
    return None

def tile(color, icon, label, value, delta=None):
    d = ""
    if delta is not None:
        d = f"<span class='delta {'up' if delta >= 0 else 'down'}'>{'▲' if delta >= 0 else '▼'} {abs(delta):,.0f}</span>"
    return f"<div class='tile' style='--c:{color}'><div class='tic'>{icon}</div><div><div class='kpi-l'>{label}</div><div class='kpi-v'>{value}</div>{d}</div></div>"

def dots(val, scale=2.0, n=10):
    k = max(0, min(n, int(val / scale)))
    return "<span class='dots'>" + "".join(f"<span class='{'on' if i < k else 'off'}'>●</span>" for i in range(n)) + "</span>"

def calendar_html(turn):
    year = (turn - 1) // 12 + 1
    cur_m = ((turn - 1) % 12) + 1
    cells = ""
    for m in range(1, 13):
        t_of_m = (year - 1) * 12 + m
        state = "cal-cur" if m == cur_m else ("cal-past" if t_of_m < turn else "cal-fut")
        marks = ""
        if m in SUBSIDY_MONTHS: marks += "<span class='cal-mk'>♜</span>"
        elif m in ANNOUNCE_MONTHS: marks += "<span class='cal-mk cal-mk-a'>•</span>"
        if m in TENDER_MONTHS: marks += "<span class='cal-mk cal-mk-d'>▣</span>"
        if m == 12: marks += "<span class='cal-mk cal-mk-d'>✦</span>"
        cells += f"<div class='calcell {state}'><div class='calnum'>{m:02d}</div><div class='calname'>{MONTH_NAMES[m-1]}</div><div class='calmarks'>{marks}</div></div>"
    return (f"<div class='calcard'><div class='calhead'><span class='calyear'>Год {year}</span>"
            f"<span class='callegend'><span><i class='lg lg-past'></i>прошедшие</span><span><i class='lg lg-cur'></i>текущий</span><span><i class='lg lg-fut'></i>впереди</span></span></div>"
            f"<div class='calgrid'>{cells}</div></div>")

STAMP = ("<div class='paper-foot'><div class='stamp'>М.П.<br>ООО «ВОЗНЕСЕНСКАЯ<br>ИГРУШЕЧНАЯ ФАБРИКА»<br>ИНН 5223000000<br>ОГРН 1025200000000</div>"
         "<div class='sign'>Главный бухгалтер<br><svg width='110' height='26' viewBox='0 0 110 26'><path d='M4 18 C 18 4, 26 24, 40 12 S 66 6, 86 16 S 100 20, 106 12' fill='none' stroke='#4a3b52' stroke-width='1.6'/></svg><br>З. П. Синявина</div></div>")
STAMP_CONSULT = ("<div class='paper-foot'><div class='stamp stamp-b'>М.П.<br>ООО «КОНСАЛТИНГОВАЯ<br>ФИРМА „СТРАТЕГИЯ+“»<br>ИНН 7712345678<br>ОГРН 1177746000000</div>"
         "<div class='sign'>Главный консультант<br><svg width='110' height='26' viewBox='0 0 110 26'><path d='M6 16 C 20 6, 30 22, 44 10 S 70 4, 88 14 S 100 18, 106 10' fill='none' stroke='#4a3b52' stroke-width='1.6'/></svg><br>Г. Г. Стратегов</div></div>")

def paper_html(title, subtitle, rows, color="#462446", stamp=None):
    body = ""
    for row in rows:
        if len(row) == 2:
            label, val = row
            body += f"<tr><td>{label}</td><td style='text-align:left'>{val}</td></tr>"
        else:
            label, val, cls = row
            body += f"<tr class='{cls}'><td>{label}</td><td class='num'>{val}</td></tr>"
    seal = stamp if stamp is not None else STAMP
    return (f"<div class='paper' style='--pc:{color}'><div class='paper-h'>{title}</div>"
            f"<div class='paper-s'>{subtitle}</div><table>{body}</table>{seal}</div>")

def news_html(items):
    return "".join(f"<div class='news {n['kind']}'><span>{ic(n['icon'])}</span><span>{n['text']}</span></div>" for n in items)

def masthead_html(issue, date_label, final=False):
    title = "РЫНОЧНЫЙ ВЕСТНИКЪ" if not final else "РЫНОЧНЫЙ ВЕСТНИКЪ · ФИНАЛЬНЫЙ ВЫПУСКЪ"
    return (f"<div class='mast'><div class='mast-t'>{title}</div>"
            f"<div class='mast-s'>Издание Вознесенского района · пишут о матрёшках с 1998 года</div>"
            f"<div class='mast-m'><span>Выпуск № {issue}</span><span>{date_label}</span><span>Цена 0 ₽ 00 коп.</span></div></div>")

def clip_html(n, month_label, front=False):
    body = n["text"] + " Редакция продолжает следить за развитием событий и обещает подробности в следующих выпусках."
    base = photo_for(n, front)
    b64 = photo_b64(base)
    if b64:
        h_px = 190 if front else 140
        ratio = photo_ratio(base)
        filt = "filter:grayscale(.45) sepia(.3) contrast(1.12) brightness(.96)"
        if ratio >= 1.3:
            photo_html = f"<div style='height:{h_px}px;overflow:hidden;border:1px solid #c9bfa8;margin:8px 0 4px'><img src='{b64}' style='width:100%;height:100%;object-fit:cover;object-position:center;display:block;{filt}'></div>"
        else:
            photo_html = f"<div style='background:#e9dfc8;border:1px solid #c9bfa8;margin:8px 0 4px;padding:6px;text-align:center'><img src='{b64}' style='height:{h_px}px;max-width:100%;width:auto;object-fit:contain;display:inline-block;{filt}'></div>"
    else:
        photo_html = f"<div class='clip-photo'>{ic(n['icon'])}</div><div class='clip-cap'>фото: архив редакции «Рыночного вестника»</div>"
    return (f"<div class='clip {n['kind']}{' front' if front else ''}'><div class='clip-head'>{n['head']}</div>"
            f"<div class='clip-h'>{n['text']}</div>{photo_html}<div class='clip-body'>{body}</div>"
            f"<div class='clip-byline'>от нашего корреспондента · {month_label}</div></div>")

HEADS = [("#", "#462446", "#fff", ""), ("Компания", "#462446", "#fff", ""),
         ("MPI итог", "#eb6b56", "#fff", "num"), ("MPI хода", "#b05f6d", "#fff", "num"),
         ("Цена", "#ffc153", "#462446", "num"), ("Продано", "#47b39d", "#fff", "num"),
         ("Доля", "#462446", "#fff", "num"), ("Качество", "#b05f6d", "#fff", "num")]

def charity_tier(mc):
    t = ""
    for thr, name in CHARITY_TIERS:
        if mc >= thr: t = name
    return t

def rank_html(game, viewer_name):
    rows = sorted([c for c in game["companies"] if c.history], key=lambda c: c.mpi_total, reverse=True)
    th = "".join(f"<th style='background:{bg};color:{fg}' class='{cls}'>{t}</th>" for t, bg, fg, cls in HEADS)
    tr = ""
    for i, c in enumerate(rows):
        h = c.history[-1]
        place = f"<span class='medal m{i+1}'>{i+1}</span>" if i < 3 else str(i + 1)
        me = c.name == viewer_name
        tag = "<span class='you'>вы</span>" if me else ""
        bot = "<span class='badge b-bot'>бот</span>" if c.is_bot else ""
        dead = "<span class='badge b-dead'>банкрот</span>" if c.bankrupt else ""
        brand = "<span class='badge b-brand'>®</span>" if h.get("brand") else ""
        heart = "<span class='badge b-heart'>♥</span>" if charity_tier(h.get("charity", 0)) else ""
        tr += (f"<tr class='{'me' if me else ''}'><td class='place' style='background:{PAL[i % 5]}'>{place}</td>"
               f"<td><b>{c.name}</b>{bot}{dead}{brand}{heart}{tag}</td>"
               f"<td class='num'><b>{c.mpi_total:.1f}</b></td><td class='num'>{h.get('mpi', 0):.1f}</td>"
               f"<td class='num'>{h['price']:.1f}</td><td class='num'>{int(h['sales'])}</td>"
               f"<td class='num'>{h['market_share']:.1f}%</td><td class='num'>{c.quality:.1f}</td></tr>")
    tot_sold = sum(int(c.history[-1]["sales"]) for c in rows)
    avg_p = sum(c.history[-1]["price"] for c in rows) / max(1, len(rows))
    avg_q = sum(c.quality for c in rows) / max(1, len(rows))
    tr += (f"<tr class='rt-total'><td></td><td>ИТОГО ПО РЫНКУ</td><td class='num'>—</td><td class='num'>—</td>"
           f"<td class='num'>{avg_p:.1f}</td><td class='num'>{tot_sold}</td><td class='num'>100%</td><td class='num'>{avg_q:.1f}</td></tr>")
    return f"<table class='rt'><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>"

def fig_base(fig, h=310, legend=False):
    fig.update_layout(height=h, margin=dict(l=8, r=8, t=30, b=8), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter", size=12, color="#4a3b52"),
                      showlegend=legend, bargap=0.35)
    return fig

def compute_titles(game):
    comps = [c for c in game["companies"] if c.history]
    if not comps: return []
    emp = max(comps, key=lambda c: sum(h["workers"] for h in c.history) / len(c.history))
    taxp = max(comps, key=lambda c: sum(h["tax"] for h in c.history))
    mec = max(comps, key=lambda c: sum(h.get("charity", 0) for h in c.history))
    titles = [f"«Работодатель года» — «{emp.name}»", f"«Налогоплательщик года» — «{taxp.name}»"]
    if sum(h.get("charity", 0) for h in mec.history) > 0:
        titles.append(f"«Меценат года» — «{mec.name}»")
    if game.get("record_company"):
        titles.append(f"«Рекордсмен года» — «{game['record_company']}»")
    brand_comps = [c for c in comps if getattr(c, "brand", False)]
    if brand_comps:
        titles.append("Носители бренда ®: " + ", ".join(f"«{c.name}»" for c in brand_comps))
    return titles

def diploma_html(game, c, place):
    head = "ДИПЛОМ ПОБЕДИТЕЛЯ" if place == 1 else ("ГРАМОТА ЛАУРЕАТА" if place <= 3 else "ГРАМОТА УЧАСТНИКА")
    date = datetime.now().strftime("%d.%m.%Y")
    titles = [t for t in compute_titles(game) if c.name in t]
    _lg = logo_b64()
    emb = f"<img class='dip-emblem' src='{_lg}'>" if _lg else "<div class='dip-mono'>МК</div>"
    titles_html = ("<div class='dip-titles'>" + "<br>".join(titles) + "</div>") if titles else ""
    return (f"<div class='diploma'>{emb}<div class='dip-title'>{head}</div>"
            f"<div class='dip-sub'>экономический симулятор Вознесенского округа · Мастер Капитала</div>"
            f"<div class='dip-line'>награждается</div><div class='dip-name'>«{c.name}»</div>"
            f"<div class='dip-line'>за {place} место · индекс развития отрасли {c.mpi_total:.1f}</div>"
            f"<div class='dip-line'>сезон: {game['turn']} мес. · дата: {date}</div>{titles_html}"
            f"<div class='dip-foot'><div class='dip-stamp'>КОМИТЕТ СИМУЛЯТОРА<br>ВОЗНЕСЕНСКИЙ ОКРУГ<br>«МАСТЕР КАПИТАЛА»</div>"
            f"<div class='dip-sign'>Председатель комитета<br>"
            f"<svg width='110' height='26' viewBox='0 0 110 26'><path d='M6 16 C 20 6, 30 22, 44 10 S 70 4, 88 14 S 100 18, 106 10' fill='none' stroke='#e8e2d5' stroke-width='1.6'/></svg>"
            f"<br>И. И. Ведущий</div></div></div>")

def industry_stats(game):
    agg_inv = sum(h.get("investment", 0) for c in game["companies"] for h in c.history)
    agg_rnd = sum(h.get("rnd", 0) for c in game["companies"] for h in c.history)
    agg_rev = sum(h.get("revenue", 0) for c in game["companies"] for h in c.history)
    agg_tax = sum(h.get("tax", 0) for c in game["companies"] for h in c.history)
    agg_units = sum(int(h.get("sales", 0)) for c in game["companies"] for h in c.history)
    agg_char = sum(h.get("charity", 0) for c in game["companies"] for h in c.history)
    return agg_inv, agg_rnd, agg_rev, agg_tax, agg_units, agg_char

SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saves")
os.makedirs(SAVE_DIR, exist_ok=True)
HOF_FILE = os.path.join(SAVE_DIR, "halloffame.json")

def save_game(game, slot):
    data = {k: v for k, v in game.items() if k != "companies"}
    data["companies"] = [c.to_dict() for c in game["companies"]]
    data["saved_at"] = datetime.now().strftime("%d.%m.%Y %H:%M")
    with open(os.path.join(SAVE_DIR, slot + ".json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

def load_game(slot):
    with open(os.path.join(SAVE_DIR, slot + ".json"), encoding="utf-8") as f:
        data = json.load(f)
    data["companies"] = [Company.from_dict(c) for c in data.pop("companies")]
    data.pop("saved_at", None)
    for k, v in {"news_log": [], "next_event": None, "forecast_dir": None, "cost_factor": 1.0,
                 "loan_rate": LOAN_RATE, "deposit_rate": DEPOSIT_RATE, "record_sales": 0,
                 "record_company": "", "record_period": "", "patents_log": [], "start_cash": START_CASH,
                 "sub_types_open": None, "decisions_current": {}, "social_capital": 0.0, "retention": 1.0,
                 "royalty": False, "sandbox": False, "pool": dict(POOL_START), "achievements": {},
                 "coalition": None, "coalition_cd": 0, "tender": None}.items():
        data.setdefault(k, v)
    if not data.get("humans"): data["humans"] = [data.get("player", "Моя компания")]
    return data

def list_saves():
    return sorted(f[:-5] for f in os.listdir(SAVE_DIR) if f.endswith(".json") and f != "halloffame")

def hof_load():
    if os.path.exists(HOF_FILE):
        try:
            with open(HOF_FILE, encoding="utf-8") as f: return json.load(f)
        except Exception: return []
    return []

def hof_add(rec):
    data = hof_load(); data.append(rec)
    data.sort(key=lambda r: -r.get("mpi", 0)); data = data[:50]
    with open(HOF_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=1)

class Company:
    def __init__(self, name, is_bot=False, strategy="balanced", tax="usn6", start_cash=START_CASH):
        self.name = name; self.is_bot = is_bot; self.strategy = strategy; self.tax = tax
        self.cash = start_cash; self.assets = START_ASSETS
        self.inventory = 0; self.quality = 100.0; self.patent = False
        self.cum_rnd = 0.0; self.loans = []; self.deposits = []
        self.neg_turns = 0; self.bankrupt = False
        self.reputation = 0.0; self.mpi_total = 0.0; self.history = []
        self.rescue_taken = False; self.sub_won = False; self.sub_type = 0; self.sub_msg = ""
        self.brand = False; self.pr_next = False
        self.staff = {"assemblers": 6, "turners": 3, "painters": 1, "managers": 1}
        self.skill = {"assemblers": 2.0, "turners": 2.5, "painters": 3.0, "managers": 3.0}
        self.novices = 0; self.training = []; self.premium = 0.0; self.loyalty = 0.0
        self.workers = sum(self.staff.values()) + self.novices
        self.vacancies = {p: 0 for p in PROFS}; self.vac_pct = 0.0
        self.tension = 0.0; self.strike = 0; self.union = False; self.union_offer = False
        self.contracts = []; self.reliability = 0.0
    def capacity(self): return max(1, int(self.assets / CAP_NORM))
    def productivity_eff(self):
        s = self.skill
        mult = 0.75 + 0.10 * (0.55 * s["turners"] + 0.30 * s["assemblers"] + 0.15 * s["painters"])
        return (20 + self.capacity() * 0.02) * mult
    def staff_need(self, prod):
        base = self.productivity_eff()
        turners = math.ceil(prod / base) if prod > 0 else 0
        painters = math.ceil(turners * 0.4)
        assemblers = math.ceil(turners * 0.6) + math.ceil(self.capacity() / 100)
        total = turners + painters + assemblers
        managers = math.ceil(total / MANAGER_SPAN)
        return {"assemblers": assemblers, "turners": turners, "painters": painters, "managers": managers}
    def labor_cost(self):
        prem = 1 + self.premium / 100
        base = sum(self.staff[p] * LABOR_WAGE[p] for p in PROFS) * prem + self.novices * NOVICE_WAGE
        if self.union: base *= (1 + UNION_WAGE_UP)
        return base
    def unit_cost(self, volume):
        if volume <= 0: return 0.0
        need = self.staff_need(volume)
        labor = sum(need[p] * LABOR_WAGE[p] for p in PROFS) * (1 + self.premium / 100)
        mat = MATERIAL_UNIT * max(0.85, 1 - self.cum_rnd * 1e-6)
        uc = mat + labor / volume + FIXED_COST / volume
        if self.patent: uc *= (1 - PATENT_COST_CUT)
        return uc
    def to_dict(self):
        return dict(name=self.name, is_bot=self.is_bot, strategy=self.strategy, tax=self.tax,
                    cash=self.cash, assets=self.assets, inventory=self.inventory, quality=self.quality,
                    patent=self.patent, cum_rnd=self.cum_rnd, loans=self.loans, deposits=self.deposits,
                    neg_turns=self.neg_turns, bankrupt=self.bankrupt, reputation=self.reputation,
                    mpi_total=self.mpi_total, history=self.history, rescue_taken=self.rescue_taken,
                    sub_won=self.sub_won, sub_type=self.sub_type, sub_msg=self.sub_msg,
                    brand=self.brand, pr_next=self.pr_next, staff=self.staff, skill=self.skill,
                    novices=self.novices, training=self.training, premium=self.premium, loyalty=self.loyalty,
                    workers=self.workers, vacancies=self.vacancies, vac_pct=self.vac_pct,
                    tension=self.tension, strike=self.strike, union=self.union, union_offer=self.union_offer,
                    contracts=self.contracts, reliability=self.reliability)
    @classmethod
    def from_dict(cls, d):
        c = cls(d["name"], d["is_bot"], d["strategy"], d["tax"])
        for k, v in d.items(): setattr(c, k, v)
        return c

def corp_points(pay):
    return 50 + min(50, pay / 100)

def check_achievements(game, c, h):
    got = game.setdefault("achievements", {}).setdefault(c.name, [])
    def unlock(i):
        if i not in got: got.append(i)
    if h["profit"] > 0: unlock("first_profit")
    if c.patent: unlock("first_patent")
    if c.contracts: unlock("first_tender")
    if h.get("strike", 0) == 0 and any(x.get("strike", 0) > 0 for x in c.history[:-1]): unlock("survived_strike")
    if h.get("charity", 0) >= 1000: unlock("mecenate")
    if c.brand: unlock("brand_holder")
    if game.get("record_company") == c.name: unlock("record_setter")
    if c.workers >= 25: unlock("big_employer")
    if c.quality >= 120: unlock("master_quality")
    if sum(x["revenue"] for x in c.history) >= 1_000_000: unlock("millionaire")
    if len(c.history) >= 3 and all(x["profit"] > 0 for x in c.history[-3:]): unlock("clean_quarter")
    if h["market_share"] >= 50: unlock("half_market")
    if h["sales"] > 0 and h["inventory"] == 0: unlock("sold_out")
    if any("сувенир" in ct.get("customer", "").lower() for ct in c.contracts): unlock("exporter")
    if c.reliability >= 5: unlock("reliable_supplier")
    if h.get("vac_pct", 0) == 0 and h.get("util", 0) >= 0.8: unlock("full_staff")
    if h.get("tension", 0) <= 25 and c.workers >= 15: unlock("calm_collective")
    if c.reputation >= 10: unlock("peoples_love")
    if c.quality >= 150: unlock("quality_150")
    if game["turn"] <= 8 and c.mpi_total >= 150: unlock("fast_start")
    if game["turn"] >= game.get("max_turns", 24) and not c.bankrupt: unlock("marathon")
    return got

def bot_decision(c, avg_price, season, month, difficulty, last_factor, sc, open_types, pool, game):
    cap = c.capacity(); s = c.strategy
    poor = c.cash < sc * 0.5
    price, prod = avg_price, int(cap * 0.85 * season)
    if s == "conservative": price, prod = avg_price * 0.95, int(cap * 0.7 * season)
    elif s == "aggressive": price, prod = avg_price * 1.10, cap
    elif s == "dumper": price, prod = avg_price * 0.85, cap
    elif s == "niche": price, prod = avg_price * 1.35, int(cap * 0.5)
    elif s == "financier": price, prod = avg_price * 1.05, int(cap * 0.5)
    elif s == "expansionist": price, prod = avg_price * 0.95, cap
    elif s == "follower": prod = int(cap * 0.7 * season)
    est_labor = c.labor_cost()
    reserve = 2 * (FIXED_COST + est_labor)
    free = c.cash - reserve
    last_profit = c.history[-1]["profit"] if c.history else 0.0
    envelope = max(0.0, min(free * 0.25, 3 * max(0.0, last_profit) + 500))
    if last_profit < 0: envelope *= 0.5
    util_last = c.history[-1]["util"] if c.history else 0.0
    gate_invest = util_last >= 0.85
    est_rev = cap * 0.85 * avg_price
    prio = {"conservative": [("charity",0.20),("rnd",0.30),("marketing",0.30),("invest",0.20)],
            "balanced": [("charity",0.15),("marketing",0.45),("rnd",0.25),("invest",0.15)],
            "aggressive": [("charity",0.05),("marketing",0.50),("invest",0.30),("rnd",0.15)],
            "niche": [("charity",0.30),("rnd",0.50),("marketing",0.20)],
            "financier": [("charity",0.10),("rnd",0.20),("marketing",0.20),("invest",0.10)],
            "dumper": [("marketing",0.60),("invest",0.20),("rnd",0.10)],
            "adaptive": [("charity",0.15),("marketing",0.40),("rnd",0.25),("invest",0.20)],
            "expansionist": [("invest",0.50),("marketing",0.25),("charity",0.05),("rnd",0.20)],
            "follower": [("charity",0.10),("marketing",0.30),("rnd",0.20),("invest",0.10)]}.get(
            s, [("marketing",0.4),("rnd",0.3),("charity",0.1),("invest",0.2)])
    spend = {"marketing":0.0,"rnd":0.0,"invest":0.0,"charity":0.0}
    for kind, share in prio:
        amt = envelope * share
        if kind == "invest" and not gate_invest: continue
        if kind == "marketing": amt = min(amt, 0.15 * est_rev)
        if kind == "rnd": amt = min(amt, 0.10 * est_rev)
        spend[kind] += amt
    char_floor = {"conservative":400,"balanced":500,"aggressive":400,"niche":1000,"financier":200,
                  "dumper":0,"adaptive":500,"expansionist":300,"follower":200}.get(s, 300)
    if c.tax != "usn6": char_floor = round(char_floor * 1.3)
    if free > 0: spend["charity"] = max(spend["charity"], float(char_floor))
    recip = {"conservative":2,"balanced":1,"aggressive":4,"niche":3,"financier":1,"dumper":1,
             "adaptive":1,"expansionist":1,"follower":2}.get(s, 1)
    mkt, rnd, inv, ch = spend["marketing"], spend["rnd"], spend["invest"], spend["charity"]
    if poor: mkt, rnd, inv, ch = mkt/2, rnd/2, inv/2, ch/2
    need = c.staff_need(prod)
    hire = {p: max(0, need[p] - c.staff[p]) for p in PROFS}
    if s in ("aggressive", "niche"): hire["painters"] += 1
    premium = {"conservative":0,"aggressive":25,"balanced":10,"dumper":0,"niche":15,"financier":0,
               "adaptive":10,"expansionist":10,"follower":0}.get(s, 0)
    nov_hire = max(0, need["assemblers"] - c.staff["assemblers"] - hire["assemblers"])
    train = ["painters"] if (need["painters"] > c.staff["painters"] and c.novices > 0) else []
    d = dict(price=price, production=max(0, min(cap, prod - c.inventory)), marketing=mkt, investment=inv,
             rnd=rnd, charity=ch, charity_rec=recip, loan=0.0, loan_term=6, deposit=0.0, deposit_term=6,
             subsidy_apply=False, sub_type=open_types[0], sub_pay=0.0, hire=hire, fire={p:0 for p in PROFS},
             train=train, nov_hire=nov_hire, premium=premium,
             loyalty=300.0 if s in ("conservative","balanced") else 0.0,
             tender_apply=False, tender_price=0.0, union_choice=None)
    if s == "conservative" and c.cash > sc * 1.2: d["deposit"] = c.cash * 0.2
    if difficulty == "easy":
        d["price"] *= 1 + random.uniform(-0.10, 0.10)
        d["production"] = int(d["production"] * random.uniform(0.85, 1.15))
    else:
        if c.history:
            h = c.history[-1]
            if h["lost"] > h["sales"] * 0.15:
                d["price"] *= 1.03; d["production"] = min(cap, d["production"] + int(h["lost"] * 0.5))
            if c.inventory > max(20, h["prod"] * 0.25):
                d["price"] *= 0.95; d["production"] = max(0, d["production"] - c.inventory // 2)
        if last_factor < 1.0:
            d["production"] = int(d["production"] * 0.8); d["marketing"] *= 0.7
    floor = c.unit_cost(max(1, d["production"])) * 1.05
    if d["price"] < floor: d["price"] = round(floor, 2)
    if c.cash < RESCUE_CASH:
        d.update(marketing=0.0, rnd=0.0, investment=0.0, charity=0.0)
        d["price"] = max(avg_price * 0.92, floor)
        d["production"] = max(0, min(cap, int(cap * 0.5) - c.inventory))
        free_loan = LOAN_LIMIT - sum(l[0] for l in c.loans)
        if not c.rescue_taken and free_loan > 0:
            d["loan"] = min(sc * 0.5, free_loan); c.rescue_taken = True
    if month in SUBSIDY_MONTHS and c.cash > sc * 0.5:
        chance = {"easy":0.35,"medium":0.65,"hard":0.95}.get(difficulty, 0.65)
        if random.random() < chance:
            d["subsidy_apply"] = True
            base_pay = {"conservative":300,"aggressive":2000,"balanced":1000,"dumper":500,"niche":1500,
                        "financier":200,"adaptive":1000,"expansionist":1500,"follower":300}.get(s, 800)
            if difficulty == "hard": base_pay = max(base_pay, 1500)
            d["sub_pay"] = float(base_pay)
            pref = 2 if s == "conservative" else (1 if s == "aggressive" else open_types[0])
            d["sub_type"] = pref if pref in open_types else open_types[0]
    if difficulty == "hard":
        if c.cum_rnd < PATENT_THRESHOLD and c.cash > sc * 0.8: d["rnd"] = max(d["rnd"], 2000.0)
        if not c.brand and c.cash > sc * 0.9: d["rnd"] = max(d["rnd"], 2500.0); d["charity"] = max(d["charity"], 800.0)
    coal = game.get("coalition")
    if coal and coal["months"] > 0 and c.name in coal["participants"]:
        d["price"] *= (1 - random.uniform(0.08, 0.12))
        d["marketing"] = d["marketing"] * random.uniform(1.3, 1.6) + 500
    tnd = game.get("tender")
    if tnd and tnd.get("open") and c.quality >= tnd["quality_min"]:
        sm = {"dumper":0.88,"aggressive":0.92,"balanced":0.95,"conservative":0.97,"niche":0.97,"expansionist":0.90}.get(c.strategy, 0.95)
        d["tender_apply"] = True
        d["tender_price"] = round(tnd["price_cap"] * sm, 1)
    if c.union_offer:
        d["union_choice"] = "sign" if c.cash > 15000 else "refuse"
    return d

def run_turn(game, decisions):
    game["turn"] += 1
    month = ((game["turn"] - 1) % 12) + 1
    season = MONTH_SEASON[month - 1]
    ev = game.get("next_event") or roll_event()
    _, event_text, factor, cost_factor, rate_delta, _dir_ov, special = ev
    game["last_factor"] = factor
    game["cost_factor"] = cost_factor
    if rate_delta:
        game["loan_rate"] = min(0.04, max(0.005, game.get("loan_rate", LOAN_RATE) + 0.008 * rate_delta))
        game["deposit_rate"] = min(0.02, max(0.002, game.get("deposit_rate", DEPOSIT_RATE) + 0.004 * rate_delta))
    market = int(BASE_MARKET * season * factor)
    alive = [c for c in game["companies"] if not c.bankrupt]
    news = []
    period_label = f"{MONTH_NAMES[month-1]}, год {(game['turn']-1)//12+1}"
    HEADS_KIND = {"info": "Хроника", "gold": "Рекорд месяца", "ok": "Достижение", "warn": "Молния"}
    def add(icon, text, kind="info", head=None):
        news.append(dict(icon=icon, text=text, kind=kind, head=head or HEADS_KIND[kind], period=period_label))
    add("📅", f"{MONTH_NAMES[month-1]}, ход {game['turn']}: {event_text} Размер рынка: {market} ед.", "info", "Событие месяца")
    if month == 12:
        add("🎄", f"Предновогодний спрос: премиальные матрёшки (качество >{DEC_PREMIUM_QUALITY:.0f}) получают +20% заказов.", "info", "Сезон")
    if month in ANNOUNCE_MONTHS:
        game["sub_types_open"] = random.sample([1, 2, 3], 2)
        names = f"{SUB_TYPE_NAMES[game['sub_types_open'][0]]} и {SUB_TYPE_NAMES[game['sub_types_open'][1]]}"
        add("🏛", f"Минпромторг в следующем месяце объявит конкурс субсидий по направлениям: {names}.", "gold", "Минпромторг")
    open_types = game.get("sub_types_open") or [1, 2]
    # --- Коалиция ---
    coal = game.get("coalition")
    if coal and coal["months"] > 0:
        coal["months"] -= 1
        if coal["months"] <= 0:
            add("🤝", f"Ценовая коалиция против «{coal['leader']}» распалась: участники вернулись к прежним ценам.", "info", "Ценовая коалиция")
            game["coalition"] = None; game["coalition_cd"] = COALITION_COOLDOWN
    else:
        game["coalition_cd"] = max(0, game.get("coalition_cd", 0) - 1)
        if game["turn"] >= 4 and game.get("coalition_cd", 0) == 0 and alive:
            share_lead_c = max(alive, key=lambda x: x.history[-1]["market_share"] if x.history else 0)
            mpi_lead_c = max(alive, key=lambda x: x.mpi_total)
            second = sorted([x.mpi_total for x in alive], reverse=True)[1] if len(alive) > 1 else 0
            share_val = share_lead_c.history[-1]["market_share"] if share_lead_c.history else 0
            if share_val > COALITION_SHARE * 100:
                lead = share_lead_c
            elif second and mpi_lead_c.mpi_total > COALITION_GAP * second:
                lead = mpi_lead_c
            else:
                lead = None
            if lead is not None:
                if random.random() < COALITION_CHANCE:
                    threats = [x for x in alive if x is not lead and x.is_bot]
                    random.shuffle(threats)
                    parts = [x.name for x in threats[:random.randint(2, min(4, len(threats)))]] if threats else []
                    if parts:
                        game["coalition"] = {"months": random.randint(1, 2), "participants": parts, "leader": lead.name}
                        add("🤝", f"Конкуренты объявили ценовую коалицию против «{lead.name}»: {', '.join(parts)} срезают цены и наращивают маркетинг.", "warn", "Ценовая коалиция")
    # --- Профсоюз триггер ---
    for c in alive:
        if c.workers > UNION_WORKERS and not c.union and not c.union_offer and random.random() < UNION_CHANCE:
            c.union_offer = True
            if c.is_bot:
                if c.cash > 15000:
                    c.union = True; c.union_offer = False; c.tension = max(0, c.tension - 25)
                    add("🧑🤝‍🧑", f"«{c.name}» подписала коллективный договор: зарплаты +{UNION_WAGE_UP*100:.0f}%, риск забастовок ниже.", "info", "Профсоюз")
                else:
                    c.union_offer = False; c.tension = min(100, c.tension + 8)
                    add("🧑‍🤝‍🧑", f"«{c.name}» отклонила коллективный договор профсоюза.", "warn", "Профсоюз")
    # --- Тендер лот ---
    if game["turn"] >= 3 and not game.get("tender") and month in TENDER_MONTHS:
        cname, vshare, pcap, qmin = random.choice(TENDER_CUSTOMERS)
        vol = max(20, int(market * vshare / 3))
        game["tender"] = dict(customer=cname, monthly_vol=vol, price_cap=round(game["avg_price"] * pcap, 1),
                              quality_min=qmin, open=True)
        add("🏛", f"Объявлен тендер госзакупок: {cname}. Объём {vol} ед./мес на 3 мес, потолок {game['tender']['price_cap']:.1f} ₽, качество ≥{qmin}.", "gold", "Госзакупки")
    if month in SUBSIDY_MONTHS:
        names = f"{SUB_TYPE_NAMES[open_types[0]]} и {SUB_TYPE_NAMES[open_types[1]]}"
        add("🏛", f"Открыто окно заявок на субсидии Минпромторга: {names}.", "gold", "Минпромторг")
    for c in alive: c.sub_won, c.sub_type, c.sub_msg = False, 0, ""
    if month in SUBSIDY_MONTHS:
        apps = []
        for c in alive:
            dd = decisions[c.name]
            if dd.get("subsidy_apply"):
                apps.append([c, dd, corp_points(dd.get("sub_pay", 0.0)) + c.reputation + c.mpi_total * 0.05])
        n = len(apps)
        if n == 0:
            add("🏛", "Конкурс Минпромторга завершился: заявок не подано.", "warn", "Минпромторг")
        elif n == 1:
            apps[0][0].sub_msg = "Отказ: подана только одна заявка (антимонопольное правило)."
            add("🏛", "Конкурс Минпромторга не состоялся: одна заявка (антимонопольное правило).", "warn", "Минпромторг")
        else:
            w = n // 2
            apps.sort(key=lambda x: -x[2])
            winners = [a[0].name for a in apps[:w]]
            for a in apps:
                if a[0].name in winners:
                    a[0].sub_won, a[0].sub_type = True, a[1]["sub_type"]
                    a[0].sub_msg = f"СУБСИДИЯ ВЫДАНА (балл {a[2]:.1f})."
                else:
                    a[0].sub_msg = f"Отказ: балл {a[2]:.1f} не прошёл."
            add("🏛", f"Итоги конкурса Минпромторга: заявок {n}, выдано {w}. Победители: {', '.join(winners)}.", "ok", "Минпромторг: итоги")
    # --- Персональные случайные события ---
    if alive and random.random() < 0.35:
        pc = random.choice(alive)
        pe = random.choice(PERSONAL_EVENTS)
        if pe == "recall":
            fine = pc.history[-1]["revenue"] * random.uniform(0.08, 0.12) if pc.history else 500
            pc.cash -= fine; pc.quality = max(20, pc.quality - 3); pc.reputation = max(0, pc.reputation - 0.5)
            add("⚠️", f"Отзыв партии у «{pc.name}»: брак росписи, штраф {fine:,.0f} ₽, качество и репутация просели.", "warn", "Отзыв партии")
        elif pe == "viral":
            pc.pr_next = True
            add("📯", f"Вирусный ролик с матрёшкой «{pc.name}»: +20% спроса на 2 месяца.", "ok", "Вирусный ролик")
        elif pe == "master_leave":
            if pc.staff["painters"] > 0 and pc.skill["painters"] >= 3:
                pc.skill["painters"] = max(1.0, pc.skill["painters"] - 0.5)
                rivals = [x for x in alive if x is not pc]
                if rivals:
                    rv = random.choice(rivals); rv.skill["painters"] = min(5.0, rv.skill["painters"] + 0.5)
                add("⚠️", f"Уход ключевого мастера из «{pc.name}»: навык росписи −0.5, конкурент переманил его.", "warn", "Уход ключевого мастера")
        elif pe == "corp_order":
            qty = int(pc.capacity() * 0.3); rev = qty * pc.history[-1]["price"] if pc.history else qty * 30
            pc.cash += rev; pc.inventory = max(0, pc.inventory - qty)
            add("📯", f"Крупный корпоративный заказ для «{pc.name}»: разовая продажа {qty} ед. на {rev:,.0f} ₽.", "ok", "Корпоративный заказ")
        elif pe == "warehouse_accident":
            loss = int(pc.inventory * random.uniform(0.2, 0.3))
            pc.inventory = max(0, pc.inventory - loss)
            add("⚠️", f"Складская авария у «{pc.name}»: потеряно {loss} ед. запасов.", "warn", "Складская авария")
        elif pe == "roscachestvo":
            if pc.quality >= 110:
                pc.reputation += 1
                add("✅", f"Проверка Роскачества у «{pc.name}»: пройдено, +1 репутация.", "ok", "Проверка Роскачества")
            else:
                pc.cash -= 1500
                add("⚠️", f"Проверка Роскачества у «{pc.name}»: не пройдено, штраф 1 500 ₽.", "warn", "Проверка Роскачества")
    game["merge_boost"] = {}
    bots_alive = [c for c in alive if c.is_bot]
    if (game["turn"] >= 5 and not game.get("merger_done") and len(bots_alive) >= 5
            and random.random() < 0.12):
        ranked = sorted(bots_alive, key=lambda x: x.mpi_total, reverse=True)
        absorber = ranked[0]; target = ranked[-1]
        if absorber is not target:
            game["merger_done"] = True
            tgt_share = target.history[-1]["market_share"] if target.history else 0.0
            absorber.cash += target.cash
            absorber.assets += target.assets
            absorber.inventory += target.inventory
            for p in PROFS: absorber.staff[p] += target.staff[p]
            absorber.novices += target.novices
            absorber.training += target.training
            absorber.contracts += target.contracts
            absorber.reputation = max(absorber.reputation, target.reputation)
            absorber.quality = max(absorber.quality, target.quality)
            absorber.reliability = max(absorber.reliability, target.reliability)
            absorber.patent = absorber.patent or target.patent
            absorber.brand = absorber.brand or target.brand
            absorber.union = absorber.union or target.union
            absorber.cum_rnd += target.cum_rnd
            absorber.workers = sum(absorber.staff.values()) + absorber.novices
            integ = absorber.cash * 0.05
            absorber.cash -= integ
            absorber.tension = min(100, absorber.tension + 15)
            game["merge_boost"][absorber.name] = 1 + tgt_share / 100
            if game.get("record_company") == target.name:
                game["record_company"] = absorber.name
            add("🏛", f"Слияние на рынке матрёшек: «{absorber.name}» поглотила «{target.name}». Мощности, касса, штат и контракты объединены; интеграция стоила {integ:,.0f} ₽ и дала всплеск напряжённости.", "warn", "Слияние и поглощение")
            add("🏛", f"Площадка «{target.name}» проходит ребрендинг: новая вывеска с логотипом «{absorber.name}».", "info", "Ребрендинг площадки")
            game["companies"].remove(target)
            alive.remove(target)
    attr = []
    for c in alive:
        dd = decisions[c.name]
        rep_mult = min(1.0 + REP_MKT_CAP, 1.0 + REP_MKT * c.reputation)
        mkt_eff = dd["marketing"] * rep_mult * (1.5 if (c.sub_won and c.sub_type == 2) else 1.0)
        a = c.quality * 0.02 + mkt_eff / 3000.0 - dd["price"] / 30.0 + REP_ATTRACT * c.reputation
        brand_now = c.quality >= BRAND_QUALITY and c.reputation >= BRAND_REPUTATION
        if brand_now: a *= BRAND_BONUS
        if brand_now and not c.brand:
            add("®", f"«{c.name}» получила право знака «Вознесенская матрёшка».", "ok", "Региональный бренд")
        if not brand_now and c.brand:
            add("®", f"«{c.name}» приостановила знак «Вознесенская матрёшка».", "warn", "Региональный бренд")
        c.brand = brand_now
        attr.append(max(0.1, a))
    total_attr = sum(attr)
    total_charity = 0.0
    charity_lines = []
    pool = game.setdefault("pool", dict(POOL_START))
    prod_mult_all = 0.85 if special == "sick" else 1.0
    for i, c in enumerate(alive):
        dd = decisions[c.name]
        # профсоюз выбор человека
        if c.union_offer and dd.get("union_choice"):
            if dd["union_choice"] == "sign":
                c.union = True; c.tension = max(0, c.tension - 25)
                add("🧑‍‍🧑", f"«{c.name}» подписала коллективный договор: зарплаты +{UNION_WAGE_UP*100:.0f}%.", "info", "Профсоюз")
            else:
                c.tension = min(100, c.tension + 8)
                add("🧑‍🤝‍🧑", f"«{c.name}» отклонила коллективный договор.", "warn", "Профсоюз")
            c.union_offer = False
        share = attr[i] / total_attr
        orders = market * share
        if month == 12 and c.quality > DEC_PREMIUM_QUALITY: orders *= DEC_PREMIUM_MULT
        if c.pr_next: orders *= 1.02; c.pr_next = False
        orders *= game.get("merge_boost", {}).get(c.name, 1.0)
        prod = max(0, min(int(dd["production"]), c.capacity()))
        if c.strike > 0:
            prod = int(prod * STRIKE_PROD_MULT); c.strike -= 1
            if c.strike == 0:
                add("🏭", f"Забастовка на «{c.name}» завершилась; качество просело из-за спешки.", "info", "Забастовка")
                c.quality = max(20, c.quality - 3)
        prod = int(prod * prod_mult_all)
        avail = c.inventory + prod
        contract_rev = 0.0; contract_pen = 0.0
        for ct in list(c.contracts):
            need_v = ct["monthly_vol"]; deliver = min(need_v, avail); avail -= deliver
            contract_rev += deliver * ct["price"]; ct["months"] -= 1
            if deliver < need_v:
                pen = (need_v - deliver) * ct["price"] * TENDER_PENALTY
                contract_pen += pen; c.reliability = max(0, c.reliability - 1); c.reputation = max(0, c.reputation - 1)
                add("⚠️", f"«{c.name}» недогрузила контракт {ct['customer']}: штраф {pen:,.0f} ₽.", "warn", "Госзакупки")
            else:
                c.reliability += 1
            if ct["months"] <= 0:
                c.contracts.remove(ct)
                add("✅", f"«{c.name}» исполнила контракт {ct['customer']}: +1 репутация.", "ok", "Госзакупки")
        sales = min(int(orders), avail)
        lost = max(0.0, orders - sales)
        c.inventory = avail - sales
        if sales > game.get("record_sales", 0):
            game["record_sales"] = sales; game["record_company"] = c.name; game["record_period"] = period_label
            add("📯", f"Новый рекорд отрасли: «{c.name}» продала {sales} ед. за месяц!", "gold", "Книга рекордов отрасли")
        c.premium = dd.get("premium", c.premium); c.loyalty = dd.get("loyalty", 0.0)
        prem_mult = 1 + c.premium / 100
        hire_fee = 0.0; hired_txt = []
        for p in PROFS:
            want = int(dd.get("hire", {}).get(p, 0))
            if want <= 0: continue
            speed = 0.6 + 0.015 * c.premium + c.reputation * 0.01
            got = min(want, pool.get(p, 0), max(1, round(want * speed)))
            if got > 0:
                pool[p] -= got; c.staff[p] += got; hire_fee += got * 0.5 * LABOR_WAGE[p] * prem_mult
                hired_txt.append(f"{PROF_RU[p]} +{got}")
        nov = int(dd.get("nov_hire", 0))
        if nov > 0: c.novices += nov; hire_fee += nov * 0.5 * NOVICE_WAGE; hired_txt.append(f"новички +{nov}")
        sever = 0.0
        for p in PROFS:
            f_ = min(int(dd.get("fire", {}).get(p, 0)), c.staff[p])
            if f_ > 0:
                c.staff[p] -= f_; sever += f_ * 2 * LABOR_WAGE[p] * prem_mult; pool[p] += f_
                c.reputation = max(0, c.reputation - 0.2 * f_)
        for prof in dd.get("train", []):
            if c.novices > 0: c.novices -= 1; c.training.append([TRAIN_MONTHS, prof])
        train_cost = len(c.training) * TRAIN_COST
        still = []
        for t in c.training:
            t[0] -= 1
            if t[0] <= 0:
                prof = t[1]; mentor = any(c.skill[q] >= 3.5 for q in ["turners","painters","assemblers"])
                c.staff[prof] += 1; c.skill[prof] = min(5.0, c.skill[prof] + 0.1 + (MENTOR_BONUS*0.1 if mentor else 0))
                hired_txt.append(f"выпуск → {PROF_RU[prof]}")
            else: still.append(t)
        c.training = still
        poached = []
        risk = max(0.0, 0.05 - 0.002*c.premium - c.loyalty/50000 - c.reputation*0.002)
        for p in ["painters", "turners"]:
            if c.staff[p] > 0 and c.skill[p] >= 3 and random.random() < risk:
                c.staff[p] -= 1; pool[p] += 1; poached.append(PROF_RU[p])
        if poached:
            add("👥", f"«{c.name}»: конкуренты переманили {', '.join(poached)}.", "warn", "Биржа труда")
        if hired_txt:
            add("👥", f"«{c.name}» кадровые движения: {', '.join(hired_txt)}.", "info", "Биржа труда")
        need = c.staff_need(prod)
        mgr_short = max(0, need["managers"] - c.staff["managers"]); coord = mgr_short * 500
        c.vacancies = {p: max(0, need[p] - c.staff[p]) for p in PROFS}
        tot_need = sum(need.values()) or 1
        c.vac_pct = sum(c.vacancies.values()) / tot_need * 100
        ot = c.vac_pct
        dt = ot * 0.5
        dt += (0 if c.premium >= 10 else (4 if c.premium < 0 else 1.5))
        dt += (3 if c.reputation < 2 else (-2 if c.reputation >= 5 else 0))
        if dd.get("fire") and sum(dd["fire"].values()) > 0: dt += 6
        dt -= c.loyalty / 2000.0
        dt -= (3 if c.union else 0)
        if ot == 0: dt -= 4
        c.tension = max(0, min(100, c.tension + dt))
        if c.tension > TENSION_STRIKE and c.strike == 0 and random.random() < (c.tension - TENSION_STRIKE)/30*0.5:
            c.strike = 1
            add("✊", f"На фабрике «{c.name}» забастовка: производство упадёт до {int(STRIKE_PROD_MULT*100)}% на месяц.", "warn", "Забастовка")
        c.quality += (c.skill["painters"] - 2.5) * 0.8
        qcap = 80 + 15 * c.skill["painters"]
        c.workers = sum(c.staff.values()) + c.novices
        labor = c.labor_cost() + coord + train_cost + hire_fee + sever
        mat = prod * MATERIAL_UNIT * max(0.85, 1 - c.cum_rnd * 1e-6)
        prod_cost = (mat + c.labor_cost()) * cost_factor + coord + train_cost + hire_fee + sever
        if c.patent: prod_cost *= (1 - PATENT_COST_CUT)
        storage = c.inventory * STORAGE_COST
        rep_mult = min(1.0 + REP_MKT_CAP, 1.0 + REP_MKT * c.reputation)
        mkt_eff = dd["marketing"] * rep_mult * (1.5 if (c.sub_won and c.sub_type == 2) else 1.0)
        charity = dd.get("charity", 0.0)
        rec_name, rec_mult = CHARITY_RECS.get(dd.get("charity_rec", 1), CHARITY_RECS[1])
        c.reputation = max(0.0, c.reputation + charity/1000.0*rec_mult - REP_EROSION)
        total_charity += charity
        if charity > 0:
            charity_lines.append(f"«{c.name}» — {charity:,.0f} ₽ ({rec_name})")
            if charity >= 1000 and random.random() < 0.4:
                c.pr_next = True
                add("♥", f"«{c.name}» получила тёплую заметку за щедрость: +2% спроса в след. месяце.", "ok", "Благотворительная ведомость")
        costs = prod_cost + storage + mkt_eff + dd["rnd"] + contract_pen
        revenue = sales * dd["price"] + contract_rev
        vat = revenue * 20 / 120 if c.tax == "osno" else 0.0
        operating = revenue - vat - costs - charity
        if c.tax == "osno": tax = max(0.0, operating) * 0.25
        elif c.tax == "usn6": tax = revenue * 0.06
        else: tax = max((revenue - costs) * 0.15, revenue * 0.01)
        profit = operating - tax
        grant = GRANT_FIXED if (c.sub_won and c.sub_type == 1) else 0.0
        refund = dd["investment"] * 0.3 if (c.sub_won and c.sub_type == 2) else 0.0
        base_loan = game.get("loan_rate", LOAN_RATE)
        loan_rate = base_loan * 0.5 if (c.sub_won and c.sub_type == 3) else base_loan
        cash_start = c.cash
        c.cash += revenue - vat - costs - charity - tax - dd["investment"] + refund + grant
        if dd.get("subsidy_apply"): c.cash -= dd.get("sub_pay", 0.0)
        if dd["loan"] > 0 and sum(l[0] for l in c.loans) + dd["loan"] <= LOAN_LIMIT:
            c.cash += dd["loan"]; c.loans.append([dd["loan"], loan_rate, dd["loan_term"], dd["loan_term"]])
        if dd["deposit"] > 0 and dd["deposit"] <= c.cash:
            c.cash -= dd["deposit"]; c.deposits.append([dd["deposit"], game.get("deposit_rate", DEPOSIT_RATE), dd["deposit_term"], dd["deposit_term"]])
        nl = []; fin_expense = 0.0
        for l in c.loans:
            l[2] -= 1
            if l[2] <= 0:
                interest = l[0]*l[1]*l[3]; c.cash -= l[0] + interest; fin_expense += interest
            else: nl.append(l)
        c.loans = nl
        nd = []; fin_income = 0.0
        for dp in c.deposits:
            dp[2] -= 1
            if dp[2] <= 0:
                interest = dp[0]*dp[1]*dp[3]; c.cash += dp[0] + interest; fin_income += interest
            else: nd.append(dp)
        c.deposits = nd
        depr = c.assets * DEPRECIATION
        c.assets *= (1 - DEPRECIATION); c.assets += dd["investment"]
        c.cum_rnd += dd["rnd"]
        c.quality += (dd["rnd"] * RND_GAIN - QUALITY_DECAY * 0.3) if dd["rnd"] > 0 else -QUALITY_DECAY
        c.quality = max(20.0, min(qcap, c.quality))
        patent = False
        if not c.patent and c.cum_rnd >= PATENT_THRESHOLD:
            if c.cum_rnd >= PATENT_PITY or random.random() < PATENT_CHANCE:
                c.patent = True; c.quality += PATENT_QUALITY; patent = True; c.mpi_total += PATENT_MPI_BONUS
                game.setdefault("patents_log", []).append({"company": c.name, "period": period_label})
                add("🔬", f"«{c.name}»: патент на новую роспись! +{PATENT_QUALITY:.0f} качества, −10% себестоимости, +{PATENT_MPI_BONUS} MPI.", "ok", "Наука и производство")
        c.neg_turns = c.neg_turns + 1 if c.cash < 0 else 0
        bankrupt_now = False
        if c.neg_turns == 2:
            add("⚠️", f"«{c.name}»: деньги в минусе 2-й месяц — ещё один и банкротство!", "warn")
        if c.neg_turns >= 3 and not (game.get("sandbox") and game["turn"] <= 6):
            c.bankrupt = True; bankrupt_now = True
            add("💀", f"«{c.name}»: БАНКРОТСТВО, выбывает с рынка.", "warn")
        dep_total = sum(dp[0] for dp in c.deposits)
        tier = charity_tier(charity)
        c.history.append(dict(turn=game["turn"], month=month, month_name=MONTH_NAMES[month-1],
            price=dd["price"], prod=prod, sales=sales, orders=orders, lost=lost, inventory=c.inventory,
            revenue=revenue, vat=vat, prod_cost=prod_cost, storage=storage, marketing=mkt_eff,
            rnd=dd["rnd"], charity=charity, charity_rec=rec_name, tier=tier, investment=dd["investment"],
            costs=costs, tax=tax, operating=operating, base=operating, fin_income=fin_income,
            fin_expense=fin_expense, roy_in=0.0, roy_out=0.0, profit=profit, cash=c.cash,
            cash_start=cash_start, quality=c.quality, reputation=c.reputation, market_share=share*100,
            capacity=c.capacity(), util=prod / c.capacity(), unit_cost=prod_cost/prod if prod>0 else 0.0,
            assets=c.assets, dep_total=dep_total, depr=depr, workers=c.workers, labor=labor,
            productivity=c.productivity_eff(), brand=c.brand, staff=dict(c.staff), skill=dict(c.skill),
            novices=c.novices, training=len(c.training), vac_pct=c.vac_pct, premium=c.premium,
            tension=c.tension, strike=c.strike, union=c.union, reliability=c.reliability,
            contracts=len(c.contracts), patent=patent, bankrupt=bankrupt_now))
        check_achievements(game, c, c.history[-1])
    # --- Розыгрыш тендера ---
    tnd = game.get("tender")
    if tnd and tnd.get("open"):
        bids = []
        for c in alive:
            dd = decisions[c.name]
            if dd.get("tender_apply") and c.quality >= tnd["quality_min"]:
                price = min(dd.get("tender_price", tnd["price_cap"]), tnd["price_cap"])
                price_score = max(0.0, 1 - price / tnd["price_cap"])
                qual_score = min(1.0, c.quality / (tnd["quality_min"] * 1.2))
                rel_score = min(1.0, 0.5 + c.reliability*0.1 + c.reputation*0.02)
                bids.append((0.6*price_score + 0.2*qual_score + 0.2*rel_score, c, price))
        if bids:
            bids.sort(key=lambda x: -x[0])
            sc_, wc, wprice = bids[0]
            total = wprice * tnd["monthly_vol"] * 3
            advance = total * TENDER_ADVANCE
            wc.cash += advance
            wc.contracts.append(dict(months=3, monthly_vol=tnd["monthly_vol"], price=wprice,
                                     customer=tnd["customer"], total=total))
            add("🏛", f"Тендер {tnd['customer']} выиграла «{wc.name}» (балл {sc_:.2f}, цена {wprice:.1f} ₽). Аванс {advance:,.0f} ₽.", "ok", "Госзакупки")
        else:
            add("🏛", f"Тендер {tnd['customer']} не состоялся: нет квалифицированных заявок.", "warn", "Госзакупки")
        game["tender"] = None
    # --- Роялти ---
    hl = [c for c in game["companies"] if c.history and c.history[-1]["turn"] == game["turn"]]
    if game.get("royalty"):
        patents = [c for c in hl if c.patent]
        if patents:
            for p in patents:
                incoming = sum(ROYALTY_RATE * c.history[-1]["revenue"] for c in hl if c is not p)
                p.history[-1]["roy_in"] = incoming; p.cash += incoming
            for c in hl:
                out = sum(ROYALTY_RATE * c.history[-1]["revenue"] for p in patents if p is not c)
                c.history[-1]["roy_out"] = out; c.cash -= out
    # --- Пул округа ---
    for p in PROFS:
        drain = round(pool.get(p, 0) * 0.05 * game.get("retention", 1.0))
        pool[p] = max(0, pool.get(p, 0) - drain)
    pool["assemblers"] = pool.get("assemblers", 0) + 2
    pool["turners"] = pool.get("turners", 0) + 1
    if month == 9: pool["painters"] = pool.get("painters", 0) + 1
    if month == 1: pool["managers"] = pool.get("managers", 0) + 1
    add("👥", f"Биржа труда: свободны сб {pool['assemblers']}, ток {pool['turners']}, мр {pool['painters']}, упр {pool['managers']}.", "info", "Биржа труда")
    game["social_capital"] = game.get("social_capital", 0.0) * SOC_DECAY + total_charity
    game["retention"] = max(0.4, 1 - game["social_capital"] / SOC_DIV)
    if charity_lines:
        add("♥", f"Благотворительная ведомость: {'; '.join(charity_lines)}. Соцкапитал {game['social_capital']:,.0f} ₽.", "info", "Благотворительная ведомость")
    else:
        add("♥", f"Благотворительная ведомость: бизнес не финансировал добрые дела. Соцкапитал тает: {game['social_capital']:,.0f} ₽.", "warn", "Благотворительная ведомость")
    mp = max([c.history[-1]["profit"] for c in hl] + [0.0]) or 1.0
    ms = max([c.history[-1]["market_share"] for c in hl] + [1e-9]) or 1.0
    mc = max([c.cash + c.history[-1]["dep_total"] for c in hl] + [0.0]) or 1.0
    mq = max([c.quality for c in hl] + [1e-9]) or 1.0
    for c in hl:
        h = c.history[-1]; funds = c.cash + h["dep_total"]
        h["mpi"] = 100 * (0.35*max(0.0,h["profit"])/mp + 0.25*h["market_share"]/ms + 0.25*max(0.0,funds)/mc + 0.15*c.quality/mq)
        c.mpi_total += h["mpi"]
    game["avg_price"] = sum(c.history[-1]["price"] for c in hl) / max(1, len(hl))
    game["market"], game["month"] = market, month
    top_sales = max(hl, key=lambda c: c.history[-1]["sales"])
    if top_sales.history[-1]["sales"] > 0:
        add("🏆", f"«{top_sales.name}» — лучшие продажи месяца: {int(top_sales.history[-1]['sales'])} ед.", "gold")
    top_rev = max(hl, key=lambda c: c.history[-1]["revenue"])
    if top_rev.history[-1]["revenue"] > 0:
        add("💰", f"«{top_rev.name}» — рекордная выручка месяца: {top_rev.history[-1]['revenue']:,.0f} ₽.", "gold")
    worst = min(hl, key=lambda c: c.history[-1]["profit"])
    if worst.history[-1]["profit"] < 0:
        add("📉", f"«{worst.name}» — крупнейший убыток месяца: {worst.history[-1]['profit']:,.0f} ₽.", "warn")
    notes = []
    for c in hl:
        h = c.history[-1]
        if len(c.history) > 1:
            prev_p = c.history[-2]["price"]
            if h["price"] > prev_p * 1.05 and factor < 1.0:
                notes.append(f"«{c.name}» подняла цену в падающем рынке — ждём потери доли")
            if h["inventory"] > 0.3 * max(1, h["prod"]):
                notes.append(f"у «{c.name}» склад съедает {h['storage']:,.0f} ₽/мес")
        if h.get("vac_pct", 0) > 20:
            notes.append(f"«{c.name}» не закрывает {h['vac_pct']:.0f}% вакансий")
    rep_leader = max(hl, key=lambda c: c.reputation)
    if rep_leader.reputation > 0.5:
        notes.append(f"«{rep_leader.name}» лидирует по репутации ({rep_leader.reputation:.1f})")
    for nt in notes[:3]:
        add("📊", nt, "info", "Аналитика")
    leader = max(hl, key=lambda c: c.mpi_total)
    if game.get("prev_leader") and game["prev_leader"] != leader.name:
        add("👑", f"Смена лидера! «{leader.name}» возглавляет зачёт.", "gold", "Смена лидера")
    game["prev_leader"] = leader.name
    game["news"] = news
    game["news_log"] = (game.get("news_log", []) + news)[-200:]
    game["next_event"] = roll_event()
    score = (game["next_event"][2]-1.0) - (game["next_event"][3]-1.0)
    if game["next_event"][4] > 0: score -= 0.06
    if game["next_event"][4] < 0: score += 0.06
    true_dir = "positive" if score > 0.03 else ("negative" if score < -0.03 else "stable")
    game["forecast_dir"] = true_dir if random.random() < 0.9 else random.choice([d for d in ("positive","negative","stable") if d != true_dir])

def execute_turn(game, cur):
    dec = dict(cur)
    sc = game.get("start_cash", START_CASH)
    open_types = game.get("sub_types_open") or [1, 2]
    next_m = (game["turn"] % 12) + 1
    for c in game["companies"]:
        if c.is_bot and not c.bankrupt:
            dec[c.name] = bot_decision(c, game["avg_price"], MONTH_SEASON[next_m-1], next_m,
                                       game["difficulty"], game["last_factor"], sc, open_types,
                                       game.setdefault("pool", dict(POOL_START)), game)
    run_turn(game, dec)
    if game.get("autosave", True): save_game(game, "autosave")
    game["phase"] = "report"; game["decisions_current"] = {}; st.session_state.gate = None
def build_advice(game, c):
    rows = [("Введение", f"Отчёт подготовлен по состоянию на ход {game['turn']}. Ниже — диагностика и целевые цифры на этот ход.")]
    rec = {}
    if c.history:
        last = c.history[-1]
        comps = [x for x in game["companies"] if x.history]
        avg_q = sum(x.quality for x in comps) / max(1, len(comps))
        unit = last["unit_cost"] if last["unit_cost"] > 0 else c.unit_cost(max(1, last["prod"]))
        if last["inventory"] > 0.2 * max(1, last["prod"]):
            rows.append(("Склад", f"Избыток {last['inventory']} ед. — снижайте цену или выпуск (см. цифры ниже)."))
        if last["price"] > game["avg_price"] * 1.1:
            rows.append(("Цена", "Текущая цена выше среднерыночной >10% — урежет долю, если не обоснована качеством."))
        if last["prod"] > 0 and last["price"] < unit:
            rows.append(("Цена", "Цена ниже себестоимости — каждая продажа убыточна."))
        if last["util"] < 0.6:
            rows.append(("Мощность", "Загрузка низкая — постоянные расходы размазаны; не расширяйте мощность, наращивайте спрос."))
        if last.get("vac_pct", 0) > 20:
            rows.append(("Кадры", f"Вакансии {last['vac_pct']:.0f}% — производство упирается в людей."))
        if c.reputation < 2:
            rows.append(("Репутация", "Низкая репутация удорожает маркетинг и найм."))
        if c.cash < 3 * FIXED_COST:
            rows.append(("Ликвидность", "Касса мала — держите подушку ≥ 3 месячных постоянных расходов."))
        q_edge = (c.quality - avg_q) / max(1.0, avg_q)
        price_floor = unit * 1.35
        price_market = game["avg_price"] * (1 + 0.5 * q_edge)
        rec_price = round(min(max(price_floor, price_market), game["avg_price"] * 1.3), 1)
        next_m = (game["turn"] % 12) + 1
        season_next = MONTH_SEASON[next_m - 1]
        exp_sales = last["sales"] * season_next
        rec_prod = int(max(0, min(c.capacity() * 0.9, exp_sales * 1.05 - last["inventory"] * 0.6)))
        exp_rev = rec_price * rec_prod
        rec_mkt = round(min(max(exp_rev * 0.10, 300), 8000), -2)
        rec_inv = round(min(c.cash * 0.20, c.assets * DEPRECIATION + 4000), -2) if (last["util"] >= 0.85 and c.cash > 15000) else round(c.assets * DEPRECIATION, -2)
        rec_rnd = round(min(c.cash * 0.10, 4000), -2) if (c.cum_rnd < PATENT_THRESHOLD and c.cash > 15000) else round(min(c.cash * 0.03, 1500), -2)
        rec_char = 500 if c.reputation < 3 else 300
        hire_txt = "; ".join(f"{PROF_RU[p]} +{c.vacancies[p]}" for p in PROFS if c.vacancies.get(p, 0) > 0) or "не требуется"
        if c.cash < 3 * FIXED_COST: fin_txt = f"взять кредит ≈ {round(3*FIXED_COST - c.cash, -2):,.0f} ₽"
        elif c.cash > 25000 and last["util"] < 0.8: fin_txt = f"положить депозит ≈ {round(c.cash*0.3, -2):,.0f} ₽"
        else: fin_txt = "кредит/депозит не требуются"
        rec = dict(price=rec_price, prod=rec_prod, mkt=rec_mkt, inv=rec_inv, rnd=rec_rnd, char=rec_char, hire=hire_txt, fin=fin_txt)
    if rec:
        rows.append(("── ЦЕЛЕВЫЕ ЦИФРЫ НА ЭТОТ ХОД ──", ""))
        rows.append(("Цена", f"{rec['price']:.1f} ₽/ед."))
        rows.append(("Производство", f"{rec['prod']} ед."))
        rows.append(("Маркетинг", f"{rec['mkt']:,.0f} ₽"))
        rows.append(("Инвестиции", f"{rec['inv']:,.0f} ₽"))
        rows.append(("НИОКР", f"{rec['rnd']:,.0f} ₽"))
        rows.append(("Благотворительность", f"{rec['char']:,.0f} ₽"))
        rows.append(("Найм", rec["hire"]))
        rows.append(("Финансы", rec["fin"]))
    rows.append(("Заключение", "Цифры рассчитаны по вашему балансу и позиции на рынке; их соблюдение удерживает маржу, долю и ликвидность."))
    return rows

def enc_sections():
    return [
        ("Быстрый старт и порядок хода",
         "Ход = 1 месяц. Во вкладке «Решения» каждая человеческая компания сдаёт решения по очереди (хот-сит до 10 человек). "
         "Боты сдают сами. Когда все готовы — ход рассчитывается. Кнопка «Следующий ход» — в сайдбаре. Песочница даёт подсказки и иммунитет от банкротства первые 6 месяцев."),
        ("Кадры, специальности и обучение",
         "Штат: сборщики, токари, мастера росписи, управленцы (1 на 8 работников). Производительность растёт от навыка токарей/сборщиков; "
         "потолок качества — от навыка мастеров росписи; дефицит управленцев даёт штраф координации. Новички дешевле, но 0.55 производительности; "
         "обучение 3 месяца по 1200 ₽/мес превращает новичка в специалиста; наставник (навык ≥3.5) даёт +0.5. Вакансии и % вакансий — в отчёте «Персонал». Пул округа ограничен, мастеров переманивают при низкой премии."),
        ("Напряжённость, забастовки, профсоюз",
         "Напряжённость копится от переработок (вакансии), низкой премии, слабой репутации и увольнений; сбрасывается бонусом лояльности, отдыхом и уступками. "
         f"При напряжённости >{TENSION_STRIKE} растёт шанс забастовки: производство падает до {int(STRIKE_PROD_MULT*100)}% на месяц. "
         f"При штате >{UNION_WORKERS} профсоюз может предложить коллективный договор: подписать (зарплаты +{UNION_WAGE_UP*100:.0f}%, риск забастовок ниже) или отклонить (дешевле сейчас, рискованнее потом)."),
        ("Ценовая коалиция против лидера",
         f"Если доля лидера >{COALITION_SHARE*100:.0f}% или его MPI >{COALITION_GAP}× второго, с шансом {COALITION_CHANCE*100:.0f}%/мес 2–4 конкурента объявляют ценовую коалицию: "
         "срезают цены и наращивают маркетинг на 1–2 месяца. Это их реальная жертва, а не подачка отстающим. После распада кулдаун 3 мес."),
        ("Госзакупки (тендеры)",
         "В марте/июне/сентябре/декабре открывается тендер одного из заказчиков (Администрация / Минкульт / «Русский сувенир») с объёмом, потолком цены и минимумом качества. "
         "Заявка = цена (не выше потолка) + обязательный объём на 3 мес. Победа по баллам 0.6×цена + 0.2×качество + 0.2×надёжность. Аванс 30% сразу; недогруз → штраф 10% и −надёжность/репутация; исполнение → +надёжность."),
        ("Решения: цена и производство",
         "Цена снижает привлекательность (−цена/30), но растит маржу. Производство ограничено мощностью; непроданное уходит на склад и стоит 1.5 ₽/ед./мес. Амортизация 1.7%/мес; инвестиции расширяют мощность."),
        ("Маркетинг, репутация и благотворительность",
         "Маркетинг усиливается репутацией ×(1+0.05×реп), потолок ×1.5. Репутация +0.04 привлекательности за пункт, эрозия −0.01/мес. Благотворительность +1 реп за 1000 ₽ × множитель получателя; на ОСНО вычитается из базы; тиры и значок ♥; PR-заметка 40% при ≥1000. Соцкапитал округа копит благотворительность и удерживает кадры."),
        ("НИОКР, патент и роялти",
         f"Патент: шанс 50% при НИОКР ≥{PATENT_THRESHOLD:,.0f}, гарантия при ≥{PATENT_PITY:,.0f}; даёт +{PATENT_QUALITY:.0f} качества, −10% себестоимости, +{PATENT_MPI_BONUS} MPI разово. Роялти (тумблер): конкуренты платят патентообладателю 0.5% выручки."),
        ("Случайные события: общие и персональные",
         "Общие бьют по всему рынку (бум, кризис, сырьё, ЦБ, эко-тренд, туризм, ГОСТ, грипп, краски). Персональные — по одной компании: отзыв партии, вирусный ролик, уход ключевого мастера, корпоративный заказ, складская авария, проверка Роскачества. Все попадают в газету с фото."),
        ("Финансы, налоги, банкротство",
         "ОСНО 25% (благотворительность вычитается), УСН-6, УСН-15. Банкротство: деньги в минусе 3 месяца подряд. В песочнице первые 6 месяцев банкротство отключено."),
        ("Субсидии Минпромторга",
         "Окна июнь и декабрь, анонс в мае и ноябре. Конкурс на 2 из 3 направлений. Балл = 50 + min(50, плата/100) + репутация + MPI×0.05. Победителей ≤50%; одна заявка = отказ. Грант 10 000 ₽."),
        ("Достижения игрока (ачивки)",
         "Открываются по ходу игры: Первая прибыль, Первый патент, Первый госконтракт, Пережил забастовку, Меценат, Носитель бренда, Рекордсмен отрасли, Крупный работодатель, Мастер качества (≥120). Отображаются бейджами на дашборде."),
        ("MPI, звания, Зал славы",
         "MPI = 100×(0.35×прибыль + 0.25×доля + 0.25×средства + 0.15×качество), компоненты делятся на лидера месяца; итог = сумма. Звания года и Зал славы округа."),
        ("Словарь",
         "Загрузка, соцкапитал, pity-timer, роялти, хот-сит, конверт развития ботов, вакансия, наставник, премия к зарплате, напряжённость, коалиция, тендер, надёжность."),
    ]

if "game" not in st.session_state: st.session_state.game = None
if "book_page" not in st.session_state: st.session_state.book_page = 0
if "view_company" not in st.session_state: st.session_state.view_company = None
if "gate" not in st.session_state: st.session_state.gate = None
if "print_doc" not in st.session_state: st.session_state.print_doc = None
game = st.session_state.game

if game is None:
    _lg = logo_b64()
    _logo_html = f"<img class='mk-logo' src='{_lg}'>" if _lg else "<div class='mk-emblem'>МК</div>"
    st.markdown(f"""
    <div class='mk-hero'>
      {_logo_html}
      <div class='mk-title'>МАСТЕР КАПИТАЛА</div>
      <div class='mk-sub'>экономический симулятор Вознесенского округа</div>
      <div class='mk-slogan'>Каждое решение — капитал.<br>От цеха — до холдинга.</div>
      <div class='mk-chips'><span>◆ Деревообработка и ЧПУ</span><span>▲ Рынок и конкуренция</span><span>♜ Субсидии и госзакупки</span><span>👥 Биржа труда</span><span>🤝 Слияния и коалиции</span><span>🏅 Достижения</span><span>■ Газета «Рыночный вестникъ»</span></div>
    </div>""", unsafe_allow_html=True)
    hof = hof_load()
    if hof:
        with st.expander("🏆 Зал славы округа"):
            for r in hof[:10]:
                st.markdown(f"**{r.get('company')}** — MPI {r.get('mpi'):.1f} · {r.get('turns')} ходов · {r.get('date')}")
    saves = list_saves()
    if saves:
        with st.expander("Загрузить сохранение"):
            slot = st.selectbox("Файл сохранения", saves)
            if st.button("Загрузить игру"):
                st.session_state.game = load_game(slot); st.rerun()
    with st.expander(" Правила и Энциклопедия"):
        for t, body in enc_sections():
            st.markdown(f"**{t}**  \n{body}")
    with st.form("setup"):
        c1, c2 = st.columns(2)
        with c1:
            humans_n = st.slider("Игроков-людей (хот-сит)", 1, 10, 1)
            human_names = [st.text_input(f"Компания игрока {i+1}", "Моя компания" if i == 0 else f"Игрок {i+1}") for i in range(humans_n)]
            tax = st.selectbox("Налоговый режим (для всех людей)", list(TAX_REGIMES.keys()), format_func=lambda x: TAX_REGIMES[x])
            sandbox = st.checkbox("Песочница: подсказки + иммунитет от банкротства 6 мес", value=False)
        with c2:
            nbots = st.slider("Ботов-конкурентов", 0, 9, 6)
            diff = st.selectbox("Сложность ботов", ["easy", "medium", "hard"],
                                format_func=lambda x: {"easy": "Лёгкие", "medium": "Средние", "hard": "Сложные"}[x])
            royalty = st.checkbox("Роялти: конкуренты платят патентообладателю 0.5% выручки", value=False)
        turns = st.slider("Длительность игры (месяцев)", 12, 36, 24)
        start_cash = st.selectbox("Стартовый капитал", list(START_OPTIONS.keys()), format_func=lambda x: START_OPTIONS[x], index=0)
        if st.form_submit_button("Начать игру", use_container_width=True, type="primary"):
            seen = set(); uniq = []
            for nm in human_names:
                base = (nm or "Игрок").strip(); cand = base; i = 2
                while cand in seen: cand = f"{base} {i}"; i += 1
                seen.add(cand); uniq.append(cand)
            g = dict(turn=0, phase="decisions", companies=[], avg_price=START_PRICE, last_factor=1.0,
                     news=[], news_log=[], market=BASE_MARKET, month=1, max_turns=turns, difficulty=diff,
                     player=uniq[0], humans=uniq, prev_leader=None, next_event=None, forecast_dir=None,
                     cost_factor=1.0, loan_rate=LOAN_RATE, deposit_rate=DEPOSIT_RATE, record_sales=0,
                     record_company="", record_period="", patents_log=[], start_cash=start_cash,
                     sub_types_open=None, decisions_current={}, social_capital=0.0, retention=1.0,
                     royalty=royalty, sandbox=sandbox, pool=dict(POOL_START), achievements={},
                     coalition=None, coalition_cd=0, tender=None)
            for nm in uniq:
                g["companies"].append(Company(nm, is_bot=False, tax=tax, start_cash=start_cash))
            for i in range(nbots):
                g["companies"].append(Company(BOT_NAMES[i], is_bot=True, strategy=BOT_STRATS[i % 9], start_cash=start_cash))
            st.session_state.game = g; st.session_state.view_company = uniq[0]; st.rerun()
    st.stop()

humans = game.get("humans", [game.get("player", "Моя компания")])
if st.session_state.view_company not in humans: st.session_state.view_company = humans[0]
viewer = next(c for c in game["companies"] if c.name == st.session_state.view_company)
humans_alive = [nm for nm in humans if not next(c for c in game["companies"] if c.name == nm).bankrupt]
over = game["turn"] >= game["max_turns"] or not humans_alive
year = (game["turn"] - 1) // 12 + 1
month_label = f"{MONTH_NAMES[game['month'] - 1]}, год {year}"

if over and not game.get("hof_written"):
    winner = max(game["companies"], key=lambda c: c.mpi_total)
    hof_add({"date": datetime.now().strftime("%d.%m.%Y"), "company": winner.name,
             "mpi": round(winner.mpi_total, 1), "turns": game["turn"], "humans": len(humans),
             "sandbox": bool(game.get("sandbox")), "titles": compute_titles(game)})
    game["hof_written"] = True

if st.session_state.get("print_doc"):
    kind = st.session_state.print_doc[0]
    pname = st.session_state.print_doc[1] if len(st.session_state.print_doc) > 1 else None
    st.markdown(f"<div class='print-head'><div class='ph-t'>Вознесенский муниципальный округ · бизнес-симулятор «МЭКОМ+»</div>"
                f"<div class='ph-s'>Документ сформирован {datetime.now().strftime('%d.%m.%Y %H:%M')} · ход {game['turn']}, {month_label}</div></div>", unsafe_allow_html=True)
    if st.button("← Вернуться в игру"):
        st.session_state.print_doc = None; st.rerun()
    if kind == "rank":
        st.markdown("#### Общий зачёт (MPI за всю игру)")
        st.markdown(rank_html(game, pname or game.get("player", "")), unsafe_allow_html=True)
    elif kind in ("team", "pack"):
        c = next(x for x in game["companies"] if x.name == pname)
        st.markdown(f"#### Отчёт команды: {c.name}")
        if c.history:
            last = c.history[-1]
            inv_val = last["inventory"] * last["unit_cost"]
            loans_sum = sum(l[0] for l in c.loans)
            total_assets = last["cash"] + last["assets"] + inv_val + last["dep_total"]
            equity = total_assets - loans_sum
            st.markdown(paper_html("ОТЧЁТ О ПРИБЫЛЯХ И УБЫТКАХ", f"{c.name} · {last['month_name']}", [
                ("Выручка", f"{last['revenue']:,.0f} ₽", ""), ("(−) НДС", f"{last['vat']:,.0f} ₽", ""),
                ("(−) Себестоимость", f"{last['prod_cost']:,.0f} ₽", ""), ("(−) Хранение", f"{last['storage']:,.0f} ₽", ""),
                ("(−) Маркетинг", f"{last['marketing']:,.0f} ₽", ""), ("(−) НИОКР", f"{last['rnd']:,.0f} ₽", ""),
                ("(−) Благотворительность", f"{last['charity']:,.0f} ₽", ""),
                ("= Прибыль от продаж", f"{last['operating']:,.0f} ₽", ""),
                ("= Прибыль до налога", f"{last['base']:,.0f} ₽", ""), ("(−) Налог", f"{last['tax']:,.0f} ₽", ""),
                ("= ЧИСТАЯ ПРИБЫЛЬ", f"{last['profit']:,.0f} ₽", "total")], PAL[2]), unsafe_allow_html=True)
            st.markdown(paper_html("ПЕРСОНАЛ И ОБУЧЕНИЕ", f"{c.name} · {last['month_name']}",
                [(f"{PROF_RU[p]}: занято/навык/вакансии", f"{last['staff'][p]}/{last['skill'][p]:.1f}/{c.vacancies.get(p,0)}", "") for p in PROFS] + [
                ("Новички / в обучении", f"{last['novices']}/{last['training']}", ""),
                ("Вакансии (%)", f"{last['vac_pct']:.0f}%", ""),
                ("Напряжённость", f"{last['tension']:.0f}/100", ""),
                ("ФОТ", f"{last['labor']:,.0f} ₽", "total")], PAL[1]), unsafe_allow_html=True)
        if kind == "pack":
            st.markdown("#### Общий зачёт"); st.markdown(rank_html(game, pname), unsafe_allow_html=True)
    elif kind == "news":
        st.markdown(masthead_html(game["turn"], month_label), unsafe_allow_html=True)
        for n in game.get("news", []):
            st.markdown(clip_html(n, month_label), unsafe_allow_html=True)
    elif kind == "rules":
        for i, (t, body) in enumerate(enc_sections()):
            st.markdown(f"<div class='paper' style='--pc:{PAL[i % 5]}'><div class='paper-h'>{t}</div>"
                        f"<div class='paper-s'>Энциклопедия игры «Вознесенская матрёшка»</div></div>", unsafe_allow_html=True)
            st.markdown(body)
    elif kind == "diploma":
        rank_pos = sorted([x for x in game["companies"] if x.history], key=lambda x: x.mpi_total, reverse=True)
        for i, cc in enumerate(rank_pos[:3]):
            st.markdown(diploma_html(game, cc, i + 1), unsafe_allow_html=True)
        st.markdown("#### Звания года")
        for t in compute_titles(game):
            st.markdown(f"- {t}")
    components.html("<script>window.parent.print()</script>", height=0)
    st.caption("Если окно печати не открылось — нажмите Ctrl+P.")
    st.stop()

with st.sidebar:
    st.markdown(f"<div class='avatar'>{viewer.name[0].upper()}</div><div class='avname'>{viewer.name}</div>", unsafe_allow_html=True)
    if len(humans) > 1:
        vc = st.selectbox("Смотрю отчёты компании", humans, index=humans.index(st.session_state.view_company))
        st.session_state.view_company = vc
        viewer = next(c for c in game["companies"] if c.name == vc)
    st.markdown(f"**Режим:** {TAX_REGIMES[viewer.tax]}  \n**Качество:** {viewer.quality:.1f} {dots(viewer.quality, 20)}  \n"
                f"**Репутация:** {viewer.reputation:.1f} {dots(viewer.reputation, 2)}  \n"
                f"**Патент:** {'есть' if viewer.patent else 'нет'}  \n"
                f"**Бренд:** {'®' if viewer.brand else '—'}  \n"
                f"**Работники:** {viewer.workers} чел.  \n**Мощность:** {viewer.capacity()} ед.  \n**Склад:** {viewer.inventory} ед.", unsafe_allow_html=True)
    st.markdown(f"**Напряжённость:** {viewer.tension:.0f}/100 · **Вакансии:** {viewer.vac_pct:.0f}%  \n"
                f"**Контрактов:** {len(viewer.contracts)} · **Надёжность:** {viewer.reliability:.0f}", unsafe_allow_html=True)
    with st.expander("Биржа труда"):
        pool = game.setdefault("pool", dict(POOL_START))
        st.markdown(f"Свободны: сб {pool['assemblers']}, ток {pool['turners']}, мр {pool['painters']}, упр {pool['managers']}.")
    st.markdown("---"); st.markdown("### Сохранение")
    game["autosave"] = st.checkbox("Автосейв каждый ход", game.get("autosave", True))
    slot_name = st.text_input("Имя сохранения", "slot1")
    if st.button("Сохранить игру"):
        save_game(game, slot_name); st.success(f"Сохранено: saves/{slot_name}.json")
    if game["phase"] == "report" and not over:
        if st.button("Следующий ход", use_container_width=True, type="primary"):
            game["phase"] = "decisions"; game["decisions_current"] = {}; st.session_state.gate = None; st.rerun()
    if st.button("Новая игра"):
        st.session_state.game = None; st.session_state.book_page = 0; st.session_state.gate = None; st.rerun()

h1, h2 = st.columns([3, 2])
h1.markdown("### Панель управления")
h2.markdown(f"<div class='chips'><span class='chip'>■ Ход {game['turn']}/{game['max_turns']}</span>"
            f"<span class='chip'>◆ Рынок {game['market']} ед.</span><span class='chip'>$ Ср. цена {game['avg_price']:.1f} ₽</span>"
            f"<span class='chip'>♥ Соцкапитал {game.get('social_capital', 0):,.0f} ₽</span></div>", unsafe_allow_html=True)
st.markdown(calendar_html(game["turn"]), unsafe_allow_html=True)
st.progress(game["turn"] / game["max_turns"])

tabs = st.tabs(["Дашборд", "Решения", "Рейтинг", "Газета", "Отчётная книга", "Динамика", "🖨 Печать", "📖 Энциклопедия"])

with tabs[0]:
    if viewer.history:
        last = viewer.history[-1]
        prev = viewer.history[-2] if len(viewer.history) > 1 else None
        d_profit = (last["profit"] - prev["profit"]) if prev else None
        d_cash = ((last["cash"] + last["dep_total"]) - (prev["cash"] + prev["dep_total"])) if prev else None
        st.markdown("<div class='kpi-row'>" + tile(PAL[0], "$", "Деньги (касса+банк)", f"{last['cash'] + last['dep_total']:,.0f} ₽", d_cash)
                    + tile(PAL[2], "▲", "Чистая прибыль", f"{last['profit']:+,.0f} ₽", d_profit)
                    + tile(PAL[3], "★", "Качество", f"{last['quality']:.1f}")
                    + tile(PAL[4], "♥", "Репутация", f"{last['reputation']:.1f}") + "</div>", unsafe_allow_html=True)
        ach = game.get("achievements", {}).get(viewer.name, [])
        if ach:
            st.markdown("<div>" + "".join(f"<span class='ach'>🏅 {dict(ACH_DEFS).get(a, a)}</span>" for a in ach) + "</div>", unsafe_allow_html=True)
        if game.get("sandbox"):
            hints = []
            if last["inventory"] > 0.2 * max(1, last["prod"]): hints.append("склад велик — снизьте цену/выпуск")
            if last["price"] > game["avg_price"] * 1.15: hints.append("цена выше рынка >15%")
            if last.get("vac_pct", 0) > 20: hints.append("вакансии >20% — наймите/обучите")
            if viewer.tension > 60: hints.append("высокая напряжённость — риск забастовки")
            if hints: st.info("**Советник (песочница):** " + "; ".join(hints))
        if viewer.bankrupt: st.error("Компания обанкротилась.")
        elif viewer.neg_turns == 2: st.warning("Деньги в минусе 2-й месяц!")
        if viewer.sub_msg: st.info(viewer.sub_msg)
        g1, g2, g3 = st.columns(3)
        with g1, st.container(border=True):
            st.markdown("<div class='ct'>Доли рынка за месяц</div>", unsafe_allow_html=True)
            comps = [c for c in game["companies"] if c.history]
            fig = go.Figure(go.Pie(labels=[c.name for c in comps], values=[c.history[-1]["market_share"] for c in comps],
                                   hole=0.62, textinfo="percent", marker=dict(colors=[PAL[i % 5] for i in range(len(comps))])))
            fig_base(fig, 300); st.plotly_chart(fig, use_container_width=True)
        with g2, st.container(border=True):
            st.markdown("<div class='ct'>Финансы компании</div>", unsafe_allow_html=True)
            dhp = pd.DataFrame(viewer.history); per = dhp["month_name"] + " " + dhp["turn"].astype(str)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=per, y=dhp["revenue"], name="Выручка", mode="lines+markers", line=dict(color="#eb6b56", width=3)))
            fig.add_trace(go.Scatter(x=per, y=dhp["profit"], name="Прибыль", mode="lines+markers", line=dict(color="#47b39d", width=3)))
            fig_base(fig, 300, legend=True); st.plotly_chart(fig, use_container_width=True)
        with g3, st.container(border=True):
            st.markdown("<div class='ct'>Загрузка и склад</div>", unsafe_allow_html=True)
            fig = go.Figure()
            fig.add_trace(go.Indicator(mode="gauge+number", value=round(last["util"]*100), number=dict(suffix="%"),
                                       title=dict(text="Загрузка"), domain=dict(x=[0.02,0.45], y=[0.05,0.95])))
            fig.add_trace(go.Indicator(mode="gauge+number", value=round(min(100, last["inventory"]/max(1,last["capacity"])*100)), number=dict(suffix="%"),
                                       title=dict(text="Склад"), domain=dict(x=[0.55,0.98], y=[0.05,0.95])))
            fig_base(fig, 300); st.plotly_chart(fig, use_container_width=True)
        g4, g5 = st.columns([3, 2])
        with g4, st.container(border=True):
            st.markdown("<div class='ct'>Продажи компаний с начала года</div><div class='cs'>столбики накопленно; серый — тот же период прошлого года</div>", unsafe_allow_html=True)
            rows = []
            for c in game["companies"]:
                for h in c.history: rows.append(dict(name=c.name, turn=h["turn"], sales=h["sales"]))
            dfall = pd.DataFrame(rows)
            if len(dfall):
                dfall["year"] = ((dfall["turn"]-1)//12)+1; dfall["moy"] = ((dfall["turn"]-1)%12)+1
                cur_year = (game["turn"]-1)//12+1; cur_moy = ((game["turn"]-1)%12)+1
                cur = dfall[dfall["year"]==cur_year].groupby("name")["sales"].sum()
                fig = go.Figure()
                fig.add_trace(go.Bar(x=cur.index, y=cur.values, name=f"Год {cur_year}",
                                     marker=dict(color=[PAL[i%5] for i in range(len(cur))])))
                if cur_year >= 2:
                    pv = dfall[(dfall["year"]==cur_year-1) & (dfall["moy"]<=cur_moy)].groupby("name")["sales"].sum().reindex(cur.index).fillna(0)
                    fig.add_trace(go.Bar(x=pv.index, y=pv.values, name=f"Год {cur_year-1}", marker=dict(color="#b8b8b8")))
                fig.update_layout(barmode="group"); fig_base(fig, 320, legend=True)
                st.plotly_chart(fig, use_container_width=True)
        with g5, st.container(border=True):
            st.markdown("<div class='ct'>Динамика MPI (топ-5)</div>", unsafe_allow_html=True)
            top5 = sorted([c for c in game["companies"] if c.history], key=lambda c: c.mpi_total, reverse=True)[:5]
            fig = go.Figure()
            for i, c in enumerate(top5):
                dc = pd.DataFrame(c.history)
                fig.add_trace(go.Scatter(x=dc["month_name"]+" "+dc["turn"].astype(str), y=dc["mpi"], name=c.name,
                                         mode="lines+markers", line=dict(color=PAL[i%5], width=3)))
            fig_base(fig, 320, legend=True); st.plotly_chart(fig, use_container_width=True)
        st.markdown("#### Главное за месяц")
        st.markdown(news_html(game.get("news", [])), unsafe_allow_html=True)
        if over:
            st.markdown("## ИТОГИ ИГРЫ"); st.markdown(rank_html(game, viewer.name), unsafe_allow_html=True)
            st.markdown("#### Звания года")
            for t in compute_titles(game): st.markdown(f"- {t}")
            st.balloons()
            if st.button("🎓 Печать дипломов (топ-3 + звания)", type="primary"):
                st.session_state.print_doc = ("diploma",); st.rerun()
    else:
        st.info("Игра создана. Перейдите во вкладку «Решения».")

with tabs[1]:
    if game["phase"] == "decisions" and not over:
        cur = game.setdefault("decisions_current", {})
        pending = [nm for nm in humans_alive if nm not in cur]
        if pending:
            nm = pending[0]
            company = next(c for c in game["companies"] if c.name == nm)
            if len(humans_alive) == 1 or st.session_state.gate == nm:
                next_m = (game["turn"] % 12) + 1
                st.markdown(f"<div class='chips'><span class='chip'>◆ Компания: {nm}</span>"
                            f"<span class='chip'>■ {MONTH_NAMES[next_m-1]}, сезонность ×{MONTH_SEASON[next_m-1]:.2f}</span>"
                            f"<span class='chip'>▲ Мощность {company.capacity()}</span><span class='chip'>□ Склад {company.inventory}</span>"
                            f"<span class='chip'>$ {company.cash:,.0f} ₽</span><span class='chip'>№ Работники {company.workers}</span>"
                            f"<span class='chip'>♥ Репутация {company.reputation:.1f}</span><span class='chip'>! Напряжённость {company.tension:.0f}</span></div>", unsafe_allow_html=True)
                fd = game.get("forecast_dir")
                if fd:
                    ft = {"positive": "рост спроса / снижение затрат", "negative": "падение спроса / рост затрат",
                          "stable": "стабильная динамика"}[fd]
                    st.info(f"◆ Прогноз «Рыночного вестника»: **{ft}**. Точность 90%.")
                consult_cost = min(5000, max(500, round(0.02 * (company.cash + sum(d[0] for d in company.deposits) + company.assets), -2)))
                can_consult = (game.get("consult_count", 0) == 0) or (game["turn"] - game.get("consult_last_turn", -99) >= 4)
                with st.expander(f"🧠 Консультация «Стратегия+» ({consult_cost:,.0f} ₽)"):
                    if can_consult:
                        if st.button("Заказать отчёт-подсказку на этот ход", key=nm + "_consult"):
                            company.cash -= consult_cost
                            game["consult_count"] = game.get("consult_count", 0) + 1
                            game["consult_last_turn"] = game["turn"]
                            game["consult_doc"] = build_advice(game, company)
                            game["consult_doc_turn"] = game["turn"]
                            st.rerun()
                    else:
                        left = 4 - (game["turn"] - game.get("consult_last_turn", -99))
                        st.caption(f"Следующая консультация через {max(0, left)} ход(а).")
                    if game.get("consult_doc") and game.get("consult_doc_turn") == game["turn"]:
                        st.markdown(paper_html("ОТЧЁТ КОНСАЛТИНГОВОЙ ФИРМЫ «СТРАТЕГИЯ+»",
                                               f"для {company.name} · ход {game['turn']}", game["consult_doc"], PAL[0],
                                               stamp=STAMP_CONSULT), unsafe_allow_html=True)
                with st.form("dec_" + nm):
                    fc, pc = st.columns(2)
                    with fc, st.container():
                        st.markdown("<div id='card-finance' style='display:none'></div><div class='tag' style='--c:#1f6fb2'><span class='tag-hole'></span>ФИНАНСЫ: КРЕДИТ И ДЕПОЗИТ</div>", unsafe_allow_html=True)
                        with st.container():
                            st.markdown("<div id='panel-finance' style='display:none'></div>", unsafe_allow_html=True)
                            free_loan = LOAN_LIMIT - sum(l[0] for l in company.loans)
                            loan = st.number_input(f"Кредит, ₽ ({game.get('loan_rate', LOAN_RATE)*100:.1f}%/мес)", 0.0, max(0.0, free_loan), 0.0, 1000.0, key=nm+"_loan")
                            loan_term = st.slider("Срок кредита, мес.", 3, 12, 6, key=nm+"_loan_term")
                            if loan > 0:
                                repay = loan * (1 + game.get("loan_rate", LOAN_RATE) * loan_term)
                                st.caption(f"Вернуть: **{repay:,.0f} ₽**")
                            deposit = st.number_input(f"Депозит, ₽ ({game.get('deposit_rate', DEPOSIT_RATE)*100:.1f}%/мес)", 0.0, max(0.0, company.cash), 0.0, 1000.0, key=nm+"_dep")
                            deposit_term = st.slider("Срок депозита, мес.", 3, 12, 6, key=nm+"_dep_term")
                            if deposit > 0:
                                payout = deposit * (1 + game.get("deposit_rate", DEPOSIT_RATE) * deposit_term)
                                st.caption(f"Получите: **{payout:,.0f} ₽**")
                    with pc, st.container():
                        st.markdown("<div id='card-subsidy' style='display:none'></div><div class='tag' style='--c:#462446'><span class='tag-hole'></span>СУБСИДИЯ МИНПРОМТОРГА</div>", unsafe_allow_html=True)
                        with st.container():
                            st.markdown("<div id='panel-subsidy' style='display:none'></div>", unsafe_allow_html=True)
                            open_types = game.get("sub_types_open") or [1, 2]
                            sub_apply = False; sub_type = open_types[0]; sub_pay = 0.0
                            if next_m in SUBSIDY_MONTHS:
                                st.markdown(f"Направления: **{SUB_TYPE_NAMES[open_types[0]]}** и **{SUB_TYPE_NAMES[open_types[1]]}**.")
                                sub_apply = st.checkbox("Подать заявку", key=nm+"_sub")
                                if sub_apply:
                                    sub_type = st.selectbox("Направление", open_types, format_func=lambda x: SUB_TYPE_NAMES[x], key=nm+"_subtype")
                                    sub_pay = st.number_input("Плата Корпорации, ₽ (0=сами)", 0.0, 5000.0, 0.0, 100.0, key=nm+"_subpay")
                                    st.caption(f"Баллы документов: **{corp_points(sub_pay):.0f}**")
                            else:
                                wait = min((m - next_m) % 12 for m in SUBSIDY_MONTHS) or 12
                                st.caption(f"Окно заявок через {wait} мес.")
                    r1, r2 = st.columns(2)
                    with r1, st.container():
                        st.markdown("<div id='card-price' style='display:none'></div><div class='tag' style='--c:#1a7a4a'><span class='tag-hole'></span>ЦЕНА И ПРОИЗВОДСТВО</div>", unsafe_allow_html=True)
                        with st.container():
                            st.markdown("<div id='panel-price' style='display:none'></div>", unsafe_allow_html=True)
                            price = st.number_input("Цена, ₽/ед.", 1.0, 200.0, float(game["avg_price"]), 0.5, key=nm+"_price")
                            production = st.slider("Производство, ед.", 0, company.capacity(), int(company.capacity()*0.85), key=nm+"_prod")
                    with r2, st.container():
                        st.markdown("<div id='card-charity' style='display:none'></div><div class='tag' style='--c:#e8b30a'><span class='tag-hole'></span>МАРКЕТИНГ И БЛАГОТВОРИТЕЛЬНОСТЬ</div>", unsafe_allow_html=True)
                        with st.container():
                            st.markdown("<div id='panel-charity' style='display:none'></div>", unsafe_allow_html=True)
                            marketing = st.number_input("Маркетинг, ₽", 0.0, 500000.0, 0.0, 500.0, key=nm+"_mkt")
                            cc1, cc2 = st.columns(2)
                            with cc1: charity = st.number_input("Благотворительность, ₽", 0.0, 100000.0, 0.0, 100.0, key=nm+"_ch")
                            with cc2: charity_rec = st.selectbox("Получатель", list(CHARITY_RECS.keys()), format_func=lambda x: f"{CHARITY_RECS[x][0]} ×{CHARITY_RECS[x][1]}", key=nm+"_rec")
                    with st.container():
                        st.markdown("<div id='card-growth' style='display:none'></div><div class='tag' style='--c:#e07b1f'><span class='tag-hole'></span>РОСТ: ИНВЕСТИЦИИ И НИОКР</div>", unsafe_allow_html=True)
                        with st.container():
                            st.markdown("<div id='panel-growth' style='display:none'></div>", unsafe_allow_html=True)
                            gg1, gg2 = st.columns(2)
                            with gg1: investment = st.number_input("Инвестиции, ₽", 0.0, 500000.0, round(company.assets*DEPRECIATION, -2), 500.0, key=nm+"_inv")
                            with gg2: rnd = st.number_input("НИОКР, ₽", 0.0, 500000.0, 0.0, 500.0, key=nm+"_rnd")
                    with st.container():
                        st.markdown("<div id='card-hr' style='display:none'></div><div class='tag' style='--c:#0e7c86'><span class='tag-hole'></span>КАДРЫ И ОБУЧЕНИЕ</div>", unsafe_allow_html=True)
                        with st.container():
                            st.markdown("<div id='panel-hr' style='display:none'></div>", unsafe_allow_html=True)
                            hcol = st.columns(4); hire = {}
                            for idx, p in enumerate(PROFS):
                                with hcol[idx]: hire[p] = st.number_input(f"Нанять {PROF_RU[p]}", 0, 10, 0, 1, key=nm+"_hire_"+p)
                            h2col = st.columns(4)
                            with h2col[0]: nov_hire = st.number_input("Нанять новичков", 0, 20, 0, 1, key=nm+"_nov")
                            with h2col[1]: train_n = st.number_input("Отправить учиться", 0, max(0, company.novices), 0, 1, key=nm+"_trainn")
                            with h2col[2]: train_prof = st.selectbox("Куда учим", ["painters","turners","assemblers"], format_func=lambda x: PROF_RU[x], key=nm+"_trainp")
                            with h2col[3]: premium = st.slider("Премия к зарплате, %", -10, 40, 0, 5, key=nm+"_prem")
                            loyalty = st.number_input("Бонус лояльности, ₽/мес", 0.0, 20000.0, 0.0, 500.0, key=nm+"_loy")
                            st.caption(f"Вакансии: {company.vac_pct:.0f}% · В обучении: {len(company.training)} · Новички: {company.novices}")
                    tnd = game.get("tender")
                    if tnd and tnd.get("open"):
                        with st.container():
                            st.markdown("<div id='card-tender' style='display:none'></div><div class='tag' style='--c:#7a1f3d'><span class='tag-hole'></span>ГОСЗАКУПКИ: ЗАЯВКА НА ТЕНДЕР</div>", unsafe_allow_html=True)
                            with st.container():
                                st.markdown("<div id='panel-tender' style='display:none'></div>", unsafe_allow_html=True)
                                st.markdown(f"<div class='chips'><span class='chip'>🏛 {tnd['customer']}</span>"
                                            f"<span class='chip'>Объём {tnd['monthly_vol']} ед./мес ×3 мес</span>"
                                            f"<span class='chip'>Потолок цены {tnd['price_cap']:.1f} ₽</span>"
                                            f"<span class='chip'>Качество ≥{tnd['quality_min']}</span>"
                                            f"<span class='chip'>Аванс {TENDER_ADVANCE*100:.0f}%</span></div>", unsafe_allow_html=True)
                                tender_apply = st.checkbox("Подать заявку на тендер", key=nm+"_tender")
                                tender_price = tnd["price_cap"]
                                if tender_apply:
                                    tender_price = st.slider("Ваша цена заявки, ₽", round(tnd["price_cap"]*0.7,1), tnd["price_cap"], tnd["price_cap"], 0.5, key=nm+"_tprice")
                                    ps = max(0.0, 1 - tender_price/tnd["price_cap"])
                                    qs = min(1.0, company.quality/(tnd["quality_min"]*1.2))
                                    rs = min(1.0, 0.5 + company.reliability*0.1 + company.reputation*0.02)
                                    st.caption(f"Ваш оценочный балл ≈ {0.6*ps + 0.2*qs + 0.2*rs:.2f} (цена {ps:.2f} + качество {qs:.2f} + надёжность {rs:.2f}). Ниже цена — выше балл, но меньше маржа.")
                                else:
                                    tender_apply = False
                    union_choice = None
                    if company.union_offer:
                        with st.container():
                            st.markdown("<div class='tag' style='--c:#5a4632'><span class='tag-hole'></span>ПРОФСОЮЗ: КОЛЛЕКТИВНЫЙ ДОГОВОР</div>", unsafe_allow_html=True)
                            st.markdown(f"Профсоюз предлагает коллективный договор: зарплаты +{UNION_WAGE_UP*100:.0f}% постоянно, но риск забастовок заметно ниже. Отказать — дешевле сейчас, рискованнее потом.")
                            union_choice = st.radio("Ваше решение", ["sign", "refuse"], format_func=lambda x: "Подписать договор" if x=="sign" else "Отклонить", key=nm+"_union")
                    if st.form_submit_button("Завершить ход компании", use_container_width=True, type="primary"):
                        cur[nm] = dict(price=price, production=production, marketing=marketing, investment=investment,
                                       rnd=rnd, charity=charity, charity_rec=charity_rec, loan=loan, loan_term=loan_term,
                                       deposit=deposit, deposit_term=deposit_term, subsidy_apply=sub_apply,
                                       sub_type=sub_type, sub_pay=sub_pay, hire=hire, fire={p:0 for p in PROFS},
                                       train=[train_prof]*train_n, nov_hire=nov_hire, premium=premium, loyalty=loyalty,
                                       tender_apply=(tnd and tnd.get("open") and tender_apply) or False,
                                       tender_price=tender_price if (tnd and tnd.get("open")) else 0.0,
                                       union_choice=union_choice)
                        st.session_state.gate = None
                        if not [x for x in humans_alive if x not in cur]:
                            execute_turn(game, cur)
                        st.rerun()
            else:
                st.markdown(f"<div class='banner'>Передача хода: за устройство садится игрок компании «{nm}». Остальным отвернуться.</div>", unsafe_allow_html=True)
                st.markdown(f"Прогресс сдачи решений: {len(humans_alive)-len(pending)} из {len(humans_alive)}")
                if st.button(f"Я — «{nm}», открыть мою форму", type="primary"):
                    st.session_state.gate = nm; st.rerun()
        else:
            execute_turn(game, cur); st.rerun()
    else:
        st.info("Решения приняты. Отчёты — во вкладках. Кнопка «Следующий ход» — в сайдбаре.")

with tabs[2]:
    if viewer.history:
        st.markdown("#### Общий зачёт (по MPI за всю игру)")
        st.markdown(rank_html(game, viewer.name), unsafe_allow_html=True)
        agg_inv, agg_rnd, agg_rev, agg_tax, agg_units, agg_char = industry_stats(game)
        st.markdown(f"<div class='calcard'><div class='calhead'><span class='calyear'>Отрасль в цифрах</span></div>"
                    f"<div class='chips'><span class='chip'>◆ Товарооборот {agg_rev:,.0f} ₽</span><span class='chip'>▲ Инвестиции {agg_inv:,.0f} ₽</span>"
                    f"<span class='chip'>★ НИОКР {agg_rnd:,.0f} ₽</span><span class='chip'>■ Продано {agg_units:,} ед.</span>"
                    f"<span class='chip'>$ Налоги {agg_tax:,.0f} ₽</span><span class='chip'>♥ Благотворительность {agg_char:,.0f} ₽</span></div></div>", unsafe_allow_html=True)
    else:
        st.info("Рейтинг появится после первого хода.")

with tabs[3]:
    if viewer.history:
        st.caption(img_status())
        cur_news = game.get("news", [])
        if over:
            tops = sorted([c for c in game["companies"] if c.history], key=lambda c: c.mpi_total, reverse=True)[:3]
            line = "; ".join(f"{i+1}) «{c.name}» — индекс {c.mpi_total:.1f}" for i, c in enumerate(tops))
            st.markdown(masthead_html(game["turn"], month_label, final=True), unsafe_allow_html=True)
            st.markdown(clip_html(dict(icon="🏆", kind="gold", head="Итоги года", text=f"Отчётный период завершён. Лидеры: {line}."), month_label, front=True), unsafe_allow_html=True)
        else:
            st.markdown(masthead_html(game["turn"], month_label), unsafe_allow_html=True)
        if cur_news:
            if not over:
                st.markdown(clip_html(cur_news[0], month_label, front=True), unsafe_allow_html=True)
            rest = cur_news[1:] if not over else cur_news
            contracts_rows = [(ct["customer"], c.name, ct["months"], ct["price"]) for c in game["companies"] for ct in c.contracts]
            if contracts_rows:
                body = "; ".join(f"{cust} → «{nm_}\" ({m} мес, {p:.1f} ₽)" for cust, nm_, m, p in contracts_rows)
                rest = [dict(icon="🏛", kind="ok", head="Реестр контрактов", text=f"Действующие госконтракты: {body}.")] + rest
            if game.get("record_sales"):
                rest = [dict(icon="📯", kind="gold", head="Книга рекордов отрасли",
                             text=f"Рекорд по продажам за месяц: {game['record_sales']} ед. — «{game['record_company']}».")] + rest
            if game.get("forecast_dir"):
                ft = {"positive": "положительная динамика", "negative": "отрицательная динамика", "stable": "стабильная динамика"}[game["forecast_dir"]]
                rest = [dict(icon="🔮", kind="ok", head="Прогноз редакции", text=f"В следующем месяце ожидается {ft}. Точность 90%.")] + rest
            for i in range(0, len(rest), 2):
                a, b = st.columns(2)
                a.markdown(clip_html(rest[i], month_label), unsafe_allow_html=True)
                if i + 1 < len(rest): b.markdown(clip_html(rest[i+1], month_label), unsafe_allow_html=True)
        archive = [n for n in reversed(game.get("news_log", [])) if n not in cur_news][:12]
        if archive:
            st.markdown("<div class='ct' style='margin-top:10px'>Архив номеров</div>", unsafe_allow_html=True)
            for n in archive:
                with st.expander(f"{n.get('period','')} · {n['head']}: {n['text'][:70]}…"):
                    st.markdown(n["text"])
    else:
        st.info("Первый выпуск «Рыночного вестника» выйдет после первого хода.")

with tabs[4]:
    if viewer.history:
        last = viewer.history[-1]
        PAGES = ["Отчёт о прибылях и убытках", "Производственный отчёт", "Персонал и обучение", "Баланс", "Движение средств и итоги"]
        pg = max(0, min(4, st.session_state.book_page))
        st.markdown(f"<div class='ribbon'></div><div class='chips'><span class='chip'>📖 стр. {pg+1} из 5</span>"
                    f"<span class='chip'>{PAGES[pg]}</span><span class='chip'>◆ {viewer.name}</span></div>", unsafe_allow_html=True)
        inv_val = last["inventory"] * last["unit_cost"]
        loans_sum = sum(l[0] for l in viewer.loans)
        total_assets = last["cash"] + last["assets"] + inv_val + last["dep_total"]
        equity = total_assets - loans_sum
        if pg == 0:
            html = paper_html("ОТЧЁТ О ПРИБЫЛЯХ И УБЫТКАХ", f"{viewer.name} · {last['month_name']}", [
                ("Выручка", f"{last['revenue']:,.0f} ₽", ""), ("(−) НДС", f"{last['vat']:,.0f} ₽", ""),
                ("(−) Себестоимость", f"{last['prod_cost']:,.0f} ₽", ""), ("(−) Хранение", f"{last['storage']:,.0f} ₽", ""),
                ("(−) Маркетинг", f"{last['marketing']:,.0f} ₽", ""), ("(−) НИОКР", f"{last['rnd']:,.0f} ₽", ""),
                ("(−) Благотворительность", f"{last['charity']:,.0f} ₽", ""),
                ("= Прибыль от продаж", f"{last['operating']:,.0f} ₽", ""),
                ("+ Прочие доходы", f"{last['fin_income']:,.0f} ₽", ""), ("− Прочие расходы", f"{last['fin_expense']:,.0f} ₽", ""),
                ("= Прибыль до налога", f"{last['base']:,.0f} ₽", ""), ("(−) Налог", f"{last['tax']:,.0f} ₽", ""),
                ("= ЧИСТАЯ ПРИБЫЛЬ", f"{last['profit']:,.0f} ₽", "total"),
                ("Справочно: амортизация", f"{last.get('depr',0):,.0f} ₽", "")], PAL[2])
        elif pg == 1:
            html = paper_html("ПРОИЗВОДСТВЕННЫЙ ОТЧЁТ", f"{viewer.name} · {last['month_name']}", [
                ("Заказы получены", f"{int(last['orders'])} ед.", ""), ("Продано", f"{int(last['sales'])} ед.", ""),
                ("Невыполненные", f"{int(last['lost'])} ед.", ""), ("Склад", f"{last['inventory']} ед.", ""),
                ("Мощность/загрузка", f"{last['capacity']}/{last['util']*100:.0f}%", ""),
                ("Себестоимость единицы", f"{last['unit_cost']:.2f} ₽", "")], PAL[4])
        elif pg == 2:
            html = paper_html("ПЕРСОНАЛ И ОБУЧЕНИЕ", f"{viewer.name} · {last['month_name']}",
                [(f"{PROF_RU[p]}: занято/навык/вакансии", f"{last['staff'][p]}/{last['skill'][p]:.1f}/{viewer.vacancies.get(p,0)}", "") for p in PROFS] + [
                ("Новички / в обучении", f"{last['novices']}/{last['training']}", ""),
                ("Вакансии (%)", f"{last['vac_pct']:.0f}%", ""),
                ("Напряжённость / забастовка", f"{last['tension']:.0f}/100 · {last['strike']}", ""),
                ("Профсоюз", "есть" if last['union'] else "нет", ""),
                ("Надёжность / контрактов", f"{last['reliability']:.0f} / {last['contracts']}", ""),
                ("ФОТ", f"{last['labor']:,.0f} ₽", "total")], PAL[1])
        elif pg == 3:
            html = (paper_html("БАЛАНС · АКТИВЫ", f"{viewer.name} · {last['month_name']}", [
                        ("Наличные", f"{last['cash']:,.0f} ₽", ""), ("Депозиты", f"{last['dep_total']:,.0f} ₽", ""),
                        ("Оборудование", f"{last['assets']:,.0f} ₽", ""), ("Запасы", f"{inv_val:,.0f} ₽", ""),
                        ("ИТОГО АКТИВЫ", f"{total_assets:,.0f} ₽", "total")], PAL[0])
                    + paper_html("БАЛАНС · ПАССИВЫ", f"{viewer.name} · {last['month_name']}", [
                        ("Кредиты", f"{loans_sum:,.0f} ₽", ""), ("Собственный капитал", f"{equity:,.0f} ₽", ""),
                        ("ИТОГО ПАССИВЫ", f"{loans_sum+equity:,.0f} ₽", "total")], PAL[1]))
        else:
            rank_pos = sorted([c for c in game["companies"] if c.history], key=lambda c: c.mpi_total, reverse=True)
            pos = next((i+1 for i, c in enumerate(rank_pos) if c.name == viewer.name), 0)
            html = (paper_html("ДВИЖЕНИЕ ДЕНЕЖНЫХ СРЕДСТВ", f"{viewer.name} · {last['month_name']}", [
                        ("Наличность на начало", f"{last['cash_start']:,.0f} ₽", ""),
                        ("Поступления от покупателей", f"{last['revenue']-last['vat']:,.0f} ₽", ""),
                        ("Прочие поступления", f"{last['fin_income']+last.get('roy_in',0):,.0f} ₽", ""),
                        ("Проценты и роялти уплаченные", f"−{last['fin_expense']+last.get('roy_out',0):,.0f} ₽", ""),
                        ("Налог", f"−{last['tax']:,.0f} ₽", ""),
                        ("Наличность на конец", f"{last['cash']:,.0f} ₽", "total")], PAL[3])
                    + paper_html("ПОКАЗАТЕЛИ ЭФФЕКТИВНОСТИ", f"{viewer.name} · {last['month_name']}", [
                        ("Место в зачёте", f"{pos} из {len(rank_pos)}", ""), ("MPI за ход", f"{last.get('mpi',0):.1f}", ""),
                        ("MPI итог", f"{viewer.mpi_total:.1f}", ""), ("Качество/репутация", f"{viewer.quality:.1f}/{viewer.reputation:.1f}", ""),
                        ("Бренд", "®" if last.get('brand') else "—", "")], PAL[0]))
        with st.container(border=True):
            st.markdown(f"<div class='book-page'>{html}</div>", unsafe_allow_html=True)
        b1, b2, b3 = st.columns([1,1,1])
        with b1:
            if st.button("◀ Назад", disabled=(pg==0), use_container_width=True): st.session_state.book_page = pg-1; st.rerun()
        with b2:
            st.markdown(f"<div style='text-align:center;color:#8a7f86;font-size:14px'>— {pg+1} —</div>", unsafe_allow_html=True)
        with b3:
            if st.button("Далее ▶", disabled=(pg==4), use_container_width=True): st.session_state.book_page = pg+1; st.rerun()
    else:
        st.info("Отчётная книга появится после первого хода.")

with tabs[5]:
    if len(viewer.history) > 1:
        t1, t2, t3 = st.tabs(["Финансы", "Качество и репутация", "Доли рынка"])
        dhp = pd.DataFrame(viewer.history); dhp["Период"] = dhp["month_name"] + " " + dhp["turn"].astype(str)
        with t1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dhp["Период"], y=dhp["revenue"], name="Выручка", line=dict(color="#eb6b56", width=3)))
            fig.add_trace(go.Scatter(x=dhp["Период"], y=dhp["profit"], name="Прибыль", line=dict(color="#47b39d", width=3)))
            fig.add_trace(go.Scatter(x=dhp["Период"], y=dhp["cash"]+dhp["dep_total"], name="Деньги", line=dict(color="#462446", width=2, dash="dot")))
            fig_base(fig, 380, legend=True); st.plotly_chart(fig, use_container_width=True)
        with t2:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dhp["Период"], y=dhp["quality"], name="Качество", line=dict(color="#ffc153", width=3)))
            fig.add_trace(go.Scatter(x=dhp["Период"], y=dhp["reputation"], name="Репутация", line=dict(color="#b05f6d", width=3)))
            fig_base(fig, 380, legend=True); st.plotly_chart(fig, use_container_width=True)
        with t3:
            fig = go.Figure()
            for i, c in enumerate(game["companies"]):
                if c.history:
                    dc = pd.DataFrame(c.history); dc["Период"] = dc["month_name"] + " " + dc["turn"].astype(str)
                    fig.add_trace(go.Scatter(x=dc["Период"], y=dc["market_share"], name=c.name, line=dict(color=PAL[i%5], width=2.5)))
            fig_base(fig, 380, legend=True); st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Графики появятся со второго хода.")

with tabs[6]:
    st.markdown("#### 🖨 Печать документов")
    doc = st.selectbox("Что печатаем", ["Рейтинг (общий зачёт)", "Отчёт команды (полный)",
                                        "Комплект команды: отчёт + рейтинг", "Газета (текущий выпуск)",
                                        "🎓 Диплом победителя (топ-3 + звания)"
                                        "Правила игры (брошюра)"], key="print_kind")
    comp_name = None
    if doc in ("Отчёт команды (полный)", "Комплект команды: отчёт + рейтинг"):
        comp_name = st.selectbox("Команда", [c.name for c in game["companies"]], key="print_comp")
    if st.button("🖨 Сформировать и печать", type="primary"):
        if doc == "Рейтинг (общий зачёт)": st.session_state.print_doc = ("rank",)
        elif doc == "Отчёт команды (полный)": st.session_state.print_doc = ("team", comp_name)
        elif doc == "Комплект команды: отчёт + рейтинг": st.session_state.print_doc = ("pack", comp_name)
        elif doc == "Газета (текущий выпуск)": st.session_state.print_doc = ("news",)
        elif doc == "🎓 Диплом победителя (топ-3 + звания)": st.session_state.print_doc = ("diploma",)
        else: st.session_state.print_doc = ("rules",)
    
        st.rerun()
    st.caption("Документ откроется на чистой странице; окно печати появится автоматически (или Ctrl+P).")

with tabs[7]:
    st.markdown("#### 📖 Энциклопедия игры «Вознесенская матрёшка»")
    for t, body in enc_sections():
        with st.expander(t):
            st.markdown(body)
    st.caption("Печатная версия — во вкладке «Печать» → «Правила игры (брошюра)».")