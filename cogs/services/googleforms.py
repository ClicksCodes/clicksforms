import discord
import datetime
import aiohttp
from discord.ext import commands

from cogs.consts import *
from cogs import handlers


class GoogleForms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.emojis = Emojis
        self.colours = Colours()
        self.handlers = handlers
        self.bot = bot
        self.db = handlers.Database()

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        if "type" not in interaction.data:
            return
        elif interaction.type.name == "application_command" and interaction.guild:
            if interaction.data["name"] == "download":
                if not interaction.guild.get_role(interaction.guild.default_role.id).permissions.external_emojis:
                    return await interaction.response.send_message(embed=discord.Embed(
                        title="Missing permissions",
                        description="Make sure `@everyone` has permission to use custom emojis to use this command"
                    ), ephemeral=True)
                await interaction.response.send_message(embed=loading_embed, ephemeral=True)
                m = await interaction.original_message()
                ctx = self.handlers.CustomCTX(self.bot, interaction.user, interaction.guild, interaction.channel, interaction=interaction, m=m)
                await self._fetch(ctx, m, interaction.data["options"][0]["value"])

    async def _fetch(self, ctx, m, code):
        if not ctx.channel.permissions_for(ctx.author).manage_guild or not ctx.channel.permissions_for(ctx.author).manage_roles:
            return await m.edit(embed=discord.Embed(
                title="Missing permissions",
                description="You need manage server and manage roles to run this command",
                color=self.colours.red
            ))
        code = code.upper().replace("I", "1").replace("O", "0")
        if code not in self.bot.codes:
            return await m.edit(embed=discord.Embed(
                title="Code not found",
                description=f"Could not find a form with the code `{code}` ",
                color=self.colours.red
            ).set_footer(text="To make it easier to read, some letters such as L and o are replaced with 1 and 0"))
        else:
            data = self.bot.codes[code]
            data["id"] = str(datetime.datetime.now().timestamp())
            data["active"] = True
            data["anonymous"] = False
            data["guild"] = ctx.guild.id
            data["created_by"] = ctx.author.id
            data["required_roles"] = []
            data["disallowed_roles"] = []
            data["given_roles"] = []
            data["removed_roles"] = []
            data["auto_accept"] = False
            v = self.handlers.createUI(ctx, [
                self.handlers.Button(label="Add", style="success", emoji=self.emojis().control.tick, cb="ad"),
                self.handlers.Button(label="Cancel", style="danger", emoji=self.emojis().control.cross, cb="ca")
            ])
            await m.edit(embed=discord.Embed(
                title="Downloaded form successfully",
                description=f"{len(data['questions'])} questions have been imported",
                color=self.colours.green
            ), view=v)
            await v.wait()
            if v.selected == "ca":
                return await m.edit(embed=discord.Embed(
                    title="Cancelled",
                    description="No changes were made",
                    color=self.colours.red
                ), view=None)
            elif v.selected == "ad":
                from config import config
                entry = await self.db.get(ctx.guild.id)
                newdata = entry.data
                for i, form in enumerate(newdata):
                    if form["id"] == data["id"]:
                        newdata[i] = data
                await entry.update(data=newdata)
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(f"{config.rsm}/clicksforms/import/googleforms", json={
                            "guild_id": ctx.guild.id,
                            "created_by": ctx.author.id,
                            "questions": len(data["questions"]),
                            "name": data["name"],
                            "auth": config.rsmToken
                        }) as _:
                            pass
                except aiohttp.ClientConnectorError:
                    pass
                return await m.edit(embed=discord.Embed(
                    title="Added",
                    description="Your form can now be accessed through `/apply`. If you would like to edit the form, run `/edit`",
                    color=self.colours.green
                ), view=None)

def setup(bot):
    bot.add_cog(GoogleForms(bot))
