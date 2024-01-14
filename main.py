from pyrogram import Client
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from plugins.notion import update_deadlines

import config

plugins = dict(
    root='plugins'
)

app = Client(
    name=config.BOT_NAME,
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
    plugins=plugins,
)

scheduler = AsyncIOScheduler()
scheduler.add_job(update_deadlines, "interval", args=[app], seconds=5)

scheduler.start()
app.run()
