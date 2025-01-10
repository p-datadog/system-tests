import base64
import json
import logging
import os
import random
import subprocess
import sys
import typing

import fastapi
from fastapi import Cookie
from fastapi import FastAPI
from fastapi import Form
from fastapi import Header
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.responses import PlainTextResponse
from iast import weak_cipher
from iast import weak_cipher_secure_algorithm
from iast import weak_hash
from iast import weak_hash_duplicates
from iast import weak_hash_multiple
from iast import weak_hash_secure_algorithm
import psycopg2
from pydantic import BaseModel
import requests
import urllib3
import xmltodict

import ddtrace
from ddtrace import Pin
from ddtrace import patch_all
from ddtrace import tracer
from ddtrace.appsec import trace_utils as appsec_trace_utils


patch_all(urllib3=True)

tracer.trace("init.service").finish()
logger = logging.getLogger(__name__)

try:
    from ddtrace.contrib.trace_utils import set_user
except ImportError:
    set_user = lambda *args, **kwargs: None  # noqa E731

app = FastAPI()

POSTGRES_CONFIG = dict(
    host="postgres",
    port="5433",
    user="system_tests_user",
    password="system_tests",
    dbname="system_tests_dbname",
)
_TRACK_CUSTOM_APPSEC_EVENT_NAME = "system_tests_appsec_event"


@app.exception_handler(404)
async def custom_404_handler(request: Request, _):
    logger.critical("request %s failed with 404", request.url)
    return JSONResponse({"error": 404}, status_code=404)


@app.get("/", response_class=PlainTextResponse)
@app.post("/", response_class=PlainTextResponse)
@app.options("/", response_class=PlainTextResponse)
async def root():
    return "Hello, World!"


@app.get("/healthcheck")
async def healthcheck():
    return {
        "status": "ok",
        "library": {
            "language": "python",
            "version": ddtrace.__version__,
        },
    }


@app.get("/set_cookie", response_class=PlainTextResponse)
async def set_cookie(request: Request):
    return PlainTextResponse(
        "OK", headers={"Set-Cookie": f"{request.query_params['name']}={request.query_params['value']}"}
    )


@app.post("/iast/header_injection/test_insecure", response_class=PlainTextResponse)
async def iast_header_injection_insecure(request: Request):
    form_data = await request.form()
    header_value = form_data.get("test")
    response = PlainTextResponse("OK")
    # label iast_header_injection
    response.headers["Header-Injection"] = header_value
    return response


@app.post("/iast/header_injection/test_secure", response_class=PlainTextResponse)
async def iast_header_injection_secure(request: Request):
    form_data = await request.form()
    header_value = form_data.get("test")
    response = PlainTextResponse("OK")
    # label iast_header_injection
    response.headers["Vary"] = header_value
    return response


@app.get("/sample_rate_route/{i}", response_class=PlainTextResponse)
async def sample_rate(i):
    return "OK"


@app.get("/api_security_sampling/{i}", response_class=PlainTextResponse)
async def api_security_sampling(i):
    return "OK"


@app.get("/api_security/sampling/{status_code}", response_class=PlainTextResponse)
async def api_security_sampling_status(status_code: int = 200):
    return PlainTextResponse("Hello!", status_code=status_code)


@app.get("/waf", response_class=PlainTextResponse)
@app.post("/waf", response_class=PlainTextResponse)
@app.options("/waf", response_class=PlainTextResponse)
@app.get("/waf/", response_class=PlainTextResponse)
@app.post("/waf/", response_class=PlainTextResponse)
@app.options("/waf/", response_class=PlainTextResponse)
async def waf():
    return "Hello, World!\n"


@app.get("/waf/{path}", response_class=PlainTextResponse)
@app.post("/waf/{path}", response_class=PlainTextResponse)
@app.options("/waf/{path}", response_class=PlainTextResponse)
@app.get("/params/{path}", response_class=PlainTextResponse)
@app.post("/params/{path}", response_class=PlainTextResponse)
@app.options("/params/{path}", response_class=PlainTextResponse)
async def waf_params(path):
    return "Hello, World!\n"


@app.get("/tag_value/{tag_value}/{status_code}", response_class=PlainTextResponse)
@app.options("/tag_value/{tag_value}/{status_code}", response_class=PlainTextResponse)
async def tag_value(tag_value: str, status_code: int, request: Request):
    appsec_trace_utils.track_custom_event(
        tracer, event_name=_TRACK_CUSTOM_APPSEC_EVENT_NAME, metadata={"value": tag_value}
    )
    return PlainTextResponse("Value tagged", status_code=status_code, headers=request.query_params)


@app.post("/tag_value/{tag_value}/{status_code}")
async def tag_value_post(tag_value: str, status_code: int, request: Request):
    appsec_trace_utils.track_custom_event(
        tracer, event_name=_TRACK_CUSTOM_APPSEC_EVENT_NAME, metadata={"value": tag_value}
    )
    if tag_value.startswith("payload_in_response_body"):
        return JSONResponse(
            {"payload": dict(await request.form())},
            status_code=status_code,
            headers=request.query_params,
        )
    return PlainTextResponse("Value tagged", status_code=status_code, headers=request.query_params)


### BEGIN EXPLOIT PREVENTION


@app.get("/rasp/lfi")
@app.post("/rasp/lfi")
async def rasp_lfi(request: Request):
    file = None
    if request.method == "GET":
        file = request.query_params.get("file")
    elif request.method == "POST":
        body = await request.body()
        try:
            file = ((await request.form()) or json.loads(body) or {}).get("file")
        except Exception as e:
            print(repr(e), file=sys.stderr)
        try:
            if file is None:
                file = xmltodict.parse(body).get("file")
        except Exception as e:
            print(repr(e), file=sys.stderr)
            pass
    if file is None:
        return PlainTextResponse("missing file parameter", status_code=400)
    try:
        with open(file, "rb") as f_in:
            f_in.seek(0, os.SEEK_END)
            return PlainTextResponse(f"{file} open with {f_in.tell()} bytes")
    except OSError as e:
        return PlainTextResponse(f"{file} could not be open: {e!r}")


@app.get("/rasp/ssrf")
@app.post("/rasp/ssrf")
async def rasp_ssrf(request: Request):
    domain = None
    if request.method == "GET":
        domain = request.query_params.get("domain")
    elif request.method == "POST":
        body = await request.body()
        try:
            domain = ((await request.form()) or json.loads(body) or {}).get("domain")
        except Exception as e:
            print(repr(e), file=sys.stderr)
        try:
            if domain is None:
                domain = xmltodict.parse(body).get("domain")
        except Exception as e:
            print(repr(e), file=sys.stderr)
            pass

    if domain is None:
        return PlainTextResponse("missing domain parameter", status_code=400)
    try:
        print("rasp_ssrf", f"http://{domain}", file=sys.stderr)
        # DEV: use requests here due to permission error with urllib
        with requests.get(f"http://{domain}", timeout=1) as url_in:
            return PlainTextResponse(f"url http://{domain} open with {len(url_in.read())} bytes")
    except Exception as e:
        print(repr(e), file=sys.stderr)
        return PlainTextResponse(f"url http://{domain} could not be open: {e!r}")


@app.get("/rasp/sqli")
@app.post("/rasp/sqli")
async def rasp_sqli(request: Request):
    user_id = None
    if request.method == "GET":
        user_id = request.query_params.get("user_id")
    elif request.method == "POST":
        body = await request.body()
        try:
            user_id = ((await request.form()) or json.loads(body) or {}).get("user_id")
        except Exception as e:
            print(repr(e), file=sys.stderr)
        try:
            if user_id is None:
                user_id = xmltodict.parse(body).get("user_id")
        except Exception as e:
            print(repr(e), file=sys.stderr)
            pass

    if user_id is None:
        return PlainTextResponse("missing user_id parameter", status_code=400)
    try:
        import sqlite3

        DB = sqlite3.connect(":memory:")
        print(f"SELECT * FROM users WHERE id='{user_id}'")
        cursor = DB.execute(f"SELECT * FROM users WHERE id='{user_id}'")
        print("DB request with {len(list(cursor))} results")
        return PlainTextResponse(f"DB request with {len(list(cursor))} results")
    except Exception as e:
        print(f"DB request failure: {e!r}", file=sys.stderr)
        return PlainTextResponse(f"DB request failure: {e!r}", status_code=201)


@app.get("/rasp/shi")
@app.post("/rasp/shi")
async def rasp_shi(request: Request):
    list_dir = None
    if request.method == "GET":
        list_dir = request.query_params.get("list_dir")
    elif request.method == "POST":
        body = await request.body()
        try:
            list_dir = ((await request.form()) or json.loads(body) or {}).get("list_dir")
        except Exception as e:
            print(repr(e), file=sys.stderr)
        try:
            if list_dir is None:
                list_dir = xmltodict.parse(body).get("list_dir")
        except Exception as e:
            print(repr(e), file=sys.stderr)
            pass

    if list_dir is None:
        return PlainTextResponse("missing list_dir parameter", status_code=400)
    try:
        command = f"ls {list_dir}"
        res = os.system(command)
        return PlainTextResponse(f"Shell command [{command}] with result: {res}")
    except Exception as e:
        print(f"Shell command failure: {e!r}", file=sys.stderr)
        return PlainTextResponse(f"Shell command failure: {e!r}", status_code=201)


@app.get("/rasp/cmdi")
@app.post("/rasp/cmdi")
async def rasp_cmdi(request: Request):
    cmd = None
    if request.method == "GET":
        cmd = request.query_params.get("command")
    elif request.method == "POST":
        body = await request.body()
        try:
            cmd = ((await request.form()) or json.loads(body) or {}).get("command")
        except Exception as e:
            print(repr(e), file=sys.stderr)
        try:
            if cmd is None:
                cmd = xmltodict.parse(body).get("command").get("cmd")
        except Exception as e:
            print(repr(e), file=sys.stderr)
            pass

    if cmd is None:
        return PlainTextResponse("missing command parameter", status_code=400)
    try:
        res = subprocess.run(cmd, capture_output=True)
        return PlainTextResponse(f"Exec command [{cmd}] with result: {res}")
    except Exception as e:
        return PlainTextResponse(f"Exec command [{cmd}] failure: {e!r}", status_code=201)


### END EXPLOIT PREVENTION


@app.get("/read_file", response_class=PlainTextResponse)
async def read_file(file: typing.Optional[str] = None):
    if file is None:
        return PlainTextResponse("Please provide a file parameter", status_code=400)
    with open(file, "r") as f:
        return f.read()


@app.get("/headers")
async def headers():
    return PlainTextResponse("OK", headers={"Content-Language": "en-US"})


@app.get("/status")
async def status_code(code: int = 200):
    return PlainTextResponse("OK, probably", status_code=code)


@app.get("/stats-unique")
async def stats_unique(code: int = 200):
    return PlainTextResponse("OK, probably", status_code=code)


@app.get("/make_distant_call")
def make_distant_call(url: str):
    response = requests.get(url)

    result = {
        "url": url,
        "status_code": response.status_code,
        "request_headers": dict(response.request.headers),
        "response_headers": dict(response.headers),
    }

    return result


@app.get("/identify", response_class=PlainTextResponse)
def identify():
    set_user(
        tracer,
        user_id="usr.id",
        email="usr.email",
        name="usr.name",
        session_id="usr.session_id",
        role="usr.role",
        scope="usr.scope",
    )
    return "OK"


@app.get("/identify-propagate", response_class=PlainTextResponse)
def identify_propagate():
    set_user(
        tracer,
        user_id="usr.id",
        email="usr.email",
        name="usr.name",
        session_id="usr.session_id",
        role="usr.role",
        scope="usr.scope",
        propagate=True,
    )
    return "OK"


@app.get("/users", response_class=PlainTextResponse)
def users(user: str):
    set_user(
        tracer,
        user_id=user,
        email="usr.email",
        name="usr.name",
        session_id="usr.session_id",
        role="usr.role",
        scope="usr.scope",
    )
    return "OK"


@app.get("/dbm", response_class=PlainTextResponse)
def dbm(integration: str, operation: str = ""):
    if integration == "psycopg":
        postgres_db = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = postgres_db.cursor()
        if operation == "execute":
            cursor.execute("select 'blah'")
            return "OK"
        elif operation == "executemany":
            cursor.executemany("select %s", (("blah",), ("moo",)))
            return "OK"
        return PlainTextResponse(f"Cursor method is not supported: {operation}", status_code=406)

    return PlainTextResponse(f"Integration is not supported: {integration}", status_code=406)


@app.get("/iast/insecure_hashing/multiple_hash", response_class=PlainTextResponse)
def view_weak_hash_multiple_hash():
    weak_hash_multiple()
    return "OK"


@app.get("/iast/insecure_hashing/test_secure_algorithm", response_class=PlainTextResponse)
def view_weak_hash_secure_algorithm():
    _ = weak_hash_secure_algorithm()
    return "OK"


@app.get("/iast/insecure_hashing/test_md5_algorithm", response_class=PlainTextResponse)
def view_weak_hash_md5_algorithm():
    _ = weak_hash()
    return "OK"


@app.get("/iast/insecure_hashing/deduplicate", response_class=PlainTextResponse)
def view_weak_hash_deduplicate():
    weak_hash_duplicates()
    return "OK"


@app.get("/iast/insecure_cipher/test_insecure_algorithm", response_class=PlainTextResponse)
def view_weak_cipher_insecure():
    weak_cipher()
    return "OK"


@app.get("/iast/insecure_cipher/test_secure_algorithm", response_class=PlainTextResponse)
def view_weak_cipher_secure():
    weak_cipher_secure_algorithm()
    return "OK"


def _sink_point(table="user", id="1"):  # noqa: A002
    sql = "SELECT * FROM " + table + " WHERE id = '" + id + "'"
    postgres_db = psycopg2.connect(**POSTGRES_CONFIG)
    cursor = postgres_db.cursor()
    try:
        cursor.execute(sql)
    except psycopg2.errors.UndefinedColumn:
        pass


def _sink_point_path_traversal(tainted_str="user"):
    try:
        m = open(tainted_str)
        _ = m.read()
    except Exception:
        pass


class Body_for_iast(BaseModel):
    table: str
    user: str


@app.post("/iast/source/body/test", response_class=PlainTextResponse)
async def view_iast_source_body(request: Request):
    body = await request.receive()

    result = body["body"]

    json_body = json.loads(result)

    _sink_point_path_traversal(json_body["value"])
    return "OK"


@app.get("/iast/source/cookiename/test", response_class=PlainTextResponse)
async def view_iast_source_cookie_name(request: Request):
    param = [key for key in request.cookies if key == "table"]
    if param:
        _sink_point_path_traversal(tainted_str=param[0])
        return "OK"
    return "KO"


@app.get("/iast/source/cookievalue/test", response_class=PlainTextResponse)
async def view_iast_source_cookie_value(table: typing.Annotated[str, Cookie()] = "undefined"):
    _sink_point_path_traversal(tainted_str=table)
    return "OK"


@app.get("/iast/source/header/test", response_class=PlainTextResponse)
async def view_iast_source_header_value(table: typing.Annotated[str, Header()] = "undefined"):
    _sink_point_path_traversal(tainted_str=table)
    return "OK"


@app.get("/iast/source/parametername/test", response_class=PlainTextResponse)
async def view_iast_source_parametername_get(request: Request):
    param = [key for key in request.query_params if key == "user"]
    if param:
        _sink_point(id=param[0])
        return "OK"
    return "KO"


@app.post("/iast/source/parametername/test", response_class=PlainTextResponse)
async def view_iast_source_parametername_post(request: Request):
    json_body = await request.form()
    param = [key for key in json_body if key == "user"]
    if param:
        _sink_point(id=param[0])
        return "OK"
    return "KO"


@app.get("/iast/source/parameter/test", response_class=PlainTextResponse)
@app.post("/iast/source/parameter/test", response_class=PlainTextResponse)
async def view_iast_source_parameter(request: Request, table: typing.Optional[str] = None):
    if table is None:
        json_body = await request.form()
        table = json_body.get("table")
    _sink_point(table=table)
    return "OK"


@app.post("/iast/path_traversal/test_insecure", response_class=PlainTextResponse)
async def view_iast_path_traversal_insecure(path: typing.Annotated[str, Form()]):
    try:
        os.mkdir(path)
    except FileExistsError:
        pass

    return "OK"


@app.get("/iast/source/path/test", response_class=PlainTextResponse)
async def view_iast_source_path(request: Request):
    _sink_point_path_traversal(tainted_str=request.url.path)
    return "OK"


@app.get("/iast/source/path_parameter/test/{table}", response_class=PlainTextResponse)
async def view_iast_source_path(table):
    _sink_point_path_traversal(tainted_str=table)
    return "OK"


@app.post("/iast/path_traversal/test_secure", response_class=PlainTextResponse)
def view_iast_path_traversal_secure(path: typing.Annotated[str, Form()]):
    root_dir = "/home/usr/secure_folder/"

    if os.path.commonprefix((os.path.realpath(path), root_dir)) == root_dir:
        open(path)

    return "OK"


_TRACK_METADATA = {
    "metadata0": "value0",
    "metadata1": "value1",
}


_TRACK_USER = "system_tests_user"


@app.get("/user_login_success_event", response_class=PlainTextResponse)
def track_user_login_success_event():
    appsec_trace_utils.track_user_login_success_event(tracer, user_id=_TRACK_USER, metadata=_TRACK_METADATA)
    return "OK"


@app.get("/user_login_failure_event", response_class=PlainTextResponse)
def track_user_login_failure_event():
    appsec_trace_utils.track_user_login_failure_event(
        tracer,
        user_id=_TRACK_USER,
        exists=True,
        metadata=_TRACK_METADATA,
    )
    return "OK"


@app.get("/login")
@app.post("/login")
async def login(request: Request):
    # FakeDB
    DB_USER = {
        "test": ("social-security-id", "test", "1234", "testuser@ddog.com"),
        "testuuid": ("591dc126-8431-4d0f-9509-b23318d3dce4", "testuuid", "1234", "testuseruuid@ddog.com"),
    }

    def check(username, password):
        if username in DB_USER:
            return (DB_USER[username][2] == password), DB_USER[username][0]
        return False, None

    form = (await request.form()) or {}

    username = form.get("username")
    password = form.get("password")
    sdk_event = request.query_params.get("sdk_event")
    if sdk_event:
        sdk_user = request.query_params.get("sdk_user")
        sdk_mail = request.query_params.get("sdk_mail")
        sdk_user_exists = request.query_params.get("sdk_user_exists")
        if sdk_event == "success":
            appsec_trace_utils.track_user_login_success_event(tracer, user_id=sdk_user, email=sdk_mail)
            return PlainTextResponse("OK")
        elif sdk_event == "failure":
            appsec_trace_utils.track_user_login_failure_event(
                tracer, user_id=sdk_user, email=sdk_mail, exists=sdk_user_exists
            )
            return PlainTextResponse("login failure", status_code=401)
    authorisation = request.headers.get("Authorization")
    if authorisation:
        username, password = base64.b64decode(authorisation[6:]).decode().split(":")
    success, user_id = check(username, password)
    if success:
        # login_user(user)
        appsec_trace_utils.track_user_login_success_event(tracer, user_id=user_id, login_events_mode="auto")
        return PlainTextResponse("OK")
    elif user_id:
        appsec_trace_utils.track_user_login_failure_event(
            tracer,
            user_id=user_id,
            exists=True,
            login_events_mode="auto",
        )
    else:
        appsec_trace_utils.track_user_login_failure_event(
            tracer, user_id=username, exists=False, login_events_mode="auto"
        )
    return PlainTextResponse("login failure", status_code=401)


MAGIC_SESSION_KEY = "random_session_id"


@app.get("/session/new")
async def session_new(request: Request):
    response = PlainTextResponse("OK")
    response.set_cookie(key="session_id", value=MAGIC_SESSION_KEY)
    return response


@app.get("/session/user")
async def session_user(request: Request):
    user = request.query_params.get("sdk_user", "")
    if user and request.cookies.get("session_id", "") == MAGIC_SESSION_KEY:
        appsec_trace_utils.track_user_login_success_event(tracer, user_id=user, session_id=f"session_{user}")
    return PlainTextResponse("OK")


_TRACK_CUSTOM_EVENT_NAME = "system_tests_event"


@app.get("/custom_event", response_class=PlainTextResponse)
def track_custom_event():
    appsec_trace_utils.track_custom_event(tracer, event_name=_TRACK_CUSTOM_EVENT_NAME, metadata=_TRACK_METADATA)
    return "OK"


@app.post("/iast/sqli/test_secure", response_class=PlainTextResponse)
async def view_sqli_secure(username: typing.Annotated[str, Form()], password: typing.Annotated[str, Form()]):
    sql = "SELECT * FROM users WHERE username=%s AND password=%s"
    postgres_db = psycopg2.connect(**POSTGRES_CONFIG)
    cursor = postgres_db.cursor()
    try:
        cursor.execute(sql, (username, password))
    except psycopg2.errors.UndefinedTable:
        pass
    return "OK"


@app.post("/iast/sqli/test_insecure", response_class=PlainTextResponse)
async def view_sqli_insecure(username: typing.Annotated[str, Form()], password: typing.Annotated[str, Form()]):
    sql = "SELECT * FROM users WHERE username='" + username + "' AND password='" + password + "'"
    postgres_db = psycopg2.connect(**POSTGRES_CONFIG)
    cursor = postgres_db.cursor()
    try:
        cursor.execute(sql)
    except psycopg2.errors.UndefinedTable:
        pass
    return "OK"


@app.post("/iast/ssrf/test_insecure", response_class=PlainTextResponse)
async def view_iast_ssrf_insecure(url: typing.Annotated[str, Form()]):
    try:
        result = requests.get(str(url))
    except Exception:
        pass

    return "OK"


@app.post("/iast/ssrf/test_secure", response_class=PlainTextResponse)
async def view_iast_ssrf_secure(url: typing.Annotated[str, Form()]):
    from urllib.parse import urlparse

    # Validate the URL and enforce whitelist
    allowed_domains = ["example.com", "api.example.com"]
    parsed_url = urlparse(str(url))

    if parsed_url.hostname not in allowed_domains:
        return PlainTextResponse("Forbidden", status_code=403)
    try:
        result = requests.get(parsed_url.geturl())
    except Exception:
        pass

    return "OK"


@app.get("/iast/insecure-cookie/test_insecure")
async def test_insecure_cookie():
    resp = PlainTextResponse("OK")
    resp.set_cookie("insecure", "cookie", secure=False, httponly=False, samesite="none")
    return resp


@app.get("/iast/insecure-cookie/test_secure")
def test_secure_cookie():
    resp = PlainTextResponse("OK")
    resp.set_cookie(key="secure3", value="value", secure=True, httponly=True, samesite="strict")
    return resp


@app.get("/iast/insecure-cookie/test_empty_cookie")
def test_empty_cookie():
    resp = PlainTextResponse("OK")
    resp.set_cookie(key="secure3", value="", secure=True, httponly=True, samesite="strict")
    return resp


@app.get("/iast/no-httponly-cookie/test_insecure")
def test_nohttponly_insecure_cookie():
    resp = PlainTextResponse("OK")
    resp.set_cookie("insecure", "cookie", secure=True, httponly=False, samesite="strict")
    return resp


@app.get("/iast/no-httponly-cookie/test_secure")
def test_nohttponly_secure_cookie():
    resp = PlainTextResponse("OK")
    resp.set_cookie(key="secure3", value="value", secure=True, httponly=True, samesite="strict")
    return resp


@app.get("/iast/no-httponly-cookie/test_empty_cookie")
def test_nohttponly_empty_cookie():
    resp = PlainTextResponse("OK")
    resp.set_cookie(key="secure3", value="", secure=True, httponly=True, samesite="strict")
    return resp


@app.get("/iast/no-samesite-cookie/test_insecure")
def test_nosamesite_insecure_cookie():
    resp = PlainTextResponse("OK")
    resp.set_cookie("insecure", "cookie", secure=True, httponly=True, samesite="none")
    return resp


@app.get("/iast/no-samesite-cookie/test_secure")
def test_nosamesite_secure_cookie():
    resp = PlainTextResponse("OK")
    resp.set_cookie(key="secure3", value="value", secure=True, httponly=True, samesite="strict")
    return resp


@app.get("/iast/no-samesite-cookie/test_empty_cookie")
def test_nohttponly_empty_cookie():
    resp = PlainTextResponse("OK")
    resp.set_cookie(key="secure3", value="", secure=True, httponly=True, samesite="none")
    return resp


@app.get("/iast/weak_randomness/test_insecure", response_class=PlainTextResponse)
def test_weak_randomness_insecure():
    _ = random.randint(1, 100)
    return "OK"


@app.get("/iast/weak_randomness/test_secure", response_class=PlainTextResponse)
def test_weak_randomness_secure():
    random_secure = random.SystemRandom()
    _ = random_secure.randint(1, 100)
    return "OK"


@app.post("/iast/cmdi/test_insecure", response_class=PlainTextResponse)
async def view_cmdi_insecure(cmd: typing.Annotated[str, Form()]):
    filename = "/"

    subp = subprocess.Popen(args=[cmd, "-la", filename])
    subp.communicate()
    subp.wait()
    return "OK"


@app.post("/iast/cmdi/test_secure", response_class=PlainTextResponse)
async def view_cmdi_secure(cmd: typing.Annotated[str, Form()]):
    filename = "/"
    command = " ".join([cmd, "-la", filename])  # noqa F841
    # TODO: add secure command
    # subp = subprocess.check_output(command, shell=False)
    # subp.communicate()
    # subp.wait()
    return "OK"


# @app.get("/db", response_class=PlainTextResponse)
# @app.post("/db", response_class=PlainTextResponse)
# @app.options("/db", response_class=PlainTextResponse)
# def db(service: str, operation: str):
#     if service == "postgresql":
#         executePostgresOperation(operation)
#     elif service == "mysql":
#         executeMysqlOperation(operation)
#     elif service == "mssql":
#         executeMssqlOperation(operation)
#     else:
#         print(f"SERVICE NOT SUPPORTED: {service}")
#     return "YEAH"


@app.get("/createextraservice", response_class=PlainTextResponse)
def create_extra_service(serviceName: str = ""):
    if serviceName:
        Pin.override(fastapi, service=serviceName, tracer=tracer)
    return "OK"


@app.get("/requestdownstream", response_class=PlainTextResponse)
@app.post("/requestdownstream", response_class=PlainTextResponse)
@app.options("/requestdownstream", response_class=PlainTextResponse)
@app.get("/requestdownstream/", response_class=PlainTextResponse)
@app.post("/requestdownstream/", response_class=PlainTextResponse)
@app.options("/requestdownstream/", response_class=PlainTextResponse)
def request_downstream():
    http_ = urllib3.PoolManager()
    # Sending a GET request and getting back response as HTTPResponse object.
    response = http_.request("GET", "http://localhost:7777/returnheaders")
    return response.data


@app.get("/vulnerablerequestdownstream", response_class=PlainTextResponse)
@app.post("/vulnerablerequestdownstream", response_class=PlainTextResponse)
@app.options("/vulnerablerequestdownstream", response_class=PlainTextResponse)
@app.get("/vulnerablerequestdownstream/", response_class=PlainTextResponse)
@app.post("/vulnerablerequestdownstream/", response_class=PlainTextResponse)
@app.options("/vulnerablerequestdownstream/", response_class=PlainTextResponse)
def vulnerable_request_downstream():
    weak_hash()
    http_ = urllib3.PoolManager()
    # Sending a GET request and getting back response as HTTPResponse object.
    response = http_.request("GET", "http://localhost:7777/returnheaders")
    return response.data


@app.get("/returnheaders", response_class=PlainTextResponse)
@app.post("/returnheaders", response_class=PlainTextResponse)
@app.options("/returnheaders", response_class=PlainTextResponse)
@app.get("/returnheaders/", response_class=PlainTextResponse)
@app.post("/returnheaders/", response_class=PlainTextResponse)
@app.options("/returnheaders/", response_class=PlainTextResponse)
def return_headers(request: Request):
    headers = {}
    for key, value in request.headers.items():
        headers[key] = value
    return JSONResponse(headers)
