import asyncio
import time
from discord.ext import commands

from cogs.consts import *


class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        m = await ctx.send(embed=loadingEmbed)
        time = m.created_at - ctx.message.created_at
        await m.edit(content=None, embed=discord.Embed(
            title=f"Ping",
            description=f"Latency is: `{int(time.microseconds / 1000)}ms`",
            color=Colours.blue)
        )

    @commands.command()
    async def help(self, ctx):
        pages = [
            discord.Embed(
                title="ClicksForms: Commands",
                description=f"`{ctx.prefix}help  ` | Shows this help message\n"
                            f"`{ctx.prefix}ping  ` | Shows the bots latency\n"
                            f"`{ctx.prefix}create` | Opens the form creator\n"
                            f"`{ctx.prefix}apply ` | Lets you apply to a servers form",
                color=Colours.blue
            ),
            discord.Embed(
                title="ClicksForms: Question types",
                description=f"{self.bot.get_emoji(Emojis.types.text)} Text - A single message response\n"
                            f"{self.bot.get_emoji(Emojis.types.number)} Number - Any number, decimals allowed\n"
                            f"{self.bot.get_emoji(Emojis.types.multichoice)} Multiple choice - Select one from a list of reactions\n"
                            f"{self.bot.get_emoji(Emojis.types.tickbox)} Select all reactions that apply, then click next\n"
                            f"{self.bot.get_emoji(Emojis.types.fileupload)} File upload - Upload any file\n"
                            f"{self.bot.get_emoji(Emojis.types.date)} Date - Use the calendar picker to select an exact date\n"
                            f"{self.bot.get_emoji(Emojis.types.time)} Time - Any valid time, inclusing using 'AM' and 'PM'\n\n"
                            f"{self.bot.get_emoji(Emojis.types.special_section)} Section header - A title for the next section\n"
                            f"{self.bot.get_emoji(Emojis.types.special_text)} Text - A piece of text to give information\n"
                            f"{self.bot.get_emoji(Emojis.types.special_image)} Image - An image shown before the next question\n"
                            f"{self.bot.get_emoji(Emojis.types.special_link)} Link - A link which can be clicked",
                color=Colours.red
            ),
            discord.Embed(
                title="ClicksForms: Question properties",
                description=f"{self.bot.get_emoji(Emojis.features.title)} Title - The title of the next question\n"
                            f"{self.bot.get_emoji(Emojis.features.description)} Description - The text under the title, giving more information\n"
                            f"{self.bot.get_emoji(Emojis.features.colour)} Colour - The colour of the side of the message the question is on\n"
                            f"{self.bot.get_emoji(Emojis.features.required)} Required - If the question is skipable or not",
                color=Colours.green
            ),
            discord.Embed(
                title="ClicksForms: Form properties",
                description=f"{self.bot.get_emoji(Emojis.features.title)} Title - The title of the form\n"
                            f"{self.bot.get_emoji(Emojis.features.description)} Description - The description of the form\n"
                            f"{self.bot.get_emoji(Emojis.roles.roles)} Roles - The roles given, removed, required, or dislalowed\n"
                            f"{self.bot.get_emoji(Emojis.channels.channelwl)} Channels - The channel(s) you can complete the form in\n"
                            f"{self.bot.get_emoji(Emojis.features.nanon)} Show applicant - If you can see the person who applied",
                color=Colours.green
            )
        ]
        page = 0
        m = await ctx.send(embed=pages[page])
        for r in [Emojis.left, Emojis.cross, Emojis.right]:
            await m.add_reaction(self.bot.get_emoji(r))
        while True:
            try:
                response = await self.bot.wait_for(
                    'reaction_add',
                    timeout=300,
                    check=lambda emoji, user: (
                        emoji.message.id == m.id
                        and user.id == ctx.author.id
                        and (emoji.emoji.name in ["Left", "Right", "Cross"])
                    )
                )
            except asyncio.TimeoutError:
                await m.clear_reactions()
                break
            await m.remove_reaction(response[0].emoji, ctx.author)
            if response[0].emoji.name == "Right":
                page += 1
            elif response[0].emoji.name == "Left":
                page -= 1
            else:
                await m.clear_reactions()
                break

            page = max(0, min(page, len(pages)-1))
            await m.edit(embed=pages[page])


def setup(bot):
    bot.add_cog(Core(bot))
