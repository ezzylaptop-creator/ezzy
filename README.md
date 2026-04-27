# File Notes Cloud Emulator

Aplikasi sederhana berbasis Flask yang menggunakan konsep cloud emulator dengan LocalStack.

Aplikasi ini menggunakan minimal 2 service:
1. Amazon S3 (untuk penyimpanan file)
2. Amazon SQS (untuk antrean notifikasi upload)

Aplikasi juga menyediakan **mode demo lokal**, sehingga tetap dapat dijalankan tanpa Docker/LocalStack.

---

## Cara menjalankan

### 1. Mode Docker (Full Emulator)

```bash
docker compose up -d
