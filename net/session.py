# Copyright 2017-2020 Denis Gushchin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import asyncio

from aiohttp import web
from base.errors import *
from base.log import *
from base.uid_util import *
from net.net_util import *
from net.web_server import *


#
# Class Session
#
class Session :
  """
    Implementation of session's base functionality
  """
  def __init__(self, web_server, parent_session_uid, session_uid_prefix) :
    self._web_server = web_server
    self._uid = create_uid(parent_session_uid, session_uid_prefix,
                           web_server.get_new_session_number())
    self._active = False
    self._cache_control = ""
    self._error_code = Error(errOk)
    self._request = None
    self._response = None
    self._run_completed_event = None
    log_print_inf("Network session UID: {}".format(self._uid))

  @log_async_function_body()
  async def call_soon(self) :
    """ Run the net session as soon as possible """
    self._run_completed_event = \
        asyncio.Event(loop = self._web_server.event_loop)
    self._web_server.event_loop.call_soon(self.run)

  @log_async_function_body()
  async def run(self) :
    """ Run execution of session """
    #  Do main work
    self._active = True
    result = await self._do_work()
    self._active = False

    # Signal that work have been done if it is necessary
    if self._run_completed_event is not None :
      self._run_completed_event.set()

    return result

  @log_async_function_body()
  async def wait(self, timeout = None) :
    """ Block until the session runs or the optional timeout occurs"""
    result = Error(errOk)
    if self._run_completed_event.wait is not None :
      done_flag = await self._run_completed_event.wait(timeout)
      self._run_completed_event.wait = None
      if not done_flag :
        result = Error(wrnTimeout, "Timeout occurs while waiting for session")

    return result

  @property
  def active(self) :
    """ Return True if session is active """
    return self._active

  @property
  def cache_control(self) :
    return self._cache_control

  @cache_control.setter
  def cache_control(self, cache_control) :
    self._cache_control = cache_control

  @property
  def error(self) :
    """ Object internal error """
    return self._error_code

  @property
  def request(self) :
    """ Network request """
    return self._request

  @property
  def response(self) :
    """ Network response """
    return self._response

  @property
  def uid(self) :
    """ Session UID """
    return self._uid

  @property
  def web_server(self) :
    """ Web-server - owner of session """
    return self._web_server

  @log_async_function_body()
  async def _do_work(self) :
    """ Main function for work """
    self._error_code = Error(errFuncNotImplemented,
                             "Сalling Session._do_work is forbidden")
    log_print_err(None, error_code = self.error)
    return web.Response(text = "Not Found", status = 404, charset = "utf-8")
