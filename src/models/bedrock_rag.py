import boto3
import json
import numpy as np
from typing import List, Dict

class BedrockRAG:
    def __init__(self):
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
        self.bedrock = boto3.client('bedrock', region_name='us-east-1')
        self.s3 = boto3.client('s3')
        self.embeddings_cache = {}
        
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding using Amazon Titan Embeddings V2"""
        try:
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
    
    def generate_response(self, query: str, context: str, user_profile: Dict = None) -> str:
        """Generate response using Claude 3 Haiku with RAG context"""
        try:
            # Build system prompt with user profile
            system_prompt = "You are a helpful cooking assistant. Provide personalized recipe recommendations and nutrition advice."
            
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
            
            # Build user message with context
            user_message = f"""Based on the following recipe information, answer the user's question.

Recipe Context:
{context}

User Question: {query}

Please provide a helpful, detailed response with specific recipe recommendations."""
            
            response = self.bedrock_runtime.invoke_model(
                modelId='anthropic.claude-3-haiku-20240307-v1:0',
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 2000,
                    "temperature": 0.7,
                    "system": system_prompt,
                    "messages": [
                        {
                            "role": "user",
                            "content": user_message
                        }
                    ]
                })
            )
            
            result = json.loads(response['body'].read())
            return result['content'][0]['text']
            
        except Exception as e:
            print(f"Claude error: {e}")
            return f"I apologize, but I'm having trouble generating a response. Error: {str(e)}"
    
    def chat_with_rag(self, query: str, recipes: List[Dict], user_profile: Dict = None) -> str:
        """Main RAG pipeline: search + generate"""
        # Search for relevant recipes
        relevant_recipes = self.search_recipes(query, recipes, top_k=3)
        
        # Build context from relevant recipes
        context = "\n\n".join([
            f"Recipe: {r.get('name', 'Unknown')}\n"
            f"Description: {r.get('description', 'No description')}\n"
            f"Tags: {', '.join(r.get('tags', []))}\n"
            f"Calories: {r.get('calories', 'Unknown')}"
            for r in relevant_recipes
        ])
        
        # Generate response with context
        return self.generate_response(query, context, user_profile)
