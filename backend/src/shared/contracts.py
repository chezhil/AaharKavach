from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field, conlist

class NutrientMetric(BaseModel):
    actual_value: float
    daily_limit: float

class ProfileEvaluation(BaseModel):
    profile_id: str
    profile_name: str
    verdict: Literal["SAFE", "CAUTION", "UNSAFE"]
    summary: str
    flagged_ingredients: List[dict]
    nutrition: Dict[str, NutrientMetric] = Field(default_factory=dict)

class EvaluationResponse(BaseModel):
    confidence: str
    profile_evaluations: List[ProfileEvaluation]
    safe_alternatives_suggestion: Optional[str] = None
    data_quality_note: Optional[str] = None

class UserProfile(BaseModel):
    householdId: str
    profileId: str
    name: str
    owner: str
    allergies: List[str] = Field(default_factory=list)
    
    # Physical Attributes
    age: Optional[int] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    gender: Optional[Literal["male", "female", "other"]] = None
    
    # Tracked Nutrients
    tracked_nutrients: conlist(str, min_length=6, max_length=6) = Field(
        default=["Energy_kcal", "Protein", "Carbs", "Sugars", "Fat", "Salt"]
    )
