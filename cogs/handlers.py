import datetime
import discord
from cogs.consts import *
import databases
import orm
import sqlalchemy
import json

database = databases.Database("sqlite:///main.db")
models = orm.ModelRegistry(database=database)
metadata = sqlalchemy.MetaData()


class GuildData(orm.Model):
    tablename = "data"
    registry = models
    fields = {
        "id": orm.Integer(primary_key=True),
        "data": orm.JSON(),
        "responses": orm.JSON()
    }


class Data:
    def __init__(self, guild, data, responses):
        self.data = data
        self.responses = responses
        self.guild = guild

    async def update(self, data=None, responses=None):
        with open("data/db.json") as entry:
            entry = json.load(entry)
            if self.guild in entry:
                if data:
                    entry[self.guild]["data"] = data
                if responses:
                    entry[self.guild]["responses"] = responses
            else:
                entry[self.guild] = {"data": data, "responses": responses}
        with open("data/db.json", "w") as f:
            json.dump(entry, f, indent=4)

class Database:
    def __init__(self):
        self.db = GuildData

    async def get(self, guild):
        if isinstance(guild, discord.Guild):
            guild = guild.id
        guild = str(guild)
        with open("data/db.json") as entry:
            entry = json.load(entry)
            if guild in entry:
                return Data(guild, entry[guild]["data"], entry[guild]["responses"])
        try:
            data = await self.db.objects.get(id=int(guild))
            return Data(guild, data.data, data.responses)
        except orm.NoMatch:
            with open("data/db.json", "w") as entry:
                entry.write(json.dumps({guild: {"data": [], "responses": {}}}, indent=4))
            return Data(guild, [], {})

engine = sqlalchemy.create_engine(str(database.url))
metadata.create_all(engine)


class Button(discord.ui.Button):
    def __init__(self, label, style="primary", disabled=False, url=None, emoji=None, row=None, cb=None):
        super().__init__(
            label=label,
            style=getattr(discord.ButtonStyle, style),
            disabled=disabled,
            url=url,
            emoji=emoji,
            row=row,
        )
        self.cb = cb

    async def callback(self, _):
        self.view.selected = self.cb
        self.view.stop()


class Select(discord.ui.Select):
    def __init__(self, id, disabled=False, max_values=1, min_values=1, options=[], placeholder="", autoaccept=False):
        super().__init__(
            custom_id=id,
            disabled=disabled,
            max_values=max_values,
            min_values=min_values,
            options=options,
            placeholder=placeholder
        )
        self.autoAccept = autoaccept

    async def callback(self, _):
        self.view.dropdowns[self.custom_id] = self.values
        if self.autoAccept:
            self.view.stop()


class View(discord.ui.View):
    def __init__(self, ctx, *args, alwaysAccept=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.selected = None
        self.dropdowns = {}
        self.ctx = ctx
        self.alwaysAccept = alwaysAccept

    def add_button(self, button):
        self.add_item(button)

    async def interaction_check(self, interaction):
        if interaction.user.id == self.ctx.author.id or self.alwaysAccept:
            return True
        if "type" in interaction.data and interaction.data["type"] == 1:
            await interaction.response.send_message(ephemeral=True, embed=discord.Embed(
                title="This message wasn't made by you",
                description="Only the person who ran the command can respond to it",
                color=Colours.red
            ))
            return False
        return False


def createUI(ctx, items, alwaysAccept=False):
    v = View(ctx=ctx, timeout=300, alwaysAccept=alwaysAccept)
    for item in items:
        v.add_item(item)
    return v


class CustomCTX:
    def __init__(self, bot, author, guild, channel, message=None, interaction=None, m=None):
        self.bot = bot
        self.author = author
        self.guild = guild
        self.message = message
        self.channel = channel
        self.interaction = interaction
        self.m = m

    async def delete(self):
        if self.message:
            await self.m.delete()
            return await self.message.delete()
        if self.interaction:
            return await self.m.edit(embed=discord.Embed(
                title="Closed",
                description="Dismiss this message to close it",
                color=Colours().red
            ).set_footer(text="Discord does not, in fact, let you delete messages only you can see :/"), view=None)


def parsedForm(data):
    out = {"questions": []}
    out["id"] = str(datetime.datetime.now().timestamp())
    if "name" not in data:
        return (400, "No name was provided." + (" Did you mean 'name'?" if "title" in data else ""))
    out["name"] = data["name"]
    if "questions" not in data:
        return (400, "No questions were privided. At least one is required")

    if "active" not in data:
        out["active"] = True
    else:
        out["active"] = data["active"]
    if "anonymous" not in data:
        out["anonymous"] = False
    else:
        out["anonymous"] = data["anonymous"]
    if "description" not in data:
        out["description"] = ""
    else:
        out["description"] = data["description"]
    if "required_roles" not in data:
        out["required_roles"] = []
    else:
        out["required_roles"] = data["required_roles"]
    if "disallowed_roles" not in data:
        out["disallowed_roles"] = []
    else:
        out["disallowed_roles"] = data["disallowed_roles"]
    if "given_roles" not in data:
        out["given_roles"] = []
    else:
        out["given_roles"] = data["given_roles"]
    if "removed_roles" not in data:
        out["removed_roles"] = []
    else:
        out["removed_roles"] = data["removed_roles"]
    if "auto_accept" not in data:
        out["auto_accept"] = False
    else:
        out["auto_accept"] = data["auto_accept"]

    for question in data["questions"]:
        question["id"] = str(datetime.datetime.now().timestamp())
        if "type" not in question:
            return (400, "No question type was provided")
        if question["type"] not in ["text", "number", "multichoice", "fileupload", "time", "date", "text-decoration", "image-decoration", "url-decoration"]:
            return (400, f"Type '{question['type']}' does not exist")
        if "title" not in question:
            return (400, f'No question title was privided')
        if not question["title"]:
            question["title"] = question["type"].capitalize()
        if "description" not in question:
            question["description"] = ""
        if "required" not in question:
            question["required"] = True
        if "colour" not in question:
            return (400, f"No colour was provided for question '{question['title']}'")
        if question["colour"] not in ["red", "orange", "yellow", "green", "blue", "purple", "pink", "grey"]:
            return (400, f"Colour '{question['colour']}' does not exist")
        if "options" not in question:
            return (400, f"No options were provided for question '{question['title']}'")

        if question["type"] == "text":
            if "min" not in question["options"]:
                return (400, f"No minimum length was provided for question '{question['title']}'")
            if "max" not in question["options"]:
                return (400, f"No maximum length was provided for question '{question['title']}'")
            question["options"]["min"] = max(int(question["options"]["min"]), 1)
            question["options"]["max"] = min(int(question["options"]["max"]), 2000)
        elif question["type"] == "number":
            if "min" not in question["options"]:
                return (400, f"No minimum value was provided for question '{question['title']}'")
            if "max" not in question["options"]:
                return (400, f"No maximum value was provided for question '{question['title']}'")
            question["options"]["min"] = max(int(question["options"]["min"]), 2 ** 32)
            question["options"]["max"] = min(int(question["options"]["max"]), 2 ** 32)
        elif question["type"] == "multichoice":
            if "min" not in question["options"]:
                return (400, f"No minimum options was provided for question '{question['title']}'")
            if "max" not in question["options"]:
                return (400, f"No maximum options was provided for question '{question['title']}'")
            if not len(question["options"]["options"]):
                return (400, f"No options were provided for question '{question['title']}'")
            question["options"]["min"] = max(int(question["options"]["min"]), 1)
            question["options"]["max"] = min(int(question["options"]["max"]), len(question["options"]["options"]))
            fixed = {}
            for k, v in question["options"]["options"].items():
                fixed[int(k)] = v
            question["options"]["options"] = fixed
            for i in question["options"]["options"].keys():
                if len(question["options"]["options"][int(i)]) != 2:
                    return (400, f"Option '{i}' does not have a title")
                question["options"]["options"][int(i)][0] = question["options"]["options"][int(i)][0][:100]
                if isinstance(question["options"]["options"][int(i)][1], str):
                    question["options"]["options"][int(i)][1] = question["options"]["options"][int(i)][1][:100]
        elif question["type"] == "image-decoration":
            if "url" not in question["options"]:
                return (400, f"No image url was provided for question '{question['title']}'")
        elif question["type"] == "url-decoration":
            if "url" not in question["options"]:
                return (400, f"No url was provided for question '{question['title']}'")

        out["questions"].append(question)
    return out
