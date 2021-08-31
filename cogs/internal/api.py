import asyncio
import random
import typing
import uvicorn
from cogs.consts import *
from config import config

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import PlainTextResponse, JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address


app = FastAPI(docs_url=None, redoc_url=None)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
colours = Colours()
emojis = Emojis

@app.get("/")
def root():
    from bot import bot
    return PlainTextResponse(str(bot.latency))

@app.get("/in/{guild}")
async def inGuild(guild: int):
    from bot import bot
    if guild in [g.id for g in bot.guilds]:
        return PlainTextResponse("True", 200)
    return PlainTextResponse("False", 404)

class Auth(BaseModel):
    token: str
    guild: int


class ServiceResponse(BaseModel):
    token: typing.Optional[str]
    service: str
    service_url: str
    data: dict


@app.get("/forms")
async def forms(auth: Auth):
    from cogs.handlers import Database
    data = dict(auth)
    if data["token"] != config.rsmToken:
        return PlainTextResponse("Invalid token", status_code=403)
    entry = await Database().get(data["guild"])
    if not entry.data:
        return PlainTextResponse("No forms found", status_code=404)
    return JSONResponse(entry.data, status_code=200)


@app.get("/responses")
async def responses(auth: Auth):
    from cogs.handlers import Database
    data = dict(auth)
    if data["token"] != config.rsmToken:
        return PlainTextResponse("Invalid token", status_code=403)
    entry = await Database().get(data["guild"])
    if not entry.responses:
        return PlainTextResponse("No forms found", status_code=404)
    return JSONResponse(entry.responses, status_code=200)


async def addAndDelete(data, verified, code):
    from bot import bot
    bot.codes[code] = (data["data"], verified, (data["service"], data["service_url"]))
    await asyncio.sleep(60 * 60)
    if code in bot.codes:
        del bot.codes[code]


@app.post("/upload")
async def responses(data: ServiceResponse):
    from bot import bot
    from cogs.handlers import parsedForm
    data = dict(data)

    data["data"] = parsedForm(data["data"])
    if isinstance(data["data"], int):
        return PlainTextResponse("400", status_code=data["data"])

    verified = False
    code = ""
    tries = 0
    chars = 5
    while (not len(code)) or (code in bot.codes):
        if tries >= 26 ** chars - 5:
            tries = 0
            chars += 1
        code = "".join([random.choice(list("0123456789ABCDEFGHJKLMNPQRTUWXYZ")) for _ in range(5)])
        await asyncio.sleep(0)
    if data["service"].lower() == "google forms" and data["token"] == config.gFormsToken:
        verified = True
    asyncio.create_task(addAndDelete(data, verified, code))
    return PlainTextResponse(code, status_code=201)


def setup(bot):
    config = uvicorn.Config(app, host="0.0.0.0", port=10006, lifespan="on", access_log=False, log_level="critical")
    server = uvicorn.Server(config)
    server.config.setup_event_loop()
    if not hasattr(bot, "loop"):
        return
    loop = bot.loop
    loop.create_task(server.serve())
    return
