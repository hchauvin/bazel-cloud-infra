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
"""Builds a zip file containing the code for an AWS Lambda function for the Python runtime."""
import sys
import argparse
import zipfile


def parse_files(files):
  """Parses the input file names."""
  ans = []
  if files:
    for f in files:
      split = f.split("=")
      if len(split) != 2:
        raise Exception("invalid file specification '%s'" % f)
      ans.append((split[0], split[1]))
  return ans


def zip_files(files, empty_files, output):
  """Zips a series of files and empty files together."""
  with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as ziph:
    for dest in empty_files:
      info = zipfile.ZipInfo(filename=dest, date_time=(1980, 1, 1, 0, 0, 0))
      info.external_attr = 0777 << 16L  # give full access to included file
      ziph.writestr(info, '')
    for (src, dest) in files:
      info = zipfile.ZipInfo(filename=dest, date_time=(1980, 1, 1, 0, 0, 0))
      info.external_attr = 0777 << 16L  # give full access to included file
      with open(src, 'r') as fh:
        ziph.writestr(info, fh.read())


def readlines(path):
  """Reads all the lines of a text runfile."""
  with open(path, "r") as f:
    return [line.strip() for line in f.readlines()]


def main(argv):
  """Program entrypoint."""
  if len(argv) != 2:
    print "Usage: %s <argfile>" % argv[0]
    return 1

  parser = argparse.ArgumentParser()
  parser.add_argument("--output", type=str, help="The output file")
  parser.add_argument(
      "--file", type=str, action="append", help="A file to add to the layer")
  parser.add_argument(
      "--empty_file",
      type=str,
      action="append",
      help="An empty file to add to the layer")

  args = parser.parse_args(readlines(argv[1]))
  if len(args.file) == 0:
    print "Warning: zip file will be empty"

  zip_files(
      files=parse_files(args.file),
      empty_files=args.empty_file or [],
      output=args.output)

  return 0


if __name__ == '__main__':
  sys.exit(main(sys.argv))
