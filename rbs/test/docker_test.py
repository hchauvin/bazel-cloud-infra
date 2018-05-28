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

from bazel_integration_test.test_base import TestBase
from rbs.local import bazel
import testutil


class DockerTest(TestBase):

  def test_simple(self):
    (lambda_config, bazel_bf_options) = self._setup(privileged=False)
    cmd_info = bazel.build_command(
        bazel_bf_options=bazel_bf_options,
        lambda_config=lambda_config,
        command="build",
        command_args=["//:hello_world", "//:simple"])
    exit_code, _stdout, stderr = self.RunBazel(cmd_info.cmd)
    self.AssertExitCode(exit_code, 0, stderr)

  def test_dind(self):
    self._build_dind(privileged=True)

  def test_dind_no_privilege(self):
    self.assertRaises(Exception, self._build_dind, privileged=False)

  def _setup(self, privileged):
    testutil.scratch_workspace(self)
    lambda_config = {
        "worker_image":
            testutil.load_container_image("bazel_cloud_infra/rbs/images/worker"
                                         ),
        "crosstool_top":
            "@bazel_toolchains//configs/debian8_clang/0.3.0/bazel_0.13.0/default:toolchain",
    }
    bazel_bf_options = {
        "local": True,
        "privileged": privileged,
    }
    # Temporary workaround due to the fact that the Docker sandbox has not yet been release
    self._bazel = "/usr/local/bin/bazel"
    return (lambda_config, bazel_bf_options)

  def _build_dind(self, privileged):
    (lambda_config, bazel_bf_options) = self._setup(privileged=privileged)
    cmd_info = bazel.build_command(
        bazel_bf_options=bazel_bf_options,
        lambda_config=lambda_config,
        command="build",
        command_args=["//:dind"])
    exit_code, stdout, stderr = self.RunBazel(cmd_info.cmd)
    self.AssertExitCode(exit_code, 0, stderr)
    self.assertTrue("Hello, world!" in stdout)


if __name__ == '__main__':
  unittest.main()
