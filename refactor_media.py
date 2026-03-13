import os
import re

COMMANDS_DIR = "/Users/paman7647/ASTRAUB/astra_userbot_test/commands"

for root, _, files in os.walk(COMMANDS_DIR):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            with open(path, "r") as f:
                content = f.read()
            
            # Special case for quote.py (sticker)
            processed_content = content
            if file == "quote.py":
                processed_content = processed_content.replace("client.send_media(message.chat_id, media, is_sticker=True)", "client.send_sticker(message.chat_id, media)")
            
            # Special case for sticker.py line 181 (document)
            if file == "sticker.py":
                processed_content = processed_content.replace("client.send_media(str(message.chat_id), media, document=True)", "client.send_file(str(message.chat_id), media, document=True)")

            # General replacement: send_media -> send_photo
            new_content = re.sub(r"client\.send_media\(", "client.send_photo(", processed_content)
            
            if new_content != content:
                print(f"Refactored: {file}")
                with open(path, "w") as f:
                    f.write(new_content)
