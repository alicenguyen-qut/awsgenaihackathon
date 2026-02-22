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
            "You are the MealBuddy Document Analyst. Answer from the provided document context below.\n"
            "If the document context contains relevant information, quote specific details from it.\n"
            "If the document context is empty or doesn't contain the answer, say so clearly and fall back to the user profile.\n"
            f"User profile — allergies: {allergies}, dietary: {dietary}\n\n"
            f"Document context:\n{doc_context or 'No documents uploaded yet.'}"
        ),
        tools=[],
    )
    if callback_handler is not None:
        kwargs['callback_handler'] = callback_handler
    return Agent(**kwargs)
