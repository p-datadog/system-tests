# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2021 Datadog, Inc.
from utils import context, bug, missing_feature, irrelevant, scenarios, flaky
from utils.tools import logger

from .sql_utils import BaseDbIntegrationsTestClass


class _BaseDatadogDbIntegrationTestClass(BaseDbIntegrationsTestClass):

    """ Verify basic DB operations over different databases.
        Check integration spans status: https://docs.google.com/spreadsheets/d/1qm3B0tJ-gG11j_MHoEd9iMXf4_DvWAGCLwmBhWCxbA8/edit#gid=623219645 """

    def get_spans(self, excluded_operations=(), operations=None):
        """ get the spans from tracer and agent generated by all requests """

        # yield the span from the tracer in first, as if it fails, there is a good chance that the one from the agent also fails
        for db_operation, request in self.get_requests(excluded_operations, operations=operations):
            logger.debug(f"Start validation for {self.db_service}/{db_operation}")

            logger.debug("Validating span generated by Datadog library")
            yield db_operation, self.get_span_from_tracer(request)

            logger.debug("Validating transmitted by Datadog agent")
            yield db_operation, self.get_span_from_agent(request)

    # Tests methods
    @flaky(context.library >= "java@1.23.0", reason="DBMON-3088")
    def test_sql_traces(self, excluded_operations=()):
        """ After make the requests we check that we are producing sql traces """
        for _, span in self.get_spans(excluded_operations):
            assert span is not None

    def test_resource(self):
        """ Usually the query """

        for db_operation, span in self.get_spans(excluded_operations=["procedure", "select_error"]):
            assert db_operation in span["resource"].lower()

    @flaky(context.library >= "java@1.23.0", reason="DBMON-3088")
    def test_sql_success(self, excluded_operations=()):
        """ We check all sql launched for the app work """

        for db_operation, span in self.get_spans(excluded_operations=excluded_operations + ("select_error",)):
            assert "error" not in span or span["error"] == 0

    @irrelevant(library="python", reason="Python is using the correct span: db.system")
    @flaky(context.library >= "java@1.23.0", reason="DBMON-3088")
    def test_db_type(self, excluded_operations=()):
        """ DEPRECATED!! Now it is db.system. An identifier for the database management system (DBMS) product being used.
            Must be one of the available values: https://datadoghq.atlassian.net/wiki/spaces/APM/pages/2357395856/Span+attributes#db.system """

        for db_operation, span in self.get_spans(excluded_operations=excluded_operations):
            assert span["meta"]["db.type"] == self.db_service, f"Test is failing for {db_operation}"

    @irrelevant(library="java", reason="Java is using the correct span: db.instance")
    def test_db_name(self):
        """ DEPRECATED!! Now it is db.instance. The name of the database being connected to. Database instance name."""
        db_container = context.scenario.get_container_by_dd_integration_name(self.db_service)

        for db_operation, span in self.get_spans():
            assert span["meta"]["db.name"] == db_container.db_instance, f"Test is failing for {db_operation}"

    @flaky(context.library >= "java@1.23.0", reason="DBMON-3088")
    def test_span_kind(self, excluded_operations=()):
        """ Describes the relationship between the Span, its parents, and its children in a Trace."""

        for _, span in self.get_spans(excluded_operations):
            assert span["meta"]["span.kind"] == "client"

    @missing_feature(library="python", reason="not implemented yet")
    @missing_feature(library="java", reason="not implemented yet")
    def test_runtime_id(self):
        """ Unique identifier for the current process."""

        for db_operation, span in self.get_spans():
            assert span["meta"]["runtime-id"].strip(), f"Test is failing for {db_operation}"

    @missing_feature(library="nodejs", reason="not implemented yet")
    @missing_feature(library="java", reason="not implemented yet")
    def test_db_system(self):
        """ An identifier for the database management system (DBMS) product being used. Formerly db.type
                Must be one of the available values: https://datadoghq.atlassian.net/wiki/spaces/APM/pages/2357395856/Span+attributes#db.system """

        for db_operation, span in self.get_spans():
            assert span["meta"]["db.system"] == self.db_service, f"Test is failing for {db_operation}"

    @missing_feature(library="python", reason="not implemented yet")
    @missing_feature(library="nodejs", reason="not implemented yet")
    @missing_feature(library="java", reason="not implemented yet")
    def test_db_connection_string(self):
        """ The connection string used to connect to the database. """

        for db_operation, span in self.get_spans():
            assert span["meta"]["db.connection_string"].strip(), f"Test is failing for {db_operation}"

    def test_db_user(self, excluded_operations=()):
        """ Username for accessing the database. """
        db_container = context.scenario.get_container_by_dd_integration_name(self.db_service)

        for db_operation, span in self.get_spans(excluded_operations=excluded_operations):
            assert span["meta"]["db.user"].casefold() == db_container.db_user.casefold()

    @missing_feature(library="python", reason="not implemented yet")
    @missing_feature(library="nodejs", reason="not implemented yet")
    @flaky(context.library >= "java@1.23.0", reason="DBMON-3088")
    def test_db_instance(self, excluded_operations=()):
        """ The name of the database being connected to. Database instance name. Formerly db.name"""
        db_container = context.scenario.get_container_by_dd_integration_name(self.db_service)

        for db_operation, span in self.get_spans(excluded_operations=excluded_operations):
            assert span["meta"]["db.instance"] == db_container.db_instance

    @missing_feature(library="python", reason="not implemented yet")
    @missing_feature(library="java", reason="not implemented yet")
    @missing_feature(library="nodejs", reason="not implemented yet")
    def test_db_statement_query(self):
        """ Usually the query """

        for db_operation, span in self.get_spans(excluded_operations=["procedure", "select_error"]):
            assert db_operation in span["meta"]["db.statement"].lower()

    @missing_feature(library="nodejs", reason="not implemented yet")
    @missing_feature(library="python", reason="not implemented yet")
    @flaky(context.library >= "java@1.23.0", reason="DBMON-3088")
    def test_db_operation(self, excluded_operations=()):
        """ The name of the operation being executed """

        for db_operation, span in self.get_spans(excluded_operations=excluded_operations + ("select_error",)):
            if db_operation == "procedure":
                assert any(
                    substring in span["meta"]["db.operation"].lower() for substring in ["call", "exec"]
                ), "db.operation span not found for procedure operation"
            else:
                assert (
                    db_operation.lower() in span["meta"]["db.operation"].lower()
                ), f"Test is failing for {db_operation}"

    @missing_feature(library="python", reason="not implemented yet")
    @missing_feature(library="java", reason="not implemented yet")
    @missing_feature(library="nodejs", reason="not implemented yet")
    def test_db_sql_table(self):
        """ The name of the primary table that the operation is acting upon, including the database name (if applicable). """

        for db_operation, span in self.get_spans(excluded_operations=["procedure"]):
            assert span["meta"]["db.sql.table"].strip(), f"Test is failing for {db_operation}"

    @missing_feature(library="python", reason="not implemented yet")
    @missing_feature(library="nodejs", reason="not implemented yet")
    @missing_feature(library="java", reason="not implemented yet")
    def test_db_row_count(self):
        """ The number of rows/results from the query or operation. For caches and other datastores. 
        This tag should only set for operations that retrieve stored data, such as GET operations and queries, excluding SET and other commands not returning data.  """

        for _, span in self.get_spans(operations=["select"]):
            assert span["meta"]["db.row_count"] > 0, "Test is failing for select"

    @flaky(context.library >= "java@1.23.0", reason="DBMON-3088")
    def test_db_password(self, excluded_operations=()):
        """ The database password should not show in the traces """
        db_container = context.scenario.get_container_by_dd_integration_name(self.db_service)

        for db_operation, span in self.get_spans(excluded_operations=excluded_operations):
            for key in span["meta"]:
                if key not in [
                    "peer.hostname",
                    "db.user",
                    "env",
                    "db.instance",
                    "out.host",
                    "db.name",
                    "peer.service",
                    "net.peer.name",
                ]:  # These fields hostname, user... are the same as password
                    assert span["meta"][key] != db_container.db_password, f"Test is failing for {db_operation}"

    @missing_feature(condition=context.library != "java", reason="Apply only java")
    @missing_feature(library="java", reason="Not implemented yet")
    def test_db_jdbc_drive_classname(self):
        """ The fully-qualified class name of the Java Database Connectivity (JDBC) driver used to connect. """

        for db_operation, span in self.get_spans():
            assert span["meta"]["db.jdbc.driver_classname"].strip(), f"Test is failing for {db_operation}"

    @flaky(context.library >= "java@1.23.0", reason="DBMON-3088")
    def test_error_message(self):
        for db_operation, span in self.get_spans(operations=["select_error"]):
            # A string representing the error message.
            assert span["meta"]["error.message"].strip()

            # A string representing the type of the error.
            assert span["meta"]["error.type"].strip()

            # A human readable version of the stack trace.
            assert span["meta"]["error.stack"].strip()

    @missing_feature(
        library="java",
        reason="The Java tracer normalizing the SQL by replacing literals to reduce resource-name cardinality",
    )
    def test_NOT_obfuscate_query(self):
        """ All queries come out without obfuscation from tracer library """
        for db_operation, request in self.get_requests():
            span = self.get_span_from_tracer(request)
            assert span["resource"].count("?") == 0, f"The query should not be obfuscated for operation {db_operation}"

    def test_sql_query(self):
        """ Usually the query """
        for db_operation, request in self.get_requests(excluded_operations=["procedure", "select_error"]):
            span = self.get_span_from_agent(request)
            assert (
                db_operation in span["meta"]["sql.query"].lower()
            ), f"sql.query span not found for operation {db_operation}"

    def test_obfuscate_query(self, excluded_operations=()):
        """ All queries come out obfuscated from agent """
        for db_operation, request in self.get_requests(excluded_operations=excluded_operations):

            span = self.get_span_from_agent(request)
            # We launch all queries with two parameters (from weblog)
            # Insert and procedure:These operations also receive two parameters, but are obfuscated as only one.
            if db_operation in ["insert", "procedure"]:
                assert (
                    span["meta"]["sql.query"].count("?") == 1
                ), f"The query is not properly obfuscated for operation {db_operation}"
            else:
                assert (
                    span["meta"]["sql.query"].count("?") == 2
                ), f"The query is not properly obfuscated for operation {db_operation}"


@scenarios.integrations
class Test_Postgres(_BaseDatadogDbIntegrationTestClass):
    """ Postgres integration with Datadog tracer+agent """

    db_service = "postgresql"

    @bug(library="nodejs", reason="the value of this span should be 'postgresql' instead of  'postgres' ")
    @irrelevant(library="python", reason="Python is using the correct span: db.system")
    @flaky(context.library >= "java@1.23.0", reason="DBMON-3088")
    def test_db_type(self):
        super().test_db_type()

    @irrelevant(context.library != "java", reason="remove this test once DBMON-3088 is fixed")
    def test_partials(self):
        """ Keep testing other operations on java"""
        super().test_db_password()
        super().test_db_operation()
        super().test_db_instance()
        super().test_span_kind()
        super().test_db_type()
        super().test_sql_success()
        super().test_sql_traces()
        super().test_db_user()
        super().test_error_message()


@scenarios.integrations
class Test_MySql(_BaseDatadogDbIntegrationTestClass):
    """ MySql integration with Datadog tracer+agent """

    db_service = "mysql"

    @irrelevant(library="java", reason="Java is using the correct span: db.instance")
    @bug(library="python", reason="the value of this span should be 'world' instead of  'b'world'' ")
    def test_db_name(self):
        super().test_db_name()

    @bug(library="python", reason="the value of this span should be 'mysqldb' instead of  'b'mysqldb'' ")
    @flaky(context.library >= "java@1.23.0", reason="DBMON-3088")
    def test_db_user(self, excluded_operations=()):
        super().test_db_user()

    @irrelevant(context.library != "java", reason="remove this test once DBMON-3088 is fixed")
    def test_partials(self):
        """ Keep testing other operations on java"""
        super().test_db_user(excluded_operations=("procedure",))
        super().test_db_password(excluded_operations=("procedure",))
        super().test_db_operation(excluded_operations=("procedure",))
        super().test_db_instance(excluded_operations=("procedure",))
        super().test_span_kind(excluded_operations=("procedure",))
        super().test_db_type(excluded_operations=("procedure",))
        super().test_sql_success(excluded_operations=("procedure",))
        super().test_sql_traces(excluded_operations=("procedure",))

    @flaky(context.library >= "java@1.23.0", reason="DBMON-3088")
    def test_obfuscate_query(self, excluded_operations=()):
        super().test_obfuscate_query()


@scenarios.integrations
class Test_MsSql(_BaseDatadogDbIntegrationTestClass):
    """ MsSql integration with Datadog tracer+agent """

    db_service = "mssql"

    @missing_feature(library="python", reason="Not implemented yet")
    @missing_feature(library="java", reason="Not implemented yet")
    @missing_feature(library="nodejs", reason="Not implemented yet")
    def test_db_mssql_instance_name(self):
        """ The Microsoft SQL Server instance name connecting to. This name is used to determine the port of a named instance. 
            This value should be set only if it’s specified on the mssql connection string. """

        for db_operation, span in self.get_spans():
            assert span["meta"][
                "db.mssql.instance_name"
            ].strip(), f"db.mssql.instance_name must not be empty for operation {db_operation}"

    @bug(library="python", reason="https://github.com/DataDog/dd-trace-py/issues/7104")
    @irrelevant(library="java", reason="Java is using the correct span: db.instance")
    def test_db_name(self):
        super().test_db_name()

    @missing_feature(library="nodejs", reason="not implemented yet")
    @missing_feature(library="java", reason="not implemented yet")
    @bug(library="python", reason="https://github.com/DataDog/dd-trace-py/issues/7104")
    def test_db_system(self):
        super().test_db_system()

    @bug(library="python", reason="https://github.com/DataDog/dd-trace-py/issues/7104")
    @flaky(context.library >= "java@1.23.0", reason="DBMON-3088")
    def test_db_user(self):
        super().test_db_user()

    @irrelevant(context.library != "java", reason="remove this test once DBMON-3088 is fixed")
    def test_partials(self):
        """ Keep testing other operations on java"""
        super().test_db_user(excluded_operations=("select_error", "procedure"))
        super().test_db_password(excluded_operations=("select_error", "procedure"))
        super().test_db_operation(excluded_operations=("select_error", "procedure"))
        super().test_db_instance(excluded_operations=("select_error", "procedure"))
        super().test_span_kind(excluded_operations=("select_error", "procedure"))
        super().test_db_type(excluded_operations=("select_error", "procedure"))
        super().test_sql_success(excluded_operations=("select_error", "procedure"))
        super().test_sql_traces(excluded_operations=("select_error", "procedure"))
        self.test_obfuscate_query(excluded_operations=("select_error", "procedure"))

    @flaky(context.library >= "java@1.23.0", reason="DBMON-3088")
    def test_obfuscate_query(self, excluded_operations=()):
        """ All queries come out obfuscated from agent """
        for db_operation, request in self.get_requests(excluded_operations=excluded_operations):

            span = self.get_span_from_agent(request)
            # We launch all queries with two parameters (from weblog)
            if db_operation == "insert":
                expected_obfuscation_count = 1
            elif db_operation == "procedure":
                # Insert and procedure:These operations also receive two parameters, but are obfuscated as only one.
                # Nodejs: The proccedure has a input parameter, but we are calling through method `execute`` and we can't see the parameters in the traces
                expected_obfuscation_count = 0 if context.library.library == "nodejs" else 2
            else:
                expected_obfuscation_count = 2

            observed_obfuscation_count = span["meta"]["sql.query"].count("?")
            assert (
                observed_obfuscation_count == expected_obfuscation_count
            ), f"The mssql query is not properly obfuscated for operation {db_operation}, expecting {expected_obfuscation_count} obfuscation(s), found {observed_obfuscation_count}:\n {span['meta']['sql.query']}"
