import json
import logging
import asyncio 
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# ✅ Bot Token & Configurations
TOKEN = "8125453394:AAEDSmpVpwgKThrjzvaGFmGF1mx-hpVbBLk"  # ❌ Apne bot ka token yahan dalein (security ke liye hardcoded token hataya gaya)
MOVIE_DB = "movies.json"  # Movie database file
ADMIN_ID = [6221923358]  # Admin ke Telegram ID list
CHANNEL_ID = ["@movie_realised", "@new_realise_movie_2025"]  # Movie update channels

# ✅ Logging setup
logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)

# ✅ JSON Database Functions
def load_movies():
    """Movies list JSON file se load kare."""
    try:
        with open(MOVIE_DB, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_movies(movies):
    """Movies list ko JSON file me save kare."""
    with open(MOVIE_DB, "w") as file:
        json.dump(movies, file, indent=4)

# ✅ Start Command
async def start(update: Update, context):
    """Bot ke start hone par welcome message aur buttons show kare."""
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
 # ✅ Sleep function ke liye import

async def add_movies(update: Update, context):
    """Admin ko naye movies add karne ki permission dega."""
    user_id = update.message.from_user.id
    if user_id not in ADMIN_ID:
        await update.message.reply_text("🚫 Aapke paas permission nahi hai!", parse_mode="Markdown")
        return

    text = update.message.text.split("\n")[1:]
    movies = load_movies()
    added_movies = []

    for line in text:
        details = line.split(" | ")
        if len(details) == 3:
            name, poster, link = details
            temp_movie = {"name": name.strip(), "poster": poster.strip(), "link": link.strip()}
            added_movies.append(temp_movie)

    if added_movies:
        # ✅ Notify Telegram Channel (Without Delay)
        final_notification = "🎥 *New Movies Available!*\n\n" + "\n".join(
            [f"🎬 {m['name']} - [Watch Now]({m['link']})" for m in added_movies]
        )
        for channel in CHANNEL_ID:
            await context.bot.send_message(chat_id=channel, text=final_notification, parse_mode="Markdown")

        # ✅ Show movie preview in bot (10s only)
        for movie in added_movies:
            message = await update.message.reply_photo(
                photo=movie["poster"],
                caption=f"⏳ *Upcoming Movie (Preview - 10s)*\n🎬 {movie['name']}",
                parse_mode="Markdown"
            )
            await asyncio.sleep(10)  # ✅ 10-second delay
            await message.delete()  # ✅ Delete message after 10s

        # ✅ Save movies to database after 10s
        movies.extend(added_movies)
        save_movies(movies)

        # ✅ Confirm to Admin that movies are saved
        await update.message.reply_text(f"✅ *Movies Added to Database:*\n🎬 " + "\n🎬 ".join([m['name'] for m in added_movies]), parse_mode="Markdown")

    else:
        await update.message.reply_text("⚠️ *Format:* `/add_movies`\nMovie1 | Poster_URL1 | Link1\nMovie2 | Poster_URL2 | Link2", parse_mode="Markdown")
        
# ✅ Delete Movie (Admin Only)
async def delete_movie(update: Update, context):
    """Admin ko movies delete karne ki permission dega."""
    user_id = update.message.from_user.id
    if user_id not in ADMIN_ID:
        await update.message.reply_text("🚫 Aapke paas permission nahi hai!", parse_mode="Markdown")
        return

    try:
        movie_name = " ".join(context.args)
        movies = load_movies()
        new_movies = [m for m in movies if m["name"].lower() != movie_name.lower()]

        if len(movies) == len(new_movies):
            await update.message.reply_text(f"❌ *Movie '{movie_name}' nahi mili!*", parse_mode="Markdown")
            return

        save_movies(new_movies)
        await update.message.reply_text(f"✅ *Movie deleted:* {movie_name}", parse_mode="Markdown")
    except:
        await update.message.reply_text("⚠️ *Format:* `/delete_movie MovieName`", parse_mode="Markdown")

# ✅ Show Movie List
async def show_movie_names(update: Update, context):
    """Movies ki list show kare."""
    movies = load_movies()
    if not movies:
        await update.callback_query.message.reply_text("❌ Koi movies available nahi hain!", parse_mode="Markdown")
        return

    buttons = [[InlineKeyboardButton(m["name"], callback_data=f"movie_{m['name']}")] for m in movies]
    reply_markup = InlineKeyboardMarkup(buttons)

    await update.callback_query.message.reply_text("🎬 *Movie List:*", reply_markup=reply_markup, parse_mode="Markdown")

# ✅ Show Movie Details
async def show_movie_details(update: Update, context):
    """Movie ke details aur watch link show kare."""
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

# ✅ Search Movie Feature
async def search_movie(update: Update, context):
    """Movie search karne ki facility dega."""
    query = " ".join(context.args).lower()
    movies = load_movies()
    results = [m for m in movies if query in m["name"].lower()]

    if results:
        buttons = [[InlineKeyboardButton(m["name"], callback_data=f"movie_{m['name']}")] for m in results]
        reply_markup = InlineKeyboardMarkup(buttons)

        await update.message.reply_text("🔎 *Search Results:*", reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ *Movie nahi mili!*", parse_mode="Markdown")

# ✅ Latest Movies
async def latest_movies(update: Update, context):
    """Latest 6 movies show karega."""
    movies = load_movies()
    if not movies:
        await update.callback_query.message.reply_text("❌ Koi latest movie available nahi hain!", parse_mode="Markdown")
        return

    latest_movies = movies[-6:]  
    buttons = [[InlineKeyboardButton(m["name"], callback_data=f"movie_{m['name']}")] for m in latest_movies]
    reply_markup = InlineKeyboardMarkup(buttons)

    await update.callback_query.message.reply_text("🔥 *Latest Movies:*", reply_markup=reply_markup, parse_mode="Markdown")

# ✅ Button Click Handling
async def button_click(update: Update, context):
    """Inline buttons ka response handle karega."""
    query = update.callback_query
    await query.answer()

    if query.data == "movie_list":
        await show_movie_names(update, context)
    elif query.data == "latest_movies":
        await latest_movies(update, context)
    elif query.data.startswith("movie_"):
        await show_movie_details(update, context)
    elif query.data == "search":
        await query.message.reply_text("🔎 *Search a movie using:* `/search MovieName`", parse_mode="Markdown")
    elif query.data == "reminder":
        await query.message.reply_text("🔔 Feature Coming Soon!", parse_mode="Markdown")
    elif query.data == "help":
        await query.message.reply_text("ℹ️ *Commands:*\n/search MovieName\n/add_movies\n/delete_movie Name", parse_mode="Markdown")

# ✅ Main Function
def main():
    """Bot start karega aur handlers add karega."""
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add_movies", add_movies))
    app.add_handler(CommandHandler("delete_movie", delete_movie))
    app.add_handler(CommandHandler("search", search_movie))
    app.add_handler(CallbackQueryHandler(button_click))

    logging.info("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()