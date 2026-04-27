# File Notes Cloud Emulator

## Kegunaan Aplikasi

Aplikasi ini digunakan untuk mensimulasikan penggunaan layanan cloud AWS secara lokal.

Fungsi utama:
- Upload file dan catatan
- Menyimpan file menggunakan konsep S3
- Mengirim notifikasi menggunakan konsep SQS
- Menampilkan daftar file dan pesan

## Kelebihan Aplikasi

- Menggunakan konsep cloud computing (S3 & SQS)
- Dapat dijalankan tanpa cloud asli (LocalStack)
- Memiliki mode fallback (tetap jalan tanpa Docker)
- Mudah dikembangkan menjadi aplikasi nyata
- Arsitektur lebih rapi dengan sistem asynchronous (SQS)

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
