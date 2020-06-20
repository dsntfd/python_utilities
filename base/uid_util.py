# Copyright 2017-2020 Denis Gushchin. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import uuid


# Export
__all__ = ('generate_uuid', 'create_uid')


#
# Function generate_uuid
#
def generate_uuid() :
  """ Generate new Universally Unique IDentifier (UUID) """
  uuid_obj = uuid.uuid4()
  uuid_str = "{0[0]:02x}{0[1]:02x}{0[2]:02x}{0[3]:02x}{0[4]:02x}{0[5]:02x}" \
             "{0[6]:02x}{0[7]:02x}{0[8]:02x}{0[9]:02x}{0[10]:02x}{0[11]:02x}" \
             "{0[12]:02x}{0[13]:02x}{0[14]:02x}{0[15]:02x}".format(
             uuid_obj.bytes)
  return uuid_obj, uuid_str

#
# Function create_uid
#
def create_uid(uid = "", uid_prefix = None, uid_suffix = None) :
  """ Create Unique IDentifier (UID) by parameters """
  if len(uid) == 0 :
    uuid_obj, uid = generate_uuid()

  if not uid_prefix is None :
    uid_prefix = "{}/".format(uid_prefix)
  else :
    uid_prefix = ""

  if not uid_suffix is None :
    uid_suffix = "/{}".format(uid_suffix)
  else :
    uid_suffix = ""

  return "{}{}{}".format(uid_prefix, uid, uid_suffix)
