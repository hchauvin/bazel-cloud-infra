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
import mock

import containers
import actions


class MockContainerService(object):

  def __init__(self, task_lists, task_counts, tasks):
    self.task_lists = task_lists
    self.task_counts = task_counts
    self.tasks = tasks

  def list_tasks(self, family, desiredStatus):
    return self.task_lists[(family, desiredStatus)]

  def count_tasks(self, family, desiredStatus):
    return self.task_counts[(family, desiredStatus)]

  def _get_network(self, task_id):
    network = self.tasks[task_id].get("network")
    if network is None:
      raise AssertionError(
          "network() was not supposed to be called on mock task ID '%s'" %
          task_id)
    return network

  def describe_tasks(self, task_ids):
    for task_id in task_ids:
      task = mock.Mock()
      task.network = mock.Mock(
          containers.Task.network,
          side_effect=lambda task_id=task_id: self._get_network(task_id))
      task.is_running = mock.Mock(
          containers.Task.is_running,
          return_value=self.tasks[task_id]["is_running"])
      yield task


class ActionsTest(unittest.TestCase):

  def setUp(self):
    self.config = {
        "stacks": {
            "infra": "infra_stack",
            "server": "server_stack",
            "workers": "workers_stack",
        },
        "region": "eu-west-1",
        "server_image": "some_server_image",
        "worker_image": "some_worker_image",
        "awslogs_region": "some_awslogs_region",
        "awslogs_group": "some_awslogs_group",
    }

  def test_status(self):
    cont = MockContainerService(
        task_lists={
            ("server_stack-BuildFarm-Server", "RUNNING"): [
                "server_1", "server_2"
            ],
            ("workers_stack-BuildFarm-Worker", "RUNNING"): [
                "worker_1", "worker_2", "worker_3"
            ],
        },
        task_counts={
            ("server_stack-BuildFarm-Server", "STOPPED"): 4,
            ("workers_stack-BuildFarm-Worker", "STOPPED"): 5,
        },
        tasks={
            "server_1": {
                "is_running": False
            },
            "server_2": {
                "is_running":
                    True,
                "network":
                    containers.Network(
                        public_ip="my_server_ip",
                        public_dns_name="my_public_dns_name",
                    ),
            },
            "worker_1": {
                "is_running": False
            },
            "worker_2": {
                "is_running": True
            },
            "worker_3": {
                "is_running": True
            },
        })

    status = actions.do_status(self.config, cont=cont)
    self.assertEqual(status,
                     actions.Status(
                         stopped_servers=4,
                         pending_servers=1,
                         running_servers=1,
                         stopped_workers=5,
                         pending_workers=1,
                         running_workers=2,
                         remote_executor="my_server_ip:8098",
                         server_ip="my_server_ip",
                     ))

  def test_status_no_running_server(self):
    cont = MockContainerService(
        task_lists={
            ("server_stack-BuildFarm-Server", "RUNNING"): ["server_1"],
            ("workers_stack-BuildFarm-Worker", "RUNNING"): [
                "worker_1", "worker_2", "worker_3"
            ],
        },
        task_counts={
            ("server_stack-BuildFarm-Server", "STOPPED"): 4,
            ("workers_stack-BuildFarm-Worker", "STOPPED"): 5,
        },
        tasks={
            "server_1": {
                "is_running": False
            },
            "worker_1": {
                "is_running": False
            },
            "worker_2": {
                "is_running": True
            },
            "worker_3": {
                "is_running": True
            },
        })

    status = actions.do_status(self.config, cont=cont)
    self.assertEqual(status,
                     actions.Status(
                         stopped_servers=4,
                         pending_servers=1,
                         running_servers=0,
                         stopped_workers=5,
                         pending_workers=1,
                         running_workers=2,
                         remote_executor="NULL",
                         server_ip="NULL",
                     ))

  @mock.patch("service.ensure", return_value="mocked_service_ensure")
  @mock.patch("actions.template")
  def test_connect_without_server(self, _actions_template, _service_ensure):
    status = actions.Status(
        stopped_servers=0,
        stopped_workers=0,
        pending_servers=2,
        pending_workers=4,
        running_servers=0,
        running_workers=3,
        remote_executor="NULL",
        server_ip="NULL",
    )
    response = actions.do_connect(self.config, status=status, worker_count=2)
    next_status = response["status"]
    self.assertEqual(next_status["server_status"], "mocked_service_ensure")
    self.assertEqual(next_status["workers_status"],
                     'Response.WaitingForPrecondition')

  @mock.patch("service.ensure", return_value="mocked_service_ensure")
  @mock.patch("actions.template")
  def test_connect(self, _actions_template, _service_ensure):
    status = actions.Status(
        stopped_servers=0,
        stopped_workers=0,
        pending_servers=2,
        pending_workers=4,
        running_servers=1,
        running_workers=3,
        remote_executor="foo:bar",
        server_ip="foo",
    )
    response = actions.do_connect(self.config, status=status, worker_count=5)
    next_status = response["status"]
    self.assertEqual(next_status["server_status"], "mocked_service_ensure")
    self.assertEqual(next_status["workers_status"], "mocked_service_ensure")

  @mock.patch("service.ensure", return_value="mocked_service_ensure")
  @mock.patch("actions.template")
  def test_down(self, _actions_template, _service_ensure):
    status = actions.Status(
        stopped_servers=0,
        stopped_workers=0,
        pending_servers=2,
        pending_workers=4,
        running_servers=1,
        running_workers=3,
        remote_executor="foo:bar",
        server_ip="foo",
    )
    next_status = actions.do_down(
        self.config, status=status, worker_count=1, cfn=lambda: 0)
    self.assertEqual(next_status["server_status"], "mocked_service_ensure")
    self.assertEqual(next_status["workers_status"], "mocked_service_ensure")


if __name__ == '__main__':
  unittest.main()
