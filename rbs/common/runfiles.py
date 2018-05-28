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
"""Module to gets the content of a runfile."""

import os
import pkgutil
import tempfile
import atexit
import shutil
import sys
import platform

_manifest = None


def is_bundled():
  """Determines whether the current Python executable is a `.par` bundle."""
  return sys.argv[0].endswith(".par") or not os.getenv("RUNFILES_MANIFEST_FILE")


def read_manifest(path):
  """Reads the given runfiles manifest."""
  with open(path, 'r') as f:
    entries = {}
    for line in f.readlines():
      components = line.strip().split(' ')
      runfile = components[0]
      if len(components) == 1:
        actual = None
      elif len(components) == 2:
        actual = components[1]
      else:
        raise Exception("unexpected components: %s" % components)
      entries[runfile] = actual
    return entries


def get_manifest():
  """Either reads the runfiles manifest or retrieves it from the manifest singleton."""
  global _manifest  # pylint: disable=global-statement
  if _manifest is None:
    _manifest = read_manifest(os.getenv("RUNFILES_MANIFEST_FILE"))
  return _manifest


def get_data(filename, pkg, prefix):
  """Get the content of a runfile."""
  if is_bundled():
    return pkgutil.get_data(pkg, filename)
  try:
    with open(get_manifest()[prefix + filename], 'r') as f:
      return f.read()
  except IOError:
    test_srcdir = os.getenv("TEST_SRCDIR")
    if not test_srcdir:
      raise
    with open(os.path.join(test_srcdir, prefix + filename)) as f:
      return f.read()


def go_bin_folder():
  """Returns the folder in which the binary is located (it depends on the platform)."""
  return {
      "Darwin": "darwin_amd64_stripped",
      "Linux": "linux_amd64_stripped",
  }[platform.system()]


_extraction_dir_set = False


def ensure_extraction_dir():
  """Set a safe extraction dir (the default is unsafe) for runfiles during bundling."""
  if not is_bundled():
    return

  global _extraction_dir_set  # pylint: disable=global-statement
  if not _extraction_dir_set:
    _extraction_dir_set = True
    extraction_tmpdir = tempfile.mkdtemp()
    atexit.register(
        lambda: shutil.rmtree(extraction_tmpdir, ignore_errors=True))
    import pkg_resources
    pkg_resources.set_extraction_path(extraction_tmpdir)


def extract_botocore_data():
  """Extracts the `botocore` data folder if the current Python executable is bundled."""
  if not is_bundled():
    return

  ensure_extraction_dir()

  import pkg_resources
  botocore = pkg_resources.Requirement.parse("botocore==1.9.3")
  dirname = pkg_resources.resource_filename(botocore, "")
  os.environ["AWS_DATA_PATH"] = dirname
