import time
import time
from config import config
from cogs.consts import Colours
from bot import bot

start = time.time()

print(f"{Colours.Cyan}[S] {Colours.CyanDark}Started in {time.time() - start}s")
bot.run(config.token)
print(f"{Colours.Cyan}[S] {Colours.CyanDark}Bot stopped after {time.time() - start}s")
