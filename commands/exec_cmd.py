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
# LANGUAGE DEFINITIONS (CORE / MOST USED)
# -----------------------------------------------------------

LANG_EXECUTORS = {
    # ------------------------ Python ------------------------
    "py": {
        "name": "Python",
        "icon": "🐍",
        "aliases": ["python", "python3", "py", "p", "py3"],
        "binary": "python3",
        "package": "python3",
        "ext": ".py",
        "run_cmd": lambda bin, f: f"{bin} {f}",
    },

    # ------------------------ JavaScript ---------------------
    "js": {
        "name": "JavaScript",
        "icon": "🟨",
        "aliases": ["javascript", "node", "js", "j", "nodejs"],
        "binary": "node",
        "package": "nodejs",
        "ext": ".js",
        "run_cmd": lambda bin, f: f"{bin} {f}",
    },

    # ------------------------ TypeScript ---------------------
    "ts": {
        "name": "TypeScript",
        "icon": "🟦",
        "aliases": ["typescript", "ts"],
        "binary": "tsc",
        "package": "typescript",
        "ext": ".ts",
        "run_cmd": lambda bin, f: f"tsc {f} --outFile /tmp/a.js && node /tmp/a.js",
    },

    # ------------------------ Java ---------------------------
    "java": {
        "name": "Java",
        "icon": "☕",
        "aliases": ["java", "javac"],
        "binary": "javac",
        "package": "default-jdk",
        "ext": ".java",
        "run_cmd": lambda bin, f: (
            f"javac {f} -d /tmp && java -cp /tmp {os.path.basename(f).replace('.java','')}"
        ),
    },

    # ------------------------ C ------------------------------
    "c": {
        "name": "C",
        "icon": "🔵",
        "aliases": ["c", "gcc"],
        "binary": "gcc",
        "package": "gcc",
        "ext": ".c",
        "run_cmd": lambda bin, f: f"gcc {f} -o /tmp/a.out && /tmp/a.out",
    },

    # ------------------------ C++ ----------------------------
    "cpp": {
        "name": "C++",
        "icon": "💠",
        "aliases": ["cpp", "g++", "c++"],
        "binary": "g++",
        "package": "g++",
        "ext": ".cpp",
        "run_cmd": lambda bin, f: f"g++ {f} -o /tmp/a.out && /tmp/a.out",
    },

    # ------------------------ Rust ---------------------------
    "rust": {
        "name": "Rust",
        "icon": "🦀",
        "aliases": ["rust", "rs", "rustc"],
        "binary": "rustc",
        "package": "rustc",
        "ext": ".rs",
        "run_cmd": lambda bin, f: f"rustc {f} -o /tmp/a.out && /tmp/a.out",
    },

    # ------------------------ Golang -------------------------
    "go": {
        "name": "Golang",
        "icon": "🐹",
        "aliases": ["go", "golang"],
        "binary": "go",
        "package": "golang-go",
        "ext": ".go",
        "run_cmd": lambda bin, f: f"go run {f}",
    },

    # ------------------------ PHP ----------------------------
    "php": {
        "name": "PHP",
        "icon": "🐘",
        "aliases": ["php"],
        "binary": "php",
        "package": "php-cli",
        "ext": ".php",
        "run_cmd": lambda bin, f: f"{bin} {f}",
    },

    # ------------------------ Ruby ---------------------------
    "ruby": {
        "name": "Ruby",
        "icon": "💎",
        "aliases": ["ruby", "rb"],
        "binary": "ruby",
        "package": "ruby-full",
        "ext": ".rb",
        "run_cmd": lambda bin, f: f"{bin} {f}",
    },

    # ------------------------ Kotlin -------------------------
    "kt": {
        "name": "Kotlin",
        "icon": "💜",
        "aliases": ["kotlin", "kt"],
        "binary": "kotlinc",
        "package": "kotlinc",
        "ext": ".kt",
        "run_cmd": lambda bin, f: f"kotlinc {f} -include-runtime -d /tmp/a.jar && java -jar /tmp/a.jar",
    },

    # ------------------------ Swift --------------------------
    "swift": {
        "name": "Swift",
        "icon": "🍎",
        "aliases": ["swift"],
        "binary": "swift",
        "package": "swift",
        "ext": ".swift",
        "run_cmd": lambda bin, f: f"{bin} {f}",
    },

    # ------------------------ C# / Mono ----------------------
    "cs": {
        "name": "C Sharp",
        "icon": "🗄️",
        "aliases": ["csharp", "cs"],
        "binary": "mcs",
        "package": "mono-complete",
        "ext": ".cs",
        "run_cmd": lambda bin, f: f"mcs {f} -out:/tmp/a.exe && mono /tmp/a.exe",
    },

    # ------------------------ Shell (Linux/macOS) ------------
    "sh": {
        "name": "Shell",
        "icon": "🐚",
        "aliases": ["sh", "shell", "bash", "zsh"],
        "binary": "bash",
        "package": "bash",
        "ext": ".sh",
        "run_cmd": lambda bin, f: f"{bin} {f}",
    },
}


def is_installed(binary: str) -> bool:
    """Check if required binary is installed."""
    return shutil.which(binary) is not None


# -----------------------------------------------------------
# PRIVACY PROTECTION (v6.0)
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
    description="🚀 Universal Multi-Language Executor. Supports popular languages like Python, JS, Java, and Rust.",
    category="Owner Utility",
    aliases=["exec-lang", "code"],
    usage=(
        ".run <lang> <code>\n\n"
        "*Core Language Stack Examples:*\n"
        "🔹 **Python:** `.run py print('Hi')`\n"
        "🔹 **TypeScript:** `.run ts console.log('Hi')`\n"
        "🔹 **C:** `.run c main(){ printf(\"Hi\"); }`\n"
        "🔹 **Kotlin:** `.run kt fun main(){println(\"Hi\")}`\n"
        "🔹 **Rust:** `.run rust fn main(){println!(\"Hi\");}`\n"
        "🔹 **C++:** `.run cpp main(){ cout<<\"Hi\"; }`"
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

        # 🚀 Send "Executing" status
        icon = selected.get("icon", "🚀")
        name = selected.get("name", lang.upper())
        status_msg = await smart_reply(message, f"{icon} *Executing {name}...*")

        # ----------------- SECURITY CHECK (v6.0) -----------------
        from utils.state import state
        # is_full_dev = skip everything. is_i_dev = bypass if violation.
        is_full_dev = state.state.get("FULL_DEV", False)
        is_i_dev = state.state.get("I_DEV", False)
        
        if not is_full_dev:
            violation = security_filter(code)
            if violation and not is_i_dev:
                warning_text = (
                    f"🚨 **SECURITY RESTRICTION** 🚨\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🛑 **Blocked:** Potential privacy leak (`{violation}`).\n\n"
                    f"🛠️ **Developer?** If you know what you are doing, set `I_DEV` to `True` to bypass this filter.\n"
                    f"💡 *Command:* `.setdb I_DEV True`\n\n"
                    f"🔥 **Global Bypass:** Set `FULL_DEV` to `True` for zero restrictions.\n"
                    f"━━━━━━━━━━━━━━━━━━━━"
                )
                return await smart_reply(message, warning_text)
        # ---------------------------------------------------------

        binary = selected["binary"]
        pkg = selected.get("package", binary)

        # Check install status
        if not is_installed(binary):
            import platform
            system = platform.system().lower()
            suggest_cmd = f"apt install {pkg} -y" if system == "linux" else f"brew install {pkg}"
            
            await status_msg.edit(
                f"❌ `{name}` environment not found.\n\n"
                f"💡 *Suggestion:* Run `{suggest_cmd}` or use `.installdeps {lang}`"
            )
            return

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

        # ----------------- OUTPUT SECURITY CHECK (v6.1) -----------------
        if not is_full_dev:
            out_violation = security_filter(stdout_str) or security_filter(stderr_str)
            if out_violation and not is_i_dev:
                output_warning = (
                    f"🚨 **OUTPUT RESTRICTED** 🚨\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🛡️ **System Guard:** Sensitive data (`{out_violation}`) detected in output and was suppressed.\n\n"
                    f"🛠️ **Developer?** Set `I_DEV` to `True` to see raw output or `FULL_DEV` for global bypass.\n"
                    f"━━━━━━━━━━━━━━━━━━━━"
                )
                return await smart_reply(message, output_warning)
        # -----------------------------------------------------------------

        output = ""
        if stdout_str:
            output += f"✅ *Output ({name}):*\n```\n{stdout_str}\n```\n"
        if stderr_str:
            output += f"❌ *Error ({name}):*\n```\n{stderr_str}\n```"

        if not output.strip():
            output = f"✅ {name} Execution Complete (No Output)."

        await status_msg.edit(output)

        # Cleanup
        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        await smart_reply(message, f"❌ Error: {str(e)}")
        await report_error(client, e, context="multi-lang exec failed")


@astra_command(
    name="installdeps",
    description="🛠️ Install missing language dependencies. Supports Linux (apt) and macOS (brew).",
    category="Owner Utility",
    usage=".installdeps <lang|all|missing> (e.g. .installdeps py js)",
    owner_only=True,
)
async def install_deps_handler(client: Client, message: Message):
    """Install missing language dependencies with OS detection and batch support."""
    try:
        import platform
        args = extract_args(message)
        if not args:
            return await smart_reply(message, "⚠️ Usage: `.installdeps <lang|all|missing>`")

        system = platform.system().lower()
        if system == "linux":
            base_cmd = "apt-get update && apt-get install -y"
        elif system == "darwin":
            base_cmd = "brew install"
        else:
            return await smart_reply(message, f"❌ Auto-install not supported on `{system}`. Please install missing packages manually.")

        targets = []
        if args[0].lower() == "all":
            targets = [data for data in LANG_EXECUTORS.values() if data.get("package")]
        elif args[0].lower() == "missing":
            targets = [data for data in LANG_EXECUTORS.values() if data.get("package") and not is_installed(data["binary"])]
        else:
            # List of languages
            for arg in args:
                arg = arg.lower()
                for key, data in LANG_EXECUTORS.items():
                    if arg in data["aliases"]:
                        targets.append(data)
                        break

        if not targets:
            return await smart_reply(message, "✅ All requested environments are already set up.")

        # Deduplicate packages
        packages = list(dict.fromkeys([t["package"] for t in targets if t.get("package")]))
        
        if not packages:
            return await smart_reply(message, "❌ No package mapping found for selections.")

        pkg_str = ", ".join(packages)
        status_msg = await smart_reply(message, f"⏳ *Executing installation...*\nOS: `{system.capitalize()}`\nTargets: `{pkg_str}`")
        
        cmd = f"{base_cmd} {' '.join(packages)}"
        
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await process.communicate()
        success = process.returncode == 0
        
        if success:
            await status_msg.edit(f"✅ *Installation Successful!*\nPackages: `{pkg_str}`\n\nYou can now use these environments.")
        else:
            err = stderr.decode() if stderr else "Check logs for details."
            await status_msg.edit(f"❌ *Installation Failed:*\n```\n{err[:800]}\n```")

    except Exception as e:
        await smart_reply(message, f"❌ Error: {str(e)}")
        await report_error(client, e, context="installdeps failure")


# -----------------------------------------------------------
# EXAMPLES FOR HELP / README
# -----------------------------------------------------------

EXAMPLES = """
📝 *Core Language Execution Examples*

🔹 Python: `.run py print("Hello!")`
🔹 Shell: `.run sh echo "Hello!"`
🔹 Node.js: `.run js console.log("Hello!")`
🔹 TypeScript: `.run ts console.log("Hello!")`
🔹 C: `.run c #include<stdio.h>\nint main(){ printf("Hi"); }`
🔹 C++: `.run cpp #include<iostream>\nint main(){ std::cout<<"Hi"; }`
🔹 Java: `.run java class A{ public static void main(String[]a){ System.out.println("Hi"); }}`
🔹 Kotlin: `.run kt fun main() = println("Hello!")`
🔹 Rust: `.run rs fn main() { println!("Hello!"); }`
"""