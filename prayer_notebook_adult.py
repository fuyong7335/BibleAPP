import streamlit as st
import json
import datetime
import os
import random
import urllib.parse

st.set_page_config(page_title="🌿 祈りノート", page_icon="🌿", layout="centered")

# ================================
# CSS：スマホ最適化 & UI調整（クリーム系×丸みフォント）
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
    background: linear-gradient(180deg, #fffaf0 0%, #fbf1de 100%);
}

.block-container {
    padding-left: 1rem !important;
    padding-right: 1rem !important;
}

h1 {
    color: #a67c52 !important;
    font-weight: 800 !important;
}

h3 {
    color: #a67c52 !important;
    font-weight: 700 !important;
    margin-top: 36px !important;
    margin-bottom: 12px !important;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 20px !important;
    border-color: #e6cba8 !important;
    background-color: #fffdf9 !important;
    padding: 6px !important;
    margin-bottom: 20px !important;
}

div.stButton {
    margin-top: 24px !important;
}

div.stButton > button {
    width: 100% !important;
    padding: 14px 18px !important;
    border-radius: 24px !important;
    font-size: 18px !important;
    font-weight: 700 !important;
    background-color: #d9b48f !important;
    color: #ffffff !important;
    border: none !important;
    box-shadow: 0 4px 10px rgba(166, 124, 82, 0.3) !important;
}

div.stButton > button:hover {
    background-color: #c9a37c !important;
}

textarea {
    font-size: 16px !important;
    border-radius: 16px !important;
    border: 2px solid #e6cba8 !important;
}

.card {
    padding: 18px !important;
    border-radius: 20px !important;
    background-color: #fff8ec;
    border: 2px solid #e6cba8;
    margin-top: 20px;
    box-shadow: 0 4px 10px rgba(166, 124, 82, 0.15);
}
.card-title {
    margin: 0 0 8px 0;
    font-size: 18px;
    color: #a67c52;
    font-weight: 700;
}

.safety-card {
    padding: 18px !important;
    border-radius: 20px !important;
    background-color: #eef6ff;
    border: 2px solid #bcdcff;
    margin-top: 16px;
}
.safety-card p {
    margin: 0 0 8px 0;
    color: #35618c;
}
.safety-card a {
    color: #2a6fb0;
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
# YouVersion 直接リンク
# ================================
YOUVERSION_VERSION_ID = "83"

BOOK_CODES = {
    "ヨハネ福音書": "JHN",
    "ローマ人への手紙": "ROM",
    "エレミヤ書": "JER",
    "第1ヨハネ": "1JN",
    "エペソ人への手紙": "EPH",
    "第1コリント": "1CO",
    "マタイ福音書": "MAT",
    "詩篇": "PSA",
    "イザヤ書": "ISA",
    "ゼパニヤ書": "ZEP",
    "ガラテヤ書": "GAL",
    "第2コリント": "2CO",
    "ピリピ人への手紙": "PHP",
    "第1ペテロ": "1PE",
    "コロサイ人への手紙": "COL",
    "使徒の働き": "ACT",
    "第2テモテ": "2TI",
    "第1テサロニケ": "1TH",
    "エゼキエル書": "EZK",
    "ユダの手紙": "JUD",
    "箴言": "PRO",
    "民数記": "NUM",
    "ヘブル人への手紙": "HEB",
    "ルカ福音書": "LUK",
    "申命記": "DEU",
    "創世記": "GEN",
    "マラキ書": "MAL",
    "テトス書": "TIT",
    "第1列王記": "1KI",
    "第2列王記": "2KI",
    "マルコ福音書": "MRK",
}


def bible_url_youversion(verse_label: str) -> str:
    # 書名が長いものから順にマッチさせる（"第1コリント"などの誤マッチを防ぐ）
    for book_name in sorted(BOOK_CODES.keys(), key=len, reverse=True):
        if verse_label.startswith(book_name):
            code = BOOK_CODES[book_name]
            rest = verse_label[len(book_name):]
            if ":" in rest:
                chapter, verse = rest.split(":", 1)
            else:
                # ユダの手紙など、章がなく節番号だけの書
                chapter, verse = "1", rest
            return f"https://www.bible.com/bible/{YOUVERSION_VERSION_ID}/{code}.{chapter}.{verse}"

    # マッチしない場合は検索ページにフォールバック
    q = urllib.parse.quote(verse_label)
    return f"https://www.bible.com/ja/search/bible?q={q}&version={YOUVERSION_VERSION_ID}"


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
    "孤独": ["孤独", "一人ぼっち", "誰にも相談できない", "孤立している", "居場所がない", "話し相手がいない", "話せる人がいない", "相談できる人がいない", "誰とも話さない"],
    "自己肯定感": ["自分に自信が持てない", "自己肯定感が低い", "自分の価値がわからない", "自分が嫌になる", "消えてしまいたい", "死にたい", "自分を消したい", "嫌われている気がする", "いなくなった方がいい"],
    "不安・恐れ": ["不安", "将来が怖い", "心配で仕方ない", "焦り", "パニックになる"],
    "平安・安心": ["気持ちが落ち着かない", "眠れない", "疲れが取れない", "ストレスが溜まっている"],
    "赦し・罪悪感": ["罪悪感", "自分を許せない", "後悔している", "過去にとらわれている"],
    "将来・進路": ["将来が不安", "この先どうなるか", "キャリア", "老後", "これからの人生"],
    "人間関係・居場所": ["職場の人間関係", "同僚", "配偶者", "家族", "子育て"],
    "力・弱さ": ["気力が出ない", "限界を感じる", "頑張れない", "疲弊している", "疲れ", "もう限界だ", "耐えられない"],
    "慰め・悲しみ": ["悲しい", "涙が止まらない", "喪失感", "つらい", "助けてほしい", "何をしても無駄に感じる"],
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


# 希死念慮など、深刻さの高い言葉。ヒットしたら聖句とは別に相談窓口を案内する
CRISIS_KEYWORDS = ["死にたい", "自分を消したい", "いなくなった方がいい", "いなくなってしまいたい", "いなくなりたい", "消えてしまいたい", "自殺"]


def detect_crisis(free_text: str) -> bool:
    return any(kw in free_text for kw in CRISIS_KEYWORDS)


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


def choose_category_and_verse(score: dict, hit_themes: set):
    # 自由記述からテーマが検出できた場合、選ばれたカテゴリの中だけを探すと
    # 該当タグの聖句が無くて完全ランダムになってしまうことがある。
    # そこで先に全カテゴリを横断してテーマに合う聖句を探し、
    # 見つかった候補の中から回答スコアで重み付けして選ぶ。
    if hit_themes:
        candidates = [
            (cat, v)
            for cat, verses in VERSES_DB.items()
            for v in verses
            if hit_themes.intersection(v.get("tags", []))
        ]
        if candidates:
            weights = [score.get(cat, 0) + 1 for cat, _ in candidates]
            return random.choices(candidates, weights=weights, k=1)[0]

    category = choose_category(score, hit_themes)
    verse = choose_verse(category, hit_themes)
    return category, verse


# ================================
# あなたに贈るメッセージ（カテゴリごとに変化）
# ================================
DEFAULT_MESSAGE = """
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

聖霊様に耳を傾ける時間を取ってください。
"""

MESSAGES = {
    "愛": [
        """
うまく言葉にできなくても、そのままで大丈夫です。
神さまは、今のあなたをそのままで愛してくださっています。

好かれるために頑張らなくても、
すでにあなたは大切にされています。

その愛には、条件がありません。
今日のあなたも、そのままで愛されています。

聖霊様に耳を傾ける時間を取ってください。
""",
        """
今のあなたのままで、十分に愛おしい存在です。
神さまの愛は、あなたの調子に左右されません。

うまくいった日も、そうでない日も、
神さまが向ける愛は変わりません。

その愛の中に、
今日も安心してとどまっていてください。

聖霊様に耳を傾ける時間を取ってください。
""",
        """
誰かに愛されているか不安になる日があっても大丈夫です。
神さまは、最初からあなたを愛しておられます。

証明しなくても、頑張らなくても、
その愛はすでにあなたに向けられています。

安心して、その愛に身を委ねてみてください。

聖霊様に耳を傾ける時間を取ってください。
""",
    ],
    "アイデンティティ": [
        """
自分がよく分からなくなる時があっても大丈夫です。
神さまは、あなたの本当の姿をちゃんと知っていてくださいます。

誰かと比べる必要はありませんし、
今の自分を否定しなくても大丈夫です。

あなたは神さまにとって、
かけがえのない大切な存在です。

聖霊様に耳を傾ける時間を取ってください。
""",
        """
自分の価値が分からなくなる時があっても大丈夫です。
神さまは、あなたを「何ができるか」だけで見ていません。

存在しているだけで、
すでにあなたには意味があります。

比べたり評価したりしなくても大丈夫です。

聖霊様に耳を傾ける時間を取ってください。
""",
        """
本当の自分が分からなくなる日があっても大丈夫です。
神さまの目には、今のあなたがそのまま映っています。

弱さも迷いも、
すべて含めて大切な存在です。

無理に取り繕わなくても大丈夫です。

聖霊様に耳を傾ける時間を取ってください。
""",
    ],
    "平安": [
        """
気持ちが落ち着かない日があっても大丈夫です。
そんな時こそ、そっと神さまに委ねてみてください。

無理に落ち着こうとしなくてもいいですし、
今すぐ答えを出さなくても構いません。

静かに深呼吸をしてみると、
神さまの平安がそっと近づいてきます。

聖霊様に耳を傾ける時間を取ってください。
""",
        """
心が落ち着かない日があっても大丈夫です。
そんな時こそ、神さまに気持ちを委ねてみてください。

考えすぎなくてもいいですし、
すぐに解決しなくても構いません。

少しずつ、心が静かになっていきます。

聖霊様に耳を傾ける時間を取ってください。
""",
        """
気持ちが不安定になる日があっても大丈夫です。
神さまは、そんなあなたのそばにいてくださいます。

無理に元気なふりをしなくてもいいですし、
今はただ休んでいただいて構いません。

深呼吸ひとつで、
少し心がゆるむこともあります。

聖霊様に耳を傾ける時間を取ってください。
""",
    ],
    "供給": [
        """
これからのことが不安になる時があっても大丈夫です。
神さまは、あなたに必要なものをちゃんと知っていてくださいます。

足りないと感じても、
一人で抱え込まなくて大丈夫です。

必要な時に、必要な分だけ、
神さまはちゃんと備えてくださいます。

聖霊様に耳を傾ける時間を取ってください。
""",
        """
足りないものばかり気になる日があっても大丈夫です。
神さまは、あなたに必要なものをちゃんと知っておられます。

今すぐすべてが整わなくても、
必要な時にきちんと与えられます。

焦らず、待っていていただいて大丈夫です。

聖霊様に耳を傾ける時間を取ってください。
""",
        """
この先のことが心配になる日があっても大丈夫です。
神さまは、その先までしっかりと見ておられます。

すべてを一人で抱え込まなくてもいいですし、
頼っていい存在がいます。

安心して、明日を委ねてみてください。

聖霊様に耳を傾ける時間を取ってください。
""",
    ],
    "祝福": [
        """
うまくいかない日があっても大丈夫です。
それでも、あなたの歩みは祝福されています。

小さな一歩も、神さまはちゃんと見ていてくださいます。
焦らなくて大丈夫です。

今のあなたにも、
良いものがすでに用意されています。

聖霊様に耳を傾ける時間を取ってください。
""",
        """
特別なことがない日があっても大丈夫です。
そんな日常の中にも、神さまの祝福は流れています。

小さな笑顔も、
ちょっとした安心も、祝福のひとつです。

今日という日にも、良いものがあります。

聖霊様に耳を傾ける時間を取ってください。
""",
        """
自分にはあまり良いことがないと感じる日があっても大丈夫です。
神さまは、見えないところであなたを祝福しておられます。

結果がすぐに出なくても、
歩みそのものが大切にされています。

焦らなくても、ちゃんと進んでいます。

聖霊様に耳を傾ける時間を取ってください。
""",
    ],
    "恵み": [
        """
うまくできなかったと感じる日があっても大丈夫です。
神さまの前では、頑張りの量で愛が決まるわけではありません。

失敗しても、自分を責めなくて大丈夫です。
神さまの恵みは、そんなあなたにも注がれています。

やり直すことができると、
覚えておいてください。

聖霊様に耳を傾ける時間を取ってください。
""",
        """
自分を許せない気持ちになる日があっても大丈夫です。
神さまの恵みは、あなたの失敗より大きいものです。

十分に頑張れなかった日も、
それだけで愛が減ることはありません。

そのままの自分で、また一歩踏み出してください。

聖霊様に耳を傾ける時間を取ってください。
""",
        """
自分にがっかりする日があっても大丈夫です。
神さまは、そんな日のあなたも見捨てません。

恵みは、あなたの調子に関係なく注がれています。
安心して、また立ち上がってください。

聖霊様に耳を傾ける時間を取ってください。
""",
    ],
    "聖霊": [
        """
一人だと感じる時があっても大丈夫です。
本当は、いつも聖霊がそばにいてくださいます。

言葉にならない気持ちも、
聖霊はちゃんと分かっていてくださいます。

静かにしていると、
胸の奥で小さな声が聞こえてくることがあります。

聖霊様に耳を傾ける時間を取ってください。
""",
        """
誰にも分かってもらえないと感じる日があっても大丈夫です。
聖霊は、あなたの内側にいつも共にいてくださいます。

言葉にならない気持ちも、
ちゃんと受け止めてくださっています。

静かな時間の中で、
そっと寄り添ってくださっています。

聖霊様に耳を傾ける時間を取ってください。
""",
        """
心細くなる日があっても大丈夫です。
そんな時、聖霊はあなたのすぐそばにいてくださいます。

一人で頑張らなくてもいいですし、
弱さを隠さなくても大丈夫です。

静かに心を開いてみると、
そっと支えを感じられるかもしれません。

聖霊様に耳を傾ける時間を取ってください。
""",
    ],
}


# ================================
# UI 本体
# ================================
st.title("🌿 祈りノート")
st.caption(f"最終更新日：{datetime.date.today()}")

st.write("今日、心に引っかかることがあれば、  \n神さまに聞いていただきましょう。")

st.markdown("### 🌿 今のあなたの気持ちを聞かせてください")

questions = {
    1: "気持ちが落ち着かず、そわそわすることがある。",
    2: "自分が誰からも受け入れられていないと感じることがある。自分自身を好きになれない時がある。",
    3: "自分は誰からも必要とされていないと感じることがある。",
    4: "自分が何を求めているのか、分からなくなることがある。",
    5: "突然悲しくなったり、気持ちが不安定になることがある。",
    6: "他人からどう見られているか、不安になることがある。",
    7: "生きる意味が分からなくなることがある。",
}

answers = {}
with st.container(border=True):
    for q_num, q_text in questions.items():
        answers[q_num] = st.radio(
            f"{q_num}. {q_text}",
            ["はい", "どちらでもない", "いいえ"],
            horizontal=True,
            key=f"q{q_num}"
        )

st.markdown("### 💬 自由に書いてみてください")

with st.container(border=True):
    free_text = st.text_area("今、感じていることを言葉にしてみませんか？", height=200, label_visibility="collapsed")


# ================================
# ボタン
# ================================
if st.button("あなたに贈るメッセージ"):

    score = score_categories(answers)
    hit_themes = detect_themes(free_text)
    is_crisis = detect_crisis(free_text)
    category, verse = choose_category_and_verse(score, hit_themes)
    link = bible_url_youversion(verse["verse"])
    message = random.choice(MESSAGES.get(category, [DEFAULT_MESSAGE]))

    # メッセージ本体
    st.write(message)

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

    # 深刻な言葉が書かれていた場合は、相談窓口も案内する
    if is_crisis:
        st.markdown(
            """
            <div class="safety-card">
                <p>神さまの愛をもっと深く知りたい方には、こちらの聖書プランもおすすめです：
                <a href="https://www.bible.com/reading-plans/55975-the-power-of-love-finding-rest-in-the-fathers-love" target="_blank">The Power of Love: Finding Rest in the Father's Love</a></p>
                <p>ここまで深刻な思いを抱えているなら、一人で抱え込まずに話してみてください。信頼できる教会の兄弟姉妹や、ご家族、ご友人がいれば、その方にも。</p>
                <p>もし今すぐ話せる相手がいなくても、
                <a href="https://ibashochatwellness.jp/about" target="_blank">「あなたのいばしょ」（24時間365日・無料・匿名のチャット相談）</a>
                があります。</p>
            </div>
            """,
            unsafe_allow_html=True
        )
