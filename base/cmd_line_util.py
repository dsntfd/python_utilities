# Copyright 2017-2020 Denis Gushchin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json
import sys

from typing import Any
from typing import NoReturn

# Export
__all__ = ('parse_cmd_line_argv', 'CommandLine',)

#: Name of command line argument for configuration
ARG_CMD_LINE_CONFIG = "cmd-line-config"

#: Argument section name in config file
JF_CMD_LINE_ARGUMENTS = "arguments"

#
# Parses a command line and returns array of arrguments
#
def parse_cmd_line_argv(argv) -> list :
  """ Parse arguments by scheme - ``--<key>=<value>`` """
  result = list()
  for arg in argv :
    if not isinstance(arg, str) or len(arg) == 0 :
      continue

    if len(arg) <= 2 or (arg[0] != '-' and arg[1] != '-') :
      result.append(["", arg])
      continue

    name_end = 2
    while name_end < len(arg) and arg[name_end] != '=' :
      name_end += 1

    result.append([arg[2 : name_end], arg[name_end + 1 : len(arg)]])

  return result

#
# Class CommandLine
#
class CommandLine :
  """
    Implementation a work with command line
  """
  def __init__(self) -> NoReturn :
    self.init_from_argv(sys.argv)

  def init_from_argv(self, argv) -> NoReturn :
    self._program = \
        argv[0] if len(argv) > 0 and isinstance(argv[0], str) else ""
    self._switches = dict()
    self._arguments = list()
    cmd_line = parse_cmd_line_argv(argv[1:])
    for item in cmd_line :
      if len(item[0]) > 0 :
        self._switches[item[0]] = item[1]
      elif len(item[1]) > 0:
        self._arguments.append(item[1])

    self.__update_by_config()

  def has_switch(self, name) -> bool :
    return name in self._switches.keys()

  def get_switch(self, name, default = None) -> Any :
    return self._switches.get(name, default)

  def get_switch_as_int(self, name, default = None) -> int :
    result = None
    try:
      result = int(self._switches.get(name, default))
    except :
      result = None

    return result

  @property
  def arguments(self) -> list :
    """ The switches of the command line """
    return self._arguments

  @property
  def program(self) -> str :
    """ The program part of the command line """
    return self._program

  @property
  def switches(self) -> list :
    """ The switches of the command line """
    return self._switches

  def __update_by_config(self) -> NoReturn :
    if ARG_CMD_LINE_CONFIG not in self._switches :
      return

    try :
      file_content = None
      with open(self.get_switch(ARG_CMD_LINE_CONFIG), 'r') as config_file :
        file_content = config_file.read()

      json_value = json.loads(file_content)
    except :
      return

    if not isinstance(json_value, dict) :
      return

    for key, value in json_value.items() :
      # Don't rewrite real switches
      if self.has_switch(key) :
        continue

      # Check section of arguments
      if key == JF_CMD_LINE_ARGUMENTS :
        if value is None or not isinstance(value, list) :
          continue

        for arg in value :
          self._arguments.append(arg)

        continue

      # Add new switch
      self._switches[key] = value
