import os
import time
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError
from flask import Flask, request, redirect, render_template_string, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "file-notes-local-secret"

REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")
BUCKET = os.getenv("S3_BUCKET", "file-notes-bucket")
QUEUE_NAME = os.getenv("SQS_QUEUE", "file-notes-queue")

session = boto3.session.Session(
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
    region_name=REGION,
)
s3 = session.client("s3", endpoint_url=ENDPOINT_URL)
sqs = session.client("sqs", endpoint_url=ENDPOINT_URL)

HTML = """
<!doctype html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>File Notes Cloud Emulator</title>
  <style>
    body{font-family:Arial,sans-serif;background:#eef2ff;margin:0;color:#111827}
    .wrap{max-width:900px;margin:35px auto;background:white;padding:28px;border-radius:20px;box-shadow:0 10px 30px #0002}
    h1{margin-top:0;color:#1e3a8a}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}
    .card{border:1px solid #e5e7eb;padding:18px;border-radius:14px;background:#fafafa}
    input,textarea,button{width:100%;padding:11px;margin:8px 0;border-radius:10px;border:1px solid #cbd5e1;box-sizing:border-box}
    button{background:#2563eb;color:white;border:0;font-weight:bold;cursor:pointer}
    button:hover{background:#1d4ed8}.msg{background:#dcfce7;padding:10px;border-radius:10px;margin-bottom:12px}
    li{margin:8px 0;word-break:break-word}.small{color:#64748b;font-size:13px}
    @media(max-width:750px){.grid{grid-template-columns:1fr}}
  </style>
</head>
<body>
<div class="wrap">
  <h1>File Notes Cloud Emulator</h1>
  <p class="small">Aplikasi sederhana menggunakan 2 service LocalStack: S3 untuk penyimpanan file dan SQS untuk antrean notifikasi.</p>
  {% with messages = get_flashed_messages() %}{% if messages %}{% for m in messages %}<div class="msg">{{m}}</div>{% endfor %}{% endif %}{% endwith %}
  <div class="grid">
    <div class="card">
      <h3>Upload File + Catatan</h3>
      <form method="post" action="/upload" enctype="multipart/form-data">
        <label>Pilih file</label><input type="file" name="file" required>
        <label>Catatan</label><textarea name="note" rows="4" placeholder="Contoh: tugas cloud emulator" required></textarea>
        <button type="submit">Simpan ke S3 & Kirim ke SQS</button>
      </form>
    </div>
    <div class="card">
      <h3>Status Service</h3>
      <p><b>S3 Bucket:</b> {{bucket}}</p>
      <p><b>SQS Queue:</b> {{queue_name}}</p>
      <p><b>Endpoint:</b> {{endpoint}}</p>
    </div>
  </div>
  <div class="grid" style="margin-top:18px">
    <div class="card">
      <h3>Daftar File di S3</h3>
      <ol>{% for f in files %}<li>{{f}}</li>{% else %}<li>Belum ada file.</li>{% endfor %}</ol>
    </div>
    <div class="card">
      <h3>Pesan Masuk dari SQS</h3>
      <form method="post" action="/receive"><button type="submit">Ambil Pesan SQS</button></form>
      <ol>{% for m in messages_sqs %}<li>{{m}}</li>{% else %}<li>Belum ada pesan ditampilkan.</li>{% endfor %}</ol>
    </div>
  </div>
</div>
</body>
</html>
"""

def ensure_resources():
    for _ in range(20):
        try:
            buckets = [b["Name"] for b in s3.list_buckets().get("Buckets", [])]
            if BUCKET not in buckets:
                s3.create_bucket(Bucket=BUCKET)
            queues = sqs.list_queues(QueueNamePrefix=QUEUE_NAME).get("QueueUrls", [])
            if not queues:
                sqs.create_queue(QueueName=QUEUE_NAME)
            return
        except Exception:
            time.sleep(1)
    raise RuntimeError("LocalStack belum siap. Jalankan ulang setelah service aktif.")

def queue_url():
    return sqs.get_queue_url(QueueName=QUEUE_NAME)["QueueUrl"]

@app.route("/")
def index():
    ensure_resources()
    objects = s3.list_objects_v2(Bucket=BUCKET).get("Contents", [])
    files = [o["Key"] for o in objects]
    return render_template_string(HTML, files=files, messages_sqs=[], bucket=BUCKET, queue_name=QUEUE_NAME, endpoint=ENDPOINT_URL)

@app.route("/upload", methods=["POST"])
def upload():
    ensure_resources()
    file = request.files.get("file")
    note = request.form.get("note", "")
    if not file:
        flash("File belum dipilih.")
        return redirect("/")
    filename = secure_filename(file.filename)
    key = f"{uuid4().hex}_{filename}"
    s3.upload_fileobj(file, BUCKET, key)
    sqs.send_message(QueueUrl=queue_url(), MessageBody=f"File '{filename}' berhasil diupload. Catatan: {note}")
    flash("Berhasil: file masuk S3 dan notifikasi masuk SQS.")
    return redirect("/")

@app.route("/receive", methods=["POST"])
def receive():
    ensure_resources()
    resp = sqs.receive_message(QueueUrl=queue_url(), MaxNumberOfMessages=5, WaitTimeSeconds=1)
    received = []
    for msg in resp.get("Messages", []):
        received.append(msg["Body"])
        sqs.delete_message(QueueUrl=queue_url(), ReceiptHandle=msg["ReceiptHandle"])
    objects = s3.list_objects_v2(Bucket=BUCKET).get("Contents", [])
    files = [o["Key"] for o in objects]
    if not received:
        received = ["Tidak ada pesan baru di SQS."]
    return render_template_string(HTML, files=files, messages_sqs=received, bucket=BUCKET, queue_name=QUEUE_NAME, endpoint=ENDPOINT_URL)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
