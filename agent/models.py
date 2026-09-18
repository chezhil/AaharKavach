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

class IngredientExplainer(BaseModel):
    ingredient: str
    explanation: str = Field(description="Short, plain-language description of what this ingredient is")

class CompareSummary(BaseModel):
    safer_choice: str = Field(description="Which of the two products is safer, or 'NEITHER' or 'EQUAL'")
    explanation: str = Field(description="Side-by-side comparison explaining the reasoning")
