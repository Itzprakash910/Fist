import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# ✅ Bot Token & Configurations
TOKEN = "7843096843:AAFqy6hmWlw98JkMwc6NuOvpLXQc_VtOtKY"  # अपना बोट टोकन यहाँ डालें
MOVIE_DB = "movies.json"
ADMIN_ID = 6221923358  # अपना टेलीग्राम ID सेट करें
CHANNEL_ID = "@movie_realised"  # अपना चैनल ID सेट करें

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)

# ✅ JSON Database Functions
def load_movies():
    try:
        with open(MOVIE_DB, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_movies(movies):
    with open(MOVIE_DB, "w") as file:
        json.dump(movies, file, indent=4)

# ✅ Start Command
async def start(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("🎬 Movie List", callback_data='movie_list')],
        [InlineKeyboardButton("🔥 Latest Movies", callback_data='latest_movies')],
        [InlineKeyboardButton("🔎 Search", callback_data='search')],
        [InlineKeyboardButton("🔔 Set Reminder", callback_data='reminder')],
        [InlineKeyboardButton("ℹ️ Help", callback_data='help')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🎥 *Welcome to Movie Bot!*\nMovies ke latest updates yahan milenge.\n\nSelect an option:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ✅ Add Movies (Admin Only)
async def add_movies(update: Update, context):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("🚫 Aapke paas permission nahi hai!", parse_mode="Markdown")
        return

    text = update.message.text.split("\n")[1:]
    movies = load_movies()
    added_movies = []

    for line in text:
        details = line.split(" | ")
        if len(details) == 3:
            name, poster, link = details
            movies.append({"name": name.strip(), "poster": poster.strip(), "link": link.strip()})
            added_movies.append(name.strip())

    if added_movies:
        save_movies(movies)
        await update.message.reply_text(f"✅ *Movies Added:*\n🎬 " + "\n🎬 ".join(added_movies), parse_mode="Markdown")
        
        # ✅ Notify Users
        notification_text = "🎥 *New Movies Added!*\n\n" + "\n".join([f"🎬 {m}" for m in added_movies])
        await context.bot.send_message(chat_id=CHANNEL_ID, text=notification_text, parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ *Format:* `/add_movies`\nMovie1 | Poster_URL1 | Link1\nMovie2 | Poster_URL2 | Link2", parse_mode="Markdown")

# ✅ Delete Movie (Admin Only)
async def delete_movie(update: Update, context):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("🚫 Aapke paas permission nahi hai!", parse_mode="Markdown")
        return

    try:
        movie_name = " ".join(context.args)
        movies = load_movies()
        movies = [m for m in movies if m["name"].lower() != movie_name.lower()]
        save_movies(movies)
        await update.message.reply_text(f"✅ *Movie deleted:* {movie_name}", parse_mode="Markdown")
    except:
        await update.message.reply_text("⚠️ *Format:* `/delete_movie MovieName`", parse_mode="Markdown")

# ✅ Show Movie List
async def show_movie_names(update: Update, context):
    movies = load_movies()
    if not movies:
        await update.callback_query.message.reply_text("❌ Koi movies available nahi hain!", parse_mode="Markdown")
        return

    buttons = []
    row = []
    for movie in movies:
        row.append(InlineKeyboardButton(movie["name"], callback_data=f"movie_{movie['name']}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    
    if row:
        buttons.append(row)

    reply_markup = InlineKeyboardMarkup(buttons)
    await update.callback_query.message.reply_text("🎬 *Movie List:*", reply_markup=reply_markup, parse_mode="Markdown")

# ✅ Show Movie Details
async def show_movie_details(update: Update, context):
    query = update.callback_query
    movie_name = query.data.replace("movie_", "")
    movies = load_movies()
    movie = next((m for m in movies if m["name"] == movie_name), None)

    if not movie:
        await query.message.reply_text("❌ *Movie nahi mili!*", parse_mode="Markdown")
        return

    keyboard = [[InlineKeyboardButton("🔗 Watch", url=movie["link"])]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_photo(
        photo=movie["poster"],
        caption=f"🎬 *{movie['name']}*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ✅ Search Movie Feature (With Clickable Buttons)
async def search_movie(update: Update, context):
    query = " ".join(context.args).lower()
    movies = load_movies()
    results = [m for m in movies if query in m["name"].lower()]

    if results:
        buttons = [[InlineKeyboardButton(m["name"], callback_data=f"movie_{m['name']}")] for m in results]
        reply_markup = InlineKeyboardMarkup(buttons)

        await update.message.reply_text(
            "🔎 *Search Results:*",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ *Movie nahi mili!*", parse_mode="Markdown")

# ✅ Button Click Handling
async def button_click(update: Update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "movie_list":
        await show_movie_names(update, context)
    elif query.data.startswith("movie_"):
        await show_movie_details(update, context)
    elif query.data == "search":
        await query.message.reply_text("🔎 *Search a movie using:* `/search MovieName`", parse_mode="Markdown")
    elif query.data == "reminder":
        await query.message.reply_text("🔔 Feature Coming Soon!", parse_mode="Markdown")
    elif query.data == "help":
        await query.message.reply_text("ℹ️ *Commands:*\n/search MovieName\n/add_movies\n/delete_movie Name", parse_mode="Markdown")

# ✅ Block User Messages (Prevents Spam)
async def block_user_messages(update: Update, context):
    await update.message.delete()

# ✅ Main Function
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add_movies", add_movies))
    app.add_handler(CommandHandler("delete_movie", delete_movie))
    app.add_handler(CommandHandler("search", search_movie))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, block_user_messages))

    logging.info("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()