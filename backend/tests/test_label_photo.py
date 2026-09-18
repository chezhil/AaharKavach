"""Label-photo scanning: OCR, parsing, and the safety boundary."""

import io

import pytest

from shared import api
from shared.label_parse import parse_label
from shared.ocr import OcrBlock, OcrResult, engine_name

ADMIN = api.Caller({"X-Aahar-Role": "Admin", "X-Aahar-User": "user_123"})

PANEL = """BRITANNIA GOOD DAY
BUTTER COOKIES
INGREDIENTS: Refined Wheat Flour (Maida), Sugar, Edible Vegetable Oil,
Butter (12%), Milk Solids, Invert Sugar Syrup, Emulsifier Soy Lecithin (322),
Iodised Salt.
CONTAINS WHEAT, MILK AND SOY.
NUTRITIONAL INFORMATION per 100g
Energy 500 kcal
"""


def test_parses_the_ingredient_list():
    parsed = parse_label(PANEL)
    assert parsed.found_ingredients
    names = " | ".join(parsed.ingredients).lower()
    assert "maida" in names
    assert "milk solids" in names
    assert "soy lecithin" in names


def test_stops_before_the_nutrition_panel():
    """Energy and per-100g rows are not ingredients."""
    parsed = parse_label(PANEL)
    joined = " ".join(parsed.ingredients).lower()
    assert "energy" not in joined
    assert "kcal" not in joined
    assert "nutritional" not in joined


def test_captures_the_contains_warning_separately():
    parsed = parse_label(PANEL)
    assert "WHEAT" in parsed.contains_note


def test_reads_the_product_name_from_above_the_list():
    assert "Good Day" in parse_label(PANEL).product_name


def test_percentages_are_stripped_from_ingredient_names():
    assert "Butter" in parse_label(PANEL).ingredients


def test_empty_or_garbage_text_finds_nothing():
    for text in ("", "   ", ".....", "|||"):
        assert not parse_label(text).found_ingredients


def test_a_list_without_a_heading_still_parses():
    """Some panels omit the word INGREDIENTS entirely."""
    parsed = parse_label("Wheat Flour, Sugar, Milk Solids, Salt")
    assert len(parsed.ingredients) >= 3


def test_photo_confidence_never_reads_as_high():
    """A photo of one packet is not a verified product record."""
    clean = OcrResult([OcrBlock("Sugar", 99.0), OcrBlock("Salt", 99.0)], "tesseract")
    assert clean.quality() == "MEDIUM"
    blurry = OcrResult([OcrBlock("Sug4r", 40.0)], "tesseract")
    assert blurry.quality() == "LOW"
    assert OcrResult([], "tesseract").quality() == "LOW"


def test_upload_without_an_image_is_refused():
    with pytest.raises(api.ApiError) as exc:
        api.scan_label_endpoint("label.jpg", b"")
    assert exc.value.status == 400


def test_unreadable_photo_says_so_rather_than_inventing_ingredients():
    """The old placeholder returned three fixed ingredients for any upload."""
    with pytest.raises(api.ApiError) as exc:
        api.scan_label_endpoint("label.jpg", b"not an image at all")
    assert exc.value.status in (422, 503)


@pytest.mark.skipif(engine_name() != "tesseract", reason="needs the tesseract engine")
def test_end_to_end_ocr_of_a_rendered_panel():
    """Render a panel, OCR it, and check the allergens survive the round trip."""
    PIL = pytest.importorskip("PIL")
    pytest.importorskip("pytesseract")
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (900, 260), "white")
    draw = ImageDraw.Draw(image)
    y = 20
    for line in [
        "INGREDIENTS: Refined Wheat Flour (Maida), Sugar,",
        "Butter, Milk Solids, Soy Lecithin, Iodised Salt.",
    ]:
        draw.text((20, y), line, fill="black")
        y += 40

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")

    status, product = api.scan_label_endpoint("panel.png", buffer.getvalue())
    assert status == 200
    assert product["source"] == "LABEL_PHOTO"
    assert product["data_confidence"] in ("MEDIUM", "LOW")
    names = " ".join(i["name"] for i in product["ingredients"]).lower()
    assert "wheat" in names or "maida" in names
