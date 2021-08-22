import datetime
import discord
import uvicorn
from cogs.consts import *
from config import config

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import PlainTextResponse, JSONResponse


app = FastAPI()
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


def setup(bot):
    config = uvicorn.Config(app, host="0.0.0.0", port=10006, lifespan="on", access_log=False, log_level="critical")
    server = uvicorn.Server(config)
    server.config.setup_event_loop()
    if not hasattr(bot, "loop"):
        return
    loop = bot.loop
    loop.create_task(server.serve())
    return
