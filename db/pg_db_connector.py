# Copyright 2017-2020 Denis Gushchin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import asyncio

from .db_connector import *
from aiopg.sa import create_engine
from base.errors import *
from base.log import *
from sqlalchemy.dialects import postgresql


#
# Class DBConnector
#
class PgDBConnector (DBConnector) :
  def __init__(self, user = "", password = "", database = "",
               host = "", port = 5432) :
    DBConnector.__init__(self, user, password, database, host, port)

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
    try :
      # https://stackoverflow.com/questions/5631078/sqlalchemy-print-the-actual-query
      # compile_kwargs={"literal_binds": True}
      log_print_vrb(
          "SQL query: \n{}", str(query.compile(dialect = postgresql.dialect())))
    except :
      log_print_vrb("Can't convert SQL query to string ({})", sys.exc_info()[1])

    try :
      async with self._engine.acquire() as connection:
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

        return Error(errOk), result
    except :
      error = Error(errExecuteFailed, sys.exc_info()[1])
      log_print_err("Query executing failed", error_code = error)
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
