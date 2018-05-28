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
"""API for the remote build system."""

import requests
from requests_aws4auth import AWS4Auth
import boto3.session


def requests_verbose():
  """Logs all the requests, for debugging."""
  import logging
  import httplib

  httplib.HTTPConnection.debuglevel = 1
  logging.basicConfig()
  logging.getLogger().setLevel(logging.DEBUG)
  req_log = logging.getLogger('requests.packages.urllib3')
  req_log.setLevel(logging.DEBUG)
  req_log.propagate = True


def iam_auth(credentials=None):
  """Returns a `requests` auth object for IAM authentication."""
  if credentials is None:
    # Gets the default AWS credentials
    credentials = boto3.session.Session().get_credentials()
  return AWS4Auth(credentials.access_key, credentials.secret_key, 'eu-west-1',
                  'execute-api')


class ControlBuildInfra(object):
  """API for the remote build system."""

  def __init__(self, endpoint, auth=None):
    self.endpoint = endpoint
    self.auth = auth

  def _get(self, path, payload=None):
    if not payload:
      payload = {}
    url = self.endpoint + path
    r = requests.get(url, params=payload, auth=self.auth)
    if r.status_code != 200:
      raise Exception(
          "non-200 status code (%d):\nURL: %s\nParams: %s\nResponse: %s" %
          (r.status_code, url, payload, r.text))
    return r.json()

  def connect(self, up=None, force_update=False):
    """Gets connection info to the remote build system and ensure a service level."""
    payload = {"force_update": "true" if force_update else "false"}
    if up:
      payload["up"] = up
    return self._get("/connect", payload)

  def status(self):
    """Gets the status of the remote build system."""
    return self._get("/status")

  def down(self, to=0):
    """Downsizes the remote build system."""
    return self._get("/down", {"to": to})
