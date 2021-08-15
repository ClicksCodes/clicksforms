import discord
import validators
from discord.ext import commands

from cogs.consts import *
from cogs import handlers


class CustomCTX:
    def __init__(self, bot, author, guild, channel, message=None):
        self.bot = bot
        self.author = author
        self.guild = guild
        self.message = message
        self.channel = channel

    async def delete(self):
        if self.message:
            await self.message.delete()


class Responses(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.emojis = Emojis
        self.colours = Colours()
        self.handlers = handlers
        self.bot = bot
        self.db = handlers.Database()

    @commands.command()
    @commands.guild_only()
    async def responses(self, ctx):
        if not ctx.channel.permissions_for(ctx.author).manage_guild or not ctx.channel.permissions_for(ctx.author).manage_guild:
            return await ctx.send(embed=discord.Embed(
                title="Missing permissions",
                description="You need manage server and manage roles to run this command",
                color=self.colours.red
            ))
        if not ctx.channel.permissions_for(ctx.me).external_emojis:
            return await ctx.send(embed=discord.Embed(
                title="Missing permissions",
                description="Make sure `@everyone` has permission to use custom emojis to use this command",
                color=self.colours.red
            ))
        m = await ctx.send(embed=loading_embed)
        ctx = CustomCTX(self.bot, ctx.author, ctx.guild, ctx.channel, message=ctx.message)
        await self._responses(ctx, m, createdBy="message")

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        if interaction.type.name == "application_command" and interaction.guild:
            if interaction.data["name"] == "responses":
                if not interaction.guild.get_role(interaction.guild.default_role.id).permissions.external_emojis:
                    return await interaction.response.send_message(embed=discord.Embed(
                        title="Missing permissions",
                        description="Make sure `@everyone` has permission to use custom emojis to use this command"
                    ), ephemeral=True)
                await interaction.response.send_message(embed=loading_embed, ephemeral=True)
                m = await interaction.original_message()
                ctx = CustomCTX(self.bot, interaction.user, interaction.guild, interaction.channel)
                await self._responses(ctx, m, createdBy="interaction", interaction=interaction)

    async def _responses(self, ctx, m, createdBy, interaction=None):
        while True:
            entry = await self.db.get(ctx.guild.id)
            forms = entry.data
            responses = entry.responses
            o = []
            for form in forms:
                if form["id"] in responses:
                    o.append(discord.SelectOption(value=form["id"], label=form["name"], description=str(len(responses[form["id"]])) + " response" + ("s" if len(responses[form["id"]]) > 1 else "")))
                else:
                    o.append(discord.SelectOption(value=form["id"], label=form["name"], description="0 responses"))
            v = self.handlers.createUI(ctx, [
                self.handlers.Select(id="form", placeholder="Select a form", autoaccept=True, options=o),
                self.handlers.Button(cb="cl", label="Close", style="danger", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.cross)),
            ])
            await m.edit(embed=discord.Embed(
                title="Responses",
                description="Select a form to view responses for",
                color=self.colours.purple
            ), view=v)
            await v.wait()
            if v.selected is not None:
                break
            if "form" in v.dropdowns:
                if v.dropdowns["form"][0] not in responses:
                    v = self.handlers.createUI(ctx, [
                        self.handlers.Button(cb="ba", label="Back", style="danger", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.left))
                    ])
                    await m.edit(embed=discord.Embed(
                        title="Responses",
                        description="This form has no responses",
                        color=self.colours.red
                    ), view=v)
                    await v.wait()
                    continue
                responses = responses[v.dropdowns["form"][0]]
                form = None
                for f in forms:
                    if f["id"] == v.dropdowns["form"][0]:
                        form = f
                        break
                applicant = 0
                question = 0
                v = self.handlers.createUI(ctx, [
                    self.handlers.Button(cb="ba", label="Back", style="danger", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.left))
                ])
                if not len(form["questions"]):
                    await m.edit(embed=discord.Embed(
                        title="Responses",
                        description="This form has no questions",
                        color=self.colours.red
                    ), view=v)
                    await v.wait()
                    continue
                questions = [q for q in form["questions"] if q["question"]]
                o = []
                for i, q in enumerate(questions):
                    o.append(discord.SelectOption(value=str(i), label=q["title"], description=q["description"], emoji=self.bot.get_emoji(getattr(self.emojis(idOnly=True).question, q["type"]))))
                while True:
                    question = max(0, min(len(questions) - 1, question))
                    applicant = max(0, min(len(responses) - 1, applicant))
                    v = self.handlers.createUI(ctx, [
                        self.handlers.Button(cb="ba", style="danger", label="Back", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.left)),
                        self.handlers.Button(cb="pq", style="primary", label="Previous question", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.back),
                            disabled=(question == 0)),
                        self.handlers.Button(cb="nq", style="primary", label="Next question", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.forward),
                            disabled=(question == len(questions) - 1)),
                        self.handlers.Button(cb="pa", style="secondary", label="Previous response", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.left),
                            disabled=(applicant == 0)),
                        self.handlers.Button(cb="na", style="secondary", label="Next response", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.right),
                            disabled=(applicant == len(responses) - 1)),
                        self.handlers.Select(id="q", placeholder="Jump to question...", options=o, autoaccept=True)
                    ])
                    q = "*Response not found*"
                    i = questions[question]["id"]
                    t = questions[question]["type"]
                    for r in responses[applicant]["answers"]:
                        if r[0] == i:
                            q = f"> {r[1]}"
                            if r[1] is None:
                                q = "*Question skipped*"
                            elif t == "multichoice":
                                q = "\n".join([f"> {icons[int(n)]}" for n in r[1]])
                    await m.edit(embed=discord.Embed(
                        title="Responses",
                        description=f"**User:** {'Anonymous' if form['anonymous'] else self.bot.get_user(responses[applicant]['user']).mention}\n"
                                    f"**Question:** {questions[question]['title']}\n"
                                    f"**Description:**\n> {questions[question]['description']}\n\n"
                                    f"**Answer:**\n{q}",
                        color=self.colours.purple
                    ).set_footer(text=f"Question {question + 1} of {len(questions)} - Response {applicant + 1} of {len(responses)}"
                    ).set_thumbnail(url=("https://example.com" if isinstance(validators.url(q[2:]), validators.ValidationFailure) else q[2:])), view=v)
                    await v.wait()
                    if "q" in v.dropdowns:
                        question = int(v.dropdowns["q"][0])
                        continue
                    if v.selected is None:
                        break
                    if v.selected == "pa":
                        applicant -= 1
                    elif v.selected == "na":
                        applicant += 1
                    elif v.selected == "pq":
                        question -= 1
                    elif v.selected == "nq":
                        question += 1
                    elif v.selected == "ba":
                        break
        await m.delete()

def setup(bot):
    bot.add_cog(Responses(bot))
