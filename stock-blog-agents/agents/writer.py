"""
ブログ文章作成係エージェント: 調査・分析をもとにブログ記事を執筆する
"""
import anthropic

SYSTEM_PROMPT = """あなたは株式投資ブログの「ブログ文章作成係」です。
提供された調査データと分析レポートをもとに、読者を引き込む質の高いブログ記事を作成してください。

記事の要件：
- ターゲット読者: 個人投資家（初心者〜中級者）
- 文体: 分かりやすく親しみやすい、でも信頼感のある文章
- 構成:
  1. 読者を引く導入（なぜこの銘柄に注目するのか）
  2. 企業・銘柄の基本情報
  3. 投資の注目ポイント（強み・成長性）
  4. リスクと注意点（正直に伝える）
  5. まとめ・投資判断のヒント
- 文字数: 1500〜2500字程度
- 免責事項を末尾に追加すること

注意: 特定の投資を勧める表現は避け、あくまで情報提供として書いてください。
日本語で回答してください。"""


def write_blog_post(
    ticker: str,
    research_data: str,
    analysis: str,
    client: anthropic.Anthropic,
) -> str:
    """ブログ記事を執筆する"""
    print(f"\n[ブログ文章作成係] {ticker} の記事を執筆中...")

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"""以下の情報をもとに、株式投資ブログの記事を執筆してください。

【銘柄】{ticker}

【調査データ】
{research_data}

【分析レポート】
{analysis}""",
            }
        ],
    )

    result = next(
        (block.text for block in response.content if block.type == "text"), ""
    )
    print(f"[ブログ文章作成係] 執筆完了")
    return result
