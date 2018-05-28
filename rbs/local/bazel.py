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
"""Calls bazel with the appropriate options for remote and docker execution strategies."""
import pprint
import time
import subprocess
import tempfile
import atexit
import shutil
import os

import attr

import infra_api
import auth

BAZEL_TOOLCHAINS_SNIPPET = """
http_archive(
  name = "bazel_toolchains",
  urls = [
    "https://mirror.bazel.build/github.com/bazelbuild/bazel-toolchains/archive/e45c1eff559abfc22f6a748d2d5835fe0f544536.tar.gz",
    "https://github.com/bazelbuild/bazel-toolchains/archive/e45c1eff559abfc22f6a748d2d5835fe0f544536.tar.gz",
  ],
  strip_prefix = "bazel-toolchains-e45c1eff559abfc22f6a748d2d5835fe0f544536",
  sha256 = "21c94c714c719613f31bfba5f066ee3eb38bc148ba1fc809571c8faa5016152e",
)
"""


def check_workspace():
  """Checks that the WORKSPACE file contains the `bazel_toolchains` repository."""
  try:
    with open("WORKSPACE") as f:
      if "bazel_toolchains" not in f.read():
        raise Exception(
            "@bazel_toolchains was probably not given in the WORKSPACE. " +
            "Please add the following to the WORKSPACE:\n" +
            BAZEL_TOOLCHAINS_SNIPPET)
  except EnvironmentError:
    raise Exception(
        "cannot find WORKSPACE file: are you sure CWD is the root of a Bazel workspace?"
    )


def remote_setup_loop(remote, up=None, force_update=False):
  """Waits until the remote build system is up."""
  while True:
    response = remote.connect(up, force_update=force_update)
    status = response["status"]
    pprint.pprint(status)
    if (status["remote_executor"] != "NULL" and
        status["running_workers"] > 0 and
        status["server_status"] == "Response.UpToDate" and
        status["workers_status"] == "Response.UpToDate"):
      return (status, response.get("auth_info"))
    time.sleep(5)


def local_bazel_options(worker_image, crosstool_top, privileged=False):
  """Returns bazel options for the "docker" execution strategy."""
  options = [
      "--spawn_strategy=docker",
      "--genrule_strategy=docker",
      "--cpu=k8",
      "--host_cpu=k8",
      "--crosstool_top=" + crosstool_top,
      "--define=EXECUTOR=remote",
      "--experimental_docker_use_customized_images=false",
      "--experimental_docker_image=" + worker_image,
  ]
  if privileged:
    options.append("--experimental_docker_privileged")
  return options


def remote_bazel_options(crosstool_top):
  """Returns bazel options for the "remote" execution strategy."""
  k8 = [
      "--cpu=k8",
      "--host_cpu=k8",
      "--crosstool_top=" + crosstool_top,
      "--define=EXECUTOR=remote",
  ]
  return k8 + [
      "--spawn_strategy=remote",
      "--genrule_strategy=remote",
  ]


def filesystem_auth_info(auth_info):
  """Takes the `auth_info` given as PEM content, write the PEM content to temporary
  files, and returns an `auth_info` given as PEM files."""
  auth_info_dir = tempfile.mkdtemp()
  atexit.register(lambda: shutil.rmtree(auth_info_dir, ignore_errors=True))

  ans = {}
  for item in auth_info:
    path = os.path.join(auth_info_dir, item)
    ans[item] = path
    with open(path, 'w') as f:
      f.write(auth_info[item])
  return ans


# pylint: disable=too-few-public-methods
@attr.s
class CommandInfo(object):
  """Return type of `build_command`."""
  crosstool_top = attr.ib(type=str)
  fs_auth_info = attr.ib(type=dict)
  remote_executor = attr.ib(type=str)
  cmd = attr.ib(type=list)


def build_command(bazel_bf_options, lambda_config, command, command_args):
  """Returns the commands for calling bazel."""

  if bazel_bf_options["local"]:
    crosstool_top = lambda_config["crosstool_top"]
    bazel_options = local_bazel_options(
        worker_image=lambda_config["worker_image"],
        crosstool_top=crosstool_top,
        privileged=bazel_bf_options["privileged"])
    remote_executor = None
    fs_auth_info = None
  elif bazel_bf_options["remote_executor"]:
    crosstool_top = bazel_bf_options["crosstool_top"]
    auth_info = bazel_bf_options.get("auth_info")
    remote_executor = bazel_bf_options["remote_executor"]
    fs_auth_info = filesystem_auth_info(auth_info) if auth_info else None
    bazel_options = remote_bazel_options(crosstool_top=crosstool_top)
  else:
    remote = infra_api.ControlBuildInfra(
        endpoint=lambda_config["infra_endpoint"], auth=infra_api.iam_auth())
    (status, auth_info) = remote_setup_loop(
        remote,
        up=bazel_bf_options["workers"],
        force_update=bazel_bf_options["force_update"])
    remote_executor = status["remote_executor"]
    crosstool_top = lambda_config["crosstool_top"]
    fs_auth_info = filesystem_auth_info(auth_info) if auth_info else None
    bazel_options = remote_bazel_options(crosstool_top=crosstool_top)

  cmd = [command] + command_args + bazel_options

  return CommandInfo(
      crosstool_top=crosstool_top,
      fs_auth_info=fs_auth_info,
      remote_executor=remote_executor,
      cmd=cmd,
  )


def call(bazel_bf_options, lambda_config, command, command_args):
  """Calls bazel."""
  check_workspace()
  cmd_info = build_command(bazel_bf_options, lambda_config, command,
                           command_args)
  subprocess.check_call(
      [bazel_bf_options["bazel_bin"], "build", cmd_info.crosstool_top])
  print "Bazel command: %s" % " ".join(cmd_info.cmd)
  if cmd_info.fs_auth_info:
    with auth.AuthProxy(
        auth_info=cmd_info.fs_auth_info,
        backend=cmd_info.remote_executor) as proxy:
      return subprocess.call([bazel_bf_options["bazel_bin"]] + cmd_info.cmd +
                             ["--remote_executor=" + proxy])
  elif cmd_info.remote_executor:
    return subprocess.call([bazel_bf_options["bazel_bin"]] + cmd_info.cmd +
                           ["--remote_executor=" + cmd_info.remote_executor])
  else:
    return subprocess.call([bazel_bf_options["bazel_bin"]] + cmd_info.cmd)
