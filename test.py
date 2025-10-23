# test_openai_api_input_v1.py
from openai import OpenAI
import time

api_key = input("🔑 Masukkan API Key OpenAI kamu: ").strip()

client = OpenAI(api_key=api_key)

try:
    print("\n🔍 Menguji API key...")

    start_time = time.time()

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "Hai! Tes API key, balas satu kalimat saja."}
        ],
        max_tokens=30
    )

    duration = time.time() - start_time
    reply = response.choices[0].message.content

    print("\n✅ API key BERHASIL digunakan!")
    print("──────────────────────────────────────────────")
    print("💬 Respons GPT :", reply)
    print(f"⚡ Waktu respon : {duration:.2f} detik")
    print("──────────────────────────────────────────────")

except Exception as e:
    print("\n❌ API key tidak valid atau gagal mengakses server.")
    print("Pesan error:", e)
