"""
株調エージェント: 銘柄情報をWeb検索で収集する
"""
import anthropic

SYSTEM_PROMPT = """あなたは株式投資ブログの「株調（銘柄調査担当）」です。
指定された銘柄について、以下の情報をWeb検索で収集してください：

- 企業概要・事業内容
- 直近の株価推移・時価総額
- 最新のニュース・決算情報
- 業界内でのポジション
- 主要な財務指標（PER、PBR、配当利回りなど）

収集した情報は正確に、ソースが分かる形でまとめてください。
日本語で回答してください。"""


def research_stock(ticker: str, client: anthropic.Anthropic) -> str:
    """指定銘柄の情報を調査する"""
    print(f"\n[株調] {ticker} の情報を収集中...")

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        tools=[
            {"type": "web_search_20260209", "name": "web_search"},
        ],
        messages=[
            {
                "role": "user",
                "content": f"銘柄「{ticker}」について詳しく調査してください。投資ブログの記事を書くために必要な情報をすべて収集してください。",
            }
        ],
    )

    # ツール使用ループ
    messages = [
        {
            "role": "user",
            "content": f"銘柄「{ticker}」について詳しく調査してください。投資ブログの記事を書くために必要な情報をすべて収集してください。",
        }
    ]

    while response.stop_reason == "tool_use":
        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": "検索実行済み",
                    }
                )
        messages.append({"role": "user", "content": tool_results})
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=[
                {"type": "web_search_20260209", "name": "web_search"},
            ],
            messages=messages,
        )

    result = next(
        (block.text for block in response.content if block.type == "text"), ""
    )
    print(f"[株調] 調査完了")
    return result
