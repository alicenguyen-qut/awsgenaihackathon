import boto3
import json
import numpy as np
import time
from typing import List, Dict, Any, Optional


class BedrockRAG:
    def __init__(self, recipes_bucket=None):
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name='ap-southeast-2')
        self.bedrock = boto3.client('bedrock', region_name='ap-southeast-2')
        self.s3 = boto3.client('s3')
        self.recipes_bucket = recipes_bucket
        self.embeddings_cache = {}
        self.recipes_cache = None
        self.tools = self._define_tools()
        self.response_cache = {}  # Cache responses
        self.last_request_time = 0  # Track last request
        
    def load_recipes_from_s3(self) -> List[Dict]:
        """Load recipes from S3 bucket"""
        if self.recipes_cache:
            return self.recipes_cache
        
        if not self.recipes_bucket:
            return []
        
        try:
            response = self.s3.get_object(Bucket=self.recipes_bucket, Key='embeddings/recipe_embeddings.json')
            data = json.loads(response['Body'].read())
            
            recipes = []
            for item in data:
                recipes.append({
                    'name': item['recipe_id'].replace('.txt', '').replace('_', ' ').title(),
                    'description': item['text'],
                    'tags': [],
                    'calories': 0
                })
            
            self.recipes_cache = recipes
            print(f"✅ Loaded {len(recipes)} recipes from S3")
            return recipes
        except Exception as e:
            print(f"Error loading recipes from S3: {e}")
            return []
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding using Amazon Titan Embeddings V2"""
        try:
            # Add delay to avoid rate limits
            time.sleep(0.5)
            
            response = self.bedrock_runtime.invoke_model(
                modelId='amazon.titan-embed-text-v2:0',
                body=json.dumps({
                    "inputText": text,
                    "dimensions": 1024,
                    "normalize": True
                })
            )
            result = json.loads(response['body'].read())
            return result['embedding']
        except Exception as e:
            print(f"Embedding error: {e}")
            return [0.0] * 1024
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    def search_recipes(self, query: str, recipes: List[Dict], top_k: int = 3) -> List[Dict]:
        """Search recipes using vector similarity"""
        try:
            query_embedding = self.get_embedding(query)
            
            results = []
            for recipe in recipes:
                # Create embedding for recipe if not cached
                recipe_text = f"{recipe.get('name', '')} {recipe.get('description', '')} {' '.join(recipe.get('tags', []))}"
                
                if recipe_text not in self.embeddings_cache:
                    self.embeddings_cache[recipe_text] = self.get_embedding(recipe_text)
                
                recipe_embedding = self.embeddings_cache[recipe_text]
                similarity = self.cosine_similarity(query_embedding, recipe_embedding)
                
                results.append({
                    'recipe': recipe,
                    'similarity': similarity
                })
            
            # Sort by similarity and return top_k
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return [r['recipe'] for r in results[:top_k]]
        except Exception as e:
            print(f"Search error: {e}")
            # Fallback to simple keyword matching
            query_lower = query.lower()
            matches = [r for r in recipes if any(word in r.get('name', '').lower() or word in r.get('description', '').lower() 
                                                  for word in query_lower.split())]
            return matches[:top_k] if matches else recipes[:top_k]
    
    def generate_agentic_response(self, query: str, context: str, user_profile: Dict = None,
                                  tool_handler: Optional[Any] = None) -> Dict:
        """Generate response using Claude with tool use capabilities"""
        # Check cache first
        cache_key = f"{query}:{str(user_profile)}"
        if cache_key in self.response_cache:
            print("Using cached response")
            return self.response_cache[cache_key]
        
        # Rate limiting: ensure at least 2 seconds between requests
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < 2:
            wait_time = 2 - time_since_last
            print(f"Rate limiting: waiting {wait_time:.1f}s...")
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
        
        try:
            # Build system prompt
            system_prompt = """You are an autonomous AI cooking assistant with the ability to take actions on behalf of the user.

            You can:
            - Search for recipes
            - Add recipes to favorites
            - Plan meals for the week
            - Generate shopping lists
            - Log nutrition information
            - Track daily nutrition stats

            When users ask you to do something (like "plan my week" or "add this to favorites"), proactively use the available tools to help them.
            Be conversational and explain what actions you're taking."""
            
            if user_profile:
                dietary = user_profile.get('dietary', [])
                goal = user_profile.get('healthGoal', '')
                allergies = user_profile.get('allergies', [])
                
                if dietary:
                    system_prompt += f"\n\nUser dietary preferences: {', '.join(dietary)}"
                if goal:
                    system_prompt += f"\nUser health goal: {goal}"
                if allergies:
                    system_prompt += f"\nUser allergies: {', '.join(allergies)}"
            
            # Build user message
            user_message = f"""Recipe Context:
            {context}

            User Request: {query}"""
                        
            messages = [{"role": "user", "content": user_message}]
            tool_results = []
            
            # Agentic loop - allow up to 5 tool calls
            for iteration in range(5):
                # Retry with exponential backoff
                for retry in range(3):
                    try:
                        response = self.bedrock_runtime.invoke_model(
                            modelId='anthropic.claude-3-haiku-20240307-v1:0',
                            body=json.dumps({
                                "anthropic_version": "bedrock-2023-05-31",
                                "max_tokens": 2000,
                                "temperature": 0.7,
                                "system": system_prompt,
                                "messages": messages,
                                "tools": self.tools
                            })
                        )
                        break
                    except Exception as e:
                        if 'ThrottlingException' in str(e) and retry < 2:
                            wait_time = (2 ** retry) * 2  # 2s, 4s
                            print(f"Rate limited, waiting {wait_time}s...")
                            time.sleep(wait_time)
                        else:
                            raise
                
                result = json.loads(response['body'].read())
                
                # Check if Claude wants to use tools
                if result.get('stop_reason') == 'tool_use':
                    # Extract tool use requests
                    assistant_message = {"role": "assistant", "content": result['content']}
                    messages.append(assistant_message)
                    
                    tool_use_blocks = [block for block in result['content'] if block.get('type') == 'tool_use']
                    
                    # Execute tools
                    tool_results_content = []
                    for tool_use in tool_use_blocks:
                        tool_name = tool_use['name']
                        tool_input = tool_use['input']
                        tool_use_id = tool_use['id']
                        
                        # Execute tool via handler
                        if tool_handler:
                            tool_result = tool_handler(tool_name, tool_input)
                            tool_results.append({"tool": tool_name, "input": tool_input, "result": tool_result})
                            
                            tool_results_content.append({
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "content": json.dumps(tool_result)
                            })
                    
                    # Add tool results to conversation
                    messages.append({"role": "user", "content": tool_results_content})
                    
                else:
                    # No more tools to use, return final response
                    text_content = [block['text'] for block in result['content'] if block.get('type') == 'text']
                    response_data = {
                        "response": ''.join(text_content),
                        "tool_calls": tool_results
                    }
                    # Cache the response
                    self.response_cache[cache_key] = response_data
                    return response_data
            
            # Max iterations reached
            return {
                "response": "I've completed the requested actions.",
                "tool_calls": tool_results
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"Claude error: {error_msg}")
            import traceback
            traceback.print_exc()
            
            # Fallback: Use simple pattern matching for common requests
            if 'ThrottlingException' in error_msg or 'Too many requests' in error_msg:
                return self._fallback_response(query, tool_handler)
            
            return {
                "response": f"I apologize, but I'm having trouble generating a response. Error: {error_msg}",
                "tool_calls": []
            }
    
    def _define_tools(self) -> List[Dict]:
        """Define tools that the agent can use"""
        return [
            {
                "name": "search_recipes",
                "description": "Search for recipes based on ingredients, dietary preferences, or meal type. Returns relevant recipe recommendations.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query for recipes"},
                        "top_k": {"type": "integer", "description": "Number of recipes to return", "default": 3}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "add_to_favorites",
                "description": "Add a recipe to user's favorites list",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "recipe_name": {"type": "string", "description": "Name of the recipe to add"},
                        "recipe_content": {"type": "string", "description": "Full recipe content"}
                    },
                    "required": ["recipe_name"]
                }
            },
            {
                "name": "add_to_meal_plan",
                "description": "Add a meal to the weekly meal plan for a specific day",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "day": {"type": "string", "enum": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
                        "meal_name": {"type": "string", "description": "Name of the meal"}
                    },
                    "required": ["day", "meal_name"]
                }
            },
            {
                "name": "add_to_shopping_list",
                "description": "Add ingredients to the shopping list",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "items": {"type": "array", "items": {"type": "string"}, "description": "List of ingredients to add"}
                    },
                    "required": ["items"]
                }
            },
            {
                "name": "log_nutrition",
                "description": "Log a meal with nutrition information",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "meal_type": {"type": "string", "enum": ["breakfast", "lunch", "dinner", "snack"]},
                        "name": {"type": "string", "description": "Name of the meal"},
                        "calories": {"type": "number", "description": "Calories"},
                        "protein": {"type": "number", "description": "Protein in grams"},
                        "carbs": {"type": "number", "description": "Carbs in grams"},
                        "fats": {"type": "number", "description": "Fats in grams"}
                    },
                    "required": ["meal_type", "name", "calories"]
                }
            },
            {
                "name": "get_nutrition_stats",
                "description": "Get today's nutrition statistics and remaining calories/macros",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
    
    def chat_with_rag(self, query: str, recipes: List[Dict], user_profile: Dict = None, 
                      tool_handler: Optional[Any] = None) -> Dict:
        """Main agentic RAG pipeline with tool use"""
        # Skip embedding search to avoid rate limits - use simple matching
        query_lower = query.lower()
        relevant_recipes = [r for r in recipes if any(word in r.get('name', '').lower() or 
                                                       word in r.get('description', '').lower() or
                                                       any(word in tag.lower() for tag in r.get('tags', []))
                                                       for word in query_lower.split())][:3]
        
        if not relevant_recipes:
            relevant_recipes = recipes[:3]
        
        # Build context from relevant recipes
        context = "\n\n".join([
            f"Recipe: {r.get('name', 'Unknown')}\n"
            f"Description: {r.get('description', 'No description')}\n"
            f"Tags: {', '.join(r.get('tags', []))}\n"
            f"Calories: {r.get('calories', 'Unknown')}"
            for r in relevant_recipes
        ])
        
        # Generate response with agentic capabilities
        return self.generate_agentic_response(query, context, user_profile, tool_handler)

    def _fallback_response(self, query: str, tool_handler: Optional[Any] = None) -> Dict:
        """Fallback response when rate limited - uses pattern matching"""
        query_lower = query.lower()
        tool_results = []
        
        # Weekly meal plan
        if 'week' in query_lower and ('plan' in query_lower or 'meal' in query_lower):
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            meals = ['Grilled Chicken Salad', 'Salmon with Vegetables', 'Vegetarian Pasta', 
                    'Beef Stir Fry', 'Quinoa Bowl', 'Fish Tacos', 'Roasted Chicken']
            
            if tool_handler:
                for day, meal in zip(days, meals):
                    result = tool_handler('add_to_meal_plan', {'day': day, 'meal_name': meal})
                    tool_results.append({'tool': 'add_to_meal_plan', 'input': {'day': day, 'meal_name': meal}, 'result': result})
            
            return {
                'response': "I've planned your week with healthy, balanced meals! Check your meal planner to see the full schedule.",
                'tool_calls': tool_results
            }
        
        # Shopping list
        elif 'shopping' in query_lower or 'grocery' in query_lower:
            items = ['chicken breast', 'salmon', 'vegetables', 'pasta', 'olive oil', 'garlic', 'rice']
            if tool_handler:
                result = tool_handler('add_to_shopping_list', {'items': items})
                tool_results.append({'tool': 'add_to_shopping_list', 'input': {'items': items}, 'result': result})
            
            return {
                'response': f"I've added {len(items)} essential ingredients to your shopping list!",
                'tool_calls': tool_results
            }
        
        # Default fallback
        return {
            'response': "I'm experiencing high demand right now. Please try again in a few seconds, or use the buttons to manage your meals manually.",
            'tool_calls': []
        }