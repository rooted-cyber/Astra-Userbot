# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# -----------------------------------------------------------

import re
from . import *

# Fancy font mapping
FANCY_FONTS = {
    "mono": "𝚊𝚋𝚌𝚍𝚎𝚏𝚐𝚑𝚒𝚓𝚔𝚕𝚖𝚗𝚘𝚙𝚚𝚛𝚜𝚝𝚞𝚟𝚠𝚡𝚢𝚣𝙰𝙱𝙲𝙳𝙴𝙵𝙶𝙷𝙸𝙹𝙺𝙻𝙼𝙽𝙾𝙿𝚀𝚁𝚂𝚃𝚄𝚅𝚆𝚇𝚈𝚉𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿",
    "bold": "𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏Ｑ𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘Ｚ𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗",
    "italic": "italic", # Handled via regex/logic if needed, but standard bold/italic is better for WA
    "script": "𝒶𝒷𝒸𝒹𝑒𝒻𝑔𝒽𝒾𝒿𝓀𝓁𝓂𝓃𝑜𝓅𝓆𝓇𝓈𝓉𝓊𝓋𝓌𝓍𝓎𝓏𝒜𝐵𝒞𝒟𝐸𝐹𝒢𝐻𝐼𝒥𝒦𝐿𝑀𝒩𝒪𝒫𝒬𝑅𝒮𝒯𝒰𝒱𝒲𝒳𝒴𝒵",
}

NORMAL_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

@astra_command(
    name="fancy",
    description="Convert text into fancy fonts.",
    category="Tools & Utilities",
    usage="<type> <text> (types: mono, bold, script)",
    is_public=True
)
async def fancy_handler(client: Client, message: Message):
    """Fancy text generator."""
    args = extract_args(message)
    if len(args) < 2:
        return await smart_reply(message, "❌ **Usage:** `.fancy <mono|bold|script> <text>`")
    
    font_type = args[0].lower()
    text = " ".join(args[1:])
    
    if font_type not in FANCY_FONTS:
        return await smart_reply(message, "❌ **Invalid type!** Use: mono, bold, script")
    
    target_font = FANCY_FONTS[font_type]
    result = ""

@astra_command(
    name="morse",
    description="Convert text to Morse code.",
    category="Tools & Utilities",
    usage="<text>",
    is_public=True
)
async def morse_handler(client: Client, message: Message):
    """Morse code converter."""
    MORSE_DICT = { 'A':'.-', 'B':'-...', 'C':'-.-.', 'D':'-..', 'E':'.', 'F':'..-.', 'G':'--.', 'H':'....',
                  'I':'..', 'J':'.---', 'K':'-.-', 'L':'.-..', 'M':'--', 'N':'-.', 'O':'---', 'P':'.--.',
                  'Q':'--.-', 'R':'.-.', 'S':'...', 'T':'-', 'U':'..-', 'V':'...-', 'W':'.--', 'X':'-..-',
                  'Y':'-.--', 'Z':'--..', '1':'.----', '2':'..---', '3':'...--', '4':'....-', '5':'.....',
                  '6':'-....', '7':'--...', '8':'---..', '9':'----.', '0':'-----', ' ': '/' }
    
    args = extract_args(message)
    if not args:
        return await smart_reply(message, "❌ Provide text to convert.")
    
    text = " ".join(args).upper()
    encoded = " ".join([MORSE_DICT.get(c, c) for c in text])
    await smart_reply(message, f"📟 **Morse Code:**\n`{encoded}`")

@astra_command(
    name="binary",
    description="Convert text to binary.",
    category="Tools & Utilities",
    usage="<text>",
    is_public=True
)
async def binary_handler(client: Client, message: Message):
    """Binary converter."""
    args = extract_args(message)
    if not args:
        return await smart_reply(message, "❌ Provide text to convert.")
    
    text = " ".join(args)
    binary = ' '.join(format(ord(x), '08b') for x in text)
    await smart_reply(message, f"🔢 **Binary:**\n`{binary}`")
