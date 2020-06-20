# Copyright 2017-2020 Denis Gushchin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""
  Module includes time utilities
"""

import datetime


# Export
__all__ = ('Timer',)


#
# Class Timer
#
class Timer :
  """
    Realize functionality of timer

    Class is used for to measure time intervals

    :param start: flag of to start timer right away
    :type start: bool
    :param name: name of Timer
    :type name: string
  """
  def __init__(self, start = True, name = "") :
    self._time_delta = datetime.timedelta()
    self._name = name
    if start :
      self._start_time = datetime.datetime.now()
    else :
      self._start_time = None

  def restart(self) :
    """ Restart timer """
    self.stop()
    self._time_delta = datetime.timedelta()
    self.start()

  def start(self) :
    """ Start timer """
    if self._start_time is None :
      self._start_time = datetime.datetime.now()

  def stop(self) :
    """ Stop timer """
    if self._start_time is not None :
      self._time_delta += datetime.datetime.now() - self._start_time
      self._start_time = None

  @property
  def delta(self) :
    """ Time delta """
    return self._time_delta

  @property
  def name(self) :
    """ Name of timer """
    return self._name

  @name.setter
  def name(self, name) :
    """ Set a name of timer """
    self._name = name

  @property
  def seconds(self) :
    """ Time delta in seconds """
    return self._time_delta.total_seconds()
