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

load(
    "@build_bazel_integration_testing//tools:bazel_py_integration_test.bzl",
    "bazel_py_integration_test",
)
load("@subpar//:subpar.bzl", "par_binary")
load("@py_deps//:requirements.bzl", "requirement")

py_library(
    name = "common",
    srcs = ["testutil.py"],
    data = glob(["workspace/**/*"]),
)

py_library(
    name = "rbe_driver",
    srcs = ["rbe_driver.py"],
    data = ["//rbs/local:bazel_bf.par"],
    deps = [
        ":common",
        "//rbs/auth:simple_auth",
        "//rbs/common:aws_util",
    ],
)

bazel_py_integration_test(
    name = "local_test",
    size = "medium",
    srcs = ["local_test.py"],
    data = [
        "compose_buildfarm/docker-compose.auth.yml",
        "compose_buildfarm/docker-compose.yml",
        ":test_certs",
        "//rbs/images:server",
        "//rbs/images:worker",
    ],
    tags = ["docker"],
    versions = ["0.12.0"],
    deps = [
        ":common",
        "//docker/testutil",
        "//rbs/common:aws_util",
        "//rbs/local:local_lib",
    ],
)

bazel_py_integration_test(
    name = "docker_test",
    size = "medium",
    srcs = ["docker_test.py"],
    data = [
        "compose_buildfarm/docker-compose.auth.yml",
        "compose_buildfarm/docker-compose.yml",
        "//rbs/images:server",
        "//rbs/images:worker",
    ],
    tags = [
        "docker",
        # The test requires a version of bazel that has not yet been released
        # (the Docker sandbox is required for this test).
        "manual",
    ],
    versions = ["0.12.0"],
    deps = [
        ":common",
        "//docker/testutil",
        "//rbs/local:local_lib",
    ],
)

bazel_py_integration_test(
    name = "aws_test",
    size = "large",
    srcs = ["aws_test.py"],
    tags = [
        "aws",
        "manual",
        "network",
    ],
    versions = ["0.12.0"],
    deps = [
        ":common",
        ":rbe_driver",
        "//rbs/images:release",
    ],
)

# TODO: do not use //rbs/auth:certstrap in genrule (the certificates are timestamped,
# and so the build is not reproducible).
genrule(
    name = "test_certs",
    outs = [
        "certs/CertAuth.key",
        "certs/CertAuth.crt",
        "certs/CertAuth.crl",
        "certs/Server.key",
        "certs/Server.csr",
        "certs/Server.crt",
        "certs/Client.key",
        "certs/Client.csr",
        "certs/Client.crt",
        "certs/Server.pkcs8.key",
        "certs/Client.pkcs8.key",
    ],
    cmd = """
CERTSTRAP_BIN=$(location //rbs/auth:certstrap) \
RUNFILES=$(location //rbs/auth:certstrap).runfiles \
    $(location //rbs/auth:simple_auth) folder $$(dirname $(location certs/CertAuth.key))
""",
    tools = [
        "//rbs/auth:certstrap",
        "//rbs/auth:simple_auth",
    ],
)

par_binary(
    name = "test_par",
    srcs = ["test_par.py"],
    data = [
        "//rbs/local/auth_proxy",
    ],
    visibility = ["//visibility:public"],
    zip_safe = False,
    deps = [
        "//rbs/local:local_lib",
    ],
)

py_test(
    name = "par_test",
    size = "small",
    srcs = ["par_test.py"],
    data = [":test_par.par"],
)

py_test(
    name = "lambda_aws_test",
    size = "medium",
    srcs = ["lambda_aws_test.py"],
    tags = [
        "aws",
        "manual",
        "network",
    ],
    deps = [
        ":rbe_driver",
        "//rbs/local:local_lib",
    ],
)
