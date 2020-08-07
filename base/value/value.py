# Copyright 2017-2020 Denis Gushchin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import copy
import enum
import sys

from ..errors import *
from ..log import *

# Export
__all__ = ('Type', 'Value')

#
# Enumeration Type
#
@enum.unique
class Type (enum.Enum) :
  """ Value type enumeration """
  NONE = 0        #: Value type: Unknown
  BOOLEAN = 1     #: Value type: Boolean - ``False | True``
  INTEGER = 2     #: Value type: Integer - ``123``
  DOUBLE = 3      #: Value type: Double - ``123.45``
  STRING = 4      #: Value type: String - ``"String sample"``
  DICTIONARY = 5  #: Value type: Dictionary - ``[{name1, value1},...]``
  LIST = 6        #: Value type: List - ``[value1, value2,...]``

#
# Function type_to_str
#
def type_to_str(type) :
  """ Converts Type to string """
  if type == Type.BOOLEAN :
    return "BOOLEAN"
  elif type == Type.INTEGER :
    return "INTEGER"
  elif type == Type.DOUBLE :
    return "DOUBLE"
  elif type == Type.STRING :
    return "STRING"
  elif type == Type.DICTIONARY :
    return "DICTIONARY"
  elif type == Type.LIST :
    return "LIST"

  return "NONE"

#
# Class Value
#
class Value :
  """
    Wrapper over values

    Class is used for general work with values
  """
  def __init__(self, value = None, value_type = Type.NONE, default = None,
               optional = False, order_number = -1, init_children = False) :
    self._value = None
    self._value_type = Type.NONE
    self._default = None
    self._optional = optional
    self._order_number = order_number
    self._error = Error(errOk)
    self._operation_error = Error(errOk)

    # Check parameters
    value_type_by_value = Value.get_value_type(value, not init_children)
    # Check 'value'
    if value is not None and value_type_by_value == Type.NONE :
      self._error = Error(
          errObjNotInit,
          "Parameter \'value\' is invalid (\'value\': {})".format(repr(value)))
      log_print_err(None, error_code = self._error)
      return
     # Check 'value_type'
    elif value_type not in Type :
      self._error = Error(errObjNotInit,
                          "Parameter \'value_type\' must be \'Type\'")
      log_print_err(None, error_code = self._error)
      return
    # Check compatibility of 'value' and 'value_type'
    elif value is not None and value_type != Type.NONE and \
         value_type_by_value != value_type :
      self._error = Error(errObjNotInit, "Parameter \'value_type\' is invalid")
      log_print_err(None, error_code = self._error)
      return

    if value is not None :
      self._value = value
      self._value_type = value_type_by_value
      if init_children :
        self.__init_children__()
    else :
      self._value_type = value_type

    if default is not None and \
       Value.get_value_type(default) != self._value_type :
      self._error = Error(errObjNotInit, "Parameter \'default\' is invalid")
      log_print_err(None, error_code = self._error)
      self._value = None
      self._value_type = Type.NONE
      return

    self._default = default

  def __init_children__(self) :
    if isinstance(self._value, list) :
      for i in range(len(self._value)) :
        if not isinstance(self._value[i], Value) :
          self._value[i] = Value(
              self._value[i], init_children = True, optional = self._optional)

    if isinstance(self._value, dict) :
      for i in self._value.keys() :
        if not isinstance(self._value[i], Value) :
          self._value[i] = Value(
              self._value[i], init_children = True, optional = self._optional)

  def __contains__(self, item) :
    if self._value_type != Type.DICTIONARY :
      self._operation_error = Error(errFuncNotImplemented,
          "The only dictionary supports this operation")
      log_print_err(None, error_code = self._operation_error)
      return False

    return item in self._value

  def __eq__(self, other) :
    if self._value is None :
      return other is None

    return self._value == other

  def __getitem__(self, index) :
    error_code = Error(errOk)
    if self._value_type != Type.DICTIONARY and \
       self._value_type != Type.LIST :
      self._operation_error = Error(errInvalidAccess,
          "Simple value doesn't have an access by index")
      log_print_err(None, error_code = self._operation_error)
      return self.value

    result = None
    try :
      result = self._value[index]
    except :
      self._operation_error = Error(errInvalidAccess, sys.exc_info()[1])
      log_print_err(None, error_code = self._operation_error)

    return result

  def __len__(self) :
    if self._value_type != Type.DICTIONARY and \
       self._value_type != Type.LIST and \
       self._value_type != Type.STRING :
      self._operation_error = Error(errFuncNotImplemented,
          "This type doesn't support this operation")
      log_print_err(None, error_code = self._operation_error)
      return 0

    return len(self._value)

  def __setitem__(self, index, value) :
    error_code = Error(errOk)
    if self._value_type != Type.DICTIONARY and \
       self._value_type != Type.LIST :
      self._operation_error = Error(errInvalidUpdate,
          "Simple value doesn't set an value by index")
      log_print_err(None, error_code = self._operation_error)
      return

    # Initialize the '_value' if it is None
    if self._value is None :
      if self._value_type == Type.DICTIONARY :
        self._value = dict()
      elif self._value_type == Type.LIST :
        self._value = list()

    # Try to set a element of '_value'
    try :
      self._value[index] = value
    except :
      self._operation_error = Error(errInvalidUpdate, sys.exc_info()[1])
      log_print_err(None, error_code = self._operation_error)

  def __repr__(self) :
    module = ""
    if Error.__module__ is not None :
      module = Error.__module__ + "."

    return "<{}{} object at 0x{:x} : value:{} value_type:{} default:{} " \
           "optional:{} order_number:{} error:{} operation_error:{}>".format(
               module, Value.__qualname__, id(self), repr(self._value),
               str(self._value_type), repr(self._default), self._optional,
               self._order_number, repr(self._error),
               repr(self._operation_error))

  def __str__(self) :
    return "value:{} value_type:{} default:{} optional:{} " \
           "order_number:{} error:<{}>".format(
               str(self._value), str(self._value_type), str(self._default),
               self._optional, self._order_number, str(self._error))

  def clone(self) :
    """ Clone itself """
    result = copy.deepcopy(self)
    result._operation_error = Error(errOk)
    return result

  def find_path(self, path) :
    if not isinstance(path, list) :
      return None

    result = self
    for item in path :
      if result is None or \
         result.value_type != Type.DICTIONARY or \
         item not in result :
        return None

      result = result[item]

    return result

  def find_path_of_type(self, path, type, real_value = False, default = None) :
    result = self.find_path(path)
    if result is None or result.value_type != type :
      return default

    if real_value :
      real_result = result.value
      if result.value_type == Type.LIST :
        real_result = list()
        for item in result.value :
          real_result.append(item.value)
      elif result.value_type == Type.DICTIONARY :
        real_result = dict()
        for key, value in result.value.items() :
          real_result[key] = value.value

      result = real_result

    return result

  def find_bool_path(self, path, real_value = False, default = None) :
    return self.find_path_of_type(path, Type.BOOLEAN, real_value, default)

  def find_int_path(self, path, real_value = False, default = None) :
    return self.find_path_of_type(path, Type.INTEGER, real_value, default)

  def find_double_path(self, path, real_value = False, default = None) :
    return self.find_path_of_type(path, Type.DOUBLE, real_value, default)

  def find_string_path(self, path, real_value = False, default = None) :
    return self.find_path_of_type(path, Type.STRING, real_value, default)

  def find_dict_path(self, path, real_value = False, default = None) :
    return self.find_path_of_type(path, Type.DICTIONARY, real_value, default)

  def find_list_path(self, path, real_value = False, default = None) :
    return self.find_path_of_type(path, Type.LIST, real_value, default)

  def set_path(self, path, value) :
    if not isinstance(path, list) :
      self._operation_error = \
          Error(errInvalidParameter, "Parameter \'path\' is invalid")
      log_print_err(None, error_code = self._operation_error)
      return False

    if len(path) == 0 :
      self.value = value.value if isinstance(value, Value) else value
      return err_success(self._operation_error)

    parent = self
    for item in path[:-1] :
      if parent.value_type != Type.DICTIONARY :
        self._operation_error = \
            Error(errInvalidParameter, "Parameter \'path\' is invalid")
        log_print_err(None, error_code = self._operation_error)
        return False

      if item not in parent :
        parent[item] = Value(dict())

      parent = parent[item]

    parent[path[-1]] = value if isinstance(value, Value) else Value(value)

  def is_matching_type(self, value) :
    """ Check 'value' to match the object """
    value_type = Value.get_value_type(value)
    if self._value_type == Type.DOUBLE and value_type == Type.INTEGER :
      return True

    return self._value_type == value_type

  def is_valid(self) :
    """
      Check internal sate of objects

      :rtype: bool
    """
    result = err_success(self._error) and \
             (self._optional or self._value is not None)
    if result and self._value is not None and \
       self._value_type == Type.DICTIONARY :
      for key, value in self._value.items() :
        result = value.is_valid()
        if not result :
          break
    elif result and self._value is not None and \
         self._value_type == Type.LIST :
      for value in self._value :
        result = value.is_valid()
        if not result :
          break

    return result

  @property
  def default(self) :
    """ Default value """
    return self._default

  @default.setter
  def default(self, default) :
    """ Set default value """
    if err_failure(self._error) :
      self._operation_error = self._error
      log_print_err(None, error_code = self._operation_error)
      return

    if default is not None and \
       Value.get_value_type(default) != self._value_type :
      self._operation_error = Error(errInvalidParameter,
                                    "Parameter \'default\' is invalid")
      log_print_err(None, error_code = self._operation_error)
      return

    self._operation_error = Error(errOk)
    self._default = default

  @property
  def error(self) :
    """ Object internal error """
    return self._error

  @property
  def operation_error(self) :
    """ Internal error that has occured during last operation """
    return self._operation_error

  @property
  def optional(self) :
    """ Property is object has to be filled """
    return self._optional

  @optional.setter
  def optional(self, optional) :
    """ Set property \'optional\' """
    self._optional = optional

  def set_optional(self, optional, children = False) :
    self._optional = optional
    if children :
      if isinstance(self._value, list) :
        for i in range(len(self._value)) :
          self._value[i].set_optional(optional, children)

      if isinstance(self._value, dict) :
        for i in self._value.keys() :
          self._value[i].set_optional(optional, children)

  @property
  def order_number(self) :
    """ Property is object's order number among other objects """
    return self._order_number

  @order_number.setter
  def order_number(self, order_number) :
    """ Set property \'order_number\' """
    self._order_number = order_number

  @property
  def value(self) :
    """ Actual value """
    if self._value is None :
      return self._default

    return self._value

  @value.setter
  def value(self, value) :
    """ Set actual value """
    if err_failure(self._error) :
      self._operation_error = self._error
      log_print_err(None, error_code = self._error)
      return

    if value is not None and not self.is_matching_type(value) :
      self._operation_error = \
          Error(errInvalidParameter, "Parameter \'value\' is invalid")
      log_print_err(None, error_code = self._operation_error)
      return

    self._operation_error = Error(errOk)
    self._value = value

  @property
  def value_type(self) :
    """ Value type """
    return self._value_type

  @staticmethod
  def check_by_scheme(value, scheme, log_flag = True) :
    """
      Check Value object by scheme

      :rtype: Error
    """
    if not isinstance(value, Value) :
      error_code = Error(
          errInvalidParameter, "\"value\" must be object of Value")
      if log_flag : log_print_err(None, error_code = error_code)
      return error_code

    try :
      check_fun, error_code = Value._get_type_check_by_scheme(value)
      if err_failure(error_code) :
        if log_flag : log_print_err(None, error_code = error_code)
        return error_code

      return check_fun(value, scheme, log_flag)
    except :
      error_code = Error(errException, sys.exc_info()[1])
      if log_flag : log_print_err(
          "Error occured during checking Value by scheme",
          error_code = error_code)
      return error_code


  @staticmethod
  def get_value_type(value, check_content = True) :
    """
      Return a value type by a value

      :rtype: Type
    """
    if isinstance(value, bool) :
      return Type.BOOLEAN
    elif isinstance(value, int) :
      return Type.INTEGER
    elif isinstance(value, float) :
      return Type.DOUBLE
    elif isinstance(value, str) :
      return Type.STRING
    elif isinstance(value, dict) and \
         (not check_content or Value._check_dict(value)) :
      return Type.DICTIONARY
    elif isinstance(value, list) and \
         (not check_content or Value._check_list(value)) :
      return Type.LIST

    return Type.NONE

  @staticmethod
  def _check_dict(dict_value) :
    """ Check dictionary value for validity """
    if not isinstance(dict_value, dict) :
      return False

    for key, value in dict_value.items() :
      if not isinstance(value, Value) :
        return False

    return True

  @staticmethod
  def _check_list(list_value) :
    """ Check list value for validity """
    if not isinstance(list_value, list) :
      return False

    for value in list_value :
      if not isinstance(value, Value) :
        return False

    return True

  @staticmethod
  def _get_type_check_by_scheme(value) :
    if value.value_type == Type.BOOLEAN or \
       value.value_type == Type.INTEGER or \
       value.value_type == Type.DOUBLE or \
       value.value_type == Type.STRING :
      return Value._check_simple_type_by_scheme, Error(errOk)
    elif value.value_type == Type.DICTIONARY :
      return Value._check_dictionary_by_scheme, Error(errOk)
    elif value.value_type == Type.LIST :
      return Value._check_list_by_scheme, Error(errOk)

    error_code = Error(errUnknown, "Value has unknow type")
    log_print_err(None, error_code = error_code)
    return None, error_code

  @staticmethod
  def _check_simple_type_by_scheme(value, scheme, log_flag) :
    if value.value_type != scheme.value_type and \
       (value.value_type != Type.INTEGER or scheme.value_type != Type.DOUBLE) :
      error_code = Error(
          errInvalidType,
          "Value must be {} but it's {}".format(
              type_to_str(scheme.value_type), type_to_str(value.value_type)))
      if log_flag : log_print_err(None, error_code = error_code)
      return error_code

    return Error(errOk)

  @staticmethod
  def _check_dictionary_by_scheme(value, scheme, log_flag) :
    if value.value_type != scheme.value_type :
      error_code = Error(
          errInvalidType,
          "Value must be {} but it's {}".format(
              type_to_str(scheme.value_type), type_to_str(value.value_type)))
      if log_flag : log_print_err(None, error_code = error_code)
      return error_code

    if scheme.value is None :
      return Error(errOk)

    # Check fields by scheme
    for sub_key, sub_value in value.value.items() :
      if sub_key not in scheme :
        error_code = Error(
            errInvalidObject,
            "Dictionary has inappropriate field - \"{}\"".format(sub_key))
        if log_flag : log_print_err(None, error_code = error_code)
        return error_code

      check_fun, error_code = Value._get_type_check_by_scheme(sub_value)
      if err_failure(error_code) :
        error_code = Error(
            error_code.error_code,
            "Field \"{}\" is corrupted - {}".format(
                sub_key, error_code.error_msg))
        if log_flag : log_print_err(None, error_code = error_code)
        return error_code

      error_code = check_fun(sub_value, scheme[sub_key], log_flag)
      if err_failure(error_code) :
        error_code = Error(
            error_code.error_code,
            "Field \"{}\" is inappropriate - {}".format(
                sub_key, error_code.error_msg))
        if log_flag : log_print_err(None, error_code = error_code)
        return error_code

    # Check necessary fields by scheme
    for sub_key, sub_value in scheme.value.items() :
      if sub_value.optional or sub_key in value :
        continue

      error_code = Error(
          errInvalidObject,
          "Dictionary doesn't have field - \"{}\"".format(sub_key))
      if log_flag : log_print_err(None, error_code = error_code)
      return error_code

    return Error(errOk)

  @staticmethod
  def _check_list_by_scheme(value, scheme, log_flag) :
    if value.value_type != scheme.value_type :
      error_code = Error(
          errInvalidType,
          "Value must be {} but it's {}".format(
              type_to_str(scheme.value_type), type_to_str(value.value_type)))
      if log_flag : log_print_err(None, error_code = error_code)
      return error_code

    if scheme.value is None or len(scheme) != 1 :
      return Error(errOk)

    # Check items by scheme
    for index, sub_value in enumerate(value.value) :
      check_fun, error_code = Value._get_type_check_by_scheme(sub_value)
      if err_failure(error_code) :
        error_code = Error(
            error_code.error_code,
            "Item[{}] is corrupted - {}".format(index, error_code.error_msg))
        if log_flag : log_print_err(None, error_code = error_code)
        return error_code

      error_code = check_fun(sub_value, scheme[0], log_flag)
      if err_failure(error_code) :
        error_code = Error(
            error_code.error_code,
            "Item[{}] is inappropriate - {}".format(
                index, error_code.error_msg))
        if log_flag : log_print_err(None, error_code = error_code)
        return error_code

    return Error(errOk)
