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

import attr
import mock
import handler
import api_util
import actions

_EXAMPLE_STATUS = actions.Status(
    stopped_servers=0,
    pending_servers=0,
    running_servers=0,
    stopped_workers=0,
    pending_workers=0,
    running_workers=0,
    remote_executor="NULL",
    server_ip="NULL",
)


def _raise_invalid_argument_exception(*_args):
  raise api_util.InvalidArgumentException("some error")


class HandlerTest(unittest.TestCase):

  @mock.patch("actions.do_status", return_value=_EXAMPLE_STATUS)
  def test_status(self, actions_do_status):
    event = {
        "httpMethod": "GET",
        "pathParameters": {
            "action": "status",
        },
    }
    resp = handler.handler(event, config={"some": "config"})
    self.assertEqual(resp, attr.asdict(_EXAMPLE_STATUS))
    actions_do_status.assert_called_once_with({"some": "config"})

  @mock.patch("actions.do_connect", return_value={"foo": "bar"})
  @mock.patch("actions.do_status", return_value=_EXAMPLE_STATUS)
  def test_connect(self, _actions_do_status, actions_do_connect):
    event = {
        "httpMethod": "GET",
        "pathParameters": {
            "action": "connect",
        },
        "queryStringParameters": {
            "up": "10",
            "force_update": "true",
        },
    }
    resp = handler.handler(event, config={"some": "config"})
    self.assertEqual(resp, {"foo": "bar"})
    actions_do_connect.assert_called_once_with(
        {
            "some": "config"
        }, _EXAMPLE_STATUS, worker_count=10, force_update=True)

  @mock.patch("actions.do_down", return_value={"foo": "bar"})
  @mock.patch("actions.do_status", return_value=_EXAMPLE_STATUS)
  def test_down(self, _actions_do_status, actions_do_down):
    event = {
        "httpMethod": "GET",
        "pathParameters": {
            "action": "down",
        },
        "queryStringParameters": {
            "to": "10",
        },
    }
    resp = handler.handler(event, config={"some": "config"})
    self.assertEqual(resp, {"foo": "bar"})
    actions_do_down.assert_called_once_with(
        {
            "some": "config"
        }, _EXAMPLE_STATUS, worker_count=10)

  def test_http_success(self):
    with mock.patch("handler.handler", return_value={"some": "response"}) as m:
      resp = handler.lambda_handler({"some": "event"}, None, {"some": "config"})
      m.assert_called_once_with({"some": "event"}, {"some": "config"})
      self.assertEqual(
          resp, {
              'statusCode': '200',
              'body': "{\"some\": \"response\"}",
              "headers": {
                  'Content-Type': 'application/json',
              },
          })

  def test_http_error(self):
    with mock.patch("handler.handler") as m:
      m.side_effect = _raise_invalid_argument_exception
      resp = handler.lambda_handler({"some": "event"}, None, {"some": "config"})
      m.assert_called_once_with({"some": "event"}, {"some": "config"})
      self.assertEqual(
          resp, {
              'statusCode': '400',
              'body': "some error",
              "headers": {
                  'Content-Type': 'application/json',
              },
          })


if __name__ == '__main__':
  unittest.main()
