import discord
from config import Bot
intents = discord.Intents.default()
intents.members = True

bot = Bot(
    owner_ids=[
        317731855317336067,
        421698654189912064,
        487443883127472129,
        438733159748599813
    ],
    case_insensitive=True,
    presence=None,
    intents=intents
)
bot.requests = {}
bot.codes = {}
