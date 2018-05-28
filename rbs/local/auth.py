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
"""Deals with authentication with the remote execution server."""
import subprocess
import os
import random

import rbs.common.runfiles as runfiles


def auth_proxy_bin():
  """Gets the path to the auth_proxy binary."""
  if runfiles.is_bundled():
    runfiles.ensure_extraction_dir()
    import rbs.local.auth_proxy.auth_proxy
    return rbs.local.auth_proxy.auth_proxy.auth_proxy_bin()

  proxy_bin_runfile = "bazel_cloud_infra/rbs/local/auth_proxy/{go_bin_folder}/auth_proxy".format(
      go_bin_folder=runfiles.go_bin_folder())
  try:
    return runfiles.get_manifest()[proxy_bin_runfile]
  except IOError:
    test_srcdir = os.getenv("TEST_SRCDIR")
    if not test_srcdir:
      raise
    return os.path.join(test_srcdir, proxy_bin_runfile)


# pylint: disable=too-few-public-methods
class AuthProxy(object):
  """Proxies the remote executor endpoint to add authentication."""

  def __init__(self, auth_info, backend, verbose=False):
    self.auth_proxy_bin = auth_proxy_bin()
    self.auth_info = auth_info
    self.backend = backend
    self.verbose = verbose
    self.process = None

    if not self.auth_info:
      raise Exception("expected an auth_info when using AuthProxy")

  def __enter__(self):
    # NOTE: This does not account for when there is a port clash.
    listen = "localhost:%d" % random.randint(50000, 60000)
    cmd = [
        auth_proxy_bin(),
        "-crt=" + self.auth_info["tls_client_certificate"],
        "-key=" + self.auth_info["tls_client_key"],
        "-ca=" + self.auth_info["tls_certificate"],
        "-backend=" + self.backend,
        "-listen=" + listen,
    ]
    if self.verbose:
      cmd.append("-verbose")
    try:
      self.process = subprocess.Popen(cmd)
    except OSError as e:
      if e.errno == 2:  # No such file or directory
        raise Exception("%s: %s" % (e, cmd[0]))
    return listen

  def __exit__(self, *args):
    if self.process:
      self.process.terminate()
