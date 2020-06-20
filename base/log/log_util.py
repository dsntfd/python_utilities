# Copyright 2017-2020 Denis Gushchin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import datetime
import inspect
import os
import sys
import threading

from . import log as log
from ..errors import *
from ..file_util import *
from functools import wraps


# Export
__all__ = ('log_print_imp', 'log_print_err', 'log_print_wrn', 'log_print_inf',
           'log_print_vrb', 'log_print_parameters', 'log_print',
           'log_async_function_body', 'log_function_body', 'log_print_file',
           'async_log_print_file')


#
# Global variables
#
_log_file_counter = 0


#
# log_print wrappers
#
def log_print_imp(msg, *args, error_code = None, exec_time = 0.0,
                  without_prefix = False, out_frame_index = 1, **kwargs) :
  return log_print(log.LOG_LEVEL_IMPORTANT, msg, *args, error_code = error_code,
                   exec_time = exec_time, without_prefix = without_prefix,
                   out_frame_index = out_frame_index + 1, **kwargs)

def log_print_err(msg, *args, error_code = None, exec_time = 0.0,
                  without_prefix = False, out_frame_index = 1, **kwargs) :
  if msg is None :
    msg = "Error has occured"

  return log_print(log.LOG_LEVEL_ERROR, msg, *args, error_code = error_code,
                   exec_time = exec_time, without_prefix = without_prefix,
                   out_frame_index = out_frame_index + 1, **kwargs)

def log_print_wrn(msg, *args, error_code = None, exec_time = 0.0,
                  without_prefix = False, out_frame_index = 1, **kwargs) :
  return log_print(log.LOG_LEVEL_WARNING, msg, *args, error_code = error_code,
                   exec_time = exec_time, without_prefix = without_prefix,
                   out_frame_index = out_frame_index + 1, **kwargs)

def log_print_inf(msg, *args, error_code = None, exec_time = 0.0,
                  without_prefix = False, out_frame_index = 1, **kwargs) :
  return log_print(log.LOG_LEVEL_INFO, msg, *args, error_code = error_code,
                   exec_time = exec_time, without_prefix = without_prefix,
                   out_frame_index = out_frame_index + 1, **kwargs)

def log_print_vrb(msg, *args, error_code = None, exec_time = 0.0,
                  without_prefix = False, out_frame_index = 1, **kwargs) :
  return log_print(log.LOG_LEVEL_VERBOSE, msg, *args, error_code = error_code,
                   exec_time = exec_time, without_prefix = without_prefix,
                   out_frame_index = out_frame_index + 1, **kwargs)

def log_print_parameters(parameters) :
  # Check parameters to be dictionary
  if not isinstance(parameters, dict) :
    return

  # Calculate size of string
  str_length = max(parameters.keys(), key = lambda k: len("{}".format(k)))
  str_length = len("{}".format(str_length))
  if str_length == 0 :
    return

  # Make string for printing
  str_template = " {: <" + "{:d}".format(str_length + 1) + "}"
  str = "Parameters:\n"
  for key, value in parameters.items() :
    str += str_template.format("{}".format(key)) + "- "
    if isinstance(value, bool) :
      str += "{}".format("True" if value else "False")
    elif isinstance(value, int) :
      str += "{:d}".format(value)
    else :
      str += "{}".format("{}".format(value))

    str += "\n"

  # Print parameters
  log_print_imp(str, without_prefix = True)

#
# Write message to log
# Example:
# log_print(LOG_LEVEL_ERROR, "Error message {}. Error code {:d}.", msg, error)
# log_print(LOG_LEVEL_INFO, "Function {} run.", name, exec_time = 11.23)
# log_print(LOG_LEVEL_IMPORTANT, "Message {}", msg, without_prefix = True)
#
def log_print(level, msg, *args, error_code = None, exec_time = 0.0,
              without_prefix = False, out_frame_index = 1, **kwargs) :
  if log._log_lock is None :
    return False

  with log._log_lock :
    if level > log._log_level :
      return False

  return_value = True

  # Get a thread id
  thread_id = threading.current_thread().ident

  # Get a prefix for message
  prefix = "VRBS "
  if level == log.LOG_LEVEL_IMPORTANT :
    prefix = "IMPNT"
  elif level == log.LOG_LEVEL_ERROR :
    prefix = "ERROR"
  elif level == log.LOG_LEVEL_WARNING :
    prefix = "WARN "
  elif level == log.LOG_LEVEL_INFO :
    prefix = "INFO "

  # Infomation of file and code
  msg_code_info = ""
  if not error_code is None :
    if isinstance(error_code, int) :
      error_code = Error(error_code)

    if isinstance(error_code, Error) :
      msg_code_info = " ({})".format(error_code)

  if level == log.LOG_LEVEL_ERROR or level == log.LOG_LEVEL_WARNING :
    frame_info = inspect.getouterframes(inspect.currentframe())[out_frame_index]
    if not frame_info is None :
      msg_code_info = msg_code_info + \
          " (file:{} line:{} func:{} locals:{})".format(
              frame_info.filename, frame_info.lineno, frame_info.function,
              frame_info.frame.f_locals)

  # Create a message
  msg_time = datetime.datetime.now()
  try :
    msg = msg.format(*args, **kwargs)
  except :
    return_value = False

  if exec_time != 0.0 :
    msg = "{} (execution time: {:.6f} s)".format(msg, exec_time)

  if not without_prefix :
    msg = "{:%Y-%m-%d %H:%M:%S}.{:06d} {:016X} {} {}".format(
        msg_time, msg_time.microsecond, thread_id, prefix, msg)

  msg = msg + msg_code_info

  # Write a message to log
  with log._log_lock :
    # Write in file
    if log._log_file is not None :
      log._log_file.write(bytes(msg, "utf-8"))
      log._log_file.write(bytes("\n", "utf-8"))
      log._log_file.flush()
    # Write in console
    if log._log_in_console :
      print(msg)

  return return_value


#
# Async-function wrapper for logging body and time
#
# Example:
# @log_async_function_body()
# async def my_func(...) :
#   ...
#
def log_async_function_body() :
  def wrapper(func) :
    @wraps(func)
    async def wrapped(*args, **kwargs) :
      begin_time = datetime.datetime.now()
      func_id = "{:%Y%m%d%H%M%S}-{:06d}".format(begin_time,
                                                begin_time.microsecond)
      log_print_vrb(
          "Async-function begin - {}(id: {})", func.__qualname__, func_id,
          out_frame_index = 1)
      result =  await func(*args, **kwargs)
      log_print_vrb(
          "Async-function end - {} (id: {})", func.__qualname__, func_id,
          exec_time = (datetime.datetime.now() - begin_time).total_seconds(),
          out_frame_index = 1)
      return result

    return wrapped

  return wrapper

#
# Function wrapper for logging body and time
#
# Example:
# @log_function_body
# def my_func(...) :
#   ...
#
def log_function_body(func) :
  @wraps(func)
  def wrapper(*args, **kwargs) :
    begin_time = datetime.datetime.now()
    log_print_vrb("Function begin - {}", func.__qualname__, out_frame_index = 1)
    result = func(*args, **kwargs)
    log_print_vrb("Function end - {}", func.__qualname__,
        exec_time = (datetime.datetime.now() - begin_time).total_seconds(),
        out_frame_index = 1)
    return result

  return wrapper

#
# Write a separated log file for message
#
def log_print_file(level, file_prefix, msg, *args,
                   out_frame_index = 1, **kwargs) :
  global _log_file_counter

  if log._log_lock is None :
    return Error(errObjNotInit, "Log hasn't initialized")

  file_affix = ""
  with log._log_lock :
    if level > log._log_level or \
       log._log_file is None :
      return Error(wrnObjNotSaved)

    _log_file_counter +=1
    file_affix = "{:02d}".format(_log_file_counter)

  file_path = log._log_file_name + "." + \
      create_unique_file_name(file_prefix, file_affix, log._LOG_FILE_EXT)

  # Create directory
  if not os.path.exists(os.path.dirname(file_path)) :
    try :
      os.makedirs(os.path.dirname(file_path))
    except FileExistsError :
      log_print_vrb("Directory exists - {}", os.path.dirname(file_path))
    except :
      result = Error(errCannotMakeDir, sys.exc_info()[1])
      log_print_err("Directory making failed - {}", os.path.dirname(file_path),
                    error_code = result)
      return result

  # Save file
  try :
    with open(file_path, "wb") as file :
      file_body = bytearray()
      if isinstance(msg, str) :
        file_body.extend(msg.encode("utf-8"))
      elif isinstance(msg, bytes) :
        file_body.extend(msg)
      elif callable(msg) :
        file_body.extend(msg(*args, **kwargs))
      else :
        result = Error(errNotSupportType,
            "log_print_file hasn't understood parameter \'msg\' (type:{})".
            format(type(msg)))
        log_print_err("Error ocurred", error_code = result)
        return result

      file.write(file_body)
  except :
    result = Error(errCannotWriteFile, sys.exc_info()[1])
    log_print_err("File saving failed - {}", file_path, error_code = result)
    return result

  log_print(level, "Saved log file: {}", file_path,
            out_frame_index = out_frame_index + 1)

  return Error(errOk)

#
# Function async_log_print_file
#
async def async_log_print_file(level, file_prefix, msg, *args,
                               out_frame_index = 1, **kwargs) :
  """ Write a separated log file for message (async implementation) """
  if log._log_lock is None :
    return Error(errObjNotInit, "Log hasn't initialized")

  with log._log_lock :
    if level > log._log_level or \
       log._log_file is None :
      return Error(wrnObjNotSaved)

  if callable(msg) :
    try :
      body = await msg(*args, **kwargs)
    except :
      result = Error(errFuncFailed, sys.exc_info()[1])
      log_print_err(None, error_code = result)
      return result

  return log_print_file(level, file_prefix, body, *args,
                        out_frame_index = out_frame_index + 1, **kwargs)
