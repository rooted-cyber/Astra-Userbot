
from . import *
from utils.media_channel import MediaChannel
from utils.helpers import handle_command_error

@astra_command(
    name="facebook",
    description="Download Facebook video",
    category="Media & Downloads",
    aliases=["fb"],
    usage="<url> (Facebook video link)",
    owner_only=False
)
async def facebook_handler(client: Client, message: Message):
    """Download Facebook video with optimized MediaChannel"""
    try:
        args_list = extract_args(message)
        if not args_list:
            return await smart_reply(message, " ❌ Please provide a Facebook URL.")

        url = args_list[0]
        status_msg = await smart_reply(message, f" 🔍 *Initializing Facebook Engine...*")

        channel = MediaChannel(client, message, status_msg)
        file_path, metadata = await channel.run_bridge(url, "video")
        await channel.upload_file(file_path, metadata, "video")

    except Exception as e:
        await handle_command_error(client, message, e, context='Facebook command failure')
