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
load("@subpar//:subpar.bzl", "par_binary")
load("//lambda:defs.bzl", "pkg_lambda_py")

pkg_lambda_py(
    name = "archive",
    src = "//rbs/lambda",
)

REQUESTS_TLS = [
    requirement("requests"),
    # Required for requests with TLS
    requirement("pyOpenSSL"),
    requirement("cryptography"),
    requirement("idna"),
    requirement("certifi"),
]

py_library(
    name = "local_lib",
    srcs = glob(
        ["*.py"],
        exclude = ["*_test.py"],
    ),
    data = glob(["cfn/**/*.yaml"]) + [
        "archive.zip",
    ],
    visibility = ["//rbs:__subpackages__"],
    deps = [
        requirement("boto3"),
        requirement("six"),
        requirement("setuptools"),
        requirement("requests-aws4auth"),
        requirement("attrs"),
        "//rbs/common:aws_util",
        "//rbs/common:config",
        "//rbs/common:runfiles",
        "//rbs/local/auth_proxy:auth_proxy_lib",
    ] + REQUESTS_TLS,
)

par_binary(
    name = "bazel_bf",
    srcs = ["bazel_bf.py"],
    data = [
        "//rbs/local/auth_proxy",
    ],
    imports = ["."],
    visibility = ["//visibility:public"],
    zip_safe = False,
    deps = [
        ":local_lib",
    ],
)

py_test(
    name = "setup_test",
    size = "small",
    srcs = ["setup_test.py"],
    deps = [
        ":local_lib",
        "//rbs:test_common",
    ],
)

py_test(
    name = "infra_api_test",
    size = "small",
    srcs = ["infra_api_test.py"],
    deps = [
        ":local_lib",
        "//rbs:test_common",
    ],
)

py_test(
    name = "bazel_test",
    size = "small",
    srcs = ["bazel_test.py"],
    deps = [
        ":local_lib",
        "//rbs:test_common",
    ],
)

py_test(
    name = "bazel_bf_test",
    size = "small",
    srcs = ["bazel_bf_test.py"],
    deps = [
        ":local_lib",
        "//rbs:test_common",
    ],
)

py_test(
    name = "auth_test",
    size = "small",
    srcs = ["auth_test.py"],
    data = [
        "//rbs/local/auth_proxy",
    ],
    deps = [
        ":local_lib",
        "//rbs:test_common",
    ],
)

genrule(
    name = "help_messages",
    outs = ["help_messages.txt"],
    cmd = """
OUT=$(location help_messages.txt)

rm -f $$OUT

invoke() {
    echo "============" >> $$OUT
    echo "$$*" >> $$OUT
    echo "------------" >> $$OUT
    set +e
    $(location :bazel_bf) "$$@" >> $$OUT
    set -e
    echo "\n" >> $$OUT
}

invoke --help
invoke setup --help
invoke remote --help
invoke remote status --help
invoke remote down --help
invoke remote up --help
invoke teardown --help
invoke options
""",
    tools = [":bazel_bf"],
)

sh_test(
    name = "test_help_messages",
    size = "small",
    srcs = ["test_help_messages.sh"],
    data = [
        "help_messages.golden.txt",
        "help_messages.txt",
    ],
)
