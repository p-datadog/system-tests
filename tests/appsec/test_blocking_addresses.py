# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2021 Datadog, Inc.

from utils import context, coverage, interfaces, irrelevant, missing_feature, released, rfc, scenarios, weblog


@released(cpp="?", dotnet="2.27.0", php_appsec="0.7.0", python="?", nodejs="?", golang="?", ruby="1.0.0")
@coverage.basic
@scenarios.appsec_blocking
@released(
    java={
        "spring-boot": "0.110.0",
        "sprint-boot-jetty": "0.111.0",
        "spring-boot-undertow": "0.111.0",
        "spring-boot-openliberty": "0.115.0",
        "ratpack": "1.6.0",
        "jersey-grizzly2": "1.7.0",
        "resteasy-netty3": "1.7.0",
        "vertx3": "1.7.0",
        "*": "?",
    }
)
class Test_BlockingAddresses:
    """Test the addresses supported for blocking"""

    def setup_request_method(self):
        self.rm_req = weblog.request("OPTIONS")

    @missing_feature(context.library == "ruby")
    def test_request_method(self):
        """can block on server.request.method"""

        interfaces.library.assert_waf_attack(self.rm_req, rule="tst-037-006")
        assert self.rm_req.status_code == 403

    def setup_request_uri(self):
        self.ruri_req = weblog.get("/waf/foo.git")

    def test_request_uri(self):
        """can block on server.request.uri.raw"""

        interfaces.library.assert_waf_attack(self.ruri_req, rule="tst-037-002")
        assert self.ruri_req.status_code == 403

    def setup_path_params(self):
        self.pp_req = weblog.get("/params/AiKfOeRcvG45")

    @missing_feature(library="java", reason="When supported, path parameter detection happens on subsequent WAF run")
    @irrelevant(context.library == "ruby" and context.weblog_variant == "rack")
    def test_path_params(self):
        """can block on server.request.path_params"""

        interfaces.library.assert_waf_attack(self.pp_req, rule="tst-037-007")
        assert self.pp_req.status_code == 403

    def setup_request_query(self):
        self.rq_req = weblog.get("/waf", params={"foo": "xtrace"})

    def test_request_query(self):
        """can block on server.request.query"""

        interfaces.library.assert_waf_attack(self.rq_req, rule="tst-037-001")
        assert self.rq_req.status_code == 403

    def setup_cookies(self):
        self.c_req = weblog.get("/", headers={"Cookie": "mycookie=jdfoSDGFkivRG_234"})

    def test_cookies(self):
        """can block on server.request.cookies"""

        interfaces.library.assert_waf_attack(self.c_req, rule="tst-037-008")
        assert self.c_req.status_code == 403

    def setup_request_body_urlencoded(self):
        self.rbue_req = weblog.post("/waf", data={"foo": "bsldhkuqwgervf"})

    @missing_feature(context.library == "java", reason="Happens on a subsequent WAF run")
    def test_request_body_urlencoded(self):
        """can block on server.request.body (urlencoded variant)"""

        interfaces.library.assert_waf_attack(self.rbue_req, rule="tst-037-004")
        assert self.rbue_req.status_code == 403

    def setup_request_body_multipart(self):
        self.rbmp_req = weblog.post("/waf", files={"foo": (None, "bsldhkuqwgervf")})

    @missing_feature(context.library == "dotnet", reason="Don't support multipart yet")
    @missing_feature(context.library == "java", reason="Happens on a subsequent WAF run")
    def test_request_body_multipart(self):
        """can block on server.request.body (multipart/form-data variant)"""

        interfaces.library.assert_waf_attack(self.rbmp_req, rule="tst-037-004")
        assert self.rbmp_req.status_code == 403

    def setup_response_status(self):
        self.rss_req = weblog.get(path="/status", params={"code": "418"})

    @missing_feature(context.library == "dotnet", reason="only support blocking on 404 status at the moment")
    @missing_feature(context.library == "java", reason="Happens on a subsequent WAF run")
    @missing_feature(context.library < "ruby@1.10.0")
    def test_response_status(self):
        """can block on server.response.status"""

        interfaces.library.assert_waf_attack(self.rss_req, rule="tst-037-005")
        assert self.rss_req.status_code == 403

    def setup_not_found(self):
        self.rnf_req = weblog.get(path="/finger_print")

    @missing_feature(context.library == "java", reason="Happens on a subsequent WAF run")
    @missing_feature(context.library == "ruby", reason="Not working")
    def test_not_found(self):
        """can block on server.response.status"""

        interfaces.library.assert_waf_attack(self.rnf_req, rule="tst-037-010")
        assert self.rnf_req.status_code == 403

    def setup_response_header(self):
        self.rsh_req = weblog.get(path="/headers")

    @missing_feature(context.library == "java", reason="Happens on a subsequent WAF run")
    @missing_feature(context.library == "ruby")
    @missing_feature(context.library == "php", reason="Headers already sent at this stage")
    @missing_feature(context.library == "dotnet", reason="Address not supported yet")
    def test_response_header(self):
        """can block on server.response.headers.no_cookies"""

        interfaces.library.assert_waf_attack(self.rsh_req, rule="tst-037-009")
        assert self.rsh_req.status_code == 403

    @missing_feature(reason="No endpoint defined yet")
    def test_response_cookies(self):
        assert False


@rfc("https://datadoghq.atlassian.net/wiki/spaces/APS/pages/2667021177/Suspicious+requests+blocking")
@scenarios.appsec_blocking
@coverage.good
@released(
    cpp="?",
    dotnet="?",
    php_appsec="?",
    python={"django-poc": "1.10", "flask-poc": "1.10", "*": "?"},
    nodejs="?",
    golang="?",
    ruby="?",
)
class Test_Blocking_request_method:
    """Test if blocking is supported on server.request.method address"""

    def setup_blocking(self):
        self.rm_req_block = weblog.request("OPTIONS")

    def test_blocking(self):
        """Test if requests that should be blocked are blocked"""
        assert self.rm_req_block.status_code == 403
        interfaces.library.assert_waf_attack(self.rm_req_block, rule="tst-037-006")

    def setup_non_blocking(self):
        self.rm_req_nonblock = weblog.request("GET")

    def test_non_blocking(self):
        """Test if requests that should not be blocked are not blocked"""
        assert self.rm_req_nonblock.status_code == 200

    def setup_blocking_before(self):
        self.set_req1 = weblog.request("GET", path="/set_value/clean_value_3876")
        self.block_req2 = weblog.request("OPTIONS", path="/set_value/tainted_value_6512")
        self.check_req = weblog.request("GET", path="/get_value")

    def test_blocking_before(self):
        """Test that blocked requests are blocked before being processed"""
        assert self.set_req1.status_code == 200
        assert self.set_req1.content == b"Value set"
        assert self.block_req2.status_code == 403
        interfaces.library.assert_waf_attack(self.block_req2, rule="tst-037-006")
        assert self.check_req.status_code == 200
        assert self.check_req.content == b"clean_value_3876"


@rfc("https://datadoghq.atlassian.net/wiki/spaces/APS/pages/2667021177/Suspicious+requests+blocking")
@coverage.not_implemented
@released(cpp="?", dotnet="?", php_appsec="?", python="?", nodejs="?", golang="?", ruby="?")
class Test_Blocking_request_uri:
    """Test if blocking is supported on server.request.uri.raw address"""

    def test_blocking(self):
        """Test if requests that should be blocked are blocked"""
        # TODO

    def test_non_blocking(self):
        """Test if requests that should not be blocked are not blocked"""
        # TODO

    def test_blocking_before(self):
        """Test that blocked requests are blocked before being processed"""
        # TODO


@rfc("https://datadoghq.atlassian.net/wiki/spaces/APS/pages/2667021177/Suspicious+requests+blocking")
@coverage.not_implemented
@released(cpp="?", dotnet="?", php_appsec="?", python="?", nodejs="?", golang="?", ruby="?")
class Test_Blocking_request_path_params:
    """Test if blocking is supported on server.request.path_params address"""

    def test_blocking(self):
        """Test if requests that should be blocked are blocked"""
        # TODO

    def test_non_blocking(self):
        """Test if requests that should not be blocked are not blocked"""
        # TODO

    def test_blocking_before(self):
        """Test that blocked requests are blocked before being processed"""
        # TODO


@rfc("https://datadoghq.atlassian.net/wiki/spaces/APS/pages/2667021177/Suspicious+requests+blocking")
@coverage.not_implemented
@released(cpp="?", dotnet="?", php_appsec="?", python="?", nodejs="?", golang="?", ruby="?")
class Test_Blocking_request_query:
    """Test if blocking is supported on server.request.query address"""

    def test_blocking(self):
        """Test if requests that should be blocked are blocked"""
        # TODO

    def test_non_blocking(self):
        """Test if requests that should not be blocked are not blocked"""
        # TODO

    def test_blocking_before(self):
        """Test that blocked requests are blocked before being processed"""
        # TODO


@rfc("https://datadoghq.atlassian.net/wiki/spaces/APS/pages/2667021177/Suspicious+requests+blocking")
@coverage.not_implemented
@released(cpp="?", dotnet="?", php_appsec="?", python="?", nodejs="?", golang="?", ruby="?")
class Test_Blocking_request_headers:
    """Test if blocking is supported on server.request.headers.no_cookies address"""

    def test_blocking(self):
        """Test if requests that should be blocked are blocked"""
        # TODO

    def test_non_blocking(self):
        """Test if requests that should not be blocked are not blocked"""
        # TODO

    def test_blocking_before(self):
        """Test that blocked requests are blocked before being processed"""
        # TODO


@rfc("https://datadoghq.atlassian.net/wiki/spaces/APS/pages/2667021177/Suspicious+requests+blocking")
@coverage.not_implemented
@released(cpp="?", dotnet="?", php_appsec="?", python="?", nodejs="?", golang="?", ruby="?")
class Test_Blocking_request_cookies:
    """Test if blocking is supported on server.request.cookies address"""

    def test_blocking(self):
        """Test if requests that should be blocked are blocked"""
        # TODO

    def test_non_blocking(self):
        """Test if requests that should not be blocked are not blocked"""
        # TODO

    def test_blocking_before(self):
        """Test that blocked requests are blocked before being processed"""
        # TODO


@rfc("https://datadoghq.atlassian.net/wiki/spaces/APS/pages/2667021177/Suspicious+requests+blocking")
@coverage.not_implemented
@released(cpp="?", dotnet="?", php_appsec="?", python="?", nodejs="?", golang="?", ruby="?")
class Test_Blocking_request_body:
    """Test if blocking is supported on server.request.headers.body address"""

    def test_blocking(self):
        """Test if requests that should be blocked are blocked"""
        # TODO

    def test_non_blocking(self):
        """Test if requests that should not be blocked are not blocked"""
        # TODO

    def test_blocking_before(self):
        """Test that blocked requests are blocked before being processed"""
        # TODO


@rfc("https://datadoghq.atlassian.net/wiki/spaces/APS/pages/2667021177/Suspicious+requests+blocking")
@coverage.not_implemented
@released(cpp="?", dotnet="?", php_appsec="?", python="?", nodejs="?", golang="?", ruby="?")
class Test_Blocking_response_status:
    """Test if blocking is supported on server.response.status address"""

    def test_blocking(self):
        """Test if requests that should be blocked are blocked"""
        # TODO

    def test_non_blocking(self):
        """Test if requests that should not be blocked are not blocked"""
        # TODO


@rfc("https://datadoghq.atlassian.net/wiki/spaces/APS/pages/2667021177/Suspicious+requests+blocking")
@coverage.not_implemented
@released(cpp="?", dotnet="?", php_appsec="?", python="?", nodejs="?", golang="?", ruby="?")
class Test_Blocking_response_headers:
    """Test if blocking is supported on server.response.headers.no_cookies address"""

    def test_blocking(self):
        """Test if requests that should be blocked are blocked"""
        # TODO

    def test_non_blocking(self):
        """Test if requests that should not be blocked are not blocked"""
        # TODO


@rfc("https://datadoghq.atlassian.net/wiki/spaces/APS/pages/2667021177/Suspicious+requests+blocking")
@coverage.not_implemented
@released(cpp="?", dotnet="?", php_appsec="?", python="?", nodejs="?", golang="?", ruby="?")
class Test_Suspicious_Request_Blocking:
    """Test if blocking on multiple addresses with multiple rules is supported"""

    def test_blocking(self):
        """Test if requests that should be blocked are blocked"""
        # TODO

    def test_non_blocking(self):
        """Test if requests that should not be blocked are not blocked"""
        # TODO

    def test_blocking_before(self):
        """Test that blocked requests are blocked before being processed"""
        # TODO
