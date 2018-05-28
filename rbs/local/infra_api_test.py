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
import requests_mock

import infra_api


class SetupTest(unittest.TestCase):

  def setUp(self):
    self.api = infra_api.ControlBuildInfra(endpoint="http://foo.bar")

  def test_connect(self):
    with requests_mock.Mocker() as m:
      m.get('http://foo.bar/connect', json={"foo": "bar"})
      self.assertEqual(self.api.connect(), {"foo": "bar"})
      m.get('http://foo.bar/connect?up=2', json={"qux": "wobble"})
      self.assertEqual(self.api.connect(up=2), {"qux": "wobble"})

  def test_status(self):
    with requests_mock.Mocker() as m:
      m.get('http://foo.bar/status', json={"foo": "bar"})
      self.assertEqual(self.api.status(), {"foo": "bar"})

  def test_down(self):
    with requests_mock.Mocker() as m:
      m.get('http://foo.bar/down?to=10', json={"foo": "bar"})
      self.assertEqual(self.api.down(to=10), {"foo": "bar"})


if __name__ == '__main__':
  unittest.main()
