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

import datetime
import unittest

from botocore.stub import Stubber
import boto3

import service


def _add_describe_stacks_response(stubber, StackStatus):
  stubber.add_response(
      'describe_stacks',
      service_response={
          "Stacks": [{
              "StackStatus": StackStatus,
              "CreationTime": datetime.datetime.today(),
              "StackName": "my_stack_name",
          }]
      },
      expected_params={"StackName": "my_stack_name"})


class ServiceTest(unittest.TestCase):

  def test_get_stack_args(self):
    stack_args = service.get_stack_args(
        stack_name="my_stack_name",
        template_body="my_template_body",
        desired_count=10,
        parameters={
            "foo": "bar",
            "some_conversion": 100
        })
    self.assertItemsEqual(stack_args.keys(),
                          ["StackName", "TemplateBody", "Parameters"])
    self.assertEqual(stack_args["StackName"], "my_stack_name")
    self.assertEqual(stack_args["TemplateBody"], "my_template_body")
    self.assertItemsEqual(stack_args["Parameters"], [
        {
            "ParameterKey": "InstanceDesiredCount",
            "ParameterValue": "10"
        },
        {
            "ParameterKey": "foo",
            "ParameterValue": "bar"
        },
        {
            "ParameterKey": "some_conversion",
            "ParameterValue": "100"
        },
    ])

  def test_current_count_is_desired_count(self):
    resp = service.ensure(
        cfn=None,
        stack_name="my_stack_name",
        template_body="my_template_body",
        parameters={},
        current_count=10,
        lower_count=5,
        upper_count=15)
    self.assertEqual(resp, service.Response.UpToDate)

  def test_already_updating(self):
    cfn = boto3.client('cloudformation', region_name="eu-west-1")
    stubber = Stubber(cfn)
    _add_describe_stacks_response(stubber, StackStatus="test")
    stubber.activate()

    resp = service.ensure(
        cfn=cfn,
        stack_name="my_stack_name",
        template_body="my_template_body",
        parameters={},
        current_count=5,
        lower_count=10)
    self.assertEqual(resp, service.Response.AlreadyUpdating)
    stubber.assert_no_pending_responses()

  def test_updating(self):
    cfn = boto3.client('cloudformation', region_name="eu-west-1")
    stubber = Stubber(cfn)
    _add_describe_stacks_response(stubber, StackStatus="CREATE_COMPLETE")
    stubber.add_response('update_stack', service_response={})
    stubber.activate()

    resp = service.ensure(
        cfn=cfn,
        stack_name="my_stack_name",
        template_body="my_template_body",
        parameters={},
        current_count=5,
        lower_count=10)
    self.assertEqual(resp, service.Response.Updating)
    stubber.assert_no_pending_responses()

  def test_nothing_to_update(self):
    cfn = boto3.client('cloudformation', region_name="eu-west-1")
    stubber = Stubber(cfn)
    _add_describe_stacks_response(stubber, StackStatus="CREATE_COMPLETE")
    stubber.add_client_error(
        "update_stack", service_message="No updates are to be performed.")
    stubber.activate()

    resp = service.ensure(
        cfn=cfn,
        stack_name="my_stack_name",
        template_body="my_template_body",
        parameters={},
        current_count=5,
        lower_count=10)
    self.assertEqual(resp, service.Response.UpToDate)
    stubber.assert_no_pending_responses()


if __name__ == '__main__':
  unittest.main()
