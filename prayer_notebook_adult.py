import streamlit as st
import json
import datetime
import os
import random
import urllib.parse

st.set_page_config(page_title="🌿 祈りノート", page_icon="🌿", layout="centered")

# ================================
# CSS：スマホ最適化 & UI調整
# ================================
st.markdown("""
<style>
html, body, div, p {
    font-size: 17px !important;
    line-height: 1.7 !important;
}

.block-container {
    padding-left: 1rem !important;
    padding-right: 1rem !important;
}

div.stButton > button {
    width: 100% !important;
    padding: 14px 0 !important;
    border-radius: 10px !important;
    font-size: 18px !important;
}

textarea {
    font-size: 16px !important;
}
.card {
    padding: 18px !important;
    border-radius: 14px !important;
    background-color: #fff8e8;
    border: 1px solid #e9d7b7;
    margin-top: 20px;
}
.card-title {
    margin: 0 0 8px 0;
    font-size: 18px;
}
</style>
""", unsafe_allow_html=True)


# ================================
# JSON 読み込み
# ================================
JSON_PATH = "bible_categories.json"

if not os.path.exists(JSON_PATH):
    st.error("bible_categories.json が見つかりません。")
    st.stop()

with open(JSON_PATH, "r", encoding="utf-8") as f:
    VERSES_DB = json.load(f)


# ================================
# YouVersion 検索リンク
# ================================
def bible_url_youversion(verse_label: str) -> str:
    q = urllib.parse.quote(verse_label)
    return f"https://www.bible.com/ja/search/bible?q={q}&version=83"


# ================================
# 設問 → カテゴリ
# ================================
CATEGORY_MAPPING = {
    1: "平安",
    2: "アイデンティティ",
    3: "愛",
    4: "供給",
    5: "祝福",
    6: "恵み",
    7: "聖霊",
}


# 自由記述に含まれやすい大人の悩み言葉 → テーマタグ
# （bible_categories.json の各節に付与されている tags と対応させることで、
#   自由記述の内容にも合わせて聖句を選べるようにする。外部通信は一切なし）
ADULT_KEYWORDS = {
    "孤独": ["孤独", "一人ぼっち", "誰にも相談できない", "孤立している", "居場所がない"],
    "自己肯定感": ["自分に自信が持てない", "自己肯定感が低い", "自分の価値がわからない", "自分が嫌になる", "消えてしまいたい"],
    "不安・恐れ": ["不安", "将来が怖い", "心配で仕方ない", "焦り", "パニックになる"],
    "平安・安心": ["気持ちが落ち着かない", "眠れない", "疲れが取れない", "ストレスが溜まっている"],
    "赦し・罪悪感": ["罪悪感", "自分を許せない", "後悔している", "過去にとらわれている"],
    "将来・進路": ["将来が不安", "この先どうなるか", "キャリア", "老後", "これからの人生"],
    "人間関係・居場所": ["職場の人間関係", "同僚", "配偶者", "家族", "子育て"],
    "力・弱さ": ["気力が出ない", "限界を感じる", "頑張れない", "疲弊している"],
    "慰め・悲しみ": ["悲しい", "涙が止まらない", "喪失感", "つらい"],
}

# テーマタグがヒットしたときに、あわせてスコアを加点するカテゴリ
THEME_TO_CATEGORY = {
    "孤独": ["愛", "平安"],
    "自己肯定感": ["アイデンティティ"],
    "不安・恐れ": ["平安"],
    "平安・安心": ["平安"],
    "赦し・罪悪感": ["恵み"],
    "将来・進路": ["供給", "祝福"],
    "人間関係・居場所": ["アイデンティティ", "愛"],
    "力・弱さ": ["聖霊", "恵み"],
    "慰め・悲しみ": ["平安", "愛"],
}


def score_categories(answers: dict) -> dict:
    score = {cat: 0 for cat in CATEGORY_MAPPING.values()}
    for q_num, ans in answers.items():
        cat = CATEGORY_MAPPING[q_num]
        if ans == "はい":
            score[cat] += 2
        elif ans == "どちらでもない":
            score[cat] += 1
    return score


def detect_themes(free_text: str) -> set:
    hits = set()
    for theme, keywords in ADULT_KEYWORDS.items():
        if any(kw in free_text for kw in keywords):
            hits.add(theme)
    return hits


def choose_category(score: dict, hit_themes: set) -> str:
    boosted = dict(score)
    for theme in hit_themes:
        for cat in THEME_TO_CATEGORY.get(theme, []):
            boosted[cat] += 2
    # 上位カテゴリだけに絞らず、スコア比率で重み付き抽選する
    # （+1の下駄で、スコア0のカテゴリにも小さな可能性を残す）
    categories = list(boosted.keys())
    weights = [boosted[c] + 1 for c in categories]
    return random.choices(categories, weights=weights, k=1)[0]


def choose_verse(category: str, hit_themes: set) -> dict:
    verses = VERSES_DB.get(category, [])
    matched = [v for v in verses if hit_themes.intersection(v.get("tags", []))]
    return random.choice(matched) if matched else random.choice(verses)


# ================================
# あなたの世界観メッセージ（固定）
# ================================
FIXED_MESSAGE = """
言葉にできなくても、そのままで大丈夫です。
いま感じていることを、神さまはちゃんと見ていてくださいます。

無理に理解しようとしなくてもいいし、
今すぐ気持ちを整理する必要もありません。

分からないままの自分を、
そっと神さまの前に置いてみてください。

静かに心を落ち着けていると、
胸の奥で小さな声が聞こえてくることがあります。
それは、あなたを一人にしないという神さまのまなざしです。

急がなくて大丈夫ですから、
少しだけ心をゆるめてみてください。

聖霊の語りかけに、
そっと耳を傾けてみてください。
"""


# ================================
# UI 本体
# ================================
st.title("🌿 祈りノート")
st.caption(f"最終更新日：{datetime.date.today()}")

st.write("今日、心に引っかかることがあれば、  \n神さまに聞いていただきましょう。")

questions = {
    1: "気持ちが落ち着かず、そわそわすることがある。",
    2: "自分が誰からも受け入れられていないと感じることがある。自分自身を好きになれない時がある。",
    3: "自分がここにいる意味が分からなくなることがある。「いない方がいいのではないか」と感じてしまうことがある。",
    4: "自分が何を求めているのか、分からなくなることがある。",
    5: "突然悲しくなったり、気持ちが不安定になることがある。",
    6: "他人からどう見られているか、不安になることがある。",
    7: "生きる意味が分からなくなることがある。",
}

answers = {}
for q_num, q_text in questions.items():
    answers[q_num] = st.radio(
        f"{q_num}. {q_text}",
        ["はい", "どちらでもない", "いいえ"],
        horizontal=True,
        key=f"q{q_num}"
    )

free_text = st.text_area("今、感じていることを言葉にしてみませんか？", height=200)


# ================================
# ボタン
# ================================
if st.button("あなたに贈るメッセージ"):

    score = score_categories(answers)
    hit_themes = detect_themes(free_text)
    category = choose_category(score, hit_themes)
    verse = choose_verse(category, hit_themes)
    link = bible_url_youversion(verse["verse"])

    # メッセージ本体
    st.write(FIXED_MESSAGE)

    # みことばカード（“み言葉を読む” 消して、カード全体をリンクに）
    st.markdown(
        f"""
        <a href="{link}" target="_blank" style="text-decoration:none;">
            <div class="card">
                <p class="card-title">📖 あなたに贈るみことば</p>
            </div>
        </a>
        """,
        unsafe_allow_html=True
    )
