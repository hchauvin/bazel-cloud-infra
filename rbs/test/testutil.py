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
"""Common utility functions for testing."""
import os
import subprocess
import re
import random
import string


def runfile(path):
  """Resolves a runfile path."""
  return os.path.join(os.getenv("PYTHON_RUNFILES"), path)


def readlines(path):
  """Reads all the lines of a text runfile."""
  with open(runfile(path), "r") as f:
    return [line.strip() for line in f.readlines()]


def read_runfile(path):
  """Reads the content of a text runfile."""
  with open(runfile(path), "r") as f:
    return f.read()


def load_container_image(path):
  """Load a container image to the current Docker daemon
  (see `DOCKER_HOST` environment variable) and returns its sha256 digest.
  """
  print "Loading container image with %s" % path
  output = subprocess.check_output([runfile(path)])
  matched = re.match(r".+\nTagging ([^ ]+) as ([^:]+):(.+)", output)
  if not matched:
    raise Exception("unexpected output <<< %s >>>" % output)
  sha256 = matched.group(1)
  return sha256


def scratch_workspace(instance):
  """Scratch the test workspace."""
  instance.ScratchFile(
      "WORKSPACE",
      readlines("bazel_cloud_infra/rbs/test/workspace/WORKSPACE.txt"))
  instance.ScratchFile(
      "BUILD", readlines("bazel_cloud_infra/rbs/test/workspace/BUILD.txt"))
  instance.ScratchFile(
      "hello_world.cc",
      readlines("bazel_cloud_infra/rbs/test/workspace/hello_world.cc"))
