import sys
import logging
from data.client.openfoodfacts import get_product, OpenFoodFactsClient

logging.basicConfig(level=logging.DEBUG)

client = OpenFoodFactsClient(user_agent="AaharKavach-Hackathon - Web - Version 1.0")

try:
    record = client.get_product("5060337500982")
    print(f"Status: {record.off_status}")
    print(f"Verbose: {record.off_status_verbose}")
    print(f"Name: {record.product_name}")
    print(f"Ingredients: {record.ingredients_raw}")
except Exception as e:
    print(f"Error: {e}")
