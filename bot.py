import os
import sqlite3
from dotenv import load_dotenv
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Initialize the database
conn = sqlite3.connect('points.db')
cursor = conn.cursor()

# Create the users table if it doesn't exist
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                  user_id INTEGER PRIMARY KEY,
                  username TEXT,
                  points INTEGER DEFAULT 0)''')
conn.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to the Points Bot! Start sending messages to earn points.")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    # Check if the user already exists
    cursor.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()

    if result:
        # User exists, increment their points
        points = result[0] + 1
        cursor.execute("UPDATE users SET points=? WHERE user_id=?", (points, user_id))
    else:
        # New user, insert them into the database
        points = 1
        cursor.execute("INSERT INTO users (user_id, username, points) VALUES (?, ?, ?)", (user_id, username, points))

    conn.commit()

    await update.message.reply_text(f"{username}, you now have {points} points!")

async def points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    cursor.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()

    if result:
        points = result[0]
        await update.message.reply_text(f"You have {points} points.")
    else:
        await update.message.reply_text("You have no points yet. Start sending messages!")

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    cursor.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()

    if result and result[0] >= 100:  # Arbitrary conversion rate (e.g., 100 points = $1)
        points = result[0]
        amount = points // 100
        remaining_points = points % 100

        cursor.execute("UPDATE users SET points=? WHERE user_id=?", (remaining_points, user_id))
        conn.commit()

        await update.message.reply_text(f"Redeemed {amount} dollars. You have {remaining_points} points left.")
    else:
        await update.message.reply_text("You need at least 100 points to redeem money.")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("points", points))
    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # Set bot commands for ease of use
    app.bot.set_my_commands([
        BotCommand("points", "Check your points"),
        BotCommand("redeem", "Redeem your points for money")
    ])

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
