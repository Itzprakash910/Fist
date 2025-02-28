from telegram import Update, InlineKeyboardButton,  InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import requests

# 🔹 API KEYS
BOT_TOKEN = "7880903198:AAGR2FEzVjDO6BP79_TzCXk0PJzZfI1owhU" 
WEATHER_API_KEY = "7gtadAg0PNIUvsz8sFR2qQ1CwKzRSAkj"  # Tomorrow.io API Key

# 🔹 Function to Get Current Weather (Tomorrow.io API)
def get_weather(city):
    url = f"https://api.tomorrow.io/v4/weather/realtime?location={city}&apikey={WEATHER_API_KEY}"
    response = requests.get(url).json()

    if "data" in response:
        temp = response["data"]["values"]["temperature"]
        humidity = response["data"]["values"]["humidity"]
        weather_code = response["data"]["values"]["weatherCode"]

        # Weather Condition Mapping
        weather_conditions = {
            1000: "Clear Sky ☀️",
            1100: "Mostly Clear 🌤️",
            1101: "Partly Cloudy ⛅",
            1102: "Mostly Cloudy 🌥️",
            2000: "Fog 🌫️",
            2100: "Light Fog 🌫️",
            4000: "Drizzle 🌦️",
            4001: "Rain 🌧️",
            4200: "Light Rain ☔",
            4201: "Heavy Rain ⛈️",
            5000: "Snow ❄️",
            5100: "Light Snow 🌨️",
            6000: "Freezing Drizzle ❄️🌧️",
            6200: "Light Freezing Rain 🌧️❄️",
            7102: "Light Ice Pellets 🌨️",
            8000: "Thunderstorm ⚡",
        }
        weather_desc = weather_conditions.get(weather_code, "Unknown Weather")

        return (
            f"🌍  • {city.upper()} Weather Report • \n"
            f"🌡 • Temperature: • {temp}°C\n"
            f"💧 • Humidity: • {humidity}%\n"
            f"🌤 • Condition: •  {weather_desc}\n\n"
            f"🔔 Stay safe and have a great day! 😊"
        )
    return "❌ City not found!"

# 🔹 Function to Get 7-Day Forecast
def get_forecast(city):
    url = f"https://api.tomorrow.io/v4/weather/forecast/daily?location={city}&apikey={WEATHER_API_KEY}"
    response = requests.get(url).json()

    if "timelines" in response:
        forecast_text = f"📍  • {city.upper()} - 7-Day Forecast 🌦 • \n"
        for day in response["timelines"]["daily"]:
            date = day["time"].split("T")[0]
            temp_min = day["values"]["temperatureMin"]
            temp_max = day["values"]["temperatureMax"]
            weather_code = day["values"]["weatherCodeMax"]
            weather_desc = get_weather(city).split("\n")[3].split("**")[1]  # Extract Condition

            forecast_text += f"📅 {date} - {temp_min}°C/{temp_max}°C, {weather_desc}\n"

        return forecast_text
    return "❌ City not found!"

# 🔹 Weather Alert Function
def get_alert(city):
    url = f"https://api.tomorrow.io/v4/weather/realtime?location={city}&apikey={WEATHER_API_KEY}"
    response = requests.get(url).json()

    if "data" in response:
        temp = response["data"]["values"]["temperature"]
        weather_code = response["data"]["values"]["weatherCode"]

        if weather_code in [4201, 5000, 8000]:
            return f"⚠️  • Weather Alert for {city.upper()}! • 🌧️🌪️\nHeavy Rain/Snow/Thunderstorm expected! Stay safe! 🙏"
        elif temp > 40:
            return f"🔥 • Heatwave Alert in {city.upper()}! • 🌡️\nStay hydrated & avoid going out in extreme heat! 🥵"
    return None

# 🔹 Command for Weather
async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = " ".join(context.args)
    if not city:
        await update.message.reply_text("❌ Please Provide A City Name ! Example: `/Weather Mumbai`")
    else:
        weather_report = get_weather(city)
        alert_message = get_alert(city)
        if alert_message:
            weather_report += f"\n\n{alert_message}"  # Add alert to weather report
        await update.message.reply_text(weather_report)

# 🔹 Command for 7-Day Forecast
async def forecast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = " ".join(context.args)
    if not city:
        await update.message.reply_text("❌ Please Provide A City Name! Example: `/Forecast Mumbai`")
    else:
        await update.message.reply_text(get_forecast(city))

# 🔹 Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🌆 Mumbai", callback_data="Mumbai"),
         InlineKeyboardButton("🏙 Delhi", callback_data="Delhi")],
        [InlineKeyboardButton("🌇 Kolkata", callback_data="Kolkata"),
         InlineKeyboardButton("🏔 Shimla", callback_data="Shimla")],
        [InlineKeyboardButton("🌎 Auto-Detect Location", callback_data="location")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🌤  • Welcome to WeatheryX! \n"
        "📌 Get real-time weather updates:\n"
        "📝 Use `/weather CityName` for current weather.\n"
        "🔮 Use `/forecast CityName` for a 7-day forecast.\n"
        "🔘 Click below to select a city:",
        reply_markup=reply_markup
    )

# 🔹 Button Click Handler
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    city = query.data

    if city == "location":
        await query.message.reply_text("📍 Please Share your Live Location For  Weather Updates.")
    else:
        weather_report = get_weather(city)
        alert_message = get_alert(city)
        if alert_message:
            weather_report += f"\n\n{alert_message}"
        await query.message.reply_text(weather_report)

# 🔹 Bot Setup
application = Application.builder().token(BOT_TOKEN).build()

# 🔹 Add Handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("weather", weather))
application.add_handler(CommandHandler("forecast", forecast))
application.add_handler(CallbackQueryHandler(button_click))

# 🔹 Start Bot
if __name__ == "__main__":
    print("✅ Bot is running...")
    application.run_polling()