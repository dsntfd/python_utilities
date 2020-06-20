# Copyright 2017-2020 Denis Gushchin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import asyncio
import sys

from base.errors import *
from base.log import *


#
# Class DBConnector
#
class DBConnector :
  def __init__(self, user = "", password = "", database = "",
               host = "", port = None) :
    self._database = database
    self._host = host
    self._password = password
    self._port = port
    self._user = user

    log_print_inf(
        "DB connector is created. "
        "User: \'{}\', DB: \'{}\', Host: \'{}\', Port: \'{}\'",
        user, database, host, port)

  async def deinit(self) :
    """ Deinitialize DB connect """
    return Error(errFuncNotImplemented,
                 "Function mast be implimented by child class")

  async def execute(self, query) :
    """ Execute query """
    return Error(errFuncNotImplemented,
                 "Function mast be implimented by child class")

  async def init(self) :
    """ Initialize DB connect """
    return Error(errFuncNotImplemented,
                 "Function mast be implimented by child class")

  @property
  def database(self) :
    return self._database

  @database.setter
  def database(self, database) :
    self._database = database

  @property
  def host(self) :
    return self._host

  @host.setter
  def host(self, host) :
    self._host = host

  @property
  def password(self) :
    return self._password

  @password.setter
  def password(self, password) :
    self._password = password

  @property
  def port(self) :
    return self._port

  @port.setter
  def port(self, port) :
    self._port = port

  @property
  def user(self) :
    return self._user

  @user.setter
  def user(self, user) :
    self._user = user
