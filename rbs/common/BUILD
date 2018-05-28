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

py_library(
    name = "runfiles",
    srcs = ["runfiles.py"],
    visibility = ["//rbs:__subpackages__"],
    deps = [
        requirement("setuptools"),
    ],
)

py_library(
    name = "config",
    srcs = ["config.py"],
    visibility = ["//rbs:__subpackages__"],
    deps = [
        requirement("boto3"),
        requirement("six"),
        ":aws_util",
        "//rbs/schemas:validate",
    ],
)

py_library(
    name = "aws_util",
    srcs = ["aws_util.py"],
    visibility = ["//rbs:__subpackages__"],
    deps = [
        requirement("botocore"),
    ],
)

py_test(
    name = "config_test",
    size = "small",
    srcs = ["config_test.py"],
    deps = [
        ":config",
        "//rbs:test_common",
    ],
)

py_test(
    name = "aws_util_test",
    size = "small",
    srcs = ["aws_util_test.py"],
    deps = [
        ":aws_util",
        "//rbs:test_common",
        requirement("boto3"),
    ],
)
