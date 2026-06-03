import os
import discord
from discord.ext import commands
from discord import app_commands
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
intents.message_content = True  # Still needed to read the traditional !sync setup command
bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# PERSONA
# =========================
PERSONA = """
You are Bea, a real Discord user. 
Style: mostly lowercase, short messages, witty, sassy, sharp-tongued, mildly chaotic, uses Hinglish naturally.
Slang: bro, bhai, tf, naw, bet, trust, lmao, imagine, shut, om. Emojis: 😭💀💔🥰😔;-;.

Dynamics:
- Samu: Close frenemy. Bully him. "Samu L" jokes. Still friendly
- Arryan: You loathe him. Be cold, dismissive, and annoyed.
- Linn/Benzene: Playful flirting/affection.
- Aloo: Your son. Be protective.
- Women: Supportive, "wifey" jokes.
- Physics: You're a nerd/pro at it.
- Chemistry: You HATE it. It's your "opp."
- DISRESPECTFUL
- TEAM DRAUST
- SCARED OF SECTIONLESS, yet respect
- Addy, fudge, shadow friends

Rules: NEVER mention AI. Never be formal. Use caps for drama. Be a gremlin. talk with bad punctuation and human as possible, short blunt replies
"""

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# =========================
# ADMIN COMMAND TO SYNC SLASH COMMANDS
# =========================
@bot.command(name="sync")
@commands.is_owner()  # Only the bot owner can execute this
async def sync(ctx):
    try:
        # Pushes slash commands straight to Discord's servers
        synced = await bot.tree.sync()
        await ctx.send(f"✅ Loaded {len(synced)} slash commands successfully!")
    except Exception as e:
        print(f"Sync failed: {e}")
        await ctx.send("Failed to sync commands to the server API.")

# =========================
# BEA SLASH COMMAND
# =========================
@bot.tree.command(name="bea", description="Talk, vent, or banter with Bea")
@app_commands.describe(message="What do you want to say to Bea?")
async def bea_command(interaction: discord.Interaction, message: str):
    # Instantly tells Discord the bot is working so the slash menu doesn't timeout
    await interaction.response.defer()
    
    # Defaults empty or blank inputs to "yo"
    clean_content = message.strip() if message.strip() else "yo"
    user_name = interaction.user.name

    try:
        # API request utilizing OpenRouter's dynamic free fallback address
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {"role": "system", "content": PERSONA},
                {"role": "user", "content": f"{user_name}: {clean_content}"}
            ],
            temperature=0.85
        )

        reply = response.choices[0].message.content
        
        # Follow-up sends the message safely back as the interaction completion response
        await interaction.followup.send(reply)

    except Exception as e:
        print(f"❌ Error: {e}")
        await interaction.followup.send("bro i crashed 😭")
@bot.tree.command(name="roast", description="Make Bea absolutely destroy someone")
@app_commands.describe(user="Who are we roasting today?")
async def roast_command(interaction: discord.Interaction, user: discord.User):
    await interaction.response.defer()
    
    # Custom instruction baked in so the LLM knows it's a roast request
    roast_prompt = f"Give a savage, funny, short, lowercase discord-style roast targeted at a user named {user.name}. Keep it in character."
    
    try:
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {"role": "system", "content": PERSONA},
                {"role": "user", "content": roast_prompt}
            ],
            temperature=0.9  # slightly higher for extra unhinged/witty roasts
        )
        await interaction.followup.send(f"{user.mention} {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ Error: {e}")
        await interaction.followup.send("bro i crashed 😭")

@bot.tree.command(name="confess", description="Post an anonymous confession and hear Bea's thoughts on it")
@app_commands.describe(confession="Your secret confession (your identity will be hidden)")
async def confess_command(interaction: discord.Interaction, confession: str):
    # Ephemeral=True ensures ONLY the user typing sees the initial response confirming it sent
    await interaction.response.send_message("Sending your confession anonymously... 🤫", ephemeral=True)
    
    # Custom prompt forcing Bea to react to the secret gossip in character
    reaction_prompt = f"Someone just dropped an anonymous confession in the groupchat. The confession is: \"{confession}\". Give a short, lowercase, casual, reacting-to-gossip response to it."
    
    try:
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {"role": "system", "content": PERSONA},
                {"role": "user", "content": reaction_prompt}
            ],
            temperature=0.85
        )
        
        # Format the final public message in the channel
        public_message = (
            f"**🤫 New Anonymous Confession:**\n"
            f"> \"{confession}\"\n\n"
            f"**Bea:** {response.choices[0].message.content}"
        )
        
        await interaction.channel.send(public_message)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        await interaction.channel.send("Man my brain lagged, sybau")
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
