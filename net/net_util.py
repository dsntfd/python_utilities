# Copyright 2017-2020 Denis Gushchin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import asyncio
import sys

from aiohttp.web_request import BaseRequest
from aiohttp.web_response import Response
from base.errors import *
from base.log import *

# Export
__all__ = ('get_request_raw_header', 'dump_request', 'dump_response',)

#
# Function get_request_raw_header
#
def get_request_raw_header(request, name) :
  """ Return raw header value of request by header name """
  name = name.lower()
  for header in request.raw_headers :
    if header[0].decode("utf-8").lower() == name:
      return header[1].decode("utf-8")

  return ""

#
# Function dump_request
#
async def dump_request(request) :
  """ Dump http-request in byte array """
  result = bytearray()
  # Add request string
  try :
    result.extend((request.method + " " + str(request.url) + " " +
        "HTTP/{:d}.{:d}".format(request.version.major, request.version.minor)).
        encode("utf-8"))
  except :
    error = Error(errInvalidParameter, sys.exc_info()[1])
    log_print_err("Can't read properties of request", error_code = error)

  # Add http-headers
  try :
    if isinstance(request, BaseRequest) :
      for header in request.raw_headers :
        result.extend("\r\n".encode("utf-8"))
        result.extend(header[0])
        result.extend(": ".encode("utf-8"))
        result.extend(header[1])
    else :
      for key, value in request.headers.items() :
        result.extend("\r\n".encode("utf-8"))
        result.extend(key.encode("utf-8"))
        result.extend(": ".encode("utf-8"))
        result.extend(value.encode("utf-8"))
  except :
    error = Error(errInvalidParameter, sys.exc_info()[1])
    log_print_err("Can't read properties of request", error_code = error)

  # Add http-body
  try :
    if isinstance(request, BaseRequest) :
      result.extend("\r\n\r\n".encode("utf-8"))
      body = await request.read()
      if body is not None :
        result.extend(body)
    else :
      result.extend("\r\n\r\n".encode("utf-8"))
      if request.body is not None :
        result.extend(request.body)
  except :
    error = Error(errInvalidParameter, sys.exc_info()[1])
    log_print_err("Can't read body of request", error_code = error)

  return bytes(result)

#
# Function dump_response
#
async def dump_response(response) :
  """ Dump http-response in byte array """
  result = bytearray()
  # Add response string
  try :
    result.extend(
        ("HTTP/{:d}.{:d} {} {}".format(
             response.version.major, response.version.minor,
             response.status, response.reason)).
        encode("utf-8"))
  except :
    error = Error(errInvalidParameter, sys.exc_info()[1])
    log_print_err("Can't read properties of response", error_code = error)

  # Add http-headers
  try :
    for name, value in response.headers.items() :
      result.extend("\r\n".encode("utf-8"))
      result.extend(name.encode("utf-8"))
      result.extend(": ".encode("utf-8"))
      result.extend(value.encode("utf-8"))
  except :
    error = Error(errInvalidParameter, sys.exc_info()[1])
    log_print_err("Can't read headers of response", error_code = error)

  # Add http-body
  try :
    if isinstance(response, Response) :
      result.extend("\r\n\r\n".encode("utf-8"))
      if response.body is not None :
        result.extend(response.body)
    else :
      result.extend("\r\n\r\n".encode("utf-8"))
      body = await response.read()
      if body is not None :
        result.extend(body)
  except :
    error = Error(errInvalidParameter, sys.exc_info()[1])
    log_print_err("Can't read body of response", error_code = error)

  return bytes(result)
