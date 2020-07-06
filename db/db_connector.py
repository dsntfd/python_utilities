# Copyright 2017-2020 Denis Gushchin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import asyncio
import datetime
import sys

from ..base.errors import *
from ..base.log import *
from ..base.uid_util import *
from ..base.value import *

# Export
__all__ = ('DBConnector',)

# Json names
_JSON_NAME_ID = "__id__"
_JSON_NAME_CREATED_AT = "__created_at__"
_JSON_NAME_VERSION = "__version__"

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
    self.__uid = create_uid()
    self.__version = None

    log_print_imp("DBConnector UUID: {}", self.__uid)

    # Statistics members
    self.__created_at = datetime.datetime.now(tz = datetime.timezone.utc)
    self.__count_time_flag = None

    log_print_inf(
        "DB connector is created. "
        "User: \'{}\', DB: \'{}\', Host: \'{}\', Port: \'{}\'",
        user, database, host, port)

  # Destructor
  def __del__(self) :
    self.deinit_activity_counters()

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

  # Adds statistics counter of the db-connector
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
    result[_JSON_NAME_CREATED_AT] = Value(
        "{:%Y-%m-%d %H:%M:%S}.{:06d}{:%z}".format(
            self.__created_at, self.__created_at.microsecond,
            self.__created_at))
    if self.__version is not None :
      result[_JSON_NAME_VERSION] = Value(self.__version)

    for key in ActivityCounter.get_all_counter_names() :
      if not isinstance(key, tuple) :
        continue

      key_list = list(key)
      if len(key_list) == 0 or key_list[0] != self.uid :
        continue

      result.set_path(key_list[1:], ActivityCounter.get(key).get_as_value())

    return result

  @property
  def created_at(self) :
    return self.__created_at

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
  def uid(self) :
    return self.__uid

  @property
  def user(self) :
    return self._user

  @user.setter
  def user(self, user) :
    self._user = user

  @property
  def version(self) :
    return self.__version

  @version.setter
  def version(self, version) :
    self.__version = version
