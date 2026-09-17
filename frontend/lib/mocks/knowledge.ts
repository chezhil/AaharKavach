/**
 * A hand-cut slice of what Role 2 will serve from OpenSearch.
 * Only here so the frontend can demo without the backend — when Role 2's
 * index is live this file stops being used, not the components.
 */

/** allergen -> the names it hides behind on an Indian/global label */
export const ALLERGEN_SYNONYMS: Record<string, string[]> = {
  "Dairy / Milk": [
    "milk", "milk solids", "milk powder", "skimmed milk", "toned milk",
    "casein", "sodium caseinate", "caseinate", "whey", "whey protein",
    "lactose", "butter", "butterfat", "ghee", "paneer", "khoya", "curd",
    "yoghurt", "cream", "cheese",
  ],
  "Gluten / Wheat": [
    "wheat", "wheat flour", "maida", "atta", "refined flour", "semolina",
    "suji", "rava", "barley", "rye", "malt", "malt extract", "malted barley",
    "triticum", "seitan", "couscous",
  ],
  Peanuts: ["peanut", "peanuts", "groundnut", "groundnuts", "arachis oil", "peanut butter"],
  "Tree Nuts": [
    "almond", "badam", "cashew", "kaju", "walnut", "akhrot", "hazelnut",
    "pistachio", "pista", "pecan", "macadamia",
  ],
  Soy: ["soy", "soya", "soybean", "soy lecithin", "soya lecithin", "e322", "tofu", "edamame"],
  Egg: ["egg", "eggs", "egg white", "albumen", "ovalbumin", "egg powder", "mayonnaise"],
  Sesame: ["sesame", "til", "tahini", "gingelly"],
  "Fish / Shellfish": ["fish", "prawn", "shrimp", "crab", "anchovy", "oyster"],
  "Insect-derived (Carmine)": ["carmine", "cochineal", "e120", "carminic acid"],
  Mustard: ["mustard", "sarson", "rai"],
  Gelatin: ["gelatin", "gelatine"],
};

/**
 * Restriction label -> allergen keys above.
 * Lets a user type "no dairy" / "Lactose" / "Milk" and still hit the same rules.
 */
export const RESTRICTION_ALIASES: Record<string, string[]> = {
  dairy: ["Dairy / Milk"],
  milk: ["Dairy / Milk"],
  lactose: ["Dairy / Milk"],
  "lactose intolerant": ["Dairy / Milk"],
  gluten: ["Gluten / Wheat"],
  wheat: ["Gluten / Wheat"],
  celiac: ["Gluten / Wheat"],
  coeliac: ["Gluten / Wheat"],
  peanut: ["Peanuts"],
  peanuts: ["Peanuts"],
  groundnut: ["Peanuts"],
  "tree nuts": ["Tree Nuts"],
  nuts: ["Tree Nuts", "Peanuts"],
  nut: ["Tree Nuts", "Peanuts"],
  soy: ["Soy"],
  soya: ["Soy"],
  egg: ["Egg"],
  eggs: ["Egg"],
  sesame: ["Sesame"],
  fish: ["Fish / Shellfish"],
  shellfish: ["Fish / Shellfish"],
  seafood: ["Fish / Shellfish"],
  vegetarian: ["Fish / Shellfish", "Gelatin", "Insect-derived (Carmine)"],
  vegan: ["Dairy / Milk", "Egg", "Fish / Shellfish", "Gelatin", "Insect-derived (Carmine)"],
  jain: ["Fish / Shellfish", "Egg", "Gelatin"],
  mustard: ["Mustard"],
  carmine: ["Insect-derived (Carmine)"],
};

/** allergen -> ingredients that can trigger it by cross-reaction, not by being it */
export const CROSS_REACTIVITY: Record<string, { triggers: string[]; note: string }> = {
  Latex: {
    triggers: ["banana", "avocado", "kiwi", "chestnut", "papaya"],
    note: "Latex-fruit syndrome — these share proteins with natural rubber latex.",
  },
  "Birch Pollen": {
    triggers: ["apple", "hazelnut", "carrot", "celery", "peach"],
    note: "Oral allergy syndrome — birch pollen proteins resemble these fruits.",
  },
  Peanuts: {
    triggers: ["lupin", "lupine"],
    note: "Lupin is a legume like peanut and cross-reacts in some peanut allergies.",
  },
  "Fish / Shellfish": {
    triggers: ["dust mite", "glucosamine"],
    note: "Shellfish tropomyosin cross-reacts with mite and some supplement sources.",
  },
};

/** plain-language "what is this", for the tap-to-explain chips */
export const INGREDIENT_EXPLAINERS: Record<string, string> = {
  e322: "Lecithin — an emulsifier that stops oil and water separating. Usually made from soy, sometimes sunflower.",
  e120: "Carmine — a red colour made from cochineal insects. Not vegetarian or vegan.",
  e471: "Mono- and diglycerides of fatty acids — an emulsifier. Can be plant or animal derived; labels rarely say which.",
  e330: "Citric acid — a common sour-tasting preservative, usually made by fermenting sugar.",
  e500: "Sodium bicarbonate — ordinary baking soda, used as a raising agent.",
  e503: "Ammonium bicarbonate — another raising agent, used in crisp biscuits.",
  e627: "Disodium guanylate — a flavour enhancer, almost always paired with MSG.",
  e631: "Disodium inosinate — a savoury flavour enhancer; can be fish or meat derived.",
  e635: "Disodium ribonucleotides — a flavour booster blending E627 and E631.",
  e150d: "Caramel colour (sulphite ammonia process) — the brown colour in colas and sauces.",
  "sodium caseinate": "A milk protein pulled out of casein. It is dairy, even when the label says 'non-dairy creamer'.",
  "milk solids": "What is left when water is removed from milk — full dairy protein and lactose.",
  whey: "The watery part of milk left over from cheese-making, dried into a powder. Dairy.",
  ghee: "Clarified butter. Dairy, though most milk sugars are cooked out.",
  maida: "Refined wheat flour. Contains gluten.",
  "palm oil": "A cheap vegetable fat from oil-palm fruit. Not an allergen, but high in saturated fat.",
  "invert sugar syrup": "Sugar split into glucose and fructose so it stays soft and does not crystallise.",
  lecithin: "An emulsifier that keeps fats and water mixed. Soy is the usual source.",
  "cocoa butter": "The fat pressed from cocoa beans. Despite the name, it contains no dairy.",
  oats: "A cereal grain. Naturally gluten-free, but often milled alongside wheat.",
  "rapeseed oil": "A mild cooking oil, also sold as canola.",
  "calcium carbonate": "Chalk, added to fortify a food with calcium.",
  salt: "Sodium chloride — seasoning and preservative.",
  sugar: "Refined sucrose, usually from sugarcane.",
};
