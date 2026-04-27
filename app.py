import os
from uuid import uuid4
from flask import Flask, request, redirect, render_template_string, flash, session

app = Flask(__name__)
app.secret_key = "cloud-secret-123"

BUCKET = os.getenv("S3_BUCKET", "file-notes-bucket")
QUEUE_NAME = os.getenv("SQS_QUEUE", "file-notes-queue")
ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")

users = {
    "admin": "ezzy"
}
uploaded_files = []
sqs_messages = []

HTML = """
<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cloud Notes Emulator</title>
<style>
*{box-sizing:border-box}
body{
  margin:0;
  font-family:'Segoe UI',Arial,sans-serif;
  background:#0066f5;
  color:white;
  overflow-x:hidden;
}
.stars{position:fixed;inset:0;z-index:0;pointer-events:none}
.star{
  position:absolute;width:2px;height:2px;background:white;border-radius:50%;
  animation:fall linear infinite;opacity:.8;
}
@keyframes fall{from{transform:translateY(-40px)}to{transform:translateY(100vh);opacity:0}}
.click-effect{
  position:fixed;width:15px;height:15px;border-radius:50%;
  background:#fff;pointer-events:none;z-index:9999;
  animation:click .55s ease-out forwards;
}
@keyframes click{from{transform:scale(1);opacity:.7}to{transform:scale(7);opacity:0}}

.navbar{
  position:relative;z-index:2;
  display:flex;align-items:center;justify-content:space-between;
  padding:25px 8%;
}
.logo{font-size:25px;font-weight:900;display:flex;align-items:center;gap:8px}
.logo span{background:white;color:#0066f5;border-radius:50%;padding:6px 8px;font-size:15px}
.menu a{color:white;text-decoration:none;margin:0 15px;font-weight:700}
.auth a{
  text-decoration:none;color:white;font-weight:800;margin-left:10px;
  padding:12px 22px;border-radius:12px;border:1px solid rgba(255,255,255,.4);
}
.auth .primary{background:rgba(255,255,255,.18);backdrop-filter:blur(10px)}

.banner{
  position:relative;z-index:2;
  width:66%;margin:10px auto 35px;
  background:white;color:#0f172a;border-radius:12px;
  padding:14px 22px;text-align:center;font-weight:900;
  box-shadow:0 10px 25px rgba(0,0,0,.15);
}
.banner span{color:#0066f5}

.hero{
  position:relative;z-index:2;
  width:84%;margin:0 auto 55px;
  display:grid;grid-template-columns:1.2fr .9fr;gap:45px;align-items:center;
}
.hero h1{font-size:64px;line-height:1.25;margin:0 0 25px;font-weight:900}
.hero p{font-size:21px;line-height:1.6;color:#dbeafe;margin-bottom:30px}
.btn{
  display:inline-block;text-decoration:none;border-radius:14px;
  padding:15px 28px;font-weight:900;margin-right:12px;
}
.btn-white{background:white;color:#0066f5}
.btn-outline{border:1px solid white;color:white}

.panel{
  background:white;color:#0f172a;border-radius:24px;padding:32px;
  box-shadow:0 30px 70px rgba(0,0,0,.25);
}
.panel h2{margin-top:0;font-size:28px}
.service{
  padding:17px;border-radius:16px;background:#f1f5f9;margin:15px 0;
  display:flex;justify-content:space-between;align-items:center;
}
.badge{background:#2563eb;color:white;border-radius:999px;padding:8px 13px;font-weight:900}

.features{
  position:relative;z-index:2;
  width:84%;margin:0 auto 70px;
  display:grid;grid-template-columns:repeat(4,1fr);gap:20px;
}
.feature{
  background:rgba(255,255,255,.14);
  border:1px solid rgba(255,255,255,.25);
  backdrop-filter:blur(14px);
  border-radius:20px;padding:24px;
  box-shadow:0 15px 35px rgba(0,0,0,.15);
}

.formbox{
  position:relative;z-index:2;
  max-width:430px;margin:50px auto;
  background:white;color:#0f172a;border-radius:24px;padding:32px;
  box-shadow:0 30px 70px rgba(0,0,0,.25);
}
.demo-box{
  background:linear-gradient(135deg,#2563eb,#1e40af);
  color:white;
  padding:13px;
  border-radius:13px;
  margin-bottom:15px;
  font-size:14px;
  line-height:1.6;
}
input,textarea{
  width:100%;padding:14px;margin:10px 0;
  border-radius:12px;border:1px solid #cbd5e1;font-size:15px;
}
button{
  width:100%;padding:15px;border:0;border-radius:12px;
  background:#0066f5;color:white;font-weight:900;font-size:15px;cursor:pointer;
}
button:hover{filter:brightness(1.08)}

.dashboard{
  position:relative;z-index:2;
  width:84%;margin:35px auto;
  display:grid;grid-template-columns:1fr 1fr;gap:25px;
}
.card{
  background:white;color:#0f172a;border-radius:24px;padding:28px;
  box-shadow:0 20px 50px rgba(0,0,0,.18);
}
.msg{
  position:relative;z-index:3;width:84%;margin:15px auto;
  background:#22c55e;color:white;padding:14px;border-radius:14px;font-weight:900;
}
li{background:#f1f5f9;margin:10px 0;padding:12px;border-radius:12px}
.footer{position:relative;z-index:2;text-align:center;color:#dbeafe;padding:30px}

@media(max-width:900px){
  .hero,.dashboard,.features{grid-template-columns:1fr}
  .hero h1{font-size:42px}
  .banner{width:90%}
  .menu{display:none}
}
</style>
</head>
<body>

<div class="stars" id="stars"></div>

<div class="navbar">
  <div class="logo"><span>☁</span> CloudNotes</div>
  <div class="menu">
    <a href="/">Beranda</a>
    <a href="#fitur">Fitur</a>
    <a href="/dashboard">Dashboard</a>
  </div>
  <div class="auth">
    {% if session.get("user") %}
      <a href="/logout" class="primary">Logout</a>
    {% else %}
      <a href="/login">Login</a>
      <a href="/register" class="primary">Daftar</a>
    {% endif %}
  </div>
</div>

{% with messages = get_flashed_messages() %}
  {% for m in messages %}
    <div class="msg">✅ {{m}}</div>
  {% endfor %}
{% endwith %}

{% if page == "home" %}

<div class="banner">
  Dapatkan pengalaman simulasi <span>Cloud Emulator S3 & SQS</span> dalam satu aplikasi
</div>

<section class="hero">
  <div>
    <h1>Cloud Storage<br>dan Queue<br>Lebih Mudah!</h1>
    <p>
      Aplikasi modern untuk upload file, menyimpan catatan,
      dan mensimulasikan layanan cloud seperti Amazon S3 dan SQS.
    </p>
    <a href="/register" class="btn btn-white">Mulai Sekarang</a>
    <a href="/login" class="btn btn-outline">Masuk</a>
  </div>

  <div class="panel">
    <h2>Pilih Service</h2>
    <p>Simulasi layanan cloud lokal untuk kebutuhan belajar dan demo project.</p>

    <div class="service">
      <div><b>Amazon S3</b><br>Penyimpanan file</div>
      <span class="badge">Storage</span>
    </div>

    <div class="service">
      <div><b>Amazon SQS</b><br>Antrean notifikasi</div>
      <span class="badge">Queue</span>
    </div>

    <div class="service">
      <div><b>Flask App</b><br>Backend aplikasi</div>
      <span class="badge">Web</span>
    </div>
  </div>
</section>

<section class="features" id="fitur">
  <div class="feature">
    <h3>📁 Upload File</h3>
    <p>User dapat mengunggah file beserta catatan.</p>
  </div>
  <div class="feature">
    <h3>☁ S3 Storage</h3>
    <p>Menggunakan konsep penyimpanan cloud storage.</p>
  </div>
  <div class="feature">
    <h3>📩 SQS Queue</h3>
    <p>Notifikasi upload masuk ke antrean pesan.</p>
  </div>
  <div class="feature">
    <h3>🚀 Mode Demo</h3>
    <p>Tetap bisa berjalan tanpa Docker/LocalStack.</p>
  </div>
</section>

{% elif page == "login" %}

<div class="formbox">
  <h2>Login Akun</h2>
  <p>Masuk untuk membuka dashboard aplikasi.</p>

  <div class="demo-box">
    🔑 <b>Akun Demo</b><br>
    Username: <b>admin</b><br>
    Password: <b>ezzy</b>
  </div>

  <form method="post">
    <input name="username" placeholder="Username" required>
    <input name="password" type="password" placeholder="Password" required>
    <button>Login</button>
  </form>
  <p>Belum punya akun? <a href="/register">Daftar</a></p>
</div>

{% elif page == "register" %}

<div class="formbox">
  <h2>Daftar Akun</h2>
  <p>Buat akun untuk mulai menggunakan aplikasi.</p>
  <form method="post">
    <input name="username" placeholder="Username baru" required>
    <input name="password" type="password" placeholder="Password baru" required>
    <button>Daftar</button>
  </form>
  <p>Sudah punya akun? <a href="/login">Login</a></p>
</div>

{% else %}

<div class="dashboard">
  <div class="card">
    <h2>📤 Upload File + Catatan</h2>
    <form method="post" action="/upload" enctype="multipart/form-data">
      <input type="file" name="file" required>
      <textarea name="note" rows="5" placeholder="Tulis catatan file..." required></textarea>
      <button>Simpan File & Kirim Notifikasi</button>
    </form>
  </div>

  <div class="card">
    <h2>⚙ Status Service</h2>
    <p><b>S3 Bucket:</b> {{bucket}}</p>
    <p><b>SQS Queue:</b> {{queue_name}}</p>
    <p><b>Endpoint:</b> {{endpoint}}</p>
    <p>Mode demo lokal aktif jika Docker/LocalStack belum tersedia.</p>
  </div>

  <div class="card">
    <h2>📁 Daftar File</h2>
    <ol>
      {% for f in files %}
        <li>📄 {{f}}</li>
      {% else %}
        <li>Belum ada file.</li>
      {% endfor %}
    </ol>
  </div>

  <div class="card">
    <h2>📩 Pesan Notifikasi</h2>
    <form method="post" action="/receive">
      <button>Ambil Pesan SQS</button>
    </form>
    <ol>
      {% for m in messages_sqs %}
        <li>🔔 {{m}}</li>
      {% else %}
        <li>Belum ada pesan ditampilkan.</li>
      {% endfor %}
    </ol>
  </div>
</div>

{% endif %}

<div class="footer">
  CloudNotes Emulator — Implementasi Cloud Emulator dengan konsep S3 dan SQS
</div>

<script>
const stars=document.getElementById("stars");
for(let i=0;i<100;i++){
  let s=document.createElement("div");
  s.className="star";
  s.style.left=Math.random()*100+"%";
  s.style.animationDuration=(2+Math.random()*5)+"s";
  s.style.animationDelay=Math.random()*5+"s";
  stars.appendChild(s);
}

document.addEventListener("click",function(e){
  let c=document.createElement("div");
  c.className="click-effect";
  c.style.left=e.clientX+"px";
  c.style.top=e.clientY+"px";
  document.body.appendChild(c);
  setTimeout(()=>c.remove(),550);
});
</script>

</body>
</html>
"""

def render(page, messages_sqs=[]):
    return render_template_string(
        HTML,
        page=page,
        files=uploaded_files,
        messages_sqs=messages_sqs,
        bucket=BUCKET,
        queue_name=QUEUE_NAME,
        endpoint=ENDPOINT_URL
    )

@app.route("/")
def home():
    return render("home")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users:
            flash("Username sudah terdaftar.")
            return redirect("/register")

        users[username] = password
        flash("Pendaftaran berhasil. Silakan login.")
        return redirect("/login")

    return render("register")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if users.get(username) == password:
            session["user"] = username
            flash("Login berhasil.")
            return redirect("/dashboard")

        flash("Username atau password salah.")
        return redirect("/login")

    return render("login")

@app.route("/dashboard")
def dashboard():
    if not session.get("user"):
        return redirect("/login")
    return render("dashboard")

@app.route("/logout")
def logout():
    session.clear()
    flash("Berhasil logout.")
    return redirect("/")

@app.route("/upload", methods=["POST"])
def upload():
    if not session.get("user"):
        return redirect("/login")

    file = request.files.get("file")
    note = request.form.get("note", "")

    if not file:
        flash("File belum dipilih.")
        return redirect("/dashboard")

    key = f"{uuid4().hex}_{file.filename}"
    uploaded_files.append(key)
    sqs_messages.append(f"File '{file.filename}' berhasil diupload. Catatan: {note}")

    flash("File berhasil disimpan dan notifikasi masuk antrean.")
    return redirect("/dashboard")

@app.route("/receive", methods=["POST"])
def receive():
    if not session.get("user"):
        return redirect("/login")

    if sqs_messages:
        received = sqs_messages.copy()
        sqs_messages.clear()
    else:
        received = ["Tidak ada pesan baru."]

    return render("dashboard", received)

if __name__ == "__main__":
    app.run(debug=True)
