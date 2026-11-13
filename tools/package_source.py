"""Create a source-only ZIP from an explicit list; never collect local runtime data."""
from pathlib import Path
import hashlib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "whale-companion"
# Keep this list explicit: a new local file must not silently become public.
SOURCE_FILES = (
    ".env.example",
    ".gitattributes",
    ".gitignore",
    "README.md",
    "THIRD_PARTY_NOTICES.md",
    "Start-Whale.cmd",
    "backend/__init__.py",
    "backend/companion.py",
    "backend/server.py",
    "content/feiyu/character.json",
    "content/feiyu/world.json",
    "content/mira/character.json",
    "content/mira/world.json",
    "desktop/chat-preload.cjs",
    "desktop/main.cjs",
    "desktop/package.json",
    "desktop/package-lock.json",
    "desktop/pet.css",
    "desktop/pet.html",
    "desktop/preload.cjs",
    "desktop/renderer.ts",
    "desktop/tsconfig.json",
    "desktop/vendor/rig.ts",
    "desktop/vendor/surfpet-LICENSE.txt",
    "docs/DEVELOPMENT.md",
    "docs/LICENSING.md",
    "docs/MIRA_README.md",
    "docs/REFERENCES.md",
    "evaluation/RUBRIC.md",
    "evaluation/scenarios/feiyu.json",
    "evaluation/scenarios/mira.json",
    "scripts/Resolve-Python.ps1",
    "scripts/Start-Mira.cmd",
    "scripts/Start-Mira.ps1",
    "scripts/Start-Whale.ps1",
    "tests/test_companion.py",
    "tests/test_feiyu.py",
    "tools/__init__.py",
    "tools/evaluate.py",
    "tools/package_source.py",
    "tools/setup_local.py",
    "tools/setup_pet_assets.py",
    "web/feiyu/app.js",
    "web/feiyu/index.html",
    "web/feiyu/style.css",
    "web/mira/app.js",
    "web/mira/index.html",
    "web/mira/mira.svg",
    "web/mira/style.css",
)


def package_source():
    entries = {}
    for name in sorted(SOURCE_FILES):
        path = ROOT / name
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(ROOT):
            raise ValueError(f"Missing or unsafe source file: {name}")
        entries[name] = path.read_bytes()
    # A populated template is an easy way to accidentally publish credentials.
    template = entries[".env.example"].decode("utf-8")
    for line in template.splitlines():
        key, sep, value = line.partition("=")
        if sep and key.strip() == "DEEPSEEK_API_KEY" and value.strip():
            raise ValueError("DEEPSEEK_API_KEY must be empty in .env.example")
    manifest = "".join(f"{hashlib.sha256(data).hexdigest()}  {name}\n" for name, data in entries.items())
    entries["SOURCE_MANIFEST.sha256"] = manifest.encode("utf-8")
    destination = ROOT / "dist"
    destination.mkdir(exist_ok=True)
    archive = destination / "whale-companion-source.zip"
    temporary = archive.with_suffix(".zip.tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as package:
        for name, data in entries.items():
            # Fixed metadata makes unchanged source produce the same archive hash.
            info = zipfile.ZipInfo(f"{PREFIX}/{name}", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            package.writestr(info, data)
    with zipfile.ZipFile(temporary) as package:
        if package.testzip() is not None:
            raise RuntimeError("ZIP integrity check failed")
    temporary.replace(archive)
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    (destination / "SHA256SUMS.txt").write_text(f"{checksum}  {archive.name}\n", encoding="utf-8")
    print(f"Packaged {len(SOURCE_FILES)} source files + SHA-256 manifest ({archive.stat().st_size:,} bytes).")
    print(archive)
    print("No runtime data, downloaded artwork, dependencies or credentials are collected.")
    return archive


if __name__ == "__main__":
    package_source()
