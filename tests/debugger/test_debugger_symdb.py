# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2021 Datadog, Inc.

import re
import tests.debugger.utils as debugger
from utils import features, scenarios, bug, context
from utils import remote_config as rc


@features.debugger
@scenarios.debugger_symdb
class Test_Debugger_SymDb(debugger._Base_Debugger_Test):
    ############ setup ############
    def _setup(self):
        self.rc_state = rc.send_symdb_command()

    ############ assert ############
    def _assert(self):
        self.collect()
        self.assert_rc_state_not_error()
        self._assert_symbols_uploaded()

    def _assert_symbols_uploaded(self):
        assert len(self.symbols) > 0, "No symbol files were found"

        errors = []
        for symbol in self.symbols:
            error = symbol.get("system-tests-error")
            if error is not None:
                errors.append(
                    f"Error is: {error}, exported to file: {symbol.get('system-tests-file-path', 'No file path')}"
                )

        assert not errors, "Found system-tests-errors:\n" + "\n".join(f"- {err}" for err in errors)
        self._assert_debugger_controller_exists()

    def _assert_debugger_controller_exists(self):
        pattern = r"[Dd]ebugger[_]?[Cc]ontroller"

        def check_scope(scope):
            name = scope.get("name", "")
            if re.search(pattern, name):
                scope_type = scope.get("scope_type", "")
                if scope_type in ["CLASS", "class", "MODULE"]:
                    return True

                return False

            for nested_scope in scope.get("scopes", []):
                if check_scope(nested_scope):
                    return True
            return False

        for symbol in self.symbols:
            content = symbol.get("content", {})
            if isinstance(content, dict):
                for scope in content.get("scopes", []):
                    if check_scope(scope):
                        return

        raise ValueError(
            "No scope containing debugger controller with scope_type CLASS or MODULE was found in the symbols"
        )

    ############ test ############
    def setup_symdb_upload(self):
        self._setup()

    @bug(context.library == "dotnet", reason="DEBUG-3298")
    def test_symdb_upload(self):
        self._assert()
