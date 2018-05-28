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

from botocore.stub import Stubber
import boto3
import mock

import containers


class ContainersTest(unittest.TestCase):

  def test_list_tasks(self):
    ecs = boto3.client('ecs', region_name="eu-west-1")
    stubber = Stubber(ecs)
    stubber.add_response(
        'list_tasks',
        service_response={
            "taskArns": ["task1", "task2"],
            "nextToken": "next_token"
        },
        expected_params={
            "cluster": "my_cluster",
            "family": "my_family"
        })
    stubber.add_response(
        'list_tasks',
        service_response={"taskArns": ["task3", "task4"]},
        expected_params={
            "cluster": "my_cluster",
            "family": "my_family",
            "nextToken": "next_token"
        })
    stubber.activate()

    inst = containers.ContainerService(cluster="my_cluster", ecs=ecs)
    tasks = inst.list_tasks(family="my_family")
    self.assertEqual(tasks, ["task1", "task2", "task3", "task4"])

  @mock.patch(
      "containers.Task", side_effect=lambda task, region: {"processed": task})
  def test_describe_tasks(self, _containers_task):
    ecs = boto3.client('ecs', region_name="eu-west-1")
    stubber = Stubber(ecs)
    stubber.add_response(
        'describe_tasks',
        expected_params={
            "cluster": "my_cluster",
            "tasks": ["task_id1", "task_id2"]
        },
        service_response={
            "tasks": [{
                "taskDefinitionArn": "a"
            }, {
                "taskDefinitionArn": "b"
            }]
        })
    stubber.activate()

    inst = containers.ContainerService(cluster="my_cluster", ecs=ecs)
    tasks = list(inst.describe_tasks(["task_id1", "task_id2"]))
    self.assertEqual(tasks, [{
        "processed": {
            "taskDefinitionArn": "a"
        }
    }, {
        "processed": {
            "taskDefinitionArn": "b"
        }
    }])

  def test_task_network(self):
    ec2 = boto3.client('ec2', region_name="eu-west-1")
    stubber = Stubber(ec2)
    stubber.add_response(
        'describe_network_interfaces',
        expected_params={"NetworkInterfaceIds": ["eni_xxx"]},
        service_response={
            "NetworkInterfaces": [{
                "Association": {
                    "PublicIp": "my_public_ip",
                    "PublicDnsName": "my_public_dns_name",
                },
            }],
        })
    stubber.activate()

    task = {
        "attachments": [{
            "details": [{
                "name": "networkInterfaceId",
                "value": "eni_xxx",
            }, {
                "name": "foo",
                "value": "bar",
            }]
        }]
    }
    inst = containers.Task(task, ec2=ec2)
    association = inst.network()
    self.assertEqual(association,
                     containers.Network(
                         public_ip="my_public_ip",
                         public_dns_name="my_public_dns_name",
                     ))


if __name__ == '__main__':
  unittest.main()
