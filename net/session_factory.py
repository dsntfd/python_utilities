# Copyright 2017-2020 Denis Gushchin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from .error_session import *

#
# Session factory function
#
_session_factory = None

#
# Set a session factory function
#
def set_session_factory(session_factory) :
  global _session_factory

  _session_factory = session_factory

#
# Create session by request
#
@log_async_function_body()
async def create_session(web_server, request) :
  global _session_factory

  log_print_vrb("Url's path: {}".format(request.path))

  result = None
  if _session_factory is not None :
    result = await _session_factory(web_server, request)

  if result is None :
    result = ErrorSession(web_server)

  await result.set_request(request)
  return result
