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
"""Definitions for using `docker-compose` within Bazel."""

load(
    "@bazel_tools//tools/build_defs/repo:http.bzl",
    "http_file",
)

def repositories():
  """Injects the repositories for using `docker-compose` within Bazel."""
  http_file(
      name = "docker_compose_linux_x86_64",
      urls = [
          "https://github.com/docker/compose/releases/download/1.21.2/docker-compose-Linux-x86_64"
      ],
      sha256 =
      "8a11713e11ed73abcb3feb88cd8b5674b3320ba33b22b2ba37915b4ecffdf042",
      executable = True,
  )

  http_file(
      name = "docker_compose_darwin_x86_64",
      urls = [
          "https://github.com/docker/compose/releases/download/1.21.2/docker-compose-Darwin-x86_64"
      ],
      sha256 =
      "cbbb44bcd14af1c57104099b802898b2bbc359ae06b543bfb9bb6d95302026e2",
      executable = True,
  )
