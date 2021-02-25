import json
import discord

with open("./data/emojis.json") as rfile:
    emojis = json.load(rfile)


class C:
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


class Decorations:
    header = emojis["sectionheader"]
    text = emojis["sectiontext"]
    image = emojis["sectionimage"]
    link = emojis["sectionlink"]


class Types:
    text = emojis["text"]
    number = emojis["number"]
    multichoice = emojis["multiplechoice"]
    tickbox = emojis["checkbox"]
    fileupload = emojis["fileupload"]
    date = emojis["date"]
    time = emojis["time"]
    decoration = emojis["decoration"]

    special_section = Decorations.header
    special_text = Decorations.text
    special_image = Decorations.image
    special_link = Decorations.link


class Features:
    title = emojis["qtitle"]
    description = emojis["qdescription"]
    colour = emojis["qcolour"]
    required = emojis["qrequired"]
    changeimg = emojis["changeimg"]
    changeurl = emojis["changeurl"]

    anon = emojis["anon"]
    nanon = emojis["nanon"]


class Responses:
    r1 = emojis["r1"]
    r2 = emojis["r2"]
    r3 = emojis["r3"]
    r4 = emojis["r4"]
    r5 = emojis["r5"]
    r6 = emojis["r6"]
    r7 = emojis["r7"]
    r8 = emojis["r8"]


class Colours:
    r = emojis["r"]
    o = emojis["o"]
    y = emojis["y"]
    g = emojis["g"]
    b = emojis["b"]
    m = emojis["m"]
    p = emojis["p"]
    n = emojis["n"]


class Main:
    new = emojis["newquestion"]
    remove = emojis["rmquestion"]
    save = emojis["save"]
    meta = emojis["editmeta"]


class Question:
    valid = emojis["valid"]  # Validation (green)
    nvalid = emojis["nvalid"]  # No validation (red)
    required = emojis["required"]  # Required (green)
    nrequired = emojis["nrequired"]  # Not required (red)
    options = emojis["options"]  # Change options (multichoice)


class Roles:
    roles = emojis["roles"]["roles"]
    noauto = emojis["roles"]["noauto"]
    given = emojis["roles"]["given"]
    removed = emojis["roles"]["removed"]
    required = emojis["roles"]["required"]
    disallowed = emojis["roles"]["disallowed"]


class Channels:
    channelwl = emojis["channelWl"]
    channelbl = emojis["channelBl"]
    formCat = emojis["formCat"]
    anywhere = emojis["anywhere"]


class Emojis:
    types = Types
    decorations = Decorations
    features = Features
    main = Main
    responses = Responses
    colours = Colours
    question = Question
    roles = Roles
    channels = Channels

    calendar = emojis["calendar"]

    left = emojis['left']
    right = emojis['right']
    tick = emojis['tick']
    cross = emojis['cross']


class Colours:
    red = 0xF27878
    orange = 0xE5AB71
    yellow = 0xF2D478
    green = 0x65CC76
    blue = 0x71AFE5
    purple = 0xA358B2
    pink = 0xD46899
    grey = 0x777777


class Descriptions:
    text = "Please send a text response"
    number = "Please send a number"
    multichoice = "Pick any one from the following choices:"
    tickbox = f"Pick all that apply from the following choices, then click <:e:{Emojis.right}>"
    fileupload = "Please send an image or file. Only your first will count."
    date = "Loading..."
    time = "Loading..."

    special_section = "THIS SHOULD NOT BE SEEN"
    special_text = "THIS SHOULD NOT BE SEEN"
    special_image = "THIS SHOULD NOT BE SEEN"
    special_link = "THIS SHOULD NOT BE SEEN"


loadingEmbed = discord.Embed(
    title="Loading",
    color=Colours.red
)
