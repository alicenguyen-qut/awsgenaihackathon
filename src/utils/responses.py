"""Mock responses for local mode"""

def get_mock_chat_response(query):
    """Generate mock chat response based on query"""
    query_lower = query.lower()
    
    if 'plan my week' in query_lower or 'weekly meal plan' in query_lower:
        return """Here's your weekly meal plan:

• Grilled Chicken Salad - Mediterranean-style with fresh vegetables (380 cal)
• Salmon with Roasted Vegetables - Omega-3 rich with broccoli (420 cal)
• Vegetarian Buddha Bowl - Quinoa, chickpeas, sweet potato (520 cal)
• Pasta Primavera - Whole wheat pasta with seasonal vegetables (450 cal)
• Chicken Stir Fry - Asian-style with brown rice (410 cal)
• Baked Cod with Asparagus - Light and healthy (350 cal)
• Veggie Tacos - Black beans, avocado, salsa (380 cal)

All meals are balanced and nutritious!"""
    
    elif 'vegan' in query_lower:
        return """🌱 Vegetarian Buddha Bowl - A colorful bowl with quinoa, chickpeas, sweet potato, and tahini dressing. High in fiber and plant-based protein (520 cal).

Ingredients: quinoa, chickpeas, sweet potato, kale, tahini, lemon"""
    
    elif 'protein' in query_lower or 'muscle' in query_lower:
        return """💪 Grilled Chicken Salad - Mediterranean-style with fresh vegetables. Perfect for muscle growth (380 cal, 42g protein).

🐟 Salmon with Roasted Vegetables - Rich in omega-3 and protein (420 cal, 38g protein)."""
    
    elif 'breakfast' in query_lower:
        return """⏰ Quick Protein Oatmeal - Steel-cut oats with banana, almonds, and protein powder (350 cal, 20g protein)

🥚 Veggie Egg Scramble - Eggs with spinach, tomatoes, and feta (280 cal, 18g protein)"""
    
    else:
        return """Here are some recipe suggestions:

• Grilled Chicken Salad - Mediterranean-style with fresh vegetables (380 cal)
• Vegetarian Buddha Bowl - Quinoa, chickpeas, sweet potato (520 cal)  
• Salmon with Roasted Vegetables - Omega-3 rich (420 cal)

All meals are balanced and nutritious!"""
