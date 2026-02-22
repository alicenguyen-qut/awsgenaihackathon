import json
from strands import Agent, tool
from strands.models import BedrockModel

MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"
REGION = "ap-southeast-2"


def make_planner_agent(tool_handler, meal_plan: dict, callback_handler=None):
    @tool
    def search_recipes(query: str, top_k: int = 5) -> str:
        """Search for recipes matching a query. Use this before planning meals."""
        return json.dumps(tool_handler("search_recipes", {"query": query, "top_k": top_k}))

    @tool
    def add_to_meal_plan(day: str, meal_name: str) -> str:
        """Add a meal to the weekly plan for a specific day (Monday-Sunday)."""
        return json.dumps(tool_handler("add_to_meal_plan", {"day": day, "meal_name": meal_name}))

    @tool
    def add_to_shopping_list(items: list) -> str:
        """Add ingredients to the shopping list."""
        return json.dumps(tool_handler("add_to_shopping_list", {"items": items}))

    @tool
    def add_to_favorites(recipe_name: str, recipe_content: str = "") -> str:
        """Bookmark a recipe to the user's favourites."""
        return json.dumps(tool_handler("add_to_favorites", {"recipe_name": recipe_name, "recipe_content": recipe_content}))

    meal_plan_text = "\n".join(f"- {d}: {m}" for d, m in meal_plan.items() if m) or "None yet"

    kwargs = dict(
        model=BedrockModel(model_id=MODEL_ID, region_name=REGION, temperature=0.7),
        system_prompt=(
            "You are the MealBuddy Planner. You handle meal planning, shopping lists, and favourites.\n"
            "Only call tools when the user explicitly asks to ADD a meal, PLAN a week, create a SHOPPING LIST, or SAVE to favourites.\n"
            "If the user is asking to SEE or GET a recipe (e.g. 'give me the recipe', 'show me the recipe'), "
            "respond with the full recipe details from the context provided — do NOT call add_to_meal_plan.\n"
            "When planning a week, first call search_recipes to find suitable meals, then call add_to_meal_plan exactly 7 times — Monday through Sunday.\n"
            "When generating a shopping list, derive ingredients from the most recently discussed recipe or meal in the conversation context. "
            "If a specific recipe was just discussed, use its ingredients. Only fall back to the current meal plan if no recent recipe is mentioned.\n"
            "Always respect the user's dietary restrictions and allergies.\n"
            f"Current meal plan:\n{meal_plan_text}"
        ),
        tools=[search_recipes, add_to_meal_plan, add_to_shopping_list, add_to_favorites],
    )
    if callback_handler is not None:
        kwargs['callback_handler'] = callback_handler
    return Agent(**kwargs)
