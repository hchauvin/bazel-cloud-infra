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
"""Validates configuration objects against JSON schemas."""
import jsonschema
import yaml

import rbs.common.runfiles as runfiles

SCHEMAS = [
    "local_config",
    "main_config",
    "simple_auth_config",
    "test_config",
]


def validate(instance, schema_name):
  """Validates an object against a pre-built schema."""
  jsonschema.validate(instance, get_schema(schema_name))


_schemas = {schema_name: None for schema_name in SCHEMAS}


def get_schema(schema_name):
  """Returns the JSON schema for the given schema name."""
  global _schemas  # pylint: disable=global-statement
  if not _schemas[schema_name]:
    _schemas[schema_name] = yaml.load(
        runfiles.get_data(
            schema_name + ".yaml",
            pkg="rbs.schemas.validate",
            prefix="bazel_cloud_infra/rbs/schemas/"))
  return _schemas[schema_name]
