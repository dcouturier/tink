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

"""Tests for tink.python.testing.helper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import unittest
from tink.python.core import tink_error
from tink.python.testing import helper


class HelperTest(unittest.TestCase):

  def test_fake_mac_success(self):
    mac = helper.FakeMac('Name')
    mac_value = mac.compute_mac(b'data')
    mac.verify_mac(mac_value, b'data')

  def test_fake_mac_fail_wrong_data(self):
    mac = helper.FakeMac('Name')
    mac_value = mac.compute_mac(b'data')
    with self.assertRaisesRegex(tink_error.TinkError,
                                'invalid mac'):
      mac.verify_mac(mac_value, b'wrong data')

  def test_fake_mac_fail_wrong_primitive(self):
    mac = helper.FakeMac('Name')
    mac_value = mac.compute_mac(b'data')
    wrong_mac = helper.FakeMac('Wrong Name')
    with self.assertRaisesRegex(tink_error.TinkError,
                                'invalid mac'):
      wrong_mac.verify_mac(mac_value, b'data')

  def test_fake_aead_success(self):
    aead = helper.FakeAead('Name')
    ciphertext = aead.encrypt(b'plaintext', b'associated_data')
    self.assertEqual(
        aead.decrypt(ciphertext, b'associated_data'),
        b'plaintext')

  def test_fake_aead_fail_wrong_cipertext(self):
    aead = helper.FakeAead('Name')
    with self.assertRaisesRegex(tink_error.TinkError,
                                'failed to decrypt ciphertext'):
      aead.decrypt(b'wrong ciphertext', b'associated_data')

  def test_fake_aead_fail_wrong_associated_data(self):
    aead = helper.FakeAead('Name')
    ciphertext = aead.encrypt(b'plaintext', b'associated_data')
    with self.assertRaisesRegex(tink_error.TinkError,
                                'failed to decrypt ciphertext'):
      aead.decrypt(ciphertext, b'wrong_associated_data')

  def test_fake_aead_fail_wrong_primitive(self):
    aead = helper.FakeAead('Name')
    ciphertext = aead.encrypt(b'plaintext', b'associated_data')
    wrong_aead = helper.FakeAead('Wrong Name')
    with self.assertRaisesRegex(tink_error.TinkError,
                                'failed to decrypt ciphertext'):
      wrong_aead.decrypt(ciphertext, b'associated_data')

  def test_fake_deterministic_aead_success(self):
    daead = helper.FakeDeterministicAead('Name')
    ciphertext = daead.encrypt_deterministically(b'plaintext',
                                                 b'associated_data')
    self.assertEqual(
        daead.decrypt_deterministically(ciphertext, b'associated_data'),
        b'plaintext')

  def test_fake_deterministic_aead_fail_wrong_cipertext(self):
    daead = helper.FakeDeterministicAead('Name')
    with self.assertRaisesRegex(tink_error.TinkError,
                                'failed to decrypt ciphertext'):
      daead.decrypt_deterministically(b'wrong ciphertext', b'associated_data')

  def test_fake_deterministic_aead_fail_wrong_associated_data(self):
    daead = helper.FakeDeterministicAead('Name')
    ciphertext = daead.encrypt_deterministically(b'plaintext',
                                                 b'associated_data')
    with self.assertRaisesRegex(tink_error.TinkError,
                                'failed to decrypt ciphertext'):
      daead.decrypt_deterministically(ciphertext, b'wrong_associated_data')

  def test_fake_deterministic_aead_fail_wrong_primitive(self):
    daead = helper.FakeDeterministicAead('Name')
    ciphertext = daead.encrypt_deterministically(b'plaintext',
                                                 b'associated_data')
    wrong_daead = helper.FakeDeterministicAead('Wrong Name')
    with self.assertRaisesRegex(tink_error.TinkError,
                                'failed to decrypt ciphertext'):
      wrong_daead.decrypt_deterministically(ciphertext, b'associated_data')

  def test_fake_hybrid_success(self):
    enc = helper.FakeHybridEncrypt('Name')
    dec = helper.FakeHybridDecrypt('Name')
    ciphertext = enc.encrypt(b'plaintext', b'context_info')
    self.assertEqual(
        dec.decrypt(ciphertext, b'context_info'),
        b'plaintext')

  def test_fake_hybrid_fail_wrong_context(self):
    enc = helper.FakeHybridEncrypt('Name')
    dec = helper.FakeHybridDecrypt('Name')
    ciphertext = enc.encrypt(b'plaintext', b'context_info')
    with self.assertRaisesRegex(tink_error.TinkError,
                                'failed to decrypt ciphertext'):
      dec.decrypt(ciphertext, b'other_context_info')

  def test_fake_hybrid_fail_wrong_dec(self):
    enc = helper.FakeHybridEncrypt('Name')
    dec = helper.FakeHybridDecrypt('Wrong Name')
    ciphertext = enc.encrypt(b'plaintext', b'context_info')
    with self.assertRaisesRegex(tink_error.TinkError,
                                'failed to decrypt ciphertext'):
      dec.decrypt(ciphertext, b'context_info')

  def test_fake_hybrid_fail_wrong_ciphertext(self):
    dec = helper.FakeHybridDecrypt('Name')
    with self.assertRaisesRegex(tink_error.TinkError,
                                'failed to decrypt ciphertext'):
      dec.decrypt(b'wrong ciphertext', b'context_info')


if __name__ == '__main__':
  googletest.main()
