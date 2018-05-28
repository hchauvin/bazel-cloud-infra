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

py_binary(
    name = "lambda",
    srcs = glob(
        ["*.py"],
        exclude = ["*_test.py"],
    ),
    data = glob(["cfn/**/*.yaml"]),
    main = "handler.py",
    visibility = ["//rbs:__subpackages__"],
    deps = [
        requirement("boto3"),
        requirement("six"),
        requirement("attrs"),
        "//rbs/schemas:validate",
    ],
)

py_test(
    name = "containers_test",
    size = "small",
    srcs = ["containers_test.py"],
    deps = [
        ":lambda",
        "//rbs:test_common",
    ],
)

py_test(
    name = "handler_test",
    size = "small",
    srcs = ["handler_test.py"],
    deps = [
        ":lambda",
        "//rbs:test_common",
    ],
)

py_test(
    name = "service_test",
    size = "small",
    srcs = ["service_test.py"],
    deps = [
        ":lambda",
        "//rbs:test_common",
    ],
)

py_test(
    name = "actions_test",
    size = "small",
    srcs = ["actions_test.py"],
    deps = [
        ":lambda",
        "//rbs:test_common",
    ],
)

py_test(
    name = "api_util_test",
    size = "small",
    srcs = ["api_util_test.py"],
    deps = [
        ":lambda",
        "//rbs:test_common",
    ],
)
