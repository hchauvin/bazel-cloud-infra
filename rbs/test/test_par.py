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
"""Entrypoint to a Python `.par` bundle to test the various resource extraction
mechanismes used in `bazel_bf.par`."""

import sys
import subprocess
import os

import rbs.local.auth
import rbs.common.runfiles
import rbs.local.setup
import rbs.schemas.validate


class Tests(object):
  """Test cases."""

  def test_is_bundled(self):
    """Tests that the libraries detects executing from within a `.par` file."""
    if not rbs.common.runfiles.is_bundled():
      self.fail("expected is_bundled() to return True")

  def test_auth_proxy_bin(self):
    """Tests loading the `auth_proxy` binary."""
    proxy_bin = rbs.local.auth.auth_proxy_bin()
    print "Proxy bin: %s" % proxy_bin
    returncode = subprocess.call([proxy_bin, "--help"])
    if returncode != 2:
      self.fail("expected returncode to be '2'; got %d" % returncode)

  def test_extract_botocore_data(self):
    """Tests extracting the `botocore` data folder."""
    if os.getenv("AWS_DATA_PATH") is not None:
      self.fail("expected AWS_DATA_PATH to not be set")
    rbs.common.runfiles.extract_botocore_data()
    print "AWS_DATA_PATH: %s" % os.getenv("AWS_DATA_PATH")
    if os.getenv("AWS_DATA_PATH") is None:
      self.fail("expected AWS_DATA_PATH to be set")

  def test_template_body(self):  # pylint: disable=no-self-use
    """Tests loading the template bodies."""
    print "infra: %s" % rbs.local.setup.template_body("infra.yaml")
    print "lambda: %s" % rbs.local.setup.template_body("lambda.yaml")

  def test_get_lambda_zip(self):  # pylint: disable=no-self-use
    """Tests loading the lambda code zip archive."""
    print "lambda zip: %s" % rbs.local.setup.get_lambda_zip()

  def test_validate_get_schema(self):  # pylint: disable=no-self-use
    """Tests that the schemas can be located."""
    rbs.schemas.validate.get_schema("local_config")

  def fail(self, msg):  # pylint: disable=no-self-use
    """Test failure."""
    raise Exception(msg)


def main(argv):
  """Entrypoint."""
  if len(argv) != 2:
    print "Usage: %s <test_case>" % argv[0]
    return 1
  test_case = argv[1]
  suite = Tests()
  getattr(suite, test_case)()
  return 0


if __name__ == "__main__":
  sys.exit(main(sys.argv))
