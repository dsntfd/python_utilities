# Copyright 2017-2020 Denis Gushchin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""
  Module realize a outgoing session
"""

import aiohttp

from .session import *
from aiohttp.helpers import sentinel
from base.log import *

# Export
__all__ = ('SessionOutResult', 'SessionOut',)

#
# Class SessionOutResult
#
class SessionOutResult :
  """
    Class provides functionality for session's result by means of properties
  """
  pass

#
# Incoming session
#
class SessionOut (Session) :
  """
    Implementation of outgoing session

    Session is used to receive information from net
  """
  def __init__(self, web_server, parent_session_uid, session_uid_prefix) :
    Session.__init__(self, web_server, parent_session_uid, session_uid_prefix)

    self._body = None
    self._headers = None
    self._method = aiohttp.hdrs.METH_GET
    self._query = None
    self._result = SessionOutResult()
    self._url = None

  @log_async_function_body()
  async def request(self,
                    skip_auto_headers=None,
                    auth=None,
                    allow_redirects=True,
                    max_redirects=10,
                    encoding=None,
                    compress=None,
                    chunked=None,
                    expect100=False,
                    read_until_eof=True,
                    proxy=None,
                    proxy_auth=None,
                    timeout=sentinel,
                    verify_ssl=None,
                    fingerprint=None,
                    ssl_context=None,
                    proxy_headers=None) :
    """ Perform HTTP request """
    # Check url to exist
    if self.url is None :
      self._error_code = Error(errObjNotInit, "Url must be")
      log_print_err(None, error_code = self._error_code)
      return self._error_code

    # Run request
    try :
      async with aiohttp.ClientSession() as session :
        response = await session.request(
            self.method,
            self.url,
            params = self.query,
            data = self.body,
            headers = self.headers,
            skip_auto_headers = skip_auto_headers,
            auth = auth,
            allow_redirects = allow_redirects,
            max_redirects = max_redirects,
            compress = compress,
            chunked = chunked,
            expect100 = expect100,
            read_until_eof = read_until_eof,
            proxy = proxy,
            proxy_auth = proxy_auth,
            timeout = timeout,
            verify_ssl = verify_ssl,
            fingerprint = fingerprint,
            ssl_context = ssl_context,
            proxy_headers = proxy_headers)
        log_print_inf("Requested url: {}", response.request_info.url)
        await self._set_response(response)
    except :
      self._error_code = Error(errRequestFailed, sys.exc_info()[1])
      log_print_err("Error occured during asking \'{}\'", self.url,
                    error_code = self._error_code)
      return self._error_code

    return Error(errOk)

  @log_async_function_body()
  async def _set_request(self, response) :
    """ Set network request """
    if self._request is not None :
      error = Error(errObjAlreadyInit, "Can't set a request twice")
      log_print_err(None, error_code = error)
      return error

    class RequestMock :
      pass

    self._request = RequestMock()
    self._request.url = response.request_info.url
    self._request.method = response.request_info.method
    self._request.headers = response.request_info.headers
    self._request.version = response.version
    self._request.body = self.body
    await async_log_print_file(
        LOG_LEVEL_VERBOSE, "request", dump_request, self._request)
    return Error(errOk)

  async def _set_response(self, response) :
    """ Set network response """
    if self._response is not None :
      error = Error(errObjAlreadyInit, "Can't set a response twice")
      log_print_err(None, error_code = error)
      return error

    if response is None :
      error = Error(errObjAlreadyInit, "Try to set a response as None")
      log_print_err(None, error_code = error)
      return error

    # Set request
    await self._set_request(response)

    # Set response
    self._response = response
    await async_log_print_file(
        LOG_LEVEL_VERBOSE, "response", dump_response, self._response)
    return Error(errOk)

  @property
  def body(self) :
    """ Request's body """
    return self._body

  @body.setter
  def body(self, body) :
    """ Set request's body """
    self._body = body

  @property
  def headers(self) :
    """ Request's headers """
    return self._headers

  @headers.setter
  def headers(self, headers) :
    """ Set request's headers """
    self._headers = headers

  @property
  def method(self) :
    """ HTTP method """
    return self._method

  @method.setter
  def method(self, method) :
    """ Set HTTP method """
    self._method = method

  @property
  def query(self) :
    """ Dictionary of url's query string """
    return self._query

  @query.setter
  def query(self, query) :
    """ Set dictionary of url's query string """
    self._query = query

  @property
  def result(self) :
    """ Result of session's work """
    return self._result

  @property
  def url(self) :
    """ Request's url """
    return self._url

  @url.setter
  def url(self, url) :
    """ Set request's url """
    self._url = url
