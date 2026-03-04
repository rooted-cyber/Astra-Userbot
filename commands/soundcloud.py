from utils.helpers import handle_command_error
from utils.media_channel import MediaChannel

from . import *


@astra_command(
    name="soundcloud",
    description="Download SoundCloud track",
    category="Media & Downloads",
    aliases=["sc"],
    usage="<url> (SoundCloud track link)",
    owner_only=False,
)
async def soundcloud_handler(client: Client, message: Message):
    """Download SoundCloud track with optimized MediaChannel"""
    try:
        args_list = extract_args(message)
        if not args_list:
            return await smart_reply(message, " ❌ Please provide a SoundCloud URL.")

        url = args_list[0]
        status_msg = await smart_reply(message, " 🔍 *Initializing SoundCloud Engine...*")

        channel = MediaChannel(client, message, status_msg)
        # SoundCloud is audio
        file_path, metadata = await channel.run_bridge(url, "audio")
        await channel.upload_file(file_path, metadata, "audio")

    except Exception as e:
        await handle_command_error(client, message, e, context="SoundCloud command failure")
