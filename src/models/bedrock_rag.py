import boto3
import json
import re
import numpy as np
from typing import List, Dict, Any, Optional

from strands.models import BedrockModel


def _extract_text(result) -> str:
    """Extract the final assistant text from a Strands agent result."""
    try:
        texts = [
            block["text"].strip()
            for block in (result.message or {}).get("content", [])
            if isinstance(block, dict) and block.get("type") == "text" and block.get("text", "").strip()
        ]
        if texts:
            # Join all text blocks — post-tool-call summary is often the last block
            # but sometimes split across multiple blocks
            return "\n".join(texts)
    except Exception:
        pass
    # Fallback: str() may contain the full conversation; extract last assistant turn
    raw = str(result).strip()
    # If str(result) looks like a role/content dump, try to pull the last assistant text
    if "'role': 'assistant'" in raw or '"role": "assistant"' in raw:
        import re as _re
        matches = _re.findall(r"'text':\s*'([^']{10,})'|\"text\":\s*\"([^\"]{10,})\"", raw)
        if matches:
            return (matches[-1][0] or matches[-1][1]).strip()
    return raw if raw else ""


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

    # ── Multi-Agent helpers ────────────────────────────────────────────────

    def _build_agent_inputs(self, query, recipes, user_profile, tool_handler, chat_history,
                            user_id, uploads_bucket, meal_plan):
        context = ""
        if meal_plan:
            meal_plan_text = "\n".join(f"- {day}: {meal}" for day, meal in meal_plan.items() if meal)
            if meal_plan_text:
                context += f"User's Current Meal Plan:\n{meal_plan_text}"

        tool_calls_log: List[Dict] = []

        def logged_tool(name, inp):
            print(f"[TOOL CALL] {name} | input: {json.dumps(inp, default=str)}")
            result = tool_handler(name, inp) if tool_handler else {}
            print(f"[TOOL RESULT] {name} | result: {json.dumps(result, default=str)}")
            tool_calls_log.append({"tool": name, "input": inp, "result": result})
            return result

        def get_recipe_context():
            relevant = self.search_recipes(query, recipes, top_k=5) if recipes else []
            return "\n\n".join([
                f"Recipe: {r.get('name','Unknown')}\nDescription: {r.get('description','')}\n"
                f"Tags: {', '.join(r.get('tags',[]))}\nCalories: {r.get('calories','Unknown')} kcal"
                for r in relevant
            ])

        def get_doc_context():
            if not (user_id and uploads_bucket):
                return ""
            chunks = self.search_user_uploads(query, user_id, uploads_bucket, top_k=5)
            return "\n---\n".join(chunks) if chunks else ""

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

        recipe_context = get_recipe_context()
        # For shopping list / action queries, surface the last assistant recipe response so the
        # planner uses the most recently discussed recipe rather than a fresh semantic search.
        last_assistant = ""
        for m in reversed(chat_history or []):
            if m.get("role") == "assistant":
                c = m.get("content", "")
                if isinstance(c, list):
                    c = " ".join(b.get("text", "") for b in c if isinstance(b, dict))
                last_assistant = str(c).strip()
                break

        full_query = (
            (f"Context:\n{context}\n\n" if context else "")
            + (f"Relevant Recipes:\n{recipe_context}\n\n" if recipe_context else "")
            + (f"Previously discussed:\n{last_assistant}\n\n" if last_assistant else "")
            + f"User Request: {query}"
        )

        return full_query, logged_tool, get_recipe_context, get_doc_context, tool_calls_log, meal_plan or {}, last_assistant

    def _make_coordinator(self, logged_tool, get_recipe_context, get_doc_context, meal_plan,
                          user_profile, last_assistant="", callback_handler=None, sub_agent_callback=None):
        from models.agents.planner_agent import make_planner_agent
        from models.agents.nutrition_agent import make_nutrition_agent
        from models.agents.document_agent import make_document_agent
        from strands import Agent, tool

        @tool
        def ask_planner(request: str) -> str:
            """Use ONLY when the user explicitly asks to: add a meal to their plan, plan their week, add to favourites/favorites, or create a shopping list. NEVER call for meal ideas, recipe requests, or suggestions."""
            print(f"[COORDINATOR → PLANNER] {request}")
            # Inject last assistant response so planner has full recipe/ingredient details
            enriched = request
            if last_assistant:
                enriched = f"Most recently discussed recipe/meal details:\n{last_assistant}\n\nRequest: {request}"
            result = _extract_text(make_planner_agent(logged_tool, meal_plan, callback_handler=sub_agent_callback)(enriched))
            print(f"[PLANNER → COORDINATOR] {result[:200]}")
            return result

        @tool
        def ask_nutrition(request: str) -> str:
            """Use ONLY when the user explicitly asks to log a meal/calories or check their calorie/macro totals (e.g. 'log my lunch', 'how many calories have I had'). NEVER call for food suggestions, recipe ideas, or nutrition facts."""
            print(f"[COORDINATOR → NUTRITION] {request}")
            result = _extract_text(make_nutrition_agent(logged_tool, user_profile or {}, callback_handler=sub_agent_callback)(request))
            print(f"[NUTRITION → COORDINATOR] {result[:200]}")
            return result

        @tool
        def ask_document(request: str) -> str:
            """Delegate questions about uploaded documents, dietary restrictions, or allergies to the Document Agent."""
            print(f"[COORDINATOR → DOCUMENT] {request}")
            result = _extract_text(make_document_agent(get_doc_context(), user_profile or {}, callback_handler=sub_agent_callback)(request))
            print(f"[DOCUMENT → COORDINATOR] {result[:200]}")
            return result

        kwargs = dict(
            model=BedrockModel(model_id="anthropic.claude-3-haiku-20240307-v1:0", region_name="ap-southeast-2", temperature=0.3),
            system_prompt=(
                "You are MealBuddy, a friendly AI nutrition assistant.\n\n"
                "## Recipe & food questions — ALWAYS answer directly, NO tools needed\n"
                "Recipe context is already provided above. Use it as inspiration, then answer from your general nutrition knowledge.\n"
                "This includes: showing a recipe, listing ingredients, giving cooking instructions, suggesting meals, or any food/nutrition question.\n"
                "When the user asks for a recipe (e.g. 'give me the recipe', 'show me the recipe', 'how do I make it'), "
                "respond with the full recipe details — name, ingredients, and steps — using the recipe context provided above.\n"
                "For filters like 'quick', 'under 15 minutes', 'high protein': suggest 2-3 options immediately. "
                "If the provided recipes don't perfectly match, use your general knowledge to suggest suitable meals that fit the criteria.\n"
                "Start your answer directly with the suggestions. NEVER say 'let me search', 'let me try', 'the results don\'t contain', or narrate any process.\n\n"
                "## Tools — ONLY when the user explicitly requests one of these exact actions\n"
                "- ask_planner: 'add to my plan', 'plan my week', 'add to favourites/favorites', 'shopping list'. NEVER for meal ideas, recipe requests, or suggestions.\n"
                "- ask_nutrition: 'log my meal', 'log my calories', 'how many calories have I had today'. NEVER for food suggestions, recipe questions, or nutrition facts.\n"
                "- ask_document: user explicitly asks about their uploaded documents or files.\n\n"
                "If in doubt, answer directly without tools.\n"
                "Never call more than one tool per message.\n"
                "CRITICAL: After a tool result, write a full response with actual details. Never say vague phrases like 'I\'ve completed the action'."
            ),
            tools=[ask_planner, ask_nutrition, ask_document],
        )
        if callback_handler is not None:
            kwargs['callback_handler'] = callback_handler
        return Agent(**kwargs)

    # ── Multi-Agent entry points ───────────────────────────────────────────

    def chat_with_rag_stream(self, query: str, recipes: List[Dict], user_profile: Dict = None,
                             tool_handler: Optional[Any] = None, chat_history: List[Dict] = None,
                             user_id: str = None, uploads_bucket: str = None,
                             meal_plan: Dict = None, token_callback=None) -> Dict:
        """Streaming variant — calls token_callback(text) for each token as it arrives from Bedrock."""
        full_query, logged_tool, get_recipe_context, get_doc_context, tool_calls_log, meal_plan, last_assistant = \
            self._build_agent_inputs(query, recipes, user_profile, tool_handler, chat_history,
                                     user_id, uploads_bucket, meal_plan)

        def callback_handler(**kwargs):
            chunk = kwargs.get('data') or kwargs.get('text', '')
            if chunk and isinstance(chunk, str) and token_callback:
                token_callback(chunk)


        try:
            print(f"[STREAM] query={repr(query[:120])}")
            coordinator = self._make_coordinator(
                logged_tool, get_recipe_context, get_doc_context, meal_plan,
                user_profile, last_assistant=last_assistant, callback_handler=callback_handler,
                sub_agent_callback=callback_handler if token_callback else None
            )
            result = coordinator(full_query)
            response_text = _extract_text(result)
            print(f"[STREAM DONE] response_text={repr(response_text[:200])} | tool_calls={len(tool_calls_log)}")
            return {"response": response_text, "tool_calls": tool_calls_log}
        except Exception as e:
            print(f"[STREAM ERROR] {e}")
            import traceback; traceback.print_exc()
            if 'ThrottlingException' in str(e) or 'Too many requests' in str(e):
                return self._fallback_response(query, tool_handler)
            return {"response": f"I'm having trouble responding right now. Error: {e}", "tool_calls": []}

    def chat_with_rag(self, query: str, recipes: List[Dict], user_profile: Dict = None,
                      tool_handler: Optional[Any] = None, chat_history: List[Dict] = None,
                      user_id: str = None, uploads_bucket: str = None,
                      meal_plan: Dict = None) -> Dict:
        """Non-streaming variant (used by /chat endpoint)."""
        full_query, logged_tool, get_recipe_context, get_doc_context, tool_calls_log, meal_plan, last_assistant = \
            self._build_agent_inputs(query, recipes, user_profile, tool_handler, chat_history,
                                     user_id, uploads_bucket, meal_plan)
        try:
            print(f"[CHAT] query={repr(query[:120])}")
            coordinator = self._make_coordinator(
                logged_tool, get_recipe_context, get_doc_context, meal_plan, user_profile,
                last_assistant=last_assistant
            )
            result = coordinator(full_query)
            response_text = _extract_text(result)
            print(f"[CHAT DONE] response_text={repr(response_text[:200])} | tool_calls={len(tool_calls_log)}")
            return {"response": response_text, "tool_calls": tool_calls_log}
        except Exception as e:
            print(f"[CHAT ERROR] {e}")
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
