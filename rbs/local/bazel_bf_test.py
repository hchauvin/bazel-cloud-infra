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
import mock

import bazel_bf


def _test_cli_remote(method, argv, *args, **kwargs):
  remote = lambda: 0
  m = mock.Mock(return_value={"some": "status"})
  setattr(remote, method, m)
  bazel_bf.cli_remote(argv, remote=remote)
  m.assert_called_once_with(*args, **kwargs)


class CliTest(unittest.TestCase):

  def test_cli_remote_status(self):  # pylint: disable=no-self-use
    _test_cli_remote("status", ["status"])

  def test_cli_remote_down(self):  # pylint: disable=no-self-use
    _test_cli_remote("down", ["down"], to=0)
    _test_cli_remote("down", ["down", "--to=5"], to=5)

  def test_cli_bazel_bf_options(self):
    self.assertEqual(
        bazel_bf.cli_bazel_bf_options([]), {
            "bazel_bin": "bazel",
            "workers": None,
            "local": False,
            "privileged": False,
            "force_update": False,
            "crosstool_top": None,
            "remote_executor": None,
        })
    self.assertEqual(bazel_bf.cli_bazel_bf_options(["--local"])["local"], True)
    self.assertEqual(
        bazel_bf.cli_bazel_bf_options(["--workers=10"])["workers"], 10)
    self.assertEqual(
        bazel_bf.cli_bazel_bf_options(["--bazel_bin=foo/bar"])["bazel_bin"],
        "foo/bar")
    self.assertRaises(bazel_bf.CommandLineException,
                      bazel_bf.cli_bazel_bf_options,
                      ["--remote_executor=foo:bar"])
    self.assertRaises(bazel_bf.CommandLineException,
                      bazel_bf.cli_bazel_bf_options,
                      ["--crosstool_top=@crosstool"])
    remote_options = bazel_bf.cli_bazel_bf_options(
        ["--remote_executor=foo:bar", "--crosstool_top=@crosstool"])
    self.assertEqual(remote_options["remote_executor"], "foo:bar")
    self.assertEqual(remote_options["crosstool_top"], "@crosstool")


if __name__ == '__main__':
  unittest.main()
