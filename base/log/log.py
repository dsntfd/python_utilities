# Copyright 2017-2020 Denis Gushchin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import datetime
import os
import sys
import threading

from ..file_util import *


# Export
__all__ = ('LOG_LEVEL_NONE', 'LOG_LEVEL_IMPORTANT', 'LOG_LEVEL_ERROR',
           'LOG_LEVEL_WARNING', 'LOG_LEVEL_INFO', 'LOG_LEVEL_VERBOSE',
           'ARG_LOG_FILE_MAX_SIZE', 'ARG_LOG_LEVEL', 'ARG_LOG_PATH',
           'ARG_LOG_IN_CONSOLE', 'init_log', 'init_log_by_cmd_line',
           'deinit_log', 'get_log_level', 'get_log_level_as_str',
           'get_log_max_file_size', 'get_log_path', 'is_log_in_console')


#
# Constants
#
_LOG_FILE_EXT = ".log"

#
# Log levels
#
LOG_LEVEL_NONE = -1
LOG_LEVEL_IMPORTANT = 0
LOG_LEVEL_ERROR = 1
LOG_LEVEL_WARNING = 2
LOG_LEVEL_INFO = 3
LOG_LEVEL_VERBOSE = 4

#
# Command line argument names
#
ARG_LOG_LEVEL = "log-level"
ARG_LOG_PATH = "log-path"
ARG_LOG_FILE_MAX_SIZE = "log-file-max-size"
ARG_LOG_IN_CONSOLE = "log-in-console"

#
# Global variables
#
_log_path = ""
_log_file_name = ""
_log_file = None
_log_file_max_size = -1
_log_level = LOG_LEVEL_NONE
_log_lock = None
_log_in_console = False


def _update_log_file() :
  global _log_file
  global _log_file_name

  # Get main file name
  file_name = os.path.basename(sys.argv[0])
  # Save previous log file name
  previous_name = _log_file_name
  # Create new log file name
  _log_file_name = os.path.join(
      _log_path,
      create_unique_file_name(
          file_name, "%016x" % os.getpid(), _LOG_FILE_EXT))
  _log_file_name = os.path.abspath(_log_file_name)
  # Create a log directory
  if not os.path.exists(os.path.dirname(_log_file_name)) :
    os.makedirs(os.path.dirname(_log_file_name))

  # If log file exists then to write message and close it
  if _log_file is not None :
    _log_file.write(bytes(
        "\n***** Next file: {} *****\n\n".format(_log_file_name), "utf-8"))
    _log_file.flush()
    _log_file.close()
    _log_file = None

  # Open file
  try :
    _log_file = open(_log_file_name, "wb")
  except :
    print("Can't open file - {}", _log_file_name)
    _log_file = None

  # Write log if previous file exists
  if _log_file is not None and len(previous_name) > 0 :
    _log_file.write(bytes(
        "***** Previous file: {} *****\n\n".format(previous_name), "utf-8"))

#
# Initializes logging system
#
def init_log(
    level, log_path, log_name = "", in_console = False,
    log_file_max_size = -1) :
  """ Initializes logging system """
  global _log_path
  global _log_file_name
  global _log_file
  global _log_file_max_size
  global _log_level
  global _log_lock
  global _log_in_console

  _log_level = level
  _log_in_console = in_console
  if _log_level <= LOG_LEVEL_NONE :
    return

  # Get date and msg_time
  date = datetime.datetime.now()

  # Open a log file
  if log_path is not None and len(log_path) > 0 :
    # Get main file name
    file_name = os.path.basename(sys.argv[0])
    # Normalize and get a log path
    _log_path = os.path.join(
        log_path, file_name, "{:%Y_%m_%d_%H_%M_%S}".format(date))
    _log_path = os.path.abspath(_log_path)
    # Save maximal file size
    _log_file_max_size = log_file_max_size
    # Open log file
    _update_log_file()

  # Create lock
  _log_lock = threading.RLock()

  # Check name
  if len(log_name) == 0 :
    log_name = "Log"

  # Write a log header
  from .log_util import log_print_imp
  log_print_imp("{:*^80}".format(""), without_prefix = True)
  log_print_imp("*" + "{: ^78}".format("") + "*", without_prefix = True)
  title = "{} {:%Y-%m-%d %H:%M:%S}".format(log_name, date)
  log_print_imp("*" + "{: ^78}".format(title) + "*", without_prefix = True)
  log_print_imp("*" + "{: ^78}".format("") + "*", without_prefix = True)
  log_print_imp("{:*^80}".format(""), without_prefix = True)

#
# Initializes logging system by command line
#
def init_log_by_cmd_line(cmd_line, log_name = "") :
  """ Initializes logging system by command line """
  log_path = cmd_line.get_switch(ARG_LOG_PATH, "")
  log_level = cmd_line.get_switch_as_int(ARG_LOG_LEVEL, LOG_LEVEL_NONE)
  log_in_console = cmd_line.has_switch(ARG_LOG_IN_CONSOLE)
  log_file_max_size = cmd_line.get_switch_as_int(ARG_LOG_FILE_MAX_SIZE, -1)
  init_log(log_level, log_path, log_name, log_in_console, log_file_max_size)

#
# Deinitializes logging system
#
def deinit_log() :
  """ Deinitializes log """
  global _log_file
  global _log_lock

  if _log_lock is None :
    return

  with _log_lock :
    # Write a log footer
    date = datetime.datetime.now()
    title = " {:%Y-%m-%d %H:%M:%S} ".format(date)
    from .log_util import log_print_imp
    log_print_imp("\n" + "{:*^80}".format(title), without_prefix = True)

    # Close a log file
    if not _log_file is None:
      _log_file.close()

  _log_file = None
  _log_level = LOG_LEVEL_NONE
  _log_lock = None

#
# Returns a logging level
#
def get_log_level() :
  """ Returns a log level """
  global _log_level
  return _log_level

#
# Returns a logging level as string
#
def get_log_level_as_str() :
  """ Returns a log level as string """
  global _log_level

  if _log_level <= LOG_LEVEL_NONE :
    return "NONE"
  elif _log_level == LOG_LEVEL_IMPORTANT :
    return "IMPORTANT"
  elif _log_level == LOG_LEVEL_ERROR :
    return "ERROR"
  elif _log_level == LOG_LEVEL_WARNING :
    return "WARNING"
  elif _log_level == LOG_LEVEL_INFO :
    return "INFO"

  return "VERBOSE"

#
# Returns a log maximal file size
#
def get_log_max_file_size() :
  """ Returns a log maximal file size """
  global _log_file_max_size
  return _log_file_max_size

#
# Returns a logging level
#
def get_log_path() :
  """ Returns a log path """
  global _log_path
  return _log_path

#
# Returns flag of printing logs into console
#
def is_log_in_console() :
  """ Returns flag of printing logs into console """
  global _log_in_console
  return _log_in_console
