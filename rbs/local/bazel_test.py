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
import mock

import bazel


class BazelTest(unittest.TestCase):

  @mock.patch('time.sleep', return_value=None)
  def test_remote_setup_loop(self, _time_sleep):
    remote = lambda: 0
    m = mock.Mock()
    m.side_effect = [{
        "status": {
            "remote_executor": "NULL",
        },
    }, {
        "status": {
            "remote_executor": "foo:bar",
            "running_workers": 1,
            "server_status": "Response.UpToDate",
            "workers_status": "Response.UpToDate",
        },
    }]
    remote.connect = m
    (status, _) = bazel.remote_setup_loop(remote, up=10)
    self.assertEqual(
        status, {
            "remote_executor": "foo:bar",
            "running_workers": 1,
            "server_status": "Response.UpToDate",
            "workers_status": "Response.UpToDate",
        })
    m.assert_has_calls(
        [mock.call(10, force_update=False),
         mock.call(10, force_update=False)])


if __name__ == '__main__':
  unittest.main()
