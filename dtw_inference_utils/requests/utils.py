import re


def api_endpoint_from_url(request_url):
    """Extract the API endpoint from the request URL."""
    # match = re.search("^https://[^/]+/v\\d+/(.+)$", request_url)
    match = re.search("^https?://[^/]+/(v\\d+/)?(.+)$", request_url)
    return match.group(2)


def task_id_generator_function():
    """Generate integers 0, 1, 2, and so on."""
    task_id = 0
    while True:
        yield task_id
        task_id += 1


def create_chat_completion_object(
        message: str, system_message: str = "You are an honest and helpful assistant",
        temperature: float = 0.3, response_format: str = None,  metadata: dict = None
):
    object = {
        "messages": [
            {
                "role": "system",
                "content": system_message
            },
            {
                "role": "user",
                "content": message
            }
        ],
        "temperature": temperature,
        "metadata": metadata
    }
    if response_format:
        object["response_format"] = {"type": response_format}
    return object

