
from moesifapi.moesif_api_client import *
from datetime import datetime, timedelta
from .app_config import AppConfig
from .logger_helper import LoggerHelper
from .event_mapper import EventMapper
from .update_users import User
from .update_companies import Company
from .send_batch_events import SendEventAsync
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
import atexit
import queue
import random
import math
import logging

class MoesifMiddleware(object):

    def __init__(self, moesif_config):
        if moesif_config is None:
            raise Exception('Moesif Application ID is required in settings')
        self.moesif_config = moesif_config

        if self.moesif_config.get('APPLICATION_ID', None):
            self.client = MoesifAPIClient(self.moesif_config.get('APPLICATION_ID'))
        else:
            raise Exception('Moesif Application ID is required in settings')

        if self.moesif_config.get('DEBUG', False):
            Configuration.BASE_URI = self.get_configuration_uri(self.moesif_config, 'BASE_URI', 'LOCAL_MOESIF_BASEURL')
        Configuration.version = 'moesiftornado-python/0.1.4'
        self.DEBUG = self.moesif_config.get('DEBUG', False)
        self.api_version = self.moesif_config.get('API_VERSION', None)
        self.api_client = self.client.api
        self.LOG_BODY = self.moesif_config.get('LOG_BODY', True)
        self.app_config = AppConfig()
        self.logger_helper = LoggerHelper()
        self.event_mapper = EventMapper()
        self.config_etag = None
        self.config = self.app_config.get_config(self.api_client, self.DEBUG)
        self.sampling_percentage = 100
        self.last_updated_time = datetime.utcnow()
        self.send_async_events = SendEventAsync()
        self.moesif_events_queue = queue.Queue()
        self.BATCH_SIZE = self.moesif_config.get('BATCH_SIZE', 25)
        self.last_event_job_run_time = datetime(1970, 1, 1, 0, 0)  # Assuming job never ran, set it to epoch start time
        self.scheduler = None
        self.is_event_job_scheduled = False
        self.user = User()
        self.company = Company()

    # Function to get configuration uri
    def get_configuration_uri(self, settings, field, deprecated_field):
        uri = settings.get(field)
        if uri:
            return uri
        else:
            return settings.get(deprecated_field, 'https://api.moesif.net')

    def process_data(self, handler, event_request_time, event_response_time):
        # Prepare Event Request Model
        event_req = self.event_mapper.to_request(handler, self.LOG_BODY, self.api_version, event_request_time)

        # Prepare Event Response Model
        event_rsp = self.event_mapper.to_response(handler, event_response_time)

        # Prepare Event Model
        event_model = self.event_mapper.to_event(handler, self.moesif_config, event_req, event_rsp, self.DEBUG)

        # Mask Event Model
        return self.logger_helper.mask_event(event_model, self.moesif_config, self.DEBUG)

    def log_event(self, handler):

        # Prepare event request and response time
        event_request_time, event_response_time = self.logger_helper.get_event_request_response_time(handler)
        # Check if need to skip logging event
        if not self.logger_helper.should_skip(handler, self.moesif_config, self.DEBUG):
            random_percentage = random.random() * 100

            self.sampling_percentage = self.app_config.get_sampling_percentage(self.config,
                                                                               self.logger_helper.get_user_id(
                                                                                   handler, self.moesif_config, self.DEBUG),
                                                                               self.logger_helper.get_company_id(
                                                                                   handler, self.moesif_config, self.DEBUG))

            if self.sampling_percentage > random_percentage:
                # Prepare event to be sent to Moesif
                event_data = self.process_data(handler, event_request_time, event_response_time)
                if event_data:
                    # Add Weight to the event
                    event_data.weight = 1 if self.sampling_percentage == 0 else math.floor(
                        100 / self.sampling_percentage)
                    try:
                        if not self.is_event_job_scheduled and datetime.utcnow() > self.last_event_job_run_time + timedelta(
                                minutes=5):
                            try:
                                self.schedule_background_job()
                                self.is_event_job_scheduled = True
                                self.last_event_job_run_time = datetime.utcnow()
                            except Exception as ex:
                                self.is_event_job_scheduled = False
                                if self.DEBUG:
                                    print('Error while starting the event scheduler job in background')
                                    print(str(ex))
                        # Add Event to the queue
                        if self.DEBUG:
                            print('Add Event to the queue')
                        self.moesif_events_queue.put(event_data)
                    except Exception as ex:
                        if self.DEBUG:
                            print("Error while adding event to the queue")
                            print(str(ex))
                else:
                    if self.DEBUG:
                        print('Skipped Event as the moesif event model is None')
            else:
                if self.DEBUG:
                    print("Skipped Event due to sampling percentage: " + str(
                        self.sampling_percentage) + " and random percentage: " + str(random_percentage))
        else:
            if self.DEBUG:
                print('Skipped Event using should_skip configuration option')

    # Function to listen to the send event job response
    def moesif_event_listener(self, event):
        if event.exception:
            if self.DEBUG:
                print('Error reading response from the scheduled job')
        else:
            if event.retval:
                response_etag, self.last_event_job_run_time = event.retval
                if response_etag is not None \
                    and self.config_etag is not None \
                    and self.config_etag != response_etag \
                        and datetime.utcnow() > self.last_updated_time + timedelta(minutes=5):
                    try:
                        self.config = self.app_config.get_config(self.api_client, self.DEBUG)
                        self.config_etag, self.sampling_percentage, self.last_updated_time = self.app_config.parse_configuration(
                            self.config, self.DEBUG)
                    except Exception as ex:
                        if self.DEBUG:
                            print('Error while updating the application configuration')
                            print(str(ex))

    def schedule_background_job(self):
        try:
            if not self.scheduler:
                self.scheduler = BackgroundScheduler(daemon=True)
            if not self.scheduler.get_jobs():
                self.scheduler.add_listener(self.moesif_event_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
                self.scheduler.start()
                self.scheduler.add_job(
                    func=lambda: self.send_async_events.batch_events(self.api_client, self.moesif_events_queue,
                                                                     self.DEBUG, self.BATCH_SIZE),
                    trigger=IntervalTrigger(seconds=2),
                    id='moesif_events_batch_job',
                    name='Schedule events batch job every 2 second',
                    replace_existing=True)

                # Avoid passing logging message to the ancestor loggers
                logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)
                logging.getLogger('apscheduler.executors.default').propagate = False

                # Exit handler when exiting the app
                atexit.register(lambda: self.send_async_events.exit_handler(self.scheduler, self.DEBUG))
        except Exception as ex:
            if self.DEBUG:
                print("Error when scheduling the job")
                print(str(ex))

    def update_user(self, user_profile):
        self.user.update_user(user_profile, self.api_client, self.DEBUG)

    def update_users_batch(self, user_profiles):
        self.user.update_users_batch(user_profiles, self.api_client, self.DEBUG)

    def update_company(self, company_profile):
        self.company.update_company(company_profile, self.api_client, self.DEBUG)

    def update_companies_batch(self, companies_profiles):
        self.company.update_companies_batch(companies_profiles, self.api_client, self.DEBUG)
