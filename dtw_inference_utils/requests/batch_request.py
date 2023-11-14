""""Taken and adapted from https://github.com/openai/openai-cookbook/blob/main/examples/api_request_parallel_processor.py
"""""

# imports
import time
import aiohttp  # for making API calls concurrently
import asyncio  # for running API calls concurrently
import json  # for saving results to a jsonl file
import logging  # for logging rate limit warnings and other messages
import os  # for reading API key
from typing import List

from dtw_inference_utils.requests.constants import get_limits

from dtw_inference_utils.requests.status import StatusTracker, RateLimitStatus
from dtw_inference_utils.requests.request import APIRequest

from dtw_inference_utils.requests.rate_limits import num_tokens_consumed_from_request
from dtw_inference_utils.requests.utils import api_endpoint_from_url, task_id_generator_function


async def process_api_batch_request(
        request_batch: List[dict],
        save_filepath: str,
        request_url: str = "https://api.openai.com/v1/chat/completions",
        model_name: str = "gpt-3.5-turbo",
        max_attempts: int = 5,
        max_requests_per_minute: int = None,
):
    """Processes API requests in parallel, throttling to stay under rate limits."""
    # constants
    seconds_to_pause_after_rate_limit_error = 15
    seconds_to_sleep_each_loop = 0.001  # 1 ms limits max throughput to 1,000 requests per second

    # infer API endpoint and construct request header
    api_endpoint = api_endpoint_from_url(request_url)
    api_key = os.getenv("OPENAI_API_KEY")
    request_header = {"Authorization": f"Bearer {api_key}"}

    if max_requests_per_minute is None:
        max_requests_per_minute, max_tokens_per_minute, token_encoding_name = get_limits(model_name)
    else:
        _, max_tokens_per_minute, token_encoding_name = get_limits(model_name)

    # initialize trackers
    queue_of_requests_to_retry = asyncio.Queue()
    task_id_generator = (task_id_generator_function())  # generates integer IDs of 1, 2, 3, ...
    status_tracker = (StatusTracker())  # single instance to track a collection of variables
    next_request = None  # variable to hold the next request to call

    # initialize available capacity counts

    rate_limit_status = RateLimitStatus(
        max_requests_per_minute=max_requests_per_minute, max_tokens_per_minute=max_tokens_per_minute
    )

    # initialize flags
    file_not_finished = True  # after file is empty, we'll skip reading it
    logging.debug(f"Initialization complete.")

    # initialize file reading
    # `requests` will provide requests one at a time

    requests_iter = request_batch.__iter__()
    logging.debug(f"File opened. Entering main loop")
    async with aiohttp.ClientSession() as session:  # Initialize ClientSession here
        while True:
            # get next request (if one is not already waiting for capacity)
            if next_request is None:
                if not queue_of_requests_to_retry.empty():
                    next_request = queue_of_requests_to_retry.get_nowait()
                    logging.debug(f"Retrying request {next_request.task_id}: {next_request}")
                elif file_not_finished:
                    try:
                        # get new request
                        request_json = next(requests_iter)
                        next_request = APIRequest(
                            task_id=next(task_id_generator),
                            request_json=request_json,
                            token_consumption=num_tokens_consumed_from_request(
                                request_json, api_endpoint, token_encoding_name
                            ),
                            attempts_left=max_attempts,
                            metadata=request_json.pop("metadata", None),
                        )

                        status_tracker.num_tasks_started += 1
                        status_tracker.num_tasks_in_progress += 1
                        logging.debug(f"Reading request {next_request.task_id}: {next_request}")
                    except StopIteration:
                        # if file runs out, set flag to stop reading it
                        logging.debug("Read file exhausted")
                        file_not_finished = False

            # update available capacity
            rate_limit_status.reset_capacity()

            # if enough capacity available, call API
            if next_request:
                next_request_tokens = next_request.token_consumption
                if rate_limit_status.is_capacity_available(next_request_tokens):
                    # update counters
                    rate_limit_status.update_capacity(next_request_tokens)
                    next_request.attempts_left -= 1

                    # call API
                    asyncio.create_task(
                        next_request.call_api(
                            session=session,
                            request_url=request_url,
                            request_header=request_header,
                            retry_queue=queue_of_requests_to_retry,
                            save_filepath=save_filepath,
                            status_tracker=status_tracker,
                        )
                    )
                    next_request = None  # reset next_request to empty

            # if all tasks are finished, break
            if status_tracker.num_tasks_in_progress == 0:
                break

            # main loop sleeps briefly so concurrent tasks can run
            await asyncio.sleep(seconds_to_sleep_each_loop)

            # if a rate limit error was hit recently, pause to cool down
            seconds_since_rate_limit_error = time.time() - status_tracker.time_of_last_rate_limit_error

            if seconds_since_rate_limit_error < seconds_to_pause_after_rate_limit_error:
                remaining_seconds_to_pause = seconds_to_pause_after_rate_limit_error - seconds_since_rate_limit_error

                await asyncio.sleep(remaining_seconds_to_pause)

                # ^e.g., if pause is 15 seconds and final limit was hit 5 seconds ago
                cooldown_time = time.ctime(
                    status_tracker.time_of_last_rate_limit_error + seconds_to_pause_after_rate_limit_error
                )
                logging.warning(f"Pausing to cool down until {cooldown_time}")

    # after finishing, log final status
    logging.info(f"""Parallel processing complete. Results saved to {save_filepath}""")

    if status_tracker.num_tasks_failed > 0:
        logging.warning(
            f"{status_tracker.num_tasks_failed} / {status_tracker.num_tasks_started} requests failed. Errors logged to {save_filepath}."
        )

    if status_tracker.num_rate_limit_errors > 0:
        logging.warning(
            f"{status_tracker.num_rate_limit_errors} rate limit errors received. Consider running at a lower rate."
        )


def batch_request(
        request_batch: List[dict],
        cache_dir: str = os.path.join(os.getcwd(), "cache"),
        model_name: str = "gpt-3.5-turbo",
        request_url: str = "https://api.openai.com/v1/chat/completions",
        max_attempts: int = 5,
        max_requests_per_minute: int = None
):
    """Processes API requests in parallel, throttling to stay under rate limits.
    
    Args:
        request_batch: List of requests to process, of the form:
        {
            "messages": [{"role": "system", "content": system_message}],
            "temperature": temperature,
            "metadata": metadata
        }
        cache_dir: Directory to save results to, defaults to "cache" in current working directory.
        model_name: Name of the model to use, defaults to "gpt-3.5-turbo".
        max_attempts: Maximum number of attempts to make per request.
    """
    os.makedirs(cache_dir, exist_ok=True)

    for idx in range(len(request_batch)):
        if "metadata" in request_batch[idx]:
            request_batch[idx]["metadata"]["request_id"] = idx
        else:
            request_batch[idx]["metadata"] = {"request_id": idx}

    save_filepath = os.path.join(cache_dir, f"batch_request_{time.time()}.jsonl")
    asyncio.run(
        process_api_batch_request(
            request_batch=request_batch,
            save_filepath=save_filepath,
            request_url=request_url,
            model_name=model_name,
            max_attempts=max_attempts,
            max_requests_per_minute=max_requests_per_minute
        )
    )
    results = []
    with open(save_filepath, "r") as f:
        for line in f:
            results.append(json.loads(line))

    response_dict = {
        result[2]["request_id"]: {
            "request": result[0],
            "response": result[1],
            "metadata": result[2]
        } for result in results
    }


    return response_dict

