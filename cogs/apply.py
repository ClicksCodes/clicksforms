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
        # formData = {
        #     "meta": {
        #         "type": "form",
        #         "active": False,
        #         "anonymous": False,
        #         "invoke": "apply",
        #         "guild": 805408534145531935,
        #         "created_by": 438733159748599813,
        #         "name": "New Application",
        #         "description": "The default application",
        #         "required_roles": [], "disallowed_roles": [], "given_roles": [], "removed_roles": []
        #     },
        #     "questions": [
        #         {
        #             "question": True,
        #             "name": "Default question",
        #             "description": "The default question for an application",
        #             "colour": 15051633,
        #             "type": "text",
        #             "required": True,
        #             "question_specific": {}
        #         },
        #         {
        #             "question": False,
        #             "name": "a",
        #             "description": "b",
        #             "colour": 13421772,
        #             "type": "special_section"
        #         },
        #         {
        #             "question": True,
        #             "name": "pick a number",
        #             "description": "anything will do",
        #             "colour": "ffff00",
        #             "type": "number",
        #             "required": True,
        #             "question_specific": {}
        #         },
        #         {
        #             "question": False,
        #             "description": "god damn text",
        #             "colour": "F27878",
        #             "type": "special_text"
        #         },
        #         {
        #             "question": True,
        #             "name": "pick",
        #             "description": "plz",
        #             "colour": "0000ff",
        #             "type": "multichoice",
        #             "required": True,
        #             "question_specific": {
        #                 805737834098065408: "option 1",
        #                 805737834069622814: "option 2",
        #                 805737834136731658: "option 3",
        #                 805737833792536597: "option 4"
        #             }
        #         },
        #         {
        #             "question": False,
        #             "name": "aaaaaaaaa",
        #             "caption": "https://media.discordapp.net/attachments/755427300073275445/803712856070946866/image0.png?width=617&height=670",
        #             "url": "https://media.discordapp.net/attachments/755427300073275445/803712856070946866/image0.png?width=617&height=670",
        #             "colour": 64206,
        #             "type": "special_image"
        #         },
        #         {
        #             "question": True,
        #             "name": "pick all",
        #             "description": "definitely not based on eek",
        #             "colour": "ff00ff",
        #             "type": "tickbox",
        #             "required": True,
        #             "question_specific": {
        #                 805737834098065408: "programmer",
        #                 805737834069622814: "dead inside",
        #                 805737834136731658: "asexual",
        #                 805737833792536597: "wears bubble wrap on head"
        #             }
        #         },
        #         {
        #             "question": False,
        #             "name": "meme",
        #             "text": "check out this meme",
        #             "url": "https://cdn.discordapp.com/attachments/755427300073275445/803712856070946866/image0.png",
        #             "colour": "A358B2",
        #             "type": "special_link"
        #         },
        #         {
        #             "question": True,
        #             "name": "upload your soul",
        #             "description": "gotta do it or pay up",
        #             "colour": "ff8800",
        #             "type": "fileupload",
        #             "required": False,
        #             "question_specific": {}
        #         },
        #         {
        #             "question": True,
        #             "name": "when do you want to die",
        #             "description": "or else",
        #             "colour": "2c2f33",
        #             "type": "date",
        #             "required": True,
        #             "question_specific": {}
        #         },
        #         {
        #             "question": True,
        #             "name": "when",
        #             "description": "time",
        #             "colour": "72aef1",
        #             "type": "time",
        #             "required": True,
        #             "question_specific": {}
        #         }
        #     ]
        # }
        formData = {'meta': {'type': 'form', 'active': False, 'anonymous': False, 'guild': 684492926528651336, 'created_by': 438733159748599813, 'name': 'New Application', 'description': 'The default form', 'auto_accept': True, 'required_roles': [785902485088370750], 'disallowed_roles': [760901551496626187], 'given_roles': [762687733482520647], 'removed_roles': [762687733482520647], 'channel_requiremens': {'type': 'any'}}, 'questions': [{'question': True, 'name': 'Default question', 'description': 'The default question for a form', 'colour': 15051633, 'type': 'text', 'required': True, 'question_specific': {}}]}

        if formData['meta']['guild'] != ctx.guild.id:
            return

        failedFor = [[], []]
        memberRoles = [r.id for r in ctx.author.roles]
        for role in formData['meta']['required_roles']:
            if role not in memberRoles:
                failedFor[0].append(role)

        for role in formData['meta']['disallowed_roles']:
            if role in memberRoles:
                failedFor[1].append(role)

        if len(failedFor[0]) or len(failedFor[1]):
            failedMessage0 = "" if not len(failedFor[0]) \
                else f"You are missing the following role{s if len(failedFor[0]) > 1 else ''}:\n> {', '.join(ctx.guild.get_role(r).mention for r in failedFor[0])}\n\n"
            failedMessage1 = "" if not len(failedFor[1]) \
                else f"You cannot have the following role{s if len(failedFor[0]) > 1 else ''}:\n> {', '.join(ctx.guild.get_role(r).mention for r in failedFor[1])}"
            return await ctx.send(embed=discord.Embed(
                title=f"Looks like you can't apply",
                description=f"{failedMessage0}"
                            f"{failedMessage1}",
                color=Colours.orange
            ))

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

                if question["required"]:
                    desc += f"\nThis question is required"
                else:
                    desc += f"\nThis question is not required. Click {self.bot.get_emoji(Emojis.tick)} to skip."

                await m.edit(embed=discord.Embed(
                    title=f"{self.bot.get_emoji(getattr(Emojis.types, question['type']))} {y}. {question['name']} ({y}/{question_len})",
                    description=desc,
                    color=colour
                ))

                if question['type'] == "text":
                    t, out = await self.get_response(m, ctx, required=question["required"])
                    if t is None:
                        break

                    elif t == "Special":
                        responses.append(out)
                        continue

                    elif t == "Emoji":
                        break

                    elif t == "Message":
                        if out.content.lower() == "cancel":
                            await m.clear_reactions()
                            break
                        else:
                            responses.append(out.content)
                            continue

                elif question['type'] == "number":
                    t, out = await self.get_response(m, ctx, required=question["required"], mcheck=lambda message: (
                            message.author.id == ctx.author.id and
                            message.content.replace(".", "", 1).isdigit()
                        ))
                    if t is None:
                        break

                    elif t == "Special":
                        responses.append(out)
                        continue

                    elif t == "Emoji":
                        break

                    elif t == "Message":
                        if out.content.lower() == "cancel":
                            await m.clear_reactions()
                            break
                        else:
                            responses.append(out.content)
                            continue
                elif question['type'] == "multichoice":
                    for r in question['question_specific'].keys():
                        await m.add_reaction(self.bot.get_emoji(int(r)))
                    if not question["required"]:
                        await m.add_reaction(self.bot.get_emoji(805431640209752125))
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
                        if response[0].emoji.name == "Tick":
                            responses.append("/Skipped/")
                        else:
                            responses.append(question['question_specific'][response[0].emoji.id])
                    except KeyError:
                        responses.append("Invalid response")
                elif question['type'] == "tickbox":
                    await m.add_reaction(self.bot.get_emoji(Emojis.right))
                    for r in question['question_specific'].keys():
                        await m.add_reaction(self.bot.get_emoji(int(r)))
                    if not question["required"]:
                        await m.add_reaction(self.bot.get_emoji(805431640209752125))
                    try:
                        response = await self.bot.wait_for(
                            'reaction_add',
                            timeout=300,
                            check=lambda emoji, user: (
                                emoji.message.id == m.id
                                and user.id == ctx.author.id
                                and (emoji.emoji.name in ["Tick", "Right"])
                            )
                        )
                    except asyncio.TimeoutError:
                        await m.clear_reactions()
                        break
                    if response[0].emoji.name == "Tick":
                        await m.clear_reactions()
                        responses.append("/Skipped/")
                        continue
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
                    t, out = await self.get_response(m, ctx, required=question["required"], mcheck=lambda message: (
                                message.author.id == ctx.author.id and
                                len(message.attachments) >= 1
                            ))
                    if t is None:
                        break

                    elif t == "Special":
                        responses.append(out)
                        continue

                    elif t == "Emoji":
                        break

                    elif t == "Message":
                        if out.content.lower() == "cancel":
                            await m.clear_reactions()
                            break
                        else:
                            responses.append(out.attachments[0].url)
                            continue
                elif question['type'] == "date":
                    now = datetime.datetime.now()
                    month = int(now.strftime("%m"))
                    year = int(now.strftime("%Y"))
                    for r in [811943209772515358, 805431640292851723, 805431640364154950, 811943210351460382]:
                        await m.add_reaction(self.bot.get_emoji(r))

                    if not question["required"]:
                        await m.add_reaction(self.bot.get_emoji(805431640209752125))

                    if question["required"]:
                        skip = f"\n\nThis question is required"
                    else:
                        skip = f"\n\nThis question is not required. Click {self.bot.get_emoji(Emojis.tick)} to skip."

                    while True:
                        d = calendar.monthrange(year, month)

                        lis = ["B"] * (d[0]-1)
                        for x in range(1, d[1]+1):
                            lis.append(str(x))
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
                                        f"Type `2020-4-20` to select a full date{skip}",
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
                            if name == "Tick":
                                responses.append(f"/Skipped/")
                                break
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
                    desc = f"> {question['description']}\n" \
                           f"Please enter a time as `12:34` or `3:20 AM`\n"

                    if question["required"]:
                        desc += f"\nThis question is required"
                    else:
                        desc += f"\nThis question is not required. Click {self.bot.get_emoji(Emojis.tick)} to skip."

                    await m.edit(embed=discord.Embed(
                        title=f"{self.bot.get_emoji(getattr(Emojis.types, question['type']))} {y}. {question['name']} ({y}/{question_len})",
                        description=desc,
                        color=colour
                    ))
                    t, out = await self.get_response(m, ctx, required=question["required"], mcheck=lambda message: (
                            message.author.id == ctx.author.id and
                            bool(re.match(r"(^(2[0-3]|1[0-9]|0?0):([0-5][0-9])$)|(^(1[0-2]|0?[1-9]):([0-5][0-9]) ?([AaPp][Mm])?$)", str(message.content)))
                        ))
                    if t is None:
                        break

                    elif t == "Special":
                        responses.append(out)
                        continue

                    elif t == "Emoji":
                        break

                    elif t == "Message":
                        if out.content.lower() == "cancel":
                            await m.clear_reactions()
                            break
                        else:
                            responses.append(out.content)
                            continue

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
                "applicant": ctx.author.id if not formData["meta"]["anonymous"] else "Anonymous",
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

    async def get_response(
                self,
                m,
                ctx,
                mcheck=False,
                rcheck=False,
                required=True
            ):
        await m.clear_reactions()
        if not required:
            await m.add_reaction(self.bot.get_emoji(805431640209752125))

        if not rcheck:
            def rcheck(emoji, user):
                return emoji.message.id == m.id and user.id == ctx.author.id
        if not mcheck:
            def mcheck(message):
                return message.author.id == ctx.author.id

        done, pending = await asyncio.wait(
            [
                self.bot.wait_for('reaction_add', timeout=300, check=rcheck),
                self.bot.wait_for('message', timeout=300, check=mcheck)
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
            return (None, None)

        for future in done:
            future.exception()
        for future in pending:
            future.cancel()

        await m.clear_reactions()

        if isinstance(response, tuple):
            if response[0].emoji.name == "Tick":
                return ("Special", "/Skipped/")
            return ("Emoji", reponse[0])
        else:
            await response.delete()
            return ("Message", response)


def setup(bot):
    bot.add_cog(Apply(bot))
