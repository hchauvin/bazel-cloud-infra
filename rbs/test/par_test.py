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
import subprocess
import os


class ParTest(unittest.TestCase):

  def test_auth_proxy_bin(self):
    self._invoke("test_auth_proxy_bin")

  def test_extract_botocore_data(self):
    self._invoke("test_extract_botocore_data")

  def test_template_body(self):
    self._invoke("test_template_body")

  def test_get_lambda_zip(self):
    self._invoke("test_get_lambda_zip")

  def test_validate_get_schema(self):
    self._invoke("test_validate_get_schema")

  def _invoke(self, test_case):
    print "CWD: %s" % os.getcwd()
    subprocess.check_call(["rbs/test/test_par.par", test_case])


if __name__ == '__main__':
  unittest.main()
