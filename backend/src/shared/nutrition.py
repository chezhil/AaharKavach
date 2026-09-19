def calculate_daily_limits(profile: dict) -> dict:
    """
    Calculates dynamic daily nutritional limits using the Mifflin-St Jeor equation.
    Expects profile dict to have: age, weight_kg, height_cm, gender
    """
    age = profile.get('age', 30)
    weight_kg = profile.get('weight_kg', 70.0)
    height_cm = profile.get('height_cm', 170.0)
    gender = profile.get('gender', 'male').lower()

    # Base BMR calculation
    bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age)
    
    if gender == 'female':
        bmr -= 161
    else:
        # Default to male / other
        bmr += 5

    # Total Daily Energy Expenditure (baseline activity 1.2)
    tdee = bmr * 1.2

    return {
        "Energy_kcal": round(tdee, 1),
        "Carbs": round((tdee * 0.50) / 4, 1),      # 50% of TDEE / 4 kcal per gram
        "Protein": round(weight_kg * 1.0, 1),      # 1g per kg of body weight
        "Fat": round((tdee * 0.30) / 9, 1),        # 30% of TDEE / 9 kcal per gram
        "SatFat": round((tdee * 0.10) / 9, 1),     # Max 10% of TDEE / 9 kcal per gram
        "Sugars": round((tdee * 0.10) / 4, 1),     # Max 10% of TDEE / 4 kcal per gram
        "Salt": 2000.0,                            # Fixed 2000mg sodium
        "Fiber": 30.0,                             # Fixed 30g fiber
        "TransFat": 2.0                            # Strict minimal limit
    }
