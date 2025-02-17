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

"""Tests for tink.python.keyset_handle."""

from __future__ import absolute_import
from __future__ import division
from __future__ import google_type_annotations
from __future__ import print_function

import io

import unittest
from tink.proto import tink_pb2
from tink.python import aead
from tink.python import core
from tink.python import hybrid
from tink.python import mac
from tink.python.core import tink_config
from tink.python.testing import helper


def setUpModule():
  tink_config.register()


class FaultyAead(aead.Aead):

  def encrypt(self, plaintext: bytes, associated_data: bytes) -> bytes:
    raise core.TinkError('encrypt failed.')

  def decrypt(self, plaintext: bytes, associated_data: bytes) -> bytes:
    raise core.TinkError('decrypt failed.')


class BadAead1(aead.Aead):

  def encrypt(self, plaintext: bytes, associated_data: bytes) -> bytes:
    return b'ciphertext'

  def decrypt(self, plaintext: bytes, associated_data: bytes) -> bytes:
    return b'plaintext'


class BadAead2(aead.Aead):

  def encrypt(self, plaintext: bytes, associated_data: bytes) -> bytes:
    return b'ciphertext'

  def decrypt(self, plaintext: bytes, associated_data: bytes) -> bytes:
    return tink_pb2.Keyset(primary_key_id=42).SerializeToString()


def _master_key_aead():
  return core.Registry.primitive(
      core.Registry.new_key_data(aead.aead_key_templates.AES128_EAX),
      aead.Aead)


class KeysetHandleTest(unittest.TestCase):

  def test_generate_new(self):
    keyset_info = core.new_keyset_handle(
        mac.mac_key_templates.HMAC_SHA256_128BITTAG).keyset_info()
    self.assertLen(keyset_info.key_info, 1)
    key_info = keyset_info.key_info[0]
    self.assertEqual(key_info.status, tink_pb2.ENABLED)
    self.assertEqual(
        key_info.output_prefix_type,
        mac.mac_key_templates.HMAC_SHA256_128BITTAG.output_prefix_type)
    self.assertEqual(keyset_info.primary_key_id, key_info.key_id)

  def test_generate_new_key_id_is_randomized(self):
    handle1 = core.new_keyset_handle(
        mac.mac_key_templates.HMAC_SHA256_128BITTAG)
    handle2 = core.new_keyset_handle(
        mac.mac_key_templates.HMAC_SHA256_128BITTAG)
    self.assertNotEqual(handle1.keyset_info().key_info[0].key_id,
                        handle2.keyset_info().key_info[0].key_id)

  def test_write_encrypted(self):
    handle = core.new_keyset_handle(
        mac.mac_key_templates.HMAC_SHA256_128BITTAG)
    # Encrypt the keyset with Aead.
    master_key_aead = _master_key_aead()
    output_stream = io.BytesIO()
    writer = core.BinaryKeysetWriter(output_stream)
    handle.write(writer, master_key_aead)
    reader = core.BinaryKeysetReader(output_stream.getvalue())
    handle2 = core.read_keyset_handle(reader, master_key_aead)
    # Check that handle2 has the same primitive as handle.
    handle2.primitive(mac.Mac).verify_mac(
        handle.primitive(mac.Mac).compute_mac(b'data'), b'data')

  def test_write_raises_error_when_encrypt_failed(self):
    handle = core.new_keyset_handle(
        mac.mac_key_templates.HMAC_SHA256_128BITTAG)
    writer = core.BinaryKeysetWriter(io.BytesIO())
    with self.assertRaisesRegex(core.TinkError, 'encrypt failed'):
      handle.write(writer, FaultyAead())

  def test_write_raises_error_when_decrypt_not_possible(self):
    handle = core.new_keyset_handle(
        mac.mac_key_templates.HMAC_SHA256_128BITTAG)
    writer = core.BinaryKeysetWriter(io.BytesIO())
    with self.assertRaisesRegex(core.TinkError,
                                'invalid keyset, corrupted key material'):
      handle.write(writer, BadAead1())

  def test_write_raises_error_when_decrypt_to_wrong_keyset(self):
    handle = core.new_keyset_handle(
        mac.mac_key_templates.HMAC_SHA256_128BITTAG)
    writer = core.BinaryKeysetWriter(io.BytesIO())
    with self.assertRaisesRegex(core.TinkError, 'cannot encrypt keyset:'):
      handle.write(writer, BadAead2())

  def test_read_empty_keyset_fails(self):
    with self.assertRaisesRegex(core.TinkError, 'No keyset found'):
      core.read_keyset_handle(
          core.BinaryKeysetReader(b''), _master_key_aead())

  def test_public_keyset_handle(self):
    private_handle = core.new_keyset_handle(
        hybrid.hybrid_key_templates.ECIES_P256_HKDF_HMAC_SHA256_AES128_GCM)
    public_handle = private_handle.public_keyset_handle()
    hybrid_dec = private_handle.primitive(hybrid.HybridDecrypt)
    hybrid_enc = public_handle.primitive(hybrid.HybridEncrypt)

    self.assertEqual(public_handle.keyset_info().primary_key_id,
                     private_handle.keyset_info().primary_key_id)
    self.assertLen(public_handle.keyset_info().key_info, 1)
    self.assertEqual(
        public_handle.keyset_info().key_info[0].type_url,
        'type.googleapis.com/google.crypto.tink.EciesAeadHkdfPublicKey')

    ciphertext = hybrid_enc.encrypt(b'some plaintext', b'some context info')
    self.assertEqual(
        hybrid_dec.decrypt(ciphertext, b'some context info'), b'some plaintext')

  def test_primitive_success(self):
    keyset = tink_pb2.Keyset()
    key = keyset.key.add()
    key.key_data.CopyFrom(
        core.Registry.new_key_data(aead.aead_key_templates.AES128_EAX))
    key.output_prefix_type = tink_pb2.TINK
    key.key_id = 1
    key.status = tink_pb2.ENABLED
    keyset.primary_key_id = 1
    handle = core.KeysetHandle(keyset)
    aead_primitive = handle.primitive(aead.Aead)
    self.assertEqual(
        aead_primitive.decrypt(
            aead_primitive.encrypt(b'message', b'aad'), b'aad'), b'message')

  def test_primitive_fails_on_empty_keyset(self):
    keyset = tink_pb2.Keyset()
    keyset.key.extend([helper.fake_key(key_id=1, status=tink_pb2.DESTROYED)])
    keyset.primary_key_id = 1
    handle = core.KeysetHandle(keyset)
    with self.assertRaisesRegex(core.TinkError, 'empty keyset'):
      handle.primitive(aead.Aead)

  def test_primitive_fails_on_key_without_keydata(self):
    keyset = tink_pb2.Keyset()
    key = helper.fake_key(key_id=123)
    key.ClearField('key_data')
    keyset.key.extend([key])
    keyset.primary_key_id = 123
    handle = core.KeysetHandle(keyset)
    with self.assertRaisesRegex(core.TinkError,
                                'key 123 has no key data'):
      handle.primitive(aead.Aead)

  def test_primitive_fails_on_key_with_unknown_prefix(self):
    keyset = tink_pb2.Keyset()
    keyset.key.extend([
        helper.fake_key(key_id=12, output_prefix_type=tink_pb2.UNKNOWN_PREFIX)
    ])
    keyset.primary_key_id = 12
    handle = core.KeysetHandle(keyset)
    with self.assertRaisesRegex(core.TinkError,
                                'key 12 has unknown prefix'):
      handle.primitive(aead.Aead)

  def test_primitive_fails_on_key_with_unknown_status(self):
    keyset = tink_pb2.Keyset()
    keyset.key.extend(
        [helper.fake_key(key_id=1234, status=tink_pb2.UNKNOWN_STATUS)])
    keyset.primary_key_id = 1234
    handle = core.KeysetHandle(keyset)
    with self.assertRaisesRegex(core.TinkError,
                                'key 1234 has unknown status'):
      handle.primitive(aead.Aead)

  def test_primitive_fails_on_multiple_primary_keys(self):
    keyset = tink_pb2.Keyset()
    keyset.key.extend(
        [helper.fake_key(key_id=12345),
         helper.fake_key(key_id=12345)])
    keyset.primary_key_id = 12345
    handle = core.KeysetHandle(keyset)
    with self.assertRaisesRegex(core.TinkError,
                                'keyset contains multiple primary keys'):
      handle.primitive(aead.Aead)

  def test_primitive_fails_without_primary_key_present(self):
    keyset = tink_pb2.Keyset()
    key = keyset.key.add()
    key.key_data.CopyFrom(
        core.Registry.new_key_data(aead.aead_key_templates.AES128_EAX))
    key.output_prefix_type = tink_pb2.TINK
    key.key_id = 2
    key.status = tink_pb2.ENABLED
    keyset.primary_key_id = 1
    handle = core.KeysetHandle(keyset)
    with self.assertRaisesRegex(core.TinkError,
                                'keyset does not contain a valid primary key'):
      handle.primitive(aead.Aead)

  def test_primitive_fails_on_wrong_primitive_class(self):
    keyset = tink_pb2.Keyset()
    key = keyset.key.add()
    key.key_data.CopyFrom(
        core.Registry.new_key_data(aead.aead_key_templates.AES128_EAX))
    key.output_prefix_type = tink_pb2.TINK
    key.key_id = 1
    key.status = tink_pb2.ENABLED
    keyset.primary_key_id = 1
    handle = core.KeysetHandle(keyset)
    with self.assertRaisesRegex(core.TinkError, 'Wrong primitive class'):
      handle.primitive(mac.Mac)

  def test_primitive_wrapped_correctly(self):
    keydata2 = core.Registry.new_key_data(
        aead.aead_key_templates.AES128_EAX)
    keyset = tink_pb2.Keyset()
    key = keyset.key.add()
    key.key_data.CopyFrom(
        core.Registry.new_key_data(aead.aead_key_templates.AES128_EAX))
    key.output_prefix_type = tink_pb2.TINK
    key.key_id = 1
    key.status = tink_pb2.ENABLED
    key = keyset.key.add()
    key.key_data.CopyFrom(keydata2)
    key.output_prefix_type = tink_pb2.RAW
    key.key_id = 2
    key.status = tink_pb2.ENABLED
    keyset.primary_key_id = 1
    handle = core.KeysetHandle(keyset)
    aead_primitive = handle.primitive(aead.Aead)
    aead_primitive2 = core.Registry.primitive(keydata2, aead.Aead)
    self.assertEqual(
        aead_primitive.decrypt(
            aead_primitive2.encrypt(b'message', b'aad'), b'aad'), b'message')

  def test_keyset_info(self):
    keyset = tink_pb2.Keyset(primary_key_id=2)
    keyset.key.extend([
        helper.fake_key(
            value=b'v1',
            type_url='t1',
            key_id=1,
            status=tink_pb2.ENABLED,
            output_prefix_type=tink_pb2.TINK),
        helper.fake_key(
            value=b'v2',
            type_url='t2',
            key_id=2,
            status=tink_pb2.DESTROYED,
            output_prefix_type=tink_pb2.RAW)
    ])
    handle = core.KeysetHandle(keyset)
    expected_keyset_info = tink_pb2.KeysetInfo(primary_key_id=2)
    info1 = expected_keyset_info.key_info.add()
    info1.type_url = 't1'
    info1.status = tink_pb2.ENABLED
    info1.output_prefix_type = tink_pb2.TINK
    info1.key_id = 1
    info2 = expected_keyset_info.key_info.add()
    info2.type_url = 't2'
    info2.status = tink_pb2.DESTROYED
    info2.output_prefix_type = tink_pb2.RAW
    info2.key_id = 2
    self.assertEqual(expected_keyset_info, handle.keyset_info())


if __name__ == '__main__':
  googletest.main()
