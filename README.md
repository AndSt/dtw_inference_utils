# DTW Inference Utils

Package to make inference using LLM's for research easier.
Visit our webpage: https://dm.cs.univie.ac.at/about-us/natural-language-processing/


### Table of Contents
1. [Installation](#install)
2. [Batch call OpenAI](#batch_call)
3. [OpenAI costs](#costs)
4. [Private vllm](#private_vllm)

<a id="install"></a>
## Installation

Install using:

```bash
 pip install --extra-index-url http://185.128.246.103/pypicloud/simple/ --trusted-host 185.128.246.103 dtw_inference_utils
```

If you also want to be able to run local models, use this. Note that a GPU is needed for vllm.
```bash
pip install --extra-index-url http://185.128.246.103/pypicloud/simple/ --trusted-host 185.128.246.103 "dtw_inference_utils[server]"
```

## Usage

<a name="batch_call"></a>
### Batch Call OpenAI

```python
import random 
import nest_asyncio

from dtw_inference_utils.requests.batch_request import batch_request

# Enable nested asyncio event loop
nest_asyncio.apply()


jobs = [
    {
        "model": "gpt-3.5-turbo",
        "messages": [{
            "role": "system",
            "content": "You are a helpful assistant."
        }, 
        {
            "role": "user",
            "content": "Who won the world series in 2020?"
        }
    ],
        "metadata": {}  # Here you can save whatever you want, it will be returned like this again, might make your live easier.
    } for idx in [1, 2, 3]
]

discussion_result = batch_request(
    jobs, cache_dir="cache", model_name="gpt-3.5-turbo"
)
```

It returns a dictionary, where the keys are the list indices of jobs. Each object holds the keys "request", "response" and "metadata":

```json
{
  "0": {
    "request": {
      "model": "gpt-3.5-turbo",
      "messages": [
        {
          "role": "system",
          "content": "You are a helpful assistant."
        },
        {
          "role": "user",
          "content": "Who won the world series in 2020?"
        }
      ]
    },
    "response": {
      "id": "chatcmpl-8Kl8eGjGb9Ze2uZEgSpHOl8jVoOQs",
      "object": "chat.completion",
      "created": 1699958452,
      "model": "gpt-3.5-turbo-0613",
      "choices": [
        {
          "index": 0,
          "message": {
            "role": "assistant",
            "content": "The Los Angeles Dodgers won the World Series in 2020."
          },
          "finish_reason": "stop"
        }
      ],
      "usage": {
        "prompt_tokens": 27,
        "completion_tokens": 13,
        "total_tokens": 40
      }
    },
    "metadata": {
      "test": "test",
      "request_id": 0
    }
  }
}
```

<a name="costs"></a>
### Approximating costs

Keep in mind that rate limits and pricing is constantly changing, so this might not be the newest standard.

```python
from dtw_inference_utils.costs import (
    get_input_costs_in_dollar, get_output_costs_in_dollar, 
    get_job_input_cost_in_dollar, get_job_output_cost_in_dollar
    )

jobs = [
    {
        "model": "gpt-3.5-turbo",
        "messages": [{
            "role": "system",
            "content": "You are a helpful assistant."
        }, 
        {
            "role": "user",
            "content": "Who won the world series in 2020?"
        }
    ],
        "metadata": {}  # Here you can save whatever you want, it will be returned like this again, might make your live easier.
    } for idx in [1, 2, 3]
]

# single messages
input_costs = get_input_costs_in_dollar(messages=jobs[0["messages"], model_name="gpt-3.5-turbo")
print(input_costs) # 0.00027 Dollar

# for jobs
input_costs = get_job_input_cost_in_dollar(jobs=jobs)
print(input_costs) # 0.00081 Dollar

# maybe output is equally long, so compute on the same messages
output_costs = get_job_output_cost_in_dollar(jobs=jobs)
print(output_costs) # 0.00162 Dollar

```



### Serve a local LLM with vllm

```bash
dtw_serve --model "HuggingFaceH4/zephyr-7b-beta" 
```
which is a wrapper around vllm. Use the following command for more options:

```bash
python -m vllm.entrypoints.openai.api_server --model "HuggingFaceH4/zephyr-7b-beta" --disable-log-requests 
```

You can then use the normal OpenAI API

```python
from openai import Client


client, model = Client(base_url="http://localhost:8000/v1", api_key="EMPTY"), "HuggingFaceH4/zephyr-7b-beta"
response = client.chat.completions.create(
    model=model,
    messages=[{
            "role": "system",
            "content": "You are a helpful assistant."
        }, 
        {
            "role": "user",
            "content": "Who won the world series in 2020?"
        }
    ]
)
```

or again, run multiple jobs. Now you should set the number of calls per minute


```python
import random 
import nest_asyncio

from dtw_inference_utils.requests.batch_request import batch_request

# Enable nested asyncio event loop
nest_asyncio.apply()

model_name = "HuggingFaceH4/zephyr-7b-beta"

jobs = [
    {
        "model":model_name, 
        "messages": [{
            "role": "system",
            "content": "You are a helpful assistant."
        }, 
        {
            "role": "user",
            "content": "Who won the world series in 2020?"
        }
    ],
        "metadata": {}  # Here you can save whatever you want, it will be returned like this again, might make your live easier.
    } for idx in random.sample(range(len(dataset["train_sft"])), 2000)
]

discussion_result = batch_request(
    jobs, cache_dir="cache", model_name=model_name,
    request_url="http://localhost:8000/v1/chat/completions"
    max_requests_per_minute=50, 
)
```