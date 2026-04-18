#!/usr/bin/env python3
"""
請求書PDF生成スクリプト
使い方:
  python generate_invoice.py --client "山田商事" --subject "コンサルティング料" \
    --items '[{"name":"コンサルティング料","qty":1,"unit_price":50000}]'
"""
import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    from jinja2 import Template
    from playwright.sync_api import sync_playwright
except ImportError as e:
    print(f"必要なライブラリが不足しています: {e}")
    print("   pip install playwright jinja2 を実行してください")
    sys.exit(1)

BASE_DIR = Path(__file__).parent
SELLER_FILE = BASE_DIR / "seller.md"
LEDGER_FILE = BASE_DIR / "請求書番号台帳.md"
OUTPUT_DIR = BASE_DIR / "送付済み"
TEMPLATE_FILE = BASE_DIR / "templates" / "invoice.html"


def read_seller():
    seller = {}
    with open(SELLER_FILE, encoding="utf-8") as f:
        for line in f:
            if ":" in line and not line.startswith("#"):
                key, _, value = line.partition(":")
                seller[key.strip()] = value.strip()
    return seller


def get_next_invoice_number():
    today = datetime.today().strftime("%Y%m%d")
    prefix = f"INV-{today}-"
    if not LEDGER_FILE.exists():
        return f"{prefix}001"
    content = LEDGER_FILE.read_text(encoding="utf-8")
    matches = re.findall(re.escape(prefix) + r"(\d+)", content)
    if not matches:
        return f"{prefix}001"
    return f"{prefix}{str(max(int(m) for m in matches) + 1).zfill(3)}"


def update_ledger(invoice_no, client, total, filename):
    today = datetime.today().strftime("%Y-%m-%d")
    entry = f"| {invoice_no} | {today} | {client} | ¥{total:,} | {filename} |\n"
    if not LEDGER_FILE.exists():
        header = (
            "# 請求書番号台帳\n\n"
            "| 請求番号 | 発行日 | 宛先 | 合計 | ファイル名 |\n"
            "|---|---|---|---|---|\n"
        )
        LEDGER_FILE.write_text(header, encoding="utf-8")
    with open(LEDGER_FILE, "a", encoding="utf-8") as f:
        f.write(entry)


def generate_pdf(html_content, output_path):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html_content, wait_until="networkidle")
        page.pdf(
            path=str(output_path),
            format="A4",
            print_background=True,
            margin={"top": "20mm", "bottom": "20mm", "left": "15mm", "right": "15mm"},
        )
        browser.close()


def main():
    parser = argparse.ArgumentParser(description="請求書PDF生成")
    parser.add_argument("--client", required=True, help="宛先（会社名・氏名）")
    parser.add_argument("--subject", required=True, help="件名")
    parser.add_argument(
        "--items",
        required=True,
        help='項目JSON例: [{"name":"コンサルティング料","qty":1,"unit_price":50000}]',
    )
    args = parser.parse_args()

    seller = read_seller()
    invoice_no = get_next_invoice_number()
    issue_date = datetime.today()
    due_date = issue_date + timedelta(days=30)

    items = json.loads(args.items)
    for item in items:
        item["amount"] = item["qty"] * item["unit_price"]
    subtotal = sum(item["amount"] for item in items)
    tax = int(subtotal * 0.1)
    total = subtotal + tax

    template_src = TEMPLATE_FILE.read_text(encoding="utf-8")
    html = Template(template_src).render(
        invoice_no=invoice_no,
        issue_date=issue_date.strftime("%Y年%m月%d日"),
        due_date=due_date.strftime("%Y年%m月%d日"),
        client=args.client,
        subject=args.subject,
        items=items,
        subtotal=subtotal,
        tax=tax,
        total=total,
        seller=seller,
    )

    OUTPUT_DIR.mkdir(exist_ok=True)
    # ファイル名に使えない文字を除去
    safe_client = re.sub(r'[\\/:*?"<>|]', "", args.client)
    filename = f"{invoice_no}_{safe_client}.pdf"
    output_path = OUTPUT_DIR / filename

    print("PDF生成中...")
    generate_pdf(html, output_path)
    update_ledger(invoice_no, args.client, total, filename)

    print("請求書を作成しました")
    print(f"  ファイル: 送付済み/{filename}")
    print(f"  請求番号: {invoice_no}")
    print(f"  宛先    : {args.client}")
    print(f"  合計    : {total:,}円")


if __name__ == "__main__":
    main()
