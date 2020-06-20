# Copyright 2017-2020 Denis Gushchin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""
  Error codes, class Error and help functions
"""

import inspect


#
# OK
#
errOk = 0

#
# Help-functions
#
def err_number(error) :
  """ Return a error number """
  result = errOk
  if isinstance(error, int) :
    result = error
  elif isinstance(error, Error) :
    result = error.error_code

  if result < 0 :
    result = (result - ErrorBaseNumber) * -1

  return result

def err_success(error) :
  """ Check a error on success """
  error_code = errUnknown
  if isinstance(error, int) :
    error_code = error
  elif isinstance(error, Error) :
    error_code = error.error_code

  return error_code >= 0

def err_failure(error) :
  """ Check a error on failure """
  return not err_success(error)

#
# Class Error
#
class Error :
  """ Object describes a error """
  def __init__(self, error_code = errOk, error_msg = "") :
    self._error_code = error_code
    self._error_msg = str(error_msg)
    self._module_name = ""
    self._module_line = -1
    if isinstance(error_code, Error) :
      self._error_code = error_code._error_code
      self._error_msg = error_code._error_msg
      self._module_name = error_code._module_name
      self._module_line = error_code._module_line
    elif self._error_code != errOk :
      frame_info = inspect.getouterframes(inspect.currentframe())[1]
      if not frame_info is None :
        self._module_name = frame_info.filename
        self._module_line = frame_info.lineno

  def __bool__(self) :
    return err_success(self)

  def __repr__(self) :
    module = ""
    if Error.__module__ is not None :
      module = Error.__module__ + "."

    return "<{}{} object at 0x{:x} : {}>".format(
               module, Error.__qualname__, id(self), self.__str__())

  def __str__(self) :
    result = "{}:0x{:08X}".format(
        "error" if err_failure(self._error_code) else "code",
        err_number(self.error_code))
    if (len(self._error_msg) > 0) :
      result = "{} msg:\'{}\'".format(result, self._error_msg)

    if (len(self._module_name) > 0) :
      result = "{} module:{}".format(result, self._module_name)

    if (self._module_line >= 0) :
      result = "{} line:{}".format(result, self._module_line)

    return result

  @property
  def error_code(self) :
    """ Error code """
    return self._error_code

  @property
  def error_msg(self) :
    """ Error message """
    return self._error_msg

  @property
  def module_name(self) :
    """ Module name where error has occured """
    return self._module_name

  @property
  def module_line(self) :
    """ Module line where error has occured """
    return self._module_line

#
# Warnings
#

# Warning constants
WarnBaseNumber = errOk #: Warning base naumber
WarnStepSize = 0x1000  #: Step size for different type warning

# Common warnings
CommonWarnBaseNumber = WarnBaseNumber             #: Common warning base number
wrnNothingDone = CommonWarnBaseNumber + 0x3       #: Warning: Nothing has been done (0x3)
wrnObjNotFound = CommonWarnBaseNumber + 0x4       #: Warning: Object hasn't been found (0x4)
wrnObjNotSaved = CommonWarnBaseNumber + 0x1       #: Warning: Object hasn't been saved (0x1)
wrnTimeout = CommonWarnBaseNumber + 0x2           #: Warning: The timeout period have expired (0x2)
CommonWarnLastNumber = CommonWarnBaseNumber + 0x5 #: Error: Common warning last number (0x5)

#
# Errors
#

# Error constants
ErrorBaseNumber = -0x10000000 #: Error base number
ErrorStepSize = 0x1000        #: Step size for different type error

# Common errors
CommonErrorBaseNumber = ErrorBaseNumber              #: Common error base number (0x0)
errAccessDenied = CommonErrorBaseNumber - 0x11       #: Error: Access denied (0x11)
errCannotMakeDir = CommonErrorBaseNumber - 0x5       #: Error: Can't make directory (0x5)
errCannotWriteFile = CommonErrorBaseNumber - 0x6     #: Error: Can't write file (0x6)
errException = CommonErrorBaseNumber - 0xe           #: Error: Exception occurs (0xe)
errFuncFailed = CommonErrorBaseNumber - 0xd          #: Error: Error occurs during function's calling (0xd)
errFuncNotImplemented = CommonErrorBaseNumber - 0x3  #: Error: Function hasn't been implemented (0x3)
errInvalidAccess = CommonErrorBaseNumber - 0x8       #: Error: Try to access to information by invalid reference (0x8)
errInvalidObject = CommonErrorBaseNumber - 0xb       #: Error: Invalid object (0xb)
errInvalidParameter = CommonErrorBaseNumber - 0x2    #: Error: Invalid parameter (0x2)
errInvalidType = CommonErrorBaseNumber - 0xf         #: Error: Invalid type (0xf)
errInvalidUpdate = CommonErrorBaseNumber - 0x9       #: Error: Try to update information by invalid reference (0x9)
errNotSupportType = CommonErrorBaseNumber - 0x7      #: Error: Don't support variable type (0x7)
errObjAlreadyInit = CommonErrorBaseNumber - 0xc      #: Error: Object has already beed initialized (0xc)
errObjNotInit = CommonErrorBaseNumber - 0x4          #: Error: Object hasn't beed initialized (0x4)
errObjNotFound = CommonErrorBaseNumber - 0x10        #: Error: Object hasn't beed found (0x10)
errParsingFailed = CommonErrorBaseNumber - 0xa       #: Error: Can't parse xml or json or etc (0xa)
errUnknown = CommonErrorBaseNumber - 0x1             #: Error: Unknown error (0x1)
CommonErrorLastNumber = CommonErrorBaseNumber - 0x12 #: Error: Common error last number (0x12)

# Net error
NetErrorBaseNumber = CommonErrorBaseNumber - ErrorStepSize #: Net error base number (0x1000)
errAPIVersionNotSupported = NetErrorBaseNumber - 0xa       #: Error: API version isn't supported (0x100a)
errCannotDeinitServer = NetErrorBaseNumber - 0x2           #: Error: Can't deinitialize server (0x1002)
errCannotInitServer = NetErrorBaseNumber - 0x1             #: Error: Can't initialize server (0x1001)
errCannotReadAPIVersion = NetErrorBaseNumber - 0x9         #: Error: Can't read content (0x1009)
errCannotReadContent = NetErrorBaseNumber - 0x8            #: Error: Can't read content (0x1008)
errCannotSendEmail = NetErrorBaseNumber - 0xb              #: Error: Sending email failed (0x100b)
errInternalServerError = NetErrorBaseNumber - 0x3          #: Error: Internal server error (0x1003)
errMethodNotImplemented = NetErrorBaseNumber - 0x6         #: Error: Method hasn't been implemented (0x1006)
errMethodNotSupported = NetErrorBaseNumber - 0x7           #: Error: Method isn't supported (0x1007)
errNotSupportUrl = NetErrorBaseNumber - 0x4                #: Error: Don't support URL (0x1004)
errRequestFailed = NetErrorBaseNumber - 0x5                #: Error: Error occurs during url's requesting (0x1005)
NetErrorLastNumber = NetErrorBaseNumber - 0xc              #: Error: Net error last number (0x100c)

# DB error
DBErrorBaseNumber = NetErrorBaseNumber - ErrorStepSize #: DB error base number (0x2000)
errCannotDeinitDBConnect = DBErrorBaseNumber - 0x2     #: Error: Can't deinitialize DB connect (0x2002)
errCannotInitDBConnect = DBErrorBaseNumber - 0x1       #: Error: Can't initialize DB connect (0x2001)
errExecuteFailed = DBErrorBaseNumber - 0x3             #: Error: Error occurs during query's executing (0x2003)
errQueryFormingFailed = DBErrorBaseNumber - 0x4        #: Error: Query forming failed (0x2004)
DBErrorLastNumber = DBErrorBaseNumber - 0x5            #: Error: Net error last number (0x2005)
