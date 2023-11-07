# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2021 Datadog, Inc.
import json
import time

import pytest
from pytest_jsonreport.plugin import JSONReport

from manifests.parser.core import load as load_manifests
from utils import context
from utils._context._scenarios import scenarios
from utils.tools import logger
from utils.scripts.junit_report import junit_modifyreport
from utils._context.library_version import LibraryVersion
from utils._decorators import released

# Monkey patch JSON-report plugin to avoid noise in report
JSONReport.pytest_terminal_summary = lambda *args, **kwargs: None


def _JSON_REPORT_FILE():
    return f"{context.scenario.host_log_folder}/report.json"


def _XML_REPORT_FILE():
    return f"{context.scenario.host_log_folder}/reportJunit.xml"


def pytest_addoption(parser):
    parser.addoption(
        "--scenario", "-S", type=str, action="store", default="DEFAULT", help="Unique identifier of scenario"
    )
    parser.addoption("--replay", "-R", action="store_true", help="Replay tests based on logs")
    parser.addoption("--sleep", action="store_true", help="Startup scenario without launching the tests (keep running)")
    parser.addoption(
        "--force-execute", "-F", action="append", default=[], help="Item to execute, even if they are skipped"
    )
    # Onboarding scenarios mandatory parameters
    parser.addoption("--obd-weblog", type=str, action="store", help="Set onboarding weblog")
    parser.addoption("--obd-library", type=str, action="store", help="Set onboarding library to test")
    parser.addoption("--obd-env", type=str, action="store", help="Set onboarding environment")


def pytest_configure(config):
    # First of all, we must get the current scenario
    for name in dir(scenarios):
        if name.upper() == config.option.scenario:
            context.scenario = getattr(scenarios, name)
            break

    if context.scenario is None:
        pytest.exit(f"Scenario {config.option.scenario} does not exists", 1)

    context.scenario.configure(config)

    if not config.option.replay and not config.option.collectonly:
        config.option.json_report_file = _JSON_REPORT_FILE()
        config.option.xmlpath = _XML_REPORT_FILE()


# Called at the very begening
def pytest_sessionstart(session):

    # get the terminal to allow logging directly in stdout
    setattr(logger, "terminal", session.config.pluginmanager.get_plugin("terminalreporter"))

    if session.config.option.sleep:
        logger.terminal.write("\n ********************************************************** \n")
        logger.terminal.write(" *** .:: Sleep mode activated. Press Ctrl+C to exit ::. *** ")
        logger.terminal.write("\n ********************************************************** \n\n")

    if session.config.option.collectonly:
        return

    context.scenario.session_start()


# called when each test item is collected
def _collect_item_metadata(item):

    _docs = {}
    _skip_reasons = {}
    _release_versions = {}
    _coverages = {}
    _rfcs = {}

    _docs[item.nodeid] = item.obj.__doc__
    _docs[item.parent.nodeid] = item.parent.obj.__doc__

    _release_versions[item.parent.nodeid] = getattr(item.parent.obj, "__released__", None)

    if hasattr(item.parent.obj, "__coverage__"):
        _coverages[item.parent.nodeid] = getattr(item.parent.obj, "__coverage__")

    if hasattr(item.parent.obj, "__rfc__"):
        _rfcs[item.parent.nodeid] = getattr(item.parent.obj, "__rfc__")
    if hasattr(item.obj, "__rfc__"):
        _rfcs[item.nodeid] = getattr(item.obj, "__rfc__")

    if hasattr(item.parent.parent, "obj"):
        _docs[item.parent.parent.nodeid] = item.parent.parent.obj.__doc__
    else:
        _docs[item.parent.parent.nodeid] = "Unexpected structure"

    markers = item.own_markers

    parent = item.parent
    while parent is not None:
        markers += parent.own_markers
        parent = parent.parent

    for marker in reversed(markers):
        skip_reason = _get_skip_reason_from_marker(marker)
        if skip_reason:
            logger.debug(f"{item.nodeid} => {skip_reason} => skipped")
            _skip_reasons[item.nodeid] = skip_reason
            break
    return {
        "docs": _docs,
        "skip_reasons": _skip_reasons,
        "release_versions": _release_versions,
        "coverages": _coverages,
        "rfcs": _rfcs,
    }


def _get_skip_reason_from_marker(marker):
    if marker.name == "skipif":
        if all(marker.args):
            return marker.kwargs.get("reason", "")
    elif marker.name in ("skip", "xfail"):
        if len(marker.args):  # if un-named arguments are present, the first one is the reason
            return marker.args[0]

        # otherwise, search in named arguments
        return marker.kwargs.get("reason", "")

    return None


def pytest_pycollect_makemodule(module_path, parent):

    # As now, declaration only works for tracers at module level

    if context.scenario.library.library == "python_http":
        library = "python"
    else:
        library = context.scenario.library.library

    manifests = load_manifests()

    nodeid = str(module_path.relative_to(module_path.cwd()))

    if nodeid in manifests and library in manifests[nodeid]:
        declaration = manifests[nodeid][library]

        logger.info(f"Manifest declaration found for {nodeid}: {declaration}")

        mod: pytest.Module = pytest.Module.from_parent(parent, path=module_path)

        if declaration.startswith("irrelevant") or declaration.startswith("flaky"):
            mod.add_marker(pytest.mark.skip(reason=declaration))
            logger.debug(f"Module {nodeid} is skipped by manifest file because {declaration}")
        else:
            mod.add_marker(pytest.mark.xfail(reason=declaration))
            logger.debug(f"Module {nodeid} is xfailed by manifest file because {declaration}")

        return mod


@pytest.hookimpl(tryfirst=True)
def pytest_pycollect_makeitem(collector, name, obj):

    if collector.istestclass(obj, name):

        manifest = load_manifests()

        nodeid = f"{collector.nodeid}::{name}"

        if nodeid in manifest:
            declaration = manifest[nodeid]
            logger.info(f"Manifest declaration found for {nodeid}: {declaration}")

            released(_is_from_manifest=True, **declaration)(obj)


def pytest_collection_modifyitems(session, config, items):
    """unselect items that are not included in the current scenario"""

    logger.debug("pytest_collection_modifyitems")

    def get_declared_scenario(item):
        for marker in item.own_markers:
            if marker.name == "scenario":
                return marker.args[0]

        for marker in item.parent.own_markers:
            if marker.name == "scenario":
                return marker.args[0]

        for marker in item.parent.parent.own_markers:
            if marker.name == "scenario":
                return marker.args[0]

        return None

    selected = []
    deselected = []

    for item in items:
        declared_scenario = get_declared_scenario(item)
        # If we are running scenario with the option sleep, we deselect all
        if session.config.option.sleep:
            deselected.append(item)
            continue

        if (
            declared_scenario == context.scenario.name
            or declared_scenario is None
            and context.scenario.name == "DEFAULT"
        ):
            logger.info(f"{item.nodeid} is included in {context.scenario}")
            selected.append(item)

            for forced in config.option.force_execute:
                if item.nodeid.startswith(forced):
                    logger.info(f"{item.nodeid} is normally skipped, but forced thanks to -F {forced}")
                    item.own_markers = [m for m in item.own_markers if m.name not in ("skip", "skipif")]

        else:
            logger.debug(f"{item.nodeid} is not included in {context.scenario}")
            deselected.append(item)
    items[:] = selected
    config.hook.pytest_deselected(items=deselected)


def _item_is_skipped(item):
    for marker in item.own_markers:
        if marker.name in ("skip",):
            return True

    for marker in item.parent.own_markers:
        if marker.name in ("skip",):
            return True

    # for test methods in classes, item.parent.parent is the module
    if item.parent.parent:
        for marker in item.parent.parent.own_markers:
            if marker.name in ("skip",):
                return True

    return False


def pytest_collection_finish(session):
    from utils import weblog

    if session.config.option.collectonly:
        return

    if session.config.option.sleep:  # on this mode, we simply sleep, not running any test or setup
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:  # catching ctrl+C
            context.scenario.close_targets()
            return
        except Exception as e:
            raise e

    last_item_file = ""
    for item in session.items:

        if _item_is_skipped(item):
            continue

        if not item.instance:  # item is a method bounded to a class
            continue

        # the test metohd name is like test_xxxx
        # we replace the test_ by setup_, and call it if it exists

        setup_method_name = f"setup_{item.name[5:]}"

        if not hasattr(item.instance, setup_method_name):
            continue

        item_file = item.nodeid.split(":", 1)[0]
        if last_item_file != item_file:
            if len(last_item_file) == 0:
                logger.terminal.write_sep("-", "tests setup", bold=True)

            logger.terminal.write(f"\n{item_file} ")
            last_item_file = item_file

        setup_method = getattr(item.instance, setup_method_name)
        logger.debug(f"Call {setup_method} for {item}")
        try:
            weblog.current_nodeid = item.nodeid
            setup_method()
            weblog.current_nodeid = None
        except Exception:
            logger.exception("Unexpected failure during setup method call")
            logger.terminal.write("x", bold=True, red=True)
            context.scenario.close_targets()
            raise
        else:
            logger.terminal.write(".", bold=True, green=True)
        finally:
            weblog.current_nodeid = None

    logger.terminal.write("\n\n")

    context.scenario.post_setup()


def pytest_runtest_call(item):
    from utils import weblog

    if item.nodeid in weblog.responses:
        for response in weblog.responses[item.nodeid]:
            request = response["request"]
            if "method" in request:
                logger.info(f"weblog {request['method']} {request['url']} -> {response['status_code']}")
            else:
                logger.info("weblog GRPC request")


@pytest.hookimpl(optionalhook=True)
def pytest_json_runtest_metadata(item, call):

    if call.when != "setup":
        return {}

    return _collect_item_metadata(item)


def pytest_json_modifyreport(json_report):

    try:
        logger.debug("Modifying JSON report")

        # populate and adjust some data
        for test in json_report["tests"]:
            if "metadata" in test:
                test["skip_reason"] = (
                    test["metadata"]["skip_reasons"][test["nodeid"]]
                    if test["nodeid"] in test["metadata"]["skip_reasons"]
                    else None
                )

        # add usefull data for reporting
        json_report["docs"] = {}
        json_report["context"] = context.serialize()
        json_report["release_versions"] = {}
        json_report["rfcs"] = {}
        json_report["coverages"] = {}

        # clean useless and volumetric data
        json_report.pop("collectors", None)

        for test in json_report["tests"]:
            if "metadata" in test:
                json_report["docs"] = json_report["docs"] | test["metadata"]["docs"]
                json_report["release_versions"] = json_report["release_versions"] | test["metadata"]["release_versions"]
                json_report["rfcs"] = json_report["rfcs"] | test["metadata"]["rfcs"]
                json_report["coverages"] = json_report["coverages"] | test["metadata"]["coverages"]

            for k in ("setup", "call", "teardown", "keywords", "lineno", "metadata"):
                if k in test:
                    del test[k]

        logger.debug("Modifying JSON report finished")

    except:
        logger.error("Fail to modify json report", exc_info=True)


def pytest_sessionfinish(session, exitstatus):

    context.scenario.pytest_sessionfinish(session)
    if session.config.option.collectonly or session.config.option.replay:
        return

    # xdist: pytest_sessionfinish function runs at the end of all tests. If you check for the worker input attribute, it will run in the master thread after all other processes have finished testing
    if not hasattr(session.config, "workerinput"):
        json.dump(
            {library: sorted(versions) for library, versions in LibraryVersion.known_versions.items()},
            open(f"{context.scenario.host_log_folder}/known_versions.json", "w", encoding="utf-8"),
            indent=2,
        )

        junit_modifyreport(
            _JSON_REPORT_FILE(), _XML_REPORT_FILE(), junit_properties=context.scenario.get_junit_properties(),
        )
