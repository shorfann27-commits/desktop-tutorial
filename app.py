import os
import psycopg2
from flask import Flask, request, render_template_string
from dotenv import load_dotenv



load_dotenv()  # 本地读取 .env，Render 上读取环境变量
DATABASE_URL = os.environ["DATABASE_URL"]

app = Flask(__name__)

HTML = """
<!doctype html>
<html lang="zh">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>数据提交</title>
</head>
<body style="font-family:sans-serif;max-width:480px;margin:60px auto;">
  <h2>提交一行数据</h2>
  <form method="post">
    <input name="content" required maxlength="500"
           style="width:100%;padding:8px;" placeholder="请输入内容">
    <button type="submit" style="margin-top:12px;padding:8px 20px;">提交</button>
  </form>
  {% if msg %}<p>{{ msg }}</p>{% endif %}
</body>
</html>
"""

def init_db():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn, conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS entries (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT now()
                )
            """)
    finally:
        conn.close()

init_db()

@app.route("/", methods=["GET", "POST"])
def index():
    msg = None
    if request.method == "POST":
        content = request.form.get("content", "").strip()
        if content:
            conn = psycopg2.connect(DATABASE_URL)
            try:
                with conn, conn.cursor() as cur:
                    cur.execute("INSERT INTO entries (content) VALUES (%s)", (content,))
                msg = "✅ 提交成功！"
            except Exception as e:
                msg = f"❌ 提交失败：{e}"
            finally:
                conn.close()
        else:
            msg = "内容不能为空"
    return render_template_string(HTML, msg=msg)

if __name__ == "__main__":
    app.run(debug=True)