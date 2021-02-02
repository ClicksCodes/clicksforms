import discord
import asyncio
import copy
import re
from datetime import datetime
from discord.ext import commands

from cogs.consts import *


class New(commands.Cog):
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
    @commands.guild_only()
    async def create(self, ctx):
        m = await ctx.send(embed=loadingEmbed)
        formData = {
            "meta": {
                "type": "form",  # form quiz
                "active": True,  # If users can apply
                "anonymous": False,  # If the applicant is shown
                "invoke": "apply",  # The command to apply
                "guild": ctx.guild.id,  # The server the application is for
                "created_by": ctx.author.id,  # Who made the application
                "name": "New Application",  # The name of the application
                "description": "The default application",  # The description of the form
                "required_roles": [],  # You need these roles to apply
                "disallowed_roles": [],  # You cannot apply with these roles
                "given_roles": [],  # Roles given once accepted
                "removed_roles": []  # Roles removed once accepted
            },
            "questions": [
                {
                    "question": True,
                    "name": "Default question",  # The title of a question
                    "description": "The default question for an application",  # The description of a question
                    "colour": Colours.orange,  # The colour of the embed
                    "type": "text",  # text number multiplechoice tickbox file date time  |  header text image link
                    "required": True,  # If the question is required or not
                    "question_specific": {}  # Length requirements, validation, multiple choice options...
                }
            ]
        }

        while True:
            desc = f"**Description:**\n> {formData['meta']['description']}\n"
            desc += f"**Command to apply:** `{ctx.prefix}{formData['meta']['invoke']}`\n\n"

            desc += f"{self.bot.get_emoji(Emojis.main.new)} New question\n" \
                    f"{self.bot.get_emoji(Emojis.main.remove)} Remove question\n" \
                    f"{self.bot.get_emoji(Emojis.main.meta)} Edit application details\n" \
                    f"{self.bot.get_emoji(Emojis.main.save)} Save application\n" \
                    f"{self.bot.get_emoji(Emojis.cross)} Exit without saving\n\n" \
                    f"**Questions:** ({len(formData['questions'])})"

            embed = discord.Embed(
                title=formData['meta']['name'],
                description=desc,
                color=Colours.blue
            )

            x = 0
            for question in formData['questions']:
                if question['question']:
                    x += 1
                    embed.add_field(
                        name=f"{self.bot.get_emoji(getattr(Emojis.types, question['type']))} {x}. {str(question['name'])[:200]}",
                        value=str(question['description'])[:1000],
                        inline=True
                    )
                else:
                    embed.add_field(
                        name=f"{self.bot.get_emoji(getattr(Emojis.types, question['type']))} Decoration",
                        value=str(question['type'])[8:].capitalize(),
                        inline=True
                    )

            await m.edit(embed=embed)
            m = await ctx.channel.fetch_message(m.id)
            for r in [
                805445243977596980,  # New
                805445244329263144,  # Remove
                805445244224536586,  # Meta
                805445244191637515,  # Save
                805431640402034750   # Close
            ]:
                if r not in [r.emoji.id for r in m.reactions]:
                    await m.add_reaction(self.bot.get_emoji(r))
            reaction = None
            try:
                done, pending = await asyncio.wait(
                    [
                        self.bot.wait_for('reaction_add', timeout=120, check=lambda emoji, user: emoji.message.id == m.id and user.id == ctx.author.id),
                        self.bot.wait_for('reaction_remove', timeout=120, check=lambda emoji, user: emoji.message.id == m.id and user.id == ctx.author.id),
                        self.bot.wait_for('message', timeout=120, check=lambda message: message.author.id == ctx.author.id)
                    ],
                    return_when=asyncio.FIRST_COMPLETED
                )
            except asyncio.TimeoutError:
                break

            try:
                reaction = copy.copy(done)
                response, _ = reaction.pop().result()
                response = response[0]
            except TypeError:
                response = next(iter(done)).result()
            except asyncio.TimeoutError:
                break

            for future in done:
                future.exception()
            for future in pending:
                future.cancel()

            if isinstance(response, tuple):
                response = response[0]
                await m.remove_reaction(response.emoji, ctx.author)
                if response.emoji.name.lower() == "newquestion":
                    formData = await self.newQuestion(m, ctx, formData)
                elif response.emoji.name.lower() == "removequestion":
                    formData = await self.removeQuestion(m, ctx, formData)
                elif response.emoji.name.lower() == "editmeta":
                    formData = await self.editMeta(m, ctx, formData)
                    pass
                elif response.emoji.name.lower() == "save":
                    formData["meta"]["active"] = False
                    # self.pushData(ctx, formData)
                    await ctx.send(formData)
                    break
                else:
                    break

            elif isinstance(response, discord.message.Message):
                pass

        await m.clear_reactions()
        await m.edit(embed=discord.Embed(
            title="Application closed",
            description="You have stopped editing this application",
            color=Colours.red
        ))

    async def editMeta(self, m, ctx, formData):
        while True:
            desc = f"**Title:** {formData['meta']['name']}\n" \
                   f"**Description:**\n> {formData['meta']['description']}\n"
            await m.clear_reactions()
            for r in [
                Emojis.left,
                Emojis.features.title,
                Emojis.features.description
            ]:
                await m.add_reaction(self.bot.get_emoji(r))
            await m.edit(embed=discord.Embed(
                title="Editing application details",
                description=desc,
                color=Colours.green
            ))
            try:
                done, pending = await asyncio.wait(
                    [
                        self.bot.wait_for('reaction_add', timeout=120, check=lambda emoji, user: emoji.message.id == m.id and user.id == ctx.author.id),
                        self.bot.wait_for('reaction_remove', timeout=120, check=lambda emoji, user: emoji.message.id == m.id and user.id == ctx.author.id)
                    ],
                    return_when=asyncio.FIRST_COMPLETED
                )
            except asyncio.TimeoutError:
                return formData

            try:
                reaction = copy.copy(done)
                response, _ = reaction.pop().result()
            except asyncio.TimeoutError:
                return formData

            for future in done:
                future.exception()
            for future in pending:
                future.cancel()

            name = response.emoji.name.lower()
            await m.clear_reactions()
            if name == "left":
                return formData
            elif name == "qtitle":
                text = await self.getText(
                    m,
                    f"{self.bot.get_emoji(Emojis.features.title)} What should the application title be?",
                    "This is the name of the application. Type `cancel` to cancel.",
                    ctx.author
                )
                if not text:
                    continue
                formData['meta']['name'] = text
            elif name == "qdescription":
                text = await self.getText(
                    m,
                    f"{self.bot.get_emoji(Emojis.features.description)} What should the application description be?",
                    "This is the explanation of the application. Type `cancel` to cancel.",
                    ctx.author
                )
                if not text:
                    continue
                formData['meta']['description'] = text

    async def newQuestion(self, m, ctx, formData):
        await m.clear_reactions()
        desc = f"Select a question type\n\n" \
               f"{self.bot.get_emoji(Emojis.types.text)} **Text** - A simple text response\n" \
               f"{self.bot.get_emoji(Emojis.types.number)} **Number** - A single number\n" \
               f"{self.bot.get_emoji(Emojis.types.multichoice)} **Multiple choice** - Choose from a list of reactions\n" \
               f"{self.bot.get_emoji(Emojis.types.tickbox)} **Tickboxes** - Choose any amount of reactions\n" \
               f"{self.bot.get_emoji(Emojis.types.fileupload)} **File upload** - Send a file or image (May not work if file is deleted)\n" \
               f"{self.bot.get_emoji(Emojis.types.date)} **Date** - A specific date\n" \
               f"{self.bot.get_emoji(Emojis.types.time)} **Time** - A specific time\n" \
               f"{self.bot.get_emoji(Emojis.types.decoration)} **A decoration** - A section header, some text, or image\n" \
               f"{self.bot.get_emoji(Emojis.cross)} **Cancel**\n"

        await m.edit(embed=discord.Embed(
            title="New question",
            description=desc,
            color=Colours.red
        ))
        for r in [
            Emojis.types.text,
            Emojis.types.number,
            Emojis.types.multichoice,
            Emojis.types.tickbox,
            Emojis.types.fileupload,
            Emojis.types.date,
            Emojis.types.time,
            Emojis.types.decoration,
            Emojis.cross
        ]:
            await m.add_reaction(self.bot.get_emoji(r))

        try:
            done, pending = await asyncio.wait(
                [
                    self.bot.wait_for('reaction_add', timeout=120, check=lambda emoji, user: emoji.message.id == m.id and user.id == ctx.author.id),
                    self.bot.wait_for('reaction_remove', timeout=120, check=lambda emoji, user: emoji.message.id == m.id and user.id == ctx.author.id)
                ],
                return_when=asyncio.FIRST_COMPLETED
            )
        except asyncio.TimeoutError:
            return formData

        try:
            reaction = copy.copy(done)
            response, _ = reaction.pop().result()
        except asyncio.TimeoutError:
            return formData

        for future in done:
            future.exception()
        for future in pending:
            future.cancel()

        name = response.emoji.name.lower()
        await m.clear_reactions()
        if name == "text":
            title = await self.getText(
                m,
                f"{self.bot.get_emoji(Emojis.features.title)} What should the question title be?",
                "This is the text that appears at the top of this question. Type `cancel` to cancel.",
                ctx.author
            )
            if not title:
                return formData
            description = await self.getText(
                m,
                f"{self.bot.get_emoji(Emojis.features.description)} What should the question description be?",
                "This is the text that appears below the title to give more information. Type `cancel` to cancel.",
                ctx.author
            )
            if not desc:
                return formData
            colour = await self.getColour(m, ctx.author)
            if not colour:
                return formData

            formData['questions'].append({
                "question": True,
                "name": title,
                "description": description,
                "colour": colour,
                "type": "text",
                "required": True,
                "question_specific": {}
            })
            return formData
        elif name == "number":
            title = await self.getText(
                m,
                f"{self.bot.get_emoji(Emojis.features.title)} What should the question title be?",
                "This is the text that appears at the top of this question. Type `cancel` to cancel.",
                ctx.author
            )
            if not title:
                return formData
            description = await self.getText(
                m,
                f"{self.bot.get_emoji(Emojis.features.description)} What should the question description be?",
                "This is the text that appears below the title to give more information. Type `cancel` to cancel.",
                ctx.author
            )
            if not desc:
                return formData
            colour = await self.getColour(m, ctx.author)
            if not colour:
                return formData

            formData['questions'].append({
                "question": True,
                "name": title,
                "description": description,
                "colour": colour,
                "type": "number",
                "required": True,
                "question_specific": {}
            })
            return formData

        elif name == "multiplechoice":
            title = await self.getText(
                m,
                f"{self.bot.get_emoji(Emojis.features.title)} What should the question title be?",
                "This is the text that appears at the top of this question. Type `cancel` to cancel.",
                ctx.author
            )
            if not title:
                return formData
            description = await self.getText(
                m,
                f"{self.bot.get_emoji(Emojis.features.description)} What should the question description be?",
                "This is the text that appears below the title to give more information. Type `cancel` to cancel.",
                ctx.author
            )
            if not desc:
                return formData
            colour = await self.getColour(m, ctx.author)
            if not colour:
                return formData
            options = await self.getEmojis(m, ctx.author)
            if options == {}:
                return formData
            formData['questions'].append({
                "question": True,
                "name": title,
                "description": description,
                "colour": colour,
                "type": "multichoice",
                "required": True,
                "question_specific": options
            })
            return formData

        elif name == "checkbox":
            title = await self.getText(
                m,
                f"{self.bot.get_emoji(Emojis.features.title)} What should the question title be?",
                "This is the text that appears at the top of this question. Type `cancel` to cancel.",
                ctx.author
            )
            if not title:
                return formData
            description = await self.getText(
                m,
                f"{self.bot.get_emoji(Emojis.features.description)} What should the question description be?",
                "This is the text that appears below the title to give more information. Type `cancel` to cancel.",
                ctx.author
            )
            if not desc:
                return formData
            colour = await self.getColour(m, ctx.author)
            if not colour:
                return formData
            options = await self.getEmojis(m, ctx.author)
            if options == {}:
                return formData
            formData['questions'].append({
                "question": True,
                "name": title,
                "description": description,
                "colour": colour,
                "type": "tickbox",
                "required": True,
                "question_specific": options
            })
            return formData

        elif name == "fileupload":
            title = await self.getText(
                m,
                f"{self.bot.get_emoji(Emojis.features.title)} What should the question title be?",
                "This is the text that appears at the top of this question. Type `cancel` to cancel.",
                ctx.author
            )
            if not title:
                return formData
            description = await self.getText(
                m,
                f"{self.bot.get_emoji(Emojis.features.description)} What should the question description be?",
                "This is the text that appears below the title to give more information. Type `cancel` to cancel.",
                ctx.author
            )
            if not desc:
                return formData
            colour = await self.getColour(m, ctx.author)
            if not colour:
                return formData
            formData['questions'].append({
                "question": True,
                "name": title,
                "description": description,
                "colour": colour,
                "type": "fileupload",
                "required": True,
                "question_specific": {}
            })
            return formData
        elif name == "date":
            title = await self.getText(
                m,
                f"{self.bot.get_emoji(Emojis.features.title)} What should the question title be?",
                "This is the text that appears at the top of this question. Type `cancel` to cancel.",
                ctx.author
            )
            if not title:
                return formData
            description = await self.getText(
                m,
                f"{self.bot.get_emoji(Emojis.features.description)} What should the question description be?",
                "This is the text that appears below the title to give more information. Type `cancel` to cancel.",
                ctx.author
            )
            if not desc:
                return formData
            colour = await self.getColour(m, ctx.author)
            if not colour:
                return formData
            formData['questions'].append({
                "question": True,
                "name": title,
                "description": description,
                "colour": colour,
                "type": "date",
                "required": True,
                "question_specific": {}
            })
            return formData
        elif name == "time":
            title = await self.getText(
                m,
                f"{self.bot.get_emoji(Emojis.features.title)} What should the question title be?",
                "This is the text that appears at the top of this question. Type `cancel` to cancel.",
                ctx.author
            )
            if not title:
                return formData
            description = await self.getText(
                m,
                f"{self.bot.get_emoji(Emojis.features.description)} What should the question description be?",
                "This is the text that appears below the title to give more information. Type `cancel` to cancel.",
                ctx.author
            )
            if not desc:
                return formData
            colour = await self.getColour(m, ctx.author)
            if not colour:
                return formData
            formData['questions'].append({
                "question": True,
                "name": title,
                "description": description,
                "colour": colour,
                "type": "time",
                "required": True,
                "question_specific": {}
            })
            return formData
        elif name == "decoration":
            await m.clear_reactions()
            await m.edit(embed=discord.Embed(
                title="Select a decoration",
                description=f"{self.bot.get_emoji(Emojis.left)} **Cancel**\n"
                            f"{self.bot.get_emoji(Emojis.decorations.header)} **Section** - A header for a section\n"
                            f"{self.bot.get_emoji(Emojis.decorations.text)} **Text** - A piece of information about the next question\n"
                            f"{self.bot.get_emoji(Emojis.decorations.image)} **Image** - Shows an image and caption\n"
                            f"{self.bot.get_emoji(Emojis.decorations.link)} **Link** - Clickable text for a link\n",
                color=Colours.orange
            ))
            for r in [
                Emojis.left,
                Emojis.decorations.header,
                Emojis.decorations.text,
                Emojis.decorations.image,
                Emojis.decorations.link
            ]:
                await m.add_reaction(self.bot.get_emoji(r))
            done, pending = await asyncio.wait(
                [
                    self.bot.wait_for('reaction_add', timeout=120, check=lambda emoji, user: emoji.message.id == m.id and user.id == ctx.author.id),
                    self.bot.wait_for('reaction_remove', timeout=120, check=lambda emoji, user: emoji.message.id == m.id and user.id == ctx.author.id)
                ],
                return_when=asyncio.FIRST_COMPLETED
            )

            try:
                response, _ = done.pop().result()
            except asyncio.TimeoutError:
                await m.clear_reactions()
                return formData

            for future in done:
                future.exception()
            for future in pending:
                future.cancel()

            if isinstance(response, discord.Reaction):
                emoji = response.emoji.name.lower()
                await m.clear_reactions()
                if emoji == "sectionheader":
                    title = await self.getText(
                        m,
                        f"{self.bot.get_emoji(Emojis.features.title)} What should the section title be?",
                        "This is the text that appears before the next question. Type `cancel` to cancel.",
                        ctx.author
                    )
                    if not title:
                        return formData
                    description = await self.getText(
                        m,
                        f"{self.bot.get_emoji(Emojis.features.description)} What should the section description be?",
                        "This is the text that appears below the section title to give more information. Type `cancel` to cancel.",
                        ctx.author
                    )
                    if not description:
                        return formData
                    colour = await self.getColour(m, ctx.author)
                    if not colour:
                        return formData
                    formData['questions'].append({
                        "question": False,
                        "name": title,
                        "description": description,
                        "colour": colour,
                        "type": "special_section"
                    })
                    return formData
                elif emoji == "sectiontext":
                    description = await self.getText(
                        m,
                        f"{self.bot.get_emoji(Emojis.features.description)} What should the text say?",
                        "This is the text that is shown between questions. Type `cancel` to cancel.",
                        ctx.author
                    )
                    if not description:
                        return formData
                    colour = await self.getColour(m, ctx.author)
                    if not colour:
                        return formData
                    formData['questions'].append({
                        "question": False,
                        "description": description,
                        "colour": colour,
                        "type": "special_text"
                    })
                    return formData
                elif emoji == "sectionimage":
                    title = await self.getText(
                        m,
                        f"{self.bot.get_emoji(Emojis.features.description)} What should the title be?",
                        "This is the text that is shown at the top of the embed. Type `cancel` to cancel.",
                        ctx.author
                    )
                    if not title:
                        return formData
                    description = await self.getText(
                        m,
                        f"{self.bot.get_emoji(Emojis.features.description)} What should the image caption be?",
                        "This is the text that is shown above the image. Type `cancel` to cancel.",
                        ctx.author
                    )
                    if not description:
                        return formData
                    image = await self.getText(
                        m,
                        f"{self.bot.get_emoji(Emojis.features.description)} What should the image be?",
                        "Please send the url of the image. Type `cancel` to cancel.",
                        ctx.author,
                        url=True
                    )
                    if not image:
                        return formData
                    colour = await self.getColour(m, ctx.author)
                    if not colour:
                        return formData
                    formData['questions'].append({
                        "question": False,
                        "name": title,
                        "caption": description,
                        "url": image,
                        "colour": colour,
                        "type": "special_image"
                    })
                    return formData
                elif emoji == "sectionlink":
                    title = await self.getText(
                        m,
                        f"{self.bot.get_emoji(Emojis.features.description)} What the title be?",
                        "This is the text that appears at the top of the embed. Type `cancel` to cancel.",
                        ctx.author
                    )
                    if not title:
                        return formData
                    description = await self.getText(
                        m,
                        f"{self.bot.get_emoji(Emojis.features.description)} What should the text say?",
                        "This is the text that can be clicked to open the link. Type `cancel` to cancel.",
                        ctx.author
                    )
                    if not description:
                        return formData
                    link = await self.getText(
                        m,
                        f"{self.bot.get_emoji(Emojis.features.description)} What should the link be?",
                        "This is the link you are taken to when the text is clicked. Type `cancel` to cancel.",
                        ctx.author,
                        url=True
                    )
                    if not link:
                        return formData
                    colour = await self.getColour(m, ctx.author)
                    if not colour:
                        return formData
                    formData['questions'].append({
                        "question": False,
                        "name": title,
                        "text": description,
                        "url": link,
                        "colour": colour,
                        "type": "special_link"
                    })
                    return formData

        await m.clear_reactions()
        return formData

    async def removeQuestion(self, m, ctx, formData):
        embed = discord.Embed(
            title="Delete question",
            description="Enter the number of the question you wish to delete:",
            color=Colours.blue
        )

        x = 0
        for question in formData['questions']:
            x += 1
            embed.add_field(
                name=f"{x}. {str(question['name'])[:250]}",
                value=str(question['description'])[:1000],
                inline=True
            )
        await m.edit(embed=embed)
        for r in [
            805445243977596980,  # New
            805445244329263144,  # Remove
            805445244224536586,  # Meta
            805445244191637515   # Save
        ]:
            if r not in [r.emoji.id for r in m.reactions]:
                await m.remove_reaction(self.bot.get_emoji(r), ctx.me)

        reaction = None
        done, pending = await asyncio.wait(
            [
                self.bot.wait_for('reaction_add', timeout=120, check=lambda emoji, user: emoji.message.id == m.id and user.id == ctx.author.id),
                self.bot.wait_for('reaction_remove', timeout=120, check=lambda emoji, user: emoji.message.id == m.id and user.id == ctx.author.id),
                self.bot.wait_for('message', timeout=120, check=lambda message: message.author.id == ctx.author.id)
            ],
            return_when=asyncio.FIRST_COMPLETED
        )

        try:
            reaction = copy.copy(done)
            response, _ = reaction.pop().result()
            response = response[0]
        except TypeError:
            response = next(iter(done)).result()
        except asyncio.TimeoutError:
            return formData

        for future in done:
            future.exception()
        for future in pending:
            future.cancel()

        if isinstance(response, tuple):
            await m.clear_reactions()
            return formData

        if isinstance(response, discord.message.Message):
            try:
                delete = int(response.content)
            except ValueError:
                return formData
            if delete <= len(formData['questions']):
                await response.delete()
                del formData["questions"][delete-1]
        await m.clear_reactions()
        return formData

    async def getText(self, m, title, desc, usr, url=False):
        await m.edit(embed=discord.Embed(
            title=title,
            description=desc,
            color=Colours.green
        ))
        await m.add_reaction(self.bot.get_emoji(805431640402034750))
        url = not url

        done, pending = await asyncio.wait(
            [
                self.bot.wait_for('reaction_add', timeout=120, check=lambda emoji, user: emoji.message.id == m.id and user.id == usr.id),
                self.bot.wait_for('reaction_remove', timeout=120, check=lambda emoji, user: emoji.message.id == m.id and user.id == usr.id),
                self.bot.wait_for('message', timeout=120, check=lambda message: (
                    message.author.id == usr.id and (
                        url or
                        bool(re.match(r"^(http(s)?:\/\/)([[a-zA-Z0-9\-]{3,}).([a-zA-Z.]{2,})(\/([^\n]*)?)?$", message.content))
                    )
                ))
            ],
            return_when=asyncio.FIRST_COMPLETED
        )

        try:
            reaction = copy.copy(done)
            response, _ = reaction.pop().result()
            response = response[0]
        except TypeError:
            response = next(iter(done)).result()
        except asyncio.TimeoutError:
            await m.clear_reactions()
            return None

        for future in done:
            future.exception()
        for future in pending:
            future.cancel()

        if isinstance(response, tuple):
            await m.clear_reactions()
            return None

        if isinstance(response, discord.message.Message):
            await response.delete()
            if response.content.lower() == "cancel":
                await m.clear_reactions()
                return None
            else:
                await m.clear_reactions()
                return response.content

        await m.clear_reactions()
        return None

    async def getColour(self, m, usr):
        await m.edit(embed=discord.Embed(
            title=f"{self.bot.get_emoji(Emojis.features.colour)} What colour should this question be?",
            description="This is the colour of the embed the question is on. \nYou can pick a preset colour, or type your own hex code as `ffffff`.\nType `cancel` to cancel.",
            color=Colours.green
        ))
        for r in list(Emojis.colours.__dict__.values())[1:(len(Emojis.colours.__dict__)-3)]:
            await m.add_reaction(self.bot.get_emoji(r))
        await m.add_reaction(self.bot.get_emoji(805431640402034750))

        done, pending = await asyncio.wait(
            [
                self.bot.wait_for('reaction_add', timeout=120, check=lambda emoji, user: emoji.message.id == m.id and user.id == usr.id),
                self.bot.wait_for('reaction_remove', timeout=120, check=lambda emoji, user: emoji.message.id == m.id and user.id == usr.id),
                self.bot.wait_for('message', timeout=120, check=lambda message: message.author.id == usr.id and bool(re.match(r"^(#|0x)?([0-9a-fA-F]{6})$", message.content)))
            ],
            return_when=asyncio.FIRST_COMPLETED
        )

        try:
            reaction = copy.copy(done)
            response, _ = reaction.pop().result()
            response = response[0]
        except TypeError:
            response = next(iter(done)).result()
        except asyncio.TimeoutError:
            await m.clear_reactions()
            return None

        for future in done:
            future.exception()
        for future in pending:
            future.cancel()

        if isinstance(response, tuple):
            await m.clear_reactions()
            if response[0].emoji.name.lower() == "col1":
                return "F27878"
            elif response[0].emoji.name.lower() == "col2":
                return "E5AB71"
            elif response[0].emoji.name.lower() == "col3":
                return "F2D478"
            elif response[0].emoji.name.lower() == "col4":
                return "65CC76"
            elif response[0].emoji.name.lower() == "col5":
                return "71AFE5"
            elif response[0].emoji.name.lower() == "col6":
                return "A358B2"
            elif response[0].emoji.name.lower() == "col7":
                return "D46899"
            else:
                return

        if isinstance(response, discord.message.Message):
            await response.delete()
            await m.clear_reactions()
            if response.content.lower() == "cancel":
                return None
            else:
                text = response.content.lower()
                if text.startswith("#"):
                    text = text[1:]

                for char in text:
                    if char not in list("0123456789abcdef"):
                        return None

                if len(text) == 6:
                    return int(text, base=16)
                if len(text) == 1:
                    return int(str(text) * 6, base=16)
                if len(text) == 2:
                    return int(str(text) * 3, base=16)
                if len(text) == 3:
                    return int((str(text[0])*2 + str(text[1])*2 + str(text[2])*2), base=16)
                return int("F27878", base=16)

        await m.clear_reactions()
        return None

    async def getEmojis(self, m, author):
        await m.add_reaction(self.bot.get_emoji(805431640209752125))
        possible = list(Emojis.responses.__dict__.values())[1:(len(Emojis.colours.__dict__)-3)]
        for r in possible:
            await m.add_reaction(self.bot.get_emoji(r))
        await m.add_reaction(self.bot.get_emoji(805431640402034750))
        options = {}
        while True:
            desc = f"React with the option you would like to add.\n" \
                    f"React with {self.bot.get_emoji(Emojis.cross)} to cancel or {self.bot.get_emoji(Emojis.tick)} to add the question." \
                    f"\n\n**Options:**"
            if not len(options):
                desc += "\n*No options*"
            for key, val in options.items():
                desc += f"\n{self.bot.get_emoji(key)} {val}"
            await m.edit(embed=discord.Embed(
                title=f"{self.bot.get_emoji(Emojis.responses.r5)} Add an option",
                description=desc,
                color=Colours.purple
            ))
            try:
                response = await self.bot.wait_for('reaction_add', timeout=120, check=lambda emoji, user: emoji.message.id == m.id and user.id == author.id),
            except asyncio.TimeoutError:
                await m.clear_reactions()
                break
            await m.remove_reaction(response[0][0].emoji, author)
            emoji = response[0][0].emoji.id
            if response[0][0].emoji.name == "Cross":
                await m.clear_reactions()
                options = {}
                break
            if response[0][0].emoji.name == "Tick":
                await m.clear_reactions()
                break
            desc = f"Enter the text {self.bot.get_emoji(emoji)} should use. Type `cancel` to cancel.\n\n**Options:**"
            if not len(options):
                desc += "\n*No options*"
            for key, val in options.items():
                desc += f"\n{self.bot.get_emoji(key)} {val}"
            await m.edit(embed=discord.Embed(
                title=f"{self.bot.get_emoji(Emojis.responses.r5)} Add an option",
                description=desc,
                color=Colours.purple
            ))
            try:
                response = await self.bot.wait_for('message', timeout=120, check=lambda message: message.author.id == author.id),
            except asyncio.TimeoutError:
                await m.clear_reactions()
                break
            if response[0].content.lower() == "cancel":
                options = {}
                break
            await response[0].delete()
            text = str(response[0].content)[:100]
            options[emoji] = text
        return options


def setup(bot):
    bot.add_cog(New(bot))
