# test_openai_api_input.py
import openai
import time

# Minta user masukkan API key tanpa menyimpannya
api_key = input("🔑 Masukkan API Key OpenAI kamu: ").strip()

# Set API key ke library
openai.api_key = api_key

try:
    print("\n🔍 Menguji API key...")

    start_time = time.time()

    # Kirim prompt sederhana
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hai! Tolong jawab 1 kalimat singkat untuk test API key ini."}],
        max_tokens=30
    )

    duration = time.time() - start_time
    reply = response["choices"][0]["message"]["content"]

    print("\n✅ API key BERHASIL digunakan!")
    print("──────────────────────────────────────────────")
    print("💬 Respons GPT :", reply)
    print(f"⚡ Waktu respon : {duration:.2f} detik")
    print("──────────────────────────────────────────────")

except Exception as e:
    print("\n❌ API key tidak valid atau gagal mengakses server.")
    print("Pesan error:", e)
