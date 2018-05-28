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
"""Actual actions performed by the API."""
import os

import boto3
import attr

import service
import containers
import auth


def template(name):
  """Returns the body of a template found on the local filesystem."""
  with open(os.path.join('./cfn', name)) as f:
    return f.read()


# pylint: disable=too-many-arguments
def ensure_servers(cfn,
                   config,
                   current_count,
                   lower_count=-1,
                   upper_count=-1,
                   force_update=False):
  """Ensure that the build servers conform to spec."""
  auth_info = auth.get_authenticator(config).get_server_auth_info()
  return service.ensure(
      cfn,
      stack_name=config["stacks"]["server"],
      template_body=template('server.yaml'),
      parameters={
          "StackName": config["stacks"]["infra"],
          "ServerImage": config["server_image"],
          "LogsRegion": config["awslogs_region"],
          "LogsGroup": config["awslogs_group"],
          "CertChain": auth_info["server_crt"],
          "PrivateKey": auth_info["server_pkcs8_key"],
          "ClientCertChain": auth_info["ca_crt"],
      },
      current_count=current_count,
      lower_count=lower_count,
      upper_count=upper_count,
      force_update=force_update)


# pylint: disable=too-many-arguments
def ensure_workers(cfn,
                   config,
                   server_ip,
                   current_count,
                   lower_count=-1,
                   upper_count=-1,
                   force_update=False):
  "Ensures that the build workers conform to spec."
  if server_ip == "NULL":
    if upper_count == 0:
      return service.Response.UpToDate
    return service.Response.WaitingForPrecondition
  auth_info = auth.get_authenticator(config).get_server_auth_info()
  return service.ensure(
      cfn,
      stack_name=config["stacks"]["workers"],
      template_body=template('worker.yaml'),
      parameters={
          "StackName": config["stacks"]["infra"],
          "ServerIP": server_ip,
          "WorkerImage": config["worker_image"],
          "LogsRegion": config["awslogs_region"],
          "LogsGroup": config["awslogs_group"],
          "TrustCertCollection": auth_info["ca_crt"],
          "ClientPrivateKey": auth_info["client_pkcs8_key"],
          "WorkerCertChain": auth_info["client_crt"],
      },
      current_count=current_count,
      lower_count=lower_count,
      upper_count=upper_count,
      force_update=force_update)


# pylint: disable=too-few-public-methods
@attr.s
class Status(object):
  """Status of the remote build system."""
  stopped_servers = attr.ib()
  pending_servers = attr.ib()
  running_servers = attr.ib()
  stopped_workers = attr.ib()
  pending_workers = attr.ib()
  running_workers = attr.ib()
  remote_executor = attr.ib()
  server_ip = attr.ib()


def do_status(config, cont=None):
  """Gets the status of the remote build system."""
  if not cont:
    cont = containers.ContainerService(
        cluster=config["cluster"], region=config["region"])
  server_family = config["stacks"]["server"] + "-BuildFarm-Server"
  worker_family = config["stacks"]["workers"] + "-BuildFarm-Worker"

  server_ip = "NULL"
  remote_executor = "NULL"
  all_servers = cont.list_tasks(family=server_family, desiredStatus="RUNNING")
  running_servers = 0
  for server in cont.describe_tasks(all_servers):
    if server.is_running():
      server_ip = server.network().public_ip
      remote_executor = server_ip + ":" + str(8098)
      running_servers += 1

  all_workers = cont.list_tasks(family=worker_family, desiredStatus="RUNNING")
  running_workers = 0
  for worker in cont.describe_tasks(all_workers):
    if worker.is_running():
      running_workers += 1

  return Status(
      stopped_servers=cont.count_tasks(
          family=server_family, desiredStatus="STOPPED"),
      pending_servers=len(all_servers) - running_servers,
      running_servers=running_servers,
      stopped_workers=cont.count_tasks(
          family=worker_family, desiredStatus="STOPPED"),
      pending_workers=len(all_workers) - running_workers,
      running_workers=running_workers,
      remote_executor=remote_executor,
      server_ip=server_ip,
  )


def do_connect(config,
               status,
               worker_count,
               force_update=False,
               auth_info=None,
               cfn=None):
  """Gets connection info to the remote build system and ensures a minimal
  service level.
  """
  cfn = cfn or boto3.client('cloudformation', region_name=config["region"])

  ans = {
      "status": {},
  }
  ans["status"].update(attr.asdict(status))

  ans["status"]["server_status"] = str(
      ensure_servers(
          cfn,
          config,
          current_count=status.running_servers,
          lower_count=1,
          upper_count=1,
          force_update=force_update))
  ans["status"]["workers_status"] = str(
      ensure_workers(
          cfn,
          config,
          server_ip=status.server_ip,
          current_count=status.running_workers,
          lower_count=worker_count,
          force_update=force_update))

  ans["auth_info"] = auth_info or auth.get_authenticator(config).get_auth_info()

  return ans


def do_down(config, status, worker_count, cfn=None):
  """Downsizes the remote build system."""
  cfn = cfn or boto3.client('cloudformation', region_name=config["region"])

  ans = {}
  ans.update(attr.asdict(status))

  desired_server_count = 0 if worker_count == 0 else 1
  ans["server_status"] = str(
      ensure_servers(
          cfn,
          config,
          current_count=status.running_servers,
          lower_count=desired_server_count,
          upper_count=desired_server_count))
  ans["workers_status"] = str(
      ensure_workers(
          cfn,
          config,
          server_ip=status.server_ip,
          current_count=status.running_workers,
          upper_count=worker_count))

  return ans
