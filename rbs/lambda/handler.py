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
"""Entrypoint for the AWS Lambda handler."""
import os
import json
import traceback
import attr

import api_util
import actions


def get_config_from_env():
  """Retrieves configuration from environment variables."""
  config_str = os.getenv("CONFIG")
  if not config_str:
    raise Exception("The 'CONFIG' environment variable is required")
  config = json.loads(config_str)
  config["command_env"] = {
      "HOME": str(os.getcwd()),
      "AWS_REGION": config["region"],
  }
  config["debug"] = os.getenv("DEBUG") == "true"
  return config


def respond(err, res=None):
  """Writes back an HTTP response suitable for the AWS API gateway."""
  return {
      'statusCode': '400' if err else '200',
      'body': err if err else json.dumps(res, sort_keys=True),
      'headers': {
          'Content-Type': 'application/json',
      },
  }


def handler(event, config=None):
  """Actual handling."""
  if event["httpMethod"] != "GET":
    raise api_util.InvalidArgumentException("invalid HTTP method")
  params = api_util.Params(event.get("queryStringParameters", dict()))
  action = event.get("pathParameters", dict()).get("action", "<none>")

  status = actions.do_status(config)
  if action == "status":
    return attr.asdict(status)
  elif action == "connect":
    return actions.do_connect(
        config,
        status,
        worker_count=params.get_positive_int("up", 2),
        force_update=params.get_bool("force_update", False))
  elif action == "down":
    return actions.do_down(
        config, status, worker_count=params.get_positive_int("to"))
  else:
    raise AssertionError("unexpected action %s" % action)


def lambda_handler(event, _context, config=None):
  """Entrypoint for AWS Lambda."""
  if not config:
    config = get_config_from_env()
  try:
    ans = handler(event, config)
    return respond(None, ans)
  except api_util.InvalidArgumentException as e:
    return respond(e.message)
  except Exception as e:  # pylint: disable=broad-except
    if not config["debug"]:
      raise e
    return respond(traceback.format_exc())
