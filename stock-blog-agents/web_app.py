"""
株式投資ブログ AI作成 Webアプリ
localhost:5000 でのみ動作（自分だけが開ける）
"""
import os, json, uuid, queue, threading
from flask import Flask, render_template, request, Response, jsonify
from dotenv import load_dotenv, set_key
import anthropic

from agents.editor import plan_article, review_and_finalize
from agents.researcher import research_stock
from agents.analyst import analyze_stock
from agents.writer import write_blog_post

load_dotenv()

app = Flask(__name__)
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ジョブ管理（job_id → Queue）
jobs: dict[str, queue.Queue] = {}
articles: dict[str, str] = {}


# ─── SSEヘルパー ────────────────────────────────────
def sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


# ─── パイプライン本体（バックグラウンドスレッド） ──────
def run_pipeline(ticker: str, api_key: str, job_id: str, q: queue.Queue):
    def push(type, **kwargs):
        q.put({"type": type, **kwargs})

    try:
        client = anthropic.Anthropic(api_key=api_key)

        # Step1 編集長
        push("agent", key="editor", status="running")
        push("log", msg=f"[編集長] {ticker} の記事方針を検討中...")
        plan = plan_article(ticker, client)
        push("agent", key="editor", status="done")
        push("log", msg=f"[編集長] 完了")

        # Step2 株調
        push("agent", key="researcher", status="running")
        push("log", msg=f"[株調] {ticker} の情報を収集中...")
        research_data = research_stock(ticker, client)
        push("agent", key="researcher", status="done")
        push("log", msg=f"[株調] 完了")

        # Step3 分析係
        push("agent", key="analyst", status="running")
        push("log", msg=f"[分析係] {ticker} を分析中...")
        analysis = analyze_stock(ticker, research_data, client)
        push("agent", key="analyst", status="done")
        push("log", msg=f"[分析係] 完了")

        # Step4 ブログ作成係
        push("agent", key="writer", status="running")
        push("log", msg=f"[ブログ作成係] {ticker} の記事を執筆中...")
        draft = write_blog_post(ticker, research_data, analysis, client)
        push("agent", key="writer", status="done")
        push("log", msg=f"[ブログ作成係] 完了")

        # Step5 編集長（最終）
        push("agent", key="final", status="running")
        push("log", msg=f"[編集長] 最終チェック中...")
        final = review_and_finalize(ticker, research_data, analysis, draft, client)
        push("agent", key="final", status="done")
        push("log", msg=f"[編集長] 最終チェック完了！")

        articles[job_id] = final
        push("done", article=final)

    except anthropic.AuthenticationError:
        push("error", msg="APIキーが無効です。正しいキーを入力してください。")
    except Exception as e:
        push("error", msg=f"エラーが発生しました: {str(e)}")


# ─── ルート ────────────────────────────────────────
@app.route("/")
def index():
    has_key = bool(os.getenv("ANTHROPIC_API_KEY", "").strip())
    return render_template("index.html", has_key=has_key)


@app.route("/save_key", methods=["POST"])
def save_key():
    key = request.json.get("api_key", "").strip()
    if not key:
        return jsonify({"ok": False, "msg": "キーが空です"})
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        open(env_path, "w").close()
    set_key(env_path, "ANTHROPIC_API_KEY", key)
    os.environ["ANTHROPIC_API_KEY"] = key
    return jsonify({"ok": True})


@app.route("/generate", methods=["POST"])
def generate():
    ticker = (request.json.get("ticker") or "").strip()
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not ticker:
        return jsonify({"ok": False, "msg": "銘柄名を入力してください"})
    if not api_key:
        return jsonify({"ok": False, "msg": "APIキーが設定されていません"})

    job_id = str(uuid.uuid4())
    q: queue.Queue = queue.Queue()
    jobs[job_id] = q

    t = threading.Thread(target=run_pipeline, args=(ticker, api_key, job_id, q), daemon=True)
    t.start()
    return jsonify({"ok": True, "job_id": job_id})


@app.route("/stream/<job_id>")
def stream(job_id):
    q = jobs.get(job_id)
    if not q:
        return Response("data: {\"type\":\"error\",\"msg\":\"job not found\"}\n\n",
                        mimetype="text/event-stream")

    def event_stream():
        while True:
            try:
                msg = q.get(timeout=120)
                yield sse(msg)
                if msg.get("type") in ("done", "error"):
                    break
            except queue.Empty:
                yield sse({"type": "error", "msg": "タイムアウトしました"})
                break
        jobs.pop(job_id, None)

    return Response(event_stream(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/download/<job_id>")
def download(job_id):
    from flask import make_response
    from datetime import datetime
    article = articles.get(job_id, "")
    if not article:
        return "記事が見つかりません", 404
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    resp = make_response(article)
    resp.headers["Content-Type"] = "text/markdown; charset=utf-8"
    resp.headers["Content-Disposition"] = f"attachment; filename=blog_{ts}.md"
    return resp


if __name__ == "__main__":
    import webbrowser
    webbrowser.open("http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
