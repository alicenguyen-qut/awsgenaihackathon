import boto3
import json
import re
import numpy as np
import time
from typing import List, Dict, Any, Optional

from strands import Agent, tool
from strands.models import BedrockModel


class BedrockRAG:
    def __init__(self, recipes_bucket=None):
        self.s3 = boto3.client('s3', region_name='ap-southeast-2')
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name='ap-southeast-2')
        self.recipes_bucket = recipes_bucket
        self.embeddings_cache = {}
        self.recipes_cache = None

    # ── S3 / Embedding helpers  ────────────────────────────────

    def load_recipes_from_s3(self) -> List[Dict]:
        if self.recipes_cache:
            return self.recipes_cache
        if not self.recipes_bucket:
            return []
        try:
            response = self.s3.get_object(Bucket=self.recipes_bucket, Key='embeddings/recipe_embeddings.json')
            data = json.loads(response['Body'].read())
            recipes = []
            for item in data:
                clean_name = re.sub(r'^recipe_\d+_', '', item['recipe_id'].replace('.txt', '')).replace('_', ' ').title()
                recipes.append({'name': clean_name, 'description': item['text'], 'tags': [], 'calories': 0})
            self.recipes_cache = recipes
            print(f"✅ Loaded {len(recipes)} recipes from S3")
            return recipes
        except Exception as e:
            print(f"Error loading recipes from S3: {e}")
            return []

    def get_embedding(self, text: str) -> List[float]:
        try:
            time.sleep(0.5)
            response = self.bedrock_runtime.invoke_model(
                modelId='amazon.titan-embed-text-v2:0',
                body=json.dumps({"inputText": text, "dimensions": 1024, "normalize": True})
            )
            return json.loads(response['body'].read())['embedding']
        except Exception as e:
            print(f"Embedding error: {e}")
            return [0.0] * 1024

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        v1, v2 = np.array(vec1), np.array(vec2)
        return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))

    def search_recipes(self, query: str, recipes: List[Dict], top_k: int = 5) -> List[Dict]:
        try:
            query_emb = self.get_embedding(query)
            results = []
            for recipe in recipes:
                key = f"{recipe.get('name','')} {recipe.get('description','')} {' '.join(recipe.get('tags',[]))}"
                if key not in self.embeddings_cache:
                    self.embeddings_cache[key] = self.get_embedding(key)
                results.append({'recipe': recipe, 'similarity': self.cosine_similarity(query_emb, self.embeddings_cache[key])})
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return [r['recipe'] for r in results[:top_k]]
        except Exception as e:
            print(f"Search error: {e}")
            q = query.lower()
            matches = [r for r in recipes if any(w in r.get('name','').lower() or w in r.get('description','').lower() for w in q.split())]
            return matches[:top_k] if matches else recipes[:top_k]

    def embed_and_store_file(self, text: str, user_id: str, file_id: str, bucket: str) -> bool:
        try:
            chunk_size, overlap = 500, 50
            chunks = [text[i:i+chunk_size].strip() for i in range(0, len(text), chunk_size - overlap) if text[i:i+chunk_size].strip()]
            embeddings = [{'text': c, 'embedding': self.get_embedding(c), 'file_id': file_id} for c in chunks]
            key = f'uploads/{user_id}_embeddings.json'
            try:
                existing = json.loads(self.s3.get_object(Bucket=bucket, Key=key)['Body'].read())
            except Exception:
                existing = []
            existing = [e for e in existing if e.get('file_id') != file_id]
            existing.extend(embeddings)
            self.s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(existing), ContentType='application/json')
            return True
        except Exception as e:
            print(f"embed_and_store_file error: {e}")
            return False

    def search_user_uploads(self, query: str, user_id: str, bucket: str, top_k: int = 3) -> List[str]:
        try:
            embeddings = json.loads(self.s3.get_object(Bucket=bucket, Key=f'uploads/{user_id}_embeddings.json')['Body'].read())
            if not embeddings:
                return []
            q_emb = self.get_embedding(query)
            scored = sorted([(self.cosine_similarity(q_emb, e['embedding']), e['text']) for e in embeddings], reverse=True)
            return [t for _, t in scored[:top_k]]
        except Exception:
            return []

    # ── Strands Agent entry point ──────────────────────────────────────────

    def chat_with_rag(self, query: str, recipes: List[Dict], user_profile: Dict = None,
                      tool_handler: Optional[Any] = None, chat_history: List[Dict] = None,
                      user_id: str = None, uploads_bucket: str = None) -> Dict:
        """Main RAG pipeline — now powered by Strands Agent."""

        # Build RAG context
        relevant = self.search_recipes(query, recipes, top_k=5) if recipes else []
        context = "\n\n".join([
            f"Recipe: {r.get('name','Unknown')}\nDescription: {r.get('description','')}\n"
            f"Tags: {', '.join(r.get('tags',[]))}\nCalories: {r.get('calories','Unknown')}"
            for r in relevant
        ])
        if user_id and uploads_bucket:
            chunks = self.search_user_uploads(query, user_id, uploads_bucket)
            if chunks:
                context += "\n\nUser Uploaded Documents:\n" + "\n---\n".join(chunks)

        # Build system prompt
        profile_lines = ""
        if user_profile:
            if user_profile.get('dietary'):
                profile_lines += f"\nUser dietary preferences: {', '.join(user_profile['dietary'])}"
            if user_profile.get('healthGoal'):
                profile_lines += f"\nUser health goal: {user_profile['healthGoal']}"
            if user_profile.get('allergies'):
                profile_lines += f"\nUser allergies: {', '.join(user_profile['allergies'])}"

        system_prompt = (
            "You are MealBuddy, a friendly AI meal planning assistant.\n\n"
            "TOOL USE RULES:\n"
            "- Only call tools when the user explicitly asks to save, add, plan, or log something.\n"
            "- If the user asks to SEE, SHOW, FIND, or GET recipes — just answer with text, do NOT call any tools.\n"
            "- When planning a week, call add_to_meal_plan once per day (Monday-Sunday) only if the user asks to save/add to planner.\n"
            "- Never reference recipe numbers. Use only the recipe's actual name.\n"
            "- If recipe context is limited, use your own culinary knowledge to give complete recipes with ingredients and steps.\n"
            "- After calling tools, briefly confirm what was done."
            + profile_lines
        )

        # Capture tool calls for the frontend
        tool_calls_log: List[Dict] = []

        # Build Strands tools that delegate to the existing tool_handler
        def make_tool(name: str, description: str, fn):
            fn.__name__ = name
            fn.__doc__ = description
            return tool(fn)

        @tool
        def search_recipes_tool(query: str, top_k: int = 5) -> str:
            """Search for recipes based on ingredients, dietary preferences, or meal type."""
            result = tool_handler("search_recipes", {"query": query, "top_k": top_k}) if tool_handler else {}
            tool_calls_log.append({"tool": "search_recipes", "input": {"query": query}, "result": result})
            return json.dumps(result)

        @tool
        def add_to_favorites(recipe_name: str, recipe_content: str = "") -> str:
            """Add a recipe to the user's favourites list."""
            result = tool_handler("add_to_favorites", {"recipe_name": recipe_name, "recipe_content": recipe_content}) if tool_handler else {}
            tool_calls_log.append({"tool": "add_to_favorites", "input": {"recipe_name": recipe_name}, "result": result})
            return json.dumps(result)

        @tool
        def add_to_meal_plan(day: str, meal_name: str) -> str:
            """Add a meal to the weekly meal plan for a specific day (Monday-Sunday)."""
            result = tool_handler("add_to_meal_plan", {"day": day, "meal_name": meal_name}) if tool_handler else {}
            tool_calls_log.append({"tool": "add_to_meal_plan", "input": {"day": day, "meal_name": meal_name}, "result": result})
            return json.dumps(result)

        @tool
        def add_to_shopping_list(items: list) -> str:
            """Add a list of ingredients to the shopping list."""
            result = tool_handler("add_to_shopping_list", {"items": items}) if tool_handler else {}
            tool_calls_log.append({"tool": "add_to_shopping_list", "input": {"items": items}, "result": result})
            return json.dumps(result)

        @tool
        def log_nutrition(meal_type: str, name: str, calories: float,
                          protein: float = 0, carbs: float = 0, fats: float = 0) -> str:
            """Log a meal with nutrition information. meal_type must be breakfast, lunch, dinner, or snack."""
            inp = {"meal_type": meal_type, "name": name, "calories": calories,
                   "protein": protein, "carbs": carbs, "fats": fats}
            result = tool_handler("log_nutrition", inp) if tool_handler else {}
            tool_calls_log.append({"tool": "log_nutrition", "input": inp, "result": result})
            return json.dumps(result)

        @tool
        def get_nutrition_stats() -> str:
            """Get today's nutrition statistics and remaining calories/macros."""
            result = tool_handler("get_nutrition_stats", {}) if tool_handler else {}
            tool_calls_log.append({"tool": "get_nutrition_stats", "input": {}, "result": result})
            return json.dumps(result)

        # Inject chat history
        history_text = ""
        for m in (chat_history or [])[-6:]:
            role = m.get("role", "")
            if role not in ("user", "assistant"):
                continue
            c = m.get("content", "")
            if isinstance(c, list):
                c = " ".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
            elif isinstance(c, dict):
                c = c.get("text", "") or c.get("S", "")
            if str(c).strip():
                history_text += f"{role.capitalize()}: {c}\n"

        full_query = (
            f"Recipe Context:\n{context}\n\n"
            + (f"Recent conversation:\n{history_text}\n" if history_text else "")
            + f"User Request: {query}"
        )

        try:
            model = BedrockModel(
                model_id="anthropic.claude-3-haiku-20240307-v1:0",
                region_name="ap-southeast-2",
                max_tokens=2000,
                temperature=0.7,
            )
            agent = Agent(
                model=model,
                system_prompt=system_prompt,
                tools=[search_recipes_tool, add_to_favorites, add_to_meal_plan,
                       add_to_shopping_list, log_nutrition, get_nutrition_stats],
            )
            result = agent(full_query)
            response_text = str(result).strip()

            return {"response": response_text, "tool_calls": tool_calls_log}

        except Exception as e:
            print(f"Strands agent error: {e}")
            import traceback; traceback.print_exc()
            if 'ThrottlingException' in str(e) or 'Too many requests' in str(e):
                return self._fallback_response(query, tool_handler)
            return {"response": f"I'm having trouble responding right now. Error: {e}", "tool_calls": []}

    def _fallback_response(self, query: str, tool_handler: Optional[Any] = None) -> Dict:
        query_lower = query.lower()
        tool_results = []
        if 'week' in query_lower and ('plan' in query_lower or 'meal' in query_lower):
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            meals = ['Grilled Chicken Salad', 'Salmon with Vegetables', 'Vegetarian Pasta',
                     'Tofu Stir Fry', 'Quinoa Bowl', 'Mediterranean Salmon', 'Lentil Curry']
            if tool_handler:
                for day, meal in zip(days, meals):
                    r = tool_handler('add_to_meal_plan', {'day': day, 'meal_name': meal})
                    tool_results.append({'tool': 'add_to_meal_plan', 'input': {'day': day, 'meal_name': meal}, 'result': r})
            return {'response': "I've planned your week with healthy meals! Check your meal planner.", 'tool_calls': tool_results}
        elif 'shopping' in query_lower or 'grocery' in query_lower:
            items = ['chicken breast', 'salmon', 'vegetables', 'olive oil', 'garlic', 'rice', 'lentils']
            if tool_handler:
                r = tool_handler('add_to_shopping_list', {'items': items})
                tool_results.append({'tool': 'add_to_shopping_list', 'input': {'items': items}, 'result': r})
            return {'response': f"Added {len(items)} essentials to your shopping list!", 'tool_calls': tool_results}
        return {'response': "I'm experiencing high demand. Please try again in a few seconds.", 'tool_calls': []}
