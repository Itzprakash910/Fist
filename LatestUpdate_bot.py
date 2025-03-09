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
ADMIN_ID = ["6221923358"]  
CHANNEL_ID = ["@farzi_show","@pahla_pyarshow","@panchayat_webshow","@movie_realised", "@new_realise_movie_2025"]  

# ✅ Logging setup
logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)

# ✅ Channel Join Check
async def check_group_membership(user_id, context):
    for group in CHANNEL_ID:
        try:
            member = await context.bot.get_chat_member(group, user_id)
            if member.status in ["member", "administrator", "creator"]:
                return True  
        except Exception as e:
            logging.warning(f"Error checking membership in {group}: {e}")
    return False

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

# ✅ Return to Main Menu
# ✅ Return to Main Menu (Fix for start command)
async def return_to_main(update: Update, context):
    """User को वापस Main Menu पर ले जाने के लिए 'Return' बटन काम करेगा।"""
    
    # अगर request callback query से आई है
    if update.callback_query:
        query = update.callback_query
        chat_id = query.message.chat_id
        message = query.message
    else:
        chat_id = update.message.chat_id
        message = update.message

    keyboard = [
        [InlineKeyboardButton("🎬 Movie List", callback_data='movie_list')],
        [InlineKeyboardButton("🔥 Latest Movies", callback_data='latest_movies')],
        [InlineKeyboardButton("🔎 Search", callback_data='search_movie')],
        [InlineKeyboardButton("🔔 Set Reminder", callback_data='reminder')],
        [InlineKeyboardButton("ℹ️ Help", callback_data='help')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=chat_id,
        text="🎥 *Welcome to Movie Bot!*\nMovies के latest updates यहाँ मिलेंगे।\n\nSelect an option:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
# ✅ Start Command
async def start(update: Update, context):
    user_id = update.message.from_user.id

    if not await check_group_membership(user_id, context):
        keyboard = [[InlineKeyboardButton("🔗 Join Group", url=f"https://t.me/{CHANNEL_ID[0].replace('@', '')}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("🚫 पहले ग्रुप जॉइन करें, फिर '/start' करें।", reply_markup=reply_markup)
        return

    await return_to_main(update, context)

# ✅ Show Movie List
async def show_movie_names(update: Update, context):
    query = update.callback_query
    movies = load_movies()

    if not movies:
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("📭 No movie available", reply_markup=reply_markup)
        return  

    buttons = [[InlineKeyboardButton(m["name"], callback_data=f"movie_{m['name']}")] for m in movies]
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_main")])
    buttons.append([InlineKeyboardButton("🔙 Return", callback_data="return_to_main")])
    
    reply_markup = InlineKeyboardMarkup(buttons)
    await query.message.edit_text("🎬 *Movie List:*", reply_markup=reply_markup, parse_mode="Markdown")
    
# ✅ Latest Movies Handler (Clickable)
async def latest_movies(update: Update, context):
    query = update.callback_query
    movies = load_movies()

    if not movies:
        await query.message.edit_text("📭 No latest movies available.")
        return  

    latest_movies = movies[-5:]  # ✅ सिर्फ़ 5 latest मूवी दिखाएँ
    movie_buttons = [[InlineKeyboardButton(f"🎬 {m['name']}", callback_data=f"movie_{m['name']}")] for m in latest_movies]

    movie_buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="return_to_main")])
    reply_markup = InlineKeyboardMarkup(movie_buttons)

    await query.message.edit_text("🔥 *Latest Movies:*\n\nClick a movie to view details.", reply_markup=reply_markup, parse_mode="Markdown")

# ✅ Search Movie Feature
# ✅ Movie Search Feature (Fixed)
async def search_movie(update: Update, context):
    """Movies को सर्च करने का ऑप्शन देगा।"""
    if update.message:  # ✅ अगर `/search` कमांड यूज़र ने टाइप की
        if not context.args:
            await update.message.reply_text("⚠️ *Usage:* `/search MovieName`", parse_mode="Markdown")
            return
        query = " ".join(context.args).lower()
    elif update.callback_query:  # ✅ अगर बटन के ज़रिए आया है
        query = update.callback_query.data.replace("search_movie", "").lower()
    else:
        return

    movies = load_movies()
    results = [m for m in movies if query in m["name"].lower()]

    if results:
        buttons = [[InlineKeyboardButton(m["name"], callback_data=f"movie_{m['name']}")] for m in results]
        buttons.append([InlineKeyboardButton("🔙 Return", callback_data="return_to_main")])
        reply_markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text("🔎 *Search Results:*", reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ *'{query}' से कोई मूवी नहीं मिली!*", parse_mode="Markdown")
# ✅ Help Handler
async def help(update: Update, context):
    help_text = "ℹ️ *Help Section*\n\n1️⃣ Use `/add_movies` to add movies.\n2️⃣ Use `/delete_movie` to remove movies.\n3️⃣ Click on buttons to navigate."
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.message.edit_text(help_text, reply_markup=reply_markup, parse_mode="Markdown")
    

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
        final_notification = "🎥 *New Movies Available! *\n\n" + "\n".join(
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
    user_id = update.message.from_user.id
    if user_id not in ADMIN_ID:
        await update.message.reply_text("🚫 Aapke paas permission nahi hai!", parse_mode="Markdown")
        return

    if not context.args:
        await update.message.reply_text("⚠️ *Format:* `/delete_movie MovieName`", parse_mode="Markdown")
        return

    movie_name = " ".join(context.args)
    movies = load_movies()
    new_movies = [m for m in movies if m["name"].lower() != movie_name.lower()]

    if len(movies) == len(new_movies):
        await update.message.reply_text(f"❌ *Movie '{movie_name}' nahi mili!*", parse_mode="Markdown")
        return

    save_movies(new_movies)
    await update.message.reply_text(f"✅ *Movie deleted:* {movie_name}", parse_mode="Markdown")

# ✅ Button Click Handling
async def button_click(update: Update, context):
    query = update.callback_query
    data = query.data

    if data == "movie_list":
        await show_movie_names(update, context)
    elif data == "latest_movies":
        await latest_movies(update, context)
    elif data == "search":
        await search_movie(update, context)
    elif data == "help":
        await help(update, context)
    elif data.startswith("movie_"):
        movie_name = data[6:]  # ✅ "movie_" हटाकर मूवी नाम प्राप्त करें
        await show_movie_details(update, context, movie_name)
    elif data == "return_to_main":
        await return_to_main(update, context)
    elif data == "back_to_main":
        await return_to_main(update, context)

# ✅ Movie Details Function
async def show_movie_details(update: Update, context, movie_name):
    query = update.callback_query
    movies = load_movies()

    movie = next((m for m in movies if m["name"].lower() == movie_name.lower()), None)

    if not movie:
        await query.message.edit_text(f"❌ *Movie not found:* {movie_name}", parse_mode="Markdown")
        return

    keyboard = [
        [InlineKeyboardButton("🎥 Watch Now", url=movie["link"])],
        [InlineKeyboardButton("⬅️ Back", callback_data="movie_list")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.edit_text(
        f"🎬 *{movie['name']}*\n\n🎭 *Watch Here:* [Click Here]({movie['link']})",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
# ✅ Run Bot
async def run_bot(token):
    app = Application.builder().token(token).build()
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add_movies", add_movies))
    app.add_handler(CommandHandler("delete_movie", delete_movie))
    logging.info(f"✅ Bot ({token[:10]}...) is running...")
    await app.run_polling(allowed_updates=Update.ALL_TYPES)

async def main():
    tasks = [asyncio.create_task(run_bot(token)) for token in TOKEN if token]
    if tasks:
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
