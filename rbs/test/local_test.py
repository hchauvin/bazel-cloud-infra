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
import time

from docker.testutil.compose import DockerCompose
from rbs.local import bazel
from rbs.local import auth
from bazel_integration_test.test_base import TestBase
from rbs.common import aws_util
import testutil


class LocalTest(TestBase):

  def tearDown(self):
    if self.compose:
      self.compose.down()
    TestBase.tearDown(self)

  def testWorkspace(self):
    self._test_workspace(
        compose_file=
        "bazel_cloud_infra/rbs/test/compose_buildfarm/docker-compose.yml")

  def testWorkspaceAuth(self):
    cert_auth = testutil.read_runfile(
        "bazel_cloud_infra/rbs/test/certs/CertAuth.crt")
    self._test_workspace(
        compose_file=
        "bazel_cloud_infra/rbs/test/compose_buildfarm/docker-compose.auth.yml",
        extra_environ={
            "CERT_CHAIN":
                testutil.read_runfile(
                    "bazel_cloud_infra/rbs/test/certs/Server.crt"),
            "PRIVATE_KEY":
                testutil.read_runfile(
                    "bazel_cloud_infra/rbs/test/certs/Server.pkcs8.key"),
            "CLIENT_CERT_CHAIN":
                cert_auth,
            "TRUST_CERT_COLLECTION":
                cert_auth,
            "WORKER_CERT_CHAIN":
                testutil.read_runfile(
                    "bazel_cloud_infra/rbs/test/certs/Client.crt"),
            "CLIENT_PRIVATE_KEY":
                testutil.read_runfile(
                    "bazel_cloud_infra/rbs/test/certs/Client.pkcs8.key"),
        },
        extra_bazel_bf_options={
            "auth_info": {
                "tls_certificate":
                    cert_auth,
                "tls_client_certificate":
                    testutil.read_runfile(
                        "bazel_cloud_infra/rbs/test/certs/Client.crt"),
                "tls_client_key":
                    testutil.read_runfile(
                        "bazel_cloud_infra/rbs/test/certs/Client.pkcs8.key"),
            },
        },
    )

  def _test_workspace(self,
                      compose_file,
                      extra_environ=None,
                      extra_bazel_bf_options=None):
    environ = {
        "SERVER_IMAGE":
            testutil.load_container_image("bazel_cloud_infra/rbs/images/server"
                                         ),
        "WORKER_IMAGE":
            testutil.load_container_image("bazel_cloud_infra/rbs/images/worker"
                                         ),
    }
    if extra_environ:
      environ.update(extra_environ)
    self.compose = DockerCompose(
        compose_file=compose_file,
        project_name="buildfarm_" + aws_util.random_string(),
        environ=environ)
    self.compose.up()
    time.sleep(5)
    testutil.scratch_workspace(self)
    bazel_bf_options = {
        "remote_executor":
            self.compose.port("buildfarm-server", 8098),
        "crosstool_top":
            "@bazel_toolchains//configs/debian8_clang/0.3.0/bazel_0.13.0/default:toolchain",
        "local":
            False,
    }
    if extra_bazel_bf_options:
      bazel_bf_options.update(extra_bazel_bf_options)
    cmd_info = bazel.build_command(
        bazel_bf_options=bazel_bf_options,
        lambda_config=None,
        command="build",
        command_args=["//:hello_world", "//:simple"])
    exit_code, _stdout, stderr = self.RunBazel(
        ["build", cmd_info.crosstool_top])
    self.AssertExitCode(exit_code, 0, stderr)
    print "Bazel command: %s" % " ".join(cmd_info.cmd)
    if cmd_info.fs_auth_info:
      with auth.AuthProxy(
          auth_info=cmd_info.fs_auth_info,
          backend=cmd_info.remote_executor,
          verbose=True) as proxy:
        exit_code, _stdout, stderr = self.RunBazel(
            cmd_info.cmd + ["--remote_executor=" + proxy])
    else:
      exit_code, _stdout, stderr = self.RunBazel(
          cmd_info.cmd + ["--remote_executor=" + cmd_info.remote_executor])
    self.AssertExitCode(exit_code, 0, stderr)


if __name__ == '__main__':
  unittest.main()
