
# --- Centralized LLM Provider & Model Selection ---
import logging, os
from typing import List, Dict, Any, Optional
from app.config import config
from openai import AzureOpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

provider = (config.LLM_PROVIDER or "openai").lower()
if provider == "azure":
    REASONING_MODEL = config.AZURE_REASONING_MODEL
    SUMMARIZING_MODEL = config.AZURE_SUMMARIZING_MODEL
    PLANNER_MODEL = config.AZURE_PLANNER_MODEL
    EMBEDDING_MODEL = config.EMBEDDING_MODEL_NAME
    BASE_MODEL_PARAMS = {
        "azure_endpoint": config.AZURE_OPENAI_ENDPOINT,
        "api_key": config.AZURE_OPENAI_KEY,
        "api_version": config.AZURE_OPENAI_API_VERSION,
    }
    def create_llm_client():
        client = AzureOpenAI(**BASE_MODEL_PARAMS)
        logger.info("Azure OpenAI client created successfully (llmutils.py)")
        logger.info(f"Using endpoint: {BASE_MODEL_PARAMS['azure_endpoint']}")
        logger.info(f"Using API version: {BASE_MODEL_PARAMS['api_version']}")
        return client
elif provider == "openai":
    REASONING_MODEL = config.OPENAI_REASONING_MODEL
    SUMMARIZING_MODEL = config.OPENAI_SUMMARIZING_MODEL
    PLANNER_MODEL = config.OPENAI_PLANNER_MODEL
    EMBEDDING_MODEL = config.EMBEDDING_MODEL_NAME
    BASE_MODEL_PARAMS = {}
    def create_llm_client():
        # Placeholder for OpenAI client creation
        logger.info("OpenAI client would be created here.")
        return None
else:
    raise ValueError(f"Unsupported LLM_PROVIDER: {config.LLM_PROVIDER}")

llm_client = create_llm_client()


def get_embeddings(text: str, model_name: str = None) -> Optional[list]:
    """
    Generate an embedding for the given text using the selected LLM provider.
    """
    if not text or not text.strip():
        return None
    try:
        response = llm_client.embeddings.create(
            input=text.strip(),
            model=model_name or EMBEDDING_MODEL
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return None


def generate_sloka_summary(context: List[dict]) -> str:
    """
    Generate a comprehensive context summary for surrounding slokas using the selected LLM provider.
    """
    try:
        if not context or len(context) == 0:
            return "No context provided for summary generation."
        main_sloka = context[0]
        sloka_index = main_sloka.get('sloka_index', '')
        scripture_name = main_sloka.get('scripture_name', '')
        input_sloka = main_sloka.get('input_sloka', '')
        english_meaning = main_sloka.get('english_meaning', '')
        context_info = []
        for i, sloka in enumerate(context):
            sloka_text = sloka.get('input_sloka', '')
            meaning = sloka.get('english_meaning', '')
            index = sloka.get('sloka_index', f'sloka_{i}')
            if sloka_text and meaning:
                context_info.append(f"Sloka {index}: {sloka_text}\nMeaning: {meaning}")
        context_text = "\n\n".join(context_info)
        system_prompt = """You are an expert scholar of Hindu scriptures and Sanskrit literature. Your task is to generate a comprehensive contextual summary that helps readers understand the given sloka within its broader narrative and thematic context.

        Focus on:
        1. The narrative flow and how this verse fits into the broader story
        2. Thematic connections with surrounding verses
        3. Philosophical or spiritual significance within the context
        4. Character development or dialogue context if applicable
        5. How understanding the context enhances interpretation of the main verse

        Provide a clear, accessible summary that would help someone better understand and answer questions about this verse."""
        user_prompt = f"""Please generate a comprehensive contextual summary for the main sloka and its surrounding context:

        Main Sloka:
        Scripture: {scripture_name}
        Sloka Index: {sloka_index}
        Original Sanskrit: {input_sloka}
        English Meaning: {english_meaning}

        Surrounding Context:
        {context_text}

        Analyze this verse within its surrounding context and provide insights that would help in answering questions about its meaning, significance, and relevance. Focus on how the surrounding verses inform the interpretation of the main sloka."""
        completion = llm_client.chat.completions.create(
            model=SUMMARIZING_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=2000,
            temperature=0.7,
            top_p=1.0,
            presence_penalty=0.0,
            frequency_penalty=0.0
        )
        response_text = (
            completion.choices[0].message.reasoning_content
            if hasattr(completion.choices[0].message, 'reasoning_content') and completion.choices[0].message.reasoning_content
            else completion.choices[0].message.content
        )
        if not response_text:
            raise ValueError("No response text received from model.")
        logger.info(f"Generated contextual summary for {sloka_index} in {scripture_name} with {len(context)} surrounding slokas")
        return response_text.strip()
    except Exception as e:
        logger.warning(f"Context summary generation failed: {e}")
        main_sloka = context[0] if context else {}
        if not isinstance(main_sloka, dict):
            logger.warning(f"main_sloka is not a dict: {type(main_sloka)} - {main_sloka}")
            return "Unable to generate contextual summary due to data format issues. Please check the sloka index and try again."
        return f"Contextual analysis for {main_sloka.get('sloka_index', 'unknown verse')} from {main_sloka.get('scripture_name', 'scripture')}. This verse discusses: {main_sloka.get('english_meaning', 'teachings from the sacred text')}. For deeper understanding, consider the surrounding verses and their thematic connections."