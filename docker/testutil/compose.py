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
"""Interface to docker-compose.

The system docker-compose is not used, a standalone version is downloaded and
used from within the execroot.
"""

import os
import subprocess
import time


def _docker_compose_bin():
  return os.path.join(
      os.getenv("PYTHON_RUNFILES"), "bazel_cloud_infra/docker/compose/compose")


class DockerCompose(object):
  """Interface to docker-compose."""

  def __init__(self, compose_file, project_name=None, environ=None,
               block=False):
    self.compose_file = compose_file
    self.project_name = project_name
    self.environ = environ or {}
    self.block = block
    self.up_p = None

    self.environ["TEST_SRCDIR"] = os.getenv("TEST_SRCDIR", default="")
    self.environ["RUNFILES"] = os.getenv("RUNFILES", default="")

  def up(self):
    """Invokes `docker-compose up`.

    The call is non-blocking by default.
    """
    p = self._popen(["up"])
    if self.block:
      retcode = p.wait()
      if retcode:
        raise Exception("non-zero exit code (%d)" % retcode)
    else:
      self.up_p = p

  def down(self):
    """Invokes `docker-compose down`."""
    if self.up_p:
      self.up_p.terminate()
    retcode = self._popen(["down"]).wait()
    if retcode:
      raise Exception("non-zero exit code (%d)" % retcode)

  def port(self, service, container_port):
    """Gets the host port assigned to a given service."""
    tries = 0
    while True:
      try:
        return subprocess.check_output(
            self._command(["port", service,
                           str(container_port)]),
            env=self.environ).strip()
      except subprocess.CalledProcessError as e:
        if tries > 3:
          raise e
        tries += 1
        time.sleep(1)

  def _command(self, compose_cmd):
    cmd = [
        _docker_compose_bin(), "--file",
        os.path.join(os.getenv("PYTHON_RUNFILES"), self.compose_file)
    ]
    if self.project_name:
      cmd += ["--project-name", self.project_name]
    return cmd + compose_cmd

  def _popen(self, compose_cmd):
    return subprocess.Popen(self._command(compose_cmd), env=self.environ)
