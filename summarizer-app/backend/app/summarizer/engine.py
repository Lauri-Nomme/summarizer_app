from openai import AzureOpenAI
from ..config import settings
from ..errors import SummarizationError
from ..logger import get_logger

SUMMARY_PROMPTS = {
    "short": "Provide a very concise summary in 2-3 sentences.",
    "medium": "Provide a clear and informative summary in about one paragraph.",
    "long": "Provide a detailed and comprehensive summary covering all key points.",
}


def get_client() -> AzureOpenAI:
    if not settings.azure_openai_configured:
        raise SummarizationError(
            "Azure OpenAI is not configured. "
            "Set AZURE_OPENAI_KEY, AZURE_OPENAI_ENDPOINT, and "
            "AZURE_OPENAI_DEPLOYMENT environment variables."
        )
    return AzureOpenAI(
        api_key=settings.AZURE_OPENAI_KEY,
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_version=settings.AZURE_OPENAI_API_VERSION,
    )


def _truncate_input(text: str) -> str:
    """Truncate text to stay within model input limits."""
    if len(text) > settings.MAX_INPUT_CHARS:
        return text[: settings.MAX_INPUT_CHARS] + "\n\n[Text truncated due to length]"
    return text


def summarize(text: str, length: str = "medium", user_id: str = "anonymous") -> str:
    log = get_logger(user_id)

    if length not in SUMMARY_PROMPTS:
        raise SummarizationError(
            f"Invalid summary length '{length}'. Choose from: short, medium, long."
        )

    prompt = SUMMARY_PROMPTS[length]
    text = _truncate_input(text)
    log.info(f"Generating {length} summary for text of {len(text)} characters")
    log.info(f"Using Azure OpenAI deployment: {settings.AZURE_OPENAI_DEPLOYMENT}")

    try:
        client = get_client()
        response = client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {
                    "role": "system",
                    "content": f"You are a text summarization assistant. {prompt}",
                },
                {"role": "user", "content": text},
            ],
            max_tokens=settings.SUMMARY_LENGTHS.get(length, 300),
            temperature=0.3,
        )
        summary = response.choices[0].message.content.strip()
        log.info(f"Summary generated successfully ({len(summary)} characters)")
        return summary
    except SummarizationError:
        raise
    except Exception as e:
        log.error(f"Summarization failed: {str(e)}")
        raise SummarizationError(f"Azure OpenAI error: {str(e)}")
