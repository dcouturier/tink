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

"""Tests for tink.python.core."""

from __future__ import absolute_import
from __future__ import division
from __future__ import google_type_annotations
from __future__ import print_function

import io

import unittest
from tink.proto import tink_pb2
from tink.python import core


def example_keyset():
  keyset = tink_pb2.Keyset()
  keyset.primary_key_id = 42
  key = keyset.key.add()
  key.key_data.type_url = u'type.googleapis.com/google.crypto.tink.AesGcmKey'
  key.key_data.key_material_type = tink_pb2.KeyData.SYMMETRIC
  key.key_data.value = b'GhCS/1+ejWpx68NfGt6ziYHd'
  key.output_prefix_type = tink_pb2.TINK
  key.key_id = 42
  key.status = tink_pb2.ENABLED
  return keyset


def example_encrypted_keyset():
  encrypted_keyset = tink_pb2.EncryptedKeyset()
  encrypted_keyset.encrypted_keyset = b'c29tZSBjaXBoZXJ0ZXh0IHdpdGgga2V5c2V0'
  encrypted_keyset.keyset_info.primary_key_id = 42
  key_info = encrypted_keyset.keyset_info.key_info.add()
  key_info.type_url = 'type.googleapis.com/google.crypto.tink.AesGcmKey'
  key_info.output_prefix_type = tink_pb2.TINK
  key_info.key_id = 42
  key_info.status = tink_pb2.ENABLED
  return encrypted_keyset


class JsonKeysetWriterTest(unittest.TestCase):

  def test_write_read(self):
    keyset = example_keyset()
    stream = io.StringIO()
    writer = core.JsonKeysetWriter(stream)
    writer.write(keyset)
    reader = core.JsonKeysetReader(stream.getvalue())
    self.assertEqual(keyset, reader.read())

  def test_write_encrypted_read_encrypted(self):
    encrypted_keyset = example_encrypted_keyset()
    stream = io.StringIO()
    writer = core.JsonKeysetWriter(stream)
    writer.write_encrypted(encrypted_keyset)
    reader = core.JsonKeysetReader(stream.getvalue())
    self.assertEqual(encrypted_keyset, reader.read_encrypted())

  def test_write_read_with_unicode_chars(self):
    keyset = tink_pb2.Keyset()
    key = keyset.key.add()
    key.key_data.type_url = (
        u'\xe3\x82\xb3\xe3\x83\xb3\xe3\x83\x8b\xe3\x83\x81\xe3\x83\x8f')
    stream = io.StringIO()
    writer = core.JsonKeysetWriter(stream)
    writer.write(keyset)
    reader = core.JsonKeysetReader(stream.getvalue())
    self.assertEqual(keyset, reader.read())

  def test_write_invalid_fails(self):
    with self.assertRaisesRegex(core.TinkError, 'invalid keyset'):
      stream = io.StringIO()
      writer = core.JsonKeysetWriter(stream)
      writer.write(example_encrypted_keyset())

  def test_write_encrypted_invalid_fails(self):
    with self.assertRaisesRegex(core.TinkError, 'invalid encrypted keyset'):
      stream = io.StringIO()
      writer = core.JsonKeysetWriter(stream)
      writer.write_encrypted(example_keyset())


class BinaryKeysetReaderTest(unittest.TestCase):

  def test_write_read(self):
    keyset = example_keyset()
    stream = io.BytesIO()
    writer = core.BinaryKeysetWriter(stream)
    writer.write(keyset)
    reader = core.BinaryKeysetReader(stream.getvalue())
    self.assertEqual(keyset, reader.read())

  def test_write_encrypted_read_encrypted(self):
    encrypted_keyset = example_encrypted_keyset()
    stream = io.BytesIO()
    writer = core.BinaryKeysetWriter(stream)
    writer.write_encrypted(encrypted_keyset)
    reader = core.BinaryKeysetReader(stream.getvalue())
    self.assertEqual(encrypted_keyset, reader.read_encrypted())

  def test_write_invalid_fails(self):
    with self.assertRaisesRegex(core.TinkError, 'invalid keyset'):
      stream = io.BytesIO()
      writer = core.BinaryKeysetWriter(stream)
      writer.write(example_encrypted_keyset())

  def test_write_encrypted_invalid_fails(self):
    with self.assertRaisesRegex(core.TinkError, 'invalid encrypted keyset'):
      stream = io.BytesIO()
      writer = core.BinaryKeysetWriter(stream)
      writer.write_encrypted(example_keyset())


if __name__ == '__main__':
  googletest.main()
