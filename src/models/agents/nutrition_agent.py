import json
from strands import Agent, tool
from strands.models import BedrockModel

MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"
REGION = "ap-southeast-2"


def make_nutrition_agent(tool_handler, user_profile: dict):
    allergies = ", ".join(user_profile.get("allergies", [])) or "none"
    dietary = ", ".join(user_profile.get("dietary", [])) or "none"
    health_goal = user_profile.get("healthGoal", "maintain weight")

    @tool
    def get_nutrition_stats() -> str:
        """Get today's calories consumed, goal, and remaining budget."""
        return json.dumps(tool_handler("get_nutrition_stats", {}))

    @tool
    def log_nutrition(meal_type: str, name: str, calories: float,
                      protein: float = 0, carbs: float = 0, fats: float = 0) -> str:
        """Log a meal. meal_type must be breakfast, lunch, dinner, or snack."""
        return json.dumps(tool_handler("log_nutrition", {
            "meal_type": meal_type, "name": name, "calories": calories,
            "protein": protein, "carbs": carbs, "fats": fats
        }))

    return Agent(
        model=BedrockModel(model_id=MODEL_ID, region_name=REGION, max_tokens=1000, temperature=0.5),
        system_prompt=(
            "You are the MealBuddy Nutrition Tracker. You handle calorie/macro tracking and snack suggestions.\n"
            "Always call get_nutrition_stats before answering any calorie or remaining-budget question.\n"
            "Give precise answers using the returned calorie_goal and calories_remaining fields, e.g. 'You have X cal remaining (goal: Y, consumed: Z)'.\n"
            f"User profile — health goal: {health_goal}, dietary: {dietary}, allergies: {allergies}.\n"
            "Never suggest foods containing the user's allergens."
        ),
        tools=[get_nutrition_stats, log_nutrition],
    )
