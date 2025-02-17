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

"""Tests for tink.python.cc.clif.py_key_manager."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import unittest
from tink.proto import aes_eax_pb2
from tink.proto import aes_siv_pb2
from tink.proto import common_pb2
from tink.proto import ecdsa_pb2
from tink.proto import ecies_aead_hkdf_pb2
from tink.proto import hmac_pb2
from tink.proto import tink_pb2
from tink.python.aead import aead_key_templates
from tink.python.cc.clif import cc_key_manager
from tink.python.cc.clif import cc_tink_config
from tink.python.hybrid import hybrid_key_templates
from tink.util import error


def setUpModule():
  cc_tink_config.register()


class AeadKeyManagerTest(unittest.TestCase):

  def setUp(self):
    super(AeadKeyManagerTest, self).setUp()
    self.key_manager = cc_key_manager.AeadKeyManager.from_cc_registry(
        'type.googleapis.com/google.crypto.tink.AesEaxKey')

  def new_aes_eax_key_template(self, iv_size, key_size):
    key_format = aes_eax_pb2.AesEaxKeyFormat()
    key_format.params.iv_size = iv_size
    key_format.key_size = key_size
    key_template = tink_pb2.KeyTemplate()
    key_template.type_url = 'type.googleapis.com/google.crypto.tink.AesEaxKey'
    key_template.value = key_format.SerializeToString()
    return key_template

  def test_key_type(self):
    self.assertEqual(self.key_manager.key_type(),
                     'type.googleapis.com/google.crypto.tink.AesEaxKey')

  def test_new_key_data(self):
    key_template = self.new_aes_eax_key_template(12, 16)
    key_data = self.key_manager.new_key_data(key_template)
    self.assertEqual(key_data.type_url, self.key_manager.key_type())
    self.assertEqual(key_data.key_material_type, tink_pb2.KeyData.SYMMETRIC)
    key = aes_eax_pb2.AesEaxKey()
    key.ParseFromString(key_data.value)
    self.assertEqual(key.version, 0)
    self.assertEqual(key.params.iv_size, 12)
    self.assertLen(key.key_value, 16)

  def test_invalid_params_throw_exception(self):
    key_template = self.new_aes_eax_key_template(9, 16)
    with self.assertRaises(error.StatusNotOk):
      self.key_manager.new_key_data(key_template)

  def test_encrypt_decrypt(self):
    aead = self.key_manager.primitive(
        self.key_manager.new_key_data(self.new_aes_eax_key_template(12, 16)))
    plaintext = b'plaintext'
    associated_data = b'associated_data'
    ciphertext = aead.encrypt(plaintext, associated_data)
    self.assertEqual(aead.decrypt(ciphertext, associated_data), plaintext)


class DeterministicAeadKeyManagerTest(unittest.TestCase):

  def setUp(self):
    super(DeterministicAeadKeyManagerTest, self).setUp()
    daead_key_manager = cc_key_manager.DeterministicAeadKeyManager
    self.key_manager = daead_key_manager.from_cc_registry(
        'type.googleapis.com/google.crypto.tink.AesSivKey')

  def new_aes_siv_key_template(self, key_size):
    key_format = aes_siv_pb2.AesSivKeyFormat()
    key_format.key_size = key_size
    key_template = tink_pb2.KeyTemplate()
    key_template.type_url = 'type.googleapis.com/google.crypto.tink.AesSivKey'
    key_template.value = key_format.SerializeToString()
    return key_template

  def test_key_type(self):
    self.assertEqual(self.key_manager.key_type(),
                     'type.googleapis.com/google.crypto.tink.AesSivKey')

  def test_new_key_data(self):
    key_template = self.new_aes_siv_key_template(64)
    key_data = self.key_manager.new_key_data(key_template)
    self.assertEqual(key_data.type_url, self.key_manager.key_type())
    self.assertEqual(key_data.key_material_type, tink_pb2.KeyData.SYMMETRIC)
    key = aes_siv_pb2.AesSivKey()
    key.ParseFromString(key_data.value)
    self.assertEqual(key.version, 0)
    self.assertLen(key.key_value, 64)

  def test_invalid_params_throw_exception(self):
    key_template = self.new_aes_siv_key_template(65)
    with self.assertRaises(error.StatusNotOk):
      self.key_manager.new_key_data(key_template)

  def test_encrypt_decrypt(self):
    aead = self.key_manager.primitive(
        self.key_manager.new_key_data(self.new_aes_siv_key_template(64)))
    plaintext = b'plaintext'
    associated_data = b'associated_data'
    ciphertext = aead.encrypt_deterministically(plaintext, associated_data)
    self.assertEqual(
        aead.decrypt_deterministically(ciphertext, associated_data), plaintext)


class HybridKeyManagerTest(unittest.TestCase):

  def hybrid_decrypt_key_manager(self):
    return cc_key_manager.HybridDecryptKeyManager.from_cc_registry(
        'type.googleapis.com/google.crypto.tink.EciesAeadHkdfPrivateKey')

  def hybrid_encrypt_key_manager(self):
    return cc_key_manager.HybridEncryptKeyManager.from_cc_registry(
        'type.googleapis.com/google.crypto.tink.EciesAeadHkdfPublicKey')

  def test_new_key_data(self):
    key_manager = self.hybrid_decrypt_key_manager()
    key_data = key_manager.new_key_data(
        hybrid_key_templates.ECIES_P256_HKDF_HMAC_SHA256_AES128_GCM)
    self.assertEqual(key_data.type_url, key_manager.key_type())
    self.assertEqual(key_data.key_material_type,
                     tink_pb2.KeyData.ASYMMETRIC_PRIVATE)
    key = ecies_aead_hkdf_pb2.EciesAeadHkdfPrivateKey()
    key.ParseFromString(key_data.value)
    self.assertLen(key.key_value, 32)
    self.assertEqual(key.public_key.params.kem_params.curve_type,
                     common_pb2.NIST_P256)

  def test_new_key_data_invalid_params_throw_exception(self):
    with self.assertRaisesRegex(error.StatusNotOk,
                                'Unsupported elliptic curve'):
      self.hybrid_decrypt_key_manager().new_key_data(
          hybrid_key_templates.create_ecies_aead_hkdf_key_template(
              curve_type=100,
              ec_point_format=common_pb2.UNCOMPRESSED,
              hash_type=common_pb2.SHA256,
              dem_key_template=aead_key_templates.AES128_GCM))

  def test_encrypt_decrypt(self):
    decrypt_key_manager = self.hybrid_decrypt_key_manager()
    encrypt_key_manager = self.hybrid_encrypt_key_manager()
    key_data = decrypt_key_manager.new_key_data(
        hybrid_key_templates.ECIES_P256_HKDF_HMAC_SHA256_AES128_GCM)
    public_key_data = decrypt_key_manager.public_key_data(key_data)
    hybrid_encrypt = encrypt_key_manager.primitive(public_key_data)
    ciphertext = hybrid_encrypt.encrypt(b'some plaintext', b'some context info')
    hybrid_decrypt = decrypt_key_manager.primitive(key_data)
    self.assertEqual(hybrid_decrypt.decrypt(ciphertext, b'some context info'),
                     b'some plaintext')

  def test_decrypt_fails(self):
    decrypt_key_manager = self.hybrid_decrypt_key_manager()
    key_data = decrypt_key_manager.new_key_data(
        hybrid_key_templates.ECIES_P256_HKDF_HMAC_SHA256_AES128_GCM)
    hybrid_decrypt = decrypt_key_manager.primitive(key_data)
    with self.assertRaisesRegex(error.StatusNotOk, 'ciphertext too short'):
      hybrid_decrypt.decrypt(b'bad ciphertext', b'some context info')


class MacKeyManagerTest(unittest.TestCase):

  def setUp(self):
    super(MacKeyManagerTest, self).setUp()
    self.key_manager = cc_key_manager.MacKeyManager.from_cc_registry(
        'type.googleapis.com/google.crypto.tink.HmacKey')

  def new_hmac_key_template(self, hash_type, tag_size, key_size):
    key_format = hmac_pb2.HmacKeyFormat()
    key_format.params.hash = hash_type
    key_format.params.tag_size = tag_size
    key_format.key_size = key_size
    key_template = tink_pb2.KeyTemplate()
    key_template.type_url = 'type.googleapis.com/google.crypto.tink.HmacKey'
    key_template.value = key_format.SerializeToString()
    return key_template

  def test_key_type(self):
    self.assertEqual(self.key_manager.key_type(),
                     'type.googleapis.com/google.crypto.tink.HmacKey')

  def test_new_key_data(self):
    key_template = self.new_hmac_key_template(common_pb2.SHA256, 24, 16)
    key_data = self.key_manager.new_key_data(key_template)
    self.assertEqual(key_data.type_url, self.key_manager.key_type())
    key = hmac_pb2.HmacKey()
    key.ParseFromString(key_data.value)
    self.assertEqual(key.version, 0)
    self.assertEqual(key.params.hash, common_pb2.SHA256)
    self.assertEqual(key.params.tag_size, 24)
    self.assertLen(key.key_value, 16)

  def test_invalid_params_throw_exception(self):
    key_template = self.new_hmac_key_template(common_pb2.SHA256, 9, 16)
    with self.assertRaises(error.StatusNotOk):
      self.key_manager.new_key_data(key_template)

  def test_mac_success(self):
    mac = self.key_manager.primitive(
        self.key_manager.new_key_data(
            self.new_hmac_key_template(common_pb2.SHA256, 24, 16)))
    data = b'data'
    tag = mac.compute_mac(data)
    self.assertLen(tag, 24)
    # No exception raised.
    mac.verify_mac(tag, data)

  def test_mac_wrong(self):
    mac = self.key_manager.primitive(
        self.key_manager.new_key_data(
            self.new_hmac_key_template(common_pb2.SHA256, 16, 16)))
    with self.assertRaisesRegex(error.StatusNotOk, 'verification failed'):
      mac.verify_mac(b'0123456789ABCDEF', b'data')


class PublicKeySignVerifyKeyManagerTest(unittest.TestCase):

  def setUp(self):
    super(PublicKeySignVerifyKeyManagerTest, self).setUp()
    public_key_verify_manager = cc_key_manager.PublicKeyVerifyKeyManager
    self.key_manager_verify = public_key_verify_manager.from_cc_registry(
        'type.googleapis.com/google.crypto.tink.EcdsaPublicKey')
    public_key_sign_manager = cc_key_manager.PublicKeySignKeyManager
    self.key_manager_sign = public_key_sign_manager.from_cc_registry(
        'type.googleapis.com/google.crypto.tink.EcdsaPrivateKey')

  def new_ecdsa_key_template(self, hash_type, curve_type, encoding,
                             public=False):
    params = ecdsa_pb2.EcdsaParams(
        hash_type=hash_type, curve=curve_type, encoding=encoding)
    key_format = ecdsa_pb2.EcdsaKeyFormat(params=params)
    key_template = tink_pb2.KeyTemplate()
    if public:
      append = 'EcdsaPublicKey'
    else:
      append = 'EcdsaPrivateKey'
    key_template.type_url = 'type.googleapis.com/google.crypto.tink.' + append

    key_template.value = key_format.SerializeToString()
    return key_template

  def test_key_type_sign(self):
    self.assertEqual(self.key_manager_sign.key_type(),
                     'type.googleapis.com/google.crypto.tink.EcdsaPrivateKey')

  def test_key_type_verify(self):
    self.assertEqual(self.key_manager_verify.key_type(),
                     'type.googleapis.com/google.crypto.tink.EcdsaPublicKey')

  def test_new_key_data_sign(self):
    key_template = self.new_ecdsa_key_template(
        common_pb2.SHA256, common_pb2.NIST_P256, ecdsa_pb2.DER)
    key_data = self.key_manager_sign.new_key_data(key_template)
    self.assertEqual(key_data.type_url, self.key_manager_sign.key_type())
    key = ecdsa_pb2.EcdsaPrivateKey()
    key.ParseFromString(key_data.value)
    public_key = key.public_key
    self.assertEqual(key.version, 0)
    self.assertEqual(public_key.version, 0)
    self.assertEqual(public_key.params.hash_type, common_pb2.SHA256)
    self.assertEqual(public_key.params.curve, common_pb2.NIST_P256)
    self.assertEqual(public_key.params.encoding, ecdsa_pb2.DER)
    self.assertLen(key.key_value, 32)

  def test_new_key_data_verify(self):
    key_template = self.new_ecdsa_key_template(
        common_pb2.SHA256, common_pb2.NIST_P256, ecdsa_pb2.DER, True)
    with self.assertRaisesRegex(error.StatusNotOk, 'Operation not supported'):
      self.key_manager_verify.new_key_data(key_template)

  def test_signature_success(self):
    priv_key = self.key_manager_sign.new_key_data(
        self.new_ecdsa_key_template(common_pb2.SHA256, common_pb2.NIST_P256,
                                    ecdsa_pb2.DER))
    pub_key = self.key_manager_sign.public_key_data(priv_key)

    verifier = self.key_manager_verify.primitive(pub_key)
    signer = self.key_manager_sign.primitive(priv_key)

    data = b'data'
    signature = signer.sign(data)

    # Starts with a DER sequence
    self.assertEqual(bytearray(signature)[0], 0x30)

    verifier.verify(signature, data)

  def test_signature_fails(self):
    key_template = self.new_ecdsa_key_template(
        common_pb2.SHA256, common_pb2.NIST_P256, ecdsa_pb2.DER, False)
    priv_key = self.key_manager_sign.new_key_data(key_template)
    pub_key = self.key_manager_sign.public_key_data(priv_key)

    signer = self.key_manager_sign.primitive(priv_key)
    verifier = self.key_manager_verify.primitive(pub_key)

    data = b'data'
    signature = signer.sign(data)

    with self.assertRaisesRegex(error.StatusNotOk, 'Signature is not valid'):
      verifier.verify(signature, 'wrongdata')

    with self.assertRaisesRegex(error.StatusNotOk, 'Signature is not valid'):
      verifier.verify('wrongsignature', data)


if __name__ == '__main__':
  googletest.main()
