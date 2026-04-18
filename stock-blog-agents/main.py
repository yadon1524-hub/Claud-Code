"""
株式投資ブログ マルチエージェントシステム
=============================================
編集長 → 株調 → 分析係 → ブログ文章作成係 → 編集長（最終チェック）
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import anthropic

from agents.editor import plan_article, review_and_finalize
from agents.researcher import research_stock
from agents.analyst import analyze_stock
from agents.writer import write_blog_post

load_dotenv()


def save_article(ticker: str, article: str) -> str:
    """記事をファイルに保存する"""
    os.makedirs("output", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"output/{ticker}_{timestamp}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(article)
    return filename


def run_blog_pipeline(ticker: str) -> None:
    """ブログ記事作成パイプラインを実行する"""

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("エラー: ANTHROPIC_API_KEY が設定されていません。")
        print(".env ファイルに ANTHROPIC_API_KEY=your_api_key を追加してください。")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    print("=" * 60)
    print(f"株式投資ブログ 記事作成システム")
    print(f"対象銘柄: {ticker}")
    print("=" * 60)

    # Step 1: 編集長が記事の方針を決める
    print("\n【Step 1】編集長が方針を決定...")
    plan = plan_article(ticker, client)
    print(f"\n方針:\n{plan}")

    # Step 2: 株調が銘柄情報を収集
    print("\n【Step 2】株調が銘柄情報を収集...")
    research_data = research_stock(ticker, client)
    print(f"\n収集データ（抜粋）:\n{research_data[:300]}...")

    # Step 3: 分析係が分析レポートを作成
    print("\n【Step 3】分析係が分析...")
    analysis = analyze_stock(ticker, research_data, client)
    print(f"\n分析レポート（抜粋）:\n{analysis[:300]}...")

    # Step 4: ブログ文章作成係が記事を執筆
    print("\n【Step 4】ブログ文章作成係が執筆...")
    draft = write_blog_post(ticker, research_data, analysis, client)
    print(f"\nドラフト（抜粋）:\n{draft[:300]}...")

    # Step 5: 編集長が最終チェック・完成
    print("\n【Step 5】編集長が最終チェック...")
    final_article = review_and_finalize(ticker, research_data, analysis, draft, client)

    # 保存
    filename = save_article(ticker, final_article)

    print("\n" + "=" * 60)
    print(f"記事が完成しました！")
    print(f"保存先: {filename}")
    print("=" * 60)
    print("\n【完成記事】")
    print(final_article)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python main.py <銘柄名またはティッカー>")
        print("例:")
        print("  python main.py トヨタ自動車")
        print("  python main.py 7203")
        print("  python main.py NVIDIA")
        sys.exit(1)

    ticker = " ".join(sys.argv[1:])
    run_blog_pipeline(ticker)
