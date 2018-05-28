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
"""Configuration system."""

import json
import os

import boto3

import rbs.schemas.validate
import aws_util


def config_filename():
  """Returns the local configuration file name."""
  return os.getenv(
      "INFRA_LOCAL_CONFIG",
      default=os.path.expanduser("~/.bazel_bf/config.json"))


def write_local_config(region, s3_bucket, s3_key, path=None, validate=True):
  """Commits the local configuration."""
  if not path:
    path = config_filename()
  with open(path, 'w') as f:
    local_config = {
        "region": region,
        "s3_bucket": s3_bucket,
        "s3_key": s3_key,
    }
    if validate:
      rbs.schemas.validate.validate(local_config, "local_config")
    f.write(json.dumps(local_config, sort_keys=True))


def read_local_config(path=None, validate=True):
  """Reads the local configuration."""
  if not path:
    path = config_filename()

  try:
    with open(path, 'r') as f:
      local_config = json.load(f)
  except IOError as e:
    if e.errno == 2:  # No such file or directory
      raise Exception("cannot read config file '%s'." % path)
    raise e

  if validate:
    rbs.schemas.validate.validate(local_config, "local_config")
  return local_config


def read_config(s3=None, local_config=None, validate=True):
  """Reads the remote configuration."""
  config_str = os.getenv("INFRA_CONFIG")
  if not config_str:
    if not local_config:
      local_config = read_local_config()
    if not s3:
      s3 = boto3.client("s3", region_name=local_config["region"])

    config_str = s3.get_object(
        Bucket=local_config["s3_bucket"],
        Key=local_config["s3_key"])["Body"].read()

  try:
    main_config = json.loads(config_str)
    print "Remote configuration: %s" % main_config
  except ValueError as e:
    raise Exception("cannot read JSON config:\n%s\nValueError: %s\n" %
                    (config_str, e.message))

  if validate:
    rbs.schemas.validate.validate(main_config, "main_config")
  return main_config


def write_config(next_config, s3=None, local_config=None, validate=True):
  """Writes the remote configuration."""
  if validate:
    rbs.schemas.validate.validate(next_config, "main_config")
  if not local_config:
    local_config = read_local_config()
  if not s3:
    s3 = boto3.client("s3", region_name=local_config["region"])
  version = aws_util.maybe_put_s3_object(
      s3,
      bucket=local_config["s3_bucket"],
      key=local_config["s3_key"],
      content=json.dumps(next_config, indent=2, sort_keys=True),
      desc="Remote config")
  return {
      "bucket": local_config["s3_bucket"],
      "key": local_config["s3_key"],
      "version": version,
  }
