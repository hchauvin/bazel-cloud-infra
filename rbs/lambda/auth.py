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
"""Deals with authentication."""
import os
import json
import boto3

# https://bbengfort.github.io/programmer/2017/03/03/secure-grpc.html
# https://github.com/grpc/grpc-java/blob/701c127f4ca4e61d649db4e1a02538061e3db3ad/examples/src/main/java/io/grpc/examples/helloworldtls/HelloWorldClientTls.java
# https://github.com/awslabs/serverless-application-model/issues/25


def get_authenticator(config):
  """Returns the authenticator implementation, given a configuration object."""
  if config.get("auth") is None:
    return NoOpAuthenticator()
  keys = config["auth"].keys()
  if len(keys) != 1:
    raise Exception("expected one key under auth, got %s" % keys)
  auth_type = keys[0]
  if auth_type == "simple":
    return SimpleAuthenticator(
        config["auth"]["simple"], region=config["region"])
  else:
    raise Exception("unexpected auth type '%s'" % auth_type)


class NoOpAuthenticator(object):
  """No-op authenticator.  It does nothing."""

  def get_auth_info(self):
    return None

  def get_server_auth_info(self):
    return {
        "server_crt": "",
        "server_pkcs8_key": "",
        "ca_crt": "",
        "client_pkcs8_key": "",
        "client_crt": "",
    }


class SimpleAuthenticator(object):
  """Simple authenticator.  The certificates and private keys are stored in a JSON file
  on an S3 bucket.
  
  The JSON file must obviously has restricted access, and it is probably a good
  idea to use a KMS encryption-at-rest."""

  def __init__(self, config, region):
    self.s3_bucket = config["bucket"]
    self.s3_key = config["key"]
    self.config = None
    self.region = region

  def get_auth_info(self):
    """Returns the authentication info that is forwarded to the `bazel_bf` client."""
    config = self._config()
    return {
        "tls_certificate": config["ca_crt"],
        "tls_client_certificate": config["client_crt"],
        "tls_client_key": config["client_pkcs8_key"],
    }

  def get_server_auth_info(self):
    """Returns the server authentication info that is used for setting up the services
    with the proper credentials and trust chains."""
    return self._config()

  def _config(self):
    """Fetches the authentication info from the S3 object."""
    if self.config is None:
      s3 = boto3.client("s3", region_name=self.region)
      config_str = s3.get_object(
          Bucket=self.s3_bucket, Key=self.s3_key)["Body"].read()
      self.config = json.loads(config_str)
      # TODO: make it work by changing how the Lambda function is packaged
      # from infra.rbs.schemas.validate import validate
      # validate(self.config, "simple_auth_config")
    return self.config
