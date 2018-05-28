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

import rbe_driver
import testutil


class LambdaAWSTest(unittest.TestCase):

  def run(self, result=None):
    """Wraps the test case within an RBEDriver context."""
    with rbe_driver.RBEDriver(
        test_config_filename=rbe_driver.get_test_config_filename(),
        container_images=lambda test_config: { "server": "foo", "worker": "bar" }) as rbe:
      self.rbe = rbe  # pylint: disable=attribute-defined-outside-init
      super(LambdaAWSTest, self).run(result)

  def testLambdaStatus(self):
    # Works with authentication
    self.rbe.invoke(["remote", "status"])

    # Does not work without authentication
    self.assertRaises(
        Exception,
        self.rbe.invoke, ["remote", "status"],
        extra_env={"TEST_ONLY__NO_IAM_AUTH": "1"})


if __name__ == '__main__':
  unittest.main()
