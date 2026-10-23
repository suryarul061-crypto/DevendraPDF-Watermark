import io
import json
import os
import sys
import hashlib
import shutil
import subprocess
import traceback
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

APP_NAME = "Devendra PDF Watermark"
APP_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Programs" / "DevendraPDF"
DATA_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "DevendraPDF"
LOG_DIR = DATA_DIR / "Logs"
LOG_FILE = LOG_DIR / "launcher.log"
CONFIG_FILE = APP_DIR / "config.json"
LOGO_FILE = APP_DIR / "Logo.png"
OUTPUT_DIR = DATA_DIR / "Watermarked"


def log(message):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"{message}\n")


def load_config():
    defaults = {"viewer": "auto", "logo_width_points": 64, "margin_points": 18}
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        defaults.update(data)
    except Exception:
        pass
    return defaults


def output_path_for(source: Path) -> Path:
    try:
        identity = str(source.resolve()).lower()
    except Exception:
        identity = str(source).lower()
    digest = hashlib.sha256(identity.encode("utf-8", errors="replace")).hexdigest()[:10]
    safe_stem = "".join(c if c.isalnum() or c in "-_." else "_" for c in source.stem)[:90]
    return OUTPUT_DIR / f"{safe_stem}_{digest}_watermarked.pdf"


def make_overlay(width, height, logo_width, margin):
    if not LOGO_FILE.exists():
        raise FileNotFoundError(f"Company logo not found: {LOGO_FILE}")
    image = ImageReader(str(LOGO_FILE))
    image_width, image_height = image.getSize()
    if image_width <= 0 or image_height <= 0:
        raise ValueError("Logo image has invalid dimensions")
    draw_width = min(float(logo_width), max(18.0, width * 0.25))
    draw_height = draw_width * image_height / image_width
    max_height = max(18.0, height * 0.12)
    if draw_height > max_height:
        draw_height = max_height
        draw_width = draw_height * image_width / image_height
    x = max(0.0, width - draw_width - float(margin))
    y = max(0.0, float(margin))
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(width, height), pageCompression=1)
    c.drawImage(image, x, y, width=draw_width, height=draw_height, preserveAspectRatio=True, mask="auto", anchor="c")
    c.save()
    buffer.seek(0)
    return PdfReader(buffer).pages[0]


def watermark_pdf(source: Path, destination: Path, config):
    # Never write to the source path. Only the separate Watermarked folder is written.
    reader = PdfReader(str(source), strict=False)
    if reader.is_encrypted:
        raise ValueError("Password-protected PDF skipped; unlock it in a trusted PDF viewer first.")
    try:
        fields = reader.get_fields() or {}
        if any(str(field.get("/FT", "")) == "/Sig" for field in fields.values() if hasattr(field, "get")):
            raise ValueError("PDF contains a digital-signature field and was skipped to avoid invalidating the signature.")
    except ValueError:
        raise
    except Exception:
        # If signature metadata cannot be inspected reliably, do not assume it is safe to rewrite.
        raise ValueError("Could not safely inspect PDF signature fields; file skipped and original preserved.")
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    for page in writer.pages:
        rotation = int(page.get("/Rotate", 0) or 0)
        if rotation:
            page.transfer_rotation_to_content()
        box = page.mediabox
        width = float(box.width)
        height = float(box.height)
        overlay = make_overlay(width, height, config.get("logo_width_points", 64), config.get("margin_points", 18))
        page.merge_page(overlay, over=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_destination = destination.with_suffix(".tmp.pdf")
    with temp_destination.open("wb") as f:
        writer.write(f)
    temp_destination.replace(destination)


def viewer_candidates(viewer_setting):
    windir = Path(os.environ.get("WINDIR", r"C:\Windows"))
    local = Path(os.environ.get("LOCALAPPDATA", str(Path.home())))
    program_files = [Path(os.environ.get("ProgramFiles", r"C:\Program Files")), Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))]
    edge_paths = [
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        local / "Microsoft" / "Edge" / "Application" / "msedge.exe",
    ]
    chrome_paths = [
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        local / "Google" / "Chrome" / "Application" / "chrome.exe",
    ]
    acrobat_paths = []
    for root in program_files:
        acrobat_paths.extend([
            root / "Adobe" / "Acrobat DC" / "Acrobat" / "Acrobat.exe",
            root / "Adobe" / "Acrobat" / "Acrobat.exe",
            root / "Adobe" / "Acrobat Reader DC" / "Reader" / "AcroRd32.exe",
            root / "Adobe" / "Acrobat Reader" / "Reader" / "AcroRd32.exe",
        ])
    if viewer_setting == "edge":
        paths = edge_paths + chrome_paths + acrobat_paths
    elif viewer_setting == "chrome":
        paths = chrome_paths + edge_paths + acrobat_paths
    elif viewer_setting == "acrobat":
        paths = acrobat_paths + edge_paths + chrome_paths
    else:
        # Mixed environment: prefer Edge, then Chrome, then Adobe Reader.
        paths = edge_paths + chrome_paths + acrobat_paths
    seen = set()
    for path in paths:
        key = str(path).lower()
        if key not in seen and path.exists():
            seen.add(key)
            yield path
    names = {
        "edge": ["msedge.exe", "chrome.exe", "Acrobat.exe", "AcroRd32.exe"],
        "chrome": ["chrome.exe", "msedge.exe", "Acrobat.exe", "AcroRd32.exe"],
        "acrobat": ["Acrobat.exe", "AcroRd32.exe", "msedge.exe", "chrome.exe"],
    }.get(viewer_setting, ["msedge.exe", "chrome.exe", "Acrobat.exe", "AcroRd32.exe"])
    for name in names:
        found = shutil.which(name)
        if found:
            yield Path(found)

def open_in_viewer(pdf_path, config):
    for exe in viewer_candidates(str(config.get("viewer", "auto")).lower()):
        try:
            subprocess.Popen([str(exe), str(pdf_path)], close_fds=True)
            return
        except Exception as e:
            log(f"Viewer launch failed for {exe}: {e}")
    # Fallback: Windows default association. If this launcher is still the default,
    # avoid recursion by telling the user to install/configure a supported viewer.
    os.startfile(str(pdf_path))


def show_error(message):
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, APP_NAME, 0x10)
    except Exception:
        pass


def main():
    if len(sys.argv) < 2:
        show_error("Open a PDF by double-clicking it after setting Devendra PDF Watermark as the default PDF app.")
        return 2
    source = Path(sys.argv[1].strip('"')).expanduser()
    if not source.exists() or source.suffix.lower() != ".pdf":
        show_error("The selected file does not exist or is not a PDF.")
        return 2
    config = load_config()
    try:
        if not LOGO_FILE.exists():
            raise FileNotFoundError(f"Company logo is missing. Copy Logo.png to:\n{LOGO_FILE}")
        destination = output_path_for(source)
        watermark_pdf(source, destination, config)
        log(f"SUCCESS | source={source} | output={destination}")
        open_in_viewer(destination, config)
        return 0
    except Exception as e:
        log(f"ERROR | source={source} | {e}\n{traceback.format_exc()}")
        show_error(f"Could not watermark this PDF. The original was not changed.\n\nReason: {e}\n\nLog: {LOG_FILE}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
