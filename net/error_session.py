# Copyright 2017-2020 Denis Gushchin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from aiohttp import web
from ..base.errors import *
from ..base.log import *
from .session_in import *


#
# Session prefix
#
_SESSION_PREFIX = "err" #: Error session prefix

#
# Class ErrorSession
#
class ErrorSession (SessionIn) :
  """
    Common error session

    If we can't find another session then we create it
  """
  def __init__(self, web_server) :
    SessionIn.__init__(self, web_server, _SESSION_PREFIX)

  async def _do_work(self) :
    """ Main function for work """
    self._error_code = Error(
        errNotSupportUrl, "Url isn't supported - {}".format(self.request.url))
    log_print_err(None, error_code = self.error)
    await self.set_response(web.Response(
        text = "Url isn't supported - \'{}\'".format(self.request.url),
        status = 200, charset = "utf-8"))
    return Error(errOk)

  @property
  def counter_name(self) :
    return "error_session"
