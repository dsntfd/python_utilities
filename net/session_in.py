# Copyright 2017-2020 Denis Gushchin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import aiohttp

from .session import *

# Export
__all__ = ('SessionIn',)

#
# Class SessionIn
#
class SessionIn (Session) :
  """
    Implementation of incoming session

    Session is used to respond to incoming request
  """
  def __init__(self, web_server, session_uid_prefix) :
    Session.__init__(self, web_server, web_server.uid, session_uid_prefix)

    self._server_software = None

  @log_async_function_body()
  async def set_request(self, request) :
    """ Set network request """
    if self._request is not None :
      error = Error(errObjAlreadyInit, "Can't set a request twice")
      log_print_err(None, error_code = error)
      return error

    if request is None :
      error = Error(errObjAlreadyInit, "Try to set a request as None")
      log_print_err(None, error_code = error)
      return error

    self._request = request
    await async_log_print_file(
        LOG_LEVEL_VERBOSE, "request", dump_request, self._request)
    return Error(errOk)

  async def set_response(self, response) :
    """ Set network response """
    if self._response is not None :
      error = Error(errObjAlreadyInit, "Can't set a response twice")
      log_print_err(None, error_code = error)
      return error

    if response is None :
      error = Error(errObjAlreadyInit, "Try to set a response as None")
      log_print_err(None, error_code = error)
      return error

    if self._server_software is not None and len(self._server_software) > 0 :
      server_software = ""
      if aiohttp.hdrs.SERVER in response.headers :
        server_software += response.headers[aiohttp.hdrs.SERVER] + " "

      server_software += self._server_software
      response.headers[aiohttp.hdrs.SERVER] = server_software

    if self._cache_control is not None and len(self._cache_control) > 0 :
      response.headers[aiohttp.hdrs.CACHE_CONTROL] = self._cache_control

    await response.prepare(self.request)
    response.version = self.request.version
    self._response = response
    await async_log_print_file(
        LOG_LEVEL_VERBOSE, "response", dump_response, self._response)
    return Error(errOk)

  @property
  def server_software(self) :
    return self._server_software

  @server_software.setter
  def server_software(self, server_software) :
    self._server_software = server_software
