import gzip
import json
import base64
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO


class ParseBody:

    @classmethod
    def start_with_json(cls, body):
        return body.startswith("{") or body.startswith("[")

    @classmethod
    def transform_headers(cls, headers):
        return {k.lower(): v for k, v in headers.items()}

    @classmethod
    def base64_body(cls, body):
        return base64.standard_b64encode(body).decode(encoding="UTF-8"), "base64"

    def parse_body(self, body, headers):
        try:
            if self.start_with_json(body):
                parsed_body = json.loads(body)
                transfer_encoding = 'json'
            elif (headers is not None and "content-encoding" in headers and headers["content-encoding"] is not None
                  and "gzip" in (headers["content-encoding"]).lower()):
                decompressed_body = gzip.GzipFile(fileobj=StringIO(body)).read()
                if self.start_with_json(decompressed_body):
                    parsed_body = json.loads(decompressed_body)
                    transfer_encoding = 'json'
                else:
                    parsed_body, transfer_encoding = self.base64_body(decompressed_body)
            else:
                parsed_body, transfer_encoding = self.base64_body(body)
        except:
            parsed_body, transfer_encoding = self.base64_body(body)
        return parsed_body, transfer_encoding
