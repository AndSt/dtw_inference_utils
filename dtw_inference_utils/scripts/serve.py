import logging
from re import T
import subprocess

import click

from dtw_inference_utils.log import init_logging


@click.command()
@click.option(
    "--model", type=str, help="Model ID", default="HuggingFaceH4/zephyr-7b-beta"
)
@click.option(
    "--server_type",
    type=click.Choice(["OpenAI", "standard"]),
    help='Server type. Allowed values are "OpenAI" and "standard".',
    default="OpenAI",
)
@click.option(
    "--disable-log-requests",
    is_flag=True,
    help="Disable logging of requests",
    default=True,
)
def start_server(model, server_type):
    init_logging()

    if server_type not in ["OpenAI", "standard"]:
        print("Invalid server type. Allowed values are 'OpenAI' and 'standard'.")
        exit(1)

    logging.info(f"Starting server for model {model} with server type {server_type}")

    log_flag = "--disable-log-requests" if server_type == "OpenAI" else "[]"

    server_cmd = (
        "vllm.entrypoints.openai.api_server"
        if server_type == "OpenAI"
        else "vllm.entrypoints.api_server"
    )

    cmd_list = ["python", "-m", server_cmd, "--model", model, log_flag]
    logging.info(f"Running command: {' '.join(cmd_list)}")

    subprocess.run(
        ["python", "-m", server_cmd, "--model", model, log_flag],
        check=True,
    )


if __name__ == "__main__":
    start_server()
    exit(1)
