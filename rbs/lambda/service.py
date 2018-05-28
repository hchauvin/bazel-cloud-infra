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
"""Ensures a given service level for an AWS CloudFormation stack that describes an
Elastic Container Service (ECS) task."""
from botocore.exceptions import ClientError


def describe_stack(cfn, stack_name):
  """Returns a description of an ECS stack, or `None` if the stack cannot be found."""
  try:
    stacks = cfn.describe_stacks(StackName=stack_name)["Stacks"]
    return stacks[0]
  except ClientError as e:
    if "does not exist" not in e.response["Error"]["Message"]:
      raise e
    return None


class State(object):  # pylint: disable=too-few-public-methods
  """State of an ECS stack for the purpose of this module."""
  Missing = 'State.Missing'  # The stack is missing and must be created
  Updating = 'State.Updating'  # The stack is being updated
  Stable = 'State.Stable'  # The stack is not undergoing any change


def get_state(desc):
  """Gets the `State` of an ECS stack."""
  if not desc:
    return State.Missing
  if not desc["StackStatus"].endswith("_COMPLETE"):
    return State.Updating
  return State.Stable


def get_desired_count(value, lower, upper):
  """Gets the desired count from an actual count and allowed value interval."""
  if lower != -1 and value < lower:
    return lower
  if upper != -1 and value > upper:
    return upper
  return value


def get_stack_args(stack_name, template_body, desired_count, parameters):
  """Returns the arguments to pass to either `update_stack` or `create_stack`."""
  parameter_list = [
      {
          "ParameterKey": "InstanceDesiredCount",
          "ParameterValue": str(desired_count)
      },
  ]
  for key, value in parameters.items():
    parameter_list.append({"ParameterKey": key, "ParameterValue": str(value)})
  return {
      "StackName": stack_name,
      "TemplateBody": template_body,
      "Parameters": parameter_list,
  }


class Response(object):  # pylint: disable=too-few-public-methods
  """Response to a call to `ensure`."""
  UpToDate = 'Response.UpToDate'  # The service is up-to-date
  AlreadyUpdating = 'Response.AlreadyUpdating'  # The service is in the process of being updated,
  # so we cannot touch it
  Creating = 'Response.Creating'  # The service is being created
  Updating = 'Response.Updating'  # The service is being updated
  WaitingForPrecondition = 'Response.WaitingForPrecondition'


# pylint: disable=too-many-arguments
def ensure(cfn,
           stack_name,
           template_body,
           parameters,
           current_count,
           lower_count=-1,
           upper_count=-1,
           force_update=False):
  """Ensures a given level of service for a CloudFormation stack that describes an ECS task."""
  desired_count = get_desired_count(current_count, lower_count, upper_count)
  if not force_update and desired_count == current_count:
    return Response.UpToDate
  desc = describe_stack(cfn, stack_name)
  state = get_state(desc)
  if state == State.Missing:
    assert current_count == 0
    cfn.create_stack(
        **get_stack_args(stack_name, template_body, desired_count, parameters))
    return Response.Creating
  elif state == State.Updating:
    return Response.AlreadyUpdating
  elif state == State.Stable:
    try:
      cfn.update_stack(**get_stack_args(stack_name, template_body,
                                        desired_count, parameters))
    except ClientError as e:
      if "No updates are to be performed." in e.response["Error"]["Message"]:
        return Response.UpToDate
    return Response.Updating
  else:
    raise AssertionError("unexpected state %s" % state)
