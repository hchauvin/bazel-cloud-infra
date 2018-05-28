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
"""Utilities for writing APIs."""


class InvalidArgumentException(Exception):
  """Raised when an API receives a wrong argument.

  The exception message is safe to pass back to the API client.
  """
  pass


class Params(object):
  """Provides access to a dictionary of parameters, with validation."""

  def __init__(self, params):
    self.params = params

  def get_positive_int(self, name, default=None, optional=False):
    """Gets a positive integer."""
    ans_str = self.params.get(name, None if default is None else str(default))
    if not ans_str:
      if optional:
        return None
      else:
        raise InvalidArgumentException("parameter '%s' is required" % name)
    try:
      ans = int(ans_str)
    except ValueError:
      raise InvalidArgumentException(
          "invalid '%s' parameter: expected an integer" % name)
    if ans < 0:
      raise InvalidArgumentException(
          "invalid '%s' parameter: expected a positive integer or zero" % name)
    return ans

  def get_one_of(self, name, options, default=None):
    """Gets a string that must be within a set of allowed values."""
    ans = self.params.get(name, None if default is None else default.name)
    if ans in options:
      return ans
    raise InvalidArgumentException(
        "invalid '%s' parameter: expected one of: %s" % (name,
                                                         ", ".join(options)))

  def get_bool(self, name, default=False):
    """Gets a boolean value."""
    ans = self.params.get(name, "true" if default else "false")
    if ans == "true":
      return True
    elif ans == "false":
      return False
    raise InvalidArgumentException(
        "invalid '%s' parameter: expected either 'true' or 'false'" % name)
