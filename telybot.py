import json
import logging
import asyncio
import nest_asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# ✅ Nest asyncio को enable करें (Pydroid3 के लिए जरूरी)
nest_asyncio.apply()

# ✅ Bot Token & Configurations
TOKEN = ["7348893495:AAEyPcdCEhgZPI8FmKNBlgAQjMVj-na0fhA"]  
MOVIE_DB = "movies.json"  
ADMIN_ID = [6221923358]  
CHANNEL_ID = ["@farzi_show", "@pahla_pyarshow", "@panchayat_webshow", "@movie_realised", "@new_realise_movie_2025"]

# ✅ Logging setup
logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)

# ✅ Check Channel Membership
async def check_group_membership(user_id, context):
    for group in CHANNEL_ID:
        try:
            member = await context.bot.get_chat_member(group, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except Exception as e:
            logging.warning(f"Error checking membership in {group}: {e}")
            return False
    return True

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

# ✅ Main Menu Function
async def return_to_main(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("🎬 Movie List", callback_data='movie_list')],
        [InlineKeyboardButton("🔥 Latest Movies", callback_data='latest_movies')],
        [InlineKeyboardButton("🔎 Search", callback_data='search')],
        [InlineKeyboardButton("ℹ️ Help", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=update.message.chat_id,
        text="🎥 *Welcome to Movie Bot!*\nMovies के latest updates यहाँ मिलेंगे।",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ✅ Start Command
async def start(update: Update, context):
    user_id = update.message.from_user.id

    # ✅ Check if user has joined all channels
    if not await check_group_membership(user_id, context):
        keyboard = [[InlineKeyboardButton("🔗 Join Group", url=f"https://t.me/{CHANNEL_ID[0].replace('@', '')}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("🚫 पहले ग्रुप जॉइन करें, फिर '/start' करें।", reply_markup=reply_markup)
        return

    await return_to_main(update, context)

# ✅ Show Movie List
async def show_movie_list(update: Update, context):
    query = update.callback_query
    movies = load_movies()

    if not movies:
        await query.message.edit_text("📭 No movie available")
        return

    buttons = [[InlineKeyboardButton(m["name"], callback_data=f"movie_{m['name']}")] for m in movies]
    reply_markup = InlineKeyboardMarkup(buttons)

    await query.message.edit_text("🎬 *Movie List:*", reply_markup=reply_markup, parse_mode="Markdown")

# ✅ Add Movies (Admin Only)
async def add_movies(update: Update, context):
    user_id = update.message.from_user.id
    if user_id not in ADMIN_ID:
        await update.message.reply_text("🚫 आपके पास permission नहीं है!")
        return

    text = update.message.text.split("\n")[1:]
    movies = load_movies()

    added_movies = []
    for line in text:
        name, poster, link = line.split(" | ")
        movies.append({"name": name.strip(), "poster": poster.strip(), "link": link.strip()})
        added_movies.append(name.strip())

    save_movies(movies)

    # ✅ Send Notification in Group
    notification = "\n".join([f"🎬 {m['name']} - [Watch Now]({m['link']})" for m in movies])
    for channel in CHANNEL_ID:
        await context.bot.send_message(chat_id=channel, text=notification, parse_mode="Markdown")

    # ✅ Movie Preview for 10 Seconds
    for movie in added_movies:
        msg = await update.message.reply_photo(photo=movie["poster"], caption=f"🎬 {movie['name']}")
        await asyncio.sleep(10)
        await msg.delete()

    await update.message.reply_text(f"✅ Movies Added:\n🎬 " + "\n🎬 ".join(added_movies))

# ✅ Delete Movie (Admin Only)
async def delete_movie(update: Update, context):
    user_id = update.message.from_user.id
    if user_id not in ADMIN_ID:
        await update.message.reply_text("🚫 Permission denied!")
        return

    movie_name = " ".join(context.args)
    movies = load_movies()
    new_movies = [m for m in movies if m["name"].lower() != movie_name.lower()]

    if len(movies) == len(new_movies):
        await update.message.reply_text("❌ Movie not found!")
        return

    save_movies(new_movies)
    await update.message.reply_text(f"✅ Movie Deleted: {movie_name}")

# ✅ Handle Button Click
async def button_click(update: Update, context):
    query = update.callback_query
    data = query.data

    if data == "movie_list":
        await show_movie_list(update, context)
    elif data == "latest_movies":
        await latest_movies(update, context)
    elif data == "search":
        await search_movie(update, context)

# ✅ Movie Details
async def show_movie_details(update: Update, context):
    query = update.callback_query
    movie_name = query.data.replace("movie_", "")
    movies = load_movies()

    movie = next((m for m in movies if m["name"].lower() == movie_name.lower()), None)
    if not movie:
        await query.message.edit_text("❌ Movie not found!")
        return

    await query.message.reply_photo(
        photo=movie["poster"],
        caption=f"🎬 *{movie['name']}*\n\n👉 [Watch Now]({movie['link']})",
        parse_mode="Markdown"
    )

# ✅ Run Bot
async def run_bot(token):
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add_movies", add_movies))
    app.add_handler(CommandHandler("delete_movie", delete_movie))
    app.add_handler(CallbackQueryHandler(button_click))
    await app.run_polling()

async def main():
    tasks = [asyncio.create_task(run_bot(token)) for token in TOKEN]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())