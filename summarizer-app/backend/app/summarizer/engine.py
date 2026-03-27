import time
from openai import AzureOpenAI, APIConnectionError, RateLimitError, APITimeoutError
from ..config import settings
from ..errors import SummarizationError
from ..logger import get_logger

SUMMARY_PROMPTS = {
    "short": "Provide a very concise summary in 2-3 sentences.",
    "medium": "Provide a clear and informative summary in about one paragraph.",
    "long": "Provide a detailed and comprehensive summary covering all key points.",
}

# Transient errors that are safe to retry
RETRYABLE_EXCEPTIONS = (APIConnectionError, RateLimitError, APITimeoutError)


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


def _call_with_retry(client, messages, max_tokens, user_id="anonymous"):
    """Call Azure OpenAI with exponential backoff retry on transient errors."""
    log = get_logger(user_id)
    max_retries = settings.MAX_RETRIES
    base_delay = settings.RETRY_BASE_DELAY
    last_exception = None

    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.3,
            )
            if attempt > 1:
                log.info(f"Azure OpenAI call succeeded on attempt {attempt}")
            return response
        except RETRYABLE_EXCEPTIONS as e:
            last_exception = e
            if attempt < max_retries:
                delay = base_delay * (2 ** (attempt - 1))
                log.warning(
                    f"Azure OpenAI transient error (attempt {attempt}/{max_retries}): "
                    f"{type(e).__name__}: {e}. Retrying in {delay:.1f}s..."
                )
                time.sleep(delay)
            else:
                log.error(
                    f"Azure OpenAI failed after {max_retries} attempts: "
                    f"{type(e).__name__}: {e}"
                )

    error_type = type(last_exception).__name__
    if isinstance(last_exception, RateLimitError):
        raise SummarizationError(
            "The AI service is temporarily overloaded. Please try again in a few moments."
        )
    elif isinstance(last_exception, APITimeoutError):
        raise SummarizationError(
            "The AI service took too long to respond. Please try again."
        )
    elif isinstance(last_exception, APIConnectionError):
        raise SummarizationError(
            "Unable to connect to the AI service. Please check your network and try again."
        )
    raise SummarizationError(f"Azure OpenAI error after {max_retries} retries: {error_type}")


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
        messages = [
            {
                "role": "system",
                "content": f"You are a text summarization assistant. {prompt}",
            },
            {"role": "user", "content": text},
        ]
        max_tokens = settings.SUMMARY_LENGTHS.get(length, 300)
        response = _call_with_retry(client, messages, max_tokens, user_id)
        summary = response.choices[0].message.content.strip()
        log.info(f"Summary generated successfully ({len(summary)} characters)")
        return summary
    except SummarizationError:
        raise
    except Exception as e:
        log.error(f"Summarization failed unexpectedly: {type(e).__name__}: {str(e)}")
        raise SummarizationError(
            "An unexpected error occurred while generating the summary. Please try again."
        )
