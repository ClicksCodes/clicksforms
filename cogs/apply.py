import asyncio
import time
import re
from datetime import datetime
from discord.ext import commands

from cogs.consts import *


class Apply(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Command
    @commands.guild_only()
    async def apply(self, ctx):
        formData = {
            "meta": {
                "type": "form",
                "active": False,
                "anonymous": False,
                "invoke": "apply",
                "guild": 805408534145531935,
                "created_by": 438733159748599813,
                "name": "New Application",
                "description": "The default application",
                "required_roles": [], "disallowed_roles": [], "given_roles": [], "removed_roles": []
            },
            "questions": [
                {
                    "question": True,
                    "name": "Default question",
                    "description": "The default question for an application",
                    "colour": 15051633,
                    "type": "text",
                    "required": True,
                    "question_specific": {}
                },
                {
                    "question": False,
                    "name": "a",
                    "description": "b",
                    "colour": 13421772,
                    "type": "special_section"
                },
                {
                    "question": True,
                    "name": "pick a number",
                    "description": "anything will do",
                    "colour": "ffff00",
                    "type": "number",
                    "required": True,
                    "question_specific": {}
                },
                {
                    "question": False,
                    "description": "god damn text",
                    "colour": "F27878",
                    "type": "special_text"
                },
                {
                    "question": True,
                    "name": "pick",
                    "description": "plz",
                    "colour": "0000ff",
                    "type": "multichoice",
                    "required": True,
                    "question_specific": {
                        805737834098065408: "option 1",
                        805737834069622814: "option 2",
                        805737834136731658: "option 3",
                        805737833792536597: "option 4"
                    }
                },
                {
                    "question": False,
                    "name": "aaaaaaaaa",
                    "caption": "https://media.discordapp.net/attachments/755427300073275445/803712856070946866/image0.png?width=617&height=670",
                    "url": "https://media.discordapp.net/attachments/755427300073275445/803712856070946866/image0.png?width=617&height=670",
                    "colour": 64206, "type": "special_image"
                },
                {
                    "question": True,
                    "name": "pick all",
                    "description": "definitely not based on eek",
                    "colour": "ff00ff",
                    "type": "tickbox",
                    "required": True,
                    "question_specific": {
                        805737834098065408: "programmer",
                        805737834069622814: "dead inside",
                        805737834136731658: "asexual",
                        805737833792536597: "wears bubble wrap on head"
                    }
                },
                {
                    "question": False,
                    "name": "meme",
                    "text": "check out this meme",
                    "url": "https://cdn.discordapp.com/attachments/755427300073275445/803712856070946866/image0.png",
                    "colour": "A358B2",
                    "type": "special_link"
                },
                {
                    "question": True,
                    "name": "upload your soul",
                    "description": "gotta do it or pay up",
                    "colour": "ff8800",
                    "type": "fileupload",
                    "required": True,
                    "question_specific": {}
                },
                {
                    "question": True,
                    "name": "when do you want to die",
                    "description": "or else",
                    "colour": "2c2f33",
                    "type": "date",
                    "required": True,
                    "question_specific": {}
                },
                {
                    "question": True,
                    "name": "when",
                    "description": "time",
                    "colour": "72aef1",
                    "type": "time",
                    "required": True,
                    "question_specific": {}
                }
            ]
        }
        # if formData['meta']['guild'] != ctx.guild.id:
        #     return

        question_len = len([q for q in formData['questions'] if q['question']])

        m = await ctx.send(embed=discord.Embed(
            title=f"{formData['meta']['name']}",
            description=f"> {formData['meta']['description']}\n"
                        f"Questions: {question_len}\n\n"
                        f"React with {self.bot.get_emoji(Emojis.tick)} to begin the application.\n"
                        f"To quit, just leave this application and it will end automatically.",
            color=Colours.orange
        ))
        await m.add_reaction(self.bot.get_emoji(Emojis.tick))
        try:
            response = await self.bot.wait_for('reaction_add', timeout=120, check=lambda emoji, user: (
                    emoji.message.id == m.id and user.id == ctx.author.id
                )
            ),
        except asyncio.TimeoutError:
            await m.clear_reactions()
            return

        await m.clear_reactions()

        x, y = 0, 0
        responses = []
        start = time.time()
        for question in formData['questions']:
            x += 1
            colour = question['colour']
            if type(colour) == str:
                colour = int(colour, 16)

            if question['question']:
                y += 1

                desc = f"> {question['description']}\n" \
                       f"{getattr(Descriptions, question['type'])}"

                if question['type'] in ["multichoice", "tickbox"]:
                    desc += "\n\n"
                    for k, v in question['question_specific'].items():
                        desc += f"{self.bot.get_emoji(k)} {v}\n"

                await m.edit(embed=discord.Embed(
                    title=f"{self.bot.get_emoji(getattr(Emojis.types, question['type']))} {y}. {question['name']} ({y}/{question_len})",
                    description=desc,
                    color=colour
                ))

                if question['type'] == "text":
                    try:
                        response = await self.bot.wait_for(
                            'message',
                            timeout=120,
                            check=lambda message: message.author.id == ctx.author.id
                        )
                    except asyncio.TimeoutError:
                        break
                    responses.append(response.content)
                    await response.delete()
                elif question['type'] == "number":
                    try:
                        response = await self.bot.wait_for('message', timeout=120, check=lambda message: (
                                message.author.id == ctx.author.id and
                                message.content.replace(".", "", 1).isdigit()
                            )
                        )
                    except asyncio.TimeoutError:
                        break
                    responses.append(response.content)
                    await response.delete()
                elif question['type'] == "multichoice":
                    for r in question['question_specific'].keys():
                        await m.add_reaction(self.bot.get_emoji(int(r)))
                    try:
                        response = await self.bot.wait_for(
                            'reaction_add',
                            timeout=120,
                            check=lambda emoji, user: (
                                emoji.message.id == m.id and
                                type(emoji) == discord.Reaction and
                                user.id == ctx.author.id
                            )
                        )
                    except asyncio.TimeoutError:
                        await m.clear_reactions()
                        break
                    await m.clear_reactions()
                    responses.append(question['question_specific'][response[0].emoji.id])
                elif question['type'] == "tickbox":
                    await m.add_reaction(self.bot.get_emoji(Emojis.tick))
                    for r in question['question_specific'].keys():
                        await m.add_reaction(self.bot.get_emoji(int(r)))
                    try:
                        response = await self.bot.wait_for(
                            'reaction_add',
                            timeout=120,
                            check=lambda emoji, user: (
                                emoji.message.id == m.id
                                and user.id == ctx.author.id
                                and emoji.emoji.name == "Tick"
                            )
                        )
                    except asyncio.TimeoutError:
                        await m.clear_reactions()
                        break
                    message = await ctx.channel.fetch_message(m.id)
                    reacted = []
                    for r in message.reactions:
                        if (
                            r.emoji.name != "Tick" and
                            ctx.author in await r.users().flatten() and
                            type(r) == discord.Reaction
                        ):
                            if r.emoji.id in question['question_specific'].keys():
                                reacted.append(question['question_specific'][r.emoji.id])
                    await m.clear_reactions()
                    responses.append(reacted)
                elif question['type'] == "fileupload":
                    try:
                        response = await self.bot.wait_for('message', timeout=120, check=lambda message: (
                                message.author.id == ctx.author.id and
                                len(message.attachments) >= 1
                            )
                        )
                    except asyncio.TimeoutError:
                        break

                    responses.append(response.attachments[0].url)
                    await response.delete()
                elif question['type'] == "date":
                    await m.edit(embed=discord.Embed(
                        title=f"{self.bot.get_emoji(getattr(Emojis.types, question['type']))} {y}. {question['name']} ({y}/{question_len})",
                        description=f"> {question['description']}\n"
                                    f"`____ - __ - __`\n"
                                    f"Please enter the **year**",
                        color=colour
                    ))
                    try:
                        response = await self.bot.wait_for('message', timeout=120, check=lambda message: (
                                message.author.id == ctx.author.id and
                                message.content.isdigit()
                            )
                        )
                    except asyncio.TimeoutError:
                        break
                    await response.delete()
                    year = response.content
                    await m.edit(embed=discord.Embed(
                        title=f"{self.bot.get_emoji(getattr(Emojis.types, question['type']))} {y}. {question['name']} ({y}/{question_len})",
                        description=f"> {question['description']}\n"
                                    f"`{year} - __ - __`\n"
                                    f"Please enter the **month** as a number (January = 1)",
                        color=colour
                    ))
                    try:
                        response = await self.bot.wait_for('message', timeout=120, check=lambda message: (
                                message.author.id == ctx.author.id and
                                message.content.isdigit() and
                                0 < int(message.content) <= 12
                            )
                        )
                    except asyncio.TimeoutError:
                        break
                    await response.delete()
                    month = response.content
                    if len(month) == 1:
                        month = "0" + month
                    await m.edit(embed=discord.Embed(
                        title=f"{self.bot.get_emoji(getattr(Emojis.types, question['type']))} {y}. {question['name']} ({y}/{question_len})",
                        description=f"> {question['description']}\n"
                                    f"`{year} - {month} - __`\n"
                                    f"Please enter the **day** (3rd = 3)",
                        color=colour
                    ))
                    limits = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
                    try:
                        response = await self.bot.wait_for('message', timeout=120, check=lambda message: (
                                message.author.id == ctx.author.id and
                                message.content.isdigit() and
                                int(message.content) <= limits[int(month)-1]
                            )
                        )
                    except asyncio.TimeoutError:
                        break
                    await response.delete()
                    day = response.content
                    responses.append(f"{year}-{month}-{day}")
                elif question['type'] == "time":
                    await m.edit(embed=discord.Embed(
                        title=f"{self.bot.get_emoji(getattr(Emojis.types, question['type']))} {y}. {question['name']} ({y}/{question_len})",
                        description=f"> {question['description']}\n"
                                    f"Please enter a time as `12:34` or `3:20 AM`\n",
                        color=colour
                    ))
                    try:
                        response = await self.bot.wait_for('message', timeout=120, check=lambda message: (
                                message.author.id == ctx.author.id and
                                bool(re.match(r"(^(2[0-3]|1[0-9]|0?0):([0-5][0-9])$)|(^(1[0-2]|0?[1-9]):([0-5][0-9]) ?([AaPp][Mm])?$)", str(message.content)))
                            )
                        )
                    except asyncio.TimeoutError:
                        break
                    await response.delete()
                    responses.append(response.content)

            else:
                colour = question['colour']
                if type(colour) == str:
                    colour = int(colour, 16)

                if question['type'] == 'special_section':
                    await m.edit(embed=discord.Embed(
                        title=f"{self.bot.get_emoji(Emojis.decorations.text)} {question['name']}",
                        description=f"{question['description']}\n\nClick {self.bot.get_emoji(Emojis.tick)} to continue",
                        color=colour
                    ))

                elif question['type'] == 'special_text':
                    await m.edit(embed=discord.Embed(
                        title=str(self.bot.get_emoji(Emojis.decorations.text)),
                        description=f"{question['description']}\n\nClick {self.bot.get_emoji(Emojis.tick)} to continue",
                        color=colour
                    ))

                elif question['type'] == 'special_link':
                    await m.edit(embed=discord.Embed(
                        title=f"{self.bot.get_emoji(Emojis.decorations.link)} {question['name']}",
                        description=f"[{question['text']}]({question['url']})\n\nClick {self.bot.get_emoji(Emojis.tick)} to continue",
                        color=colour
                    ))

                elif question['type'] == 'special_image':
                    embed = discord.Embed(
                        title=f"{self.bot.get_emoji(Emojis.decorations.image)} {question['name']}",
                        description=f"{question['caption']}\n\nClick {self.bot.get_emoji(Emojis.tick)} to continue",
                        color=colour
                    )
                    embed.set_image(url=question['url'])
                    await m.edit(embed=embed)

                await m.add_reaction(self.bot.get_emoji(Emojis.tick))
                try:
                    response = await self.bot.wait_for(
                        'reaction_add',
                        timeout=120,
                        check=lambda emoji, user: (
                            emoji.message.id == m.id and
                            type(emoji) == discord.Reaction and
                            user.id == ctx.author.id
                        )
                    )
                except asyncio.TimeoutError:
                    await m.clear_reactions()
                    break
                await m.clear_reactions()

        application = {
            "meta": {
                "applicant": ctx.author.id,
                "duration": f"{time.time() - start} seconds",
                "channel": ctx.channel.id
            },
            "responses": responses
        }
        await m.edit(embed=discord.Embed(
            title=f"Application completed",
            description=f"Your application was submitted successfully",
            color=Colours.orange
        ))
        await ctx.send(str(application))


def setup(bot):
    bot.add_cog(Apply(bot))
