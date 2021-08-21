import discord
from discord.ext import commands

from cogs.consts import *
from cogs import handlers


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.emojis = Emojis
        self.colours = Colours()
        self.handlers = handlers
        self.bot = bot

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        if "type" not in interaction.data:
            return
        elif interaction.type.name == "application_command" and interaction.guild:
            if interaction.data["name"] == "help":
                if not interaction.guild.get_role(interaction.guild.default_role.id).permissions.external_emojis:
                    return await interaction.response.send_message(embed=discord.Embed(
                        title="Missing permissions",
                        description="Make sure `@everyone` has permission to use custom emojis to use this command"
                    ), ephemeral=True)
                await interaction.response.send_message(embed=loading_embed, ephemeral=True)
                m = await interaction.original_message()
                ctx = self.handlers.CustomCTX(self.bot, interaction.user, interaction.guild, interaction.channel, interaction=interaction, m=m)
                await self._help(ctx, m)

    @commands.command()
    @commands.guild_only()
    async def help(self, ctx):
        if not ctx.channel.permissions_for(ctx.me).external_emojis:
            return await ctx.send(embed=discord.Embed(
                title="Missing permissions",
                description="Make sure I have permission to use custom emojis to use this command"
            ))
        m = await ctx.send(embed=loading_embed)
        ctx = self.handlers.CustomCTX(self.bot, ctx.author, ctx.guild, ctx.channel, message=ctx.message, m=m)
        await self._help(ctx, m)

    async def _help(self, ctx, m):
        await m.edit(embed=discord.Embed(
            title="ClicksForms",
            description=f"Prefix: `/`  (recommended)  |  `>` or {ctx.guild.me.mention} (not recommended) \n\n"
                        f"`/help` - Show this help message\n"
                        f"`/create` - Creates a new form\n"
                        f"`/manage` - Lets you edit, delete and create forms\n"
                        f"`/responses` - Lets you view and export responses\n"
                        f"`/accept` - Starts a form if you were asked to complete one\n\n"
                        f"`Apps > Ask to complete form` - Asks a user to complete a form\n"
                        f"*This is a new Discord feature, it may not be avaliable to you. Try right clicking a member to open the apps page.*\n\n"
                        f"[[Invite](https://discord.com/api/oauth2/authorize?client_id=805392054678192169&permissions=2416307200&scope=bot%20applications.commands)]"
                        f"[[Support](https://discord.gg/bPaNnxe)]",
            colour=self.colours.purple,
        ))


def setup(bot):
    bot.add_cog(Help(bot))
