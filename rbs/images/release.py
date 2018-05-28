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
"""Library and binary to release/push the container images related to this project."""

import sys
import subprocess
import tempfile
import os
import re
import argparse
import json

import attr
import boto3

import rbs.common.config as config


def get_image_tag(script_file):
  """Returns the image tag based on the script file produced by the `container_push`
  rule (`rules_docker` rules)."""
  with open(script_file, "r") as script:
    match = re.search(r"--name=([^ ]+)", script.read())
  if not match:
    raise Exception(
        "cannot get image name: the version of rules_docker is probably not supported"
    )
  return match.group(1)


def tag_parts(image_tag):
  """Decomposes a container image tag into its registry, repository and tag."""
  match = re.match(r"([^/\n]+)/([^:]+):(.+)", image_tag)
  if not match:
    raise Exception("invalid image tag '%s'" % image_tag)
  return (match.group(1), match.group(2), match.group(3))


def ecr_registry(account_id=None, region="eu-west-1"):
  """Returns the ECR registry for a specific region associated with an AWS account ID
  (or the default account ID if it left `None`)."""
  if account_id is None:
    # Assume the default AWS ECR registry
    account_id = boto3.client("sts").get_caller_identity().get("Account")
  return "{account_id}.dkr.ecr.{region}.amazonaws.com".format(
      account_id=account_id, region=region)


def maybe_create_ecr_repository(image_repository, region="eu-west-1", ecr=None):
  """Creates an ECR repository if it does not already exist."""
  ecr = ecr or boto3.client("ecr", region_name=region)
  try:
    ecr.create_repository(repositoryName=image_repository)
  except ecr.exceptions.InvalidParameterException as e:
    print "Invalid repository name '%s': %s" % (image_repository, e)
  except ecr.exceptions.RepositoryAlreadyExistsException:
    print "ECR repository '%s' already exists" % image_repository


# pylint: disable=too-few-public-methods
@attr.s
class PushedImageInfo(object):
  """Infos relative to a pushed image"""
  registry = attr.ib()
  repository = attr.ib()
  tag = attr.ib()
  digest = attr.ib()

  def full_tag(self):
    return self.registry + "/" + self.repository + ":" + self.tag

  def with_digest(self):
    """Combines the image info attributes into a full image URI complete with the sha256 digest."""
    return "{registry}/{repository}@sha256:{digest}".format(
        registry=self.registry,
        repository=self.repository,
        digest=self.digest,
    )


def ecr_cred_helper_logs():
  try:
    log_dir = os.path.expanduser("~/.ecr/log")
    if not os.path.isdir(log_dir):
      return "Log dir '%s' not found" % log_dir
    log_files = sorted(os.listdir(log_dir), reverse=True)
    if len(log_files) == 0:
      return "Log files: <none>"
    with open(os.path.join(log_dir, log_files[0]), "r") as last:
      return "Log files: %s\nLatest logs: %s" % (" ".join(log_files),
                                                 last.read())
  except IOError as e:
    import traceback
    return "Silenced OSError while retrieving logs: " + traceback.format_exc()


def get_env_for_pusher(runfiles):
  """Returns a dictionary of environment variables for the container pusher."""
  env = {
      "PYTHON_RUNFILES": runfiles,
  }
  env.update(os.environ)

  # Maybe add some user configs, if the files exist
  user_configs = {
      "AWS_SHARED_CREDENTIALS_FILE": "~/.aws/credentials",
      "DOCKER_CONFIG": "~/.docker",
  }
  for (env_var, usr_filename) in user_configs.items():
    filename = os.path.expanduser(usr_filename)
    if os.path.exists(filename):
      env[env_var] = filename

  return env


def push(script_file,
         stamp_info_file,
         runfiles,
         is_ecr=False,
         transform_image_repository=lambda x: x):
  """Pushes an image."""
  if is_ecr:
    (_, image_repository, _) = tag_parts(get_image_tag(script_file))
    maybe_create_ecr_repository(transform_image_repository(image_repository))

  env = get_env_for_pusher(runfiles=runfiles)
  command = [
      script_file,
      "--stamp-info-file=" + stamp_info_file,
  ]
  try:
    output = subprocess.check_output(command, env=env, stderr=subprocess.STDOUT)
  except subprocess.CalledProcessError as e:
    raise Exception("Error while invoking push script:\n" +
                    ("Command: %s\n" % (" ".join(command))) +
                    ("Environment: %s\n" % env) + ("Output: %s\n" % e.output) +
                    ("ECR cred helper logs: %s" % ecr_cred_helper_logs()))
  match = re.search(
      r"([^/ \n]+)/([^:]+):([^ \n]+) was published with digest: sha256:(.+)\n",
      output)
  if not match:
    raise Exception(
        "missing image digest: the version of rules_docker is probably not supported"
    )

  return PushedImageInfo(
      registry=match.group(1),
      repository=match.group(2),
      tag=match.group(3),
      digest=match.group(4))


def is_aws_ecr(registry):
  """Checks whether registry is an AWS ECR registry."""
  return re.match(r"[0-9]+\.dkr\.ecr\.[^.]+\.amazonaws\.com",
                  registry) is not None


def write_stamp_info(file, stamps):
  for (key, value) in stamps.items():
    file.write("%s %s\n" % (key, value))
  file.flush()


def release(registry):
  """Pushes all the images to the given registry."""
  is_ecr = is_aws_ecr(registry)
  runfiles = os.path.abspath("..")

  ans = {}
  with tempfile.NamedTemporaryFile() as stamp_info_file:
    write_stamp_info(stamp_info_file, {"REGISTRY": registry})
    for image in ["server", "worker"]:
      script_file = "%s/bazel_cloud_infra/rbs/images/%s_push" % (runfiles,
                                                                 image)
      ans[image] = push(script_file, stamp_info_file.name, runfiles, is_ecr)
  return ans


def main_self(load):
  """Pushes the images to the ECR registry of the default AWS account and
  updates the remote config to use these images."""
  current_config = config.read_config()
  images = release(registry=ecr_registry(region=current_config["region"]))
  next_config = {}
  next_config.update(current_config)
  next_config["server_image"] = images["server"].with_digest()
  next_config["worker_image"] = images["worker"].with_digest()
  write_config_response = config.write_config(next_config)
  print "Configuration has been committed to %s" % json.dumps(
      write_config_response, sort_keys=True, indent=2)

  if load:
    subprocess.check_call(["rbs/images/worker"])
    subprocess.check_call([
        "docker", "tag", "bazel/rbs/images:worker", images["worker"].full_tag()
    ])


def main(argv):
  """Entrypoint."""
  parser = argparse.ArgumentParser()

  subparsers = parser.add_subparsers(dest="subparsers_name")

  args_self = subparsers.add_parser("self")
  args_self.add_argument(
      "--load",
      action="store_true",
      help=("Load the worker onto the local Docker deamon as well. " +
            "This prevents network roundtrips when using the Docker sandbox."))

  args = parser.parse_args(argv)

  if args.subparsers_name == "self":
    main_self(args.load)

  return 0


if __name__ == "__main__":
  sys.exit(main(sys.argv[1:]))
