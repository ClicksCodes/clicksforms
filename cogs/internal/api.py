import datetime
import asyncio
import discord
from discord.client import _cancel_tasks
import uvicorn
from cogs.consts import *
from config import config

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import PlainTextResponse, JSONResponse


app = FastAPI(docs_url=None, redoc_url=None)
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


class GoogleFormsResponse(BaseModel):
    token: str
    data: dict
    code: str


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


async def addAndDelete(data):
    from bot import bot
    bot.codes[data["code"]] = data["data"]
    await asyncio.sleep(60 * 30)
    if data["code"] in bot.codes:
        del bot.codes[data["code"]]

@app.post("/googleforms")
async def responses(data: GoogleFormsResponse):
    data = dict(data)
    if data["token"] != config.gFormsToken:
        return PlainTextResponse("Invalid token", status_code=403)
    asyncio.create_task(addAndDelete(data))
    return PlainTextResponse("Success", status_code=200)


def setup(bot):
    config = uvicorn.Config(app, host="0.0.0.0", port=10006, lifespan="on", access_log=False, log_level="critical")
    server = uvicorn.Server(config)
    server.config.setup_event_loop()
    if not hasattr(bot, "loop"):
        return
    loop = bot.loop
    loop.create_task(server.serve())
    return
