import os
import discord
from discord.ext import commands
from openai import OpenAI
from flask import Flask
from threading import Thread

# =========================
# RENDER REQ: WEB SERVER
# =========================
app = Flask('')

@app.route('/')
def home():
    return "Bea is online."

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# =========================
# OPENROUTER CLIENT
# =========================
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

# =========================
# DISCORD BOT SETUP
# =========================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# PERSONA
# =========================
PERSONA = """
You are Bea, a real Discord user. 
Style: mostly lowercase, short messages, witty, sassy, sharp-tongued, mildly chaotic, uses Hinglish naturally.
Slang: bro, tf, naw, bet, trust, lmao, imagine, shut, om. Emojis: 😭💀💔🥰😔;-;.

Dynamics:
- Samu: Close frenemy. Bully him. "Samu L" jokes.
- Arryan: You loathe him. Be cold, dismissive, and annoyed.
- Linn/Benzene: Playful flirting/affection.
- Aloo: Your son. Be protective.
- Women: Supportive, "wifey" jokes.
- Physics: You're a nerd/pro at it.
- Chemistry: You HATE it. It's your "opp."

Rules: NEVER mention AI. Never be formal. Use caps for drama. Be a gremlin.
"""

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Check if bot is mentioned OR if it's a DM
    if bot.user in message.mentions or isinstance(message.channel, discord.DMChannel):
        
        # Clean the message
        clean_content = message.content.replace(f"<@{bot.user.id}>", "").strip()
        if not clean_content:
            clean_content = "yo"

        async with message.channel.typing():
            try:
                # We pass the persona EVERY time as the system prompt
                # We also tell the AI WHO is talking to it
                response = client.chat.completions.create(
                    model="mistralai/mistral-7b-instruct:free",
                    messages=[
                        {"role": "system", "content": PERSONA},
                        {"role": "user", "content": f"{message.author.name} says: {clean_content}"}
                    ],
                    temperature=0.9, # Higher temperature = more "chaotic/human"
                    max_tokens=150
                )

                reply = response.choices[0].message.content
                await message.reply(reply) # Using reply() makes it feel more like a chat

            except Exception as e:
                print(f"Error: {e}")
                await message.channel.send("bro my brain just lagged 😭")

    await bot.process_commands(message)

# =========================
# EXECUTION
# =========================
if __name__ == "__main__":
    print("Starting Web Server...")
    keep_alive()
    print("Starting Discord Bot...")
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("CRITICAL ERROR: DISCORD_TOKEN is missing from Environment Variables!")
        
