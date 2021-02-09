# Moesif Middleware for Python Tornado based Frameworks

[![Built For][ico-built-for]][link-built-for]
[![Latest Version][ico-version]][link-package]
[![Language Versions][ico-language]][link-language]
[![Software License][ico-license]][link-license]
[![Source Code][ico-source]][link-source]

Tornado middleware that automatically logs _incoming_ API calls and sends to [Moesif](https://www.moesif.com) for API analytics and monitoring.
Supports Python Frameworks built on Tornado.

[Source Code on GitHub](https://github.com/moesif/moesiftornado)

## How to install

```shell
pip install moesiftornado
```

## How to use

```python
from moesiftornado import MoesifMiddleware
import tornado.web
import json

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(json.dumps({ "msg": "Hello, world" }))

moesif_config = {
    'APPLICATION_ID': 'Your Moesif Application id',
    'LOG_BODY': True,
    # ... For other options see below.
}

# Create a moesif middleware
middleware = MoesifMiddleware(moesif_config)
# Set the log_function to middleware.log_event to log the events to Moesif
application = tornado.web.Application([(r"/", MainHandler)], log_function=middleware.log_event)

```

Your Moesif Application Id can be found in the [_Moesif Portal_](https://www.moesif.com/).
After signing up for a Moesif account, your Moesif Application Id will be displayed during the onboarding steps. 

You can always find your Moesif Application Id at any time by logging 
into the [_Moesif Portal_](https://www.moesif.com/), click on the top right menu,
and then clicking _API Keys_.

## Configuration options

#### __`APPLICATION_ID`__
(__required__), _string_, is obtained via your Moesif Account, this is required.

#### __`SKIP`__
(optional) _(handler) => boolean_, a function that takes a Request handler,
and returns true if you want to skip this particular event. 

#### __`IDENTIFY_USER`__
(optional, but highly recommended) _(handler) => string_, a function that takes a Request handler, and returns a string that is the user id used by your system. While Moesif tries to identify users automatically,
but different frameworks and your implementation might be very different, it would be helpful and much more accurate to provide this function.

#### __`IDENTIFY_COMPANY`__
(optional) _(handler) => string_, a function that takes a Request handler, and returns a string that is the company id for this event.

#### __`GET_METADATA`__
(optional) _(handler) => dictionary_, a function that takes a Request handler, and
returns a dictionary (must be able to be encoded into JSON). This allows your
to associate this event with custom metadata. For example, you may want to save a VM instance_id, a trace_id, or a tenant_id with the request.

#### __`GET_SESSION_TOKEN`__
(optional) _(handler) => string_, a function that takes a Request handler, and returns a string that is the session token for this event. Again, Moesif tries to get the session token automatically, but if you setup is very different from standard, this function will be very helpful for tying events together, and help you replay the events.

#### __`MASK_EVENT_MODEL`__
(optional) _(EventModel) => EventModel_, a function that takes an EventModel and returns an EventModel with desired data removed. The return value must be a valid EventModel required by Moesif data ingestion API. For details regarding EventModel please see the [Moesif Python API Documentation](https://www.moesif.com/docs/api?python).

#### __`DEBUG`__
(optional) _boolean_, a flag to see debugging messages.

#### __`LOG_BODY`__
(optional) _boolean_, default True, Set to False to remove logging request and response body.

#### __`BATCH_SIZE`__
(optional) __int__, default 25, Maximum batch size when sending to Moesif.

#### __`AUTHORIZATION_HEADER_NAME`__
(optional) _string_, A request header field name used to identify the User in Moesif. Default value is `authorization`. Also, supports a comma separated string. We will check headers in order like `"X-Api-Key,Authorization"`.

#### __`AUTHORIZATION_USER_ID_FIELD`__
(optional) _string_, A field name used to parse the User from authorization header in Moesif. Default value is `sub`.

### Example:

```python
from moesiftornado import MoesifMiddleware
import tornado.web

def identify_user(handler):
    # Your custom code that returns a user id string
    return "my_user_id"

def identify_company(handler):
    # Your custom code that returns a company id string
    return "my_company_id"

def get_token(handler):
    # Your custom code that returns a string for session/API token
    return "XXXXXXXXXXXXXX"

def should_skip(handler):
    # Your custom code that returns true to skip logging
    return "health/probe" in handler.request.full_url()

def mask_event(event_model):
    # Your custom code to change or remove any sensitive fields
    if 'password' in event_model.request.body:
        event_model.request.body['password'] = None
    return event_model

def get_metadata(handler):
    return {
        'datacenter': 'westus',
        'deployment_version': 'v1.2.3',
    }

moesif_config = {
    'APPLICATION_ID': 'Your Moesif Application Id',
    'LOG_BODY': True,
    'DEBUG': False,
    'IDENTIFY_USER': identify_user,
    'IDENTIFY_COMPANY': identify_company,
    'GET_SESSION_TOKEN': get_token,
    'SKIP': should_skip,
    'MASK_EVENT_MODEL': mask_event,
    'GET_METADATA': get_metadata,
}

middleware = MoesifMiddleware(moesif_config)
application = tornado.web.Application([(r"/", MainHandler)], log_function=middleware.log_event)

```

## Update User

### Update A Single User
Create or update a user profile in Moesif.
The metadata field can be any customer demographic or other info you want to store.
Only the `user_id` field is required.
For details, visit the [Python API Reference](https://www.moesif.com/docs/api?python#update-a-user).

```python
from moesiftornado import MoesifMiddleware
middleware = MoesifMiddleware(moesif_config)

# Only user_id is required.
# Campaign object is optional, but useful if you want to track ROI of acquisition channels
# See https://www.moesif.com/docs/api#users for campaign schema
# metadata can be any custom object
user_profile = {
  'user_id': '12345',
  'company_id': '67890', # If set, associate user with a company object
  'campaign': {
    'utm_source': 'google',
    'utm_medium': 'cpc', 
    'utm_campaign': 'adwords',
    'utm_term': 'api+tooling',
    'utm_content': 'landing'
  },
  'metadata': {
    'email': 'john@acmeinc.com',
    'first_name': 'John',
    'last_name': 'Doe',
    'title': 'Software Engineer',
    'sales_info': {
        'stage': 'Customer',
        'lifetime_value': 24000,
        'account_owner': 'mary@contoso.com'
    },
  }
}

middleware.update_user(user_profile)
```

### Update Users in Batch
Similar to update_user, but used to update a list of users in one batch. 
Only the `user_id` field is required.
For details, visit the [Python API Reference](https://www.moesif.com/docs/api?python#update-users-in-batch).

```python
from moesiftornado import MoesifMiddleware
middleware = MoesifMiddleware(moesif_config)

userA = {
  'user_id': '12345',
  'company_id': '67890', # If set, associate user with a company object
  'metadata': {
    'email': 'john@acmeinc.com',
    'first_name': 'John',
    'last_name': 'Doe',
    'title': 'Software Engineer',
    'sales_info': {
        'stage': 'Customer',
        'lifetime_value': 24000,
        'account_owner': 'mary@contoso.com'
    },
  }
}

userB = {
  'user_id': '54321',
  'company_id': '67890', # If set, associate user with a company object
  'metadata': {
    'email': 'mary@acmeinc.com',
    'first_name': 'Mary',
    'last_name': 'Jane',
    'title': 'Software Engineer',
    'sales_info': {
        'stage': 'Customer',
        'lifetime_value': 48000,
        'account_owner': 'mary@contoso.com'
    },
  }
}
middleware.update_users_batch([userA, userB])
```

## Update Company

### Update A Single Company
Create or update a company profile in Moesif.
The metadata field can be any company demographic or other info you want to store.
Only the `company_id` field is required.
For details, visit the [Python API Reference](https://www.moesif.com/docs/api?python#update-a-company).

```python
from moesiftornado import MoesifMiddleware
middleware = MoesifMiddleware(moesif_config)

# Only company_id is required.
# Campaign object is optional, but useful if you want to track ROI of acquisition channels
# See https://www.moesif.com/docs/api#update-a-company for campaign schema
# metadata can be any custom object
company_profile = {
  'company_id': '67890',
  'company_domain': 'acmeinc.com', # If domain is set, Moesif will enrich your profiles with publicly available info 
  'campaign': {
    'utm_source': 'google',
    'utm_medium': 'cpc', 
    'utm_campaign': 'adwords',
    'utm_term': 'api+tooling',
    'utm_content': 'landing'
  },
  'metadata': {
    'org_name': 'Acme, Inc',
    'plan_name': 'Free',
    'deal_stage': 'Lead',
    'mrr': 24000,
    'demographics': {
        'alexa_ranking': 500000,
        'employee_count': 47
    },
  }
}

middleware.update_company(company_profile)
```

### Update Companies in Batch
Similar to update_company, but used to update a list of companies in one batch. 
Only the `company_id` field is required.
For details, visit the [Python API Reference](https://www.moesif.com/docs/api?python#update-companies-in-batch).

```python
from moesiftornado import MoesifMiddleware
middleware = MoesifMiddleware(moesif_config)

companyA = {
  'company_id': '67890',
  'company_domain': 'acmeinc.com', # If domain is set, Moesif will enrich your profiles with publicly available info 
  'metadata': {
    'org_name': 'Acme, Inc',
    'plan_name': 'Free',
    'deal_stage': 'Lead',
    'mrr': 24000,
    'demographics': {
        'alexa_ranking': 500000,
        'employee_count': 47
    },
  }
}

companyB = {
  'company_id': '09876',
  'company_domain': 'contoso.com', # If domain is set, Moesif will enrich your profiles with publicly available info 
  'metadata': {
    'org_name': 'Contoso, Inc',
    'plan_name': 'Free',
    'deal_stage': 'Lead',
    'mrr': 48000,
    'demographics': {
        'alexa_ranking': 500000,
        'employee_count': 53
    },
  }
}
middleware.update_companies_batch([companyA, companyB])
```

## Tested versions

Moesif has validated moesiftornado against the following combinations. 

| Python       | Tornado  |
| ------------ | -------- |
| Python 2.7   |  4.4.1   |

## Example

An example Moesif integration based on quick start tutorial of Tornado:
[Moesif Tornado Example](https://github.com/Moesif/moesif-tornado-example)

## Other integrations

To view more documentation on integration options, please visit __[the Integration Options Documentation](https://www.moesif.com/docs/getting-started/integration-options/).__

[ico-built-for]: https://img.shields.io/badge/built%20for-python%20tornado-blue.svg
[ico-version]: https://img.shields.io/pypi/v/moesiftornado.svg
[ico-language]: https://img.shields.io/pypi/pyversions/moesiftornado.svg
[ico-license]: https://img.shields.io/badge/License-Apache%202.0-green.svg
[ico-source]: https://img.shields.io/github/last-commit/moesif/moesiftornado.svg?style=social

[link-built-for]: https://en.wikipedia.org/wiki/Web_Server_Gateway_Interface
[link-package]: https://pypi.python.org/pypi/moesiftornado
[link-language]: https://pypi.python.org/pypi/moesiftornado
[link-license]: https://raw.githubusercontent.com/Moesif/moesiftornado/master/LICENSE
[link-source]: https://github.com/Moesif/moesiftornado
