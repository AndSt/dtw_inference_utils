from dataclasses import dataclass
import time


@dataclass
class StatusTracker:
    """Stores metadata about the script's progress. Only one instance is created."""

    num_tasks_started: int = 0
    num_tasks_in_progress: int = 0  # script ends when this reaches 0
    num_tasks_succeeded: int = 0
    num_tasks_failed: int = 0
    num_rate_limit_errors: int = 0
    num_api_errors: int = 0  # excluding rate limit errors, counted above
    num_other_errors: int = 0
    time_of_last_rate_limit_error: int = 0  # used to cool off after hitting rate limits


class RateLimitStatus:
    def __init__(self, max_requests_per_minute: float, max_tokens_per_minute: float, last_update_time: int = None):
        self.max_requests_per_minute = max_requests_per_minute
        self.max_tokens_per_minute = max_tokens_per_minute

        self.available_request_capacity = max_requests_per_minute
        self.available_token_capacity = max_tokens_per_minute

        if last_update_time is None:
            self.last_update_time = time.time()
        else:
            self.last_update_time = last_update_time

    def reset_capacity(self):
        current_time = time.time()
        seconds_since_update = current_time - self.last_update_time
        self.available_request_capacity = min(
            self.available_request_capacity + self.max_requests_per_minute * seconds_since_update / 60.0,
            self.max_requests_per_minute,
        )
        self.available_token_capacity = min(
            self.available_token_capacity + self.max_tokens_per_minute * seconds_since_update / 60.0,
            self.max_tokens_per_minute,
        )
        self.last_update_time = current_time

    def is_capacity_available(self, num_tokens: int):
        return self.available_request_capacity >= 1 and self.available_token_capacity >= num_tokens

    def update_capacity(self, num_tokens: int):
        self.available_request_capacity -= 1
        self.available_token_capacity -= num_tokens