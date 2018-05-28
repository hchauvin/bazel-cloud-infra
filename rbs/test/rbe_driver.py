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
"""Driver to test the Remote Build System."""
import subprocess
import tempfile
import json
import os
import boto3

import rbs.common.aws_util as aws_util
import rbs.auth.simple_auth as simple_auth
import testutil


# pylint: disable=too-few-public-methods
class RBEDriver(object):
  """Driver to test the Remote Build System."""

  def __init__(self, test_config_filename, container_images):
    self.test_config_filename = test_config_filename
    self.container_images = container_images
    self.s3 = None
    self.local_config_path = None
    self.test_config = None
    self.cleanup = not os.getenv("SKIP_CLEANUP")

  def invoke(self, args, extra_env=None):
    """Invokes bazel_bf."""
    cmd = [testutil.runfile("bazel_cloud_infra/rbs/local/bazel_bf.par")] + args
    print "INVOKE: %s" % " ".join(cmd)
    env = {
        "INFRA_LOCAL_CONFIG": self.local_config_path,
        "INFRA_DEBUG": "true",
    }
    env.update(os.environ)
    if extra_env:
      env.update(extra_env)
    subprocess.check_call(
        cmd,
        env=env,
    )

  def __enter__(self):
    """Sets up."""
    self._read_test_config()
    self.s3 = boto3.client('s3', region_name=self.test_config["region"])
    self._setup_config()
    self.invoke([
        "setup",
        "--region=" + self.test_config["region"],
        "--s3_bucket=" + self.test_config["config"]["s3_bucket"],
        "--s3_key=" + self.test_config["config"]["s3_key"],
    ])
    return self

  def __exit__(self, *args):
    """Tears down."""
    if self.cleanup:
      self.invoke(["remote", "down", "--to=0"])
      self.invoke(["teardown", "--force"])
      self._teardown_config()
      self._delete_log_group()
    else:
      print "Cleanup: SKIPPED"

  def _read_test_config(self):
    test_id = aws_util.random_string()
    print "TEST ID: %s" % test_id
    with open(self.test_config_filename, 'r') as f:
      self.test_config = json.loads(f.read().replace("{test_id}", test_id))

  def _setup_config(self):
    _, local_config_path = tempfile.mkstemp(prefix=".bazel_bf", suffix=".json")
    self.local_config_path = local_config_path

    simple_auth.upload_config(
        out=simple_auth.generate(),
        bucket=self.test_config["auth_config"]["bucket"],
        key=self.test_config["auth_config"]["key"],
        region=self.test_config["region"])

    container_images = self.container_images(self.test_config)
    config = {
        "awslogs_group":
            self.test_config["awslogs_group"],
        "awslogs_region":
            self.test_config["region"],
        "region":
            self.test_config["region"],
        "server_image":
            container_images["server"],
        "worker_image":
            container_images["worker"],
        "stacks":
            self.test_config["stacks"],
        "api_stage":
            "Prod",
        "crosstool_top":
            "@bazel_toolchains//configs/debian8_clang/0.3.0/bazel_0.13.0/default:toolchain",
        "lambda":
            self.test_config["lambda"],
        "vpc": {
            "existing": self.test_config["vpc"],
        },
        "auth": {
            "simple": {
                "bucket": self.test_config["auth_config"]["bucket"],
                "key": self.test_config["auth_config"]["key"],
            },
        },
    }
    self.s3.put_object(
        Bucket=self.test_config["config"]["s3_bucket"],
        Key=self.test_config["config"]["s3_key"],
        Body=json.dumps(config, indent=2, sort_keys=True),
    )

  def _teardown_config(self):
    self.s3.delete_object(
        Bucket=self.test_config["config"]["s3_bucket"],
        Key=self.test_config["config"]["s3_key"],
    )
    self.s3.delete_object(
        Bucket=self.test_config["auth_config"]["bucket"],
        Key=self.test_config["auth_config"]["key"],
    )
    os.remove(self.local_config_path)

  def _delete_log_group(self):
    logs = boto3.client('logs')
    logs.delete_log_group(logGroupName=self.test_config["awslogs_group"])


def get_test_config_filename():
  """Returns the canonical filename where the test config is located."""
  usr_filename = "~/.bazel_bf/test_config.json"
  filename = os.path.expanduser(usr_filename)
  if not os.path.isfile(filename):
    raise Exception(
        ("canonical test config file %s (expanded to %s) not found: " +
         "have you set up a test config file with the proper schema?") %
        (usr_filename, filename))
  return filename
