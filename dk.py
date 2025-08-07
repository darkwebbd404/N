import telebot
import requests
import time
import threading
import json
import os

BOT_TOKEN = "8457409015:AAEhftH_WZqjHJOicWbOExW9WFRtZVJchZY"
bot = telebot.TeleBot(BOT_TOKEN)

DATA_FILE = "data.json"
REMAINS_FILE = "like_remains.json"
MAX_DAILY_LIKES = 1
ADMIN_USER_ID = 6632157651

# --------------------- JSON DB ---------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        data = {
            "vip_users": [ADMIN_USER_ID],
            "allowed_groups": [-1002727846121, ]
        }
        save_data(data)
        return data
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

data = load_data()

# --------------------- Remains DB ---------------------
def load_remains():
    if not os.path.exists(REMAINS_FILE):
        with open(REMAINS_FILE, "w") as f:
            json.dump({}, f)
    with open(REMAINS_FILE, "r") as f:
        return json.load(f)

def save_remains(remains):
    with open(REMAINS_FILE, "w") as f:
        json.dump(remains, f, indent=2)

def reset_daily_remains():
    save_remains({})
    print("🕛 Daily remains reset complete!")

def auto_reset_remains():
    while True:
        now = time.localtime()
        seconds_until_midnight = (24 * 60 * 60) - (now.tm_hour * 3600 + now.tm_min * 60 + now.tm_sec)
        time.sleep(seconds_until_midnight + 5)
        reset_daily_remains()

# --------------------- API CALL ---------------------
def call_api(region, uid):
    url = f"https://likexthug.vercel.app/like?uid={uid}&region={region}&key=GREAT"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code != 200 or not response.text.strip():
            return "API_ERROR"
        return response.json()
    except:
        return "API_ERROR"

# --------------------- LIKE PROCESS ---------------------
def process_like(message, region, uid):
    chat_id = message.chat.id
    user_id = message.from_user.id
    remains = load_remains()

    if user_id not in data["vip_users"]:
        used_count = remains.get(str(user_id), 0)
        if used_count >= MAX_DAILY_LIKES:
            bot.reply_to(message, "⚠️ Daily request limit reached! ⏳ Try again tomorrow.")
            return

    msg = bot.reply_to(message, "⏳ Processing your request... 🔄")
    time.sleep(0.5)
    bot.edit_message_text("🔄 Sending like request... 60%", chat_id, msg.message_id)
    time.sleep(0.5)
    bot.edit_message_text("🔄 Almost Done... 90%", chat_id, msg.message_id)

    response = call_api(region, uid)
    if response == "API_ERROR":
        bot.edit_message_text("🚨 API Error! Please wait 8 hours. ⚒️", chat_id, msg.message_id)
        return

    if response.get("status") == 1:
        result = response.get("response", {})

        caption = (
            f"✅ LIKE SUCCESSFULLY SEND\n\n"
            f"✨ NAME: `{res.get('PlayerNickname', 'N/A')}`\n"
            f"✨ UID: `{uid}`\n"
            f"✨ Like Before Command: `{res.get('LikesbeforeCommand', 0)}`\n"
            f"✨ Like After Command: `{res.get('LikesafterCommand', 0)}`\n"
            f"✨ Like Given By Bot: `{res.get('LikesGivenByAPI', 0)}`\n"
            f"📅 Valid Till: `{res.get('expire_date')}`"
        )

        try:
            photos = bot.get_user_profile_photos(user_id)
            if photos.total_count > 0:
                file_id = photos.photos[0][-1].file_id
                bot.edit_message_media(
                    chat_id=chat_id,
                    message_id=msg.message_id,
                    media=telebot.types.InputMediaPhoto(file_id, caption=caption, parse_mode="Markdown")
                )
                return
        except:
            pass

        bot.edit_message_text(caption, chat_id, msg.message_id, parse_mode="Markdown")
    else:
        bot.edit_message_text(
            f"💔 UID `{uid}` has already received max likes for today.\n🔄 Try a different UID.",
            chat_id, msg.message_id, parse_mode="Markdown"
        )

# --------------------- COMMAND: /like ---------------------
@bot.message_handler(commands=['like'])
def handle_like(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if chat_id not in data["allowed_groups"]:
        bot.reply_to(message, "🚫 This group is not allowed to use this bot! ❌")
        return

    args = message.text.split()
    if len(args) != 3:
        bot.reply_to(message, "❌ Format: `/like ind 1234567890`", parse_mode="Markdown")
        return

    region, uid = args[1].lower(), args[2]
    if not region.isalpha() or not uid.isdigit():
        bot.reply_to(message, "⚠️ Invalid input! Example: `/like ind 1234567890`", parse_mode="Markdown")
        return

    threading.Thread(target=process_like, args=(message, region, uid)).start()

# --------------------- COMMAND: /remains ---------------------
@bot.message_handler(commands=['remains'])
def check_remains(message):
    user_id = message.from_user.id
    remains = load_remains()
    used = remains.get(str(user_id), 0)

    bot.reply_to(
        message,
        f"📊 *TOTAL REMAINS LEFT ✅*\n"
        f"`({used}/{MAX_DAILY_LIKES})`\n\n"
        f"🕛 *REMAINS WILL AUTOMATICALLY RESET AT MIDNIGHT ❤️‍🩹*",
        parse_mode="Markdown"
    )

# --------------------- ADMIN COMMANDS ---------------------
@bot.message_handler(commands=['vip'])
def add_vip_user(message):
    if message.from_user.id != ADMIN_USER_ID:
        return
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        bot.reply_to(message, "❌ Use: /vip {user_id}")
        return
    vip_id = int(args[1])
    if vip_id not in data["vip_users"]:
        data["vip_users"].append(vip_id)
        save_data(data)
        bot.reply_to(message, f"✅ VIP access granted to `{vip_id}`", parse_mode="Markdown")
    else:
        bot.reply_to(message, "ℹ️ Already a VIP user.")

@bot.message_handler(commands=['allow'])
def add_allowed_group(message):
    if message.from_user.id != ADMIN_USER_ID:
        return
    args = message.text.split()
    if len(args) != 2 or not args[1].startswith("-100"):
        bot.reply_to(message, "❌ Use: /allow -100xxxxxxxxx")
        return
    group_id = int(args[1])
    if group_id not in data["allowed_groups"]:
        data["allowed_groups"].append(group_id)
        save_data(data)
        bot.reply_to(message, f"✅ Group `{group_id}` allowed!", parse_mode="Markdown")
    else:
        bot.reply_to(message, "ℹ️ Group is already allowed.")

@bot.message_handler(commands=['disband'])
def disband_group(message):
    if message.from_user.id != ADMIN_USER_ID:
        return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "❌ Use: /disband -100xxxxxxxxx")
        return
    group_id = int(args[1])
    if group_id in data["allowed_groups"]:
        data["allowed_groups"].remove(group_id)
        save_data(data)
        bot.reply_to(message, f"🚫 Group `{group_id}` removed from allowed list!", parse_mode="Markdown")
    else:
        bot.reply_to(message, "ℹ️ Group not found.")

@bot.message_handler(commands=['remove'])
def remove_vip(message):
    if message.from_user.id != ADMIN_USER_ID:
        return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "❌ Use: /remove {user_id}")
        return
    uid = int(args[1])
    if uid in data["vip_users"]:
        data["vip_users"].remove(uid)
        save_data(data)
        bot.reply_to(message, f"❌ VIP access removed from `{uid}`", parse_mode="Markdown")
    else:
        bot.reply_to(message, "ℹ️ User not found in VIP list.")

@bot.message_handler(commands=['setused'])
def set_used_remains(message):
    if message.from_user.id != ADMIN_USER_ID:
        return
    args = message.text.split()
    if len(args) != 3 or not args[1].isdigit() or not args[2].isdigit():
        bot.reply_to(message, "❌ Use: /setused {user_id} {count}")
        return
    uid, count = args[1], int(args[2])
    remains = load_remains()
    remains[uid] = count
    save_remains(remains)
    bot.reply_to(message, f"✅ Set remains used for `{uid}` to `{count}`", parse_mode="Markdown")

# --------------------- Start Bot ---------------------
print("🤖 Bot Started with JSON DB!")
threading.Thread(target=auto_reset_remains, daemon=True).start()
bot.polling(none_stop=True)
