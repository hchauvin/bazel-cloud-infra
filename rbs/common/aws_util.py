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
"""Utility functions for dealing with AWS."""
import hashlib
import random
import string

from botocore.exceptions import ClientError


def sha256_checksum(content):
  """Returns the sha256 hexdigest for a file in the local filesystem."""
  sha256 = hashlib.sha256()
  sha256.update(content)
  return sha256.hexdigest()


# pylint: disable=too-many-arguments
def maybe_put_s3_object(s3, bucket, key, content, desc=None, next_digest=None):
  """Puts an object into S3 if and only if its digest has changed.

  This makes S3 content-addressable."""
  if desc is None:
    desc = "s3://%s/%s" % (bucket, key)
  next_digest = next_digest or sha256_checksum(content)
  try:
    head = s3.head_object(Bucket=bucket, Key=key)
    current_digest = head["Metadata"].get("sha256_digest")
    if current_digest == next_digest:
      print "%s: up-to-date (digest: %s)" % (desc, current_digest)
      return head["VersionId"]
    print "%s: Current digest (%s) differs from next digest (%s)" % (
        desc, current_digest, next_digest)
  except ClientError as e:
    if "Not Found" not in e.response["Error"]["Message"]:
      raise e
    print "%s: previous version not found" % desc
  desc = s3.put_object(
      Body=content,
      Bucket=bucket,
      Key=key,
      Metadata={
          "sha256_digest": next_digest,
      })
  return desc["VersionId"]


def random_string(n=5, uppercase=True):
  """Generates a random string of a given length, containing only uppercase letters and digits."""
  letters = string.ascii_uppercase if uppercase else string.ascii_lowercase
  return ''.join(random.choice(letters + string.digits) for _ in range(n))
