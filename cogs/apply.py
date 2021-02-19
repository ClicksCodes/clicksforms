import asyncio
import time
import re
import datetime
import copy
import calendar
from discord.ext import commands

from cogs.consts import *


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


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
                    "name": "when do you want to die",
                    "description": "or else",
                    "colour": "2c2f33",
                    "type": "date",
                    "required": True,
                    "question_specific": {}
                },
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

        if formData['meta']['guild'] != ctx.guild.id:
            # return
            pass

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
            response = await self.bot.wait_for('reaction_add', timeout=300, check=lambda emoji, user: (
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
                            timeout=300,
                            check=lambda message: message.author.id == ctx.author.id
                        )
                    except asyncio.TimeoutError:
                        break
                    responses.append(response.content)
                    await response.delete()
                elif question['type'] == "number":
                    try:
                        response = await self.bot.wait_for('message', timeout=300, check=lambda message: (
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
                            timeout=300,
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
                    try:
                        responses.append(question['question_specific'][response[0].emoji.id])
                    except KeyError:
                        responses.append("Invalid response")
                elif question['type'] == "tickbox":
                    await m.add_reaction(self.bot.get_emoji(Emojis.tick))
                    for r in question['question_specific'].keys():
                        await m.add_reaction(self.bot.get_emoji(int(r)))
                    try:
                        response = await self.bot.wait_for(
                            'reaction_add',
                            timeout=300,
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
                                try:
                                    reacted.append(question['question_specific'][r.emoji.id])
                                except KeyError:
                                    reacted.append("Invalid response")
                    await m.clear_reactions()
                    responses.append(reacted)
                elif question['type'] == "fileupload":
                    try:
                        response = await self.bot.wait_for('message', timeout=300, check=lambda message: (
                                message.author.id == ctx.author.id and
                                len(message.attachments) >= 1
                            )
                        )
                    except asyncio.TimeoutError:
                        break

                    responses.append(response.attachments[0].url)
                    await response.delete()
                elif question['type'] == "date":
                    now = datetime.datetime.now()
                    month = int(now.strftime("%m"))
                    year = int(now.strftime("%Y"))
                    for r in [811943209772515358, 805431640292851723, 805431640364154950, 811943210351460382]:
                        await m.add_reaction(self.bot.get_emoji(r))

                    while True:
                        d = calendar.monthrange(year, month)

                        lis = ["B"] * (d[0]-1)
                        for x in range(1, d[1]+1):
                            lis.append(x)
                        pad = 7-(len(lis) % 7)
                        lis += ["B" for _ in range(pad if pad < 7 else 0)]
                        lis = [Emojis.calendar[emoji] for emoji in lis]
                        chunked = [n for n in chunks(lis, 7)]

                        out = "` ` " + (" ` `\n` ` ".join(["".join(x) for x in chunked])) + " ` `"
                        await m.edit(embed=discord.Embed(
                            title=f"{self.bot.get_emoji(getattr(Emojis.types, question['type']))} {y}. {question['name']} ({y}/{question_len})",
                            description=f"> {question['description']}\n\n**{calendar.month_name[month]} {year}**\n` ` {''.join([Emojis.calendar[n] for n in 'MTWTFSS'])} ` `\n"
                                        f"{out}\n"
                                        f"Enter a day to select it (`4`)\n"
                                        f"Use {self.bot.get_emoji(805431640292851723)} or {self.bot.get_emoji(805431640364154950)} to change the month\n"
                                        f"Use {self.bot.get_emoji(811943209772515358)} or {self.bot.get_emoji(811943210351460382)} to change the year\n"
                                        f"Type `M4` to select month 4, or `Y2020` to select the year 2020\n"
                                        f"Type `2020-4-20` to select a full date",
                            color=colour
                        ))
                        done, pending = await asyncio.wait(
                            [
                                self.bot.wait_for('reaction_add', timeout=300, check=lambda emoji, user: emoji.message.id == m.id and user.id == ctx.author.id),
                                self.bot.wait_for('reaction_remove', timeout=300, check=lambda emoji, user: emoji.message.id == m.id and user.id == ctx.author.id),
                                self.bot.wait_for('message', timeout=300, check=lambda message: message.author.id == ctx.author.id)
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
                            await m.remove_reaction(response[0], ctx.author)
                            name = response[0].emoji.name
                            if name == "Back":
                                year -= 1
                            elif name == "Left":
                                month -= 1
                                if month == 0:
                                    month = 12
                                    year -= 1
                            elif name == "Right":
                                month += 1
                                if month == 13:
                                    month = 1
                                    year += 1
                            elif name == "Forward":
                                year += 1

                        if isinstance(response, discord.message.Message):
                            await response.delete()
                            content = response.content.lower()
                            if bool(re.match(r"^y[0-9]{1,5}$", str(content))):
                                year = int(str(content)[1:])
                            elif bool(re.match(r"^m(1[0-2]|0?[1-9])$", str(content))):
                                month = int(str(content)[1:])
                            elif bool(re.match(r"^[0-9]{1,4}[-\/\.][0-1]?[0-9][-\/\.][0-9]{1,2}$", str(content))):
                                responses.append(content)
                                break
                            else:
                                try:
                                    content = int(content)
                                    if 0 < content <= d[1]:
                                        responses.append(f"{year}-{month}-{content}")
                                        break
                                except ValueError:
                                    continue
                    await m.clear_reactions()

                elif question['type'] == "time":
                    await m.edit(embed=discord.Embed(
                        title=f"{self.bot.get_emoji(getattr(Emojis.types, question['type']))} {y}. {question['name']} ({y}/{question_len})",
                        description=f"> {question['description']}\n"
                                    f"Please enter a time as `12:34` or `3:20 AM`\n",
                        color=colour
                    ))
                    try:
                        response = await self.bot.wait_for('message', timeout=300, check=lambda message: (
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
                        timeout=300,
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
