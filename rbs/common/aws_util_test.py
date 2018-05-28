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

import boto3
from botocore.stub import Stubber

import aws_util


class AwsUtilTest(unittest.TestCase):

  def test_sha256_checksum(self):
    self.assertEqual(
        aws_util.sha256_checksum("some content"),
        "290f493c44f5d63d06b374d0a5abd292fae38b92cab2fae5efefe1b0e9347f56",
        "sha256 digest does not match")

  def test_skip_put_s3_object(self):
    s3 = boto3.client('s3', region_name="eu-west-1")
    stubber = Stubber(s3)
    stubber.add_response(
        'head_object',
        service_response={
            "Metadata": {
                "sha256_digest": "current_digest",
            },
            "VersionId": "current_version_id",
        },
        expected_params={
            "Bucket": "bucket",
            "Key": "key"
        })
    stubber.activate()

    version_id = aws_util.maybe_put_s3_object(
        s3,
        bucket="bucket",
        key="key",
        next_digest="current_digest",
        content="content")
    self.assertEqual(version_id, "current_version_id")

  def test_put_s3_object(self):
    s3 = boto3.client('s3', region_name="eu-west-1")
    stubber = Stubber(s3)
    stubber.add_response(
        'head_object',
        service_response={
            "Metadata": {
                "sha256_digest": "current_digest",
            },
            "VersionId": "current_version_id",
        },
        expected_params={
            "Bucket": "bucket",
            "Key": "key"
        })
    stubber.add_response(
        'put_object',
        service_response={
            "VersionId": "next_version_id",
        },
        expected_params={
            "Bucket": "bucket",
            "Key": "key",
            "Body": "next_body",
            "Metadata": {
                "sha256_digest": "next_digest"
            },
        })
    stubber.activate()

    version_id = aws_util.maybe_put_s3_object(
        s3,
        bucket="bucket",
        key="key",
        next_digest="next_digest",
        content="next_body")
    self.assertEqual(version_id, "next_version_id")

  def test_random_string(self):
    aws_util.random_string()


if __name__ == '__main__':
  unittest.main()
