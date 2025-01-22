import os
import time
from datetime import datetime, timedelta, timezone
import requests
import random
from utils.tools import logger


API_HOST = "https://dd.datadoghq.com"


def wait_backend_trace_id(trace_id, profile: bool = False, validator=None):
    runtime_id = _query_for_trace_id(trace_id, validator=validator)
    if profile:
        _query_for_profile(runtime_id)


def _headers():
    return {
        "DD-API-KEY": os.getenv("DD_API_KEY_ONBOARDING"),
        "DD-APPLICATION-KEY": os.getenv("DD_APP_KEY_ONBOARDING"),
    }


def _query_for_trace_id(trace_id, validator=None):
    url = f"{API_HOST}/api/v1/trace/{trace_id}"

    trace_data = _make_request(url, headers=_headers())
    if validator:
        logger.info("Validating backend trace...")
        if not validator(trace_id, trace_data):
            logger.info("Backend trace is not valid")
            return None
        logger.info("Backend trace is valid")

    root_id = trace_data["trace"]["root_id"]
    start_time = trace_data["trace"]["spans"][root_id]["start"]
    start_date = datetime.fromtimestamp(start_time)
    if (datetime.now() - start_date).days > 1:
        logger.info("Backend trace is too old")
        return None

    return trace_data["trace"]["spans"][root_id]["meta"]["runtime-id"]


def _make_request(
    url,
    headers=None,
    method="get",
    json=None,
    overall_timeout=300,
    request_timeout=10,
    retry_delay=1,
    backoff_factor=2,
    max_retries=8,
):
    """Make a request to the backend with retries and backoff. With the defaults, this will retry for approximately 5 minutes."""
    start_time = time.perf_counter()
    for _attempt in range(max_retries):
        try:
            r = requests.request(method=method, url=url, headers=headers, json=json, timeout=request_timeout)
            logger.debug(f" Backend response status for url [{url}]: [{r.status_code}]")
            if r.status_code == 200:
                return r.json()

            if r.status_code == 429:
                retry_after = _parse_retry_after(r.headers)
                logger.debug(f" Received 429 for url [{url}], rate limit reset in: [{retry_after}]")
                if retry_after > 0:
                    # If we have a rate limit, we should wait for the reset time instead of the exponential backoff.
                    retry_delay = retry_after
                    retry_delay += random.uniform(0, 1)
        except requests.exceptions.RequestException as e:
            logger.error(f"Error received connecting to url: [{url}] {e} ")

        logger.debug(f" Received unsuccessful status code for [{url}], retrying in: [{retry_delay}]")

        # Avoid sleeping if we are going to hit the overall timeout.
        if time.perf_counter() + retry_delay - start_time >= overall_timeout:
            raise TimeoutError(f" Reached overall timeout of {overall_timeout} for {method} {url}")

        time.sleep(retry_delay)
        retry_delay *= backoff_factor
        retry_delay += random.uniform(0, 1)

    raise TimeoutError(f"Reached max retries limit for {method} {url}")


def _parse_retry_after(headers):
    # docs: https://docs.datadoghq.com/api/latest/rate-limits/
    limit = headers.get("X-RateLimit-Limit")
    period = headers.get("X-RateLimit-Period")
    remaining = headers.get("X-RateLimit-Remaining")
    reset = headers.get("X-RateLimit-Reset")
    name = headers.get("X-RateLimit-Name")

    logger.info(
        f" Rate limit information: X-RateLimit-Name={name} X-RateLimit-Limit={limit} X-RateLimit-period={period} X-RateLimit-Ramaining={remaining} X-RateLimit-Reset={reset}"
    )

    try:
        return int(reset)
    except (ValueError, TypeError):
        return -1


def _query_for_profile(runtime_id):
    url = f"{API_HOST}/api/unstable/profiles/list"
    headers = _headers()
    headers["Content-Type"] = "application/json"

    time_to = datetime.now(timezone.utc)
    time_from = time_to - timedelta(minutes=2)
    queryJson = {
        "track": "profile",
        "filter": {
            "query": f"-_dd.hotdog:* runtime-id:{runtime_id}",
            "from": time_from.isoformat(timespec="seconds"),
            "to": time_to.isoformat(timespec="seconds"),
        },
    }

    logger.debug(f"Posting to {url} with query: {queryJson}")
    data = _make_request(url, headers=headers, method="post", json=queryJson)["data"]

    # Check if we got any profile events
    return bool(isinstance(data, list) and len(data) > 0)
