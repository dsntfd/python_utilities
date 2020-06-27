# Copyright 2017-2020 Denis Gushchin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import datetime

from ..errors import *
from ..value import *
from .log_util import *

# Export
__all__ = ('ActivityCounter',)

# Json names
_JSON_NAME_STARTED_AT = "started_at"
_JSON_NAME_COUNTER = "counter"
_JSON_NAME_LAST_CALLED_AT = "last_called_at"
_JSON_NAME_TOTAL_TIME = "total_time"
_JSON_NAME_MIN_TIME = "min_time"
_JSON_NAME_MAX_TIME = "max_time"

class ActivityCounter :
  __create_key = object()
  __counters = dict()

  @classmethod
  def add(cls, name, count_time_flag = True) :
    counter = cls.__counters.get(name)
    if counter is None :
      cls.__counters[name] = cls(cls.__create_key, name, count_time_flag)

    return cls.__counters.get(name)

  @classmethod
  def get(cls, name) :
    return cls.__counters.get(name)

  @classmethod
  def get_all_counter_names(cls) :
    return list(cls.__counters.keys())

  @classmethod
  def pop_counter(cls, name, default = None) :
    result = cls.__counters.pop(name, None)
    if result is not None :
      return result

    return default

  @classmethod
  def start(cls, name, id = "") :
    item = cls.__counters.get(name)
    if item is not None :
      return item.start(id)

    return False

  @classmethod
  def stop(cls, name, id = "") :
    item = cls.__counters.get(name)
    if item is not None :
      return item.stop(id)

    return False

  @staticmethod
  def now() :
    return datetime.datetime.now(tz = datetime.timezone.utc)

  def __init__(self, create_key, name, count_time_flag = True) :
    assert(create_key == ActivityCounter.__create_key), \
        "ActivityCounter objects must be created using ActivityCounter.add"
    self.__items = dict()
    self.__started_at = ActivityCounter.now()
    self.__last_called_at = None
    self.__name = name
    self.__count_time_flag = count_time_flag
    self.__counter = 0
    self.__time_counter = datetime.timedelta() if count_time_flag else None
    self.__min_time = None
    self.__max_time = None

  def start(self, id = "") :
    item = self.__items.get(id)
    if item is not None :
      return False

    class ItemMock :
      pass

    item = ItemMock()
    item.started_at = ActivityCounter.now() if self.__count_time_flag else None
    self.__items[id] = item
    return True

  def stop(self, id = "") :
    item = self.__items.pop(id, None)
    if item is None :
      return False

    if not self.__count_time_flag :
      self.__counter += 1
      self.__last_called_at = ActivityCounter.now()
    elif self.__count_time_flag and item.started_at is not None :
      self.__counter += 1
      self.__last_called_at = ActivityCounter.now()
      time_delta = self.__last_called_at - item.started_at
      self.__time_counter += time_delta
      if self.__min_time is None :
        self.__min_time = time_delta
        self.__max_time = time_delta
      else :
        self.__min_time = min([ self.__min_time, time_delta ])
        self.__max_time = max([ self.__max_time, time_delta ])

    del item
    return True

  def is_count_time(self) :
    return self.__count_time_flag

  def get_as_value(self) :
    result = Value(dict())
    result[_JSON_NAME_STARTED_AT] = Value(
        "{:%Y-%m-%d %H:%M:%S}.{:06d}{:%z}".format(
            self.__started_at, self.__started_at.microsecond,
            self.__started_at))
    result[_JSON_NAME_COUNTER] = Value(self.__counter)

    if self.__last_called_at is not None :
      result[_JSON_NAME_LAST_CALLED_AT] = Value(
          "{:%Y-%m-%d %H:%M:%S}.{:06d}{:%z}".format(
              self.__last_called_at, self.__last_called_at.microsecond,
              self.__last_called_at))

    if self.__count_time_flag :
      result[_JSON_NAME_TOTAL_TIME] = Value(self.__time_counter.total_seconds())
      if self.__min_time is not None :
        result[_JSON_NAME_MIN_TIME] = Value(self.__min_time.total_seconds())
        result[_JSON_NAME_MAX_TIME] = Value(self.__max_time.total_seconds())

    return result

  @property
  def started_at(self) :
    return self.__started_at

  @property
  def name(self) :
    return self.__name

  @property
  def counter(self) :
    return self.__counter

  @property
  def time_counter(self) :
    return self.__time_counter

  @property
  def min_time(self) :
    return self.__min_time

  @property
  def max_time(self) :
    return self.__max_time
