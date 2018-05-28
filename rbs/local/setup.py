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
"""Sets up the "infra" and "lambda" CloudFormation stacks.

These stacks are the foundations for the remote build system.
"""
import os
import time
import json
import random
import string

import boto3
from botocore.exceptions import ClientError

import rbs.common.runfiles as runfiles
import rbs.common.aws_util as aws_util


def template_body(filename):
  """Returns the body of a cloud formation template."""
  return runfiles.get_data(
      "cfn/" + filename, pkg="setup", prefix="bazel_cloud_infra/rbs/local/")


class CfnStackDesc(object):
  """Represents a CloudFormation stack description."""

  def __init__(self, desc):
    self.desc = desc

  def outputs(self):
    """Returns a dictionary of output keys to output values."""
    outputs = {}
    for output in self.desc["Outputs"]:
      outputs[output["OutputKey"]] = output["OutputValue"]
    return outputs

  def tags(self):
    """Returns a dictionary of tag keys to tag values."""
    tags = {}
    for item in self.desc["Tags"]:
      tags[item["Key"]] = item["Value"]
    return tags

  def complete(self):
    """Whether the stack is in "complete" mode (meaning that its state is stable)."""
    return self.desc["StackStatus"].endswith("_COMPLETE")

  def __getitem__(self, key):
    return self.desc[key]

  def __str__(self):
    return "%s (status: %s)" % (self.desc["StackName"],
                                self.desc["StackStatus"])


class CfnStack(object):
  """Represents a CloudFormation stack."""

  def __init__(self, cfn, name):
    self.cfn = cfn
    self.stack_name = name

  def describe(self):
    """Returns a `CfnStackDesc` object to describe the stack."""
    stacks = self.cfn.describe_stacks(StackName=self.stack_name)["Stacks"]
    if not stacks:
      raise Exception("stack '%s' could not be found" % self.stack_name)
    return CfnStackDesc(stacks[0])

  def update_or_create(self, **kwargs):
    """Updates or creates the stack.

    If the stack has already been create, the stack is updated.
    It is not an error if `update_or_create_stack` is called but the stack
    is up-to-date.
    """
    try:
      change_set_id = self.cfn.create_change_set(
          StackName=self.stack_name,
          ChangeSetType='UPDATE',
          ChangeSetName='%s-ChangeSet-%s' % (self.stack_name,
                                             aws_util.random_string()),
          **kwargs)["Id"]
    except ClientError as e:
      if "does not exist" not in e.response["Error"]["Message"]:
        raise e
      change_set_id = self.cfn.create_change_set(
          StackName=self.stack_name,
          ChangeSetType='CREATE',
          ChangeSetName='%s-ChangeSet-%s' % (self.stack_name,
                                             aws_util.random_string()),
          **kwargs)["Id"]

    while True:
      desc = self.cfn.describe_change_set(ChangeSetName=change_set_id)
      status = desc["Status"]
      status_reason = desc.get("StatusReason", "<empty info>")
      print "%s: change set status: %s - %s" % (self.stack_name, status,
                                                status_reason)
      if status == "CREATE_COMPLETE":
        break
      if status == "FAILED":
        if ("The submitted information didn't contain changes." in status_reason
            or "No updates are to be performed." in status_reason):
          print "%s: up-to-date" % self.stack_name
          return None
        raise Exception("Change set in unexpected state for stack %s: %s - %s" %
                        (self.stack_name, status, status_reason))
      time.sleep(2)
    return self.cfn.execute_change_set(ChangeSetName=change_set_id)

  def wait_for_stack(self):
    """Waits for a stack to be "complete"/"stable"."""
    while True:
      desc = self.describe()
      if desc.complete():
        return desc
      print str(desc)
      time.sleep(2)


def setup_infra(lambda_config, cfn):
  """Sets up the "infra" CloudFormation stack.

  The "infra" stack represents the underlying infrastructure and requires heightened
  privilege for setting up VPCs, security groups and roles.
  """
  infra_stack = CfnStack(cfn, name=lambda_config["stacks"]["infra"])
  vpc_keys = lambda_config["vpc"].keys()
  if len(vpc_keys) != 1:
    raise Exception("invalid vpc keys: %s" % vpc_keys)
  parameters = [
      {
          "ParameterKey": "LambdaFunctionName",
          "ParameterValue": lambda_config["lambda"]["function_name"],
      },
      {
          "ParameterKey": "ServerStack",
          "ParameterValue": lambda_config["stacks"]["server"],
      },
      {
          "ParameterKey": "WorkersStack",
          "ParameterValue": lambda_config["stacks"]["workers"],
      },
  ]
  if vpc_keys[0] == "new":
    parameters += [
        {
            "ParameterKey": "VpcCIDR",
            "ParameterValue": lambda_config["vpc"]["new"]["vpc_cidr"],
        },
        {
            "ParameterKey":
                "PublicSubnet1CIDR",
            "ParameterValue":
                lambda_config["vpc"]["new"]["public_subnet1_cidr"],
        },
    ]
  elif vpc_keys[0] == "existing":
    parameters += [
        {
            "ParameterKey": "VpcID",
            "ParameterValue": lambda_config["vpc"]["existing"]["vpc_id"],
        },
        {
            "ParameterKey":
                "PublicSubnet1ID",
            "ParameterValue":
                lambda_config["vpc"]["existing"]["public_subnet1_id"],
        },
    ]
  else:
    raise Exception("invalid vpc type '%s'" % vpc_keys[0])
  if lambda_config.get("auth") and lambda_config["auth"].get("simple"):
    parameters += [
        {
            "ParameterKey":
                "SimpleAuthS3ObjectArn",
            "ParameterValue":
                "arn:aws:s3:::%s/%s" % (
                    lambda_config["auth"]["simple"]["bucket"],
                    lambda_config["auth"]["simple"]["key"],
                ),
        },
    ]
  infra_stack.update_or_create(
      TemplateBody=template_body("infra.yaml"),
      Parameters=parameters,
      Capabilities=["CAPABILITY_IAM"])
  return infra_stack.wait_for_stack().outputs()


def get_lambda_zip():
  """Returns the content of the lambda zip."""
  return runfiles.get_data(
      "archive.zip", pkg="setup", prefix="bazel_cloud_infra/rbs/local/")


def setup_lambda_code(lambda_config, s3):
  """Uploads the code for the lambda function."""
  return aws_util.maybe_put_s3_object(
      s3,
      bucket=lambda_config["lambda"]["code_bucket"],
      key=lambda_config["lambda"]["code_key"],
      content=get_lambda_zip(),
      desc="Lambda code")


def main_setup_lambda(lambda_config, cfn, s3, lambda_role):
  """Sets up the "lambda" CloudFormation stack.

  This stack depends on the "infra" CloudFormation stack and sets up the backend
  for the remote build system API.
  """
  code_version = setup_lambda_code(lambda_config, s3)
  lambda_stack = CfnStack(cfn, name=lambda_config["stacks"]["lambda"])
  lambda_stack.update_or_create(
      TemplateBody=template_body("lambda.yaml"),
      Parameters=[
          {
              "ParameterKey": "Role",
              "ParameterValue": lambda_role
          },
          {
              "ParameterKey": "CodeS3Bucket",
              "ParameterValue": lambda_config["lambda"]["code_bucket"]
          },
          {
              "ParameterKey": "CodeS3Key",
              "ParameterValue": lambda_config["lambda"]["code_key"]
          },
          {
              "ParameterKey": "CodeS3ObjectVersion",
              "ParameterValue": code_version
          },
          {
              "ParameterKey": "FunctionName",
              "ParameterValue": lambda_config["lambda"]["function_name"]
          },
          {
              "ParameterKey": "LambdaConfig",
              "ParameterValue": json.dumps(lambda_config, sort_keys=True),
          },
          {
              "ParameterKey": "Debug",
              "ParameterValue": os.getenv("INFRA_DEBUG", "false"),
          },
      ])
  return lambda_stack.wait_for_stack().outputs()


def infra_endpoint(restapi_id, region, stage):
  """Returns the API endpoint for the remote build system."""
  return "https://{restapi_id}.execute-api.{region}.amazonaws.com/{stage}/ControlBuildInfra".format(
      restapi_id=restapi_id, region=region, stage=stage)


def maybe_create_log_group(log_group, logs):
  """Creates the given log group if it does not already exists."""
  try:
    logs.create_log_group(logGroupName=log_group)
  except ClientError as e:
    if "The specified log group already exists" not in e.response["Error"][
        "Message"]:
      raise e
    print "Log group %s: already exists" % log_group


def setup(lambda_config):
  """Sets up the "infra" and "lambda" stacks.

  These stacks are the foundations for the remote build system.
  """
  cfn = boto3.client('cloudformation', region_name=lambda_config["region"])
  s3 = boto3.client('s3', region_name=lambda_config["region"])
  logs = boto3.client('logs', region_name=lambda_config["region"])

  maybe_create_log_group(lambda_config["awslogs_group"], logs)

  infra_stack_outputs = setup_infra(lambda_config, cfn)
  lambda_role = infra_stack_outputs["LambdaRole"]

  next_lambda_config = {}
  next_lambda_config.update(lambda_config)
  next_lambda_config.update({
      "cluster": infra_stack_outputs["ClusterName"],
  })
  lambda_stack_outputs = main_setup_lambda(next_lambda_config, cfn, s3,
                                           lambda_role)

  next_lambda_config.update({
      "infra_endpoint":
          infra_endpoint(
              restapi_id=lambda_stack_outputs["RestapiId"],
              region=lambda_config["region"],
              stage="Prod"),
  })
  return next_lambda_config


def teardown(lambda_config, cfn=None):
  """Tears down all the stacks associated with the remote build system.

  The remote configuration file is left intact.
  """
  cfn = cfn or boto3.client(
      'cloudformation', region_name=lambda_config["region"])
  # TODO: parallel delete
  err = False
  for stack in ["workers", "server", "lambda", "infra"]:
    while True:
      try:
        cfn.delete_stack(StackName=lambda_config["stacks"][stack])
        break
      except ClientError as e:
        print e
        if "cannot be deleted while in status" not in e.response["Error"][
            "Message"]:
          err = True
          break
      time.sleep(2)

  next_lambda_config = {}
  next_lambda_config.update(lambda_config)
  del next_lambda_config["infra_endpoint"]
  del next_lambda_config["cluster"]
  return (next_lambda_config, err)
