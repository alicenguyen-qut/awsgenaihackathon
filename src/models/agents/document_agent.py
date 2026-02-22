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
            "You are the MealBuddy Document Analyst. Answer ONLY from the provided document context below.\n"
            "Quote specific details from the documents. Never invent information not present in the documents.\n"
            f"User profile — allergies: {allergies}, dietary: {dietary}\n\n"
            f"Document context:\n{doc_context or 'No documents uploaded yet.'}"
        ),
        tools=[],
    )
    if callback_handler is not None:
        kwargs['callback_handler'] = callback_handler
    return Agent(**kwargs)
