# Copyright 2017-2020 Denis Gushchin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import asyncio
import hashlib

from aiopg.sa import create_engine
from sqlalchemy.dialects import postgresql
from ..base.errors import *
from ..base.log import *
from ..base.uid_util import *
from .db_connector import *

# Export
__all__ = ('PgDBConnector',)

# Query counter name
_QUERY_COUNTER_NAME = "queries"

#
# Class DBConnector
#
class PgDBConnector (DBConnector) :
  def __init__(self, user = "", password = "", database = "",
               host = "", port = 5432) :
    DBConnector.__init__(self, user, password, database, host, port)

    self.__query_counter = None
    self.__query_ids = set()

  @log_async_function_body()
  async def deinit(self) :
    """ Deinitialize DB connect """
    if len(self.database) == 0 :
      log_print_inf("Haven't used any DB")
      return Error(errOk)

    log_print_inf("Deinitialize PostgreDB connect")
    self._engine.close()
    await self._engine.wait_closed()
    del self._engine
    return Error(errOk)

  @log_async_function_body()
  async def execute(self, query) :
    """ Execute query """
    query_str = None
    try :
      # https://stackoverflow.com/questions/5631078/sqlalchemy-print-the-actual-query
      # compile_kwargs={"literal_binds": True}
      query_str = str(query.compile(dialect = postgresql.dialect()))
      log_print_vrb("SQL query: \n{}", query_str)
    except :
      log_print_vrb("Can't convert SQL query to string ({})", sys.exc_info()[1])

    # Generate query id if it needs
    query_uid = None
    if self.__query_counter is not None :
      query_uid = create_uid()

    try :
      async with self._engine.acquire() as connection:
        # Start counter
        query_hash = None
        counter = None
        if self.__query_counter is not None :
          self.__query_counter.start(query_uid)
          if query_str is not None :
            query_hash = hashlib.sha256(query_str.encode("utf-8")).hexdigest()
            counter = self.add_counter(["query_details", query_hash])
            counter.start(query_uid)
            if query_hash not in self.__query_ids :
              log_print_imp("SQL query (id - {}): \n{}", query_hash, query_str)
              self.__query_ids.add(query_hash)

        # Execute a query
        db_result = await connection.execute(query)
        result = None
        if db_result.returns_rows :
          result = list()
          row = await db_result.fetchone()
          while row is not None :
            row_values = dict()
            for column, value in row.items() :
              row_values[column] = value

            result.append(row_values)
            row = await db_result.fetchone()

        # Stop counter
        if self.__query_counter is not None :
          self.__query_counter.stop(query_uid)
          if counter is not None :
            counter.stop(query_uid)

        return Error(errOk), result
    except :
      error = Error(errExecuteFailed, sys.exc_info()[1])
      log_print_err("Query executing failed", error_code = error)
      # Stop counter
      if self.__query_counter is not None :
        self.__query_counter.stop(query_uid)
        if counter is not None :
          counter.stop(query_uid)

      return error, None

    error = Error(errUnknown, "Unknown state has been reached")
    return error, None

  @log_async_function_body()
  async def init(self) :
    """ Initialize DB connect """
    # Sometimes we needn't use DB. Check it by DB name.
    if len(self.database) == 0 :
      log_print_inf("Won't use any DB")
      return Error(errOk)

    log_print_inf("Initialize PostgreDB connect")
    try :
      self._engine = await create_engine(
          user = self.user, database = self.database, host = self.host,
          password= self.password, port = self.port)
    except :
      error = Error(errCannotInitDBConnect, sys.exc_info()[1])
      log_print_err("DB's connect initialization failed", error_code = error)
      return error

    return Error(errOk)

  # Initializes activity counters
  def init_activity_counters(self, count_time_flag = True) :
    super().init_activity_counters(count_time_flag)
    self.__query_counter = self.add_counter([_QUERY_COUNTER_NAME])

  # Denitializes activity counters
  def deinit_activity_counters(self) :
    self.__query_counter = None
    super().deinit_activity_counters()
