from tiktoken.model import encoding_name_for_model


limits_dict = {
    "gpt-3.5-turbo": {
        "token_limits": "1,000,000 TPM",
        "request_and_other_limits": "10,000 RPM",
        "max_requests_per_minute": 10000,
        "max_tokens_per_minute": 1000000,
    },
    "gpt-3.5-turbo-1106": {
        "token_limits": "1,000,000 TPM",
        "request_and_other_limits": "10,000 RPM",
        "max_requests_per_minute": 10000,
        "max_tokens_per_minute": 1000000,
    },
    "gpt-3.5-turbo-16k": {
        "token_limits": "1,000,000 TPM",
        "request_and_other_limits": "10,000 RPM",
        "max_requests_per_minute": 10000,
        "max_tokens_per_minute": 1000000,
    },
    "gpt-4": {
        "token_limits": "300,000 TPM",
        "request_and_other_limits": "10,000 RPM",
        "max_requests_per_minute": 10000,
        "max_tokens_per_minute": 300000,
    },
    "gpt-4-1106-preview": {
        "token_limits": "300,000 TPM",
        "request_and_other_limits": "500 RPM",
        "max_requests_per_minute": 500,
        "max_tokens_per_minute": 300000,
    },
    "text-embedding-ada-002": {
        "token_limits": "5,000,000 TPM",
        "request_and_other_limits": "10,000 RPM",
        "max_requests_per_minute": 10000,
        "max_tokens_per_minute": 5000000,
    },
    "dall-e-3": {
        "token_limits": "N/A",
        "request_and_other_limits": "15 images per minute",
        "max_requests_per_minute": 1,
        "max_tokens_per_minute": 0,
    },
    "tts-1": {
        "token_limits": "N/A",
        "request_and_other_limits": "100 RPM",
        "max_requests_per_minute": 100,
        "max_tokens_per_minute": 0,
    },
    "whisper-1": {
        "token_limits": "N/A",
        "request_and_other_limits": "100 RPM",
        "max_requests_per_minute": 100,
        "max_tokens_per_minute": 0,
    },
}


def get_limits(model_name):
    if model_name in limits_dict:
        max_requests_per_minute = limits_dict[model_name]["max_requests_per_minute"] / 3
        max_tokens_per_minute = limits_dict[model_name]["max_tokens_per_minute"] / 3
        token_encoding_name = encoding_name_for_model(model_name)

    else:
        max_requests_per_minute = 80
        max_tokens_per_minute = 200000
        token_encoding_name = model_name

    return max_requests_per_minute, max_tokens_per_minute, token_encoding_name
