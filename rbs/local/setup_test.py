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
import os
import datetime

import boto3
from botocore.stub import Stubber

import setup


class SetupTest(unittest.TestCase):

  def setUp(self):
    self.tmpdir = os.getenv("TEST_TMPDIR")

  def test_zipdir(self):  # pylint: disable=no-self-use
    print "TODO"

  def test_cfn_stack_desc(self):
    raw_desc = {
        "StackStatus":
            "CREATE_COMPLETE",
        "Outputs": [
            {
                "OutputKey": "foo",
                "OutputValue": "bar"
            },
            {
                "OutputKey": "qux",
                "OutputValue": "wobble"
            },
        ],
        "Tags": [
            {
                "Key": "tag_foo",
                "Value": "tag_bar"
            },
            {
                "Key": "tag_qux",
                "Value": "tag_wobble"
            },
        ],
    }
    desc = setup.CfnStackDesc(raw_desc)
    self.assertTrue(desc.complete())
    self.assertEqual(desc.outputs()["foo"], "bar")
    self.assertEqual(desc.outputs()["qux"], "wobble")
    self.assertEqual(desc.tags()["tag_foo"], "tag_bar")
    self.assertEqual(desc.tags()["tag_qux"], "tag_wobble")

  def test_cfn_stack_exists(self):
    cfn = boto3.client('cloudformation', region_name="eu-west-1")
    stubber = Stubber(cfn)
    response = {
        "Stacks": [{
            "StackName": "some_stack",
            "CreationTime": datetime.datetime.today(),
            "StackStatus": "UPDATE_COMPLETE",
            "Description": "bar",
        }],
    }
    expected_params = {"StackName": "some_stack"}
    stubber.add_response('describe_stacks', response, expected_params)
    stubber.activate()

    stack = setup.CfnStack(cfn, "some_stack")
    desc = stack.describe()
    self.assertEqual(desc.desc["Description"], "bar")

  def test_cfn_stack_missing(self):
    cfn = boto3.client('cloudformation', region_name="eu-west-1")
    stubber = Stubber(cfn)
    response = {"Stacks": []}
    expected_params = {"StackName": "some_stack"}
    stubber.add_response('describe_stacks', response, expected_params)
    stubber.activate()

    stack = setup.CfnStack(cfn, "some_stack")
    self.assertRaises(Exception, stack.describe)

  def test_wait_for_stack(self):
    cfn = boto3.client('cloudformation', region_name="eu-west-1")
    stubber = Stubber(cfn)
    stubber.add_response(
        'describe_stacks',
        service_response={
            "Stacks": [{
                "StackName": "some_stack",
                "CreationTime": datetime.datetime.today(),
                "StackStatus": "",
            }],
        },
        expected_params={"StackName": "some_stack"})
    stubber.add_response(
        'describe_stacks',
        service_response={
            "Stacks": [{
                "StackName": "some_stack",
                "CreationTime": datetime.datetime.today(),
                "StackStatus": "CREATE_COMPLETE",
                "Description": "bar",
            }],
        },
        expected_params={"StackName": "some_stack"})
    stubber.activate()

    stack = setup.CfnStack(cfn, "some_stack")
    response = stack.wait_for_stack()
    self.assertEqual(response["Description"], "bar")
    stubber.assert_no_pending_responses()

  def test_template_body(self):  # pylint: disable=no-self-use
    setup.template_body("infra.yaml")

  def test_get_lambda_zip(self):  # pylint: disable=no-self-use
    setup.get_lambda_zip()


if __name__ == '__main__':
  unittest.main()
