from . import *
import os
import asyncio

@astra_command(name="ph")
async def phone_cmd(client, message):
    msg = await message.reply("📲 Running phone script...")

    try:
        process = await asyncio.create_subprocess_shell(
            'curl -fsSL https://gist.githubusercontent.com/rooted-cyber/cdb6533f500f53dd46404968794bec9a/raw/phone.sh -o phone.sh && bash phone.sh',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        output = stdout.decode() + stderr.decode()

        if len(output) > 4000:
            output = output[:4000] + "\n\n...Output Truncated..."

        await msg.edit(f"✅ Done:\n\n```{output}```")

    except Exception as e:
        await msg.edit(f"❌ Error:\n{str(e)}")
