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
    padding: 14px 18px !important;
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
    "孤独": ["ひとりぼっち", "独りぼっち", "孤独", "誰も分かってくれない", "居場所がない", "一人が怖い", "話し相手がいない", "話せる人がいない", "相談できる人がいない", "誰とも話さない"],
    "自己肯定感": ["自分が嫌い", "自信がない", "価値がない", "自分なんて", "消えたい", "自分を好きになれない", "きらい", "きらわれた", "死んじゃいたい", "消したい", "いなくなればいい"],
    "不安・恐れ": ["不安", "怖い", "心配", "どうしよう", "パニック"],
    "平安・安心": ["落ち着かない", "眠れない", "ざわざわ", "疲れた", "しんどい"],
    "赦し・罪悪感": ["罪悪感", "許せない", "後悔", "自分を責め"],
    "将来・進路": ["将来", "進路", "受験", "就職", "これから"],
    "人間関係・居場所": ["友達", "クラス", "いじめ", "仲間はずれ", "家族", "親"],
    "力・弱さ": ["無理", "頑張れない", "力が出ない", "疲れ"],
    "慰め・悲しみ": ["悲しい", "泣きたい", "涙", "辛い", "つらい", "もうダメ", "たすけて", "いやだ", "しても無駄だと思う"],
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


# 希死念慮など、深刻さの高い言葉。ヒットしたら聖句とは別に相談窓口を案内する
CRISIS_KEYWORDS = ["死にたい", "死んじゃいたい", "消えたい", "消したい", "いなくなればいい", "いなくなってしまいたい", "いなくなりたい", "自殺"]


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

MESSAGES = {
    "愛": [
        """
うまく言葉にできなくても、そのままで大丈夫だよ。
神さまは、今のあなたをそのままで愛しているから。

好かれるために頑張らなくても、
すでにあなたは大切にされている。

その愛は、条件つきじゃない。
今日のあなたも、そのままで愛されているよ。

聖霊様の語りかけに、
そっと耳を傾けてみてね。
""",
        """
今のあなたのままで、じゅうぶん愛おしい存在だよ。
神さまの愛は、あなたの機嫌や調子に左右されない。

うまくやれた日も、そうじゃない日も、
神さまが向ける愛は変わらない。

その愛の中に、
今日も安心して留まっていていいよ。

聖霊様の語りかけに、
そっと耳を傾けてみてね。
""",
        """
誰かに愛されているか不安になる日があってもいいよ。
でも神さまは、いちばん最初からあなたを愛している。

証明しなくても、頑張らなくても、
その愛はもう、あなたに向けられているから。

安心して、その愛にもたれかかってみて。

聖霊様の語りかけに、
そっと耳を傾けてみてね。
""",
    ],
    "アイデンティティ": [
        """
自分がよく分からなくなる時があってもいいよ。
神さまは、あなたの本当の姿をちゃんと知っていてくださる。

誰かと比べなくていいし、
今の自分を否定しなくていい。

あなたは神さまにとって、
かけがえのない大切な存在だから。

聖霊様の語りかけに、
そっと耳を傾けてみてね。
""",
        """
自分の価値が分からなくなる時があってもいいよ。
神さまは、あなたを「何ができるか」だけでは見ていない。

存在しているだけで、
すでにあなたには意味があるから。

比べたりジャッジしたりしなくて大丈夫。

聖霊様の語りかけに、
そっと耳を傾けてみてね。
""",
        """
本当の自分がどこにいるか分からなくなる日があってもいいよ。
神さまの目には、今のあなたがちゃんと映っている。

弱いところも、迷っているところも、
ぜんぶ含めて大切な存在だから。

無理に取り繕わなくていいよ。

聖霊様の語りかけに、
そっと耳を傾けてみてね。
""",
    ],
    "平安": [
        """
気持ちがざわざわする日があってもいいよ。
そんな時こそ、そっと神さまに預けてみて。

無理に落ち着こうとしなくていいし、
すぐに答えを出さなくてもいい。

静かに深呼吸してみると、
神さまの平安がそっと近づいてくるよ。

聖霊様の語りかけに、
そっと耳を傾けてみてね。
""",
        """
心がざわざわして落ち着かない日があってもいいよ。
そんな時こそ、神さまに気持ちを預けてみて。

考えすぎなくていいし、
すぐに解決しなくてもいい。

少しずつ、心が静かになっていくから。

聖霊様の語りかけに、
そっと耳を傾けてみてね。
""",
        """
気持ちが不安定になる日があってもいいよ。
神さまは、そんなあなたのそばにいてくださる。

無理に元気なふりをしなくていいし、
今はただ、休んでいい。

深呼吸ひとつで、
少しだけ心がゆるむこともあるよ。

聖霊様の語りかけに、
そっと耳を傾けてみてね。
""",
    ],
    "供給": [
        """
これからのことが不安になる時があってもいいよ。
神さまは、あなたに必要なものをちゃんと知っていてくださる。

足りない気がしても、
一人で抱え込まなくて大丈夫。

必要な時に、必要な分だけ、
神さまはちゃんと備えてくださるから。

聖霊様の語りかけに、
そっと耳を傾けてみてね。
""",
        """
足りないものばかり気になる日があってもいいよ。
でも神さまは、あなたに必要なものをちゃんと知っている。

今すぐ全部そろわなくても、
必要な時にちゃんと与えられるから。

焦らず、待っていて大丈夫。

聖霊様の語りかけに、
そっと耳を傾けてみてね。
""",
        """
この先どうなるか心配になる日があってもいいよ。
神さまは、その一歩先までちゃんと見てくださっている。

自分一人で何とかしなくていいし、
頼っていい存在がいるから。

安心して、明日を任せてみて。

聖霊様の語りかけに、
そっと耳を傾けてみてね。
""",
    ],
    "祝福": [
        """
うまくいかない日があってもいいよ。
それでも、あなたの歩みは祝福されている。

小さな一歩も、神さまはちゃんと見ていてくださる。
焦らなくて大丈夫。

今のあなたにも、
ちゃんと良いものが用意されているから。

聖霊様の語りかけに、
そっと耳を傾けてみてね。
""",
        """
何も特別なことがない日があってもいいよ。
そんな日常の中にも、神さまの祝福はちゃんと流れている。

小さな笑顔も、
ちょっとした安心も、祝福のひとつだから。

今日という日にも、良いものがあるよ。

聖霊様の語りかけに、
そっと耳を傾けてみてね。
""",
        """
自分にはあまり良いことがないなって感じる日があってもいいよ。
でも神さまは、見えないところであなたを祝福している。

結果がすぐに出なくても、
歩み自体が大切にされているから。

焦らなくて大丈夫、ちゃんと進んでいるよ。

聖霊様の語りかけに、
そっと耳を傾けてみてね。
""",
    ],
    "恵み": [
        """
うまくできなかったなって思う日があってもいいよ。
神さまの前では、頑張りの量で愛されているわけじゃない。

失敗しても、責めなくて大丈夫。
神さまの恵みは、そんなあなたにも注がれている。

やり直せることを、
知っておいてほしいな。

聖霊様の語りかけに、
そっと耳を傾けてみてね。
""",
        """
自分を許せない気持ちになる日があってもいいよ。
神さまの恵みは、あなたの失敗より大きいから。

がんばりが足りなかった日も、
それだけで愛が減ったりしないよ。

そのままの自分で、また一歩踏み出していい。

聖霊様の語りかけに、
そっと耳を傾けてみてね。
""",
        """
自分にがっかりする日があってもいいよ。
でも神さまは、そんな日のあなたも見捨てない。

恵みは、あなたの調子に関係なく注がれている。
だから安心して、また立ち上がっていいよ。

聖霊様の語りかけに、
そっと耳を傾けてみてね。
""",
    ],
    "聖霊": [
        """
一人ぼっちだと感じる時があってもいいよ。
でも本当は、いつも聖霊様がそばにいてくださる。

言葉にならない気持ちも、
聖霊様はちゃんと分かっていてくださる。

静かにしていると、
胸の奥で小さな声がする時があるよ。

聖霊様の語りかけに、
そっと耳を傾けてみてね。
""",
        """
誰にも分かってもらえない気がする日があってもいいよ。
でも聖霊様は、あなたの内側にいつも一緒にいてくださる。

言葉にならない気持ちも、
ちゃんと受け止めてくださっているから。

静かな時間の中で、
そっと寄り添ってくれているよ。

聖霊様の語りかけに、
そっと耳を傾けてみてね。
""",
        """
心細くなる日があってもいいよ。
そんな時、聖霊様はあなたのすぐそばにいてくださる。

一人で頑張らなくていいし、
弱さを隠さなくてもいい。

静かに心を開いてみると、
そっと支えを感じられるかもしれないよ。

聖霊様の語りかけに、
そっと耳を傾けてみてね。
""",
    ],
}


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
                <p>でも、ここまで深刻なら、ひとりで抱えずに話してみて。信頼できる友達や家族、教会の仲間がいれば、その人にも話してみてね。</p>
                <p>もし今すぐ話せる人がいなくても、
                <a href="https://ibashochatwellness.jp/about" target="_blank">「あなたのいばしょ」（24時間365日・無料・匿名のチャット相談）</a>
                があるよ。</p>
                <p>神さまの愛をもっと味わいたいときは、こちらの聖書プランもおすすめだよ：
                <a href="https://www.bible.com/reading-plans/55975-the-power-of-love-finding-rest-in-the-fathers-love" target="_blank">The Power of Love: Finding Rest in the Father's Love</a></p>
            </div>
            """,
            unsafe_allow_html=True
        )
