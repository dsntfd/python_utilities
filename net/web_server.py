# Copyright 2017-2020 Denis Gushchin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import asyncio
import datetime
import sys
import threading

from aiohttp import abc
from aiohttp import http_parser
from aiohttp import streams
from aiohttp import web
from ..base.errors import *
from ..base.log import *
from ..base.uid_util import *
from ..base.value import *
from ..base.worker_thread import *
from .net_util import *
from .session_factory import *

# Export
__all__ = ('WebServer', 'run_web_server', 'stop_web_server',)

# Json names
_JSON_NAME_ID = "__id__"
_JSON_NAME_STARTED_AT = "__started_at__"
_JSON_NAME_VERSION = "__version__"

#
# Global variables
#
_web_server = None


#
# WebServer
#
class WebServer (WorkerThread) :
  # Constructor
  def __init__(
      self, server_host, server_port, server_db = None,
      init_fun = None, deinit_fun = None, server_software = None,
      request_max_size: int = 1024**2) :
    # Initialize thread
    WorkerThread.__init__(self, 0, 1, "WebServerThread")

    # Web-server parameters
    self._request_max_size = request_max_size
    self._server_host = server_host
    self._server_port = server_port
    self._server_software = server_software

    # Web-server database
    self._db = server_db

    # External function on initialization and deinitialization
    self._init_fun = init_fun
    self._deinit_fun = deinit_fun

    # Web-server objects
    self._event_loop = None
    self._aiohttp_server = None
    self._web_server = None

    # Create UUID web-session and a session counter
    self._uid = create_uid()
    log_print_imp("Web-server's session UUID: {}", self._uid)
    self._session_counter = 0

    # Error
    self._error_code = Error(errOk)
    self._error_mutex = threading.RLock()

    # Statistics members
    self.__started_at = None
    self.__count_time_flag = None

  # Destructor
  def __del__(self) :
    self._error_mutex = None
    self.deinit_activity_counters()

    WorkerThread.__del__(self)

  # Initializes activity counters
  def init_activity_counters(self, count_time_flag = True) :
    if self.__count_time_flag is not None :
      return

    self.__count_time_flag = count_time_flag

  # Denitializes activity counters
  def deinit_activity_counters(self) :
    if self.__count_time_flag is None :
      return

    self.__count_time_flag = None

    for key in ActivityCounter.get_all_counter_names() :
     if not isinstance(key, tuple) or len(key) == 0 or key[0] != self.uid :
       continue

     counter = ActivityCounter.pop_counter(key)
     if counter is not None :
       del counter

  # Adds statistics counter of the web-server
  def add_counter(
      self, name_as_list, count_time_flag = None, count_error_flag = False) :
    if self.__count_time_flag is None :
      return None

    name = [ self.uid ]
    name.extend(name_as_list)
    return ActivityCounter.add(
        tuple(name),
        count_time_flag
        if count_time_flag is not None else
        self.__count_time_flag,
        count_error_flag)

  # Returns all statistics counters as Value
  def get_counters_as_value(self) :
    if self.__count_time_flag is None :
      return Value(dict())

    result = Value(dict())
    result[_JSON_NAME_ID] = Value(self.uid)
    if self.__started_at is not None :
      result[_JSON_NAME_STARTED_AT] = Value(
          "{:%Y-%m-%d %H:%M:%S}.{:06d}{:%z}".format(
              self.__started_at, self.__started_at.microsecond,
              self.__started_at))

    if self._server_software is not None :
      result[_JSON_NAME_VERSION] = Value(self._server_software)

    for key in ActivityCounter.get_all_counter_names() :
      if not isinstance(key, tuple) :
        continue

      key_list = list(key)
      if len(key_list) == 0 or key_list[0] != self.uid :
        continue

      result.set_path(key_list[1:], ActivityCounter.get(key).get_as_value())

    return result

  # Thread main function
  @log_function_body
  def do_work(self) :
    # Initialize loop and server
    result = self._init_server()
    with self._error_mutex :
      self._error_code = result

    if not result :
      self._deinit_server()
      self.start_barrier.wait()
      return False

    # Run loop
    self.start_barrier.wait()
    try :
      while True :
        self._event_loop.run_until_complete(asyncio.sleep(1.0))
        with self.stop_mutex :
          if self.stop_flag :
            break
    except :
      with self._error_mutex :
        self._error_code = Error(errInternalServerError, sys.exc_info()[1])
        log_print_err("Web-server failed", error_code = self._error_code)

      self._deinit_server()
      return False

    # Deinitialize loop and server
    result = self._deinit_server()
    with self._error_mutex :
      self._error_code = result

    return False

  # Start web_server
  def start(self) :
    self.start_barrier = threading.Barrier(2)
    WorkerThread.start(self)
    self.start_barrier.wait()
    self.start_barrier = None
    return self.error

  # Stop web-server
  def stop(self) :
    # Stop thread
    WorkerThread.stopping(self)
    self.join()

  def get_new_session_number(self) :
    """ Return new session number """
    self._session_counter += 1
    return self._session_counter

  @property
  def db(self) :
    """ Database is associated with web-server """
    return self._db

  @property
  def error(self) :
    """ Return web-server error """
    with self._error_mutex :
      return Error(self._error_code)

  @property
  def event_loop(self) :
    """ Event loop is created by the web-server """
    return self._event_loop

  @property
  def request_max_size(self):
    """ Return a request maximal size """
    return self._request_max_size

  @property
  def started_at(self) :
    """ Return a start time of the web-server """
    return self.__started_at

  @property
  def uid(self) :
    """ Return the web-server UID """
    return self._uid

  # Static
  def web_server() :
    """ Return the web-server """
    global _web_server
    return _web_server

  # Private: initialize server
  def _init_server(self) :
    try :
      self._event_loop = asyncio.new_event_loop()
      asyncio.set_event_loop(self._event_loop)
      # Initialize DB
      if self._db is not None :
        error = self._event_loop.run_until_complete(self._db.init())
        if err_failure(error) :
          log_print_err("DB's initialization failed", error_code = error)
          return error

      # Call an external function of initialization
      if self._init_fun is not None :
        error = self._event_loop.run_until_complete(self._init_fun(self))
        if err_failure(error) :
          log_print_err("External initialization failed", error_code = error)
          return error

      # Initialize web-server
      self._aiohttp_server = web.Server(
          self._request_handler, request_factory = self._make_request)
      asyncio_server = self._event_loop.create_server(
          self._aiohttp_server, self._server_host, self._server_port)
      self._web_server = self._event_loop.run_until_complete(asyncio_server)
      self.__started_at = datetime.datetime.now(tz = datetime.timezone.utc)
    except :
      error = Error(errCannotInitServer, sys.exc_info()[1])
      log_print_err("Web-server's initialization failed", error_code = error)
      return error

    return Error(errOk)

  @log_function_body
  def _make_request(self,
                    message: http_parser.RawRequestMessage,
                    payload: streams.StreamReader,
                    protocol: web.RequestHandler,
                    writer: abc.AbstractStreamWriter,
                    task: 'asyncio.Task[None]') \
                    -> web.BaseRequest :
    result =  web.BaseRequest(
        message, payload, protocol, writer, task, self._event_loop,
        client_max_size = self._request_max_size)
    result.processing_error = Error(errOk)
    return result

  # Private: deinitialize server
  def _deinit_server(self) :
    try :
      # Deinitialize web-server
      if not self._web_server is None :
        self._web_server.close()
        self._event_loop.run_until_complete(self._web_server.wait_closed())

      if not self._aiohttp_server is None :
        self._event_loop.run_until_complete(self._aiohttp_server.shutdown())

      # Call an external function of deinitialization
      if self._deinit_fun is not None :
        error = self._event_loop.run_until_complete(self._deinit_fun(self))
        if err_failure(error) :
          log_print_err("External deinitialization failed", error_code = error)
          return error

      # Deinitialize DB
      if self._db is not None :
        self._event_loop.run_until_complete(self._db.deinit())

      # Close an event loop
      if not self._event_loop is None :
        self._event_loop.close()

      asyncio.set_event_loop(None)
      self._web_server = None
      self._aiohttp_server = None
      self._event_loop = None
    except :
      result = Error(errCannotDeinitServer, sys.exc_info()[1])
      log_print_err("Web-server's deinitialization failed", error_code = result)
      return result

    return Error(errOk)

  # Request handler
  @log_async_function_body()
  async def _request_handler(self, request) :
    log_print_inf("Url:{} Remote:{}", request.url, request.remote)
    try :
      session = await create_session(self, request)
      session.server_software = self._server_software
      result = await session.run()
      if err_success(result) :
        response = session.response
      else :
        log_print_err("Internal server error when session was run",
                      error_code = result)
        response = web.Response(text = "Internal Server Error", status = 500,
                                charset = "utf-8")
    except :
      log_print_err("Internal server error when session was run",
          error_code = Error(errInternalServerError, sys.exc_info()[1]))
      response = web.Response(text = "Internal Server Error", status = 500,
                              charset = "utf-8")

    return response

#
# Run web-server
#
@log_function_body
def run_web_server(
    server_host, server_port, session_factory, db = None,
    init_fun = None, deinit_fun = None, server_software = None,
    request_max_size: int = 1024**2) :
  global _web_server

  set_session_factory(session_factory)
  _web_server = WebServer(
      server_host, server_port, db, init_fun, deinit_fun, server_software,
      request_max_size)
  result = _web_server.start()
  if err_failure(result) :
    log_print_err("Web-server failed on starting", result)
    stop_web_server()

  return result

#
# Stop web-server
#
@log_function_body
def stop_web_server() :
  global _web_server

  _web_server.stop()
  _web_server = None

  return errOk
