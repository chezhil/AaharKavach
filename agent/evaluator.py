import json
import os
from typing import List, Dict, Any
from strands import Agent, tool
from .models import EvaluationResult, IngredientExplainer, CompareSummary
from .prompts import SYSTEM_PROMPT_EVALUATOR, SYSTEM_PROMPT_EXPLAINER, SYSTEM_PROMPT_COMPARE
from .tools import lookup_ingredient_details, check_cross_reactivity, get_product_data

# Bedrock model ids are account- and region-specific and the model must be
# enabled in the console first, so this is configuration, not a constant.
BEDROCK_MODEL = os.environ.get("AAHAR_BEDROCK_MODEL", "")

# Convert mock tool functions to strands tools
@tool
def tool_lookup_ingredient_details(ingredient_name: str) -> str:
    """
    Look up an ingredient in the OpenSearch Knowledge Base to retrieve synonyms, E-number mappings, and base allergens.
    """
    return json.dumps(lookup_ingredient_details(ingredient_name))

@tool
def tool_check_cross_reactivity(allergen_name: str) -> str:
    """
    Check for known cross-reactivities for a given allergen.
    """
    return json.dumps(check_cross_reactivity(allergen_name))

def evaluate_product(barcode: str, profiles: List[Dict[str, Any]]) -> EvaluationResult:
    """
    Core entrypoint for the Strands AI Agent.
    Evaluates a product against multiple user profiles.
    """
    # 1. Fetch raw product data (Role 2)
    product_data = get_product_data(barcode)
    
    # 2. Setup the Evaluator Agent
    evaluator_agent = Agent(
        system_prompt=SYSTEM_PROMPT_EVALUATOR,
        tools=[tool_lookup_ingredient_details, tool_check_cross_reactivity],
        model=BEDROCK_MODEL,
        response_schema=EvaluationResult
    )
    
    # 3. Construct the prompt
    prompt = f"""
    Product Data:
    {json.dumps(product_data, indent=2)}
    
    User Profiles to Evaluate Against:
    {json.dumps(profiles, indent=2)}
    
    Evaluate the product and provide the structured verdict.
    """
    
    # 4. Execute the agent
    result = evaluator_agent(prompt)
    
    # Depending on SDK version, result might be parsed automatically via response_schema
    return result

def explain_ingredient(ingredient: str) -> IngredientExplainer:
    """
    Provides a short plain-language explanation of an ingredient.
    """
    explainer_agent = Agent(
        system_prompt=SYSTEM_PROMPT_EXPLAINER,
        tools=[tool_lookup_ingredient_details],
        response_schema=IngredientExplainer
    )
    
    prompt = f"Explain the ingredient: {ingredient}"
    return explainer_agent(prompt)

def compare_products(barcode1: str, barcode2: str, profiles: List[Dict[str, Any]]) -> CompareSummary:
    """
    Compares two products and evaluates which is safer for the given profiles.
    """
    # Evaluate both first
    eval1 = evaluate_product(barcode1, profiles)
    eval2 = evaluate_product(barcode2, profiles)
    
    compare_agent = Agent(
        system_prompt=SYSTEM_PROMPT_COMPARE,
        response_schema=CompareSummary
    )
    
    prompt = f"""
    Product 1 Evaluation:
    {eval1.json(indent=2)}
    
    Product 2 Evaluation:
    {eval2.json(indent=2)}
    
    Write a brief side-by-side summary highlighting which is the safer choice and why.
    """
    return compare_agent(prompt)
