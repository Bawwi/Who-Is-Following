import html
import json
import logging
import os
import re
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

user_data_store = {}

def normalize_username(raw_name):
    if not raw_name or not isinstance(raw_name, str):
        return None
    name = raw_name.strip().lstrip("@").lower()
    return name if name else None

def parse_followers(data):
    """Membaca format followers_1.json (username berada di string_list_data -> value)"""
    usernames = []
    seen = set()
    items = data if isinstance(data, list) else data.get("relationships_followers", [])
    for item in items:
        if not isinstance(item, dict):
            continue
        username = None
        string_list = item.get("string_list_data", [])
        if string_list and isinstance(string_list[0], dict):
            val = string_list[0].get("value")
            if val:
                username = normalize_username(val)
        if not username and item.get("title"):
            username = normalize_username(item["title"])

        if username and username not in seen:
            seen.add(username)
            usernames.append(username)
    return usernames

def parse_following(data):
    """Membaca format following.json terbaru dengan mempertahankan urutan asli"""
    usernames = []
    seen = set()
    items = data.get("relationships_following", []) if isinstance(data, dict) else data
    for item in items:
        if not isinstance(item, dict):
            continue
        username = None
        if item.get("title"):
            username = normalize_username(item["title"])
        else:
            string_list = item.get("string_list_data", [])
            if string_list and isinstance(string_list[0], dict):
                if string_list[0].get("value"):
                    username = normalize_username(string_list[0]["value"])
                elif string_list[0].get("href"):
                    match = re.search(r"instagram\.com/(?:_u/)?([^/?#]+)", string_list[0]["href"])
                    if match:
                        username = normalize_username(match.group(1))

        if username and username not in seen:
            seen.add(username)
            usernames.append(username)
    return usernames

async def send_formatted_list(message, base_title, usernames):
    """Mengirim daftar bernomor dengan jumlah total akun pada judul dan link profil IG"""
    total = len(usernames)
    full_title = f"{base_title} ({total} akun) :"

    if not usernames:
        await message.reply_text(f"<b>{html.escape(full_title)}</b>\nTidak ada.", parse_mode=ParseMode.HTML)
        return

    header = f"<b>{html.escape(full_title)}</b>\n"
    current_chunk = header

    for idx, username in enumerate(usernames, start=1):
        safe_user = html.escape(username)
        line = f'{idx} - <a href="https://www.instagram.com/{safe_user}">{safe_user}</a>\n'

        if len(current_chunk) + len(line) > 3800:
            await message.reply_text(
                current_chunk,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            current_chunk = ""

        current_chunk += line

    if current_chunk:
        await message.reply_text(
            current_chunk,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data_store[user_id] = {"followers": [], "following": [], "has_followers": False, "has_following": False}

    pesan_start = (
        "🤖 Who is following, adalah bot telegram untuk mengetahui siapa saja yang mengikuti akun Instagram anda, "
        "tidak mengikuti anda, dan yang tidak anda ikuti balik\n\n\n"
        "File yang dibutuhkan:\n"
        "• followers_1.json\n"
        "• following.json\n\n\n"
        "Cara mendapatkan filenya:\n"
        "1. Buka Instagram dan masuk ke akun Anda.\n"
        "2. Terus ke menu Pengaturan (Garis 3 dikanan atas).\n"
        "3. Pilih Akun Meta.\n"
        "4. Klik Informasi dan Izin Anda.\n"
        "5. Pilih Ekspor informasi Anda.\n"
        "6. Klik buat eskpor, pilih akun Instagram Anda.\n"
        "7. Klik Ekspor ke Perangkat.\n"
        "8. Klik sesuaikan informasi\n"
        "9. Pilih hanya Pengikut dan Mengikuti.\n"
        "10. Klik format JSON dan pilih Rentang tanggal (Sepanjang Waktu).\n"
        "11. Klik Mulai ekspor.\n"
        "12. Tunggu beberapa detik, setelah itu Unduh file tersebut.\n\n"
        "Nahh, kemudian kamu kirim kedua file tadi ke bot ini, agar dicek untuk kedua file tersebut.. 😁\n\n\n"
        'Creator: <a href="https://www.instagram.com/dimas.4a">dimas.4a</a>'
    )

    await update.message.reply_text(
        pesan_start,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pesan_report = (
        "Halooo, Kamu pasti mengalami masalah ya terhadap botnya, seperti masalah kamu dengan pasanganmu yang tidak kunjung selesai 😆, "
        "kamu bisa menghubungi admin dibawah ini untuk melaporkan masalah.\n\n"
        'Lapor ke admin: <a href="https://www.instagram.com/dimas.4a">dimm</a>'
    )

    await update.message.reply_text(
        pesan_report,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pesan_help = (
        "Halooo, Apakah kamu butuh bantuan? aku siap membantumu, pasti kamu kesulitan ya menggunakan bot ini, "
        "seperti kamu yang kesulitan mencari siapa saja yang tidak memfollowmu balik 😅.\n\n"
        "Langkah langkah cara menggunakannya:\n\n"
        "File yang dibutuhkan:\n"
        "- followers_1.json\n"
        "- following.json\n\n\n"
        "Cara mendapatkan filenya:\n"
        "1. Buka Instagram dan masuk ke akun Anda.\n"
        "2. Terus ke menu Pengaturan garis 3 dikanan atas.\n"
        "3. Pilih Akun Meta.\n"
        "4. Klik Informasi dan Izin Anda.\n"
        "5. Pilih Ekspor informasi Anda.\n"
        "6. Klik buat eskpor, pilih akun Instagram Anda.\n"
        "7. Klik Ekspor ke Perangkat.\n"
        "8. Klik sesuaikan informasi\n"
        "9. Pilih hanya Pengikut dan Mengikuti.\n"
        "11. Klik format JSON dan pilih Rentang tanggal (Sepanjang Waktu).\n"
        "12. Klik Mulai ekspor.\n"
        "13. Tunggu beberapa detik, setelah itu Unduh file tersebut.\n\n"
        "Nahh, kemudian kamu kirim kedua file tadi ke bot ini, untuk dicek kedua file tersebut.. 😁\n\n\n"
        'Creator: <a href="https://www.instagram.com/dimas.4a">dimas.4a</a>'
    )

    await update.message.reply_text(
        pesan_help,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data_store[user_id] = {"followers": [], "following": [], "has_followers": False, "has_following": False}
    await update.message.reply_text("Data berhasil direset. Silakan kirim ulang file JSON Anda.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_data_store:
        user_data_store[user_id] = {"followers": [], "following": [], "has_followers": False, "has_following": False}

    document = update.message.document
    file_name = document.file_name.lower()

    if not file_name.endswith(".json"):
        await update.message.reply_text("Harap kirim file dengan format .json.")
        return

    telegram_file = await document.get_file()
    file_bytes = await telegram_file.download_as_bytearray()

    try:
        json_content = json.loads(file_bytes.decode("utf-8"))
    except json.JSONDecodeError:
        await update.message.reply_text("File JSON rusak atau tidak dapat dibaca.")
        return

    if (isinstance(json_content, dict) and "relationships_following" in json_content) or "following" in file_name:
        parsed = parse_following(json_content)
        existing = set(user_data_store[user_id]["following"])
        for u in parsed:
            if u not in existing:
                user_data_store[user_id]["following"].append(u)
                existing.add(u)
        user_data_store[user_id]["has_following"] = True
        await update.message.reply_text("File following.json lagi dicek, sabar yaa..")
    elif isinstance(json_content, list) or "follower" in file_name:
        parsed = parse_followers(json_content)
        existing = set(user_data_store[user_id]["followers"])
        for u in parsed:
            if u not in existing:
                user_data_store[user_id]["followers"].append(u)
                existing.add(u)
        user_data_store[user_id]["has_followers"] = True
        await update.message.reply_text(f"File {html.escape(document.file_name)} lagi dicek, sabar yaa..")
    else:
        await update.message.reply_text("Format file JSON tidak dikenali.")
        return

    if user_data_store[user_id]["has_followers"] and user_data_store[user_id]["has_following"]:
        followers_list = user_data_store[user_id]["followers"]
        following_list = user_data_store[user_id]["following"]

        followers_set = set(followers_list)
        active_following = [u for u in following_list if not u.startswith("__deleted__")]
        active_following_set = set(active_following)

        not_following_back = [u for u in active_following if u not in followers_set]
        mutual = [u for u in active_following if u in followers_set]
        fans = [u for u in followers_list if u not in active_following_set]

        await send_formatted_list(update.message, "Daftar tidak follow balik", not_following_back)
        await send_formatted_list(update.message, "Daftar saling follow (Mutualan)", mutual)
        await send_formatted_list(update.message, "Daftar tidak Anda follow", fans)

        user_data_store[user_id] = {"followers": [], "following": [], "has_followers": False, "has_following": False}

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", report_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    print("Bot sedang berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
