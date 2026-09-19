"""Plain-language ingredient descriptions for the tap-to-explain feature.

Schema for the `descriptions` index:
  {
    "ingredient_id":  "sodium_caseinate",
    "name":           "Sodium Caseinate",
    "aliases":        ["casein", "sodium caseinate", "milk protein"],
    "plain_explanation": "A milk protein used to thicken or stabilise foods...",
    "alternate_names": ["Sodium Caseinate", "Casein Sodium Salt"],
    "tone":           "neutral",          # neutral | caution | urgent
    "category":       "protein derivative",
    "typical_role":   "thickener / stabiliser",
    "confidence_source": "US FDA; Codex Alimentarius",
  }

`tone` guides the UI: a neutral tone for harmless ingredients, `caution` when
we should not alarm, `urgent` only for genuinely high-risk items.
"""

DESCRIPTIONS = {
    # ------------------------------------------------------------------ #
    # Milk-derived                                                       #
    # ------------------------------------------------------------------ #
    "sodium_caseinate": {
        "ingredient_id": "sodium_caseinate",
        "name": "Sodium Caseinate",
        "aliases": ["casein", "sodium caseinate", "caseinate", "milk protein", "calcium caseinate"],
        "plain_explanation": "A milk protein used to thicken, stabilise and add creaminess. It is dairy — important for anyone avoiding milk products.",
        "alternate_names": ["Casein", "Caseinate sodium salt", "Calcium caseinate"],
        "tone": "caution",
        "category": "protein derivative",
        "typical_role": "thickener / stabiliser",
        "confidence_source": "US FDA food labelling; Codex Alimentarius",
    },
    "whey_protein": {
        "ingredient_id": "whey_protein",
        "name": "Whey Protein",
        "aliases": ["whey", "whey protein", "whey protein concentrate", "whey protein isolate", "whey powder"],
        "plain_explanation": "A by-product of cheesemaking and a rich source of milk protein. It is dairy — cannot be used in a milk-free diet.",
        "alternate_names": ["Whey", "Whey powder", "Whey protein concentrate", "Milk serum protein"],
        "tone": "caution",
        "category": "protein derivative",
        "typical_role": "protein source / binder",
        "confidence_source": "US FDA; EUR-LEX dairy terms",
    },
    "ghee": {
        "ingredient_id": "ghee",
        "name": "Ghee",
        "aliases": ["ghee", "clarified butter", "anhydrous milk fat", "desi ghee"],
        "plain_explanation": "Clarified butter — milk fat with the water and solids removed. It still comes from milk and is not dairy-free.",
        "alternate_names": ["Clarified butter", "Anhydrous milk fat"],
        "tone": "caution",
        "category": "fat / butter product",
        "typical_role": "cooking fat / flavour",
        "confidence_source": "US FDA; FSSAI standards",
    },

    # ------------------------------------------------------------------ #
    # Plant oils / emulsifiers                                           #
    # ------------------------------------------------------------------ #
    "soy_lecithin": {
        "ingredient_id": "soy_lecithin",
        "name": "Soy Lecithin",
        "aliases": ["soy lecithin", "lecithin", "e322", "soya lecithin"],
        "plain_explanation": "A natural emulsifier extracted from soybeans that keeps oil and water mixed, e.g. in chocolate. The protein level is very low, so most soy-allergic people tolerate it, but check with your doctor.",
        "alternate_names": ["E322", "Lecithin", "Soya lecithin"],
        "tone": "caution",
        "category": "emulsifier",
        "typical_role": "emulsifier",
        "confidence_source": "EU Annex II soy declaration; FARE guidance",
    },
    "sunflower_lecithin": {
        "ingredient_id": "sunflower_lecithin",
        "name": "Sunflower Lecithin",
        "aliases": ["sunflower lecithin", "lecithin"],
        "plain_explanation": "An emulsifier made from sunflower seeds — a soy-free alternative keeps oil and water blended smoothly.",
        "alternate_names": ["Lecithin"],
        "tone": "neutral",
        "category": "emulsifier",
        "typical_role": "emulsifier",
        "confidence_source": "Food additive databases",
    },
    "palm_oil": {
        "ingredient_id": "palm_oil",
        "name": "Palm Oil",
        "aliases": ["palm oil", "palm kernel oil", "rbpo", "refined palm oil"],
        "plain_explanation": "A widely used vegetable oil from palm fruit. Not an allergen itself, but it is high in saturated fat and carries sustainability concerns.",
        "alternate_names": ["Palm kernel oil", "Refined palm oil", "Elaeis guineensis oil"],
        "tone": "neutral",
        "category": "vegetable oil",
        "typical_role": "oil / fat source",
        "confidence_source": "Codex; EU labelling",
    },

    # ------------------------------------------------------------------ #
    # Additives / colours                                                #
    # ------------------------------------------------------------------ #
    "carmine": {
        "ingredient_id": "carmine",
        "name": "Carmine",
        "aliases": ["carmine", "cochineal", "e120", "crimson lake", "natural red 4", "cochineal extract"],
        "plain_explanation": "A red dye made from crushed cochineal insects. It colours foods like yoghurt and candy red. Rarely causes allergy and is not suitable for vegans.",
        "alternate_names": ["Cochineal extract", "Natural Red 4", "Crimson lake"],
        "tone": "caution",
        "category": "colourant",
        "typical_role": "red colourant",
        "confidence_source": "FDA; EFSA re-evaluation",
    },
    "tartrazine": {
        "ingredient_id": "tartrazine",
        "name": "Tartrazine",
        "aliases": ["tartrazine", "e102", "yellow 5", "fd&c yellow no. 5", "fd&c yellow fig no. 5"],
        "plain_explanation": "A synthetic yellow dye added to drinks and candy. Some people get hives or asthma symptoms; linked to hyperactivity in children, especially with preservatives.",
        "alternate_names": ["Yellow 5", "FD&C Yellow No. 5", "E102"],
        "tone": "neutral",
        "category": "colourant",
        "typical_role": "yellow colourant",
        "confidence_source": "EFSA; McCann et al. 2007",
    },
    "monosodium_glutamate": {
        "ingredient_id": "monosodium_glutamate",
        "name": "Monosodium Glutamate (MSG)",
        "aliases": ["monosodium glutamate", "msg", "e621", "glutamate"],
        "plain_explanation": "A savoury flavour enhancer. A small group of people experience flushing or headaches after large amounts, but for most it is safe and it is not a classic allergen.",
        "alternate_names": ["MSG", "E621", "Glutamic acid monosodium salt"],
        "tone": "neutral",
        "category": "flavour enhancer",
        "typical_role": "umami flavour enhancer",
        "confidence_source": "EFSA re-evaluation (2017)",
    },

    # ------------------------------------------------------------------ #
    # Sweeteners                                                         #
    # ------------------------------------------------------------------ #
    "aspartame": {
        "ingredient_id": "aspartame",
        "name": "Aspartame",
        "aliases": ["aspartame", "e951", "nutrasweet", "equal"],
        "plain_explanation": "A zero-calorie sweetener used in diet drinks. It contains phenylalanine — people with PKU must avoid it, and it is labelled for that reason on packaging.",
        "alternate_names": ["E951", "NutraSweet", "Equal"],
        "tone": "neutral",
        "category": "sweetener",
        "typical_role": "low-calorie sweetener",
        "confidence_source": "EFSA re-evaluation (2013); PKU labelling requirement",
    },

    # ------------------------------------------------------------------ #
    # Grains                                                             #
    # ------------------------------------------------------------------ #
    "buckwheat": {
        "ingredient_id": "buckwheat",
        "name": "Buckwheat",
        "aliases": ["buckwheat", "kasha", "soba", "buckwheat flour"],
        "plain_explanation": "Despite the name, buckwheat is NOT a wheat — it is a gluten-free seed related to rhubarb. It is safe for gluten-free diets, though it can be its own (uncommon) allergen in some countries.",
        "alternate_names": ["Kasha", "Soba", "Buckwheat flour"],
        "tone": "neutral",
        "category": "gluten-free grain-like seed",
        "typical_role": "flour / noodle base",
        "confidence_source": "Coeliac UK; EU gluten-free rules",
    },
    "seitan": {
        "ingredient_id": "seitan",
        "name": "Seitan",
        "aliases": ["seitan", "wheat gluten", "vital wheat gluten", "mock meat", "wheat meat"],
        "plain_explanation": "A 'mock meat' made almost entirely from wheat gluten — it is wheat, so it is strictly off-limits for gluten-free diets.",
        "alternate_names": ["Wheat gluten", "Vital wheat gluten", "Wheat meat"],
        "tone": "caution",
        "category": "protein / wheat product",
        "typical_role": "meat substitute",
        "confidence_source": "FDA; Codex",
    },

    # ------------------------------------------------------------------ #
    # Additive misc / gelatin                                            #
    # ------------------------------------------------------------------ #
    "gelatin": {
        "ingredient_id": "gelatin",
        "name": "Gelatin",
        "aliases": ["gelatin", "gelatine", "hydrolysed gelatin"],
        "plain_explanation": "A gelling agent made from animal (usually pig or cow) connective tissue. It is used in jelly, gummy sweets and marshmallows — not suitable for vegetarians/vegans; allergen risk to gelatin itself is very rare.",
        "alternate_names": ["Gelatine", "E441"],
        "tone": "neutral",
        "category": "gelling agent",
        "typical_role": "gelling / thickening",
        "confidence_source": "FDA; EU additive regulation",
    },
    "agar_agar": {
        "ingredient_id": "agar_agar",
        "name": "Agar Agar",
        "aliases": ["agar", "agar-agar", "agar powder", "e406", "kanten"],
        "plain_explanation": "A plant-based setting agent made from seaweed — the vegan alternative to gelatin.",
        "alternate_names": ["Agar", "E406", "Kanten"],
        "tone": "neutral",
        "category": "gelling agent",
        "typical_role": "gelling / thickening (vegan)",
        "confidence_source": "EU additive regulation",
    },
    "xanthan_gum": {
        "ingredient_id": "xanthan_gum",
        "name": "Xanthan Gum",
        "aliases": ["xanthan gum", "e415", "xanthan"],
        "plain_explanation": "A thickening gum made by fermenting sugar with bacteria. Common in gluten-free baking and sauces. Very rarely triggers reactions.",
        "alternate_names": ["E415", "Corn sugar gum"],
        "tone": "neutral",
        "category": "thickener",
        "typical_role": "thickener / stabiliser",
        "confidence_source": "EFSA; FAO",
    },
    "guar_gum": {
        "ingredient_id": "guar_gum",
        "name": "Guar Gum",
        "aliases": ["guar gum", "e412", "guaran"],
        "plain_explanation": "A thickener from the guar bean, used in ice cream and gluten-free baking. A rare risk of serious reaction has been reported mostly in high-dose laxative products.",
        "alternate_names": ["E412", "Guaran"],
        "tone": "neutral",
        "category": "thickener",
        "typical_role": "thickener (gluten-free baking)",
        "confidence_source": "FDA; rare case reports in supplement doses",
    },

    # ------------------------------------------------------------------ #
    # Flavourings                                                        #
    # ------------------------------------------------------------------ #
    "natural_flavour": {
        "ingredient_id": "natural_flavour",
        "name": "Natural Flavour",
        "aliases": ["natural flavour", "natural flavor", "natural flavouring", "natural flavourings"],
        "plain_explanation": "A flavour extracted from plant or animal sources — but the exact source is legally allowed to stay hidden. When combined with undeclared allergens, this is a 'we're not sure' moment: check the manufacturer if you have a severe allergy.",
        "alternate_names": ["Natural flavouring", "Natural flavors"],
        "tone": "caution",
        "category": "flavouring",
        "typical_role": "flavour source",
        "confidence_source": "US 21 CFR §101.22; EU flavour regulation",
    },
    "citric_acid": {
        "ingredient_id": "citric_acid",
        "name": "Citric Acid",
        "aliases": ["citric acid", "e330", "lemon salt"],
        "plain_explanation": "A common acidic additive used for tart flavour and as a preservative. It is usually fermented from corn or sugar, not from citrus fruit.",
        "alternate_names": ["E330", "Lemon salt"],
        "tone": "neutral",
        "category": "acidulant",
        "typical_role": "acidity regulator / preservative",
        "confidence_source": "EFSA; food chemistry texts",
    },

    # ------------------------------------------------------------------ #
    # Common whole spices and pantry staples — no allergen table covers   #
    # these, so every scan of a typical Indian spice mix asked the model  #
    # about each one individually. These are common-knowledge, low-risk   #
    # facts, unlike the allergen/additive tables above.                   #
    # ------------------------------------------------------------------ #
    "salt": {
        "ingredient_id": "salt",
        "name": "Salt",
        "aliases": ["salt", "iodised salt", "iodized salt", "table salt", "sea salt", "rock salt"],
        "plain_explanation": "Sodium chloride, used to season and preserve food. 'Iodised' means iodine has been added, a standard public-health fortification with no allergen concern.",
        "alternate_names": ["Iodised Salt", "Table Salt", "Sea Salt"],
        "tone": "neutral",
        "category": "seasoning",
        "typical_role": "seasoning / preservative",
        "confidence_source": "Common culinary knowledge",
    },
    "cardamom": {
        "ingredient_id": "cardamom",
        "name": "Cardamom",
        "aliases": ["cardamom", "elaichi", "green cardamom", "black cardamom"],
        "plain_explanation": "An aromatic spice pod from the ginger family, common in Indian sweets, chai and spice blends.",
        "alternate_names": ["Elaichi"],
        "tone": "neutral",
        "category": "spice",
        "typical_role": "flavouring",
        "confidence_source": "Common culinary knowledge",
    },
    "bay_leaf": {
        "ingredient_id": "bay_leaf",
        "name": "Bay Leaf",
        "aliases": ["bay leaf", "bay leaves", "tej patta"],
        "plain_explanation": "A dried aromatic leaf used whole to flavour rice, curries and stocks, then usually removed before eating.",
        "alternate_names": ["Tej Patta"],
        "tone": "neutral",
        "category": "spice",
        "typical_role": "flavouring",
        "confidence_source": "Common culinary knowledge",
    },
    "nutmeg": {
        "ingredient_id": "nutmeg",
        "name": "Nutmeg",
        "aliases": ["nutmeg", "jaiphal"],
        "plain_explanation": "A warm, slightly sweet spice ground from the seed of the nutmeg tree, used in small amounts in spice blends and baked goods.",
        "alternate_names": ["Jaiphal"],
        "tone": "neutral",
        "category": "spice",
        "typical_role": "flavouring",
        "confidence_source": "Common culinary knowledge",
    },
    "black_pepper": {
        "ingredient_id": "black_pepper",
        "name": "Black Pepper",
        "aliases": ["black pepper", "pepper", "kali mirch", "ground black pepper"],
        "plain_explanation": "A pungent spice from dried peppercorns, one of the most common seasonings worldwide.",
        "alternate_names": ["Kali Mirch"],
        "tone": "neutral",
        "category": "spice",
        "typical_role": "seasoning",
        "confidence_source": "Common culinary knowledge",
    },
    "ajwain": {
        "ingredient_id": "ajwain",
        "name": "Ajwain",
        "aliases": ["ajwain", "carom seeds", "bishop's weed"],
        "plain_explanation": "A small, pungent seed used in Indian cooking for its thyme-like flavour, and traditionally believed to aid digestion.",
        "alternate_names": ["Carom Seeds"],
        "tone": "neutral",
        "category": "spice",
        "typical_role": "flavouring",
        "confidence_source": "Common culinary knowledge",
    },
    "clove": {
        "ingredient_id": "clove",
        "name": "Clove",
        "aliases": ["clove", "cloves", "clove powder", "laung"],
        "plain_explanation": "A dried aromatic flower bud with a strong, sweet-spicy flavour, used sparingly in spice blends and desserts.",
        "alternate_names": ["Laung"],
        "tone": "neutral",
        "category": "spice",
        "typical_role": "flavouring",
        "confidence_source": "Common culinary knowledge",
    },
    "coriander_seed": {
        "ingredient_id": "coriander_seed",
        "name": "Coriander Seeds",
        "aliases": ["coriander seeds", "coriander seed", "dhania"],
        "plain_explanation": "The dried seed of the coriander plant, with a citrusy, nutty flavour distinct from the fresh leaf.",
        "alternate_names": ["Dhania"],
        "tone": "neutral",
        "category": "spice",
        "typical_role": "flavouring",
        "confidence_source": "Common culinary knowledge",
    },
    "cinnamon": {
        "ingredient_id": "cinnamon",
        "name": "Cinnamon",
        "aliases": ["cinnamon", "dalchini", "cassia"],
        "plain_explanation": "A warm, sweet spice made from the dried inner bark of the cinnamon tree, common in both sweet and savoury spice blends.",
        "alternate_names": ["Dalchini", "Cassia"],
        "tone": "neutral",
        "category": "spice",
        "typical_role": "flavouring",
        "confidence_source": "Common culinary knowledge",
    },
    "ginger": {
        "ingredient_id": "ginger",
        "name": "Ginger",
        "aliases": ["ginger", "dried ginger powder", "ginger powder", "sonth", "adrak"],
        "plain_explanation": "A pungent, warming rhizome used fresh or dried and powdered, extremely common across Indian cooking.",
        "alternate_names": ["Sonth", "Adrak"],
        "tone": "neutral",
        "category": "spice",
        "typical_role": "flavouring",
        "confidence_source": "Common culinary knowledge",
    },
    "red_chilli": {
        "ingredient_id": "red_chilli",
        "name": "Red Chilli Powder",
        "aliases": ["red chilli powder", "red chili powder", "chilli powder", "chili powder", "lal mirch"],
        "plain_explanation": "Dried red chillies ground into powder, used for heat and colour in spice blends and curries.",
        "alternate_names": ["Lal Mirch"],
        "tone": "neutral",
        "category": "spice",
        "typical_role": "seasoning",
        "confidence_source": "Common culinary knowledge",
    },
    "gram_flour": {
        "ingredient_id": "gram_flour",
        "name": "Gram Flour",
        "aliases": ["besan", "gram flour", "chickpea flour", "bengal gram flour"],
        "plain_explanation": "Flour milled from chickpeas (Bengal gram), used to bind and thicken savoury Indian dishes. It is legume-derived, not wheat, so it is naturally gluten-free — but a legume allergy would still apply.",
        "alternate_names": ["Besan", "Chickpea Flour"],
        "tone": "neutral",
        "category": "flour",
        "typical_role": "binder / thickener",
        "confidence_source": "Common culinary knowledge",
    },
}

# Alias index for descriptions (lower-cased alias -> description id)
DESCRIPTION_ALIAS_INDEX = {}
for _id, _entry in DESCRIPTIONS.items():
    for _alias in _entry["aliases"]:
        DESCRIPTION_ALIAS_INDEX[_alias.lower()] = _id
    DESCRIPTION_ALIAS_INDEX[_entry["name"].lower()] = _id


def lookup_description(token: str) -> dict | None:
    """Return the description entry for an exact token, or None."""
    idx = token.lower().strip()
    found = DESCRIPTION_ALIAS_INDEX.get(idx)
    return DESCRIPTIONS[found] if found else None