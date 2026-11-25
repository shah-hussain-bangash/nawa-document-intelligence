"""Bounded local PDF OCR. Word boxes are evidence, not validated table values."""
import csv
from io import StringIO
from pathlib import Path
import re
import shutil
import subprocess
from tempfile import TemporaryDirectory


def data_options():
    bundled = Path(__file__).resolve().parents[4] / "data" / "ocr"
    return ["--tessdata-dir", str(bundled)] if (bundled / "eng.traineddata").is_file() else []


def capabilities(languages="eng+ara"):
    available = {"renderer": bool(shutil.which("pdftoppm")), "engine": bool(shutil.which("tesseract")), "languages": [], "ready": False}
    if available["engine"]:
        try:
            result = subprocess.run(["tesseract", *data_options(), "--list-langs"], capture_output=True, text=True, timeout=5, check=True)
            available["languages"] = [x.strip() for x in result.stdout.splitlines()[1:] if re.fullmatch(r"[A-Za-z0-9_]+", x.strip())]
        except (OSError, subprocess.SubprocessError):
            pass
    available["ready"] = available["renderer"] and available["engine"] and set(languages.split("+")).issubset(available["languages"])
    return available


def parse_tsv(value):
    words, lines = [], {}
    for row in csv.DictReader(StringIO(value), delimiter="\t", quoting=csv.QUOTE_NONE):
        if row.get("level") != "5" or not row.get("text", "").strip():
            continue
        if len(words) >= 4000:
            raise ValueError("OCR word limit exceeded")
        confidence = float(row["conf"])
        if confidence < 0 or confidence > 100:
            continue
        box = [int(row[k]) for k in ("left", "top", "width", "height")]
        if any(x < 0 or x > 10000 for x in box):
            raise ValueError("Invalid OCR geometry")
        text = row["text"][:500]
        words.append({"text": text, "box": box, "confidence": round(confidence, 1)})
        key = tuple(row[k] for k in ("block_num", "par_num", "line_num"))
        lines.setdefault(key, []).append(text)
    return {"text": "\n".join(" ".join(parts) for parts in lines.values())[:30000], "words": words,
            "ocr_confidence": round(sum(w["confidence"] for w in words) / len(words), 1) if words else 0,
            "method": "ocr", "warnings": ["OCR output requires source review; word confidence is not field accuracy."]}


def recognise_page(path: Path, page: int, languages: str):
    with TemporaryDirectory(prefix="nawa-ocr-") as directory:
        base = str(Path(directory) / "page")
        subprocess.run(["pdftoppm", "-f", str(page), "-l", str(page), "-r", "150", "-scale-to", "2400", "-singlefile", "-png", str(path), base], capture_output=True, timeout=15, check=True)
        result = subprocess.run(["tesseract", base + ".png", "stdout", *data_options(), "-l", languages, "--psm", "3", "-c", "tessedit_create_tsv=1"], capture_output=True, text=True, encoding="utf-8", timeout=20, check=True)
        if len(result.stdout) > 2_000_000:
            raise ValueError("OCR response limit exceeded")
        return parse_tsv(result.stdout)
