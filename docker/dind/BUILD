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
    "@io_bazel_rules_docker//container:container.bzl",
    "container_layer",
)
load(":defs.bzl", "DEBIAN8_DOCKER")

container_layer(
    name = "layer",
    debs = ["@docker_dep_%s//package" % name for name in DEBIAN8_DOCKER.keys()],
    files = [":docker_wrapper.sh"],
    symlinks = {
        "/usr/local/bin/docker": "/docker_wrapper.sh",
    },
    visibility = ["//visibility:public"],
)
