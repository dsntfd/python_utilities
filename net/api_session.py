# Copyright 2017-2020 Denis Gushchin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import aiohttp
import sys

from aiohttp import web
from ..base.errors import *
from ..base.log import *
from ..base.value import *
from .net_util import *
from .session_in import *

# Export
__all__ = ('ApiSession',)

#: API version field in Content-Type
_API_VERSION_FIELD = "api_version"

#: Defaulf main charset
_DEFAULF_CHARSET = "utf-8"

class ApiSession (SessionIn) :
  def __init__(
      self, web_server, server_api_version, session_prefix, function_map,
      function_dependency_map = None, charset = _DEFAULF_CHARSET) :
    SessionIn.__init__(self, web_server, session_prefix)

    self._server_api_version = server_api_version
    self._api_version = 0
    self._function_map = function_map
    self._function_dependency_map = function_dependency_map
    self._charset = charset
    self._request_charset = None

  @property
  def api_version(self) :
    """ API version """
    return self._api_version

  @property
  def charset(self) :
    """ Session charset """
    return self._charset

  @property
  def counter_name(self) :
    return "api_session"

  @property
  def function_dependency_map(self) :
    """ Function dependency map """
    return self._function_dependency_map

  @property
  def function_map(self) :
    """ Function map """
    return self._function_map

  @property
  def request_charset(self) :
    """ Request charset """
    return self._request_charset

  @property
  def server_api_version(self) :
    """ Server API version """
    return self._server_api_version

  async def _get_response_body(self) :
    """ Form result's body """
    # Check API version
    content_type = \
        get_request_raw_header(self.request, aiohttp.hdrs.CONTENT_TYPE)
    for item in content_type.split(';'):
      item = item.strip()
      if item.lower()[:len(_API_VERSION_FIELD)] != _API_VERSION_FIELD :
        continue

      try :
        self._api_version = int(item[len(_API_VERSION_FIELD) + 1:])
      except :
        self._error_code = Error(errCannotReadAPIVersion, sys.exc_info()[1])
        log_print_err("Error occured during reading API version ({})", item,
                      error_code = self._error_code)
        return error_to_json(self.error)

      break

    if self._api_version > self._server_api_version :
      self._error_code = \
          Error(
              errAPIVersionNotSupported,
              "Client is from future - Server API version: {}; "
              "Client API version: {}".format(
                  self._server_api_version, self._api_version))
      log_print_err(None, error_code = self._error_code)
      return error_to_json(self.error)
    elif self._api_version == 0 :
      self._error_code = \
          Error(errCannotReadAPIVersion, "Can't find API version in request")
      log_print_err(None, error_code = self._error_code)
      return error_to_json(self.error)

    log_print_inf("Request API version: {}", self._api_version)

    # Read request's body
    try :
      body = await self.request.read()
    except :
      self._error_code = Error(errCannotReadContent, sys.exc_info()[1])
      log_print_err("Error occured during reading request's body",
                    error_code = self._error_code)
      return error_to_json(self.error)

    # Decode body to json
    self._request_charset = self.request.charset
    json = body.decode(self._request_charset or self._charset)
    if self._request_charset is not None and \
       self._request_charset.lower() != self._charset :
      json = json.encode(self._charset).decode(self._charset)

    # Parse body
    api_request, error = deserialize_json_to_value(json, None, self._charset)
    if err_failure(error) :
      self._error_code = error
      log_print_err(None, error_code = self._error_code)
      return error_to_json(self.error)

    if api_request.value_type != Type.DICTIONARY :
      self._error_code = Error(errInvalidParameter, "Json is invalid")
      log_print_err(None, error_code = self._error_code)
      return error_to_json(self.error)

    # Process request
    result = Value(dict())
    for function in api_request.value :
      function_lower = function.lower()

      ## Check dependencies
      if function_lower in self._function_dependency_map :
        for dependency in self._function_dependency_map[function_lower] :
          if dependency not in result :
           self._error_code = Error(
               errFuncFailed,
               "Before calling \"{}\" to have to call \"{}\"".format(
                   function, dependency))
           log_print_err(None, error_code = self._error_code)
           result[function] = error_to_value(self.error)
           break

      if err_failure(self._error_code) :
        break

      ## Check function to be present
      if function_lower not in self._function_map :
        self._error_code = \
            Error(errInvalidParameter,
                  "Unknow function - \"{}\"".format(function))
        log_print_err(None, error_code = self._error_code)
        result[function] = error_to_value(self.error)
        break

      ## Call function
      ### Start counter
      counter = self.web_server.add_counter(
          [self.counter_name, "api", function_lower], None, True)
      if counter is not None : counter.start(self.uid)

      function_result, error = await self._function_map[function_lower](
          self, api_request[function])

      ### Stop counter
      if counter is not None : counter.stop(self.uid, err_failure(error))

      ### Check result
      if err_failure(error) :
        self._error_code = error
        log_print_err(None, error_code = self._error_code)
        result[function] = error_to_value(self.error)
        break

      result[function] = function_result

    # Generate json
    result_body, error = serialize_value_to_json(result, self._charset)
    if err_failure(error) :
      self._error_code = error
      log_print_err(None, error_code = self._error_code)
      return error_to_json(self.error)

    return result_body

  async def _do_work(self) :
    """ Main function for work """
    # Get result's body
    body = await self._get_response_body()
    body_binary = body.encode(self._charset)

    # Create response
    response = web.Response()
    response.content_type = "application/json"
    response.charset = self._charset
    response.body = body_binary
    await self.set_response(response)
    return Error(errOk)
