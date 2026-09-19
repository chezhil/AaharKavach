def calculate_daily_limits(profile) -> dict:
    """
    Calculates dynamic daily nutritional limits using the Mifflin-St Jeor equation.
    Expects profile to have: age, weight_kg, height_cm, gender
    """
    age = profile.age if profile.age is not None else 30
    weight_kg = profile.weight_kg if profile.weight_kg is not None else 70.0
    height_cm = profile.height_cm if profile.height_cm is not None else 170.0
    gender = (profile.gender or 'male').lower()

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
