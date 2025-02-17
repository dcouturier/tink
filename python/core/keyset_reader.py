# Copyright 2019 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Reads KeySets from File."""

from __future__ import absolute_import
from __future__ import division
from __future__ import google_type_annotations
from __future__ import print_function

import abc

from typing import Text

from tink.proto import tink_pb2
from tink.python.core import tink_error
from google3.net.proto2.python.public import json_format
from google3.net.proto2.python.public import message


class KeysetReader(object):
  """Reads a Keyset."""

  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def read(self) -> tink_pb2.Keyset:
    """Reads and returns a (cleartext) tink_pb2.Keyset from its source."""
    pass

  @abc.abstractmethod
  def read_encrypted(self) -> tink_pb2.EncryptedKeyset:
    """Reads and returns an tink_pb2.EncryptedKeyset from its source."""
    pass


class JsonKeysetReader(KeysetReader):
  """Reads a JSON Keyset."""

  def __init__(self, serialized_keyset: Text):
    self._serialized_keyset = serialized_keyset

  def read(self) -> tink_pb2.Keyset:
    try:
      return json_format.Parse(self._serialized_keyset, tink_pb2.Keyset())
    except json_format.ParseError as e:
      raise tink_error.TinkError(e)

  def read_encrypted(self) -> tink_pb2.EncryptedKeyset:
    try:
      return json_format.Parse(self._serialized_keyset,
                               tink_pb2.EncryptedKeyset())
    except json_format.ParseError as e:
      raise tink_error.TinkError(e)


class BinaryKeysetReader(KeysetReader):
  """Reads a binary Keyset."""

  def __init__(self, serialized_keyset: bytes):
    self._serialized_keyset = serialized_keyset

  def read(self) -> tink_pb2.Keyset:
    if not self._serialized_keyset:
      raise tink_error.TinkError('No keyset found')
    try:
      keyset = tink_pb2.Keyset()
      keyset.ParseFromString(self._serialized_keyset)
      return keyset
    except message.DecodeError as e:
      raise tink_error.TinkError(e)

  def read_encrypted(self) -> tink_pb2.EncryptedKeyset:
    if not self._serialized_keyset:
      raise tink_error.TinkError('No keyset found')
    try:
      encrypted_keyset = tink_pb2.EncryptedKeyset()
      encrypted_keyset.ParseFromString(self._serialized_keyset)
      return encrypted_keyset
    except message.DecodeError as e:
      raise tink_error.TinkError(e)
