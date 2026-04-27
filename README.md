# Cloud Emulator File Notes

Aplikasi sederhana menggunakan Cloud Emulator (LocalStack) dengan:

- Amazon S3 → untuk penyimpanan file
- Amazon SQS → untuk message queue

## Cara Menjalankan

```bash
pip install -r requirements.txt
docker compose up -d
python app.py
