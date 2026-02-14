# Agentic AI System Guide

## Overview

The Personal Cooking Assistant now uses **Claude 3.5 Sonnet's agentic capabilities** with tool use to autonomously perform actions on behalf of users.

## Architecture

```
User Query → BedrockRAG (Claude) → Tool Selection → Tool Execution → Response
                    ↓                              ↓
              RAG Context                    Tool Handler (app.py)
                    ↓                              ↓
            Recipe Embeddings              User Data Updates
```

## Available Tools

The agent can autonomously use these tools:

### 1. **search_recipes**
- Search for recipes based on ingredients, dietary preferences, or meal type
- Returns relevant recipe recommendations

### 2. **add_to_favorites**
- Add recipes to user's favorites list
- Stores full recipe content for later viewing

### 3. **add_to_meal_plan**
- Add meals to weekly meal plan (Monday-Sunday)
- Organizes meals by day

### 4. **add_to_shopping_list**
- Add ingredients to shopping list
- Supports multiple items at once

### 5. **log_nutrition**
- Log meals with nutrition information
- Tracks calories, protein, carbs, and fats

### 6. **get_nutrition_stats**
- Get today's nutrition statistics
- Shows remaining calories and macros

## Example Interactions

### Multi-Step Planning
**User:** "Plan my week with healthy meals"

**Agent Actions:**
1. Searches for healthy recipes
2. Adds 7 meals to meal plan (one per day)
3. Generates shopping list from ingredients
4. Responds with summary

### Autonomous Favorites
**User:** "Show me a chicken recipe and save it to favorites"

**Agent Actions:**
1. Searches for chicken recipes
2. Adds best match to favorites
3. Returns recipe details

### Nutrition Tracking
**User:** "I just ate a grilled chicken salad for lunch"

**Agent Actions:**
1. Estimates nutrition values
2. Logs meal with calories/macros
3. Shows remaining daily calories

### Shopping List Generation
**User:** "I'm making pasta tonight, what do I need?"

**Agent Actions:**
1. Searches for pasta recipes
2. Extracts ingredients
3. Adds items to shopping list
4. Returns recipe instructions

## How It Works

### 1. Tool Definition (bedrock_rag.py)
```python
tools = [
    {
        "name": "add_to_favorites",
        "description": "Add a recipe to user's favorites list",
        "input_schema": {
            "type": "object",
            "properties": {
                "recipe_name": {"type": "string"},
                "recipe_content": {"type": "string"}
            }
        }
    }
]
```

### 2. Agentic Loop (bedrock_rag.py)
- Claude receives user query + available tools
- Claude decides which tools to use
- Tools are executed via tool_handler
- Results are fed back to Claude
- Claude generates final response

### 3. Tool Execution (app.py)
```python
def tool_handler(tool_name: str, tool_input: dict) -> dict:
    if tool_name == "add_to_favorites":
        # Execute action
        user_data['favorites'].append(recipe)
        save_user_data(user_id, user_data)
        return {"success": True, "message": "Added to favorites"}
```

### 4. Frontend Display (03-chat.js)
- Tool calls are displayed with icons
- Actions are shown in a styled card
- Context is reloaded after actions

## Configuration

### AWS Mode (Required for Agent)
```bash
# .env file
USE_AWS=true
AWS_REGION=ap-southeast-2
```

### Local Mode
- Falls back to mock responses
- No agentic capabilities
- Uses pattern matching (07-agent.js)

## Testing the Agent

### Test 1: Multi-Step Planning
```
User: "Plan my entire week with vegetarian meals"
Expected: 7 meals added to meal plan
```

### Test 2: Autonomous Actions
```
User: "Find a salmon recipe and add it to my favorites"
Expected: Recipe searched and added to favorites
```

### Test 3: Shopping List
```
User: "I want to make tacos, add ingredients to my shopping list"
Expected: Taco ingredients added to shopping list
```

### Test 4: Nutrition Logging
```
User: "I had oatmeal with banana for breakfast"
Expected: Meal logged with estimated nutrition
```

## Benefits

### 1. **Natural Interaction**
- Users don't need to click buttons
- Conversational commands work naturally
- Agent understands intent

### 2. **Multi-Step Execution**
- Single request can trigger multiple actions
- Agent chains tools intelligently
- Reduces user effort

### 3. **Proactive Assistance**
- Agent suggests next steps
- Anticipates user needs
- Provides context-aware help

### 4. **Transparent Actions**
- All tool calls are displayed
- Users see what the agent did
- Actions can be verified

## Limitations

### Current Limitations
- Maximum 5 tool calls per request (prevents infinite loops)
- AWS mode only (requires Bedrock access)
- No tool call history persistence
- Limited error recovery

### Future Enhancements
- [ ] Multi-turn conversations with tool memory
- [ ] Undo/redo for agent actions
- [ ] User confirmation for critical actions
- [ ] Tool call analytics and insights
- [ ] Custom tool definitions per user
- [ ] Voice-activated agent commands

## Troubleshooting

### Agent Not Working
1. Check `USE_AWS=true` in .env
2. Verify AWS credentials configured
3. Ensure Bedrock access in ap-southeast-2
4. Check CloudWatch logs for errors

### Tools Not Executing
1. Check tool_handler in app.py
2. Verify user_data structure
3. Check console for errors
4. Ensure save_user_data is called

### No Tool Calls Displayed
1. Check data.tool_calls in response
2. Verify displayToolCalls function
3. Check browser console
4. Ensure 03-chat.js is loaded

## Code Structure

```
src/
├── models/
│   └── bedrock_rag.py          # Agent + tool definitions
├── app.py                       # Tool handler + execution
└── frontend/js/
    ├── 03-chat.js              # Tool call display
    └── 07-agent.js             # Legacy local mode agent
```

## API Response Format

```json
{
  "response": "I've planned your week with healthy meals!",
  "tool_calls": [
    {
      "tool": "add_to_meal_plan",
      "input": {"day": "Monday", "meal_name": "Grilled Chicken Salad"},
      "result": {"success": true, "message": "Added to Monday"}
    }
  ]
}
```

## Security Considerations

- Tool execution is server-side only
- User data is isolated by session
- No direct database access from tools
- All actions are logged
- Rate limiting recommended for production

## Performance

- Average response time: 2-4 seconds
- Tool execution: <100ms per tool
- Maximum tools per request: 5
- Concurrent requests: Handled by Flask

## Monitoring

### Key Metrics
- Tool call success rate
- Average tools per request
- Most used tools
- Error rates by tool
- Response time by tool count

### Logging
```python
print(f"Tool executed: {tool_name}")
print(f"Tool input: {tool_input}")
print(f"Tool result: {tool_result}")
```

## Contributing

To add new tools:

1. Define tool in `_define_tools()` (bedrock_rag.py)
2. Add handler in `tool_handler()` (app.py)
3. Add icon in `displayToolCalls()` (03-chat.js)
4. Test with sample queries
5. Update documentation

---
