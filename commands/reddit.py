from utils.helpers import handle_command_error
from utils.media_channel import MediaChannel

from . import *


@astra_command(
    name="reddit",
    description="Download Reddit video",
    category="Media & Downloads",
    aliases=["rd"],
    usage="<url> (Reddit post link)",
    owner_only=False,
)
async def reddit_handler(client: Client, message: Message):
    """Download Reddit video with optimized MediaChannel"""
    try:
        args_list = extract_args(message)
        if not args_list:
            return await smart_reply(message, " ❌ Please provide a Reddit URL.")

        url = args_list[0]
        status_msg = await smart_reply(message, " 🔍 *Initializing Reddit Engine...*")

        channel = MediaChannel(client, message, status_msg)
        file_path, metadata = await channel.run_bridge(url, "video")
        await channel.upload_file(file_path, metadata, "video")

    except Exception as e:
        await handle_command_error(client, message, e, context="Reddit command failure")
