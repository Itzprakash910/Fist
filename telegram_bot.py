from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Aapka Bot Token
TOKEN = "7843096843:AAFqy6hmWlw98JkMwc6NuOvpLXQc_VtOtKY"

async def start(update: Update, context):
    await update.message.reply_text("Hello! Main aapka bot hoon.")

async def reply(update: Update, context):
    await update.message.reply_text(f"Aapne kaha: {update.message.text}")

def main():
    app = Application.builder().token(TOKEN).build()
    
    # Commands aur messages handle karne ke liye handlers add karein
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
    
    # Bot ko start karo
    app.run_polling()

if __name__ == "__main__":
    main()