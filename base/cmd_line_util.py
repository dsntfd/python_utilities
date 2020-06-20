# Copyright 2017-2020 Denis Gushchin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import sys

# Export
__all__ = ('parse_cmd_line_argv', 'CommandLine',)


#
# Parses a command line and returns array of arrguments
#
def parse_cmd_line_argv(argv) :
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
  def __init__(self) :
    self.init_from_argv(sys.argv)

  def init_from_argv(self, argv) :
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

  def has_switch(self, name) :
    return self._switches.get(name) is not None

  def get_switch(self, name, default = None) :
    return self._switches.get(name, default)

  def get_switch_as_int(self, name, default = None) :
    result = None
    try:
      result = int(self._switches.get(name, default))
    except :
      result = None

    return result

  @property
  def arguments(self) :
    """ The switches of the command line """
    return self._arguments

  @property
  def program(self) :
    """ The program part of the command line """
    return self._program

  @property
  def switches(self) :
    """ The switches of the command line """
    return self._switches
