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
"""Communicates with the AWS Elastic Container Service (ECS)."""
import boto3
import attr


# pylint: disable=too-few-public-methods
@attr.s
class Network(object):
  """Represents the network info for a Fargate stack."""
  public_ip = attr.ib()
  public_dns_name = attr.ib()


class Task(object):
  """Represents a ECS stack."""

  def __init__(self, task, region="eu-west-1", ec2=None):
    """Initializes the representation from the raw description given by the ECS API."""
    self.ec2 = ec2 or boto3.client('ec2', region_name=region)
    self.task = task

  def network(self):
    """Gets the network info for this ECS task."""
    attachment_details = self.task["attachments"][0]["details"]
    network_interface_ids = [
        att for att in attachment_details if att["name"] == "networkInterfaceId"
    ]
    if not network_interface_ids:
      return None
    desc = self.ec2.describe_network_interfaces(
        NetworkInterfaceIds=[network_interface_ids[0]["value"]])
    interface = desc["NetworkInterfaces"][0]
    if interface.get("Association") is None:
      return None
    return Network(
        public_ip=interface["Association"]["PublicIp"],
        public_dns_name=interface["Association"]["PublicDnsName"],
    )

  def is_running(self):
    """Whether the task is running."""
    return self.task["lastStatus"] == "RUNNING"


class ContainerService(object):
  """Interface to the Elastic Container Service."""

  def __init__(self, cluster, region="eu-west-1", ecs=None):
    """Initializes the interface for a given ECS cluster."""
    self.ecs = ecs or boto3.client('ecs', region_name=region)
    self.region = region
    self.cluster = cluster

  def list_tasks(self, **kwargs):
    """Lists all the task ARNs in this cluster.

    Filters are provided as keyword arguments.
    """
    paginator = self.ecs.get_paginator("list_tasks")
    result = []
    for page in paginator.paginate(cluster=self.cluster, **kwargs):
      result += page["taskArns"]
    return result

  def count_tasks(self, **kwargs):
    """Counts all the tasks in this cluster.

    Filters are provided as keyword arguments.
    """
    return len(self.list_tasks(**kwargs))

  def describe_tasks(self, task_arns):
    """Describes the tasks given in a list of task ARNs."""
    if task_arns:
      tasks = self.ecs.describe_tasks(cluster=self.cluster, tasks=task_arns)
      for task in tasks["tasks"]:
        yield Task(task, region=self.region)
