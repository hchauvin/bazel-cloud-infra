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
"""Command-line interface for the remote build system."""

import os
import sys
import pprint
import argparse
import json

import rbs.common.config as config
import rbs.common.runfiles as runfiles
import setup
import bazel
import infra_api


class CommandLineException(Exception):
  """Raised when the command-mine arguments are invalid."""


def cli_remote(argv, remote=None):
  """Command-line interface for the `remote` command (control of the remote environment)."""
  parser = argparse.ArgumentParser(
      prog="bazel_bf remote",
      description="""
          Describe and control the remote environment.
      """,
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)

  subparsers = parser.add_subparsers(dest="subparsers_name")

  subparsers.add_parser(
      "status", description="Get the status of the remote environment.")

  down = subparsers.add_parser(
      "down",
      description="Downscale the remote environment.",
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  down.add_argument("--to", type=int, help="maximum worker count", default=0)

  up = subparsers.add_parser(
      "up",
      description="Upscale the remote environment.",
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  up.add_argument("--to", type=int, help="minimum worker count", default=2)
  up.add_argument(
      "--force_update",
      action='store_true',
      help="update the remote build system even if the worker count is the same"
  )

  args = parser.parse_args(argv)

  if not remote:
    lambda_config = config.read_config()
    if os.getenv("TEST_ONLY__NO_IAM_AUTH"):
      print "Authentication has been disabled for testing purposes"
      auth = None
    else:
      auth = infra_api.iam_auth()
    remote = infra_api.ControlBuildInfra(
        endpoint=lambda_config["infra_endpoint"], auth=auth)

  if args.subparsers_name == "status":
    result = remote.status()
  elif args.subparsers_name == "down":
    result = remote.down(to=args.to)
  elif args.subparsers_name == "up":
    result = remote.connect(up=args.to, force_update=args.force_update)
  pprint.pprint(result)


def cli_bazel_bf_options(argv):
  """Gets the bazel_bf options from command-line arguments."""
  parser = argparse.ArgumentParser(
      prog="bazel_bf",
      description="""
          Remote execution options.  Example Bazel invocation: "bazel_bf --workers=10 build //..."
        """,
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument(
      "--workers",
      type=int,
      default=os.getenv("BUILD_WORKERS", None),
      help="minimum number of workers")
  parser.add_argument(
      "--force_update",
      action='store_true',
      help="update the remote build system even if the worker count is the same"
  )
  parser.add_argument(
      "--local",
      action='store_true',
      default=os.getenv("BUILD_LOCAL", False),
      help="use a local Docker execution strategy instead of going remote")
  parser.add_argument(
      "--privileged",
      action='store_true',
      help="run the Docker containers in privileged mode")
  parser.add_argument(
      "--remote_executor",
      type=str,
      help="an explicit remote executor address (else derived from config)")
  parser.add_argument(
      "--crosstool_top",
      type=str,
      help="an explicit crosstool top to use (else derived from config)")
  parser.add_argument(
      "--bazel_bin", type=str, default="bazel", help="path to the Bazel binary")

  args = parser.parse_args(argv)

  if args.remote_executor or args.crosstool_top:
    if not args.remote_executor or not args.crosstool_top:
      raise CommandLineException(
          "--remote_executor and --crosstool_top must be specified together")

  return {
      "workers": args.workers,
      "force_update": args.force_update,
      "local": args.local,
      "privileged": args.privileged,
      "remote_executor": args.remote_executor,
      "crosstool_top": args.crosstool_top,
      "bazel_bin": args.bazel_bin,
  }


def cli_setup(argv):
  """Command-line interface for setting up the remote environment."""
  parser = argparse.ArgumentParser(
      prog="bazel_bf setup",
      description="""
          Set up the remote environment.
          Specify --region, --s3_bucket and --s3_key to specify a remote config for the first time.
          (After bazel_bf setup has been called, this info is stored in the local config file
          "~/.bazel_bf/config.json").
      """)
  parser.add_argument("--region", type=str)
  parser.add_argument("--s3_bucket", type=str)
  parser.add_argument("--s3_key", type=str)

  args = parser.parse_args(argv)

  if args.region or args.s3_bucket or args.s3_key:
    if not args.region or not args.s3_bucket or not args.s3_key:
      raise CommandLineException(
          "for initial setup, --region, --s3_bucket and --s3_key are all mandatory"
      )
    config.write_local_config(
        region=args.region, s3_bucket=args.s3_bucket, s3_key=args.s3_key)

  lambda_config = config.read_config()

  next_lambda_config = setup.setup(lambda_config)
  config.write_config(next_lambda_config)


def cli_teardown(argv):
  """Command-line interface for tearing down the remote environment."""
  parser = argparse.ArgumentParser(
      prog="bazel_bf teardown",
      description="Tear down the remote environment entirely.")
  parser.add_argument("--force", action='store_true')

  args = parser.parse_args(argv)

  lambda_config = config.read_config()

  if not args.force:
    print "Configuration is: " + json.dumps(
        lambda_config, indent=2, sort_keys=True)
    sys.stdout.write("Confirm tearing down the remote environment? [yes/No] ")
    choice = raw_input().lower()
    if choice == "yes":
      print "Proceeding..."
    else:
      raise CommandLineException("Abort!")

  (next_lambda_config, err) = setup.teardown(lambda_config)
  config.write_config(next_lambda_config)

  if err:
    raise CommandLineException(
        "Errors were encountered during tear down: " +
        "some resources might not have been properly deleted")


def cli_bazel(command, command_args, bazel_bf_args):
  """Command-line interface that wraps bazel for remote or docker execution."""
  bazel_bf_options = cli_bazel_bf_options(bazel_bf_args)
  lambda_config = config.read_config()

  return bazel.call(
      bazel_bf_options=bazel_bf_options,
      lambda_config=lambda_config,
      command=command,
      command_args=command_args)


USAGE = """
usage: bazel_bf {-h,--help,setup,remote,teardown,options,...} ...

Wrapper around Bazel for remote and multi-platform execution.

-h, --help  Show this help message and exit.
setup       Set up the remote environment.
remote      Describe and control the remote environment.
teardown    Tear down the remote environment entirely.
options     Show the remote execution options.
...         Execute Bazel.  Type "bazel_bf options" to show the remote options.
            Example: "bazel_bf --workers=10 build //..."
"""


def main(argv):
  """Entrypoint."""
  runfiles.extract_botocore_data()
  try:
    if len(argv) < 2 or argv[1] in ["--help", "-h"]:
      print USAGE
      return 2

    # Command is first argument not starting with '--'
    command_index = None
    for i, arg in enumerate(sys.argv[1:]):
      if not arg.startswith("--"):
        command_index = i + 1
        break
    if not command_index:
      raise CommandLineException("no command was found in the arguments!")
    command = sys.argv[command_index]

    command_args = sys.argv[command_index + 1:]
    if command == "setup":
      cli_setup(command_args)
    elif command == "remote":
      cli_remote(command_args)
    elif command == "teardown":
      cli_teardown(command_args)
    elif command == "options":
      cli_bazel_bf_options(["--help"])
      raise AssertionError(
          "should not be here, --help should have been displayed")
    else:
      return cli_bazel(
          command, command_args, bazel_bf_args=sys.argv[1:command_index])
    return 0
  except CommandLineException as e:
    print e.message
    return 1


if __name__ == "__main__":
  sys.exit(main(sys.argv))
