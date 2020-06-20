# Copyright 2017-2020 Denis Gushchin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import threading
import time

from .log import *


# Export
__all__ = ('WorkerThread',)


#
# WorkerThread
#
class WorkerThread (threading.Thread) :
  # Constructor
  def __init__(self, work_timeout, thread_id, thread_name = "WorkerThread") :
    threading.Thread.__init__(self)
    self.work_timeout = work_timeout
    self.thread_id = thread_id
    self.name = "{}_{:d}".format(thread_name, thread_id)
    self.stop_mutex = threading.RLock()
    self.stop_flag = False

  # Destructor
  def __del__(self) :
    self.stop_mutex = None

  def run(self) :
    log_print_inf("Thread started - {}", self.name)
    while True :
      # Check a stop conditon
      with self.stop_mutex :
        if self.stop_flag :
          break

      # Do work
      if not self.do_work() :
        break

      # Sleep
      if self.work_timeout != 0 :
        time.sleep(self.work_timeout)

    log_print_inf("Thread stopped - {}", self.name)

  def stopping(self) :
    with self.stop_mutex :
      self.stop_flag = True

  def do_work(self) :
    return True
