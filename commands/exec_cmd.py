# -----------------------------------------------------------
# Astra-Userbot - Universal Multi-Language Executor
# -----------------------------------------------------------

import asyncio
import shutil
import os
import uuid
import platform
import re
from typing import Optional, Union, Dict
from . import *  # Astra helpers (astra_command, extract_args, smart_reply, report_error)

# -----------------------------------------------------------
# LANGUAGE DEFINITIONS (CORE / MOST USED)
# -----------------------------------------------------------

# Package mapping notes: linux (apt) vs darwin (brew)
# Verified package names for Ubuntu 22.04/24.04 and macOS
LANG_EXECUTORS = {
    # ------------------------ Python ------------------------
    "py": {
        "name": "Python",
        "icon": "🐍",
        "aliases": ["python", "python3", "py", "p", "py3"],
        "binary": "python3",
        "package": {"apt": "python3", "brew": "python3"},
        "ext": ".py",
        "run_cmd": lambda bin, f: f"{bin} {f}",
    },

    # ------------------------ JavaScript ---------------------
    "js": {
        "name": "JavaScript",
        "icon": "🟨",
        "aliases": ["javascript", "node", "js", "j", "nodejs"],
        "binary": "node",
        "package": {"apt": "nodejs", "brew": "node"},
        "ext": ".js",
        "run_cmd": lambda bin, f: f"{bin} {f}",
    },

    # ------------------------ TypeScript ---------------------
    "ts": {
        "name": "TypeScript",
        "icon": "🟦",
        "aliases": ["typescript", "ts"],
        "binary": "tsc",
        "package": {"apt": "node-typescript", "brew": "typescript"},
        "ext": ".ts",
        "run_cmd": lambda bin, f: f"tsc {f} --outFile /tmp/a.js && node /tmp/a.js",
    },

    # ------------------------ Java ---------------------------
    "java": {
        "name": "Java",
        "icon": "☕",
        "aliases": ["java", "javac"],
        "binary": "javac",
        "package": {"apt": "default-jdk", "brew": "openjdk"},
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
        "package": {"apt": "gcc", "brew": "gcc"},
        "ext": ".c",
        "run_cmd": lambda bin, f: f"gcc -std=c11 -O2 {f} -o /tmp/a.out -lpthread -lm && /tmp/a.out",
    },

    # ------------------------ C++ ----------------------------
    "cpp": {
        "name": "C++",
        "icon": "💠",
        "aliases": ["cpp", "g++", "c++"],
        "binary": "g++",
        "package": {"apt": "g++", "brew": "gcc"},
        "ext": ".cpp",
        "run_cmd": lambda bin, f: f"g++ -std=c++17 -O2 {f} -o /tmp/a.out -lpthread -lm && /tmp/a.out",
    },

    # ------------------------ Rust ---------------------------
    "rust": {
        "name": "Rust",
        "icon": "🦀",
        "aliases": ["rust", "rs", "rustc"],
        "binary": "rustc",
        "package": {"apt": "rustc", "brew": "rust"},
        "ext": ".rs",
        "run_cmd": lambda bin, f: f"rustc -C opt-level=2 {f} -o /tmp/a.out && /tmp/a.out",
    },

    # ------------------------ Golang -------------------------
    "go": {
        "name": "Golang",
        "icon": "🐹",
        "aliases": ["go", "golang"],
        "binary": "go",
        "package": {"apt": "golang-go", "brew": "go"},
        "ext": ".go",
        "run_cmd": lambda bin, f: f"go run {f}",
    },

    # ------------------------ PHP ----------------------------
    "php": {
        "name": "PHP",
        "icon": "🐘",
        "aliases": ["php"],
        "binary": "php",
        "package": {"apt": "php-cli", "brew": "php"},
        "ext": ".php",
        "run_cmd": lambda bin, f: f"{bin} {f}",
    },

    # ------------------------ Ruby ---------------------------
    "ruby": {
        "name": "Ruby",
        "icon": "💎",
        "aliases": ["ruby", "rb"],
        "binary": "ruby",
        "package": {"apt": "ruby-full", "brew": "ruby"},
        "ext": ".rb",
        "run_cmd": lambda bin, f: f"{bin} {f}",
    },

    # ------------------------ Kotlin -------------------------
    "kt": {
        "name": "Kotlin",
        "icon": "💜",
        "aliases": ["kotlin", "kt"],
        "binary": "kotlinc",
        "package": {"apt": "kotlin", "brew": "kotlin"},
        "ext": ".kt",
        "run_cmd": lambda bin, f: f"kotlinc {f} -include-runtime -d /tmp/a.jar && java -jar /tmp/a.jar",
    },

    # ------------------------ Swift --------------------------
    "swift": {
        "name": "Swift",
        "icon": "🍎",
        "aliases": ["swift"],
        "binary": "swift",
        "package": {"apt": "swiftlang", "brew": "swift"},
        "ext": ".swift",
        "run_cmd": lambda bin, f: f"swift -O {f}",
    },

    # ------------------------ C# / Mono ----------------------
    "cs": {
        "name": "C Sharp",
        "icon": "🗄️",
        "aliases": ["csharp", "cs"],
        "binary": "mcs",
        "package": {"apt": "mono-complete", "brew": "mono"},
        "ext": ".cs",
        "run_cmd": lambda bin, f: f"mcs {f} -out:/tmp/a.exe && mono /tmp/a.exe",
    },

    # ------------------------ Shell (Linux/macOS) ------------
    "sh": {
        "name": "Shell",
        "icon": "🐚",
        "aliases": ["sh", "shell", "bash", "zsh"],
        "binary": "bash",
        "package": {"apt": "bash", "brew": "bash"},
        "ext": ".sh",
        "run_cmd": lambda bin, f: f"{bin} {f}",
    },
}


def is_installed(binary: str) -> bool:
    """Check if required binary is installed."""
    return shutil.which(binary) is not None

def get_package_name(data: dict) -> Optional[str]:
    """Resolve package name based on OS."""
    pkg = data.get("package")
    if not pkg: 
        return None
    if isinstance(pkg, str):
        return pkg
    
    sys_name = platform.system().lower()
    if sys_name == "linux":
        return pkg.get("apt")
    elif sys_name == "darwin":
        return pkg.get("brew")
    return list(pkg.values())[0] if pkg else None

def normalize_code(code: str) -> str:
    """Replaces smart quotes and other common autocompleted characters."""
    replacements = {
        '“': '"', '”': '"',  # Smart double quotes
        '〝': '"', '〞': '"',  # Other variations
        '‘': "'", '’': "'",  # Smart single quotes
        '‛': "'",
        '—': '--',            # Em dash
        '–': '-',             # En dash
    }
    for old, new in replacements.items():
        code = code.replace(old, new)
    return code


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
    description="🚀 Pro Universal Multi-Language Executor. Supports stdin inputs and custom timeouts.",
    category="Owner Utility",
    aliases=["exec-lang", "code"],
    usage=(
        ".run <lang> <code> [-t <seconds>] [--input <data>]\n\n"
        "📝 *Advanced Features:*\n"
        "🔹 **Input:** Add `--input data` at the end.\n"
        "🔹 **Timeout:** Add `-t 10` for custom duration (max 300s).\n\n"
        "*Pro Examples:*\n"
        "� **Python:** `.run py print(input()) --input Hello`\n"
        "� **C:** `.run c int x; scanf(\"%d\",&x); printf(\"%d\",x); --input 5`\n"
        "🦀 **Rust:** `.run rs fn main(){let mut s=String::new();std::io::stdin().read_line(&mut s).unwrap();print!(\"{}\",s);} --input Hi`"
    ),
    owner_only=True,
)
async def multi_lang_exec_handler(client: Client, message: Message):
    """Execute code in the selected programming language."""
    try:
        if not message.body or " " not in message.body:
            return await smart_reply(
                message,
                "⚠️ Usage:\n`.run <language> <code> [-t <seconds>] [--input <data>]`",
            )

        # Extract language and payload
        parts = message.body.split(None, 2)
        if len(parts) < 3:
            return await smart_reply(
                message,
                "⚠️ Usage:\n`.run <language> <code> [-t <seconds>] [--input <data>]`",
            )

        lang = parts[1].lower()
        full_payload = parts[2]

        # ----------------- ADVANCED PARSING -----------------
        # Order: <code> [-t <seconds>] [--input <data>]
        
        # 1. Parse Input
        stdin_data = ""
        if " --input " in full_payload:
            code_and_t, stdin_data = full_payload.rsplit(" --input ", 1)
        else:
            code_and_t = full_payload

        # 2. Parse Timeout
        timeout_val = 60.0 # Default
        if " -t " in code_and_t:
            # We use rsplit to handle case where -t is followed by code or flags
            # But usually it's at the end of the code section
            match = re.search(r"\s-t\s(\d+)(\s|$)", code_and_t)
            if match:
                timeout_val = min(float(match.group(1)), 300.0) # Cap at 300s
                # Remove -t arg from code
                code = code_and_t[:match.start()] + code_and_t[match.end():]
            else:
                code = code_and_t
        else:
            code = code_and_t
        # ---------------------------------------------------

        # 🧹 Pre-processing
        code = normalize_code(code)

        # Automatic Markdown Code Block Stripping
        if code.strip().startswith("```"):
            code = re.sub(r"^```[a-zA-Z0-9+_]*\n?", "", code.strip())
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
        status_msg = await smart_reply(message, f"{icon} *Executing {name}...* (Timeout: {timeout_val}s)")

        # ----------------- SECURITY CHECK (v6.0) -----------------
        from utils.state import state
        is_full_dev = state.state.get("FULL_DEV", False)
        is_i_dev = state.state.get("I_DEV", False)
        
        if not is_full_dev:
            violation = security_filter(code)
            if violation and not is_i_dev:
                warning_text = (
                    f"🚨 **SECURITY RESTRICTION** 🚨\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🛑 **Blocked:** Potential privacy leak (`{violation}`).\n"
                    f"━━━━━━━━━━━━━━━━━━━━"
                )
                return await smart_reply(message, warning_text)
        # ---------------------------------------------------------

        binary = selected["binary"]
        pkg = get_package_name(selected) or binary

        # Check install status
        if not is_installed(binary):
            await status_msg.edit(f"❌ `{name}` not found. Suggestion: `.installdeps {lang}`")
            return

        # ----------------- FILENAME & CLASS HANDLING -----------------
        if lang in ["java", "kotlin"]:
            match = re.search(r"(?:public\s+)?class\s+(\w+)", code)
            base_name = match.group(1) if match else f"Astra_{uuid.uuid4().hex[:8]}"
        else:
            base_name = f"astra_{uuid.uuid4().hex}"

        # Clean code whitespace for specific languages
        code_to_write = code.strip()

        filename = f"/tmp/{base_name}{selected['ext']}"
        with open(filename, "w") as f:
            f.write(code_to_write)
        # -------------------------------------------------------------

        # Execute
        run_cmd = selected["run_cmd"](binary, filename)

        process = await asyncio.create_subprocess_shell(
            run_cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            # ⏳ Pipe stdin and wait for output with custom timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=stdin_data.encode() if stdin_data else None), 
                timeout=timeout_val
            )
            stdout_str = stdout.decode().strip() if stdout else ""
            stderr_str = stderr.decode().strip() if stderr else ""
        except asyncio.TimeoutError:
            try: process.kill()
            except: pass
            return await status_msg.edit(f"⏱️ *Execution Timeout ({int(timeout_val)}s):* `{name}` terminated.")

        # ----------------- OUTPUT SECURITY CHECK (v6.1) -----------------
        if not is_full_dev:
            out_violation = security_filter(stdout_str) or security_filter(stderr_str)
            if out_violation and not is_i_dev:
                output_warning = (
                    f"🚨 **OUTPUT RESTRICTED** 🚨\n"
                    f"🛡️ **System Guard:** Sensitive data detected in output.\n"
                )
                return await smart_reply(message, output_warning)
        # -----------------------------------------------------------------

        def truncate(text, limit=1800):
            if len(text) > limit:
                return text[:limit] + f"\n... (truncated {len(text)-limit} chars)"
            return text

        output = ""
        if stdin_data:
            output += f"📥 *Input:*\n```\n{truncate(stdin_data, 200)}\n```\n"
        
        if stdout_str:
            output += f"✅ *Output ({name}):*\n```\n{truncate(stdout_str)}\n```\n"
        if stderr_str:
            output += f"❌ *Error ({name}):*\n```\n{truncate(stderr_str)}\n```"

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
    description="🛠️ Install missing language dependencies.",
    category="Owner Utility",
    usage=".installdeps <lang|all|missing>",
    owner_only=True,
)
async def install_deps_handler(client: Client, message: Message):
    """Install missing language dependencies with OS detection and batch support."""
    try:
        args = extract_args(message)
        if not args:
            return await smart_reply(message, "⚠️ Usage: `.installdeps <lang|all|missing>`")

        system = platform.system().lower()
        if system == "linux":
            update_cmd = "apt-get update -y"
            base_cmd = "apt-get install -y"
        elif system == "darwin":
            update_cmd = "brew update"
            base_cmd = "brew install"
        else:
            return await smart_reply(message, f"❌ OS not supported.")

        targets = []
        if args[0].lower() == "all":
            targets = [data for data in LANG_EXECUTORS.values() if data.get("package")]
        elif args[0].lower() == "missing":
            targets = [data for data in LANG_EXECUTORS.values() if data.get("package") and not is_installed(data["binary"])]
        else:
            for arg in args:
                arg = arg.lower()
                for key, data in LANG_EXECUTORS.items():
                    if arg in data["aliases"]:
                        targets.append(data)
                        break

        if not targets:
            return await smart_reply(message, "✅ Systems ready.")

        packages = list(dict.fromkeys([get_package_name(t) for t in targets if get_package_name(t)]))
        if not packages: return await smart_reply(message, "❌ Package mapping missing.")

        status_msg = await smart_reply(message, f"⏳ *Installing {len(packages)} packages...*")
        
        cmd = f"{update_cmd} && {base_cmd} {' '.join(packages)}"
        process = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await process.communicate()
        
        if process.returncode == 0:
            await status_msg.edit(f"✅ *Success:* Dependencies ready.")
        else:
            await status_msg.edit(f"❌ *Failed:* Installation error (Check logs).")

    except Exception as e:
        await smart_reply(message, f"❌ Error: {str(e)}")
        await report_error(client, e, context="installdeps failure")


# -----------------------------------------------------------
# EXAMPLES FOR HELP / README
# -----------------------------------------------------------

EXAMPLES = """
� *Pro Executor Examples (All Languages)*

� **Python (Stdin):**
`.run py print(f"Hello {input()}") --input Astra`

� **JavaScript (Basic):**
`.run js console.log("Standard JS Execution")`

☕ **Java (Class Handling):**
`.run java class Hi { public static void main(String[] a) { System.out.println("Pro Java"); } }`

� **C (Math & Input):**
`.run c #include <stdio.h>\n#include <math.h>\nint main() { double x; scanf("%lf", &x); printf("%.2f", sqrt(x)); } --input 16`

� **C++ (Modern & Threading):**
`.run cpp #include <iostream>\n#include <thread>\nint main() { std::this_thread::sleep_for(std::chrono::seconds(1)); std::cout << "Threaded!"; } -t 5`

🦀 **Rust (Optimized):**
`.run rs fn main() { println!("Fast Rust Snippet"); }`

� **Golang:**
`.run go package main\nimport "fmt"\nfunc main() { fmt.Println("Go!") }`

� **Shell (Automation):**
`.run sh for i in {1..3}; do echo "Loop $i"; done`

⏱️ **Custom Timeout:**
`.run py import time; time.sleep(10); print("Long Task") -t 15`
"""