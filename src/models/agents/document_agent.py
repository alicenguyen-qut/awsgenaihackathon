from strands import Agent
from strands.models import BedrockModel

MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"
REGION = "ap-southeast-2"


def make_document_agent(doc_context: str, user_profile: dict, callback_handler=None):
    allergies = ", ".join(user_profile.get("allergies", [])) or "none"
    dietary = ", ".join(user_profile.get("dietary", [])) or "none"

    kwargs = dict(
        model=BedrockModel(model_id=MODEL_ID, region_name=REGION, temperature=0.3),
        system_prompt=(
            "You are the MealBuddy Document Analyst. You have full access to this user's health profile and uploaded documents.\n"
            "ALWAYS answer questions about allergies, dietary restrictions, and health goals — never refuse.\n"
            f"User profile — allergies: {allergies}, dietary preferences: {dietary}\n\n"
            + (f"Document context:\n{doc_context}" if doc_context else "No documents uploaded. Answer from the user profile above.")
        ),
        tools=[],
    )
    if callback_handler is not None:
        kwargs['callback_handler'] = callback_handler
    return Agent(**kwargs)
