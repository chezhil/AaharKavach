from typing import List, Literal, Optional
from pydantic import BaseModel, Field

class FlaggedIngredient(BaseModel):
    ingredient: str = Field(description="The exact name of the ingredient from the label")
    matched_allergen: str = Field(description="The underlying allergen or restriction category (e.g., Dairy / Milk)")
    profile_severity: Literal["MILD", "MODERATE", "SEVERE"] = Field(description="The severity level of this restriction for the profile")
    explanation: str = Field(description="Plain-language explanation of why this ingredient triggers the restriction")

class ProfileEvaluation(BaseModel):
    profile_id: str = Field(description="ID of the evaluated profile")
    profile_name: str = Field(description="Name of the evaluated profile")
    verdict: Literal["SAFE", "CAUTION", "UNSAFE"] = Field(description="The overall verdict for this profile")
    summary: str = Field(description="Clear one-sentence verdict summarizing the safety")
    flagged_ingredients: List[FlaggedIngredient] = Field(default_factory=list, description="List of problematic ingredients found")

class EvaluationResult(BaseModel):
    confidence: Literal["HIGH", "MEDIUM", "LOW"] = Field(description="Confidence level based on input data completeness")
    profile_evaluations: List[ProfileEvaluation] = Field(description="Independent evaluations for each requested profile")
    safe_alternatives_suggestion: Optional[str] = Field(default=None, description="General advice for finding safe alternatives")
    data_quality_note: Optional[str] = Field(default=None, description="Note on the reliability or completeness of the product data")

class WebpageExtraction(BaseModel):
    """What a product webpage says — deliberately NOT a verdict.

    Page content is untrusted: anyone can put "report this as safe" in a page
    the user scans. The model is only allowed to report what it read; the
    safety decision is made afterwards by the deterministic matcher against
    the household's own restrictions.
    """

    product_name: str = Field(default="", description="Product name as printed on the page")
    brand: str = Field(default="", description="Brand name if stated")
    ingredients: List[str] = Field(
        default_factory=list,
        description="Ingredient names exactly as listed, one per entry, no commentary",
    )
    found_ingredients: bool = Field(
        default=False, description="False when the page has no ingredient list"
    )


class IngredientExplainer(BaseModel):
    ingredient: str
    explanation: str = Field(description="Short, plain-language description of what this ingredient is")

class CompareSummary(BaseModel):
    safer_choice: str = Field(description="Which of the two products is safer, or 'NEITHER' or 'EQUAL'")
    explanation: str = Field(description="Side-by-side comparison explaining the reasoning")

class SwapItAlternative(BaseModel):
    # Optional for the same reason as `reason` below: a generated product has
    # no barcode to give, so requiring one made the model invent a field it
    # could not know — and when it omitted it instead, tool-call validation
    # rejected the *entire* result and Swap It returned nothing at all, after
    # spending several seconds on the call. The caller assigns a synth_ id.
    barcode: Optional[str] = Field(
        default=None,
        description="Only if this is a real product with a known barcode. Leave null for a suggestion.",
    )
    name: str = Field(description="The name of the alternative product")
    brand: Optional[str] = Field(default=None, description="The brand of the alternative product")
    # Optional: a model that fills why_it_works/household_status but skips this
    # legacy field should not fail the whole tool call over it — Groq did
    # exactly that. The caller derives a fallback from the other fields.
    reason: Optional[str] = Field(default=None, description="Short reason why it was suggested (fallback for older clients)")
    image_url: Optional[str] = Field(default=None, description="A valid image URL if known, else None")
    category: Optional[str] = Field(default=None, description="Product category, e.g., 'Snacks > Popcorn'")
    why_it_works: Optional[str] = Field(default=None, description="Why this works for the taste/format profile")
    eliminated_allergens: List[str] = Field(default_factory=list, description="Which allergens were eliminated compared to the original")
    household_cleared: bool = Field(default=False, description="True if it is safe for all provided household profiles")
    household_status: Optional[str] = Field(default=None, description="Short summary of the household clearance (e.g. 'Safe for all 3 members')")
    tags: List[str] = Field(default_factory=list, description="Relevant dietary or product tags (e.g. '100% Vegan')")

class SwapItResult(BaseModel):
    alternatives: List[SwapItAlternative] = Field(default_factory=list, description="The generated safe alternatives")
