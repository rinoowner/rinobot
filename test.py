import telebot
import sqlite3
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Bot Token
BOT_TOKEN = "6349322697:AAE1gcnB0PPqVLyLGmc5pEzqaLUpWs6w1e0"
bot = telebot.TeleBot(BOT_TOKEN)

# Admin User ID
ADMIN_USER_ID = "1351184742"

# Channel Username
CHANNEL_USERNAME = "@rinomodsofficial"

# Database Connection
conn = sqlite3.connect("bot_database.db", check_same_thread=False)
cursor = conn.cursor()

# Database Migration (Ensure necessary columns exist)
def migrate_database():
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN invites_count INTEGER DEFAULT 0;")
        conn.commit()
        print("Column 'invites_count' added successfully.")
    except sqlite3.OperationalError:
        print("Column 'invites_count' already exists.")

# Run migration before creating tables
migrate_database()

# Create Tables if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    invites_count INTEGER DEFAULT 0
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS referrals (
    referrer_id INTEGER,
    referred_id INTEGER,
    UNIQUE(referrer_id, referred_id)
)""")
conn.commit()

# Start Command
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    if len(message.text.split()) > 1:
        referrer_id = message.text.split()[1]
        if referrer_id.isdigit() and int(referrer_id) != user_id:
            cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
            cursor.execute("INSERT OR IGNORE INTO referrals (referrer_id, referred_id) VALUES (?, ?)", (referrer_id, user_id))
            cursor.execute("UPDATE users SET invites_count = invites_count + 1 WHERE user_id = ?", (referrer_id,))
            conn.commit()

    # Ask user to join the channel with a button
    markup = InlineKeyboardMarkup()
    join_button = InlineKeyboardButton("🎯 Join Channel", url=f"https://t.me/rinomodsofficial")
    markup.add(join_button)

    # Send message with join button
    bot.send_message(user_id, f"🎯 Agar aapko free paid hack chahiye toh humare channel ko join kariye: {CHANNEL_USERNAME}", reply_markup=markup)

    # Check if user is a member of the channel
    try:
        chat_member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if chat_member.status not in ['member', 'administrator', 'creator']:
            bot.send_message(user_id, f"⚠️ Aapko {CHANNEL_USERNAME} join karna hoga tabhi aap aage badh sakte hain.")
            return
    except Exception as e:
        bot.send_message(user_id, f"❌ Channel join status check nahi ho paya: {str(e)}")
        return

    # If user is a member, inform them about the task
    bot.send_message(user_id, "🎯 Task: Apna referral link 10 logon ko bhejo aur ek din ka free paid hack paao!")

    # Provide referral link
    referral_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
    bot.send_message(user_id, f"🔗 Yeh raha aapka referral link: {referral_link}")

# Track Referrals
@bot.message_handler(commands=['referrals'])
def referrals(message):
    user_id = message.chat.id
    cursor.execute("SELECT invites_count FROM users WHERE user_id = ?", (user_id,))
    invites = cursor.fetchone()
    if invites:
        invites_count = invites[0]
        bot.send_message(user_id, f"🎯 Aapke paas {invites_count} invites hain.")
        if invites_count >= 10:
            # Notify admin when a user completes 10 invites
            bot.send_message(
                ADMIN_USER_ID,
                f"🎉 User {user_id} ne 10 invites complete kar liye hain! Wo reward ke liye eligible hain."
            )
            bot.send_message(user_id, "🎉 Mubarak ho! Aapne 10 invites complete kar liye hain aur aapka reward ready hai. Admin se reward claim karein.")
        else:
            bot.send_message(user_id, f"🎯 Aapko {10 - invites_count} aur invites complete karne hain taaki aap reward claim kar sakein.")

# Admin Message to User After Completing Task
@bot.message_handler(commands=['send_message_to_user'])
def send_message_to_user(message):
    if message.chat.id == ADMIN_USER_ID:
        try:
            # Get user ID and custom message
            _, user_id, custom_message = message.text.split(' ', 2)
            user_id = int(user_id)
            bot.send_message(user_id, custom_message)
            bot.send_message(ADMIN_USER_ID, f"Custom message user {user_id} ko bheja gaya.")
        except ValueError:
            bot.send_message(ADMIN_USER_ID, "❌ Command ka format galat hai. Use karein: /send_message_to_user <user_id> <aapka_message>")

# Help Command
@bot.message_handler(commands=['help'])
def help(message):
    user_id = message.chat.id
    help_text = """
    🤖 **Bot Help Guide:**

    1️⃣ **/start** - Jab aap bot start karenge, aapko humare channel ko join karne ka option milega. 
       - Channel join karne par aapko 10 logon ko refer karne ka task milega.
       - 10 invites complete karne par aapko free paid hack milega!

    2️⃣ **/referrals** - Yeh command aapko batayega ki ab tak aap kitne logon ko refer kar chuke hain.

    📩 **Help** - Agar aapko kisi bhi feature ko samajhne mein koi dikkat ho, aap hamesha `/help` command use kar sakte hain!

    🔗 **Referral Link** - Apna unique referral link paane ke liye, aap `/start` command use kar sakte hain.
    """
    bot.send_message(user_id, help_text)

# Run the bot
bot.polling(none_stop=True)
