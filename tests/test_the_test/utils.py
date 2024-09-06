import json
import os

from utils.tools import logger


def run_system_tests(
    scenario="MOCK_THE_TEST",
    test_path=None,
    verbose=False,
    forced_test=None,
    strict=False,
    strict_missing_features=False,
):
    cmd = ["./run.sh"]

    if scenario:
        cmd.append(scenario)
    if test_path:
        cmd.append(test_path)
    if verbose:
        cmd.append("-v")
    if forced_test:
        cmd.append(f"-F {forced_test}")
    if strict:
        cmd.append("--strict")
    if strict_missing_features:
        cmd.append("--strict-missing-features")

    cmd = " ".join(cmd)
    logger.info(cmd)
    stream = os.popen(cmd)
    output = stream.read()

    logger.info(output)

    scenario = scenario if scenario else "DEFAULT"
    with open(f"logs_{scenario.lower()}/feature_parity.json", encoding="utf-8") as f:
        report = json.load(f)

    return {test["path"]: test for test in report["tests"]}
