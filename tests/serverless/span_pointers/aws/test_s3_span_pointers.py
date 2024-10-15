import json

from utils import weblog, interfaces, rfc, features
from utils.tools import logger
from tests.serverless.span_pointers.utils import (
    POINTER_DIRECTION_DOWNSTREAM,
    make_single_span_link_validator,
    standard_hashing_function,
)


def _validate_s3_object_pointer(r):
    assert r.status_code == 200

    response_content = json.loads(r.text)
    bucket = r.request.params["bucket"].encode("ascii")
    key = r.request.params["key"].encode("utf-8")
    etag = response_content["object"]["e_tag"].encode("ascii")

    assert b'"' not in etag, "boto3 sometimes includes double-quotes in etags"

    logger.info(f"bucket: {bucket}, key: {key}, etag: {etag}")

    interfaces.library.validate_spans(
        r,
        validator=make_single_span_link_validator(
            pointer_kind="aws.s3.object",
            pointer_direction=POINTER_DIRECTION_DOWNSTREAM,
            pointer_hash=standard_hashing_function([bucket, key, etag]),
        ),
        full_trace=True,
    )


@rfc("https://github.com/DataDog/dd-span-pointer-rules")
@features.serverless_span_pointers
class Test_PutObject:
    def setup_main(self):
        self.r = weblog.get("/mock_s3/put_object", params={"bucket": "mybucket", "key": "my-key"})

    def test_main(self):
        _validate_s3_object_pointer(self.r)

    def setup_non_ascii(self):
        self.r_non_ascii = weblog.get("/mock_s3/put_object", params={"bucket": "mybucket", "key": "some-key.你好"})

    def test_non_ascii(self):
        _validate_s3_object_pointer(self.r_non_ascii)
