from functools import reduce
import discord
from discord.ext import commands
import asyncio
import calendar
import datetime

from cogs.consts import *
from cogs import handlers


class Apply(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.emojis = Emojis
        self.colours = Colours()
        self.handlers = handlers
        self.bot = bot
        self.db = handlers.Database()

    @commands.command()
    @commands.guild_only()
    async def apply(self, ctx):
        if not ctx.channel.permissions_for(ctx.me).external_emojis:
            return await ctx.send(embed=discord.Embed(
                title="Missing permissions",
                description="Make sure `@everyone` has permission to use custom emojis to use this command"
            ))
        m = await ctx.send(embed=loading_embed)
        ctx = self.handlers.CustomCTX(self.bot, ctx.author, ctx.guild, ctx.channel, message=ctx.message)
        await self._apply(ctx, m)

    async def sendNotification(self, interaction, ctx, choice, guildData):
        if self.bot.get_user(int(interaction.data["target_id"])).bot:
            return await ctx.send(embed=discord.Embed(
                title="Cannot ask a bot to complete a form",
                description="You cannot ask a bot to complete a form. Please ask a user instead",
                colour=self.colours.red
            ))
        v = self.handlers.createUI(ctx, [
            self.handlers.Button(cb="co", label="Complete form", style="success", emoji=self.emojis().control.right)
        ], alwaysAccept=True)
        m = await self.bot.get_user(int(interaction.data["target_id"])).send(embed=discord.Embed(
            title="You've been asked to complete a form",
            description=f"{ctx.author.mention} asked you to complete a form in {ctx.guild.name}. Click below or type `/accept` in <#{interaction.channel.id}> to complete it",
            color=self.colours.green
        ), view=v)
        await v.wait()
        if v.selected == "co":
            ctx.author = self.bot.get_user(int(interaction.data["target_id"]))
            ctx.message = None
            await self._apply(ctx, m, choice=choice)

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        if "type" not in interaction.data:
            return
        if interaction.data["type"] == 2 and interaction.guild:
            if interaction.data["name"] == "Ask to complete form":
                guild = self.bot.get_guild(interaction.guild.id)
                if not guild.get_channel(interaction.channel.id).permissions_for(guild.get_member(interaction.user.id)).manage_roles:
                    return await interaction.response.send_message(embed=discord.Embed(
                        title="Missing permissions",
                        description="You need the `manage_roles` permission to ask someone to complete a form",
                        color=self.colours.red
                    ), ephemeral=True)
                await interaction.response.send_message(embed=loading_embed, ephemeral=True)
                m = await interaction.original_message()
                ctx = self.handlers.CustomCTX(self.bot, interaction.user, interaction.guild, interaction.channel, interaction=interaction, m=m)
                data = await self.db.get(ctx.guild.id)
                guildData = data.data
                choice = -1
                while True:
                    o = []
                    e = []
                    warnings = []
                    for i, form in enumerate(guildData):
                        if form["active"]:
                            o.append(discord.SelectOption(value=str(i), label=form["name"], description=form["description"], default=(i == choice)))
                    if not len(o):
                        o.append(discord.SelectOption(value="-1", label="No forms", description="This server does not have any forms", default=True))
                    if choice >= 0:
                        disabled = False
                        roles = [r.id for r in ctx.guild.get_member(int(interaction.user.id)).roles]
                        for role in guildData[choice]["disallowed_roles"]:
                            if role in roles:
                                warnings.append(f"You are not allowed to apply with the {ctx.guild.get_role(role).mention} role")
                                disabled = True
                        for role in guildData[choice]["required_roles"]:
                            if role not in roles:
                                warnings.append(f"You need the {ctx.guild.get_role(role).mention} role to apply")
                                disabled = True
                        e = [self.handlers.Button(cb="ap", label="Choose", style="success", emoji=self.emojis().control.right, disabled=disabled)]
                    v = self.handlers.createUI(ctx, [
                        self.handlers.Select(id="form", placeholder="Select a form", autoaccept=True, options=o)
                    ] + e)
                    await m.edit(embed=discord.Embed(
                        title="Choose a form" if choice == -1 else guildData[choice]["name"],
                        description=self.genInfo(guildData[choice], warnings) if choice >= 0 else "Select a form to ask the user to complete",
                        color=self.colours.red if len(warnings) else self.colours.green
                    ), view=v)
                    await v.wait()
                    if v.selected:
                        break
                    elif v.dropdowns:
                        choice = int(v.dropdowns["form"][0])
                choice = guildData[choice]["id"]
                self.bot.requests[interaction.data["target_id"]] = choice
                await m.edit(embed=discord.Embed(
                    title="Sent",
                    description=f"The request was sent successfully",
                    color=self.colours.green
                ), view=None)
                await asyncio.create_task(self.sendNotification(interaction, ctx, choice, guildData))
        elif interaction.type.name == "application_command" and interaction.guild:
            if interaction.data["name"] == "apply":
                if not interaction.guild.get_role(interaction.guild.default_role.id).permissions.external_emojis:
                    return await interaction.response.send_message(embed=discord.Embed(
                        title="Missing permissions",
                        description="Make sure `@everyone` has permission to use custom emojis to use this command"
                    ), ephemeral=True)
                await interaction.response.send_message(embed=loading_embed, ephemeral=True)
                m = await interaction.original_message()
                ctx = self.handlers.CustomCTX(self.bot, interaction.user, interaction.guild, interaction.channel, interaction=interaction, m=m)
                await self._apply(ctx, m)
            elif interaction.data["name"] == "accept":
                if not interaction.guild.get_role(interaction.guild.default_role.id).permissions.external_emojis:
                    return await interaction.response.send_message(embed=discord.Embed(
                        title="Missing permissions",
                        description="Make sure `@everyone` has permission to use custom emojis to use this command",
                        color=self.colours.red
                    ), ephemeral=True)
                await interaction.response.send_message(embed=loading_embed, ephemeral=True)
                m = await interaction.original_message()
                ctx = self.handlers.CustomCTX(self.bot, interaction.user, interaction.guild, interaction.channel, interaction=interaction, m=m)
                if str(interaction.user.id) in self.bot.requests:
                    await self._apply(ctx, m, choice=self.bot.requests[str(interaction.user.id)])
                else:
                    await m.edit(embed=discord.Embed(
                        title="No requests",
                        description="You have no pending requests",
                        color=self.colours.red
                    ), view=None)

    def genInfo(self, form, warnings):
        return f"**Description:**\n> {form['description']}\n" + \
               f"**Questions:** {len([q for q in form['questions'] if q['question']])}\n" + \
               f"\nThis form is anonymous. Your username will not be visible once the form is submitted.\n\n" + \
               "\n".join(warnings)

    async def _apply(self, ctx, m, choice=None):
        data = await self.db.get(ctx.guild.id)
        guildData = data.data
        skip = False
        if choice:
            skip = True
        while True:
            if skip:
                break
            if choice is None:
                choice = -1
            o = []
            e = []
            warnings = []
            for i, form in enumerate(guildData):
                if form["active"]:
                    o.append(discord.SelectOption(value=str(i), label=form["name"], description=form["description"], default=(i == choice)))
            if not len(o):
                o.append(discord.SelectOption(value="-1", label="No forms", description="This server does not have any forms", default=True))
            if choice >= 0:
                disabled = False
                roles = [r.id for r in ctx.author.roles]
                for role in guildData[choice]["disallowed_roles"]:
                    if role in roles:
                        warnings.append(f"You are not allowed to apply with the {ctx.guild.get_role(role).mention} role")
                        disabled = True
                for role in guildData[choice]["required_roles"]:
                    if role not in roles:
                        warnings.append(f"You need the {ctx.guild.get_role(role).mention} role to apply")
                        disabled = True
                e = [self.handlers.Button(cb="ap", label="Apply", style="success", emoji=self.emojis().control.right, disabled=disabled)]
            v = self.handlers.createUI(ctx, [
                self.handlers.Select(id="form", placeholder="Select a form", autoaccept=True, options=o)
            ] + e + [self.handlers.Button(cb="ca", label="Close", style="danger", emoji=self.emojis().control.cross)])
            await m.edit(embed=discord.Embed(
                title="Choose a form" if choice == -1 else guildData[choice]["name"],
                description=self.genInfo(guildData[choice], warnings) if choice >= 0 else "Select a form to view",
                color=self.colours.red if len(warnings) else self.colours.green
            ), view=v)
            await v.wait()
            if v.selected:
                if v.selected == "ca":
                    return await ctx.delete()
                break
            elif v.dropdowns:
                choice = int(v.dropdowns["form"][0])
        if not skip:
            choice = guildData[choice]["id"]
        data = None
        for form in guildData:
            if form["id"] == choice:
                data = form
                break
        answers = []
        start = datetime.datetime.now()
        for question in data["questions"]:
            if question["type"] == "text":
                v = self.handlers.createUI(ctx, [
                    self.handlers.Button(cb="sk", label="Skip", style="success", emoji=self.emojis().control.right, disabled=(question["required"])),
                    self.handlers.Button(cb="ex", label="Exit without saving", style="danger", emoji=self.emojis().control.cross)
                ])
                await m.edit(embed=discord.Embed(
                    title=question["title"],
                    description=question["description"],
                    color=getattr(self.colours, question["colour"])
                ).set_footer(text=f"Send a text response | Length: {question['options']['min']} to {question['options']['max']}"), view=v)
                try:
                    done, pending = await asyncio.wait(
                        [
                            self.bot.wait_for(
                                "message", timeout=300,
                                check=lambda message:
                                    (message.author == ctx.author) and ((message.channel.id == ctx.channel.id) if message.guild else True) and
                                    (question["options"]["min"] <= len(message.content) <= question["options"]["max"])
                            ),
                            v.wait()
                        ], return_when=asyncio.FIRST_COMPLETED)
                except (asyncio.exceptions.TimeoutError, TimeoutError, asyncio.exceptions.CancelledError):
                    return
                for future in done:
                    future.exception()
                for future in pending:
                    future.cancel()

                response = done.pop().result()
                if v.selected == "sk":
                    answers.append([question["id"], None])
                    continue
                elif v.selected == "ex":
                    break
                try:
                    if ctx.guild:
                        await response.delete()
                except discord.HTTPException:
                    pass
                answers.append([question["id"], response.content])
            elif question["type"] == "number":
                v = self.handlers.createUI(ctx, [
                    self.handlers.Button(cb="sk", label="Skip", style="success", emoji=self.emojis().control.right, disabled=(question["required"])),
                    self.handlers.Button(cb="ex", label="Exit without saving", style="danger", emoji=self.emojis().control.cross)
                ])
                await m.edit(embed=discord.Embed(
                    title=question["title"],
                    description=question["description"],
                    color=getattr(self.colours, question["colour"])
                ).set_footer(text=f"Send a number response | Size: {question['options']['min']} to {question['options']['max']}"), view=v)
                try:
                    done, pending = await asyncio.wait(
                        [
                            self.bot.wait_for(
                                "message", timeout=300,
                                check=lambda message:
                                    (message.author == ctx.author) and ((message.channel.id == ctx.channel.id) if message.guild else True) and (message.content.isdigit()) and
                                    (question["options"]["min"] <= int(message.content) <= question["options"]["max"])
                            ),
                            v.wait()
                        ], return_when=asyncio.FIRST_COMPLETED)
                except (asyncio.exceptions.TimeoutError, TimeoutError, asyncio.exceptions.CancelledError):
                    return
                for future in done:
                    future.exception()
                for future in pending:
                    future.cancel()
                response = done.pop().result()
                if v.selected == "sk":
                    answers.append([question["id"], None])
                    continue
                elif v.selected == "ex":
                    break
                try:
                    if ctx.guild:
                        await response.delete()
                except discord.HTTPException:
                    pass
                answers.append([question["id"], int(response.content)])
            elif question["type"] == "multichoice":
                e = []
                for k, v in question["options"]["options"].items():
                    e.append(discord.SelectOption(value=str(k), label=v[0], description=v[1], emoji=getattr(self.emojis().r, str(k))))
                e = [self.handlers.Select(
                    id="chosen", placeholder="Please select", autoaccept=True, options=e,
                    min_values=question["options"]["min"], max_values=question["options"]["max"]
                )]
                v = self.handlers.createUI(ctx, e + [
                    self.handlers.Button(cb="sk", label="Skip", style="success", emoji=self.emojis().control.right, disabled=(question["required"])),
                    self.handlers.Button(cb="ex", label="Exit without saving", style="danger", emoji=self.emojis().control.cross)
                ])
                await m.edit(embed=discord.Embed(
                    title=question["title"],
                    description=question["description"],
                    color=getattr(self.colours, question["colour"])
                ).set_footer(
                    text=f"Choose {question['options']['min']} {'to ' + str(question['options']['max']) if question['options']['min'] != question['options']['max'] else ''}"
                ), view=v)
                await v.wait()
                if v.selected == "sk":
                    answers.append([question["id"], None])
                    continue
                elif v.selected == "ex":
                    break
                if v.dropdowns:
                    answers.append([question["id"], v.dropdowns["chosen"]])
            elif question["type"] == "date":
                now = datetime.datetime.now()
                month = now.month - 1
                year = now.year
                out = False
                while True:
                    if month >= 12:
                        month = 0
                        year += 1
                    elif month < 0:
                        month = 11
                        year -= 1
                    v = self.handlers.createUI(ctx, [
                        self.handlers.Button(cb="sk", label="Skip", style="success", emoji=self.emojis().control.right, disabled=(question["required"])),
                        self.handlers.Button(cb="b2", label=" ", style="secondary", emoji=self.emojis().control.back),
                        self.handlers.Button(cb="b1", label=" ", style="secondary", emoji=self.emojis().control.left),
                        self.handlers.Button(cb="f1", label=" ", style="secondary", emoji=self.emojis().control.right),
                        self.handlers.Button(cb="f2", label=" ", style="secondary", emoji=self.emojis().control.forward),
                        self.handlers.Button(cb="ex", label="Exit without saving", style="danger", emoji=self.emojis().control.cross)
                    ])
                    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
                    s = f"\n\n{months[month]} - {year}\n"
                    for d in ["M", "T", "W", "T", "F", "S", "S"]:
                        s += str(getattr(self.emojis().c, d))
                    s += "\n"
                    for week in calendar.monthcalendar(year, month + 1):
                        s += "".join([getattr(self.emojis().c, str(m) if m != 0 else "B") for m in week]) + "\n"
                    await m.edit(embed=discord.Embed(
                        title=question["title"],
                        description=question["description"] + s,
                        color=getattr(self.colours, question["colour"])
                    ).set_footer(text="Use /date select to select your final date or /date jump to view it on the calendar"), view=v)
                    try:
                        done, pending = await asyncio.wait(
                            [
                                self.bot.wait_for(
                                    "interaction", timeout=300,
                                    check=lambda interaction:
                                        (interaction.user.id == ctx.author.id) and
                                        ((interaction.channel.id == ctx.channel.id) if interaction.guild else True)
                                    ),
                                v.wait()
                            ],
                            return_when=asyncio.FIRST_COMPLETED,
                        )
                    except (asyncio.exceptions.TimeoutError, TimeoutError, asyncio.exceptions.CancelledError):
                        return None

                    for future in done:
                        future.exception()
                    for future in pending:
                        future.cancel()

                    response = done.pop().result()
                    if v.selected is not None:
                        if v.selected == "sk":
                            answers.append([question["id"], None])
                            break
                        elif v.selected == "b2":
                            year -= 1
                        elif v.selected == "b1":
                            month -= 1
                        elif v.selected == "f1":
                            month += 1
                        elif v.selected == "f2":
                            year += 1
                        elif v.selected == "ex":
                            out = True
                            break
                    elif hasattr(response, "data"):
                        await response.response.send_message(embed=discord.Embed(title="Accepted", color=self.colours.green))
                        await response.delete_original_message()
                        if response.data["name"] == "date":
                            if response.data["options"][0]["name"] == "jump":
                                choices = {r["name"]: r["value"] for r in response.data["options"][0]["options"]}
                                if "year" in choices:
                                    year = choices["year"]
                                if "month" in choices:
                                    month = int(choices["month"])
                            elif response.data["options"][0]["name"] == "select":
                                choices = {r["name"]: r["value"] for r in response.data["options"][0]["options"]}
                                if year not in choices:
                                    choices['year'] = year
                                if month not in choices:
                                    choices['month'] = month
                                maxDays = calendar.monthrange(year, choices["month"] + 1)[1]
                                if 1 <= choices["day"] <= maxDays:
                                    answers.append([question["id"], f"{choices['year']}-{choices['month']}-{choices['day']}"])
                                    break
                if out:
                    break
            elif question["type"] == "time":
                ex = False
                while True:
                    v = self.handlers.createUI(ctx, [
                        self.handlers.Button(cb="sk", label="Skip", style="success", emoji=self.emojis().control.right, disabled=(question["required"])),
                        self.handlers.Button(cb="ex", label="Exit without saving", style="danger", emoji=self.emojis().control.cross)
                    ])
                    await m.edit(embed=discord.Embed(
                        title=question["title"],
                        description=question["description"],
                        color=getattr(self.colours, question["colour"])
                    ).set_footer(text="Type /time followed by hours, minutes, and/or seconds to select your final time"), view=v)
                    try:
                        done, pending = await asyncio.wait(
                            [
                                self.bot.wait_for(
                                    "interaction",
                                    timeout=300,
                                    check=lambda interaction:
                                        (interaction.user.id == ctx.author.id) and
                                        ((interaction.channel.id == ctx.channel.id) if interaction.guild else True)
                                ),
                                v.wait()
                            ],
                            return_when=asyncio.FIRST_COMPLETED,
                        )
                    except (asyncio.exceptions.TimeoutError, TimeoutError, asyncio.exceptions.CancelledError):
                        return None

                    for future in done:
                        future.exception()
                    for future in pending:
                        future.cancel()

                    response = done.pop().result()
                    if v.selected is not None:
                        if v.selected == "sk":
                            answers.append([question["id"], None])
                            break
                        elif v.selected == "ex":
                            ex = True
                            break
                    elif hasattr(response, "data"):
                        await response.response.send_message(embed=discord.Embed(title="Accepted", color=self.colours.green))
                        await response.delete_original_message()
                        if response.data["name"] == "time":
                            choices = {r["name"]: r["value"] for r in response.data["options"]}
                            s = ""
                            if "second" in choices:
                                if 0 <= choices["second"] <= 59:
                                    s = ":" + str(choices["second"])
                            if 0 <= choices["hour"] <= 24 and 0 <= choices["minute"] <= 59:
                                if choices["hour"] == 24:
                                    choices["hour"] = "0"
                                s = f"{choices['hour']}:{choices['minute']}{s}"
                                answers.append([question["id"], s])
                                break
                if ex:
                    break
            elif question["type"] == "fileupload":
                v = self.handlers.createUI(ctx, [
                    self.handlers.Button(cb="sk", label="Skip", style="success", emoji=self.emojis().control.right, disabled=(question["required"])),
                    self.handlers.Button(cb="ex", label="Exit without saving", style="danger", emoji=self.emojis().control.cross)
                ])
                await m.edit(embed=discord.Embed(
                    title=question["title"],
                    description=question["description"],
                    color=getattr(self.colours, question["colour"])
                ).set_footer(text="Send a file"), view=v)
                try:
                    done, pending = await asyncio.wait(
                        [
                            self.bot.wait_for(
                                "message", timeout=300,
                                check=lambda message:
                                    (message.author == ctx.author) and ((message.channel.id == ctx.channel.id) if message.guild else True) and
                                    (len(message.attachments))
                            ),
                            v.wait()
                        ], return_when=asyncio.FIRST_COMPLETED)
                except (asyncio.exceptions.TimeoutError, TimeoutError, asyncio.exceptions.CancelledError):
                    return
                for future in done:
                    future.exception()
                for future in pending:
                    future.cancel()

                response = done.pop().result()
                if v.selected == "sk":
                    answers.append([question["id"], None])
                    continue
                elif v.selected == "ex":
                    break
                try:
                    if ctx.guild:
                        await response.delete()
                except discord.HTTPException:
                    pass
                if response.attachments:
                    f = response.attachments[0]
                    if f.size > 8388608:
                        try:
                            if ctx.guild:
                                await f.delete()
                        except discord.HTTPException:
                            pass
                        v = self.handlers.createUI(ctx, [
                            self.handlers.Button(cb="co", label="Continue", style="success", emoji=self.emojis().control.right)
                        ])
                        await m.edit(embed=discord.Embed(
                            title="Upload failed",
                            description="Your file was too big",
                            color=Colours.red
                        ), view=v)
                        answers.append([question["id"], "File too big"])
                        await v.wait()
                        continue
                    await m.edit(embed=discord.Embed(
                        title="Uploading your file",
                        description="Please give us a moment to upload your file",
                        color=Colours.green
                    ))
                    message = await self.bot.get_channel(814433925542969416).send(file=await f.to_file())
                    answers.append([question["id"], message.attachments[0].url])
            elif question["type"] == "text-decoration":
                v = self.handlers.createUI(ctx, [
                    self.handlers.Button(cb="sk", label="Continue", style="success", emoji=self.emojis().control.right),
                    self.handlers.Button(cb="ex", label="Exit without saving", style="danger", emoji=self.emojis().control.cross)
                ])
                await m.edit(embed=discord.Embed(
                    title=question["title"],
                    description=question["description"],
                    color=getattr(self.colours, question["colour"])
                ), view=v)
                await v.wait()
                if v.selected == "sk":
                    continue
                elif v.selected == "ex":
                    break
            elif question["type"] == "image-decoration":
                v = self.handlers.createUI(ctx, [
                    self.handlers.Button(cb="sk", label="Continue", style="success", emoji=self.emojis().control.right),
                    self.handlers.Button(cb="ex", label="Exit without saving", style="danger", emoji=self.emojis().control.cross)
                ])
                await m.edit(embed=discord.Embed(
                    title=question["title"],
                    description=question["description"],
                    color=getattr(self.colours, question["colour"])
                ).set_image(url=question["options"]["url"]), view=v)
                await v.wait()
                if v.selected == "sk":
                    continue
                elif v.selected == "ex":
                    break
            elif question["type"] == "url-decoration":
                v = self.handlers.createUI(ctx, [
                    self.handlers.Button(label="Open", style="url", url=question["options"]["url"], emoji=self.emojis().control.up),
                    self.handlers.Button(cb="sk", label="Continue", style="success", emoji=self.emojis().control.right),
                    self.handlers.Button(cb="ex", label="Exit without saving", style="danger", emoji=self.emojis().control.cross)
                ])
                await m.edit(embed=discord.Embed(
                    title=question["title"],
                    description=question["description"],
                    color=getattr(self.colours, question["colour"])
                ), view=v)
                await v.wait()
                if v.selected == "sk":
                    continue
                elif v.selected == "ex":
                    break
            else:
                continue
        else:
            if str(ctx.author.id) in self.bot.requests:
                del self.bot.requests[str(ctx.author.id)]
            response = {
                "user": None if data["anonymous"] else ctx.author.id,
                "time": round((datetime.datetime.now() - start).total_seconds()),
                "answers": answers
            }
            entry = await self.db.get(ctx.guild.id)
            newdata = entry.responses
            if choice not in newdata:
                newdata[str(choice)] = [response]
            else:
                newdata[str(choice)].append(response)
            await entry.update(responses=newdata)
            if data["auto_accept"]:
                for role in data["given_roles"]:
                    if role.id not in [r.id for r in ctx.author.roles]:
                        await ctx.author.add_roles(role)
                for role in data["removed_roles"]:
                    if role.id in [r.id for r in ctx.author.roles]:
                        await ctx.author.remove_roles(role)
            await m.edit(embed=discord.Embed(
                title="Completed",
                description=f"Your response has been recorded successfully",
                color=self.colours.green
            ), view=None)
            return
        await m.edit(embed=discord.Embed(
            title="Ended",
            description=f"Your responses has been deleted",
            color=self.colours.red
        ), view=None)


def setup(bot):
    bot.add_cog(Apply(bot))
