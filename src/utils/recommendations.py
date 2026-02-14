"""Nutrition recommendations logic by LLM - uses AWS Bedrock in production, mock responses for local testing"""
import json
import boto3
from botocore.exceptions import ClientError

def generate_daily_recommendations(logs, profile):
    """Generate AI-powered personalized daily meal recommendations"""
    total_cal = sum(l['calories'] for l in logs)
    total_protein = sum(l['protein'] for l in logs)
    total_carbs = sum(l['carbs'] for l in logs)
    total_fats = sum(l['fats'] for l in logs)
    
    goal = profile.get('healthGoal', '')
    dietary = profile.get('dietary', [])
    
    prompt = f"""You are a nutrition expert. Based on today's intake, provide 3-4 meal recommendations and 2-3 tips.

    Today's Nutrition:
    - Calories: {total_cal} / 2000
    - Protein: {total_protein}g / 100g
    - Carbs: {total_carbs}g / 250g
    - Fats: {total_fats}g / 70g

    User Profile:
    - Health Goal: {goal or 'general health'}
    - Dietary Preferences: {', '.join(dietary) if dietary else 'none'}

    Provide response in this exact JSON format:
    {{
    "recommendations": [
        {{"type": "meal", "title": "Meal Name", "reason": "Why this meal", "calories": 400, "protein": 30}}
    ],
    "tips": [
        {{"type": "tip", "message": "Helpful tip with emoji"}}
    ]
    }}

    Provide 3-4 meals and 2-3 actionable tips. Keep it concise."""
        
    try:
        bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            })
        )
        
        result = json.loads(response['body'].read())
        content = result['content'][0]['text']
        
        # Parse JSON from response
        data = json.loads(content)
        return data['recommendations'] + data['tips']
        
    except (ClientError, json.JSONDecodeError, KeyError) as e:
        # Fallback recommendations for local testing
        recs = []
        
        if total_cal < 800:
            if 'vegan' in dietary or 'vegetarian' in dietary:
                recs.extend([{'type': 'meal', 'title': 'Vegetarian Buddha Bowl', 'reason': 'Plant-based protein & fiber', 'calories': 520, 'protein': 18},
                            {'type': 'meal', 'title': 'Quinoa Veggie Stir-Fry', 'reason': 'Complete protein source', 'calories': 450, 'protein': 16}])
            else:
                recs.extend([{'type': 'meal', 'title': 'Grilled Chicken Salad', 'reason': 'High protein, low carb', 'calories': 380, 'protein': 42},
                            {'type': 'meal', 'title': 'Salmon with Vegetables', 'reason': 'Omega-3 rich', 'calories': 420, 'protein': 38}])
        elif total_cal < 1200:
            recs.append({'type': 'meal', 'title': 'Greek Yogurt Parfait', 'reason': 'Protein-rich snack', 'calories': 280, 'protein': 20})
        
        if total_protein < 30:
            recs.append({'type': 'tip', 'message': '💪 Boost protein: Add eggs, Greek yogurt, or lean meat'})
        if total_fats < 20:
            recs.append({'type': 'tip', 'message': '🥑 Healthy fats: Include avocado, nuts, or olive oil'})
        
        recs.append({'type': 'tip', 'message': '💧 Stay hydrated throughout the day'})
        return recs