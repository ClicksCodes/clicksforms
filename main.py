import time
import discord
import time
import os
from config import config
from discord.ext import commands, ipc
from cogs.consts import Colours


class Context(commands.Context):
    async def delete(self):
        if isinstance(self.channel, discord.channel.DMChannel):
            return
        if not self.channel.permissions_for(self.me).manage_messages:
            return
        await self.message.delete()

    async def remove_reaction(self, *args, **kwargs):
        if isinstance(self.channel, discord.channel.DMChannel):
            return
        if not self.channel.permissions_for(self.me).manage_reactions:
            return
        await self.remove_reaction(*args, **kwargs)

    async def reply(self, *args, **kwargs):
        kwargs["mention_author"] = False
        await self.message.reply(*args, **kwargs)


class Bot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(command_prefix=commands.when_mentioned_or(*config.prefixes), help_command=None, **kwargs)

        self.errors = 0
        self.ipc = ipc.Server(self, secret_key=config.ipcToken)
        x = 0
        m = len(config.cogs)
        try:
            _, th = os.popen('stty size', 'r').read().split()
            width = int(th)
        except ValueError:
            width = 50
        failed = []
        for cog in config.cogs:
            x += 1
            try:
                start = f"{Colours.YellowDark}[S] {Colours.Yellow}Loading cog {cog}"
                end = f"{Colours.Yellow}[{Colours.Red}{'='*(len(failed))}{Colours.Green}{'='*(x-len(failed)-1)}>{' '*(m-x)}{Colours.Yellow}] " + \
                    f"[{' '*(len(str(m))-len(str(x)))}{x}/{m}]"
                print(f"{start}{' '*(width-len(start)-len(end)+(len(Colours.Yellow*4)))}{end}", end="\r")
                self.load_extension(cog)
                start = f"{Colours.GreenDark}[S] {Colours.Green}Loaded cog {cog}"
                end = f"[{' '*(len(str(m))-len(str(x)))}{x}/{m}]"
                print(f"{start}{' '*(width-len(start)-len(end))}{end}")
            except Exception as exc:
                failed.append(exc)
                start = f"{Colours.RedDark}[S] {Colours.Red}Failed to load cog {cog}"
                end = f"[{' '*(len(str(m))-len(str(x)))}{x}/{m}]"
                print(f"{start}{' '*(width-len(start)-len(end))}{end}")
        x = 0
        for error in failed:
            x += 1
            print(f"{Colours.RedDark}[{x}/{len(failed)}] {Colours.Red}{error.__class__.__name__}: {Colours.RedDark}{error}{Colours.c}")
        lc = (len(failed), m)
        print(f"{Colours.Cyan}[S] {Colours.CyanDark}Starting with ({lc[1]-lc[0]}/{lc[1]}) cogs loaded")

    async def get_context(self, message, *, cls=Context):
        return await super().get_context(message, cls=cls)

    async def on_ready(self):
        await self.change_presence(
            activity=discord.Streaming(
                name="applications | /help",
                url="https://www.twitch.tv/clicksminuteper"
            )
        )
        print(f"{Colours.Cyan}[S] {Colours.CyanDark}Logged on as {self.user} [ID: {self.user.id}]{Colours.c}")


start = time.time()
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
bot.runningPing = False
bot.requests = {}

print(f"{Colours.Cyan}[S] {Colours.CyanDark}Started in {time.time() - start}s")
bot.run(config.token)
print(f"{Colours.Cyan}[S] {Colours.CyanDark}Bot stopped after {time.time() - start}s")
