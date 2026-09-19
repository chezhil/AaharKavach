"""A small offline product catalogue.

Open Food Facts is the real source; this is the safety net. Conference wifi
fails, OFF rate-limits, and a demo that dies on a network hiccup is a demo you
cannot record. Used only when the live lookup errors or returns nothing, and
the response is marked so the UI can say where the data came from.
"""

from __future__ import annotations

from .contracts import Product

_RAW: list[dict] = [
    {
        "barcode": "8901063152762", "name": "Good Day Butter Cookies", "brand": "Britannia",
        "categories": ["Biscuits", "Cookies"], "data_confidence": "HIGH",
        "ingredients": ["Refined Wheat Flour (Maida)", "Sugar", "Butter", "Milk Solids",
                        "Invert Sugar Syrup", "Soy Lecithin", "Raising Agent (E503)", "Salt"],
    },
    {
        "barcode": "8901058000108", "name": "2-Minute Masala Noodles", "brand": "Maggi",
        "categories": ["Instant Noodles"], "data_confidence": "HIGH",
        "ingredients": ["Refined Wheat Flour (Maida)", "Palm Oil", "Salt", "Wheat Gluten",
                        "Mixed Spices", "Flavour Enhancer (E635)", "Acidity Regulator (E330)"],
    },
    {
        "barcode": "5000159461122", "name": "Snickers Bar", "brand": "Mars",
        "categories": ["Chocolate Bars"], "data_confidence": "HIGH",
        "ingredients": ["Milk Chocolate", "Peanuts", "Glucose Syrup", "Sugar", "Milk Solids",
                        "Egg White", "Soy Lecithin", "Salt"],
    },
    {
        # The only safe pick in Biscuits/Cookies. Without it a Good Day scan has
        # no alternatives to offer at all: Oreo is the sole other biscuit and it
        # carries maida and soy lecithin, so it never clears the whole household.
        "barcode": "8904063200117", "name": "Millet & Jaggery Cookies", "brand": "Early Foods",
        "categories": ["Biscuits", "Cookies"], "data_confidence": "HIGH",
        "ingredients": ["Ragi Flour", "Rice Flour", "Jaggery", "Sunflower Oil",
                        "Sunflower Lecithin", "Cardamom", "Salt"],
    },
    {
        "barcode": "7622210449283", "name": "Oreo Original", "brand": "Cadbury",
        "categories": ["Biscuits", "Cookies"], "data_confidence": "HIGH",
        "ingredients": ["Refined Wheat Flour (Maida)", "Sugar", "Palm Oil", "Cocoa Powder",
                        "Invert Sugar Syrup", "Soy Lecithin", "Raising Agent (E500)"],
    },
    {
        "barcode": "8901491101837", "name": "India's Magic Masala Chips", "brand": "Lay's",
        "categories": ["Chips", "Savoury Snacks"], "data_confidence": "MEDIUM",
        "ingredients": ["Potato", "Palm Oil", "Spice Mix", "Milk Solids",
                        "Flavour Enhancer (E627)", "Flavour Enhancer (E631)", "Acidity Regulator (E330)"],
    },
    {
        "barcode": "8901719101090", "name": "Taaza Toned Milk", "brand": "Amul",
        "categories": ["Dairy", "Milk"], "data_confidence": "HIGH",
        "ingredients": ["Toned Milk"],
    },
    {
        "barcode": "7394376616068", "name": "Oat Drink Barista Edition", "brand": "Oatly",
        "categories": ["Plant Milk", "Milk"], "data_confidence": "HIGH",
        "ingredients": ["Water", "Oats", "Rapeseed Oil", "Calcium Carbonate", "Salt"],
    },
    {
        "barcode": "8904004401234", "name": "Special Namkeen Mixture", "brand": "Shree Ganesh",
        "categories": ["Savoury Snacks"], "data_confidence": "LOW",
        "ingredients": ["Gram Flour", "Edible Vegetable Oil", "Spices"],
    },
    {
        "barcode": "8906087130057", "name": "Multigrain Energy Bar", "brand": "Yoga Bar",
        "categories": ["Snack Bars"], "data_confidence": "MEDIUM",
        "ingredients": ["Dates", "Almond", "Oats", "Cashew", "Honey"],
    },
    {
        "barcode": "8904223830012", "name": "Millet Crunchies, Lightly Salted", "brand": "Slurrp Farm",
        "categories": ["Savoury Snacks", "Chips"], "data_confidence": "HIGH",
        "ingredients": ["Ragi Millet", "Rice", "Sunflower Oil", "Salt"],
    },
    {
        "barcode": "8901234567895", "name": "Strawberry Yoghurt Drink", "brand": "Fresh Farms",
        "categories": ["Dairy", "Yoghurt"], "data_confidence": "MEDIUM",
        "ingredients": ["Toned Milk", "Sugar", "Strawberry Pulp", "Carmine (E120)", "Stabiliser (E471)"],
    },
    {
        "barcode": "8908003847412", "name": "70% Dark Chocolate, Nut-Free Facility", "brand": "Pascati",
        "categories": ["Chocolate Bars"], "data_confidence": "HIGH",
        "ingredients": ["Cocoa Mass", "Sugar", "Cocoa Butter", "Vanilla"],
    },
    {
        "barcode": "8901030865278", "name": "Banana Chips, Kerala Style", "brand": "Beyond Snack",
        "categories": ["Chips", "Savoury Snacks"], "data_confidence": "HIGH",
        "ingredients": ["Banana", "Coconut Oil", "Salt", "Turmeric"],
    },
]


def _to_product(row: dict) -> Product:
    from .adapters import ingredient_from_token

    return Product(
        barcode=row["barcode"],
        name=row["name"],
        brand=row.get("brand"),
        categories=list(row.get("categories", [])),
        ingredients=[ingredient_from_token(t) for t in row["ingredients"]],
        data_confidence=row.get("data_confidence", "HIGH"),
        source="OFFLINE_CATALOGUE",
    )


CATALOGUE: dict[str, dict] = {row["barcode"]: row for row in _RAW}


def lookup(barcode: str) -> Product | None:
    row = CATALOGUE.get(str(barcode).strip())
    return _to_product(row) if row else None


def all_products() -> list[Product]:
    return [_to_product(row) for row in _RAW]
