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

"""Tests for tink.python.deterministic_aead_key_templates."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import unittest
from tink.proto import aes_siv_pb2
from tink.proto import tink_pb2
from tink.python.daead import deterministic_aead_key_templates


class DeterministicAeadKeyTemplatesTest(unittest.TestCase):

  def test_aes256_siv(self):
    template = deterministic_aead_key_templates.AES256_SIV
    self.assertEqual('type.googleapis.com/google.crypto.tink.AesSivKey',
                     template.type_url)
    self.assertEqual(tink_pb2.TINK, template.output_prefix_type)
    key_format = aes_siv_pb2.AesSivKeyFormat()
    key_format.ParseFromString(template.value)
    self.assertEqual(64, key_format.key_size)

  def test_create_aes_siv_key_template(self):
    # Intentionally using 'weird' or invalid values for parameters,
    # to test that the function correctly puts them in the resulting template.
    template = deterministic_aead_key_templates.create_aes_siv_key_template(
        key_size=42)
    self.assertEqual('type.googleapis.com/google.crypto.tink.AesSivKey',
                     template.type_url)
    self.assertEqual(tink_pb2.TINK, template.output_prefix_type)
    key_format = aes_siv_pb2.AesSivKeyFormat()
    key_format.ParseFromString(template.value)
    self.assertEqual(42, key_format.key_size)

if __name__ == '__main__':
  googletest.main()
