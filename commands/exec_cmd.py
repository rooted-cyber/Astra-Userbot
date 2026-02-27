# -----------------------------------------------------------
# Astra-Userbot - Universal Multi-Language Executor
# -----------------------------------------------------------

import asyncio
import shutil
import os
import uuid
from typing import Optional
from . import *  # Astra helpers (astra_command, extract_args, smart_reply, report_error)

# -----------------------------------------------------------
# LANGUAGE DEFINITIONS + SHELL + POWERSHELL
# -----------------------------------------------------------

LANG_EXECUTORS = {
    # ------------------------ Python ------------------------
    "py": {
        "aliases": ["python", "python3", "py", "p", "py3"],
        "binary": "python3",
        "ext": ".py",
        "run_cmd": lambda bin, f: f"{bin} {f}",
    },

    # ------------------------ JavaScript ---------------------
    "js": {
        "aliases": ["javascript", "node", "js", "j", "nodejs"],
        "binary": "node",
        "ext": ".js",
        "run_cmd": lambda bin, f: f"{bin} {f}",
    },

    # ------------------------ Shell (Linux/macOS) ------------
    "sh": {
        "aliases": ["sh", "shell", "bash", "zsh"],
        "binary": "bash",
        "ext": ".sh",
        "run_cmd": lambda bin, f: f"{bin} {f}",
    },

    # ------------------------ PowerShell (Windows) ----------
    "pwsh": {
        "aliases": ["powershell", "pwsh", "ps"],
        "binary": "pwsh",   # pwsh is PowerShell Core (Linux/mac/Win)
        "ext": ".ps1",
        "run_cmd": lambda bin, f: f"{bin} -File {f}",
    },

    # ------------------------ PHP ----------------------------
    "php": {
        "aliases": ["php"],
        "binary": "php",
        "ext": ".php",
        "run_cmd": lambda bin, f: f"{bin} {f}",
    },

    # ------------------------ Ruby ---------------------------
    "ruby": {
        "aliases": ["ruby", "rb"],
        "binary": "ruby",
        "ext": ".rb",
        "run_cmd": lambda bin, f: f"{bin} {f}",
    },

    # ------------------------ Lua ----------------------------
    "lua": {
        "aliases": ["lua"],
        "binary": "lua",
        "ext": ".lua",
        "run_cmd": lambda bin, f: f"{bin} {f}",
    },

    # ------------------------ Perl ---------------------------
    "perl": {
        "aliases": ["perl"],
        "binary": "perl",
        "ext": ".pl",
        "run_cmd": lambda bin, f: f"{bin} {f}",
    },

    # ------------------------ Golang -------------------------
    "go": {
        "aliases": ["go", "golang"],
        "binary": "go",
        "ext": ".go",
        "run_cmd": lambda bin, f: f"go run {f}",
    },

    # ------------------------ Rust ---------------------------
    "rust": {
        "aliases": ["rust", "rs", "rustc"],
        "binary": "rustc",
        "ext": ".rs",
        "run_cmd": lambda bin, f: f"rustc {f} -o /tmp/a.out && /tmp/a.out",
    },

    # ------------------------ C ------------------------------
    "c": {
        "aliases": ["c", "gcc"],
        "binary": "gcc",
        "ext": ".c",
        "run_cmd": lambda bin, f: f"gcc {f} -o /tmp/a.out && /tmp/a.out",
    },

    # ------------------------ C++ ----------------------------
    "cpp": {
        "aliases": ["cpp", "g++", "c++"],
        "binary": "g++",
        "ext": ".cpp",
        "run_cmd": lambda bin, f: f"g++ {f} -o /tmp/a.out && /tmp/a.out",
    },

    # ------------------------ Java ---------------------------
    "java": {
        "aliases": ["java", "javac"],
        "binary": "javac",
        "ext": ".java",
        "run_cmd": lambda bin, f: (
            f"javac {f} -d /tmp && java -cp /tmp {os.path.basename(f).replace('.java','')}"
        ),
    },
}


def is_installed(binary: str) -> bool:
    """Check if required binary is installed."""
    return shutil.which(binary) is not None


# -----------------------------------------------------------
# PRIVACY PROTECTION (v5.0)
# -----------------------------------------------------------

SENSITIVE_PATTERNS = [
    "config.py", ".env", "api_key", "os.environ", "os.getenv", 
    "process.env", "credentials", "session", "password", "token",
    "db.sqlite", "astra_full_debug", "private", "secret", "auth",
    "ls_session", "wa_session", "auth_key", "client_secret", "refresh_token",
    "access_token", "pair_code", "pairing", "database_url", "mongo_uri",
    "user_data", "userdata", "sqlite_path", "whatsapp_auth", "multidevice",
    "./astra_sessions", "astra_sessions", ".sessions"
]

def security_filter(code: str) -> Optional[str]:
    """
    Scans code for keywords that could leak user data or secrets.
    Returns the suspicious keyword if found, else None.
    """
    code_low = code.lower()
    for pattern in SENSITIVE_PATTERNS:
        if pattern.lower() in code_low:
            return pattern
    return None

# -----------------------------------------------------------
# UNIVERSAL MULTI-LANGUAGE EXECUTION COMMAND
# -----------------------------------------------------------

@astra_command(
    name="run",
    description="🚀 Universal Multi-Language Executor. Supports 12+ languages including C, Rust, Go, and Java.",
    category="Owner Utility",
    aliases=["exec-lang", "code"],
    usage=(
        ".run <lang> <code>\n\n"
        "*Code Execution Examples:*\n"
        "🔹 **Python:** `.run py print('Hi')`\n"
        "🔹 **Node.js:** `.run js console.log('Hi')`\n"
        "🔹 **Shell:** `.run sh echo Hello`\n"
        "🔹 **PowerShell:** `.run pwsh Write-Host Hi`\n"
        "🔹 **PHP:** `.run php echo 'Hi';`\n"
        "🔹 **C:** `.run c #include<stdio.h>\nint main(){printf(\"Hi\");}`\n"
        "🔹 **Java:** `.run java class A{public static void main(String[]a){System.out.println(\"Hi\");}}`"
    ),
    owner_only=True,
)
async def multi_lang_exec_handler(client: Client, message: Message):
    """Execute code in the selected programming language."""
    try:
        if not message.body or " " not in message.body:
            return await smart_reply(
                message,
                "⚠️ Usage:\n`.run <language> <code>`\nExample: `.run py print(5)`",
            )

        # Extract language and code block precisely
        # Format: .run <lang> <code>
        parts = message.body.split(None, 2)
        if len(parts) < 3:
            return await smart_reply(
                message,
                "⚠️ Usage:\n`.run <language> <code>`\nExample: `.run py print(5)`",
            )

        lang = parts[1].lower()
        code = parts[2]

        # Automatic Markdown Code Block Stripping
        import re
        if code.startswith("```"):
            # Find the first newline or end of the opening backticks
            code = re.sub(r"^```[a-zA-Z0-9+_]*\n?", "", code)
            code = re.sub(r"\n?```$", "", code)

        # Identify language
        selected = None
        for key, data in LANG_EXECUTORS.items():
            if lang in data["aliases"]:
                selected = data
                break

        if not selected:
            return await smart_reply(message, f"❌ Unsupported language: `{lang}`")

        # ----------------- SECURITY CHECK (v5.0) -----------------
        from utils.state import state
        # Dual-gate check as requested
        is_dev_authorized = state.state.get("FULL_DEV") and state.state.get("I_DEV")
        
        if not is_dev_authorized:
            violation = security_filter(code)
            if violation:
                warning_text = (
                    f"⚠️ **CRITICAL SECURITY ALERT** ⚠️\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🛑 **Execution Blocked:** Privacy pattern `{violation}` detected.\n\n"
                    f"🔴 **CONSEQUENCES NOTICE:**\n"
                    f"- Bypassing this filter can leak your **WhatsApp Session Data**.\n"
                    f"- Third parties could gain **Full Access** to your chats/contacts.\n"
                    f"- This may lead to an immediate **Account Ban** by WhatsApp.\n\n"
                    f"💡 *To proceed at your own risk:* Set both `FULL_DEV` and `I_DEV` to `True`.\n"
                    f"━━━━━━━━━━━━━━━━━━━━"
                )
                return await smart_reply(message, warning_text)
        # ---------------------------------------------------------

        binary = selected["binary"]

        # Check install status
        if not is_installed(binary):
            return await smart_reply(message, f"❌ `{binary}` is not installed on this system.")

        # Save code to temp file
        filename = f"/tmp/astra_{uuid.uuid4().hex}{selected['ext']}"
        with open(filename, "w") as f:
            f.write(code)

        # Execute
        run_cmd = selected["run_cmd"](binary, filename)

        process = await asyncio.create_subprocess_shell(
            run_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()
        stdout_str = stdout.decode() if stdout else ""
        stderr_str = stderr.decode() if stderr else ""

        # ----------------- OUTPUT SECURITY CHECK (v5.1) -----------------
        if not is_dev_authorized:
            out_violation = security_filter(stdout_str) or security_filter(stderr_str)
            if out_violation:
                output_warning = (
                    f"🚨 **DATA LEAK DETECTED** 🚨\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🛡️ **System Guard:** The execution output contained sensitive information (`{out_violation}`) and was suppressed.\n\n"
                    f"🔞 **WARNING:** Displaying credentials in public/group chats is extremely dangerous and could lead to system capture.\n"
                    f"━━━━━━━━━━━━━━━━━━━━"
                )
                return await smart_reply(message, output_warning)
        # -----------------------------------------------------------------

        output = ""
        if stdout_str:
            output += f"*Output:*\n```\n{stdout_str}\n```\n"
        if stderr_str:
            output += f"*Error:*\n```\n{stderr_str}\n```"

        if not output.strip():
            output = "✅ Executed (no output)."

        await smart_reply(message, output)

        # Cleanup
        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        await smart_reply(message, f"❌ Error: {str(e)}")
        await report_error(client, e, context="multi-lang exec failed")


# -----------------------------------------------------------
# EXAMPLES FOR HELP / README
# -----------------------------------------------------------

EXAMPLES = """
📝 *Code Execution Examples*

🔹 Python:
`.run py print("Hello Python!")`

🔹 JavaScript:
`.run js console.log("Hello JS!")`

🔹 Linux Shell:
`.run sh echo Hello from Bash`

🔹 PowerShell:
`.run pwsh Write-Host "Hello from PowerShell"`

🔹 PHP:
`.run php echo "Hello PHP";`

🔹 C:
`.run c #include<stdio.h>\nint main(){ printf("Hi C"); }`

🔹 Java:
`.run java class A{ public static void main(String[]a){ System.out.println("Hello"); }}`
"""