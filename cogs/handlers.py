import discord
from discord.mentions import A
from sqlalchemy.sql.expression import true
from cogs.consts import *
import databases
import orm
import sqlalchemy

database = databases.Database("sqlite:///main.db")
metadata = sqlalchemy.MetaData()

class GuildData(orm.Model):
    __tablename__ = "data"
    __database__ = database
    __metadata__ = metadata
    id = orm.Integer(primary_key=True)
    data = orm.JSON()
    responses = orm.JSON()


class Database:
    def __init__(self):
        self.db = GuildData

    async def get(self, guild):
        if isinstance(guild, discord.Guild):
            guild = guild.id
        try:
            return await self.db.objects.get(id=guild)
        except orm.NoMatch:
            return await self.create(guild=guild)

    async def create(self, guild):
        return await self.db.objects.create(id=guild, data=[], responses={})


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
