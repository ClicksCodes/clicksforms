import discord
import json

with open("./data/emojis.json") as emojis:
    _emojis = json.load(emojis)


class Emojis:
    def __init__(self, emojis=_emojis, progress=None, idOnly=False):
        self.emojis = emojis
        self.progress = progress or []
        self.idOnly = idOnly

    def convert(self, emoji):
        animated = ""
        if isinstance(self.emojis[emoji], str):
            animated = "a"
            emoji = self.emojis[emoji][1:]
        else:
            emoji = self.emojis[emoji]
        if self.idOnly:
            return emoji
        return f"<{animated}:a:{emoji}>"

    def __getattr__(self, item):
        self.progress.append(item)
        try:
            _ = self.emojis[".".join(self.progress)]
            return self.convert(".".join(self.progress))
        except KeyError:
            return self.__class__(self.emojis, self.progress, idOnly=self.idOnly)

    def __call__(self, item):
        try:
            _ = self.emojis[item]
            return self.convert(item)
        except KeyError:
            return KeyError(f"Emoji '{item}' does not exist")

    def __getitem__(self, item):
        try:
            _ = self.emojis[item]
            return self.convert(item)
        except KeyError:
            return KeyError(f"Emoji '{item}' does not exist")

    def __str__(self):
        return self.convert(".".join(self.progress))


class Colours:
    red = 0xF27878
    orange = 0xE5AB71
    yellow = 0xF2D478
    green = 0x65CC76
    blue = 0x71AFE5
    purple = 0xA358B2
    pink = 0xD46899
    grey = 0x777777

    c = '\033[0m'

    RedDark = '\033[31m'
    GreenDark = '\033[32m'
    YellowDark = '\033[33m'
    BlueDark = '\033[34m'
    PinkDark = '\033[35m'
    CyanDark = '\033[36m'

    Red = '\033[91m'
    Green = '\033[92m'
    Yellow = '\033[93m'
    Blue = '\033[94m'
    Pink = '\033[95m'
    Cyan = '\033[96m'


icons = {
    0: "Circle",
    1: "Square",
    2: "Triangle",
    3: "Cross",
    4: "Plus",
    5: "Minus",
    6: "Vertical line",
    7: "Star",
    8: "Diagonal line (Up)",
    9: "Diagonal line (Down)",
    10: "Mail",
    11: "Tick",
    12: "Left arrow",
    13: "Right arrow",
    14: "Up arrow",
    15: "Down arrow",
    16: "Code",
    17: "Exclamation mark",
    18: "Question mark",
    19: "At sign",
    20: "Elipsis",
    21: "Automation",
    22: "Shield",
    23: "Timer",
    24: "Pencil"
}

loading_embed = discord.Embed(
    title=f"{Emojis().loading} Loading",
    description="Your command is being processed",
    colour=Colours().red
).set_footer(text="If the message does not load in 5 seconds, something is probably broken")
