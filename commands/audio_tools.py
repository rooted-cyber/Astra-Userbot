import asyncio
import os
import time

from utils.bridge_downloader import bridge_downloader
from utils.plugin_utils import extract_args
from . import *
from utils.helpers import edit_or_reply
from utils.ui_templates import UI

async def apply_audio_effect(client: Client, message: Message, effect: str):
    target = message.quoted if message.has_quoted_msg else message
    if not target.is_media:
        return await edit_or_reply(message, f"{UI.mono('error')} Target audio/media segment required.")

    status_txt = f"{UI.header('AUDIO PROCESSING')}\n{UI.mono('processing')} Applying {UI.mono(effect)} filter..."
    status_msg = await edit_or_reply(message, status_txt)
    temp_in = f"/tmp/astra_audio_in_{int(time.time())}.mp3"
    temp_out = f"/tmp/astra_audio_out_{int(time.time())}.mp3"
    
    try:
        media_data = await bridge_downloader.download_media(client, message)
        if not media_data:
            return await status_msg.edit(f"{UI.mono('error')} Source download failed.")
        
        with open(temp_in, "wb") as f:
            f.write(media_data)
        
        media_path = temp_in

        # Build FFmpeg command based on effect
        filter_str = ""
        if effect == "bassboost":
            filter_str = "bass=g=15:f=110:w=0.6"
        elif effect == "nightcore":
            filter_str = "asetrate=44100*1.25,aresample=44100,atempo=1.25"
        elif effect == "slowed":
            # Slowed + Reverb
            filter_str = "asetrate=44100*0.85,aresample=44100,atempo=0.85,aecho=0.8:0.88:60:0.4"
        elif effect == "reverse":
            filter_str = "areverse"
        elif effect == "echo":
            filter_str = "aecho=0.8:0.9:1000:0.3"
        elif effect == "8daudio":
            filter_str = "apulsator=hz=0.125"
        else:
            return await status_msg.edit(f"{UI.mono('error')} Invalid filter parameter.")

        cmd = [
            "ffmpeg", "-y", "-i", temp_in, 
            "-af", filter_str, 
            "-c:a", "libmp3lame", "-q:a", "2", 
            temp_out
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        args = extract_args(message)
        as_doc = "-d" in args
        
        if process.returncode != 0:
            return await status_msg.edit(f"{UI.mono('error')} FFmpeg pipeline failure.")

        if as_doc:
            await client.send_document(
                message.chat_id, 
                temp_out, 
                caption=f"{UI.mono('done')} Filter applied: {UI.mono(effect)}"
            )
        else:
            await client.send_audio(
                message.chat_id, 
                temp_out, 
                caption=f"{UI.mono('done')} Filter applied: {UI.mono(effect)}",
                as_voice=True
            )
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit(f"{UI.mono('error')} Fatal exception: {UI.mono(str(e))}")
    finally:
        if os.path.exists(temp_in):
            os.remove(temp_in)
        if os.path.exists(temp_out):
            os.remove(temp_out)

@astra_command(name="bassboost", description="Apply bass boost to audio.", category="Tools & Utilities", is_public=True)
async def bassboost_handler(client: Client, message: Message):
    await apply_audio_effect(client, message, "bassboost")

@astra_command(name="nightcore", description="Apply nightcore (speed+pitch up) to audio.", category="Tools & Utilities", is_public=True)
async def nightcore_handler(client: Client, message: Message):
    await apply_audio_effect(client, message, "nightcore")

@astra_command(name="slowed", description="Apply slowed+reverb (pitch down+slow) to audio.", category="Tools & Utilities", is_public=True)
async def slowed_handler(client: Client, message: Message):
    await apply_audio_effect(client, message, "slowed")

@astra_command(name="reverseaudio", description="Reverse audio.", category="Tools & Utilities", is_public=True)
async def reverseaudio_handler(client: Client, message: Message):
    await apply_audio_effect(client, message, "reverse")

@astra_command(name="echo", description="Add an echo effect to audio.", category="Tools & Utilities", is_public=True)
async def echo_handler(client: Client, message: Message):
    await apply_audio_effect(client, message, "echo")

@astra_command(name="8daudio", description="Apply 8D panning effect to audio.", category="Tools & Utilities", is_public=True)
async def eightdaudio_handler(client: Client, message: Message):
    await apply_audio_effect(client, message, "8daudio")
