"""E-numbers and food additive mappings.

Each entry follows the OpenSearch document schema for the `additives` index:
  {
    "additive_id":   "E120",                 # Canonical E-number
    "name":          "Carmine / Cochineal",  # Common name(s)
    "aliases":       ["Carmine", "Cochineal", "E120", "Natural Red 4", "Crimson Lake", "Cochineal extract"],
    "is_derived_from": ["insects"],          # Source categories (upper-case: lists of allergens / animal)
    "derived_from":   { "animal": "insects (cochineal scale)", "insect": "cochineal scale insect" },
    "allergen_tags": ["carmine", "insect_derived"],   # Standard allergen taxonomy keys
    "risk_level": "MODERATE_RISK",           # Static domain risk (pre-allergy match)
    "top_uses": ["food colorant", "beverage colorant", "cosmetics"],
    "vegan_vegetarian": "Not vegan or vegetarian (insect-derived)",
    "plain_explanation": "...",
    "confidence_source": "EU additive regulation, Codex Alimentarius",
  }

`risk_level` is descriptive metadata ONLY. Actual per-user severity comes from
the household profile. This field lets Role 1 / the UI surface "inherent risk 
weight" when a user still has the generic "additive warning" default.
"""

# Risk tiers used by the confidence/severity helpers.
RISK_LOW = "LOW_RISK"
RISK_MODERATE = "MODERATE_RISK"
RISK_HIGH = "HIGH_RISK"


E_NUMBERS = [
    # ------------------------------------------------------------------ #
    # Colourants                                                        #
    # ------------------------------------------------------------------ #
    {
        "additive_id": "E100",
        "name": "Curcumin",
        "aliases": ["E100", "Turmeric extract", "Natural Yellow 3"],
        "is_derived_from": ["plant"],
        "derived_from": {"plant": "turmeric rhizome"},
        "allergen_tags": [],
        "risk_level": RISK_LOW,
        "top_uses": ["food colorant", "yellow colouring"],
        "vegan_vegetarian": "Vegan-friendly (plant-derived)",
        "plain_explanation": "A natural yellow colouring made from turmeric",
        "confidence_source": "EFSA re-evaluation (2010); generally recognised as low risk of allergy",
    },
    {
        "additive_id": "E120",
        "name": "Carmine / Cochineal",
        "aliases": ["E120", "Carmine", "Cochineal", "Natural Red 4", "Crimson Lake", "Cochineal extract"],
        "is_derived_from": ["insect", "animal"],
        "derived_from": {"insect": "cochineal scale insect (Dactylopius coccus)", "animal": "insect shells/extract"},
        "allergen_tags": ["carmine", "insect_derived"],
        "risk_level": RISK_MODERATE,
        "top_uses": ["red food colouring", "beverage colouring", "fruit yoghurt", "candy", "lipstick/cosmetics"],
        "vegan_vegetarian": "Not vegan / not vegetarian (insect-derived)",
        "plain_explanation": "A deep red colouring made from crushed cochineal insects — no taste, purely for appearance",
        "confidence_source": "EU/UK approved; documented case reports of anaphylaxis to carmine",
    },
    {
        "additive_id": "E122",
        "name": "Azorubine (Carmoisine)",
        "aliases": ["E122", "Carmoisine", "Azorubine"],
        "is_derived_from": ["synthetic"],
        "derived_from": {"synthetic": "synthetic azo dye"},
        "allergen_tags": ["azo_dye", "sodium_benzoate_synergy"],
        "risk_level": RISK_MODERATE,
        "top_uses": ["red food colouring", "confectionery", "drinks"],
        "vegan_vegetarian": "Vegan-friendly (synthetic)",
        "plain_explanation": "A synthetic red colouring linked in some studies to hyperactivity in children when combined with certain preservatives",
        "confidence_source": "EFSA ADI; Southampton study (2007) cautionary association",
    },
    {
        "additive_id": "E124",
        "name": "Ponceau 4R",
        "aliases": ["E124", "Cochineal Red A"],
        "is_derived_from": ["synthetic"],
        "derived_from": {"synthetic": "synthetic azo dye"},
        "allergen_tags": ["azo_dye"],
        "risk_level": RISK_MODERATE,
        "top_uses": ["red food colouring", "desserts", "biscuits"],
        "vegan_vegetarian": "Vegan-friendly (synthetic)",
        "plain_explanation": "A synthetic red dye; monitored because some people react to azo dyes with hives or asthma symptoms",
        "confidence_source": "EFSA; Southampton study (2007) cautionary association",
    },
    {
        "additive_id": "E150d",
        "name": "Sulphite Ammonia Caramel",
        "aliases": ["E150d", "Caramel colour", "Class IV caramel"],
        "is_derived_from": ["synthetic"],
        "derived_from": {"synthetic": "caramelised sugar processed with sulphites and ammonia"},
        "allergen_tags": [],
        "risk_level": RISK_LOW,
        "top_uses": ["cola and dark soft drinks", "sauces", "beer"],
        "vegan_vegetarian": "Vegan-friendly",
        "plain_explanation": "The dark colour in cola-type drinks, produced by carefully heating sugar with ammonia and sulphites",
        "confidence_source": "EFSA re-evaluation (2011)",
    },
    {
        "additive_id": "E160b",
        "name": "Annatto",
        "aliases": ["E160b", "Annatto extract", "Bixin", "Norbixin"],
        "is_derived_from": ["plant"],
        "derived_from": {"plant": "achiote (annatto) seeds"},
        "allergen_tags": ["annatto"],
        "risk_level": RISK_MODERATE,
        "top_uses": ["orange-yellow colouring", "cheese rind", "butter", "margarine", "snack seasoning"],
        "vegan_vegetarian": "Vegan-friendly (plant-derived)",
        "plain_explanation": "An orange-yellow colour from annatto seeds; a rare but documented cause of allergy and hives",
        "confidence_source": "Journal case reports; FAIA (Food Allergy and Intolerance Association) guidance",
    },
    {
        "additive_id": "E102",
        "name": "Tartrazine",
        "aliases": ["E102", "Yellow 5", "FD&C Yellow 5", "Tartrazine"],
        "is_derived_from": ["synthetic"],
        "derived_from": {"synthetic": "synthetic azo dye (petroleum-based)"},
        "allergen_tags": ["azo_dye", "sodium_benzoate_synergy"],
        "risk_level": RISK_MODERATE,
        "top_uses": ["yellow food colouring", "soft drinks", "biscuits", "candy"],
        "vegan_vegetarian": "Vegan-friendly (synthetic)",
        "plain_explanation": "A common yellow synthetic dye that can trigger hives or asthma in sensitive people, linked to hyperactivity in children",
        "confidence_source": "EFSA; multiple controlled trials (McCann et al. 2007)",
    },

    # ------------------------------------------------------------------ #
    # Preservatives                                                      #
    # ------------------------------------------------------------------ #
    {
        "additive_id": "E200",
        "name": "Sorbic Acid",
        "aliases": ["E200", "Sorbinsäure"],
        "is_derived_from": ["synthetic"],
        "derived_from": {"synthetic": "synthetically produced organic acid"},
        "allergen_tags": [],
        "risk_level": RISK_LOW,
        "top_uses": ["preservative in cheese", "baked goods", "wine", "dried fruit"],
        "vegan_vegetarian": "Vegan-friendly",
        "plain_explanation": "A preservative that stops mould and yeast from growing in moist foods like cheese and baked items",
        "confidence_source": "EFSA re-evaluation; widely tolerated",
    },
    {
        "additive_id": "E211",
        "name": "Sodium Benzoate",
        "aliases": ["E211", "Benzoic acid sodium salt", "Sodium benzoate"],
        "is_derived_from": ["synthetic"],
        "derived_from": {"synthetic": "sodium salt of benzoic acid"},
        "allergen_tags": ["sodium_benzoate_synergy"],
        "risk_level": RISK_MODERATE,
        "top_uses": ["preservative for acidic drinks", "sauces", "pickles", "salad dressings"],
        "vegan_vegetarian": "Vegan-friendly",
        "plain_explanation": "Stops microbes growing in acidic foods and fizzy drinks; can worsen asthma in rare cases and is linked to hyperactivity when combined with artificial colours",
        "confidence_source": "EFSA; Southampton study association",
    },
    {
        "additive_id": "E223",
        "name": "Sodium Metabisulphite",
        "aliases": ["E223", "Sodium disulphite", "Metabisulfite"],
        "is_derived_from": ["synthetic", "sulphite"],
        "derived_from": {"sulphite": "sulphite preservative"},
        "allergen_tags": ["sulphites", "sulphur_dioxide_group"],
        "risk_level": RISK_HIGH,
        "top_uses": ["dried fruit", "wine and beer", "dried potatoes", "bottled lemon/lime juice"],
        "vegan_vegetarian": "Vegan-friendly",
        "plain_explanation": "A sulphite preservative that keeps dried fruit and wine from browning, but can trigger asthma attacks and breathing trouble in sulphite-sensitive people",
        "confidence_source": "EU labelling obligation above 10 mg/kg; strong clinical consensus",
    },
    {
        "additive_id": "E224",
        "name": "Potassium Metabisulphite",
        "aliases": ["E224", "Potassium disulphite", "Potassium metabisulfite"],
        "is_derived_from": ["synthetic", "sulphite"],
        "derived_from": {"sulphite": "sulphite preservative"},
        "allergen_tags": ["sulphites", "sulphur_dioxide_group"],
        "risk_level": RISK_HIGH,
        "top_uses": ["wine", "beer", "cider", "dried fruit", "fruit juices"],
        "vegan_vegetarian": "Vegan-friendly",
        "plain_explanation": "Another sulphite preservative common in wine and dried fruits; people with sulphite sensitivity should avoid it",
        "confidence_source": "EU labelling obligation; clinical consensus",
    },
    {
        "additive_id": "E220",
        "name": "Sulphur Dioxide",
        "aliases": ["E220", "Sulfur dioxide"],
        "is_derived_from": ["synthetic", "sulphite"],
        "derived_from": {"sulphite": "sulphite preservative gas"},
        "allergen_tags": ["sulphites", "sulphur_dioxide_group"],
        "risk_level": RISK_HIGH,
        "top_uses": ["dried fruit", "wine", "fruit juice concentrates", "pickled vegetables"],
        "vegan_vegetarian": "Vegan-friendly",
        "plain_explanation": "A gas preservative used to keep dried fruit looking bright; one of the most common triggers of asthma symptoms in food",
        "confidence_source": "EU mandatory labelling above 10 mg/kg; strong clinical evidence",
    },
    {
        "additive_id": "E621",
        "name": "Monosodium Glutamate (MSG)",
        "aliases": ["E621", "MSG", "Monosodium glutamate", "Chinese seasoning"],
        "is_derived_from": ["fermented"],
        "derived_from": {"fermented": "glutamic acid (often fermented from corn, wheat or beet)"},
        "allergen_tags": ["glutamate_sensitivity"],
        "risk_level": RISK_MODERATE,
        "top_uses": ["flavour enhancer", "instant noodles", "savoury snacks", "restaurant food"],
        "vegan_vegetarian": "Can be vegan but source crop must be checked (corn/wheat/beet)",
        "plain_explanation": "A flavour enhancer that adds savoury 'umami' taste; causes temporary symptoms like flushing or headache in a minority of sensitive people, though it is not a true allergy for most",
        "confidence_source": "EFSA re-evaluation (2017) set ADI; general consensus not a classic allergen",
    },

    # ------------------------------------------------------------------ #
    # Emulsifiers / stabilisers                                          #
    # ------------------------------------------------------------------ #
    {
        "additive_id": "E322",
        "name": "Lecithin",
        "aliases": ["E322", "Soy lecithin", "Sunflower lecithin", "Lecithin"],
        "is_derived_from": ["plant", "soy"],
        "derived_from": {"soy": "often extracted from soybeans", "plant": "can also be from sunflower or rapeseed"},
        "allergen_tags": ["soybeans", "soy_derived"],
        "risk_level": RISK_MODERATE,
        "top_uses": ["emulsifier in chocolate", "margarine", "dressings", "bakery"],
        "vegan_vegetarian": "Vegan-friendly",
        "plain_explanation": "Helps oil and water mix together smoothly, found in chocolate and spreads; if it comes from soy it can matter to soy-allergic people, though the protein content is usually very low",
        "confidence_source": "EU allergen declaration rules (soy must be declared); allergy guidance",
    },
    {
        "additive_id": "E471",
        "name": "Mono- and diglycerides of fatty acids",
        "aliases": ["E471", "Mono- and diglycerides", "Glyceryl monostearate"],
        "is_derived_from": ["animal_or_plant"],
        "derived_from": {"plant": "often plant fats (palm, rapeseed)", "animal": "can be animal fat — source not always stated"},
        "allergen_tags": [],
        "risk_level": RISK_LOW,
        "top_uses": ["emulsifier in bakery", "margarine", "ice cream", "confectionery"],
        "vegan_vegetarian": "Variable — can be plant or animal fat origin; source is not always declared",
        "plain_explanation": "A smooth-mixing agent used in breads and spreads; the plant or animal origin isn't always written on the label",
        "confidence_source": "EU labelling rules (origin usually not declared)",
    },
    {
        "additive_id": "E322-soy",
        "name": "Lecithin (soy)",
        "aliases": ["E322", "Soy lecithin"],
        "is_derived_from": ["soy"],
        "derived_from": {"soy": "soybean extraction"},
        "allergen_tags": ["soybeans", "soy_derived"],
        "risk_level": RISK_MODERATE,
        "top_uses": ["emulsifier", "chocolate", "bakery"],
        "vegan_vegetarian": "Vegan-friendly",
        "plain_explanation": "Lecithin extracted from soy; most soy-allergic people tolerate it because the allergenic proteins are largely removed, but caution is advised with confirmed allergy",
        "confidence_source": "EU mandatory allergen declaration for soy",
    },

    # ------------------------------------------------------------------ #
    # Sweeteners                                                         #
    # ------------------------------------------------------------------ #
    {
        "additive_id": "E951",
        "name": "Aspartame",
        "aliases": ["E951", "Aspartame", "NutraSweet", "Equal"],
        "is_derived_from": ["synthetic"],
        "derived_from": {"synthetic": "two amino acids, aspartic acid and phenylalanine"},
        "allergen_tags": ["phenylalanine_source"],
        "risk_level": RISK_MODERATE,
        "top_uses": ["diet soft drinks", "sugar-free gum", "low-calorie desserts"],
        "vegan_vegetarian": "Vegan-friendly",
        "plain_explanation": "An intense sweetener; people with a rare condition called phenylketonuria (PKU) must avoid it because it contains phenylalanine",
        "confidence_source": "EU/EFSA re-evaluation (2013); PKU labelling mandated",
    },
    {
        "additive_id": "E960",
        "name": "Steviol glycosides (Stevia)",
        "aliases": ["E960", "Stevia", "Steviol glycosides", "Rebaudioside A"],
        "is_derived_from": ["plant"],
        "derived_from": {"plant": "stevia plant leaves"},
        "allergen_tags": [],
        "risk_level": RISK_LOW,
        "top_uses": ["sugar-free drinks", "diet products", "tabletop sweetener"],
        "vegan_vegetarian": "Vegan-friendly (plant-derived)",
        "plain_explanation": "A natural zero-calorie sweetener extracted from the stevia leaf",
        "confidence_source": "EFSA re-evaluation; low allergenicity",
    },
]


# Alias index built once at import time so Role 1 / search can hit it fast.
#   aliases -> additive_id (lower-cased keys for case insensitivity)
# NOTE: first entry wins so the canonical additive_id (e.g. "E322") is never
# shadowed by a derived variant (e.g. "E322-soy") that reuses the same alias.
ALIAS_INDEX = {}
for _entry in E_NUMBERS:
    for _alias in _entry["aliases"]:
        ALIAS_INDEX.setdefault(_alias.lower(), _entry["additive_id"])


def lookup_additive(token: str) -> dict | None:
    """Return the additive entry for an EXACT token (E-number or alias).

    Used by the fuzzy matcher after it has already normalised casing.
    """
    idx = token.lower()
    if idx in ALIAS_INDEX:
        add_id = ALIAS_INDEX[idx]
        return next(e for e in E_NUMBERS if e["additive_id"] == add_id)
    return None