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
    name = "compose",
    srcs = ["docker_compose_wrapper.sh"],
    data = [
        "@docker_compose_darwin_x86_64//file",
        "@docker_compose_linux_x86_64//file",
    ],
    visibility = ["//visibility:public"],
)
