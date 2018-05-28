# Copyright 2018 The Bazel Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
import tempfile
import os

from botocore.stub import Stubber
import boto3

import config


class ConfigTest(unittest.TestCase):

  def setUp(self):
    self.tmpdir = os.getenv("TEST_TMPDIR")

  def test_write_local_config(self):
    with tempfile.NamedTemporaryFile(dir=self.tmpdir) as f:
      config.write_local_config(
          region="a", s3_bucket="b", s3_key="c", path=f.name)
      self.assertEqual(
          f.read(),
          "{\"region\": \"a\", \"s3_bucket\": \"b\", \"s3_key\": \"c\"}")

  def test_read_local_config(self):
    with tempfile.NamedTemporaryFile(dir=self.tmpdir) as f:
      f.write("{\"foo\":\"bar\"}")
      f.flush()
      local_config = config.read_local_config(path=f.name, validate=False)
    self.assertEqual(local_config, {"foo": "bar"})

  def test_read_config(self):
    s3 = boto3.client('s3')
    stubber = Stubber(s3)
    body = lambda: 0
    body.read = lambda: "{\"foo\": \"bar\"}"
    stubber.add_response(
        'get_object',
        service_response={
            "Body": body,
        },
        expected_params={
            "Bucket": "bucket",
            "Key": "key"
        })
    stubber.activate()

    local_config = {
        "region": "eu-west-1",
        "s3_bucket": "bucket",
        "s3_key": "key",
    }
    cfg = config.read_config(s3, local_config=local_config, validate=False)
    self.assertEqual(cfg, {"foo": "bar"})


if __name__ == '__main__':
  unittest.main()
