# File Notes Cloud Emulator

Aplikasi sederhana Flask yang memakai LocalStack sebagai cloud emulator dengan minimal 2 service:

1. Amazon S3 emulator untuk menyimpan file.
2. Amazon SQS emulator untuk menyimpan notifikasi upload.

## Cara menjalankan

```bash
docker compose up -d
```

Buka:

```text
http://localhost:5000
```

## Alur aplikasi

1. User upload file dan menulis catatan.
2. File disimpan ke bucket S3 lokal.
3. Aplikasi mengirim pesan notifikasi ke antrean SQS lokal.
4. User dapat melihat daftar file S3 dan mengambil pesan SQS.
