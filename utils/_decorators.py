import pytest
import inspect

from utils.tools import logger
from utils._context.core import context
from utils._xfail import xfails


def _get_wrapped_class(klass, skip_reason):

    logger.info(f"{klass.__name__} class, {skip_reason} => skipped")

    @pytest.mark.skip(reason=skip_reason)
    class Test(klass):
        pass

    Test.__doc__ = klass.__doc__

    return Test


def _get_wrapped_function(function, skip_reason):
    logger.info(f"{function.__name__} function, {skip_reason} => skipped")

    @pytest.mark.skip(reason=skip_reason)
    def wrapper(*args, **kwargs):
        return function(*args, **kwargs)

    wrapper.__doc__ = function.__doc__

    return wrapper


def _get_expected_failure_function(function, skip_reason):
    logger.info(f"{function.__name__} function, {skip_reason} => xfail")

    xfails.add_xfailed_method(function)

    @pytest.mark.expected_failure(reason=skip_reason)
    def wrapper(*args, **kwargs):
        return function(*args, **kwargs)

    wrapper.__doc__ = function.__doc__

    return wrapper


def _get_expected_failure_class(klass, skip_reason):

    logger.info(f"{klass.__name__} class, {skip_reason} => xfail")

    @pytest.mark.expected_failure(reason=skip_reason)
    class Test(klass):
        pass

    Test.__doc__ = klass.__doc__
    if hasattr(klass, "__real_test_class__"):
        Test.__real_test_class__ = klass.__real_test_class__
    else:
        Test.__real_test_class__ = klass

    xfails.add_xfailed_class(Test.__real_test_class__)

    return Test


def _should_skip(condition=None, library=None, weblog_variant=None):
    if condition is not None and not condition:
        return False

    if weblog_variant is not None and weblog_variant != context.weblog_variant:
        return False

    if library is not None and context.library != library:
        return False

    return True


def missing_feature(condition=None, library=None, weblog_variant=None, reason=None):
    """ decorator, allow to mark a test function/class as missing """

    skip = _should_skip(library=library, weblog_variant=weblog_variant, condition=condition)

    def decorator(function_or_class):

        if not skip:
            return function_or_class

        full_reason = "missing feature" if reason is None else f"missing feature: {reason}"

        if inspect.isfunction(function_or_class):
            return _get_expected_failure_function(function_or_class, full_reason)
        elif inspect.isclass(function_or_class):
            return _get_expected_failure_class(function_or_class, full_reason)
        else:
            raise Exception(f"Unexpected skipped object: {function_or_class}")

    return decorator


def irrelevant(condition=None, library=None, weblog_variant=None, reason=None):
    """ decorator, allow to mark a test function/class as not relevant """

    skip = _should_skip(library=library, weblog_variant=weblog_variant, condition=condition)

    def decorator(function_or_class):

        if not skip:
            return function_or_class

        full_reason = "not relevant" if reason is None else f"not relevant: {reason}"

        if inspect.isfunction(function_or_class):
            return _get_wrapped_function(function_or_class, full_reason)
        elif inspect.isclass(function_or_class):
            return _get_wrapped_class(function_or_class, full_reason)
        else:
            raise Exception(f"Unexpected skipped object: {function_or_class}")

    return decorator


def bug(condition=None, library=None, weblog_variant=None, reason=None):
    """
        Decorator, allow to mark a test function/class as an known bug.
        The test is executed, and if it passes, and warning is reported
    """

    expected_to_fail = _should_skip(library=library, weblog_variant=weblog_variant, condition=condition)

    def decorator(function_or_class):

        if not expected_to_fail:
            return function_or_class

        full_reason = "known bug" if reason is None else f"known bug: {reason}"

        if inspect.isfunction(function_or_class):
            return _get_expected_failure_function(function_or_class, full_reason)
        elif inspect.isclass(function_or_class):
            return _get_expected_failure_class(function_or_class, full_reason)
        else:
            raise Exception(f"Unexpected skipped object: {function_or_class}")

    return decorator


def flaky(condition=None, library=None, weblog_variant=None, reason=None):
    """ Decorator, allow to mark a test function/class as a known bug, and skip it """

    skip = _should_skip(library=library, weblog_variant=weblog_variant, condition=condition)

    def decorator(function_or_class):

        if not skip:
            return function_or_class

        full_reason = "known bug (flaky)" if reason is None else f"known bug (flaky): {reason}"

        if inspect.isfunction(function_or_class):
            return _get_wrapped_function(function_or_class, full_reason)
        elif inspect.isclass(function_or_class):
            return _get_wrapped_class(function_or_class, full_reason)
        else:
            raise Exception(f"Unexpected skipped object: {function_or_class}")

    return decorator


def released(
    cpp=None, dotnet=None, golang=None, java=None, nodejs=None, php=None, python=None, ruby=None, php_appsec=None
):
    """Class decorator, allow to mark a test class with a version number of a component"""

    def wrapper(test_class):
        def compute_requirement(tested_library, component_name, released_version, tested_version):
            if context.library != tested_library or released_version is None:
                return

            if not hasattr(test_class, "__released__"):
                setattr(test_class, "__released__", {})

            if component_name in test_class.__released__:
                raise ValueError(f"A {component_name}' version for {test_class.__name__} has been declared twice")

            test_class.__released__[component_name] = released_version

            if released_version == "?":
                return "missing feature: release not yet planned"

            if released_version.startswith("not relevant"):
                raise Exception("TODO remove this test, it should never happen")

            if tested_version >= released_version:
                logger.debug(
                    f"{test_class.__name__} feature has been released in {released_version} => added in test queue"
                )
                return

            return f"missing feature for {component_name}: release version is {released_version}, tested version is {tested_version}"

        skip_reasons = [
            compute_requirement("cpp", "cpp", cpp, context.library.version),
            compute_requirement("dotnet", "dotnet", dotnet, context.library.version),
            compute_requirement("golang", "golang", golang, context.library.version),
            compute_requirement("java", "java", java, context.library.version),
            compute_requirement("nodejs", "nodejs", nodejs, context.library.version),
            compute_requirement("php", "php_appsec", php_appsec, context.php_appsec),
            compute_requirement("php", "php", php, context.library.version),
            compute_requirement("python", "python", python, context.library.version),
            compute_requirement("ruby", "ruby", ruby, context.library.version),
        ]

        skip_reasons = [reason for reason in skip_reasons if reason]  # remove None

        if len(skip_reasons) != 0:
            for reason in skip_reasons:
                logger.info(f"{test_class.__name__} class, {reason} => skipped")
            return _get_expected_failure_class(test_class, skip_reasons[0])  # use the first skip reason found
        else:
            return test_class

    return wrapper


def rfc(link):
    def wrapper(item):
        setattr(item, "__rfc__", link)
        return item

    return wrapper
