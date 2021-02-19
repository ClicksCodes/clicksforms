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
    changeimg = 812273033649717298  # Change image (green)
    changeurl = 812276265293578250  # Change URL (green)


class Responses:
    r1 = 805737834098065408  # Circle
    r2 = 805737834069622814  # Triangle
    r3 = 805737834136731658  # Square
    r4 = 805737833792536597  # Cross
    r5 = 805737834005921812  # Plus
    r6 = 805737833813377065  # Horizontal
    r7 = 805737833972236308  # Vertical
    r8 = 805737833879961600  # Star


class Colours:
    r = 805739333104566272  # Red
    o = 805739333210210334  # Orange
    y = 805739333080449074  # Yellow
    g = 805739333176262657  # Green
    b = 805739333268013176  # Blue
    m = 805739333444435988  # Magenta
    p = 805739333247041586  # Pink
    n = 806120964202168350  # Grey (none)


class Main:
    new = emojis["newquestion"]
    remove = emojis["rmquestion"]
    save = emojis["save"]
    meta = emojis["editmeta"]


class Question:
    valid = 812255889611554837  # Validation (green)
    nvalid = 812255889276665910  # No validation (red)
    required = 812255889796890644  # Required (green)
    nrequired = 812255889439850506  # Not required (red)
    options = 812255889691508786  # Change options (multichoice)


class Emojis:
    types = Types
    decorations = Decorations
    features = Features
    main = Main
    responses = Responses
    colours = Colours
    question = Question

    calendar = {
        1:  "<:e:811929465194020906>",
        2:  "<:e:811929465423790110>",
        3:  "<:e:811929465197428737>",
        4:  "<:e:811929465605193728>",
        5:  "<:e:811929465134645309>",
        6:  "<:e:811929465541623859>",
        7:  "<:e:811929465583435806>",
        8:  "<:e:811929465680035881>",
        9:  "<:e:811929465680035840>",
        10: "<:e:811929465659719720>",
        11: "<:e:811929465817923584>",
        12: "<:e:811929465542148097>",
        13: "<:e:811929465750945832>",
        14: "<:e:811929465974292500>",
        15: "<:e:811929465793150976>",
        16: "<:e:811929465764446238>",
        17: "<:e:811929465818447882>",
        18: "<:e:811929465776766978>",
        19: "<:e:811929465734955049>",
        20: "<:e:811929466074824724>",
        21: "<:e:811929465927368704>",
        22: "<:e:811929465931300875>",
        23: "<:e:811929466065780776>",
        24: "<:e:811929466057523240>",
        25: "<:e:811929466318225438>",
        26: "<:e:811929466326614036>",
        27: "<:e:811929466330808340>",
        28: "<:e:811929466438942780>",
        29: "<:e:811929466363707412>",
        30: "<:e:811929466388480000>",
        31: "<:e:811929466241679401>",
        "M": "<:e:811929465960661014>",
        "T": "<:e:811929465755533314>",
        "W": "<:e:811929466234077194>",
        "F": "<:e:811929466330284032>",
        "S": "<:e:811929466280476712>",
        "B": "<:e:811929466033012736>"
    }

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
