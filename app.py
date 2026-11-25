import os
from flask import Flask, request, jsonify, render_template_string
import psycopg2

app = Flask(__name__)
DATABASE_URL = os.environ.get("DATABASE_URL")

HTML_PAGE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>在线记录板</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 600px; margin: 40px auto; padding: 0 16px; }
    .row { display: flex; gap: 8px; }
    input { flex: 1; padding: 10px; font-size: 16px; }
    button { padding: 10px 18px; font-size: 16px; cursor: pointer; }
    pre { background: #f4f4f4; padding: 12px; margin-top: 16px; white-space: pre-wrap; }
  </style>
</head>
<body>
  <h2>输入内容并保存到 Neon</h2>
  <form id="entry-form" class="row">
    <input id="content-input" type="text" placeholder="输入你想保存的内容..." required />
    <button type="submit">提交保存</button>
  </form>
  <pre id="status">等待输入...</pre>

  <script>
    const form = document.getElementById("entry-form");
    const input = document.getElementById("content-input");
    const statusBox = document.getElementById("status");

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const text = input.value.trim();
      if (!text) return;

      statusBox.textContent = "正在保存...";
      try {
        const res = await fetch("/api/entries", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content: text })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "保存失败");

        input.value = "";
        statusBox.textContent = "保存成功！\n" + JSON.stringify(data, null, 2);
      } catch (err) {
        statusBox.textContent = "错误：" + err.message;
      }
    });
  </script>
</body>
</html>
"""

def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("未设置 DATABASE_URL 环境变量")
    return psycopg2.connect(DATABASE_URL)

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_PAGE)

@app.route("/api/entries", methods=["POST"])
def create_entry():
    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify({"error": "内容不能为空"}), 400
    if len(content) > 2000:
        return jsonify({"error": "内容过长（最多 2000 字）"}), 400

    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO entries (content) VALUES (%s) RETURNING id, content, created_at;",
                    (content,)
                )
                row = cur.fetchone()
    finally:
        conn.close()

    return jsonify({
        "id": row[0],
        "content": row[1],
        "created_at": row[2].isoformat()
    }), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)