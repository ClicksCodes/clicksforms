import discord
from discord.ext import commands

from cogs import consts


class Errors(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.emojis = consts.Emojis
        self.colours = consts.Colours()

    async def send_error(self, ctx, message):
        try:
            return await ctx.author.send(embed=discord.Embed(
                title=f"{self.emojis().control.cross} I don't have permission",
                description=message,
                colour=self.colours.red,
            ))
        except discord.Forbidden:
            pass
        try:
            return await ctx.message.add_reaction(self.emojis().control.cross)
        except discord.Forbidden:
            pass
        try:
            return await ctx.message.add_reaction("❌")
        except discord.Forbidden:
            pass

    async def _on_error(self, ctx, error):
        Colours = consts.Colours
        try:
            # Normal Green
            # Warning Yellow
            # Critical Red
            # Status Blue
            if not ctx.channel.permissions_for(ctx.me).send_messages:
                return await self.send_error(ctx, "I tried to send a message, but I didn't have permission to send it. Make sure I have `send_messages`")
            elif not ctx.channel.permissions_for(ctx.me).embed_links:
                if ctx.channel.permissions_for(ctx.me).read_message_history:
                    return await ctx.reply("I don't have permission to send an embed. Make sure I have `embed_links`")
                return await ctx.send("I don't have permission to send an embed. Make sure I have `embed_links` and `read_message_history`")
            elif not ctx.channel.permissions_for(ctx.me).external_emojis:
                return await ctx.send(ctx, "I tried to use a nitro emoji, but didn't have permission. Make sure I have `use_external_emojis`")
            elif not ctx.channel.permissions_for(ctx.me).add_reactions:
                return await ctx.send(ctx, "I tried to add a reaction, but didn't have permission. Make sure I have `add_reactions`")
            elif isinstance(error, commands.errors.CommandOnCooldown):
                return await ctx.send(embed=discord.Embed(
                    title="You're on cooldown",
                    description="Please try again in a few seconds",
                    color=self.colours.red
                ))
            elif isinstance(error, commands.errors.BotMissingPermissions) or isinstance(error, discord.ext.commands.errors.BotMissingPermissions):
                return await ctx.send(
                    embed=discord.Embed(
                        title=f"{self.emojis().control.cross} Missing permissions",
                        description=str(error),
                        colour=self.colours.red,
                    )
                )
            elif isinstance(error, commands.errors.MissingPermissions) and ctx:
                return await ctx.send(
                    embed=discord.Embed(
                        title=f"{self.emojis().control.cross} Missing permissions",
                        description=str(error),
                        colour=self.colours.red,
                    )
                )
            elif isinstance(error, discord.errors.HTTPException):
                return
            elif isinstance(error, asyncio.exceptions.TimeoutError):
                return
        except Exception as e:
            print(e)

    @commands.Cog.listener()
    async def on_error(self, error):
        await self._on_error(_, error)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        await self._on_error(ctx, error)

    #  pyright: reportUndefinedVariable=false
    @commands.command()
    @commands.is_owner()
    async def error(self, ctx):
        return f"{myhopesanddreams}"

    @commands.command()
    @commands.is_owner()
    async def raiseerror(self, ctx):
        raise ModuleNotFoundError("My hopes and dreams")


def setup(bot):
    bot.add_cog(Errors(bot))
