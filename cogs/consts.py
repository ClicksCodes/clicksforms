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


class Responses:
    r1 = 805737834098065408
    r2 = 805737834069622814
    r3 = 805737834136731658
    r4 = 805737833792536597
    r5 = 805737834005921812
    r6 = 805737833813377065
    r7 = 805737833972236308
    r8 = 805737833879961600


class Colours:
    r = 805739333104566272
    o = 805739333210210334
    y = 805739333080449074
    g = 805739333176262657
    b = 805739333268013176
    m = 805739333444435988
    p = 805739333247041586
    n = 806120964202168350


class Main:
    new = emojis["newquestion"]
    remove = emojis["rmquestion"]
    save = emojis["save"]
    meta = emojis["editmeta"]


class Emojis:
    types = Types
    decorations = Decorations
    features = Features
    main = Main
    responses = Responses
    colours = Colours

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
    tickbox = f"Pick all that apply from the following choices, then click <:e:{Emojis.tick}>"
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
