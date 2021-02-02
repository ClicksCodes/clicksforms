import config
import time
import discord
import time
from discord.ext import commands
from cogs.consts import C


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
        super().__init__(command_prefix=commands.when_mentioned_or(">"), help_command=None, **kwargs)

        x = 0
        for cog in config.cogs:
            x += 1
            try:
                print(f"{C.Cyan}[S] {C.CyanDark}Loading cog {x}/{len(config.cogs)} ({cog})", end="\r")
                self.load_extension(cog)
                print(f"{C.Green}[S] {C.GreenDark}Loaded cog {x}/{len(config.cogs)} ({cog}).")
            except Exception as e:
                print(f"{C.RedDark}[E] {C.Red}Failed cog {x}/{len(config.cogs)} ({cog}) > {e.__class__.__name__}: {e}{C.c}")

    async def get_context(self, message, *, cls=Context):
        return await super().get_context(message, cls=cls)

    async def on_ready(self):
        await self.change_presence(
            activity=discord.Streaming(
                name="applications",
                url="https://www.twitch.tv/clicksminuteper"
            )
        )
        print(f"{C.Cyan}[S] {C.CyanDark}Logged on as {self.user} [ID: {self.user.id}]{C.c}")


print(f"{C.Cyan}[S] {C.CyanDark}Launching - Please wait")

start = time.time()
bot = Bot(
    owner_ids=[
        317731855317336067,
        421698654189912064,
        487443883127472129,
        438733159748599813
    ],
    case_insensitive=True,
    presence=None,
    intents=discord.Intents.all()
)
bot.runningPing = False

print(f"{C.Cyan}[S] {C.CyanDark}Started in {time.time() - start}s")
bot.run(config.token)
print(f"{C.Cyan}[S] {C.CyanDark}Bot stopped after {time.time() - start}s")
