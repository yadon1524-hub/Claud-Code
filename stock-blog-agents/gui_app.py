"""
株式投資ブログ AI作成アプリ
デスクトップGUIアプリケーション
"""
import customtkinter as ctk
import threading
import os
import sys
import queue
from datetime import datetime
from dotenv import load_dotenv
import anthropic

# エージェントのインポート
from agents.editor import plan_article, review_and_finalize
from agents.researcher import research_stock
from agents.analyst import analyze_stock
from agents.writer import write_blog_post

load_dotenv()

# テーマ設定
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class StockBlogApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("📈 株式投資ブログ AI作成アプリ")
        self.geometry("1100x750")
        self.minsize(900, 600)

        # メッセージキュー（スレッド間通信用）
        self.msg_queue = queue.Queue()
        self.result_data = {}
        self.is_running = False

        self._build_ui()
        self._check_api_key()
        self.after(100, self._process_queue)

    # ─────────────────────────────────────────
    # UI構築
    # ─────────────────────────────────────────
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_left_panel()
        self._build_right_panel()

    def _build_left_panel(self):
        left = ctk.CTkFrame(self, width=280, corner_radius=0)
        left.grid(row=0, column=0, sticky="nsew")
        left.grid_propagate(False)
        left.grid_rowconfigure(8, weight=1)

        # ロゴ
        ctk.CTkLabel(
            left, text="📈", font=ctk.CTkFont(size=48)
        ).grid(row=0, column=0, pady=(30, 0))

        ctk.CTkLabel(
            left, text="株式投資ブログ",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=1, column=0, pady=(4, 0))

        ctk.CTkLabel(
            left, text="AI作成アプリ",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        ).grid(row=2, column=0, pady=(0, 20))

        ctk.CTkFrame(left, height=1, fg_color="gray30").grid(
            row=3, column=0, sticky="ew", padx=20, pady=8
        )

        # 銘柄入力
        ctk.CTkLabel(
            left, text="🔍 銘柄名 / ティッカー",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        ).grid(row=4, column=0, sticky="w", padx=20, pady=(16, 4))

        self.ticker_entry = ctk.CTkEntry(
            left, placeholder_text="例: トヨタ自動車 / 7203 / NVIDIA",
            height=40, font=ctk.CTkFont(size=13)
        )
        self.ticker_entry.grid(row=5, column=0, padx=20, sticky="ew")
        self.ticker_entry.bind("<Return>", lambda e: self._start_pipeline())

        # APIキー入力
        ctk.CTkLabel(
            left, text="🔑 APIキー（未設定時のみ）",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        ).grid(row=6, column=0, sticky="w", padx=20, pady=(16, 4))

        self.api_entry = ctk.CTkEntry(
            left, placeholder_text="ANTHROPIC_API_KEY",
            height=40, font=ctk.CTkFont(size=13), show="*"
        )
        self.api_entry.grid(row=7, column=0, padx=20, sticky="ew")

        # 実行ボタン
        self.run_btn = ctk.CTkButton(
            left, text="▶  記事を生成する",
            height=45, font=ctk.CTkFont(size=14, weight="bold"),
            command=self._start_pipeline,
            fg_color="#1f6aa5", hover_color="#144870"
        )
        self.run_btn.grid(row=9, column=0, padx=20, pady=(24, 8), sticky="ew")

        # 保存ボタン
        self.save_btn = ctk.CTkButton(
            left, text="💾  記事を保存する",
            height=40, font=ctk.CTkFont(size=13),
            command=self._save_article,
            fg_color="transparent", border_width=1,
            text_color=("gray10", "gray90"),
            state="disabled"
        )
        self.save_btn.grid(row=10, column=0, padx=20, pady=(0, 8), sticky="ew")

        # クリアボタン
        ctk.CTkButton(
            left, text="🗑  クリア",
            height=36, font=ctk.CTkFont(size=12),
            command=self._clear,
            fg_color="transparent", border_width=1,
            text_color=("gray40", "gray60")
        ).grid(row=11, column=0, padx=20, pady=(0, 30), sticky="ew")

    def _build_right_panel(self):
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=16, pady=16)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        # 進捗カード
        progress_frame = ctk.CTkFrame(right)
        progress_frame.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        ctk.CTkLabel(
            progress_frame, text="🤖 エージェントの進捗",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=16, pady=(12, 8))

        self.agent_labels = {}
        agents = [
            ("editor",     "📋 編集長",       "方針決定"),
            ("researcher", "🔍 株調",         "情報収集"),
            ("analyst",    "📊 分析係",       "分析"),
            ("writer",     "✍️  ブログ作成係", "執筆"),
            ("final",      "✅ 編集長",       "最終チェック"),
        ]

        for i, (key, name, action) in enumerate(agents):
            card = ctk.CTkFrame(progress_frame, fg_color="gray20", corner_radius=8)
            card.grid(row=1, column=i, padx=(8 if i == 0 else 4, 4 if i < 4 else 8),
                      pady=(0, 12), sticky="ew")
            progress_frame.grid_columnconfigure(i, weight=1)

            ctk.CTkLabel(card, text=name,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         wraplength=130).pack(pady=(10, 2))
            ctk.CTkLabel(card, text=action,
                         font=ctk.CTkFont(size=10),
                         text_color="gray").pack()

            status_lbl = ctk.CTkLabel(card, text="⏸ 待機中",
                                      font=ctk.CTkFont(size=11),
                                      text_color="gray50")
            status_lbl.pack(pady=(4, 10))
            self.agent_labels[key] = (card, status_lbl)

        # タブビュー（ログ / 記事）
        self.tabview = ctk.CTkTabview(right, height=480)
        self.tabview.grid(row=1, column=0, sticky="nsew")

        self.tabview.add("📄 完成記事")
        self.tabview.add("📋 ログ")

        # 記事タブ
        self.article_text = ctk.CTkTextbox(
            self.tabview.tab("📄 完成記事"),
            font=ctk.CTkFont(family="Yu Gothic UI", size=13),
            wrap="word"
        )
        self.article_text.pack(fill="both", expand=True, padx=4, pady=4)

        # ログタブ
        self.log_text = ctk.CTkTextbox(
            self.tabview.tab("📋 ログ"),
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color="lime green",
            fg_color="gray10",
            wrap="word"
        )
        self.log_text.pack(fill="both", expand=True, padx=4, pady=4)

        # ステータスバー
        self.status_label = ctk.CTkLabel(
            right, text="準備完了 ✔",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.status_label.grid(row=2, column=0, sticky="w", pady=(4, 0))

    # ─────────────────────────────────────────
    # ロジック
    # ─────────────────────────────────────────
    def _check_api_key(self):
        key = os.getenv("ANTHROPIC_API_KEY", "")
        if key:
            self.api_entry.insert(0, "（.envから読み込み済み）")
            self.api_entry.configure(state="disabled")

    def _get_api_key(self):
        env_key = os.getenv("ANTHROPIC_API_KEY", "")
        if env_key:
            return env_key
        return self.api_entry.get().strip()

    def _set_agent_status(self, key, status):
        """エージェントカードの色とテキストを更新"""
        colors = {
            "waiting":  ("gray20", "gray50",  "⏸ 待機中"),
            "running":  ("#1a3a5c", "#4da6ff", "⚙️ 処理中..."),
            "done":     ("#0d3320", "#4caf50", "✅ 完了"),
            "error":    ("#3a1a1a", "#ff5555", "❌ エラー"),
        }
        fg, txt_color, label = colors.get(status, colors["waiting"])
        card, lbl = self.agent_labels[key]
        card.configure(fg_color=fg)
        lbl.configure(text=label, text_color=txt_color)

    def _log(self, msg):
        self.msg_queue.put(("log", msg))

    def _set_status(self, msg):
        self.msg_queue.put(("status", msg))

    def _agent_status(self, key, status):
        self.msg_queue.put(("agent", key, status))

    def _set_article(self, text):
        self.msg_queue.put(("article", text))

    def _pipeline_done(self):
        self.msg_queue.put(("done", None))

    def _process_queue(self):
        """メインスレッドでUIを更新"""
        try:
            while True:
                item = self.msg_queue.get_nowait()
                if item[0] == "log":
                    self.log_text.insert("end", item[1] + "\n")
                    self.log_text.see("end")
                elif item[0] == "status":
                    self.status_label.configure(text=item[1])
                elif item[0] == "agent":
                    self._set_agent_status(item[1], item[2])
                elif item[0] == "article":
                    self.article_text.delete("1.0", "end")
                    self.article_text.insert("1.0", item[1])
                    self.tabview.set("📄 完成記事")
                elif item[0] == "done":
                    self.is_running = False
                    self.run_btn.configure(state="normal", text="▶  記事を生成する")
                    self.save_btn.configure(state="normal")
                    self._set_status("✅ 記事の生成が完了しました")
        except queue.Empty:
            pass
        self.after(100, self._process_queue)

    def _start_pipeline(self):
        if self.is_running:
            return

        ticker = self.ticker_entry.get().strip()
        if not ticker:
            self._show_error("銘柄名またはティッカーを入力してください。")
            return

        api_key = self._get_api_key()
        if not api_key or api_key == "（.envから読み込み済み）":
            api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            self._show_error("APIキーが設定されていません。\n入力欄にAPIキーを入力してください。")
            return

        # UIリセット
        self.is_running = True
        self.run_btn.configure(state="disabled", text="⏳ 生成中...")
        self.save_btn.configure(state="disabled")
        self.log_text.delete("1.0", "end")
        self.article_text.delete("1.0", "end")
        for key in self.agent_labels:
            self._set_agent_status(key, "waiting")

        # バックグラウンドで実行
        thread = threading.Thread(
            target=self._run_pipeline,
            args=(ticker, api_key),
            daemon=True
        )
        thread.start()

    def _run_pipeline(self, ticker, api_key):
        try:
            client = anthropic.Anthropic(api_key=api_key)

            self._log(f"{'='*50}")
            self._log(f"  対象銘柄: {ticker}")
            self._log(f"  開始時刻: {datetime.now().strftime('%H:%M:%S')}")
            self._log(f"{'='*50}")

            # Step 1: 編集長 - 方針決定
            self._agent_status("editor", "running")
            self._set_status("📋 編集長が方針を検討中...")
            self._log("\n[Step 1] 編集長 → 方針決定")
            plan = plan_article(ticker, client)
            self._log(plan[:300] + "...")
            self._agent_status("editor", "done")

            # Step 2: 株調 - 情報収集
            self._agent_status("researcher", "running")
            self._set_status("🔍 株調が情報を収集中...")
            self._log("\n[Step 2] 株調 → 銘柄情報収集")
            research_data = research_stock(ticker, client)
            self._log(research_data[:400] + "...")
            self._agent_status("researcher", "done")

            # Step 3: 分析係
            self._agent_status("analyst", "running")
            self._set_status("📊 分析係が分析中...")
            self._log("\n[Step 3] 分析係 → 投資分析")
            analysis = analyze_stock(ticker, research_data, client)
            self._log(analysis[:400] + "...")
            self._agent_status("analyst", "done")

            # Step 4: ブログ文章作成係
            self._agent_status("writer", "running")
            self._set_status("✍️ ブログ文章作成係が執筆中...")
            self._log("\n[Step 4] ブログ文章作成係 → 記事執筆")
            draft = write_blog_post(ticker, research_data, analysis, client)
            self._log(draft[:400] + "...")
            self._agent_status("writer", "done")

            # Step 5: 編集長 - 最終チェック
            self._agent_status("final", "running")
            self._set_status("✅ 編集長が最終チェック中...")
            self._log("\n[Step 5] 編集長 → 最終チェック・完成")
            final_article = review_and_finalize(
                ticker, research_data, analysis, draft, client
            )
            self._agent_status("final", "done")

            self.result_data = {
                "ticker": ticker,
                "article": final_article,
            }

            self._set_article(final_article)
            self._log("\n" + "="*50)
            self._log("  🎉 記事の生成が完了しました！")
            self._log("="*50)

        except anthropic.AuthenticationError:
            self._log("\n❌ エラー: APIキーが無効です。")
            self._set_status("❌ APIキーエラー")
            for key in self.agent_labels:
                self._set_agent_status(key, "waiting")
        except Exception as e:
            self._log(f"\n❌ エラーが発生しました: {e}")
            self._set_status(f"❌ エラー: {str(e)[:40]}")

        self._pipeline_done()

    def _save_article(self):
        article = self.result_data.get("article", "")
        ticker = self.result_data.get("ticker", "output")
        if not article:
            return

        os.makedirs("output", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"output/{ticker}_{timestamp}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(article)

        self._set_status(f"💾 保存完了: {filename}")
        self._log(f"\n💾 保存先: {os.path.abspath(filename)}")

    def _clear(self):
        self.ticker_entry.delete(0, "end")
        self.log_text.delete("1.0", "end")
        self.article_text.delete("1.0", "end")
        for key in self.agent_labels:
            self._set_agent_status(key, "waiting")
        self.save_btn.configure(state="disabled")
        self.result_data = {}
        self._set_status("準備完了 ✔")

    def _show_error(self, msg):
        dialog = ctk.CTkToplevel(self)
        dialog.title("エラー")
        dialog.geometry("360x160")
        dialog.grab_set()
        ctk.CTkLabel(dialog, text="⚠️ " + msg,
                     font=ctk.CTkFont(size=13),
                     wraplength=320).pack(pady=30)
        ctk.CTkButton(dialog, text="OK",
                      command=dialog.destroy, width=100).pack()


# ─────────────────────────────────────────
# 起動
# ─────────────────────────────────────────
if __name__ == "__main__":
    # スクリプトのディレクトリをカレントに設定
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    app = StockBlogApp()
    app.mainloop()
