import discord
from discord.ext import commands
import asyncio
import validators
import aiohttp
import datetime

from cogs.consts import *
from cogs import handlers


class New(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.emojis = Emojis
        self.colours = Colours()
        self.handlers = handlers
        self.bot = bot
        self.db = handlers.Database()

    @commands.command()
    @commands.guild_only()
    async def create(self, ctx):
        if not ctx.channel.permissions_for(ctx.author).manage_guild or not ctx.channel.permissions_for(ctx.author).manage_roles:
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
        await self._create(ctx, m, createdBy="message")

    @commands.command()
    @commands.guild_only()
    async def manage(self, ctx):
        if not ctx.channel.permissions_for(ctx.author).manage_guild or not ctx.channel.permissions_for(ctx.author).manage_roles:
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
        await self._manage(ctx, m, createdBy="message")

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        if interaction.type.name == "application_command" and interaction.guild:
            if interaction.data["name"] == "create":
                if not interaction.guild.get_role(interaction.guild.default_role.id).permissions.external_emojis:
                    return await interaction.response.send_message(embed=discord.Embed(
                        title="Missing permissions",
                        description="Make sure `@everyone` has permission to use custom emojis to use this command"
                    ), ephemeral=True)
                await interaction.response.send_message(embed=loading_embed, ephemeral=True)
                m = await interaction.original_message()
                ctx = self.handlers.CustomCTX(self.bot, interaction.user, interaction.guild, interaction.channel, interaction=interaction, m=m)
                await self._create(ctx, m, createdBy="interaction", interaction=interaction)
            if interaction.data["name"] == "manage":
                if not interaction.guild.get_role(interaction.guild.default_role.id).permissions.external_emojis:
                    return await interaction.response.send_message(embed=discord.Embed(
                        title="Missing permissions",
                        description="Make sure `@everyone` has permission to use custom emojis to use this command"
                    ), ephemeral=True)
                await interaction.response.send_message(embed=loading_embed, ephemeral=True)
                m = await interaction.original_message()
                ctx = self.handlers.CustomCTX(self.bot, interaction.user, interaction.guild, interaction.channel, interaction=interaction, m=m)
                if "options" in interaction.data:
                    if interaction.data["options"][0]["value"] == "create":
                        await self._manage(ctx, m, createdBy="interaction", interaction=interaction, page="create")
                    elif interaction.data["options"][0]["value"] == "edit":
                        await self._manage(ctx, m, createdBy="interaction", interaction=interaction, page="edit")
                    elif interaction.data["options"][0]["value"] == "delete":
                        await self._manage(ctx, m, createdBy="interaction", interaction=interaction, page="delete")
                    else:
                        await self._manage(ctx, m, createdBy="interaction", interaction=interaction)
                else:
                    await self._manage(ctx, m, createdBy="interaction", interaction=interaction)

    async def _manage(self, ctx, m, createdBy="message", interaction=None, page=None):
        v = self.handlers.createUI(ctx, [
            self.handlers.Button(cb="cr", label="Create", style="success", emoji=self.bot.get_emoji(self.emojis(idOnly=True).question.new)),
            self.handlers.Button(cb="ed", label="Edit", style="secondary", emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.edit)),
            self.handlers.Button(cb="de", label="Delete", style="danger", emoji=self.bot.get_emoji(self.emojis(idOnly=True).question.delete))
        ])
        await m.edit(embed=discord.Embed(
            title="Manage forms",
            description=(f"Select a form to {page}" if page else "Select an action"),
            color=self.colours.blue
        ), view=v)
        if not page:
            await v.wait()
            d = {
                "cr": "create",
                "ed": "edit",
                "de": "delete"
            }
            if not v.selected:
                return await ctx.delete()
            await m.edit(embed=discord.Embed(
                title="Manage forms",
                description=f"Select a form to {d[v.selected]}",
                color=self.colours.blue
            ))
        if page:
            v.selected = page
        if page == "create" or v.selected == "cr":
            return await self._create(ctx, m, createdBy, interaction)
        entry = await self.db.get(ctx.guild.id)
        o = []
        for form in entry.data:
            o.append(discord.SelectOption(value=str(form["id"]), label=form["name"], description=form["description"]))
        if not len(o):
            o.append(discord.SelectOption(value="n", label="No forms", description="There are no forms to manage"))
        if page == "edit" or v.selected == "ed":
            s = self.handlers.createUI(ctx, [self.handlers.Select(id="chosen", options=o, autoaccept=True)])
            await m.edit(view=s)
            await s.wait()
            if s.dropdowns:
                c = None
                for form in entry.data:
                    if form["id"] == s.dropdowns["chosen"][0]:
                        c = form
                return await self._create(ctx, m, createdBy, interaction=interaction, default=c)
        elif page == "delete" or v.selected == "de":
            s = self.handlers.createUI(ctx, [self.handlers.Select(id="chosen", options=o, autoaccept=True, max_values=len(o))])
            await m.edit(view=s)
            await s.wait()
            new = []
            for form in entry.data:
                if not form["id"] == s.dropdowns["chosen"][0]:
                    new.append(form)
                else:
                    from config import config
                    async with aiohttp.ClientSession() as session:
                        async with session.post(f"{config.rsm}/clicksforms/delete", json={
                            "guild_id": ctx.guild.id,
                            "created_by": ctx.author.id,
                            "questions": 0,
                            "name": form["name"],
                            "auth": config.rsmToken
                        }) as _:
                            pass
            await entry.update(data=new)
            return await m.edit(embed=discord.Embed(
                title="Forms deleted successfully",
                color=self.colours.blue
            ), view=None)

    async def _create(self, ctx, m, createdBy="message", interaction=None, default=None):
        if default:
            overwrite = True
        else:
            overwrite = False
            entry = await self.db.get(ctx.guild.id)
            if len(entry.data) >= 25:
                return await m.edit(embed=discord.Embed(
                    title="Maximum number of forms reached",
                    description="You can delete one of your forms to make room for a new one",
                    color=self.colours.red
                ), view=None)
        data = default or {
            "id": str(datetime.datetime.now().timestamp()),
            "active": True,
            "anonymous": False,
            "guild": ctx.guild.id,
            "created_by": ctx.author.id,
            "name": "New Form",
            "description": "The default form",
            "required_roles": [],
            "disallowed_roles": [],
            "given_roles": [],
            "removed_roles": [],
            "auto_accept": False,
            "questions": []
        }
        while True:
            v = self.handlers.createUI(ctx, [
                self.handlers.Button(cb="nq", label="New question", style="success", emoji=self.bot.get_emoji(self.emojis(idOnly=True).question.new),
                                     disabled=(len(data["questions"]) == 25)),
                self.handlers.Button(cb="rq", label="Remove question", style="danger", emoji=self.bot.get_emoji(self.emojis(idOnly=True).question.delete),
                                     disabled=not len(data["questions"])),
                self.handlers.Button(cb="eq", label="Edit question", style="secondary", emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.edit),
                                     disabled=not len(data["questions"])),
                self.handlers.Button(cb="re", label="Reorder questions", style="secondary", emoji=self.bot.get_emoji(self.emojis(idOnly=True).question.reorder),
                                     disabled=not len(data["questions"])),
                self.handlers.Button(cb="ed", label="Edit details", style="secondary", emoji=self.bot.get_emoji(self.emojis(idOnly=True).meta.edit)),
                self.handlers.Button(cb="sf", label="Save form", style="success", emoji=self.bot.get_emoji(self.emojis(idOnly=True).form.save)),
                self.handlers.Button(cb="ex", label="Exit without saving", style="danger", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.cross))
            ])
            e = discord.Embed(
                title=data["name"],
                description=f"**Description:**\n> " +
                            data["description"],
                color=self.colours.blue
            ).set_footer(text=("This form does not have a name, you can add one on the Edit details page" if data["name"] == "New Form" else ""))
            for question in data["questions"]:
                if question["question"]:
                    emoji = getattr(self.emojis().question, question["type"])
                else:
                    emoji = getattr(self.emojis().question.decoration, question["type"].split("-")[0])
                e.add_field(name=f"{emoji} {question['title']}", value=question["description"].strip() or "*No description set*")
            await m.edit(embed=e, view=v)
            await v.wait()
            if v.selected is None:
                break
            elif v.selected == "nq":
                data = await self.newQuestion(m, ctx, data)
            elif v.selected == "rq":
                data = await self.removeQuestion(m, ctx, data)
            elif v.selected == "eq":
                data = await self.editQuestion(m, ctx, data)
            elif v.selected == "ed":
                data = await self.editDetails(m, ctx, data)
            elif v.selected == "re":
                data = await self.reorder(m, ctx, data)
            elif v.selected == "sf":
                await self.saveForm(ctx, data, overwrite)
                return await m.edit(embed=discord.Embed(
                    title="Form saved",
                    description=f"Your form has been saved as `{data['name']}`",
                    color=self.colours.green
                ), view=None)
            elif v.selected == "ex":
                await ctx.delete()
                break

    async def reorder(self, m, ctx, data):
        o = []
        count = 0
        for question in data["questions"]:
            if question["question"]:
                emoji = getattr(self.emojis(idOnly=True).question, question["type"])
            else:
                emoji = getattr(self.emojis(idOnly=True).question.decoration, question["type"].split("-")[0])
            o.append(discord.SelectOption(
                value=str(count),
                label=question["title"],
                description=question["description"].strip() or "*No description set*",
                emoji=self.bot.get_emoji(emoji)
            ))
            count += 1
        v = self.handlers.createUI(ctx, [
            self.handlers.Select(id="order", placeholder="Decoration type", autoaccept=True, options=o, min_values=len(o), max_values=len(o)),
            self.handlers.Button(cb="ba", label="Back", style="danger", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.left))
        ])
        await m.edit(embed=discord.Embed(
            title="Select question order",
            description="Click the questions in the order they should appear in",
            color=self.colours.green
        ), view=v)
        await v.wait()
        if v.selected is not None:
            return
        neworder = []
        for i in v.dropdowns["order"]:
            neworder.append(data["questions"][int(i)])
        data["questions"] = neworder
        return data

    async def newQuestion(self, m, ctx, data):
        dec = False
        default = ""
        while True:
            decoration = []
            if dec:
                decoration = [self.handlers.Select(id="decoration", placeholder="Decoration type", autoaccept=True, options=[
                    discord.SelectOption(value="te", label="Text", description="Text shown between questions",
                                         emoji=self.bot.get_emoji(self.emojis(idOnly=True).question.decoration.text)),
                    discord.SelectOption(value="im", label="Image", description="Image shown to the user",
                                         emoji=self.bot.get_emoji(self.emojis(idOnly=True).question.decoration.image)),
                    discord.SelectOption(value="ur", label="URL", description="URL shown to the user",
                                         emoji=self.bot.get_emoji(self.emojis(idOnly=True).question.decoration.url))
                ])]
            v = self.handlers.createUI(ctx, [
                self.handlers.Select(id="type", placeholder="Question type", autoaccept=True, options=[
                    discord.SelectOption(value="te", label="Text", description="A simple text response",
                                         emoji=self.bot.get_emoji(self.emojis(idOnly=True).question.text), default=("te" == default)),
                    discord.SelectOption(value="nu", label="Number", description="An integer response",
                                         emoji=self.bot.get_emoji(self.emojis(idOnly=True).question.number), default=("nu" == default)),
                    discord.SelectOption(value="mc", label="Multiple Choice", description="Choose from a list of options",
                                         emoji=self.bot.get_emoji(self.emojis(idOnly=True).question.multichoice), default=("mc" == default)),
                    discord.SelectOption(value="fi", label="File Upload", description="A file uploaded",
                                         emoji=self.bot.get_emoji(self.emojis(idOnly=True).question.fileupload), default=("fi" == default)),
                    discord.SelectOption(value="ti", label="Time", description="A time",
                                         emoji=self.bot.get_emoji(self.emojis(idOnly=True).question.time), default=("ti" == default)),
                    discord.SelectOption(value="da", label="Date", description="A date (Year, month and day)",
                                         emoji=self.bot.get_emoji(self.emojis(idOnly=True).question.date), default=("da" == default)),
                    discord.SelectOption(value="de", label="Decoration", description="Text or images shown between questions",
                                         emoji=self.bot.get_emoji(self.emojis(idOnly=True).question.decoration.icon), default=("de" == default))
                ])
            ] + decoration + [self.handlers.Button(cb="ca", label="Cancel", style="danger", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.cross))])
            await m.edit(embed=discord.Embed(
                title="New Question",
                description="Select a question type",
                color=self.colours.red
            ), view=v)
            await v.wait()
            if v.selected == "ca":
                return data
            if "type" in v.dropdowns:
                default = v.dropdowns["type"][0]
                if v.dropdowns["type"][0] == "de":
                    dec = True
                elif v.dropdowns["type"][0] == "te":
                    await self.newText(m, ctx, data)
                    return data
                elif v.dropdowns["type"][0] == "nu":
                    await self.newNumber(m, ctx, data)
                    return data
                elif v.dropdowns["type"][0] == "mc":
                    await self.newMultipleChoice(m, ctx, data)
                    return data
                elif v.dropdowns["type"][0] == "fi":
                    await self.newFileUpload(m, ctx, data)
                    return data
                elif v.dropdowns["type"][0] == "ti":
                    await self.newTime(m, ctx, data)
                    return data
                elif v.dropdowns["type"][0] == "da":
                    await self.newDate(m, ctx, data)
                    return data
            elif "decoration" in v.dropdowns:
                if v.dropdowns["decoration"][0] == "te":
                    await self.newTextDecoration(m, ctx, data)
                    return data
                elif v.dropdowns["decoration"][0] == "im":
                    await self.newImageDecoration(m, ctx, data)
                    return data
                elif v.dropdowns["decoration"][0] == "ur":
                    await self.newURLDecoration(m, ctx, data)
                    return data

    async def TextInput(self, ctx, m, title, description, optional=False, min_length=1, max_length=100):
        v = self.handlers.createUI(ctx, [
            self.handlers.Button(cb="ca", label="Cancel", style="danger", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.cross))
        ] + ([self.handlers.Button(cb="sk", label="Skip", style="success", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.tick))] if optional else []))
        await m.edit(embed=discord.Embed(
            title=title,
            description=description,
            color=self.colours.red
        ), view=v)
        try:
            done, pending = await asyncio.wait(
                [
                    self.bot.wait_for("message", timeout=300, check=lambda message: message.author == ctx.author and message.channel.id == ctx.channel.id),
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
        if response is False:
            return False
        try:
            await response.delete()
        except discord.Forbidden:
            pass
        if min_length <= len(response.content) <= max_length:
            return response.content
        return None

    async def NumberInput(self, ctx, m, title, description, optional=False, min_size=1, max_size=100):
        v = self.handlers.createUI(ctx, [
            self.handlers.Button(cb="ca", label="Cancel", style="danger", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.cross))
        ] + ([self.handlers.Button(cb="sk", label="Skip", style="success", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.tick))] if optional else []))
        await m.edit(embed=discord.Embed(
            title=title,
            description=description,
            color=self.colours.red
        ), view=v)
        try:
            done, pending = await asyncio.wait(
                [
                    self.bot.wait_for(
                        "message",
                        timeout=300,
                        check=lambda message:
                            (message.content.isdigit() or (message.content[0] == "-" and len(message.content) > 1 and message.content[1:].isdigit())) and
                            message.author == ctx.author and
                            message.channel.id == ctx.channel.id
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
        if response is False:
            return False
        try:
            await response.delete()
        except discord.Forbidden:
            pass
        if response.content.isdigit():
            return max(min_size, min(int(response.content), max_size))
        return None

    async def ColourInput(self, ctx, m):
        v = self.handlers.createUI(ctx, [
            self.handlers.Button(cb="red", label="Red", style="secondary", emoji=self.bot.get_emoji(self.emojis(idOnly=True).cols.red)),
            self.handlers.Button(cb="orange", label="Orange", style="secondary", emoji=self.bot.get_emoji(self.emojis(idOnly=True).cols.orange)),
            self.handlers.Button(cb="yellow", label="Yellow", style="secondary", emoji=self.bot.get_emoji(self.emojis(idOnly=True).cols.yellow)),
            self.handlers.Button(cb="green", label="Green", style="secondary", emoji=self.bot.get_emoji(self.emojis(idOnly=True).cols.green)),
            self.handlers.Button(cb="blue", label="Blue", style="secondary", emoji=self.bot.get_emoji(self.emojis(idOnly=True).cols.blue)),
            self.handlers.Button(cb="purple", label="Purple", style="secondary", emoji=self.bot.get_emoji(self.emojis(idOnly=True).cols.purple)),
            self.handlers.Button(cb="pink", label="Pink", style="secondary", emoji=self.bot.get_emoji(self.emojis(idOnly=True).cols.pink)),
            self.handlers.Button(cb="grey", label="Grey", style="secondary", emoji=self.bot.get_emoji(self.emojis(idOnly=True).cols.grey))
        ])
        await m.edit(embed=discord.Embed(
            title="Question colour",
            description=f"What colour should this question be?",
            color=self.colours.red
        ), view=v)
        await v.wait()
        return v.selected

    async def RoleInput(self, ctx, m, title, description, optional=False, cap=25):
        v = self.handlers.createUI(ctx, [
            self.handlers.Button(cb="ca", label="Cancel", style="danger", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.cross))
        ] + ([self.handlers.Button(cb="sk", label="Skip", style="success", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.tick))] if optional else []))
        await m.edit(embed=discord.Embed(
            title=title,
            description=description + "\n\nUse `/roles` followed by all the roles to select",
            color=self.colours.red
        ), view=v)
        try:
            done, pending = await asyncio.wait(
                [
                    self.bot.wait_for("interaction", timeout=300, check=lambda interaction: interaction.user.id == ctx.author.id and interaction.channel.id == ctx.channel.id),
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
        if hasattr(response, "selected") and response.selected is not None:
            return True
        if hasattr(response, "data"):
            await response.response.send_message(embed=discord.Embed(title="Accepted", color=self.colours.green))
            await response.delete_original_message()
            return [r for r in list(response.data["resolved"]["roles"].keys())[:cap]]
        return None

    async def CategoryInput(self, ctx, m, title, description, optional=False):
        v = self.handlers.createUI(ctx, [
            self.handlers.Button(cb="ca", label="Cancel", style="danger", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.cross))
        ] + ([self.handlers.Button(cb="sk", label="Skip", style="success", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.tick))] if optional else []))
        await m.edit(embed=discord.Embed(
            title=title,
            description=description + "\n\nUse `/category` followed by the category, or a channel in it",
            color=self.colours.red
        ), view=v)
        try:
            done, pending = await asyncio.wait(
                [
                    self.bot.wait_for("interaction", timeout=300, check=lambda interaction: interaction.user.id == ctx.author.id and interaction.channel.id == ctx.channel.id),
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
                return True
            return None
        if hasattr(response, "data"):
            await response.response.send_message(embed=discord.Embed(title="Accepted", color=self.colours.green))
            await response.delete_original_message()
            if response.data["resolved"]["channels"][list(response.data["resolved"]["channels"].keys())[0]]["type"] == 4:
                return list(response.data["resolved"]["channels"].keys())[0]
            else:
                channel = ctx.guild.get_channel(int(list(response.data["resolved"]["channels"].keys())[0]))
                if channel and channel.category:
                    return channel.category.id
                return None
        return None

    def getCol(self, cb):
        if cb in self.cl:
            return "secondary"
        return "primary"

    async def newText(self, m, ctx, data, default=None):
        question = default or {"type": "text", "title": "", "description": "", "colour": "red",
                               "options": {"min": 1, "max": 2000}, "required": True, "question": True, "id": datetime.datetime.now().timestamp()}
        self.cl = []
        if default:
            self.cl = ["ti", "de", "co"]
        while True:
            v = self.handlers.createUI(ctx, [
                self.handlers.Button(cb="ti", label="Title", style=self.getCol("ti"), emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.title)),
                self.handlers.Button(cb="de", label="Description", style=self.getCol("de"), emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.description)),
                self.handlers.Button(cb="co", label="Colour", style=self.getCol("co"), emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.colour)),
                self.handlers.Button(cb="re", label="Required", style="secondary", emoji=self.bot.get_emoji(
                    getattr(self.emojis(idOnly=True).details.required, str(question["required"]).lower())
                )),
                self.handlers.Button(cb="mi", label="Minimum length", style="secondary", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.down)),
                self.handlers.Button(cb="ma", label="Maximum length", style="secondary", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.up)),
                self.handlers.Button(cb="ca", label="Cancel", style="danger", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.cross)),
                self.handlers.Button(cb="ad", label="Save" if default else "Add", style="success", disabled=not bool(question["title"]),
                                     emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.tick))
            ])
            await m.edit(embed=discord.Embed(
                title=self.emojis().question.text + " " + (question["title"] or ""),
                description=f"**Description:**\n> {question['description'] if 'description' in question else '*No description set*'}\n"
                            f"**Required:** {'Yes' if question['required'] else 'No'}\n"
                            f"**Length:**\n> Minimum: {question['options']['min']}\n> Maximum: {question['options']['max']}",
                color=getattr(self.colours, question["colour"])
            ).set_footer(text=("" if question["title"] else "A title is required")), view=v)
            await v.wait()
            if v.selected == "ti":
                self.cl.append("ti")
                i = await self.TextInput(ctx, m, "Question title", "What should the title of the question be?", optional=False, min_length=1, max_length=200)
                if i:
                    question["title"] = i
            elif v.selected == "de":
                self.cl.append("de")
                i = await self.TextInput(ctx, m, "Question description", "What should the description of the question be?", optional=True, min_length=1, max_length=1000)
                if i is True:
                    question["description"] = ""
                elif i:
                    question["description"] = i
            elif v.selected == "co":
                self.cl.append("co")
                question["colour"] = await self.ColourInput(ctx, m)
            elif v.selected == "re":
                question["required"] = not question["required"]
            elif v.selected == "mi":
                i = await self.NumberInput(ctx, m, "Minimum length", "What should the minimum length of the response be?", optional=False, min_size=1, max_size=1000)
                if i:
                    question["options"]["min"] = i
            elif v.selected == "ma":
                i = await self.NumberInput(ctx, m, "Maximum length", "What should the maximum length of the response be?", optional=False, min_size=1, max_size=1000)
                if i:
                    question["options"]["max"] = i
            elif v.selected == "ca":
                break
            elif v.selected == "ad":
                data["questions"].append(question)
                break
        return data

    async def newNumber(self, m, ctx, data, default=None):
        question = default or {"type": "number", "title": "", "description": "", "colour": "red",
                               "options": {"min": 1, "max": 1000000000000}, "required": True, "question": True, "id": datetime.datetime.now().timestamp()}
        self.cl = []
        if default:
            self.cl = ["ti", "de", "co"]
        while True:
            v = self.handlers.createUI(ctx, [
                self.handlers.Button(cb="ti", label="Title", style=self.getCol("ti"), emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.title)),
                self.handlers.Button(cb="de", label="Description", style=self.getCol("de"), emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.description)),
                self.handlers.Button(cb="co", label="Colour", style=self.getCol("co"), emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.colour)),
                self.handlers.Button(cb="re", label="Required", style="secondary", emoji=self.bot.get_emoji(
                    getattr(self.emojis(idOnly=True).details.required, str(question["required"]).lower())
                )),
                self.handlers.Button(cb="mi", label="Minimum size", style="secondary", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.down)),
                self.handlers.Button(cb="ma", label="Maximum size", style="secondary", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.up)),
                self.handlers.Button(cb="ca", label="Cancel", style="danger", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.cross)),
                self.handlers.Button(cb="ad", label="Save" if default else "Add", style="success", disabled=not bool(question["title"]),
                                     emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.tick))
            ])
            await m.edit(embed=discord.Embed(
                title=self.emojis().question.number + " " + (question["title"] or ""),
                description=f"**Description:**\n> {question['description'] if 'description' in question else '*No description set*'}\n"
                            f"**Required:** {'Yes' if question['required'] else 'No'}\n"
                            f"**Size limits:**\n> Minimum: {question['options']['min']}\n> Maximum: {question['options']['max']}",
                color=getattr(self.colours, question["colour"])
            ).set_footer(text=("" if question["title"] else "A title is required")), view=v)
            await v.wait()
            if v.selected == "ti":
                self.cl.append("ti")
                i = await self.TextInput(ctx, m, "Question title", "What should the title of the question be?", optional=False, min_length=1, max_length=200)
                if i:
                    question["title"] = i
            elif v.selected == "de":
                self.cl.append("de")
                i = await self.TextInput(ctx, m, "Question description", "What should the description of the question be?", optional=True, min_length=1, max_length=1000)
                if i is True:
                    question["description"] = ""
                elif i:
                    question["description"] = i
            elif v.selected == "co":
                self.cl.append("co")
                question["colour"] = await self.ColourInput(ctx, m)
            elif v.selected == "re":
                question["required"] = not question["required"]
            elif v.selected == "mi":
                i = await self.NumberInput(ctx, m, "Minimum size", "What should the minimum size of the number be?", optional=False, min_size=1, max_size=1000)
                if i:
                    question["options"]["min"] = i
            elif v.selected == "ma":
                i = await self.NumberInput(ctx, m, "Maximum size", "What should the maximum size of the number be?", optional=False, min_size=1, max_size=1000)
                if i:
                    question["options"]["max"] = i
            elif v.selected == "ca":
                break
            elif v.selected == "ad":
                data["questions"].append(question)
                break
        return data

    async def newMultipleChoice(self, m, ctx, data, default=None):
        question = default or {"type": "multichoice", "title": "", "description": "", "colour": "red",
                               "options": {"min": 1, "max": 1, "options": {}}, "required": True, "question": True, "id": datetime.datetime.now().timestamp()}
        self.cl = []
        if default:
            self.cl = ["ti", "de", "co", "ao"]
        options = {}
        while True:
            warnings = []
            if question["title"] == "":
                warnings.append("A title is required")
            if not len(options):
                warnings.append("At least one option is required")
            v = self.handlers.createUI(ctx, [
                self.handlers.Button(cb="ti", label="Title", style=self.getCol("ti"), emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.title)),
                self.handlers.Button(cb="de", label="Description", style=self.getCol("de"), emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.description)),
                self.handlers.Button(cb="co", label="Colour", style=self.getCol("co"), emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.colour)),
                self.handlers.Button(cb="re", label="Required", style="secondary", emoji=self.bot.get_emoji(
                    getattr(self.emojis(idOnly=True).details.required, str(question["required"]).lower())
                )),
                self.handlers.Button(cb="ao", label="Add option", style="primary", emoji=self.bot.get_emoji(self.emojis(idOnly=True).question.new),
                                     disabled=(len(options) == 25)),
                self.handlers.Button(cb="eo", label="Edit option", style="primary", emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.edit),
                                     disabled=not len(options)),
                self.handlers.Button(cb="ro", label="Remove option", style="primary", emoji=self.bot.get_emoji(self.emojis(idOnly=True).question.delete),
                                     disabled=not len(options)),
                self.handlers.Button(cb="mi", label="Minimum choices", style="secondary", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.down)),
                self.handlers.Button(cb="ma", label="Maximum choices", style="secondary", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.up)),
                self.handlers.Button(cb="ca", label="Cancel", style="danger", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.cross)),
                self.handlers.Button(cb="ad", label="Save" if default else "Add", style="success", disabled=(not (bool(question["title"]) and len(options))),
                                     emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.tick))
            ])
            await m.edit(embed=discord.Embed(
                title=self.emojis().question.multichoice + " " + (question["title"] or ""),
                description=f"**Description:**\n> {question['description'] if 'description' in question else '*No description set*'}\n"
                            f"**Required:** {'Yes' if question['required'] else 'No'}\n"
                            f"**Options:**\n" + "\n".join([f"> {getattr(self.emojis().r, k)} **{va[0]}:** {va[1] or '*No description provided*'}" for k, va in options.items()]) +
                            f"\n**Chosen options:**\n> Minimum: {question['options']['min']}\n> Maximum: {question['options']['max']}",
                color=getattr(self.colours, question["colour"])
            ).set_footer(text=" - ".join(warnings)), view=v)
            await v.wait()
            if v.selected == "ti":
                self.cl.append("ti")
                i = await self.TextInput(ctx, m, "Question title", "What should the title of the question be?", optional=False, min_length=1, max_length=200)
                if i:
                    question["title"] = i
            elif v.selected == "de":
                self.cl.append("de")
                i = await self.TextInput(ctx, m, "Question description", "What should the description of the question be?", optional=True, min_length=1, max_length=1000)
                if i is True:
                    question["description"] = ""
                elif i:
                    question["description"] = i
            elif v.selected == "co":
                self.cl.append("co")
                question["colour"] = await self.ColourInput(ctx, m)
            elif v.selected == "re":
                question["required"] = not question["required"]
            elif v.selected == "mi":
                i = await self.NumberInput(ctx, m, "Minimum choices", "What should the minimum of choices be?",
                                           optional=False, min_size=0, max_size=min(len(options), question["options"]["max"]))
                if i:
                    question["options"]["min"] = i
            elif v.selected == "ma":
                i = await self.NumberInput(ctx, m, "Maximum choices", "What should the maximum amount of choices be?",
                                           optional=False, min_size=max(1, question["options"]["min"]), max_size=25)
                if i:
                    question["options"]["max"] = i
            elif v.selected == "ao":
                possible = list(range(25))
                for i in options.keys():
                    possible.remove(int(i))
                o = []
                for i in possible:
                    o.append(discord.SelectOption(value=str(i), label=icons[i], emoji=self.bot.get_emoji(getattr(self.emojis(idOnly=True).r, str(i)))))
                v = self.handlers.createUI(ctx, [
                    self.handlers.Select(id="icon", placeholder="Icon", autoaccept=True, options=o),
                    self.handlers.Button(cb="ca", label="Cancel", style="danger", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.cross))
                ])
                await m.edit(embed=discord.Embed(
                    title="Add option",
                    description="Select an icon to use",
                    color=self.colours.blue
                ), view=v)
                await v.wait()
                if v.selected:
                    continue
                if v.dropdowns["icon"]:
                    t = await self.TextInput(ctx, m, "Option title", "What should the title of the option be?", optional=False, min_length=1, max_length=50)
                    if not t:
                        continue
                    d = await self.TextInput(ctx, m, "Option description", "What should the description of the option be?", optional=True, min_length=1, max_length=100)
                    if d is None:
                        continue
                    elif d is True:
                        d = ""
                    options[v.dropdowns["icon"][0]] = (t, d)
            elif v.selected == "eo":
                o = []
                for k, v in options.items():
                    o.append(discord.SelectOption(value=str(k), label=k[0], description=v[1], emoji=self.bot.get_emoji(getattr(self.emojis(idOnly=True).r, str(k)))))
                v = self.handlers.createUI(ctx, [
                    self.handlers.Select(id="questions", placeholder="Question to edit", autoaccept=True, options=o),
                    self.handlers.Button(cb="ca", label="Cancel", style="danger", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.cross))
                ])
                await m.edit(embed=discord.Embed(
                    title="Edit option",
                    description="Select an option to edit",
                    color=self.colours.blue
                ), view=v)
                await v.wait()
                if v.selected:
                    continue
                if v.dropdowns["questions"]:
                    t = await self.TextInput(ctx, m, "Option title", "What should the title of the option be?", optional=False, min_length=1, max_length=50)
                    if not t:
                        continue
                    d = await self.TextInput(ctx, m, "Option description", "What should the description of the option be?", optional=True, min_length=1, max_length=100)
                    if d is None:
                        continue
                    elif d is True:
                        d = ""
                    options[v.dropdowns["questions"][0]] = (t, d)
            elif v.selected == "ro":
                o = []
                for k, v in options.items():
                    o.append(discord.SelectOption(value=str(k), label=k[0], description=v[1], emoji=self.bot.get_emoji(getattr(self.emojis(idOnly=True).r, str(k)))))
                v = self.handlers.createUI(ctx, [
                    self.handlers.Select(id="questions", placeholder="Questions to remove", autoaccept=True, options=o, max_values=len(options), min_values=1),
                    self.handlers.Button(cb="ca", label="Cancel", style="danger", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.cross))
                ])
                await m.edit(embed=discord.Embed(
                    title="Remove options",
                    description="Select which options to remove",
                    color=self.colours.blue
                ), view=v)
                await v.wait()
                if v.selected:
                    continue
                if v.dropdowns["questions"]:
                    for i in v.dropdowns["questions"]:
                        del options[str(i)]
            elif v.selected == "ca":
                break
            elif v.selected == "ad":
                question["options"]["options"] = options
                data["questions"].append(question)
                break
        return data

    async def newFileUpload(self, m, ctx, data, default=None):
        question = default or {"type": "fileupload", "title": "", "description": "", "colour": "red",
                               "options": {}, "required": True, "question": True, "id": datetime.datetime.now().timestamp()}
        self.cl = []
        if default:
            self.cl = ["ti", "de", "co"]
        while True:
            v = self.handlers.createUI(ctx, [
                self.handlers.Button(cb="ti", label="Title", style=self.getCol("ti"), emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.title)),
                self.handlers.Button(cb="de", label="Description", style=self.getCol("de"), emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.description)),
                self.handlers.Button(cb="co", label="Colour", style=self.getCol("co"), emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.colour)),
                self.handlers.Button(cb="re", label="Required", style="secondary", emoji=self.bot.get_emoji(
                    getattr(self.emojis(idOnly=True).details.required, str(question["required"]).lower())
                )),
                self.handlers.Button(cb="ca", label="Cancel", style="danger", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.cross)),
                self.handlers.Button(cb="ad", label="Save" if default else "Add", style="success", disabled=not bool(question["title"]),
                                     emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.tick))
            ])
            await m.edit(embed=discord.Embed(
                title=self.emojis().question.fileupload + " " + (question["title"] or ""),
                description=f"**Description:**\n> {question['description'] if 'description' in question else '*No description set*'}\n"
                            f"**Required:** {'Yes' if question['required'] else 'No'}\n",
                color=getattr(self.colours, question["colour"])
            ).set_footer(text=("" if question["title"] else "A title is required")), view=v)
            await v.wait()
            if v.selected == "ti":
                self.cl.append("ti")
                i = await self.TextInput(ctx, m, "Question title", "What should the title of the question be?", optional=False, min_length=1, max_length=200)
                if i:
                    question["title"] = i
            elif v.selected == "de":
                self.cl.append("de")
                i = await self.TextInput(ctx, m, "Question description", "What should the description of the question be?", optional=True, min_length=1, max_length=1000)
                if i is True:
                    question["description"] = ""
                elif i:
                    question["description"] = i
            elif v.selected == "co":
                self.cl.append("co")
                question["colour"] = await self.ColourInput(ctx, m)
            elif v.selected == "re":
                question["required"] = not question["required"]
            elif v.selected == "ca":
                break
            elif v.selected == "ad":
                data["questions"].append(question)
                break
        return data

    async def newTime(self, m, ctx, data, default=None):
        question = default or {"type": "time", "title": "", "description": "", "colour": "red",
                               "options": {}, "required": True, "question": True, "id": datetime.datetime.now().timestamp()}
        self.cl = []
        if default:
            self.cl = ["ti", "de", "co"]
        while True:
            v = self.handlers.createUI(ctx, [
                self.handlers.Button(cb="ti", label="Title", style=self.getCol("ti"), emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.title)),
                self.handlers.Button(cb="de", label="Description", style=self.getCol("de"), emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.description)),
                self.handlers.Button(cb="co", label="Colour", style=self.getCol("co"), emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.colour)),
                self.handlers.Button(cb="re", label="Required", style="secondary", emoji=self.bot.get_emoji(
                    getattr(self.emojis(idOnly=True).details.required, str(question["required"]).lower())
                )),
                self.handlers.Button(cb="ca", label="Cancel", style="danger", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.cross)),
                self.handlers.Button(cb="ad", label="Save" if default else "Add", style="success", disabled=not bool(question["title"]),
                                     emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.tick))
            ])
            await m.edit(embed=discord.Embed(
                title=self.emojis().question.time + " " + (question["title"] or ""),
                description=f"**Description:**\n> {question['description'] if 'description' in question else '*No description set*'}\n"
                            f"**Required:** {'Yes' if question['required'] else 'No'}\n",
                color=getattr(self.colours, question["colour"])
            ).set_footer(text=("" if question["title"] else "A title is required")), view=v)
            await v.wait()
            if v.selected == "ti":
                self.cl.append("ti")
                i = await self.TextInput(ctx, m, "Question title", "What should the title of the question be?", optional=False, min_length=1, max_length=200)
                if i:
                    question["title"] = i
            elif v.selected == "de":
                self.cl.append("de")
                i = await self.TextInput(ctx, m, "Question description", "What should the description of the question be?", optional=True, min_length=1, max_length=1000)
                if i is True:
                    question["description"] = ""
                elif i:
                    question["description"] = i
            elif v.selected == "co":
                self.cl.append("co")
                question["colour"] = await self.ColourInput(ctx, m)
            elif v.selected == "re":
                question["required"] = not question["required"]
            elif v.selected == "ca":
                break
            elif v.selected == "ad":
                data["questions"].append(question)
                break
        return data

    async def newDate(self, m, ctx, data, default=None):
        question = default or {"type": "date", "title": "", "description": "", "colour": "red",
                               "options": {}, "required": True, "question": True, "id": datetime.datetime.now().timestamp()}
        self.cl = []
        if default:
            self.cl = ["ti", "de", "co"]
        while True:
            v = self.handlers.createUI(ctx, [
                self.handlers.Button(cb="ti", label="Title", style=self.getCol("ti"), emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.title)),
                self.handlers.Button(cb="de", label="Description", style=self.getCol("de"), emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.description)),
                self.handlers.Button(cb="co", label="Colour", style=self.getCol("co"), emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.colour)),
                self.handlers.Button(cb="re", label="Required", style="secondary", emoji=self.bot.get_emoji(
                    getattr(self.emojis(idOnly=True).details.required, str(question["required"]).lower())
                )),
                self.handlers.Button(cb="ca", label="Cancel", style="danger", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.cross)),
                self.handlers.Button(cb="ad", label="Save" if default else "Add", style="success", disabled=not bool(question["title"]),
                                     emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.tick))
            ])
            await m.edit(embed=discord.Embed(
                title=self.emojis().question.date + " " + (question["title"] or ""),
                description=f"**Description:**\n> {question['description'] if 'description' in question else '*No description set*'}\n"
                            f"**Required:** {'Yes' if question['required'] else 'No'}\n",
                color=getattr(self.colours, question["colour"])
            ).set_footer(text=("" if question["title"] else "A title is required")), view=v)
            await v.wait()
            if v.selected == "ti":
                self.cl.append("ti")
                i = await self.TextInput(ctx, m, "Question title", "What should the title of the question be?", optional=False, min_length=1, max_length=200)
                if i:
                    question["title"] = i
            elif v.selected == "de":
                self.cl.append("de")
                i = await self.TextInput(ctx, m, "Question description", "What should the description of the question be?", optional=True, min_length=1, max_length=1000)
                if i is True:
                    question["description"] = ""
                elif i:
                    question["description"] = i
            elif v.selected == "co":
                self.cl.append("co")
                question["colour"] = await self.ColourInput(ctx, m)
            elif v.selected == "re":
                question["required"] = not question["required"]
            elif v.selected == "ca":
                break
            elif v.selected == "ad":
                data["questions"].append(question)
                break
        return data

    async def newTextDecoration(self, m, ctx, data, default=None):
        question = default or {"type": "text-decoration", "title": "", "description": "", "colour": "red", "options": {}, "question": False}
        self.cl = []
        if default:
            self.cl = ["ti", "de", "co"]
        while True:
            v = self.handlers.createUI(ctx, [
                self.handlers.Button(cb="ti", label="Title", style=self.getCol("ti"), emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.title)),
                self.handlers.Button(cb="de", label="Description", style=self.getCol("de"), emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.description)),
                self.handlers.Button(cb="co", label="Colour", style=self.getCol("co"), emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.colour)),
                self.handlers.Button(cb="ca", label="Cancel", style="danger", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.cross)),
                self.handlers.Button(cb="ad", label="Save" if default else "Add", style="success", disabled=not bool(question["title"]),
                                     emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.tick))
            ])
            await m.edit(embed=discord.Embed(
                title=self.emojis().question.decoration.text + " " + (question["title"] or ""),
                description=f"**Description:**\n> {question['description'] if question['description'] else '*No description set*'}\n",
                color=getattr(self.colours, question["colour"])
            ).set_footer(text=("" if question["title"] else "A title is required")), view=v)
            await v.wait()
            if v.selected == "ti":
                self.cl.append("ti")
                i = await self.TextInput(ctx, m, "Decoration title", "What should the title of the decoration be?", optional=False, min_length=1, max_length=200)
                if i:
                    question["title"] = i
            elif v.selected == "de":
                self.cl.append("de")
                i = await self.TextInput(ctx, m, "Decoration description", "What should the description of the decoration be?", optional=True, min_length=1, max_length=1000)
                if i is True:
                    question["description"] = ""
                elif i:
                    question["description"] = i
            elif v.selected == "co":
                self.cl.append("co")
                question["colour"] = await self.ColourInput(ctx, m)
            elif v.selected == "ca":
                break
            elif v.selected == "ad":
                data["questions"].append(question)
                break
        return data

    async def newImageDecoration(self, m, ctx, data, default=None):
        question = default or {"type": "image-decoration", "title": "", "description": "", "colour": "red", "options": {"url": ""}, "question": False}
        self.cl = []
        if default:
            self.cl = ["ti", "de", "co", "ur"]
        while True:
            d = bool(question["title"]) and bool(question["options"]["url"])
            warnings = []
            if not question["title"]:
                warnings.append("A title is required")
            if not question["options"]["url"]:
                warnings.append("An image URL is required")
            v = self.handlers.createUI(ctx, [
                self.handlers.Button(cb="ti", label="Title", style=self.getCol("ti"), emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.title)),
                self.handlers.Button(cb="de", label="Description", style=self.getCol("de"), emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.description)),
                self.handlers.Button(cb="co", label="Colour", style=self.getCol("co"), emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.colour)),
                self.handlers.Button(cb="ur", label="Image URL", style=self.getCol("ur"), emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.url)),
                self.handlers.Button(cb="ca", label="Cancel", style="danger", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.cross)),
                self.handlers.Button(cb="ad", label="Save" if default else "Add", style="success", disabled=not bool(question["title"]),
                                     emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.tick))
            ])
            await m.edit(embed=discord.Embed(
                title=self.emojis().question.decoration.image + " " + (question["title"] or ""),
                description=f"**Description:**\n> {question['description'] if question['description'] else '*No description set*'}\n",
                color=getattr(self.colours, question["colour"])
            ).set_footer(
                text=" - ".join(warnings)
            ).set_thumbnail(
                url=question["options"]["url"]
            ), view=v)
            await v.wait()
            if v.selected == "ti":
                self.cl.append("ti")
                i = await self.TextInput(ctx, m, "Decoration title", "What should the title of the decoration be?", optional=False, min_length=1, max_length=200)
                if i:
                    question["title"] = i
            elif v.selected == "de":
                self.cl.append("de")
                i = await self.TextInput(ctx, m, "Decoration description", "What should the description of the decoration be?", optional=True, min_length=1, max_length=1000)
                if i is True:
                    question["description"] = ""
            elif v.selected == "ur":
                self.cl.append("ur")
                i = await self.TextInput(ctx, m, "Image URL", "What is the URL of the image to use?", optional=False, min_length=1, max_length=1500)
                if i:
                    question["options"]["url"] = i
            elif v.selected == "ca":
                break
            elif v.selected == "ad":
                data["questions"].append(question)
                break
        return data

    async def newURLDecoration(self, m, ctx, data, default=None):
        question = default or {"type": "url-decoration", "title": "", "description": "", "colour": "red", "options": {"url": ""}, "question": False}
        self.cl = []
        if default:
            self.cl = ["ti", "de", "co", "ur"]
        while True:
            d = bool(question["title"]) and bool(question["options"]["url"])
            url = question["options"]["url"]
            warnings = []
            if not question["title"]:
                warnings.append("A title is required")
            if isinstance(validators.url(url), validators.ValidationFailure):
                warnings.append("That URL is invalid")
                url = "https://example.com"
            v = self.handlers.createUI(ctx, [
                self.handlers.Button(cb="ti", label="Title", style=self.getCol("ti"), emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.title)),
                self.handlers.Button(cb="de", label="Description", style=self.getCol("de"), emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.description)),
                self.handlers.Button(cb="co", label="Colour", style=self.getCol("co"), emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.colour)),
                self.handlers.Button(cb="ur", label="URL", style=self.getCol("ur"), emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.url)),
                self.handlers.Button(cb="ca", label="Cancel", style="danger", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.cross)),
                self.handlers.Button(cb="ad", label="Save" if default else "Add", style="success", disabled=not bool(question["title"]),
                                     emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.tick)),
                self.handlers.Button(label="Test URL", style="link", url=url)
            ])
            await m.edit(embed=discord.Embed(
                title=self.emojis().question.decoration.url + " " + (question["title"] or ""),
                description=f"**Description:**\n> {question['description'] if question['description'] else '*No description set*'}\n"
                            f"**URL:** {url}",
                color=getattr(self.colours, question["colour"])
            ).set_footer(text=" - ".join(warnings)), view=v)
            await v.wait()
            if v.selected == "ti":
                self.cl.append("ti")
                i = await self.TextInput(ctx, m, "Decoration title", "What should the title of the decoration be?", optional=False, min_length=1, max_length=200)
                if i:
                    question["title"] = i
            elif v.selected == "de":
                self.cl.append("de")
                i = await self.TextInput(ctx, m, "Decoration description", "What should the description of the decoration be?", optional=True, min_length=1, max_length=1000)
                if i is True:
                    question["description"] = " "
                elif i:
                    question["description"] = i
            elif v.selected == "ur":
                self.cl.append("ur")
                i = await self.TextInput(ctx, m, "URL", "Where should the URL take you?", optional=True, min_length=1, max_length=1500)
                if i is True:
                    question["options"]["url"] = ""
                elif i:
                    if not (i.startswith("http://") or i.startswith("https://")):
                        i = "https://" + i
                    question["options"]["url"] = i
            elif v.selected == "co":
                self.cl.append("co")
                question["colour"] = await self.ColourInput(ctx, m)
            elif v.selected == "ca":
                break
            elif v.selected == "ad":
                if not question["description"]:
                    question["description"] = " "
                question["options"]["url"] = url
                data["questions"].append(question)
                break
        return data

    async def removeQuestion(self, m, ctx, data):
        options = []
        count = 0
        for question in data["questions"]:
            if question["question"]:
                emoji = getattr(self.emojis(idOnly=True).question, question["type"])
            else:
                emoji = getattr(self.emojis(idOnly=True).question.decoration, question["type"].split("-")[0])
            options.append(discord.SelectOption(
                value=str(count),
                label=question["title"],
                description=question["description"].strip() or "*No description set*",
                emoji=self.bot.get_emoji(emoji)
            ))
            count += 1
        v = self.handlers.createUI(ctx, [
            self.handlers.Button(cb="ca", label="Cancel", style="danger", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.cross)),
            self.handlers.Select(id="question", placeholder="Questions to remove", autoaccept=True, options=options, min_values=1, max_values=len(data["questions"]))
        ])
        await m.edit(embed=m.embeds[0], view=v)
        await v.wait()
        questions = []
        if v.dropdowns:
            count = 0
            for i in data["questions"]:
                if str(count) not in v.dropdowns["question"]:
                    questions.append(i)
                count += 1
            data["questions"] = questions
        return data

    async def editQuestion(self, m, ctx, data):
        options = []
        count = 0
        for question in data["questions"]:
            if question["question"]:
                emoji = getattr(self.emojis(idOnly=True).question, question["type"])
            else:
                emoji = getattr(self.emojis(idOnly=True).question.decoration, question["type"].split("-")[0])
            options.append(discord.SelectOption(
                value=str(count),
                label=question["title"],
                description=question["description"].strip() or "*No description set*",
                emoji=self.bot.get_emoji(emoji)
            ))
            count += 1
        v = self.handlers.createUI(ctx, [
            self.handlers.Select(id="question", placeholder="Question to edit", autoaccept=True, options=options),
            self.handlers.Button(cb="ca", label="Cancel", style="danger", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.cross))
        ])
        await m.edit(embed=m.embeds[0], view=v)
        await v.wait()
        if v.dropdowns:
            if v.dropdowns["question"]:
                if data["questions"][int(v.dropdowns["question"][0])]["type"] == "text":
                    d = await self.newText(m, ctx, data, default=data["questions"][int(v.dropdowns["question"][0])])
                elif data["questions"][int(v.dropdowns["question"][0])]["type"] == "number":
                    d = await self.newNumber(m, ctx, data, default=data["questions"][int(v.dropdowns["question"][0])])
                elif data["questions"][int(v.dropdowns["question"][0])]["type"] == "multichoice":
                    d = await self.newMultipleChoice(m, ctx, data, default=data["questions"][int(v.dropdowns["question"][0])])
                elif data["questions"][int(v.dropdowns["question"][0])]["type"] == "fileupload":
                    d = await self.newFileUpload(m, ctx, data, default=data["questions"][int(v.dropdowns["question"][0])])
                elif data["questions"][int(v.dropdowns["question"][0])]["type"] == "time":
                    d = await self.newTime(m, ctx, data, default=data["questions"][int(v.dropdowns["question"][0])])
                elif data["questions"][int(v.dropdowns["question"][0])]["type"] == "date":
                    d = await self.newDate(m, ctx, data, default=data["questions"][int(v.dropdowns["question"][0])])
                elif data["questions"][int(v.dropdowns["question"][0])]["type"] == "text-decoration":
                    d = await self.newTextDecoration(m, ctx, data, default=data["questions"][int(v.dropdowns["question"][0])])
                elif data["questions"][int(v.dropdowns["question"][0])]["type"] == "image-decoration":
                    d = await self.newImageDecoration(m, ctx, data, default=data["questions"][int(v.dropdowns["question"][0])])
                elif data["questions"][int(v.dropdowns["question"][0])]["type"] == "url-decoration":
                    d = await self.newURLDecoration(m, ctx, data, default=data["questions"][int(v.dropdowns["question"][0])])
            data["questions"][int(v.dropdowns["question"][0])] = d["questions"][-1]
            data["questions"].pop(-1)
        return data

    async def editDetails(self, m, ctx, data):
        while True:
            v = self.handlers.createUI(ctx, [
                self.handlers.Button(cb="ba", label="Back", style="success", emoji=self.bot.get_emoji(self.emojis(idOnly=True).control.left)),
                self.handlers.Button(cb="ti", label="Title", style="secondary", emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.title)),
                self.handlers.Button(cb="de", label="Description", style="secondary", emoji=self.bot.get_emoji(self.emojis(idOnly=True).details.description)),
                self.handlers.Button(cb="an", label="Anonymous", style="secondary", emoji=(
                    self.bot.get_emoji(getattr(self.emojis(idOnly=True).meta.anon, str(data["anonymous"]).lower()))
                )),
                self.handlers.Button(cb="aa", label="Automatically apply roles", style="secondary", emoji=(
                    self.bot.get_emoji(getattr(self.emojis(idOnly=True).meta.auto, str(data["auto_accept"]).lower()))
                )),
                self.handlers.Button(cb="rr", label="Required roles", style="secondary", emoji=self.bot.get_emoji(self.emojis(idOnly=True).meta.roles.required)),
                self.handlers.Button(cb="dr", label="Disallowed roles", style="secondary", emoji=self.bot.get_emoji(self.emojis(idOnly=True).meta.roles.disallowed)),
                self.handlers.Button(cb="gr", label="Given roles", style="secondary", emoji=self.bot.get_emoji(self.emojis(idOnly=True).meta.roles.given)),
                self.handlers.Button(cb="re", label="Removed roles", style="secondary", emoji=self.bot.get_emoji(self.emojis(idOnly=True).meta.roles.removed))
            ])
            e = discord.Embed(
                title=data["name"],
                description=f"**Description:**\n> {data['description']}\n"
                            f"**Anonymous:** {'Yes' if data['anonymous'] else 'No'}\n"
                            f"**Auto apply roles:** {'Yes' if data['auto_accept'] else 'No'}\n"
                            f"**Required roles:**\n> {' '.join([ctx.guild.get_role(int(r)).mention for r in data['required_roles']])}\n"
                            f"**Disallowed roles:**\n> {' '.join([ctx.guild.get_role(int(r)).mention for r in data['disallowed_roles']])}\n"
                            f"**Given roles:**\n> {' '.join([ctx.guild.get_role(int(r)).mention for r in data['given_roles']])}\n"
                            f"**Removed roles:**\n> {' '.join([ctx.guild.get_role(int(r)).mention for r in data['removed_roles']])}\n*Click Back to save*",
                color=self.colours.blue
            )
            await m.edit(embed=e, view=v)
            await v.wait()
            if v.selected == "ti":
                i = await self.TextInput(ctx, m, title="Title", description="Enter the new title", max_length=50)
                if i:
                    data["name"] = i
            elif v.selected == "de":
                i = await self.TextInput(ctx, m, title="Description", description="Enter the new description", optional=True, max_length=100)
                if i:
                    data["description"] = i
            elif v.selected == "an":
                data["anonymous"] = not data["anonymous"]
            elif v.selected == "aa":
                data["auto_accept"] = not data["auto_accept"]
            elif v.selected == "rr":
                roles = await self.RoleInput(ctx, m, "Required roles", "What roles are required to use this form", optional=True)
                if roles is True:
                    data["required_roles"] = []
                elif roles:
                    data["required_roles"] = roles
            elif v.selected == "dr":
                roles = await self.RoleInput(ctx, m, "Disallowed roles", "What roles are not allowed to use this form", optional=True)
                if roles is True:
                    data["disallowed_roles"] = []
                elif roles:
                    data["disallowed_roles"] = roles
            elif v.selected == "gr":
                roles = await self.RoleInput(ctx, m, "Given roles", "What roles should been given to users when the form is accepted", optional=True)
                if roles is True:
                    data["given_roles"] = []
                elif roles:
                    data["given_roles"] = roles
            elif v.selected == "re":
                roles = await self.RoleInput(ctx, m, "Removed roles", "What roles should be removed from users when the form is accepted", optional=True)
                if roles is True:
                    data["removed_roles"] = []
                elif roles:
                    data["removed_roles"] = roles
            elif v.selected == "ba":
                return data

    async def saveForm(self, ctx, data, overwrite=False):
        from config import config
        entry = await self.db.get(ctx.guild.id)
        if not overwrite:
            newdata = entry.data + [data]
        else:
            newdata = entry.data
            for i, form in enumerate(newdata):
                if form["id"] == data["id"]:
                    newdata[i] = data
        await entry.update(data=newdata)
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{config.rsm}/clicksforms/" + ("edit" if overwrite else "create"), json={
                "guild_id": ctx.guild.id,
                "created_by": ctx.author.id,
                "questions": len(data["questions"]),
                "name": data["name"],
                "auth": config.rsmToken
            }) as _:
                pass
        return


def setup(bot):
    bot.add_cog(New(bot))
