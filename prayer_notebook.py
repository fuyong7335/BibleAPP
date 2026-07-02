import streamlit as st
import json
import datetime
import os
import random
import urllib.parse

st.set_page_config(page_title="🌿 祈りノート", page_icon="🌿", layout="centered")

# ================================
# CSS：スマホ最適化 & UI調整（パステルピンク×丸みフォント）
# ================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@400;700;800&display=swap');

html, body, div, p, span, label, textarea, button {
    font-family: 'M PLUS Rounded 1c', sans-serif !important;
    font-size: 17px !important;
    line-height: 1.7 !important;
}

.stApp {
    background: linear-gradient(180deg, #fff5fa 0%, #ffe6f2 100%);
}

.block-container {
    padding-left: 1rem !important;
    padding-right: 1rem !important;
}

h1 {
    color: #ff6fa5 !important;
    font-weight: 800 !important;
}

div.stButton > button {
    width: 100% !important;
    padding: 14px 0 !important;
    border-radius: 24px !important;
    font-size: 18px !important;
    font-weight: 700 !important;
    background-color: #ffb6d5 !important;
    color: #ffffff !important;
    border: none !important;
    box-shadow: 0 4px 10px rgba(255, 140, 180, 0.35) !important;
}

div.stButton > button:hover {
    background-color: #ff9dc4 !important;
}

textarea {
    font-size: 16px !important;
    border-radius: 16px !important;
    border: 2px solid #ffd1e3 !important;
}

.card {
    padding: 18px !important;
    border-radius: 20px !important;
    background-color: #fff0f6;
    border: 2px solid #ffc2dd;
    margin-top: 20px;
    box-shadow: 0 4px 10px rgba(255, 140, 180, 0.2);
}
.card-title {
    margin: 0 0 8px 0;
    font-size: 18px;
    color: #ff6fa5;
    font-weight: 700;
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


# 自由記述に含まれやすいティーンの悩み言葉 → テーマタグ
# （bible_categories.json の各節に付与されている tags と対応させることで、
#   自由記述の内容にも合わせて聖句を選べるようにする。外部通信は一切なし）
TEEN_KEYWORDS = {
    "孤独": ["ひとりぼっち", "独りぼっち", "孤独", "誰も分かってくれない", "居場所がない", "一人が怖い"],
    "自己肯定感": ["自分が嫌い", "自信がない", "価値がない", "自分なんて", "消えたい", "自分を好きになれない"],
    "不安・恐れ": ["不安", "怖い", "心配", "どうしよう", "パニック"],
    "平安・安心": ["落ち着かない", "眠れない", "ざわざわ", "疲れた", "しんどい"],
    "赦し・罪悪感": ["罪悪感", "許せない", "後悔", "自分を責め"],
    "将来・進路": ["将来", "進路", "受験", "就職", "これから"],
    "人間関係・居場所": ["友達", "クラス", "いじめ", "仲間はずれ", "家族", "親"],
    "力・弱さ": ["無理", "頑張れない", "力が出ない"],
    "慰め・悲しみ": ["悲しい", "泣きたい", "涙", "辛い", "つらい"],
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
    for theme, keywords in TEEN_KEYWORDS.items():
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
言葉にできなくても、そのままで大丈夫だよ。
いま感じていることは、ちゃんと神さまが見ていてくださるから。

無理に分かろうとしなくていいし、
すぐに気持ちを整理しなくてもいい。

わからないままの自分を、
そっと神さまの前に置いてみてね。

静かにしていると、
胸の奥のほうで小さな声がする時があるよ。
それは、あなたをひとりにしないよという神さまのまなざし。

急がなくていいから、
ほんの少しだけ心をゆるめてみて。

聖霊様の語りかけに、
そっと耳を傾けてみてください。
"""


# ================================
# UI 本体
# ================================
st.title("🌿 祈りノート")
st.caption(f"最終更新日：{datetime.date.today()}")

st.write("今日、モヤモヤすることがあったら  \n神さまにきいてもらおう。")

questions = {
    1: "気持ちがざわざわしたり、落ち着かない瞬間があった。",
    2: "自分が誰にも受け入れられていない気がする。自分のことを好きになれない時がある。",
    3: "自分がここにいる意味がわからなくなる時がある。「いない方がいいのかな」と感じてしまうことがある。",
    4: "自分が何をしたいのか、よく分からなくなる。",
    5: "突然悲しくなったり、気持ちが不安定になることがある。",
    6: "他人にどう見られているのか、怖くなる時がある。",
    7: "生きる意味がわからなくなる時がある。",
}

answers = {}
for q_num, q_text in questions.items():
    answers[q_num] = st.radio(
        f"{q_num}. {q_text}",
        ["はい", "どちらでもない", "いいえ"],
        horizontal=True,
        key=f"q{q_num}"
    )

free_text = st.text_area("何かいいたいことはある？", height=200)


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
