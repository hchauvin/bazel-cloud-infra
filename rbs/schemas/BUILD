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

load("@py_deps//:requirements.bzl", "requirement")

filegroup(
    name = "schemas",
    srcs = glob(["*.yaml"]),
    visibility = ["//visibility:public"],
)

filegroup(
    name = "examples",
    srcs = glob(["examples/*.json"]),
    visibility = ["//visibility:private"],
)

py_library(
    name = "validate",
    srcs = ["validate.py"],
    data = [
        ":schemas",
    ],
    visibility = ["//visibility:public"],
    deps = [
        requirement("jsonschema"),
        requirement("PyYAML"),
        "//rbs/common:runfiles",
    ],
)

py_test(
    name = "validate_test",
    size = "small",
    srcs = ["validate_test.py"],
    data = [
        ":examples",
    ],
    deps = [":validate"],
)
