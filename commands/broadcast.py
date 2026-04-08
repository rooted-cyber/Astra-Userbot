import time

from . import *
from utils.helpers import edit_or_reply
from utils.ui_templates import UI


@astra_command(
    name="bc", description="Broadcast a message to all your chats.", category="Owner", usage="<text>", owner_only=True
)
async def broadcast_handler(client: Client, message: Message):
    """Mass broadcast to all chats."""
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, f"{UI.bold('USAGE:')} {UI.mono('.bc <text>')}")

    text = " ".join(args)
    status_msg = await edit_or_reply(
        message, f"{UI.header('BROADCAST ENGINE')}\n{UI.mono('processing')} Starting distribution..."
    )

    all_chats = await client.chat.get_all_chats()
    total = len(all_chats) or 0
    success = 0
    failed = 0

    await status_msg.edit(
        f"{UI.header('BROADCAST ENGINE')}\n{UI.mono('processing')} syncing {UI.mono(total)} chats...\n{UI.italic('Processing distribution window...')}"
    )

    for i, chat in enumerate(all_chats):
        try:
            # Slower cooldown for large scale distribution
            time.sleep(1.5)
            await client.send_message(chat.id, text)
            success += 1
        except:
            failed += 1

        if (i + 1) % 5 == 0:
            await status_msg.edit(
                f"{UI.header('BROADCAST ENGINE')}\n"
                f"Progress : {UI.mono(f'{i + 1}/{total}')}\n"
                f"Success  : {UI.mono(success)}\n"
                f"Failed   : {UI.mono(failed)}"
            )

    await status_msg.edit(
        f"{UI.header('BROADCAST COMPLETE')}\n"
        f"Success  : {UI.mono(success)}\n"
        f"Failed   : {UI.mono(failed)}\n"
        f"Total    : {UI.mono(total)}"
    )


@astra_command(
    name="bcgc",
    description="Broadcast a message to all your groups.",
    category="Owner",
    usage="<text>",
    owner_only=True,
)
async def broadcast_gc_handler(client: Client, message: Message):
    """Mass broadcast to groups only."""
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, f"{UI.bold('USAGE:')} {UI.mono('.bcgc <text>')}")

    text = " ".join(args)
    status_msg = await edit_or_reply(
        message, f"{UI.header('GROUP BROADCAST')}\n{UI.mono('processing')} Filtering group segments..."
    )

    all_chats = await client.chat.get_all_chats()
    groups = [c for c in all_chats if str(c.id).endswith("@g.us")]
    total = len(groups)
    success = 0
    failed = 0

    if not groups:
        return await status_msg.edit("❌ No groups found.")

    await status_msg.edit(
        f"{UI.header('GROUP BROADCAST')}\n{UI.mono('processing')} syncing {UI.mono(total)} groups..."
    )

    for i, gc in enumerate(groups):
        try:
            time.sleep(2)  # Slower for groups
            await client.send_message(gc.id, text)
            success += 1
        except:
            failed += 1

        if (i + 1) % 3 == 0:
            await status_msg.edit(
                f"{UI.header('GROUP BROADCAST')}\n"
                f"Progress : {UI.mono(f'{i + 1}/{total}')}\n"
                f"Success  : {UI.mono(success)}"
            )

    await status_msg.edit(
        f"{UI.header('BROADCAST COMPLETE')}\n"
        f"Success  : {UI.mono(success)}\n"
        f"Failed   : {UI.mono(failed)}\n"
        f"Total    : {UI.mono(total)}"
    )
