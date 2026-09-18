"""Read text off a photographed label.

Pluggable so the engine can change without anything downstream noticing:

    AAHAR_OCR=tesseract   # local, free, no account — the current stand-in
    AAHAR_OCR=textract    # AWS Textract, the intended engine
    AAHAR_OCR=vision      # macOS Vision, better locally but macOS-only

Both real engines return the same three things per item — text, a confidence
score and a bounding box — so they normalise onto ``OcrBlock`` and the swap is
a config change rather than a rewrite.

⚠️  TESSERACT IS A STAND-IN. It is noticeably weaker on the shiny, curved
packaging that food labels actually come on. Move to Textract once an AWS
account is available: set AAHAR_OCR=textract, nothing else changes.
"""

from __future__ import annotations

import hashlib
import io
import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

DEFAULT_ENGINE = "tesseract"
# Tried in order when the one before it errors. Textract can be held by account
# verification or simply unreachable; tesseract needs no network at all, so the
# pair covers each other. The result always reports which one actually ran.
DEFAULT_FALLBACKS = {
    "textract": ["tesseract"],
    "tesseract": [],
    "vision": ["tesseract"],
}


class OcrUnavailable(RuntimeError):
    """The chosen OCR engine isn't installed or configured — a server problem."""


class UnreadableImage(ValueError):
    """The upload isn't a usable image — the caller's problem, not the server's."""


@dataclass
class OcrBlock:
    """One recognised line. Mirrors a Textract LINE block."""

    text: str
    confidence: float  # 0-100, as Textract reports it


@dataclass
class OcrResult:
    blocks: list[OcrBlock]
    engine: str

    @property
    def text(self) -> str:
        return "\n".join(b.text for b in self.blocks)

    @property
    def mean_confidence(self) -> float:
        scored = [b.confidence for b in self.blocks if b.confidence >= 0]
        return sum(scored) / len(scored) if scored else 0.0

    def quality(self) -> str:
        """Map OCR confidence onto the app's HIGH/MEDIUM/LOW signal.

        A photograph is never HIGH: even a clean read is one person's snapshot
        of one packet, not a verified product record.
        """
        if not self.blocks:
            return "LOW"
        mean = self.mean_confidence
        return "MEDIUM" if mean >= 75 else "LOW"


def engine_name() -> str:
    return (os.environ.get("AAHAR_OCR") or DEFAULT_ENGINE).strip().lower()


def engine_chain() -> list[str]:
    """The engine to try, then its fallbacks. AAHAR_OCR_FALLBACK overrides."""
    primary = engine_name()
    override = os.environ.get("AAHAR_OCR_FALLBACK")
    if override is not None:
        rest = [e.strip().lower() for e in override.split(",") if e.strip()]
    else:
        rest = DEFAULT_FALLBACKS.get(primary, [])
    return [primary] + [e for e in rest if e != primary]


# ------------------------------------------------------------- tesseract


def _tesseract(image_bytes: bytes) -> OcrResult:
    try:
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        raise OcrUnavailable(
            "pip install pytesseract Pillow, and `brew install tesseract`"
        ) from exc

    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.load()
    except Exception as exc:
        raise UnreadableImage("That file doesn't look like an image") from exc

    # Greyscale helps on the low-contrast printing typical of ingredient panels.
    if image.mode not in ("L", "RGB"):
        image = image.convert("RGB")

    data = pytesseract.image_to_data(
        image, output_type=pytesseract.Output.DICT, config="--psm 6"
    )

    # Group words into lines, the granularity Textract returns.
    lines: dict[tuple, list[tuple[str, float]]] = {}
    for i, word in enumerate(data["text"]):
        word = (word or "").strip()
        if not word:
            continue
        try:
            conf = float(data["conf"][i])
        except (TypeError, ValueError):
            conf = -1.0
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        lines.setdefault(key, []).append((word, conf))

    blocks = []
    for key in sorted(lines):
        words = lines[key]
        scored = [c for _, c in words if c >= 0]
        blocks.append(
            OcrBlock(
                text=" ".join(w for w, _ in words),
                confidence=sum(scored) / len(scored) if scored else -1.0,
            )
        )
    return OcrResult(blocks=blocks, engine="tesseract")


# -------------------------------------------------------------- textract


def _textract(image_bytes: bytes) -> OcrResult:
    """AWS Textract — the intended engine.

    DetectDocumentText is the cheap call and all this needs: an ingredients
    panel is plain text, not forms or tables.
    """
    try:
        import boto3
    except ImportError as exc:
        raise OcrUnavailable("pip install boto3") from exc

    client = boto3.client("textract", region_name=os.environ.get("AWS_REGION"))
    response = client.detect_document_text(Document={"Bytes": image_bytes})
    blocks = [
        OcrBlock(text=b.get("Text", ""), confidence=float(b.get("Confidence", 0.0)))
        for b in response.get("Blocks", [])
        if b.get("BlockType") == "LINE" and b.get("Text")
    ]
    return OcrResult(blocks=blocks, engine="textract")


# ---------------------------------------------------------------- vision


def _vision(image_bytes: bytes) -> OcrResult:
    """macOS Vision. Better than Tesseract on real photos, but macOS-only."""
    try:
        from ocrmac import ocrmac
    except ImportError as exc:
        raise OcrUnavailable("pip install ocrmac (macOS only)") from exc

    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
        handle.write(image_bytes)
        path = handle.name
    try:
        found = ocrmac.OCR(path).recognize()
    finally:
        os.unlink(path)

    return OcrResult(
        blocks=[OcrBlock(text=text, confidence=float(conf) * 100) for text, conf, _ in found],
        engine="vision",
    )


ENGINES = {"tesseract": _tesseract, "textract": _textract, "vision": _vision}


def read_label(image_bytes: bytes) -> OcrResult:
    engine = engine_name()
    if engine not in ENGINES:
        raise OcrUnavailable(
            f"Unknown AAHAR_OCR '{engine}'. Use tesseract, textract or vision."
        )
    if not image_bytes:
        raise UnreadableImage("No image was uploaded")

    # Same photo, same engine, same answer — and Textract bills per page.
    from . import cache

    key = cache.key_for(engine, hashlib.sha256(image_bytes).hexdigest())
    hit = cache.get("ocr", key)
    if hit is not None:
        return OcrResult(
            blocks=[OcrBlock(text=b["text"], confidence=b["confidence"]) for b in hit["blocks"]],
            engine=hit["engine"],
        )

    last_error: Exception | None = None
    result = None
    for candidate in engine_chain():
        if candidate not in ENGINES:
            logger.warning("Unknown OCR engine %r in the chain — skipping", candidate)
            continue
        try:
            result = ENGINES[candidate](image_bytes)
            if candidate != engine:
                logger.warning("%s unavailable — read the label with %s instead",
                               engine, candidate)
            break
        except UnreadableImage:
            raise            # the upload is bad; another engine won't help
        except Exception as exc:
            logger.warning("OCR engine %s failed: %s", candidate, exc)
            last_error = exc

    if result is None:
        raise OcrUnavailable(f"No OCR engine could read the label ({last_error})")

    cache.put(
        "ocr",
        key,
        {
            "engine": result.engine,
            "blocks": [{"text": b.text, "confidence": b.confidence} for b in result.blocks],
        },
    )
    return result
