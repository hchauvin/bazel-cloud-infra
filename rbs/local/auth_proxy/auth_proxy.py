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
"""Extracts the auth_proxy binary from the pkg_resources."""

import os
import stat

import pkg_resources

import rbs.common.runfiles as runfiles


def auth_proxy_bin():
  """Extracts the auth_proxy binary from the pkg_resources."""
  filename = pkg_resources.resource_filename(
      "rbs.local.auth_proxy.auth_proxy",
      "%s/auth_proxy" % runfiles.go_bin_folder())
  st = os.stat(filename)
  os.chmod(filename, st.st_mode | stat.S_IEXEC)
  return filename
