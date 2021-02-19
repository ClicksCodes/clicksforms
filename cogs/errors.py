import traceback
import asyncio
import discord
import random
from discord.ext import commands
from cogs.consts import *


class Errors(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, err):
        try:
            # Normal Green
            # Warning Yellow
            # Critical Red
            # Status Blue

            if isinstance(err, commands.errors.NoPrivateMessage):
                return print(f"{C.GreenDark}[N] {C.Green}{str(err)}{C.c}")
            elif isinstance(err, commands.errors.BotMissingPermissions):
                return print(f"{C.GreenDark}[N] {C.Green}{str(err)}{C.c}")
            elif isinstance(err, commands.errors.CommandNotFound):
                return print(f"{C.GreenDark}[N] {C.Green}{str(err)}{C.c}")
            elif isinstance(err, asyncio.TimeoutError):
                return print(f"{C.GreenDark}[N] {C.Green}{str(err)}{C.c}")
            elif isinstance(err, commands.errors.NotOwner):
                return print(f"{C.GreenDark}[N] {C.Green}{str(err)}{C.c}")
            elif isinstance(err, commands.errors.TooManyArguments):
                return print(f"{C.GreenDark}[N] {C.Green}{str(err)}{C.c}")
            elif isinstance(err, commands.errors.MissingPermissions):
                return await ctx.send(embed=discord.Embed(
                    title=f"Missing permissions",
                    description=str(err),
                    color=colours["r"]
                ))
            else:
                code = "".join([random.choice("1234567890ABCDEF") for _ in range(0, 5)])
                tb = "".join(traceback.format_exception(type(err), err, err.__traceback__))
                print(f"{C.RedDark}[C] {C.Red}FATAL:\n{tb}{C.c}")
                tb = "```" + tb + "```"
                await self.bot.get_channel(812335313174397039).send(embed=discord.Embed(
                    title=f"Error #{code}",
                    description=tb,
                    color=Colours.red
                ))
                return await ctx.send(embed=discord.Embed(
                    title="Oops - Thats an error",
                    description=f"You aren't supposed to see this. "
                                f"If you want, you can give us more information by giving us the code `{code}` [here](https://discord.gg/bPaNnxe)",
                    color=Colours.red
                ))

        except Exception as e:
            print(e)

    @commands.command()
    @commands.is_owner()
    async def error(self, _):
        return f"{notexistslol}"


def setup(bot):
    bot.add_cog(Errors(bot))
