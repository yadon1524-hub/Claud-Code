"""
編集長エージェント: 全体の進行を指揮し、最終記事を品質チェックする
"""
import anthropic

SYSTEM_PROMPT = """あなたは株式投資ブログの「編集長」です。
担当ライターが書いた記事を最終チェックし、必要に応じて修正・改善を加えてください。

チェックポイント：
- 事実関係の整合性（調査データと記事の内容が一致しているか）
- 読みやすさ（導入・展開・まとめの流れが自然か）
- 投資情報としての適切さ（誤解を招く表現がないか）
- 免責事項の確認
- タイトルの魅力（読者がクリックしたくなるか）
- 全体的なクオリティ

記事を改善し、最終版として完成させてください。
タイトルも含めた完成記事を出力してください。
日本語で回答してください。"""


def review_and_finalize(
    ticker: str,
    research_data: str,
    analysis: str,
    draft: str,
    client: anthropic.Anthropic,
) -> str:
    """記事を最終チェックして完成させる"""
    print(f"\n[編集長] {ticker} の記事を最終チェック中...")

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=8192,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"""以下のドラフト記事を編集・完成させてください。

【銘柄】{ticker}

【調査データ（参照用）】
{research_data}

【分析レポート（参照用）】
{analysis}

【ドラフト記事】
{draft}

記事のクオリティを高め、最終版として完成させてください。""",
            }
        ],
    )

    result = next(
        (block.text for block in response.content if block.type == "text"), ""
    )
    print(f"[編集長] 最終チェック完了")
    return result


def plan_article(ticker: str, client: anthropic.Anthropic) -> str:
    """編集長が記事の方針を決める"""
    print(f"\n[編集長] {ticker} の記事方針を検討中...")

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"銘柄「{ticker}」のブログ記事を作成します。株調・分析係・ライターへの指示方針を簡潔にまとめてください。",
            }
        ],
    )

    result = next(
        (block.text for block in response.content if block.type == "text"), ""
    )
    return result
