import sqlite3
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import telebot

# Bot Token
BOT_TOKEN = "7834989916:AAHBI8hQVE7mIk3mzLkDbL4hpsdQvEgx5ZI"
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
    username TEXT,
    full_name TEXT,
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
    username = message.chat.username
    full_name = message.chat.first_name + " " + (message.chat.last_name if message.chat.last_name else "")

    # If user is referred by someone
    if len(message.text.split()) > 1:
        referrer_id = message.text.split()[1]
        if referrer_id.isdigit() and int(referrer_id) != user_id:
            cursor.execute("INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)", (user_id, username, full_name))
            cursor.execute("INSERT OR IGNORE INTO referrals (referrer_id, referred_id) VALUES (?, ?)", (referrer_id, user_id))
            cursor.execute("UPDATE users SET invites_count = invites_count + 1 WHERE user_id = ?", (referrer_id,))
            conn.commit()

            # Notify Admin of New User Registration
            referrer_name = get_user_name(referrer_id)  # Get the name of the person who referred
            bot.send_message(
                ADMIN_USER_ID,
                f"📢 New User Alert:\nName: {full_name}\nUser ID: {user_id}\nReferred By: {referrer_name} ({referrer_id})"
            )

    # Insert user details if not already present
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)", (user_id, username, full_name))
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

    # If user is a member, provide the referral link
    bot.send_message(user_id, "🎯 Task: Apna referral link 10 logon ko bhejo aur 3 days ka paid hack free paao!")

    # Provide referral link
    referral_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
    bot.send_message(user_id, f"🔗 Yeh raha aapka referral link: {referral_link}")

# Function to get the name of the referrer
def get_user_name(user_id):
    cursor.execute("SELECT full_name FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if result:
        return result[0]  # Return full name of the referrer
    return "Unknown"  # If username not found

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
            bot.send_message(user_id, f"🎯 Aapko {10 - invites_count} aur invites complete karne hain taaki aapko 3 days paid hack mil ske.")
    else:
        bot.send_message(user_id, "📊 Aapke paas abhi tak koi invite nahi hai.")

# Admin Message to User After Completing Task
@bot.message_handler(commands=['send_message_to_user'])
def send_message_to_user(message):
    if message.chat.id == int(ADMIN_USER_ID):
        try:
            # Get user ID and custom message
            _, user_id, custom_message = message.text.split(' ', 2)
            user_id = int(user_id)
            bot.send_message(user_id, custom_message)
            bot.send_message(ADMIN_USER_ID, f"Custom message user {user_id} ko bheja gaya.")
        except ValueError:
            bot.send_message(ADMIN_USER_ID, "❌ Command ka format galat hai. Use karein: /send_message_to_user <user_id> <aapka_message>")
        except Exception as e:
            bot.send_message(ADMIN_USER_ID, f"❌ Message bhejne me error: {str(e)}")

# Admin Broadcast Message to All Users
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.chat.id == int(ADMIN_USER_ID):
        try:
            broadcast_message = message.text.split(' ', 1)[1]
            cursor.execute("SELECT user_id FROM users")
            users = cursor.fetchall()
            for user in users:
                try:
                    bot.send_message(user[0], broadcast_message)
                except Exception as e:
                    print(f"Error sending message to {user[0]}: {e}")
            bot.send_message(ADMIN_USER_ID, "✅ Broadcast message sabhi users ko bheja gaya.")
        except IndexError:
            bot.send_message(ADMIN_USER_ID, "❌ Command ka format galat hai. Use karein: /broadcast <message>")
        except Exception as e:
            bot.send_message(ADMIN_USER_ID, f"❌ Broadcast me error: {str(e)}")

# Admin Statistics Command
@bot.message_handler(commands=['statistics'])
def statistics(message):
    if message.chat.id == int(ADMIN_USER_ID):
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        bot.send_message(ADMIN_USER_ID, f"📊 Total Users: {total_users}")

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

    3️⃣ **Admin Commands:**
        - **/send_message_to_user <user_id> <message>** - Kisi specific user ko message bhejne ke liye.
        - **/broadcast <message>** - Sabhi users ko ek message bhejne ke liye.
        - **/statistics** - Total users ka count dekhne ke liye.

    📩 **Help** - Agar aapko kisi bhi feature ko samajhne mein koi dikkat ho, aap hamesha /help command use kar sakte hain!

    🔗 **Referral Link** - Apna unique referral link paane ke liye, aap /start command use kar sakte hain.
    """
    bot.send_message(user_id, help_text)

# Run the bot
bot.polling(none_stop=True)
