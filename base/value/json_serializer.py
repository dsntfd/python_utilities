# Copyright 2017-2020 Denis Gushchin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""
  Module includes json serializing and deserializing functions for Value
"""

import collections
import json
import sys

from .value import *
from ..errors import *
from ..log import *


# Export
__all__ = ('serialize_value_to_json', 'deserialize_json_to_value')


NULL_STRING = "null"

#
# Function serialize_value_to_json
#
@log_function_body
def serialize_value_to_json(root_value, charset = "utf-8") :
  """ Serialize the data structure represented by Value into JSON """
  error_code = Error(errOk)
  result = ""
  if not isinstance(root_value, Value) or not root_value.is_valid() :
    error_code = Error(errInvalidParameter,
                       "Parameter \'root_value\' is invalid")
    log_print_err(None, error_code = error_code)
    return error_code, result

  error_code, result = \
      _serializing_function_dict[root_value.value_type](root_value, charset)
  if err_failure(error_code) :
    log_print_err(None, error_code = error_code)

  return error_code, result

#
# Function deserialize_json_to_value
#
@log_function_body
def deserialize_json_to_value(json_text, scheme_value = None,
                              charset = "utf-8") :
  """
    Deserialise the data structure encoded in JSON \
    into a structure of Value objects
  """
  error_code = Error(errOk)
  # Parse json to native values
  try :
    json_value = json.loads(json_text,
                            object_pairs_hook = collections.OrderedDict)
  except :
    error_code = Error(errInvalidParameter, sys.exc_info()[1])
    log_print_err(None, error_code = error_code)
    return error_code, None

  # Fill structure of Value objects
  value_type = Value.get_value_type(json_value, False)
  if value_type == Type.NONE :
    error_code = Error(errInvalidParameter, "Json has an unknown value type")
    log_print_err(None, error_code = error_code)
    return error_code, None

  # Deserialize a json value into a Value
  error_code, result = _deserializing_function_dict[value_type](
                       json_value, scheme_value, charset)
  if err_failure(error_code) :
    log_print_err(None, error_code = error_code)

  return error_code, result

#
# Help functions for serializing
#
def _serialize_boolean_value(value, charset) :
  """ Serialize boolean value """
  error_code = Error(errOk)
  if value is None :
    return error_code, NULL_STRING

  result = "true" if value.value else "false"
  return error_code, result

def _serialize_dictionary_value(value, charset) :
  """ Serialize dictionary value """
  error_code = Error(errOk)
  if value is None :
    return error_code, NULL_STRING

  result = "{"
  comma = ""
  for key, child_value in sorted(
      value.value.items(),
      key = lambda value: (value[1].order_number, value[0])) :
    result += comma
    result += "\"" + key + "\":"
    error_code, result_str = \
        _serializing_function_dict[child_value.value_type](child_value, charset)
    if err_failure(error_code) :
      log_print_err(None, error_code = error_code)
      return error_code, ""

    result += result_str
    comma = ","

  result += "}"
  return error_code, result

def _serialize_list_value(value, charset) :
  """ Serialize list value """
  error_code = Error(errOk)
  if value is None :
    return error_code, NULL_STRING

  result = "["
  comma = ""
  for child_value in sorted(value.value,
                            key = lambda value: (value.order_number)) :
    result += comma
    error_code, result_str = \
        _serializing_function_dict[child_value.value_type](child_value, charset)
    if err_failure(error_code) :
      log_print_err(None, error_code = error_code)
      return error_code, ""

    result += result_str
    comma = ","

  result += "]"
  return error_code, result

def _serialize_none_value(value, charset) :
  return Error(errOk), NULL_STRING

def _serialize_simple_value(value, charset) :
  """ Serialize simple value """
  error_code = Error(errOk)
  if value is None :
    return error_code, NULL_STRING

  result = "{}".format(value.value)
  return error_code, result

def _escape_json_string(raw_str) :
  """ Escape special characters """
  result = ""
  index = 0
  begin_index = 0
  for char in raw_str :
    escaped = None
    if char == '\b' :
      escaped = "\\b"
    elif char == '\f' :
      escaped = "\\f"
    elif char == '\n' :
      escaped = "\\n"
    elif char == '\r' :
      escaped = "\\r"
    elif char == '\t' :
      escaped = "\\t"
    elif char == '\\' :
      escaped = "\\\\"
    elif char == '\"' :
      escaped = "\\\""

    if escaped is not None :
      result += raw_str[begin_index : index]
      result += escaped
      begin_index = index + 1

    index += 1

  result += raw_str[begin_index :]
  return result

def _serialize_string_value(value, charset) :
  """ Serialize string value """
  error_code = Error(errOk)
  if value is None :
    return error_code, NULL_STRING

  # Encode result by charset
  result = value.value.encode(charset).decode(charset)
  # Escape special characters
  result = _escape_json_string(result)
  # Print value
  result = "\"" + result + "\""
  return error_code, result

#: Dictionary of functions for serializing by types
_serializing_function_dict = {
  Type.NONE : _serialize_none_value,
  Type.BOOLEAN : _serialize_boolean_value,
  Type.INTEGER : _serialize_simple_value,
  Type.DOUBLE : _serialize_simple_value,
  Type.STRING : _serialize_string_value,
  Type.DICTIONARY : _serialize_dictionary_value,
  Type.LIST : _serialize_list_value
}

#
# Help functions for deserializing
#
def _deserialize_boolean_value(json_value, value_scheme, charset) :
  """ Deserialize boolean value """
  error_code = Error(errOk)
  # Check a scheme types
  if value_scheme is not None and value_scheme.value_type != Type.BOOLEAN :
    error_code = Error(errInvalidParameter, "Json doesn't match the scheme")
    log_print_err(None, error_code = error_code)
    return error_code, None

  # Create Value or take out of scheme
  result = Value(value_type = value_scheme.value_type) \
           if value_scheme is not None else \
           Value(value_type = Type.BOOLEAN)
  result.value = json_value
  return error_code, result

def _deserialize_dictionary_value(json_value, value_scheme, charset) :
  """ Deserialize dictionary value """
  error_code = Error(errOk)
  # Check a scheme types
  if value_scheme is not None and value_scheme.value_type != Type.DICTIONARY :
    error_code = Error(errInvalidParameter, "Json doesn't match the scheme")
    log_print_err(None, error_code = error_code)
    return error_code, None

  # Create Value or take out of scheme
  result = \
      Value(value_type = Type.DICTIONARY, default = value_scheme.default,
            optional = value_scheme.optional,
            order_number = value_scheme.order_number) \
      if value_scheme is not None else \
      Value(value_type = Type.DICTIONARY)
  if result.value is None :
    result.value = dict()

  # Add child Values
  order_number = 0
  for key, value in json_value.items() :
    child_value_type = Value.get_value_type(value, False)
    if value is not None and child_value_type == Type.NONE :
      error_code = Error(errInvalidParameter, "Json has an unknown value type")
      log_print_err(None, error_code = error_code)
      return error_code, None

    # Get a scheme of the child item
    child_scheme = value_scheme[key] if value_scheme is not None else None
    if value_scheme is not None and child_scheme is None :
      error_code = Error(errInvalidParameter, "Json doesn't match the scheme")
      log_print_err(None, error_code = error_code)
      return error_code, None

    if value is not None :
      error_code, result[key] = _deserializing_function_dict[child_value_type](
                                value, child_scheme, charset)
    else :
      result[key] = Value()

    if err_failure(error_code) :
      log_print_err("Field is invalid:\'{}\'", key, error_code = error_code)
      return error_code, None

    # Set a order number as into incoming json
    result[key].order_number = order_number
    order_number += 1

  # Check necessary fields by scheme
  if value_scheme is not None :
    for key, value in value_scheme.value.items() :
      if not value.optional and key not in result :
        error_code = Error(errInvalidParameter, "Json doesn't match the scheme")
        log_print_err("Field isn't filled:\'{}\'", key, error_code = error_code)
        return error_code, None

  return error_code, result

def _deserialize_double_value(json_value, value_scheme, charset) :
  """ Deserialize double value """
  error_code = Error(errOk)
  # Check a scheme types
  if value_scheme is not None and value_scheme.value_type != Type.DOUBLE :
    error_code = Error(errInvalidParameter, "Json doesn't match the scheme")
    log_print_err(None, error_code = error_code)
    return error_code, None

  # Create Value or take out of scheme
  result = Value(value_type = value_scheme.value_type) \
           if value_scheme is not None else \
           Value(value_type = Type.DOUBLE)
  result.value = json_value
  return error_code, result

def _deserialize_integer_value(json_value, value_scheme, charset) :
  """ Deserialize integer value """
  error_code = Error(errOk)
  # Check a scheme types
  if value_scheme is not None and \
     not value_scheme.is_matching_type(json_value) :
    error_code = Error(errInvalidParameter, "Json doesn't match the scheme")
    log_print_err(None, error_code = error_code)
    return error_code, None

  # Create Value or take out of scheme
  result = Value(value_type = value_scheme.value_type) \
           if value_scheme is not None else \
           Value(value_type = Type.INTEGER)
  result.value = json_value
  return error_code, result

def _deserialize_list_value(json_value, value_scheme, charset) :
  """ Deserialize list value """
  error_code = Error(errOk)
  # Check a scheme types
  if value_scheme is not None and value_scheme.value_type != Type.LIST :
    error_code = Error(errInvalidParameter, "Json doesn't match the scheme")
    log_print_err(None, error_code = error_code)
    return error_code, None

  # Create Value or take out of scheme
  result = \
      Value(value_type = Type.LIST, default = value_scheme.default,
            optional = value_scheme.optional,
            order_number = value_scheme.order_number) \
      if value_scheme is not None else \
      Value(value_type = Type.LIST)
  if result.value is None :
    result.value = list()

  # Add child Values
  for value in json_value :
    child_value_type = Value.get_value_type(value, False)
    if child_value_type == Type.NONE :
      error_code = Error(errInvalidParameter, "Json has an unknown value type")
      log_print_err(None, error_code = error_code)
      return error_code, None

    # Get a scheme of the child item
    child_scheme = value_scheme[0].clone() \
                   if value_scheme is not None and \
                      len(value_scheme) == 1 \
                   else None
    if value_scheme is not None and child_scheme is None :
      error_code = Error(errInvalidParameter, "Json doesn't match the scheme")
      log_print_err(None, error_code = error_code)
      return error_code, None

    error_code, child_item = _deserializing_function_dict[child_value_type](
                             value, child_scheme, charset)
    if err_failure(error_code) :
      log_print_err(None, error_code = error_code)
      return error_code, None

    result.value.append(child_item)

  return error_code, result

def _deserialize_string_value(json_value, value_scheme, charset) :
  """ Deserialize string value """
  error_code = Error(errOk)
  # Check a scheme types
  if value_scheme is not None and value_scheme.value_type != Type.STRING :
    error_code = Error(errInvalidParameter, "Json doesn't match the scheme")
    log_print_err(None, error_code = error_code)
    return error_code, None

  # Create Value or take out of scheme
  result = Value(value_type = value_scheme.value_type) \
           if value_scheme is not None else \
           Value(value_type = Type.STRING)
  result.value = json_value.encode(charset).decode(charset)
  return error_code, result

#: Dictionary of functions for serializing by types
_deserializing_function_dict = {
  Type.BOOLEAN : _deserialize_boolean_value,
  Type.INTEGER : _deserialize_integer_value,
  Type.DOUBLE : _deserialize_double_value,
  Type.STRING : _deserialize_string_value,
  Type.DICTIONARY : _deserialize_dictionary_value,
  Type.LIST : _deserialize_list_value
}
