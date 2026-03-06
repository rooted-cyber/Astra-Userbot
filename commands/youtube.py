from . import *
from utils.helpers import edit_or_reply
from utils.ui_templates import UI


@astra_command(
    name="youtube",
    description="Download media from YouTube. Supports auto-search for queries.",
    category="Media & Downloads",
    aliases=["yt", "ytdl"],
    usage="<url|query> [video|audio]",
    owner_only=False,
)
async def youtube_handler(client: Client, message: Message):
    """
    Handles media download requests with optimized MediaChannel.
    """
    args_list = extract_args(message)
    if not args_list:
        return await edit_or_reply(message, f"{UI.mono('[ ERROR ]')} Target URL or query required.")

    url_input = args_list[0]
    args_lower = [arg.lower() for arg in args_list]

    # Mode detection
    video_keywords = ["video", "vid", "mp4", "mkv", "720p", "1080p"]
    mode = "video" if any(kw in args_lower for kw in video_keywords) else "audio"

    status_msg = await edit_or_reply(
        message, f"{UI.header('MEDIA ENGINE')}\n{UI.mono('[ BUSY ]')} Initializing request..."
    )

    # Auto-Search Logic
    url = url_input
    if not url_input.startswith(("http://", "https://", "www.")):
        search_query = " ".join(args_list)
        if " video" in search_query.lower() or " audio" in search_query.lower():
            search_query = search_query.rsplit(" ", 1)[0]

        await status_msg.edit(
            f"{UI.header('MEDIA TRACKING')}\n{UI.mono('[ BUSY ]')} Resolving: {UI.mono(search_query[:30])}..."
        )

        try:
            import yt_dlp

            ydl_opts = {"quiet": True, "extract_flat": True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                search_result = ydl.extract_info(f"ytsearch1:{search_query}", download=False)
                if search_result.get("entries"):
                    entry = search_result["entries"][0]
                    url = f"https://www.youtube.com/watch?v={entry['id']}"
                    duration = entry.get("duration_string") or (
                        f"{int(entry['duration']) // 60}:{int(entry['duration']) % 60:02d}"
                        if entry.get("duration")
                        else "N/A"
                    )
                    await status_msg.edit(
                        f"{UI.header('MEDIA TRACKING')}\n"
                        f"Title    : {UI.mono(entry['title'][:40])}\n"
                        f"Duration : {UI.mono(duration)}\n\n"
                        f"{UI.mono('[ BUSY ]')} Routing to local gateway..."
                    )
                else:
                    return await status_msg.edit(f"{UI.mono('[ ERROR ]')} No matches found for {UI.mono(search_query)}.")
        except Exception as e:
            return await status_msg.edit(f"{UI.mono('[ ERROR ]')} Network failure: {UI.mono(str(e))}")

    # Use MediaChannel for a "real-time" experience
    from utils.media_channel import MediaChannel

    channel = MediaChannel(client, message, status_msg)

    # 1. Download
    file_path, metadata = await channel.run_bridge(url, mode)

    # 2. Upload
    await channel.upload_file(file_path, metadata, mode)
