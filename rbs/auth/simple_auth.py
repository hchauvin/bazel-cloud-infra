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
"""Helpers for the Simple Authentication mode of the Remote Build System."""

import os
import json
import tempfile
import subprocess
import shutil
import sys
import atexit
import argparse

import rbs.common.config


def read(out, path):
  """Reads the content of a text file relative to the `out` folder."""
  with open(os.path.join(out, path), "r") as f:
    return f.read()


def certstrap(out, args):
  """Invokes the `certstrap` executable."""
  certstrap_bin = os.getenv("CERTSTRAP_BIN", "rbs/auth/certstrap")
  command = [certstrap_bin, "--depot-path=" + out] + args
  try:
    subprocess.check_output(command, stderr=subprocess.STDOUT)
  except subprocess.CalledProcessError as e:
    raise CommandLineException(
        "Error while invoking certstrap:\n" + "Command: %s\n" %
        (" ".join(command)) + "Output: %s" % e.output)


def to_pkcs8(src, dest):
  """Converts a key to the PKCS8 format."""
  # TODO: do not use the openssl executable, but do something directly in Python.
  subprocess.check_call([
      "openssl", "pkcs8", "-topk8", "-inform", "PEM", "-outform", "PEM",
      "-nocrypt", "-in", src, "-out", dest
  ])


def generate():
  """Generates the certificates and keys for the Simple Authentication mode."""
  out = tempfile.mkdtemp()
  atexit.register(lambda: shutil.rmtree(out, ignore_errors=True))

  certstrap(out, ["init", "--common-name=CertAuth", "--passphrase="])
  certstrap(out, [
      "request-cert", "--common-name=Server", "--passphrase=",
      "--domain=buildfarm-server,buildfarm-server:8098"
  ])
  certstrap(out, ["request-cert", "--common-name=Client", "--passphrase="])
  certstrap(out, ["sign", "Server", "--CA=CertAuth"])
  certstrap(out, ["sign", "Client", "--CA=CertAuth"])

  to_pkcs8(
      os.path.join(out, "Server.key"), os.path.join(out, "Server.pkcs8.key"))
  to_pkcs8(
      os.path.join(out, "Client.key"), os.path.join(out, "Client.pkcs8.key"))

  return out


def upload_config(out, bucket, key, region):
  """Uploads the certificates and keys as properties of a JSON file on an S3 bucket.

  The S3 object is server-side encrypted."""
  auth = {
      "ca_crt": read(out, "CertAuth.crt"),
      "client_crt": read(out, "Client.crt"),
      "client_pkcs8_key": read(out, "Client.pkcs8.key"),
      "server_crt": read(out, "Server.crt"),
      "server_pkcs8_key": read(out, "Server.pkcs8.key"),
  }

  import boto3
  s3 = boto3.client("s3", region_name=region)
  s3.put_object(
      Bucket=bucket,
      Key=key,
      Body=json.dumps(auth, indent=2, sort_keys=True),
      ServerSideEncryption="AES256")


class CommandLineException(Exception):
  """Raised when the error is explicit enough to be shown to the user
  without a stack trace."""
  pass


def config_args(args):
  """Get the arguments for the "config" subcommand."""
  if args.region or args.s3_bucket or args.s3_key:
    if not args.region or not args.s3_bucket or not args.s3_key:
      raise CommandLineException(
          "Expected either all of --region, --s3_bucket, and --s3_key to be set, or none"
      )
    return (args.s3_bucket, args.s3_key, args.region)

  cfg = rbs.common.config.read_config()
  if not cfg.get("auth") or not cfg["auth"].get("simple"):
    raise CommandLineException("Expected simple authentication to be set.")
  return (cfg["auth"]["simple"]["bucket"], cfg["auth"]["simple"]["key"],
          cfg["region"])


def main(argv):
  """Entrypoint."""
  parser = argparse.ArgumentParser(
      prog="simple_auth",
      description="""
          Helpers for the Simple Authentication mode of the Remote Build System.
      """)

  subparsers = parser.add_subparsers(dest="subparsers_name")

  folder = subparsers.add_parser(
      "folder", description="Output the certificates/keys to the given folder.")
  folder.add_argument("folder_filename", type=str, help="output folder.")

  config = subparsers.add_parser(
      "config",
      help="""
        Configure simple authentication by setting the remote S3 description file.
        The S3 object location is either specified using the command-line options,
        or derived from the local config, if present.
      """,
  )
  config.add_argument("--region", type=str, help="AWS region for the S3 object")
  config.add_argument("--s3_bucket", type=str, help="bucket for the S3 object")
  config.add_argument("--s3_key", type=str, help="key for the S3 object")

  args = parser.parse_args(argv)

  out = generate()

  try:
    if args.subparsers_name == "folder":
      if not os.path.isdir(args.folder_filename):
        os.makedirs(args.folder_filename)
      for filename in os.listdir(out):
        shutil.move(os.path.join(out, filename), args.folder_filename)
    elif argv[0] == "config":
      (bucket, key, region) = config_args(args)
      upload_config(out, bucket, key, region)
    return 0
  except CommandLineException as e:
    print e
    return 1


if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
