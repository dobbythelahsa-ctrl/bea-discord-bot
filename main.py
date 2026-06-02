import os
import discord
from discord.ext import commands
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
