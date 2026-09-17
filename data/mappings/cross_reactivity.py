"""Cross-reactivity tables.

When a user's profile lists allergy X, we must also flag 'related risk' Y when
a product contains ingredient Y. Schema for the `cross_reactivity` index:
  {
    "reaction_id":    "latex_fruit_banana",
    "trigger":        "banana",                 # ingredient name as it appears on label
    "primary_allergy":"latex",                  # allergen that MUST be in the profile to engage warning
    "confidence":     0.95,                     # 0..1 strength of evidence
    "category":       "latex_fruit_syndrome",   # named syndrome / mechanism
    "reason":         "Latex and banana share the chitinase (hevein-like) proteins...",
    "headline":       "Banana is a known latex cross-reactor",
    "severity_bump":  "none",                   # none | caution | caution_and_monitor
  }

Role 1's pipeline: for each ingredient in the scanned product, for each profile
allergy, we check BOTH the allergen synonym resolution AND this table. If the
user hasn't listed the `primary_allergy`, we do NOT emit a cross-reactivity
warning (avoid noise).
"""

CROSS_REACTIVITY_TABLE = [
    # ------------------------------------------------------------------ #
    # Latex-fruit syndrome (hevein-like proteins / class I chitinases)   #
    # ------------------------------------------------------------------ #
    {
        "reaction_id": "latex_fruit_banana",
        "trigger": "banana",
        "primary_allergy": "latex",
        "confidence": 0.95,
        "category": "latex_fruit_syndrome",
        "reason": "Banana shares the same defence-related proteins (class I chitinases / hevein) with natural rubber latex.",
        "headline": "Banana is the most common latex cross-reactor",
        "severity_bump": "caution_and_monitor",
    },
    {
        "reaction_id": "latex_fruit_avocado",
        "trigger": "avocado",
        "primary_allergy": "latex",
        "confidence": 0.9,
        "category": "latex_fruit_syndrome",
        "reason": "Avocado contains hevein-like proteins homologous to the rubber tree protein.",
        "headline": "Avocado frequently cross-reacts with latex",
        "severity_bump": "caution_and_monitor",
    },
    {
        "reaction_id": "latex_fruit_kiwi",
        "trigger": "kiwi",
        "primary_allergy": "latex",
        "confidence": 0.85,
        "category": "latex_fruit_syndrome",
        "reason": "Kiwi carries allergens with epitopes shared with latex (actinidin and hevein-like domains).",
        "headline": "Kiwi is part of the latex-fruit cluster",
        "severity_bump": "caution",
    },
    {
        "reaction_id": "latex_fruit_chestnut",
        "trigger": "chestnut",
        "primary_allergy": "latex",
        "confidence": 0.85,
        "category": "latex_fruit_syndrome",
        "reason": "Chestnut shares a 30-kd chitinase with latex; a classic documented cross-reaction.",
        "headline": "Chestnut is a known latex cross-reactor",
        "severity_bump": "caution",
    },
    {
        "reaction_id": "latex_fruit_papaya",
        "trigger": "papaya",
        "primary_allergy": "latex",
        "confidence": 0.7,
        "category": "latex_fruit_syndrome",
        "reason": "Papaya shows in-vitro cross-reactivity with latex; clinical reactions are less common.",
        "headline": "Papaya may cross-react for some latex-allergic people",
        "severity_bump": "caution",
    },
    {
        "reaction_id": "latex_fruit_tomato",
        "trigger": "tomato",
        "primary_allergy": "latex",
        "confidence": 0.7,
        "category": "latex_fruit_syndrome",
        "reason": "Tomato has been reported in latex-fruit syndrome though frequency is lower.",
        "headline": "Tomato occasionally cross-reacts with latex",
        "severity_bump": "caution",
    },
    {
        "reaction_id": "latex_fruit_passion_fruit",
        "trigger": "passion fruit",
        "primary_allergy": "latex",
        "confidence": 0.7,
        "category": "latex_fruit_syndrome",
        "reason": "Passion fruit is occasionally reported in latex-fruit cross-reactivity.",
        "headline": "Passion fruit is a minor latex cross-reactor",
        "severity_bump": "caution",
    },
    {
        "reaction_id": "latex_fruit_potato",
        "trigger": "potato",
        "primary_allergy": "latex",
        "confidence": 0.6,
        "category": "latex_fruit_syndrome",
        "reason": "Potato has been linked to latex syndrome in a subset of patients via patatin.",
        "headline": "Potato is a weaker, less common latex cross-reactor",
        "severity_bump": "caution",
    },
    {
        "reaction_id": "latex_fruit_peach",
        "trigger": "peach",
        "primary_allergy": "latex",
        "confidence": 0.6,
        "category": "latex_fruit_syndrome",
        "reason": "Peach shows some in-vitro latex cross-reactivity.",
        "headline": "Peach shows weak latex cross-reactivity",
        "severity_bump": "caution",
    },

    # ------------------------------------------------------------------ #
    # Pollen-food syndrome (birch pollen primary)                        #
    # ------------------------------------------------------------------ #
    {
        "reaction_id": "birch_apple",
        "trigger": "apple",
        "primary_allergy": "birch_pollen",
        "confidence": 0.95,
        "category": "pollen_food_syndrome",
        "reason": "Apple shares the PR-10 Bet v 1 protein with birch pollen — oral allergy syndrome, rarely systemic.",
        "headline": "Apples commonly react if you have birch pollen allergy",
        "severity_bump": "caution",
    },
    {
        "reaction_id": "birch_hazelnut",
        "trigger": "hazelnut",
        "primary_allergy": "birch_pollen",
        "confidence": 0.9,
        "category": "pollen_food_syndrome",
        "reason": "Hazelnut contains a Bet v 1-homologous protein; oral symptoms are common, systemic reactions are possible.",
        "headline": "Hazelnuts cross-react strongly with birch pollen",
        "severity_bump": "caution",
    },
    {
        "reaction_id": "birch_carrot",
        "trigger": "carrot",
        "primary_allergy": "birch_pollen",
        "confidence": 0.8,
        "category": "pollen_food_syndrome",
        "reason": "Carrot shares PR-10 homologues with birch.",
        "headline": "Carrot is a birch cross-reactor (oral allergy)",
        "severity_bump": "caution",
    },
    {
        "reaction_id": "birch_celery",
        "trigger": "celery",
        "primary_allergy": "birch_pollen",
        "confidence": 0.85,
        "category": "pollen_food_syndrome",
        "reason": "Celery cross-reacts with birch (Bet v 1) and mugwort (Api g 1); celery allergy is often birch-linked.",
        "headline": "Celery is strongly birch-linked; separate celery allergy also exists",
        "severity_bump": "caution",
    },
    {
        "reaction_id": "birch_soy",
        "trigger": "soy",
        "primary_allergy": "birch_pollen",
        "confidence": 0.7,
        "category": "pollen_food_syndrome",
        "reason": "Soy contains Gly m 4, a Bet v 1 homologue; mostly mild oral symptoms but can rarely be systemic.",
        "headline": "Soy drinks can trigger oral allergy in birch-allergic people",
        "severity_bump": "caution",
    },
    {
        "reaction_id": "birch_pear",
        "trigger": "pear",
        "primary_allergy": "birch_pollen",
        "confidence": 0.8,
        "category": "pollen_food_syndrome",
        "reason": "Pear shares Bet v 1-like PR-10 proteins with birch.",
        "headline": "Pear reacts in many birch pollen allergies",
        "severity_bump": "caution",
    },
    {
        "reaction_id": "birch_plum",
        "trigger": "plum",
        "primary_allergy": "birch_pollen",
        "confidence": 0.7,
        "category": "pollen_food_syndrome",
        "reason": "Stone fruits share PR-10 allergens with birch.",
        "headline": "Stone fruits (plum, peach, cherry) often cross-react with birch",
        "severity_bump": "caution",
    },
    {
        "reaction_id": "birch_peach",
        "trigger": "peach",
        "primary_allergy": "birch_pollen",
        "confidence": 0.8,
        "category": "pollen_food_syndrome",
        "reason": "Peach is a classic birch cross-reactor (Pru p 1 / Pru p 3 combination).",
        "headline": "Peach is strongly associated with birch pollen allergy",
        "severity_bump": "caution",
    },

    # ------------------------------------------------------------------ #
    # Mugwort-spice / celery-spice syndrome                              #
    # ------------------------------------------------------------------ #
    {
        "reaction_id": "mugwort_celery_spice_birch",
        "trigger": "caraway",
        "primary_allergy": "mugwort_pollen",
        "confidence": 0.7,
        "category": "mugwort_celery_spice_syndrome",
        "reason": "Caraway (Apiaceae spice) shares allergens with mugwort pollen.",
        "headline": "Caraway can cross-react with mugwort pollen allergy",
        "severity_bump": "caution",
    },
    {
        "reaction_id": "mugwort_celery_spice_cumin",
        "trigger": "cumin",
        "primary_allergy": "mugwort_pollen",
        "confidence": 0.65,
        "category": "mugwort_celery_spice_syndrome",
        "reason": "Cumin is in the Apiaceae celery-mugwort-spice cross-reactivity cluster.",
        "headline": "Cumin belongs to the celery-mugwort-spice cluster",
        "severity_bump": "caution",
    },
    {
        "reaction_id": "mugwort_celery_spice_coriander",
        "trigger": "coriander",
        "primary_allergy": "mugwort_pollen",
        "confidence": 0.7,
        "category": "mugwort_celery_spice_syndrome",
        "reason": "Coriander shares profiling allergens with mugwort and birch.",
        "headline": "Coriander is a spice-pollen cross-reactor",
        "severity_bump": "caution",
    },
    {
        "reaction_id": "mugwort_mustard",
        "trigger": "mustard",
        "primary_allergy": "mugwort_pollen",
        "confidence": 0.6,
        "category": "mugwort_celery_spice_syndrome",
        "reason": "Mustard links into the celery-mugwort-spice syndrome; genuine mustard allergy is also reported.",
        "headline": "Mustard is associated with the mugwort-spice cluster",
        "severity_bump": "caution",
    },

    # ------------------------------------------------------------------ #
    # Beef-milk syndrome (pork-cat + beef-milk)                          #
    # ------------------------------------------------------------------ #
    {
        "reaction_id": "milk_beef",
        "trigger": "beef",
        "primary_allergy": "milk",
        "confidence": 0.55,
        "category": "beef_milk_syndrome",
        "reason": "A subset of milk-allergic children (serum albumin reactive) react to beef; heating reduces reactivity.",
        "headline": "Beef can cross-react in some milk-allergic individuals",
        "severity_bump": "caution",
    },
    {
        "reaction_id": "cat_pork",
        "trigger": "pork",
        "primary_allergy": "cat_dander",
        "confidence": 0.8,
        "category": "pork_cat_syndrome",
        "reason": "Pork-cat syndrome: sensitisation to cat serum albumin (Fel d 2) causes reactions to undercooked pork.",
        "headline": "Pork can trigger symptoms in cat-allergic (albumin-sensitised) people",
        "severity_bump": "caution_and_monitor",
    },

    # ------------------------------------------------------------------ #
    # Dust mite-shellfish cross ("mite-shrimp" homology)                 #
    # ------------------------------------------------------------------ #
    {
        "reaction_id": "dustmite_shellfish",
        "trigger": "shrimp",
        "primary_allergy": "dust_mite",
        "confidence": 0.6,
        "category": "mite_shellfish_tropomyosin",
        "reason": "Tropomyosin homology between dust mites and shellfish; some mite-sensitised patients react to shellfish, though it is not universal.",
        "headline": "Dust mite allergy is loosely linked to shellfish reactions",
        "severity_bump": "caution",
    },

    # ------------------------------------------------------------------ #
    # Legume cross-reactivity (peanut-lupin strongest)                   #
    # ------------------------------------------------------------------ #
    {
        "reaction_id": "peanut_lupin",
        "trigger": "lupin",
        "primary_allergy": "peanuts",
        "confidence": 0.75,
        "category": "legume_cross_reactivity",
        "reason": "Lupin shares storage protein epitopes with peanut; clinically meaningful cross-reaction for some patients — hence EU labelling.",
        "headline": "Lupin carries a real cross-reaction risk for peanut allergy",
        "severity_bump": "caution_and_monitor",
    },
    {
        "reaction_id": "peanut_soy",
        "trigger": "soy",
        "primary_allergy": "peanuts",
        "confidence": 0.45,
        "category": "legume_cross_reactivity",
        "reason": "In-vitro cross-reactivity between peanut and soy is frequent but clinical cross-reaction is uncommon.",
        "headline": "Peanut and soya show lab cross-reactivity but clinical reactions are rare",
        "severity_bump": "caution",
    },
    {
        "reaction_id": "peanut_chickpea",
        "trigger": "chickpea",
        "primary_allergy": "peanuts",
        "confidence": 0.4,
        "category": "legume_cross_reactivity",
        "reason": "Limited evidence of clinical cross-reaction between peanut and chickpea; more testing needed.",
        "headline": "Chickpea cross-reaction with peanut is possible but uncommon",
        "severity_bump": "caution",
    },

    # ------------------------------------------------------------------ #
    # Banana/melon family — ragweed linkage                              #
    # ------------------------------------------------------------------ #
    {
        "reaction_id": "ragweed_banana",
        "trigger": "banana",
        "primary_allergy": "ragweed_pollen",
        "confidence": 0.6,
        "category": "ragweed_food_syndrome",
        "reason": "Ragweed-pollen food syndrome classically pairs with banana and melons.",
        "headline": "Banana is linked to ragweed pollen allergy",
        "severity_bump": "caution",
    },
    {
        "reaction_id": "ragweed_melon",
        "trigger": "melon",
        "primary_allergy": "ragweed_pollen",
        "confidence": 0.65,
        "category": "ragweed_food_syndrome",
        "reason": "Cantaloupe/melons cross-react with ragweed pollen.",
        "headline": "Melons cross-react strongly with ragweed pollen allergy",
        "severity_bump": "caution",
    },
    {
        "reaction_id": "ragweed_cucumber",
        "trigger": "cucumber",
        "primary_allergy": "ragweed_pollen",
        "confidence": 0.5,
        "category": "ragweed_food_syndrome",
        "reason": "Cucumber is a weaker member of the ragweed-melon food cluster.",
        "headline": "Cucumber may cross-react with ragweed pollen",
        "severity_bump": "caution",
    },
    {
        "reaction_id": "ragweed_zucchini",
        "trigger": "zucchini",
        "primary_allergy": "ragweed_pollen",
        "confidence": 0.5,
        "category": "ragweed_food_syndrome",
        "reason": "Zucchini/courgette belongs to the ragweed-melon profile.",
        "headline": "Zucchini is part of the ragweed food cluster",
        "severity_bump": "caution",
    },

    # ------------------------------------------------------------------ #
    # Fish / shellfish and environmental overlaps                        #
    # ------------------------------------------------------------------ #
    {
        "reaction_id": "fish_shellfish_note",
        "trigger": "shellfish",
        "primary_allergy": "fish",
        "confidence": 0.35,
        "category": "fish_shellfish_distinct",
        "reason": "Fish and shellfish allergies are caused by DIFFERENT proteins (parvalbumin vs tropomyosin) — cross-reaction is rare.",
        "headline": "Fish and shellfish are usually separate allergies",
        "severity_bump": "none",
    },
    {
        "reaction_id": "carp_collagen_fish",
        "trigger": "fish",
        "primary_allergy": "fish",
        "confidence": 0.5,
        "category": "fish_parvalbumin_cross",
        "reason": "Parvalbumin is shared across many fish species — fish-allergic people often react to multiple fish; cross-contamination in processing is the bigger risk.",
        "headline": "Different fish species often share allergens",
        "severity_bump": "caution",
    },
]


def lookup_cross_reactivity(ingredient: str, primary_allergy: str) -> list[dict]:
    """Return all cross-reactivity rows matching ingredient + profile allergy."""
    i = ingredient.lower().strip()
    a = primary_allergy.lower().strip()
    return [r for r in CROSS_REACTIVITY_TABLE if r["trigger"] == i and r["primary_allergy"] == a]


def all_cross_reactors_for(primary_allergy: str) -> list[dict]:
    """All triggers relevant for a profile allergy — for proactive suggestions."""
    a = primary_allergy.lower().strip()
    return [r for r in CROSS_REACTIVITY_TABLE if r["primary_allergy"] == a]