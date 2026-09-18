import json
import os
from typing import List, Dict, Any
from strands import Agent, tool
from .models import EvaluationResult, IngredientExplainer, CompareSummary
from .prompts import SYSTEM_PROMPT_EVALUATOR, SYSTEM_PROMPT_EXPLAINER, SYSTEM_PROMPT_COMPARE
from .tools import lookup_ingredient_details, check_cross_reactivity

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

def evaluate_product(product_data: Dict[str, Any], profiles: List[Dict[str, Any]]) -> EvaluationResult:
    """
    Core entrypoint for the Strands AI Agent.
    Evaluates a product against multiple user profiles.
    """
    
    # 2. Setup the Evaluator Agent
    evaluator_agent = Agent(
        system_prompt=SYSTEM_PROMPT_EVALUATOR,
        tools=[tool_lookup_ingredient_details, tool_check_cross_reactivity],
        model=BEDROCK_MODEL
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
    result = evaluator_agent(
        prompt,
        structured_output_model=EvaluationResult
    )
    
    return result.structured_output

def evaluate_webpage_text(webpage_text: str, profiles: List[Dict[str, Any]]) -> EvaluationResult:
    """
    Evaluates a product by extracting ingredients from webpage text.
    """
    evaluator_agent = Agent(
        system_prompt=SYSTEM_PROMPT_EVALUATOR + "\n\nExtract the product name and ingredients list from this webpage text. Cross-check against the household restrictions and return the standard AaharKavach safety JSON.",
        tools=[tool_lookup_ingredient_details, tool_check_cross_reactivity],
        model=BEDROCK_MODEL
    )
    
    prompt = f"""
    Webpage Text (first 4000 chars):
    {webpage_text}
    
    User Profiles to Evaluate Against:
    {json.dumps(profiles, indent=2)}
    
    Extract the ingredients, evaluate the product, and provide the structured verdict.
    """
    
    result = evaluator_agent(
        prompt,
        structured_output_model=EvaluationResult
    )
    
    return result.structured_output

def explain_ingredient(ingredient: str) -> IngredientExplainer:
    """
    Provides a short plain-language explanation of an ingredient.
    """
    explainer_agent = Agent(
        system_prompt=SYSTEM_PROMPT_EXPLAINER,
        tools=[tool_lookup_ingredient_details]
    )
    
    prompt = f"Explain the ingredient: {ingredient}"
    return explainer_agent(prompt, structured_output_model=IngredientExplainer).structured_output

def compare_products(product1_data: Dict[str, Any], product2_data: Dict[str, Any], profiles: List[Dict[str, Any]]) -> CompareSummary:
    """
    Compares two products and evaluates which is safer for the given profiles.
    """
    # Evaluate both first
    eval1 = evaluate_product(product1_data, profiles)
    eval2 = evaluate_product(product2_data, profiles)
    
    compare_agent = Agent(
        system_prompt=SYSTEM_PROMPT_COMPARE
    )
    
    prompt = f"""
    Product 1 Evaluation:
    {eval1.model_dump_json(indent=2)}
    
    Product 2 Evaluation:
    {eval2.model_dump_json(indent=2)}
    
    Write a brief side-by-side summary highlighting which is the safer choice and why.
    """
    return compare_agent(prompt, structured_output_model=CompareSummary).structured_output
