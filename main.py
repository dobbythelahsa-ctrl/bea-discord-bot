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
# 4. RAGEBAIT COMMAND
# =========================
@bot.tree.command(name="ragebait", description="Make Bea drop a highly provocative hot take to start an argument")
async def ragebait_command(interaction: discord.Interaction):
    await interaction.response.defer()
    prompt = "Generate a highly controversial, mildly annoying, lowercase discord-style hot take about a random topic (like food, games, music, or anime) to intentionally farm reactions. Keep it short."
    
    try:
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {"role": "system", "content": PERSONA},
                {"role": "user", "content": prompt}
            ],
            temperature=0.95
        )
        await interaction.followup.send(response.choices[0].message.content)
    except Exception as e:
        print(f"❌ Error: {e}")
        await interaction.followup.send("naw my brain is fried, no hot takes today")

# =========================
# 5. SHIP COMMAND
# =========================
@bot.tree.command(name="ship", description="Have Bea judge the compatibility of two users")
@app_commands.describe(user1="First person", user2="Second person")
async def ship_command(interaction: discord.Interaction, user1: discord.User, user2: discord.User):
    await interaction.response.defer()
    prompt = f"Judge the compatibility or friendship vibe between {user1.name} and {user2.name}. Give a dynamic percentage choice and a short, sassy, chaotic review of their pairing based on your friend rules."
    
    try:
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {"role": "system", "content": PERSONA},
                {"role": "user", "content": prompt}
            ],
            temperature=0.85
        )
        await interaction.followup.send(response.choices[0].message.content)
    except Exception as e:
        print(f"❌ Error: {e}")
        await interaction.followup.send("bro i crashed 😭")

# =========================
# 6. DESPAIR COMMAND
# =========================
@bot.tree.command(name="despair", description="Trigger a dramatic Bea meltdown about Chemistry")
async def despair_command(interaction: discord.Interaction):
    await interaction.response.defer()
    prompt = "Give a dramatic, short, lowercase-but-with-caps-for-drama existential crisis rant about how much you hate chemistry and why it is your absolute opp. Mention suffering."
    
    try:
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {"role": "system", "content": PERSONA},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9
        )
        await interaction.followup.send(response.choices[0].message.content)
    except Exception as e:
        print(f"❌ Error: {e}")
        await interaction.followup.send("chem has completely destroyed me, cannot reply")

# =========================
# 7. SELF HYPE COMMAND
# =========================
@bot.tree.command(name="selfhype", description="Make Bea talk about how peak she is")
async def selfhype_command(interaction: discord.Interaction):
    await interaction.response.defer()
    prompt = "Write a short, highly confident, arrogant-but-funny self-hype message about how amazing you are, your face card, or why you are peak. Keep it casual and text-style."
    
    try:
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {"role": "system", "content": PERSONA},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9
        )
        await interaction.followup.send(response.choices[0].message.content)
    except Exception as e:
        print(f"❌ Error: {e}")
        await interaction.followup.send("i'm too peak to even respond right now honestly")

# =========================
# 8. CHAOTIC 8BALL COMMAND
# =========================
@bot.tree.command(name="8ball", description="Ask Bea a yes or no question for some sassy advice")
@app_commands.describe(question="What do you want to ask the oracle?")
async def eightball_command(interaction: discord.Interaction, question: str):
    await interaction.response.defer()
    prompt = f"Someone asked you this question: '{question}'. Give a short, sassy, lowercase yes/no/maybe style response as a chaotic discord user. Be opinionated."
    
    try:
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {"role": "system", "content": PERSONA},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9
        )
        await interaction.followup.send(f"🔮 **Question:** {question}\n**Bea:** {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ Error: {e}")
        await interaction.followup.send("my third eye is lagging bro, ask later")

# =========================
# 9. MOCK COMMAND
# =========================
@bot.tree.command(name="mock", description="Make Bea repeat text in mocking alternating caps")
@app_commands.describe(text="What text do you want to mock?")
async def mock_command(interaction: discord.Interaction, text: str):
    # This edits the text directly into mOcKiNg CaPs without an API call (saves speed & tokens!)
    mocked_text = "".join([char.upper() if i % 2 == 0 else char.lower() for i, char in enumerate(text)])
    await interaction.response.send_message(f"\"{mocked_text}\" 💀 imagine saying that tf")

# =========================
# 10. MOOD CHECK COMMAND
# =========================
@bot.tree.command(name="mood", description="Check Bea's current mood levels")
async def mood_command(interaction: discord.Interaction):
    await interaction.response.defer()
    import random
    mood_percentage = random.randint(0, 100)
    
    prompt = f"Your current mood level is at {mood_percentage}%. Explain why you feel this way in one short, lowercase sentence referencing your persona traits (hating chem, bullying samu, loving physics, etc.)."
    
    try:
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {"role": "system", "content": PERSONA},
                {"role": "user", "content": prompt}
            ],
            temperature=0.85
        )
        await interaction.followup.send(f"📊 **Current Mood:** {mood_percentage}%\n**Bea:** {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ Error: {e}")
        await interaction.followup.send("mood is literally zero rn leave me alone")

# =========================
# 11. COINFLIP COMMAND
# =========================
@bot.tree.command(name="coinflip", description="Flip a coin against Bea")
@app_commands.describe(choice="Heads or Tails?")
@app_commands.choices(choice=[
    app_commands.Choice(name="Heads", value="Heads"),
    app_commands.Choice(name="Tails", value="Tails")
])
async def coinflip_command(interaction: discord.Interaction, choice: app_commands.Choice[str]):
    await interaction.response.defer()
    import random
    result = random.choice(["Heads", "Tails"])
    
    if choice.value == result:
        prompt = f"The user won a coinflip against you. They picked {choice.value} and it landed on {result}. Give a short, mildly annoyed but accepting response."
    else:
        prompt = f"The user lost a coinflip against you. They picked {choice.value} but it landed on {result}. Give a short, mocking, celebratory text response telling them they lost."

    try:
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {"role": "system", "content": PERSONA},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9
        )
        await interaction.followup.send(f"🪙 It landed on **{result}**!\n**Bea:** {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ Error: {e}")
        await interaction.followup.send("the coin fell into a drainage grate bro, try again")

# =========================
# 12. COMPLIMENT COMMAND
# =========================
@bot.tree.command(name="compliment", description="Force Bea to say something aggressive but nice to someone")
@app_commands.describe(user="Who are we being nice to?")
async def compliment_command(interaction: discord.Interaction, user: discord.User):
    await interaction.response.defer()
    prompt = f"Give an aggressive, tsundere-style, lowercase discord compliment to {user.name}. You hate being sweet but you are trying your best. Use emojis like 🥰 or 😔."
    
    try:
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {"role": "system", "content": PERSONA},
                {"role": "user", "content": prompt}
            ],
            temperature=0.85
        )
        await interaction.followup.send(f"{user.mention} {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ Error: {e}")
        await interaction.followup.send("naw i physically can't be nice right now")


# =========================
# 14. PHYSICS SLAP COMMAND
# =========================
@bot.tree.command(name="slap", description="Slap someone across the channel using raw kinetic physics")
@app_commands.describe(user="Who are we hitting?")
async def slap_command(interaction: discord.Interaction, user: discord.User):
    await interaction.response.defer()
    import random
    force = random.randint(500, 9999) # Random Newtons of force
    
    prompt = f"Describe slapping a user named {user.name} with exactly {force} Newtons of kinetic force. Mention a physics calculation, call them an idiot, and keep it lowercase and chaotic."
    
    try:
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {"role": "system", "content": PERSONA},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9
        )
        await interaction.followup.send(f"💥 **Impact Dynamic:** {force} N\n{user.mention} {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ Error: {e}")
        await interaction.followup.send("slap whiffed bro 😭")

# =========================
# 15. PRIVATE CONFIDE MODAL
# =========================
class ConfideModal(discord.ui.Modal, title="Private Vent Box 🤫"):
    vent_input = discord.ui.TextInput(
        label="What's bothering you? (Bea will keep it secret)",
        style=discord.TextStyle.paragraph,
        placeholder="Type your problems or rant here...",
        required=True,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_vent = self.vent_input.value
        prompt = f"The user is privately venting to you about this problem: '{user_vent}'. Give a supportive but chaotic, text-style, mildly rude but ultimately caring friend response."
        
        try:
            response = client.chat.completions.create(
                model="openrouter/free",
                messages=[
                    {"role": "system", "content": PERSONA},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.85
            )
            # This follows up completely ephemerally, making it an entirely stealthy advice session
            await interaction.followup.send(f"🤫 **Your Private Vent:** {user_vent}\n\n**Bea:** {response.choices[0].message.content}", ephemeral=True)
        except Exception as e:
            print(f"❌ Error: {e}")
            await interaction.followup.send("my inner therapist crashed bro", ephemeral=True)

@bot.tree.command(name="confide", description="Open a secure pop-up form to vent to Bea privately")
async def confide_command(interaction: discord.Interaction):
    # Triggers the native modal pop-up on the user's client UI frame
    await interaction.response.send_modal(ConfideModal())
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
