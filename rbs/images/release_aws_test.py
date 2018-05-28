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
import os
import datetime
import tempfile
import subprocess

import boto3
from botocore.stub import Stubber

from rbs.common import aws_util
import release


class ReleaseAwsTest(unittest.TestCase):

  def setUp(self):
    self.test_id = aws_util.random_string(uppercase=False)

  def tearDown(self):
    ecr = boto3.client(
        'ecr', region_name="eu-west-1")  # TODO: do not hardcode region
    repo = "test-image-" + self.test_id
    ecr.batch_delete_image(
        repositoryName=repo, imageIds=[{
            "imageTag": "latest"
        }])
    ecr.delete_repository(repositoryName=repo)

  def test_push(self):
    registry = release.ecr_registry(
        region="eu-west-1")  # TODO: do not hardcode region
    with tempfile.NamedTemporaryFile() as stamp_info_file:
      release.write_stamp_info(stamp_info_file, {
          "REGISTRY": registry,
          "TEST_ID": self.test_id,
      })
      release.push(
          script_file="rbs/images/test_image_push",
          stamp_info_file=stamp_info_file.name,
          runfiles=os.path.abspath(".."),
          is_ecr=True,
          transform_image_repository=
          lambda repo: repo.replace("{TEST_ID}", self.test_id))


if __name__ == '__main__':
  unittest.main()
