from moesifapi.models import *
from .parse_body import ParseBody
from .client_ip import ClientIp
from .logger_helper import LoggerHelper
from datetime import datetime


class EventMapper:

    def __init__(self):
        self.parse_body = ParseBody()
        self.client_ip = ClientIp()
        self.logger_helper = LoggerHelper()

    def to_event(self, handler, moesif_config, event_req, event_rsp, debug):
        # Prepare Event Model
        return EventModel(request=event_req,
                          response=event_rsp,
                          user_id=self.logger_helper.get_user_id(handler, moesif_config, debug),
                          company_id=self.logger_helper.get_company_id(handler, moesif_config, debug),
                          session_token=self.logger_helper.get_session_token(handler, moesif_config, debug),
                          metadata=self.logger_helper.get_metadata(handler, moesif_config, debug),
                          direction="Incoming")

    def to_request(self, handler, log_body, api_version, request_time):
        # Request headers
        req_headers = None
        if handler.request.headers:
            req_headers = dict(handler.request.headers.get_all())

        # Request body
        req_body = None
        req_transfer_encoding = None
        if log_body:
            req_body, req_transfer_encoding = self.parse_body.parse_body(handler.request.body, req_headers)

        # Prepare Event Request Model
        return EventRequestModel(time=request_time,
                                 uri=handler.request.full_url(),
                                 verb=handler.request.method,
                                 api_version=api_version,
                                 ip_address=self.client_ip.get_client_address(handler.request),
                                 headers=req_headers,
                                 body=req_body,
                                 transfer_encoding=req_transfer_encoding)

    @classmethod
    def to_response(cls, handler, response_time):
        # Response headers
        rsp_headers = None
        if handler._headers:
            rsp_headers = dict(handler._headers.get_all())

        # Response body
        rsp_body = None
        rsp_transfer_encoding = None
        # Prepare Event Response Model
        return EventResponseModel(time=response_time,
                                  status=handler.get_status(),
                                  headers=rsp_headers,
                                  body=rsp_body,
                                  transfer_encoding=rsp_transfer_encoding)
