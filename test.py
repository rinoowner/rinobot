import asyncio
import nest_asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import logging
from datetime import datetime, timedelta

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Admin details
ADMIN_CHAT_ID = '1351184742'  # Replace with actual admin chat ID

# Channel username
CHANNEL_USERNAME = "@rinomodsofficial"  # Replace with your channel's username

# Set to store user IDs
user_ids = set()  # Using a set to avoid duplicates

# Free key link (dynamic)
free_key_link = "https://t.me/rinosetup"  # Default link

# Data structure to store user info
user_data = {}

# Start command
async def start(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    user_id = user.id
    username = user.username if user.username else "N/A"
    first_name = user.first_name if user.first_name else "N/A"
    today = datetime.now().strftime("%Y-%m-%d")

    # Notify admin when a new user starts the bot
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"🚨 New user started the bot! 🚨\n\n"
                                                               f"Name: {first_name} {username}\n"
                                                               f"User ID: {user_id}")

    # Add user to the user_ids set (this will be used for broadcasting)
    user_ids.add(user_id)

    # Update user data
    if user_id not in user_data:
        user_data[user_id] = {"joined_date": today, "last_active": today, "is_vip": False}
    else:
        user_data[user_id]["last_active"] = today

    # Check if user is a member of the required channel
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)

        if member.status == "left":
            # If the user is not in the channel, send a prompt to join
            keyboard = [
                [KeyboardButton("Join Channel 🔒")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
            await update.message.reply_text(
                "👋 *Welcome to the Rino Mods Bot!* 🎮\n\n"
                "To get paid mod free key, please join our channel first. 🔒\n\n"
                "👇 Click below to join the channel 👇\n\n"
                "👇 after join the channel /start bot again 👇\n\n",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            # If the user is in the channel, show the available options
            keyboard = [
                [KeyboardButton("Get Mod 🎮")],
                [KeyboardButton("Tutorial Video 📹")],
                [KeyboardButton("Get Free Key 🔑")],
                [KeyboardButton("Buy VIP Key 💎")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
            await update.message.reply_text(
                "🎮 You have successfully joined the channel! Now you can access all the features.\n\n"
                "👇 Choose an option to proceed 👇",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Error while checking membership: {e}")
        await update.message.reply_text("❗ Oops, there was an issue verifying your channel membership. Please try again later.")

# Function to handle button presses
async def handle_buttons(update: Update, context: CallbackContext) -> None:
    global free_key_link
    text = update.message.text

    if text == "Join Channel 🔒":
        await update.message.reply_text("🔗 *Here is the channel link to join:* \n"
                                        "Please send a join request to our private channel.\n\n"
                                        "👉 [Click to Join the Channel](https://t.me/rinomodsofficial)",
                                        parse_mode="Markdown")

    elif text == "Get Mod 🎮":
        await update.message.reply_text("🔗 Here is the setup channel link: https://t.me/rinosetup")

    elif text == "Tutorial Video 📹":
        await update.message.reply_text(
            "📹 Watch this tutorial to get your free key!\n\n"
            "👉 [Click here to watch the tutorial video](https://t.me/rinosetup/596)",
            parse_mode="Markdown"
        )

    elif text == "Get Free Key 🔑":
        await update.message.reply_text(f"🔑 *Get your free key by clicking below:* \n{free_key_link}",
                                        parse_mode="Markdown")

    elif text == "Buy VIP Key 💎":
        await update.message.reply_text("""⭐️ *RINO MODS DDOS & MOD BOTH AVAILABLE* 👌

👑 *FEATURES*
✅ SERVER FREEZE 🥶 
✅ ESP  
✅ AIMBOT FOV

😢 *NOTE:* DDOS & MOD PANEL AVAILABLE 

🤩 *Price of mod*
❤️ Day - ₹150
❤️ Week - ₹600
❤️ Month - ₹1000

🤩 *Price of Ddos*
❤️ Day - ₹200
❤️ Week - ₹700
❤️ Month - ₹1200

💸💸💸💸💸💸

*Buy Now*: @OFFICIALRINO ✅
""", parse_mode="Markdown")

    else:
        await update.message.reply_text("❓ Something went wrong! Please try again.")

# Feedback after getting free key
async def feedback(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("📸 *Please send screenshots of our hack as feedback on @RINOxFEEDBACKSBT*\n\n"
                                    "❗ Without feedback, you won't be able to claim a free key next time. 🚫",
                                    parse_mode="Markdown")

# Broadcast message function
async def broadcast(update: Update, context: CallbackContext) -> None:
    # Only allow admin to use this command
    if str(update.message.from_user.id) == ADMIN_CHAT_ID:
        message = ' '.join(context.args) if context.args else None

        if not message:
            await update.message.reply_text("❗ Please provide a message to broadcast.")
            return

        for user_id in user_ids:
            try:
                await context.bot.send_message(chat_id=user_id, text=message)
            except Exception as e:
                logger.error(f"Error sending message to {user_id}: {e}")

        await update.message.reply_text("📢 Broadcast message sent successfully!")

    else:
        await update.message.reply_text("❌ You are not authorized to send broadcast messages.")

# Update free key link function
async def update_key(update: Update, context: CallbackContext) -> None:
    global free_key_link
    if str(update.message.from_user.id) == ADMIN_CHAT_ID:
        new_link = ' '.join(context.args)

        if not new_link:
            await update.message.reply_text("❗ Please provide a new link for the free key.")
            return

        free_key_link = new_link
        await update.message.reply_text(f"✅ Free key link updated to: {free_key_link}")
    else:
        await update.message.reply_text("❌ You are not authorized to update the free key link.")

# User analytics command
async def analytics(update: Update, context: CallbackContext) -> None:
    if str(update.message.from_user.id) == ADMIN_CHAT_ID:
        # Total users
        total_users = len(user_data)

        # Active users in last 24 hours
        active_users = sum(1 for user in user_data.values() 
                           if datetime.strptime(user['last_active'], "%Y-%m-%d") >= datetime.now() - timedelta(days=1))

        # VIP users count
        vip_users = sum(1 for user in user_data.values() if user.get('is_vip', False))

        # Recent users in the last 7 days
        new_users = sum(1 for user in user_data.values() 
                        if datetime.strptime(user['joined_date'], "%Y-%m-%d") >= datetime.now() - timedelta(days=7))

        # Analytics report
        report = (
            f"📊 *User Analytics Dashboard*\n\n"
            f"👥 *Total Users:* {total_users}\n"
            f"🟢 *Active Users (24h):* {active_users}\n"
            f"⭐ *VIP Users:* {vip_users}\n"
            f"🆕 *New Users (7d):* {new_users}\n"
        )
        await update.message.reply_text(report, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ You are not authorized to view analytics.")

# Main function to start the bot
async def main():
    application = Application.builder().token("7834989916:AAH1C-jvfyMlq7YjQ0EBnYZORWCpsOlO-w0").build()

    # Register commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("updatekey", update_key))
    application.add_handler(CommandHandler("analytics", analytics))

    # Register message handler to handle button presses
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))

    # Register message handler for feedback (images)
    application.add_handler(MessageHandler(filters.PHOTO, feedback))

    # Start the bot with polling
    await application.run_polling()

# Check if the script is being executed directly
if __name__ == '__main__':
    nest_asyncio.apply()  # Allows nested event loops
    asyncio.run(main())
