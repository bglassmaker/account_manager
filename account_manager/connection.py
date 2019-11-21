import json
import logging
import os
import time

from oauthlib.oauth2 import TokenExpiredError, WebApplicationClient, BackendApplicationClient
from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import HTTPError, RequestException, ProxyError
from requests.exceptions import SSLError, Timeout, ConnectionError
# Dynamic loading of module Retry by requests.packages
# noinspection PyUnresolvedReferences
from requests.packages.urllib3.util.retry import Retry
from requests_oauthlib import OAuth2Session
from stringcase import pascalcase, camelcase, snakecase
from tzlocal import get_localzone
from pytz import UnknownTimeZoneError, UTC

from .utils import ME_RESOURCE, BaseTokenBackend, FileSystemTokenBackend, Token

log = logging.getLogger(__name__)

O365_API_VERSION = 'v2.0'
GRAPH_API_VERSION = 'v1.0'
OAUTH_REDIRECT_URL = 'https://login.microsoftonline.com/common/oauth2/nativeclient'  # version <= 1.1.3.  : 'https://outlook.office365.com/owa/'

RETRIES_STATUS_LIST = (
    429,  # Status code for TooManyRequests
    500, 502, 503, 504  # Server errors
)
RETRIES_BACKOFF_FACTOR = 0.5

DEFAULT_SCOPES = {
    # wrap any scope in a 1 element tuple to avoid prefixing
    'basic': [('offline_access',), 'User.Read'],
    'mailbox': ['Mail.Read'],
    'mailbox_shared': ['Mail.Read.Shared'],
    'message_send': ['Mail.Send'],
    'message_send_shared': ['Mail.Send.Shared'],
    'message_all': ['Mail.ReadWrite', 'Mail.Send'],
    'message_all_shared': ['Mail.ReadWrite.Shared', 'Mail.Send.Shared'],
    'address_book': ['Contacts.Read'],
    'address_book_shared': ['Contacts.Read.Shared'],
    'address_book_all': ['Contacts.ReadWrite'],
    'address_book_all_shared': ['Contacts.ReadWrite.Shared'],
    'calendar': ['Calendars.Read'],
    'calendar_shared': ['Calendars.Read.Shared'],
    'calendar_all': ['Calendars.ReadWrite'],
    'calendar_shared_all': ['Calendars.ReadWrite.Shared'],
    'users': ['User.ReadBasic.All'],
    'onedrive': ['Files.Read.All'],
    'onedrive_all': ['Files.ReadWrite.All'],
    'sharepoint': ['Sites.Read.All'],
    'sharepoint_dl': ['Sites.ReadWrite.All'],
    'settings_all': ['MailboxSettings.ReadWrite'],
}


class Protocol:
    """ Base class for all protocols """

    # Override these in subclass
    _protocol_url = 'not_defined'  # Main url to request.
    _oauth_scope_prefix = ''  # Prefix for scopes
    _oauth_scopes = {}  # Dictionary of {scopes_name: [scope1, scope2]}

    def __init__(self, *, protocol_url=None, api_version=None,
                 default_resource=None,
                 casing_function=None, protocol_scope_prefix=None,
                 timezone=None, **kwargs):
        """ Create a new protocol object
        :param str protocol_url: the base url used to communicate with the
         server
        :param str api_version: the api version
        :param str default_resource: the default resource to use when there is
         nothing explicitly specified during the requests
        :param function casing_function: the casing transform function to be
         used on api keywords (camelcase / pascalcase)
        :param str protocol_scope_prefix: prefix url for scopes
        :param pytz.UTC timezone: preferred timezone, defaults to the
         system timezone
        :raises ValueError: if protocol_url or api_version are not supplied
        """
        if protocol_url is None or api_version is None:
            raise ValueError(
                'Must provide valid protocol_url and api_version values')
        self.protocol_url = protocol_url or self._protocol_url
        self.protocol_scope_prefix = protocol_scope_prefix or ''
        self.api_version = api_version
        self.service_url = '{}{}/'.format(protocol_url, api_version)
        self.default_resource = default_resource or ME_RESOURCE
        self.use_default_casing = True if casing_function is None else False
        self.casing_function = casing_function or camelcase
        try:
            self.timezone = timezone or get_localzone()  # pytz timezone
        except UnknownTimeZoneError as e:
            log.info('Timezone not provided and the local timezone could not be found. Default to UTC.')
            self.timezone = UTC  # pytz.timezone('UTC')
        self.max_top_value = 500  # Max $top parameter value

        # define any keyword that can be different in this protocol
        # for example, attachments Odata type differs between Outlook
        #  rest api and graph: (graph = #microsoft.graph.fileAttachment and
        #  outlook = #Microsoft.OutlookServices.FileAttachment')
        self.keyword_data_store = {}

    def get_service_keyword(self, keyword):
        """ Returns the data set to the key in the internal data-key dict
        :param str keyword: key to get value for
        :return: value of the keyword
        """
        return self.keyword_data_store.get(keyword, None)

    def convert_case(self, key):
        """ Returns a key converted with this protocol casing method
        Converts case to send/read from the cloud
        When using Microsoft Graph API, the keywords of the API use
        lowerCamelCase Casing
        When using Office 365 API, the keywords of the API use PascalCase Casing
        Default case in this API is lowerCamelCase
        :param str key: a dictionary key to convert
        :return: key after case conversion
        :rtype: str
        """
        return key if self.use_default_casing else self.casing_function(key)

    @staticmethod
    def to_api_case(key):
        """ Converts key to snake_case
        :param str key: key to convert into snake_case
        :return: key after case conversion
        :rtype: str
        """
        return snakecase(key)

    def get_scopes_for(self, user_provided_scopes):
        """ Returns a list of scopes needed for each of the
        scope_helpers provided, by adding the prefix to them if required
        :param user_provided_scopes: a list of scopes or scope helpers
        :type user_provided_scopes: list or tuple or str
        :return: scopes with url prefix added
        :rtype: list
        :raises ValueError: if unexpected datatype of scopes are passed
        """
        if user_provided_scopes is None:
            # return all available scopes
            user_provided_scopes = [app_part for app_part in self._oauth_scopes]
        elif isinstance(user_provided_scopes, str):
            user_provided_scopes = [user_provided_scopes]

        if not isinstance(user_provided_scopes, (list, tuple)):
            raise ValueError(
                "'user_provided_scopes' must be a list or a tuple of strings")

        scopes = set()
        for app_part in user_provided_scopes:
            for scope in self._oauth_scopes.get(app_part, [(app_part,)]):
                scopes.add(self.prefix_scope(scope))

        return list(scopes)

    def prefix_scope(self, scope):
        """ Inserts the protocol scope prefix if required"""
        if self.protocol_scope_prefix:
            if isinstance(scope, tuple):
                return scope[0]
            elif scope.startswith(self.protocol_scope_prefix):
                return scope
            else:
                return '{}{}'.format(self.protocol_scope_prefix, scope)
        else:
            if isinstance(scope, tuple):
                return scope[0]
            else:
                return scope


class MSGraphProtocol(Protocol):
    """ A Microsoft Graph Protocol Implementation
    https://docs.microsoft.com/en-us/outlook/rest/compare-graph-outlook
    """

    _protocol_url = 'https://graph.microsoft.com/'
    _oauth_scope_prefix = 'https://graph.microsoft.com/'
    _oauth_scopes = DEFAULT_SCOPES

    def __init__(self, api_version='v1.0', default_resource=None,
                 **kwargs):
        """ Create a new Microsoft Graph protocol object
        _protocol_url = 'https://graph.microsoft.com/'
        _oauth_scope_prefix = 'https://graph.microsoft.com/'
        :param str api_version: api version to use
        :param str default_resource: the default resource to use when there is
         nothing explicitly specified during the requests
        """
        super().__init__(protocol_url=self._protocol_url,
                         api_version=api_version,
                         default_resource=default_resource,
                         casing_function=camelcase,
                         protocol_scope_prefix=self._oauth_scope_prefix,
                         **kwargs)

        self.keyword_data_store['message_type'] = 'microsoft.graph.message'
        self.keyword_data_store['event_message_type'] = 'microsoft.graph.eventMessage'
        self.keyword_data_store[
            'file_attachment_type'] = '#microsoft.graph.fileAttachment'
        self.keyword_data_store[
            'item_attachment_type'] = '#microsoft.graph.itemAttachment'
        self.max_top_value = 999  # Max $top parameter value