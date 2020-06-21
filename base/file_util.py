# Copyright 2017-2020 Denis Gushchin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import datetime
import os
import sys

# Export
__all__ = ('create_unique_file_name', 'get_file_as_string', 'normalize_path')


#
# Creates a unique file name
#
def create_unique_file_name(file_prefix, file_affix, file_ext = "") :
  """ Create a unique file name """
  if len(file_prefix) :
    file_prefix = "".join([ c if c.isalnum() else "_" for c in file_prefix ])
    file_prefix += "_"

  if len(file_affix) :
    file_affix = "".join([ c if c.isalnum() else "_" for c in file_affix ])
    file_affix = "_" + file_affix

  date = datetime.datetime.now()
  result = "{}{:%Y_%m_%d_%H_%M_%S_}{:06d}{}{}".format(
      file_prefix, date, date.microsecond, file_affix, file_ext)
  return result

#
# Gets a file as string
#
def get_file_as_string(path, charset = "utf-8") :
  from .errors import Error
  from .log import log_print_err

  if not os.path.exists(path) :
    error = Error(errObjNotFound, "Path '{}' doesn't exist".format(path))
    log_print_err("Opening file failed", error_code = error)
    return error, None

  try :
    with open(path, 'r', encoding = charset) as file:
      result = file.read()
  except :
    error = Error(errException, sys.exc_info()[1])
    log_print_err("Reading file '{}' failed", path, error_code = error)
    return error, None

  return Error(errOk), result

#
# Normalizes a path
#
def normalize_path(path, backslash_flag = False) :
  """ Normalize a path """
  slash = "/"
  if backslash_flag :
    slash = "\\"

  if path[-1:] != "\\" or \
     path[-1:] != "/" :
    path += slash

  return path
