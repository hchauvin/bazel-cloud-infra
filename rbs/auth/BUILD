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

sh_binary(
    name = "certstrap",
    srcs = ["certstrap_wrapper.sh"],
    data = [
        "@certstrap_darwin_amd64//file",
        "@certstrap_linux_amd64//file",
    ],
    visibility = ["//visibility:public"],
)

py_binary(
    name = "simple_auth",
    srcs = ["simple_auth.py"],
    data = [":certstrap"],
    visibility = ["//visibility:public"],
    deps = [
        "//rbs/common:config",
    ],
)

genrule(
    name = "simple_auth_help_messages",
    outs = ["simple_auth_help_messages.txt"],
    cmd = """
OUT=$(location simple_auth_help_messages.txt)

rm -f $$OUT

invoke() {
    echo "============" >> $$OUT
    echo "$$*" >> $$OUT
    echo "------------" >> $$OUT
    set +e
    $(location :simple_auth) "$$@" >> $$OUT
    set -e
    echo "\n" >> $$OUT
}

invoke --help
invoke folder --help
invoke config --help
""",
    tools = [":simple_auth"],
)

sh_test(
    name = "test_help_messages",
    size = "small",
    srcs = ["test_help_messages.sh"],
    data = [
        "simple_auth_help_messages.golden.txt",
        "simple_auth_help_messages.txt",
    ],
)

sh_test(
    name = "simple_auth_test",
    srcs = ["simple_auth_test.sh"],
    data = [":simple_auth"],
)
