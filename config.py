import os
import json
import enum
import time
import discord
from discord.ext import commands


class Stage(enum.Enum):
    PRODUCTION = enum.auto()
    BETA = enum.auto()
    DEV = enum.auto()


class Config:
    def __init__(self, config_file):
        with open(config_file) as config:
            self.config = json.load(config)
        try:
            self.stage = Stage[(os.environ.get("PRODUCTION", "DEV")).upper()]
        except KeyError:
            self.stage = Stage.DEV
        # self.stage = Stage.PRODUCTION

    def __getattr__(self, item):
        return self.config.get(f"{item}-{self.stage.name.lower()}", self.config[item])


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
        super().__init__(command_prefix=commands.when_mentioned_or(*Config("config.json").prefixes), help_command=None, **kwargs)

        self.errors = 0
        x = 0
        m = len(Config("config.json").cogs)
        try:
            _, th = os.popen('stty size', 'r').read().split()
            width = int(th)
        except ValueError:
            width = 50
        failed = []
        from cogs.consts import Colours
        for cog in Config("config.json").cogs:
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
        from cogs.consts import Colours
        await self.change_presence(
            activity=discord.Streaming(
                name="applications | /help",
                url="https://www.twitch.tv/clicksminuteper"
            )
        )
        print(f"{Colours.Cyan}[S] {Colours.CyanDark}Logged on as {self.user} [ID: {self.user.id}]{Colours.c}")


config = Config("config.json")
os.environ["GIT_SSH_COMMAND"] = "ssh -i sshkey -o IdentitiesOnly=yes"
