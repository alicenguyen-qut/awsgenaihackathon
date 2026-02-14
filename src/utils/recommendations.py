"""Nutrition recommendations logic"""

def generate_daily_recommendations(logs, profile):
    """Generate personalized daily meal recommendations"""
    total_cal = sum(l['calories'] for l in logs)
    total_protein = sum(l['protein'] for l in logs)
    total_carbs = sum(l['carbs'] for l in logs)
    total_fats = sum(l['fats'] for l in logs)
    
    goal = profile.get('healthGoal', '')
    dietary = profile.get('dietary', [])
    
    recommendations = []
    tips = []
    
    # Calorie-based recommendations
    if total_cal < 800:
        if 'vegan' in dietary or 'vegetarian' in dietary:
            recommendations.append({'type': 'meal', 'title': 'Vegetarian Buddha Bowl', 'reason': 'Plant-based protein & fiber', 'calories': 520, 'protein': 18})
            recommendations.append({'type': 'meal', 'title': 'Quinoa Veggie Stir-Fry', 'reason': 'Complete protein source', 'calories': 450, 'protein': 16})
        else:
            recommendations.append({'type': 'meal', 'title': 'Grilled Chicken Salad', 'reason': 'High protein, low carb', 'calories': 380, 'protein': 42})
            recommendations.append({'type': 'meal', 'title': 'Salmon with Vegetables', 'reason': 'Omega-3 rich', 'calories': 420, 'protein': 38})
    elif total_cal < 1200:
        recommendations.append({'type': 'meal', 'title': 'Greek Yogurt Parfait', 'reason': 'Protein-rich snack', 'calories': 280, 'protein': 20})
    elif total_cal > 2000:
        tips.append('You\'ve reached your calorie goal! Consider light snacks or herbal tea.')
    
    # Protein recommendations
    if total_protein < 30:
        tips.append('💪 Boost protein: Add eggs, Greek yogurt, or lean meat to your next meal')
        if 'vegan' in dietary:
            recommendations.append({'type': 'meal', 'title': 'Tofu Scramble', 'reason': 'Plant-based protein', 'calories': 320, 'protein': 24})
    elif total_protein < 60:
        tips.append('Good protein intake! Aim for 20-30g more for optimal muscle maintenance')
    
    # Carb recommendations
    if total_carbs < 50 and goal == 'energy-boost':
        tips.append('🍞 Low on carbs: Add whole grains or fruits for sustained energy')
    
    # Fat recommendations
    if total_fats < 20:
        tips.append('🥑 Healthy fats: Include avocado, nuts, or olive oil for nutrient absorption')
    
    # Goal-specific recommendations
    if goal == 'weight-loss' and total_cal < 1500:
        recommendations.append({'type': 'meal', 'title': 'Zucchini Noodles with Chicken', 'reason': 'Low-calorie, high-volume', 'calories': 340, 'protein': 35})
    elif goal == 'muscle-gain' and total_protein < 100:
        recommendations.append({'type': 'meal', 'title': 'Protein Power Bowl', 'reason': 'High protein for muscle growth', 'calories': 580, 'protein': 48})
    elif goal == 'heart-health':
        recommendations.append({'type': 'meal', 'title': 'Mediterranean Salmon', 'reason': 'Heart-healthy omega-3s', 'calories': 420, 'protein': 38})
    
    # Hydration reminder
    if len(logs) > 0:
        tips.append('💧 Stay hydrated: Drink 8 glasses of water throughout the day')
    
    # Combine tips into recommendations
    for tip in tips:
        recommendations.append({'type': 'tip', 'message': tip})
    
    return recommendations
