import discord
import validators
import io
import asyncio
import json
from discord.ext import commands

from cogs.consts import *
from cogs import handlers


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
        ctx = self.handlers.CustomCTX(self.bot, ctx.author, ctx.guild, ctx.channel, message=ctx.message, m=m)
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
                if not interaction.channel.permissions_for(interaction.user).manage_guild or \
                    not interaction.channel.permissions_for(interaction.user).manage_guild:
                    return await ctx.send(embed=discord.Embed(
                        title="Missing permissions",
                        description="You need manage server and manage roles to run this command",
                        color=self.colours.red
                    ))
                await interaction.response.send_message(embed=loading_embed, ephemeral=True)
                m = await interaction.original_message()
                ctx = self.handlers.CustomCTX(self.bot, interaction.user, interaction.guild, interaction.channel, interaction=interaction, m=m)
                await self._responses(ctx, m, createdBy="interaction", interaction=interaction)

    async def _responses(self, ctx, m, createdBy, interaction=None):
        while True:
            entry = await self.db.get(ctx.guild.id)
            forms = entry.data
            responses = entry.responses
            o = []
            for form in forms:
                if form["id"] in responses:
                    o.append(discord.SelectOption(
                        value=form["id"],
                        label=form["name"],
                        description=str(len(responses[form["id"]])) + " response" + ("s" if len(responses[form["id"]]) > 1 else "")
                    ))
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
                formid = v.dropdowns["form"][0]
                responses = responses[formid]
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
                if not len(responses):
                    await m.edit(embed=discord.Embed(
                        title="Responses",
                        description="This form has no responses",
                        color=self.colours.red
                    ), view=v)
                    await v.wait()
                    continue
                questions = [q for q in form["questions"] if ("-decoration" not in q["type"])]
                o = []
                for i, q in enumerate(questions):
                    o.append(
                        discord.SelectOption(value=str(i), label=q["title"], description=q["description"],
                                             emoji=self.bot.get_emoji(getattr(self.emojis(idOnly=True).question, q["type"]))))
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
                        self.handlers.Button(cb="ap", style="secondary", label="Approve", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.tick)),
                        self.handlers.Button(cb="dr", style="danger", label="Delete response", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.cross)),
                        self.handlers.Button(cb="ex", style="success", label="Export responses", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.tick)),
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
                    ).set_footer(
                        text=f"Question {question + 1} of {len(questions)} - Response {applicant + 1} of {len(responses)}"
                    ).set_thumbnail(
                        url=("https://example.com" if isinstance(validators.url(q[2:]), validators.ValidationFailure) else q[2:])
                    ), view=v)
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
                    elif v.selected == "ap":
                        for role in form["given_roles"]:
                            if role.id not in [r.id for r in ctx.author.roles]:
                                await ctx.guild.get_member(int(r[formid][applicant])).add_roles(role)
                        for role in form["removed_roles"]:
                            if role.id in [r.id for r in ctx.author.roles]:
                                await ctx.guild.get_member(int(r[formid][applicant])).remove_roles(role)
                    elif v.selected == "dr":
                        entry = await self.db.get(ctx.guild.id)
                        r = entry.responses
                        del r[formid][applicant]
                        await entry.update(responses=r)
                        responses = r[formid]
                        if applicant >= len(r):
                            applicant -= 1
                        if not len(r):
                            break
                    elif v.selected == "ex":
                        await self.export(ctx, m, questions, responses)
        await ctx.delete()

    async def export(self, ctx, m, questions, responses):
        v = self.handlers.createUI(ctx, [
            self.handlers.Select(id="format", placeholder="Choose a format", options=[
                discord.SelectOption(value="cs", label="CSV", description="Supports: Microsoft Excel, Google Sheets, LibreOffice Calc"),
                discord.SelectOption(value="md", label="Markdown", description="Supports: GitHub flavoured markdown, online viewers"),
                discord.SelectOption(value="ht", label="HTML", description="Supports: Microsoft Excel, Google Sheets, LibreOffice Calc"),
                discord.SelectOption(value="js", label="JSON", description="Supports: Programming languages")
            ], autoaccept=True),
            self.handlers.Button(cb="ba", style="danger", label="Back")
        ])
        await m.edit(embed=discord.Embed(
            title="Export",
            description="Choose a file format for exporting\nNew formats will be added over time",
            color=self.colours.purple
        ), view=v)
        await v.wait()
        if v.selected:
            return
        if "format" in v.dropdowns:
            f = v.dropdowns["format"][0]
            o = None
            if f == "cs":
                o = await self.exportCSV(questions, responses)
            elif f == "md":
                o = await self.exportMD(questions, responses)
            elif f == "ht":
                o = await self.exportHTML(questions, responses)
            elif f == "js":
                o = await self.exportJSON(questions, responses)
            if o:
                asyncio.create_task(self.showFile(ctx, m, o))

    async def showFile(self, ctx, m, f):
        v = self.handlers.createUI(ctx, [
            self.handlers.Button(cb="de", style="danger", label="Delete")
        ])
        n = await m.channel.send(file=discord.File(f[0], f"responses.{f[1]}"), view=v)
        await v.wait()
        await n.delete()

    def usableFormat(self, questions, responsedata):
        headers = ["User", "Time (Seconds)"]
        responses = []
        headers += [question["title"] for question in questions]
        for r in responsedata:
            user = ""
            if r["user"] is None:
                user = "Anonymous"
            else:
                user = self.bot.get_user(r["user"])
                if user is None:
                    user = "User not found"
                else:
                    user = user.name + "#" + user.discriminator
            response = [user, r["time"]]
            for question in questions:
                for q in r["answers"]:
                    if str(q[0]) == str(question["id"]):
                        if question["type"] == "multichoice":
                            response.append(", ".join([(question["options"]["options"][n][0]) for n in (q[1] if q[1] else [])]))
                        else:
                            response.append(q[1] or "Skipped")
            responses.append(response)
        return [headers] + [r for r in responses]

    async def exportCSV(self, questions, responsedata):
        out = self.usableFormat(questions, responsedata)

        def replace(r):
            return str(r).replace('"', '\\"')

        string = "\n".join([",".join([f'"{replace(answer)}"' for answer in r]) for r in out])
        buf = io.BytesIO(string.encode("utf-8"))
        buf.seek(0)
        return buf, "csv"

    async def exportMD(self, questions, responsedata):
        out = self.usableFormat(questions, responsedata)

        def replace(r):
            return str(r).replace('|', '\\|')

        string = ["|".join([f'{replace(answer)}' for answer in r]) for r in out]
        string = (string[0]) + "\n" + ("|".join(["-" for _ in range(len(questions) + 2)])) + "\n" + ("\n".join(string[1:]))
        buf = io.BytesIO(string.encode("utf-8"))
        buf.seek(0)
        return buf, "md"

    async def exportHTML(self, questions, responsedata):
        out = self.usableFormat(questions, responsedata)

        def replace(r):
            return str(r).replace('<', '&lt;').replace('>', '&gt;')

        string = [[f'{replace(answer)}' for answer in r] for r in out]
        headers = string[0]
        rows = string[1:]
        string = "<table><tr>"
        for h in headers:
            string += f"<th>{h}</th>"
        string += "</tr>"
        for r in responsedata:
            string += "<tr>"
            user = ""
            if r["user"] is None:
                user = "Anonymous"
            else:
                user = self.bot.get_user(r["user"])
                if user is None:
                    user = "User not found"
                else:
                    user = user.name + "#" + user.discriminator
            string += f"<td>{user}</td><td>{r['time']}</td>"
            for question in questions:
                for q in r["answers"]:
                    if question["id"] == q[0]:
                        if q[1] is None:
                            string += f"<td>Skipped</td>"
                        else:
                            if question["type"] == "multichoice":
                                string += f"<td>{', '.join([(question['options']['options'][n][0]) for n in (q[1] if q[1] else [])])}</td>"
                            else:
                                string += f"<td>{q[1] or 'Skipped'}</td>"
            string += "</tr>"
        string += "</table>"
        buf = io.BytesIO(string.encode("utf-8"))
        buf.seek(0)
        return buf, "html"

    async def exportJSON(self, questions, responsedata):
        string = []
        for r in responsedata:
            user = ""
            if r["user"] is None:
                user = "Anonymous"
            else:
                user = self.bot.get_user(r["user"])
                if user is None:
                    user = "User not found"
                else:
                    user = user.name + "#" + user.discriminator
            answer = []
            for question in questions:
                for q in r["answers"]:
                    if str(q[0]) == str(question["id"]):
                        if question["type"] == "multichoice":
                            answer.append({"name": question["title"], "answer": ", ".join(q[1])})
                        else:
                            answer.append({"name": question["title"], "answer": q[1] or "Skipped"})
            string.append({"User": user, "Time (Seconds)": r["time"], "answers": answer})
        string = json.dumps(string)
        buf = io.BytesIO(string.encode("utf-8"))
        buf.seek(0)
        return buf, "json"


def setup(bot):
    bot.add_cog(Responses(bot))
