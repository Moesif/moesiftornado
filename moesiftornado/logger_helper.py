try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO
from .parse_body import ParseBody
from datetime import datetime, timedelta


class LoggerHelper:

    def __init__(self):
        self.parse_body = ParseBody()

    @classmethod
    def get_event_request_response_time(cls, handler):
        request_time = datetime.utcnow()
        response_time = request_time + timedelta(seconds=handler.request.request_time())
        return request_time.strftime("%Y-%m-%dT%H:%M:%S.%f"), response_time.strftime("%Y-%m-%dT%H:%M:%S.%f")

    @classmethod
    def get_user_id(cls, handler, moesif_config, debug):
        user_id = None
        try:
            if 'IDENTIFY_USER' in moesif_config:
                user_id = moesif_config['IDENTIFY_USER'](handler)
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
