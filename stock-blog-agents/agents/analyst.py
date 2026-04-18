"""
分析係エージェント: 収集した銘柄情報を分析・評価する
"""
import anthropic

SYSTEM_PROMPT = """あなたは株式投資ブログの「分析係」です。
提供された銘柄情報をもとに、投資家向けの分析レポートを作成してください。

分析の観点：
- 投資の魅力（強み・成長性）
- リスク要因（弱み・懸念点）
- バリュエーション評価（割安か割高か）
- 中長期的な見通し
- 投資判断のポイント（買い・保留・見送りの根拠）

個人投資家にとって分かりやすい言葉で、具体的な根拠を示しながら分析してください。
日本語で回答してください。"""


def analyze_stock(ticker: str, research_data: str, client: anthropic.Anthropic) -> str:
    """銘柄情報を分析する"""
    print(f"\n[分析係] {ticker} を分析中...")

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"""以下の銘柄情報をもとに、投資分析レポートを作成してください。

【銘柄】{ticker}

【収集データ】
{research_data}""",
            }
        ],
    )

    result = next(
        (block.text for block in response.content if block.type == "text"), ""
    )
    print(f"[分析係] 分析完了")
    return result
