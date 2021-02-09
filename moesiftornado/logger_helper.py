try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO
from .parse_body import ParseBody
from datetime import datetime, timedelta
import json
import base64


class LoggerHelper:

    def __init__(self):
        self.parse_body = ParseBody()

    @classmethod
    def get_event_request_response_time(cls, handler):
        request_time = datetime.utcnow()
        response_time = request_time + timedelta(seconds=handler.request.request_time())
        return request_time.strftime("%Y-%m-%dT%H:%M:%S.%f"), response_time.strftime("%Y-%m-%dT%H:%M:%S.%f")

    @classmethod
    def transform_token(cls, token):
        if not isinstance(token, str):
            token = token.decode('utf-8')
        return token

    @classmethod
    def fetch_token(cls, token, token_type):
        return token.split(token_type, 1)[1].strip()

    @classmethod
    def split_token(cls, token):
        return token.split('.')

    def parse_authorization_header(self, token, field, debug):
        try:
            # Fix the padding issue before decoding
            token += '=' * (-len(token) % 4)
            # Decode the payload
            base64_decode = base64.b64decode(token)
            # Transform token to string to be compatible with Python 2 and 3
            base64_decode = self.transform_token(base64_decode)
            # Convert the payload to json
            json_decode = json.loads(base64_decode)
            # Convert keys to lowercase
            json_decode = {k.lower(): v for k, v in json_decode.items()}
            # Check if field is present in the body
            if field in json_decode:
                # Fetch user Id
                return str(json_decode[field])
        except Exception as e:
            if debug:
                print("Error while parsing authorization header to fetch user id.")
                print(e)
        return None

    def get_user_id(self, handler, moesif_config, debug):
        user_id = None
        try:
            if 'IDENTIFY_USER' in moesif_config:
                user_id = moesif_config['IDENTIFY_USER'](handler)
            if not user_id:
                # Request headers
                request_headers = {}
                if handler.request.headers:
                    request_headers = dict([(k.lower(), v) for k, v in handler.request.headers.get_all()])
                # Fetch the auth header name from the config
                auth_header_names = moesif_config.get('AUTHORIZATION_HEADER_NAME', 'authorization').lower()
                # Split authorization header name by comma
                auth_header_names = [x.strip() for x in auth_header_names.split(',')]
                # Fetch the header name available in the request header
                token = None
                for auth_name in auth_header_names:
                    # Check if the auth header name in request headers
                    if auth_name in request_headers:
                        # Fetch the token from the request headers
                        token = request_headers[auth_name]
                        # Split the token by comma
                        token = [x.strip() for x in token.split(',')]
                        # Fetch the first available header
                        if len(token) >= 1:
                            token = token[0]
                        else:
                            token = None
                        break
                # Fetch the field from the config
                field = moesif_config.get('AUTHORIZATION_USER_ID_FIELD', 'sub').lower()
                # Check if token is not None
                if token:
                    # Check if token is of type Bearer
                    if 'Bearer' in token:
                        # Fetch the bearer token
                        token = self.fetch_token(token, 'Bearer')
                        # Split the bearer token by dot(.)
                        split_token = self.split_token(token)
                        # Check if payload is not None
                        if len(split_token) >= 3 and split_token[1]:
                            # Parse and set user Id
                            user_id = self.parse_authorization_header(split_token[1], field, debug)
                    # Check if token is of type Basic
                    elif 'Basic' in token:
                        # Fetch the basic token
                        token = self.fetch_token(token, 'Basic')
                        # Decode the token
                        decoded_token = base64.b64decode(token)
                        # Transform token to string to be compatible with Python 2 and 3
                        decoded_token = self.transform_token(decoded_token)
                        # Fetch the username and set the user Id
                        user_id = decoded_token.split(':', 1)[0].strip()
                    # Check if token is of user-defined custom type
                    else:
                        # Split the token by dot(.)
                        split_token = self.split_token(token)
                        # Check if payload is not None
                        if len(split_token) > 1 and split_token[1]:
                            # Parse and set user Id
                            user_id = self.parse_authorization_header(split_token[1], field, debug)
                        else:
                            # Parse and set user Id
                            user_id = self.parse_authorization_header(token, field, debug)
        except Exception as e:
            if debug:
                print("can not execute identify_user function, please check moesif settings.")
                print(e)
        return user_id

    @classmethod
    def get_company_id(cls, handler, moesif_config, debug):
        company_id = None
        try:
            if 'IDENTIFY_COMPANY' in moesif_config:
                company_id = moesif_config['IDENTIFY_COMPANY'](handler)
        except Exception as e:
            if debug:
                print("can not execute identify_company function, please check moesif settings.")
                print(e)
        return company_id

    @classmethod
    def get_metadata(cls, handler, moesif_config, debug):
        metadata = None
        try:
            if 'GET_METADATA' in moesif_config:
                metadata = moesif_config['GET_METADATA'](handler)
        except Exception as e:
            if debug:
                print("can not execute get_metadata function, please check moesif settings.")
                print(e)
        return metadata

    @classmethod
    def get_session_token(cls, handler, moesif_config, debug):
        session_token = None
        try:
            if 'GET_SESSION_TOKEN' in moesif_config:
                session_token = moesif_config['GET_SESSION_TOKEN'](handler)
        except Exception as e:
            if debug:
                print("can not execute get_session_token function, please check moesif settings.")
                print(e)
        return session_token

    @classmethod
    def get_api_version(cls, handler, moesif_config, debug):
        api_version = None
        try:
            if 'API_VERSION' in moesif_config:
                api_version = moesif_config['API_VERSION'](handler)
        except Exception as e:
            if debug:
                print("can not execute api_version function, please check moesif settings.")
                print(e)
        return api_version

    @classmethod
    def should_skip(cls, handler, moesif_config, debug):
        try:
            if 'SKIP' in moesif_config:
                return moesif_config['SKIP'](handler)
        except Exception as e:
            if debug:
                print("can not execute skip function, please check moesif settings.")
                print(e)
        return False

    @classmethod
    def mask_event(cls, event_model, moesif_config, debug):
        try:
            if 'MASK_EVENT_MODEL' in moesif_config:
                return moesif_config['MASK_EVENT_MODEL'](event_model)
        except Exception as e:
            if debug:
                print("Can not execute MASK_EVENT_MODEL function, please check moesif settings.")
                print(e)
        return event_model
