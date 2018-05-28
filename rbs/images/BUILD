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
load(
    "@io_bazel_rules_docker//container:container.bzl",
    "container_image",
    "container_push",
)
load("@distroless//cacerts:java.bzl", "cacerts_java")

package(default_visibility = ["//visibility:public"])

cacerts_java(
    name = "cacerts_java",
    tags = [
        "docker",  # cacerts_java runs docker
    ],
    visibility = ["//visibility:private"],
)

container_image(
    name = "server",
    base = "@rbe_debian8//image",
    cmd = [
        "buildfarm-server_deploy.jar",
        "/server.config",
        "--port",
        "8098",
    ],
    # leverage the implicit target of the buildfarm-server to get a fat jar.
    # this is simply a workaround for the fact that we have so many dependencies,
    # so we'd want some wrappy script. This seemed more straightforward.
    # https://docs.bazel.build/versions/master/be/java.html#java_binary_implicit_outputs
    files = [
        ":server.config",
        "@build_buildfarm//src/main/java/build/buildfarm:buildfarm-server_deploy.jar",
    ],
    tags = [
        "docker",  # cacerts_java runs docker
    ],
    tars = [":cacerts_java"],
)

container_image(
    name = "worker",
    base = "@rbe_debian8//image",
    cmd = [
        "buildfarm-worker_deploy.jar",
        "/worker.config",
    ],
    files = [
        ":worker.config",
        "@build_buildfarm//src/main/java/build/buildfarm:buildfarm-worker_deploy.jar",
    ],
    layers = ["//docker/dind:layer"],
    tags = [
        "docker",  # cacerts_java runs docker
    ],
    tars = [":cacerts_java"],
)

[container_push(
    name = "%s_push" % name,
    format = "Docker",
    image = ":" + name,
    registry = "{REGISTRY}",
    repository = "bazel_bf/" + name,
) for name in [
    "server",
    "worker",
]]

py_library(
    name = "release_lib",
    srcs = ["release.py"],
    deps = [
        requirement("attrs"),
        "//rbs/common:config",
    ],
)

py_binary(
    name = "release",
    srcs = ["release.py"],
    data = [
        "server",
        "server_push",
        "worker",
        "worker_push",
    ],
    deps = [
        ":release_lib",
    ],
)

container_push(
    name = "test_image_push",
    format = "Docker",
    image = "@busybox//image",
    registry = "{REGISTRY}",
    repository = "test-image-{TEST_ID}",
)

py_test(
    name = "release_aws_test",
    size = "small",
    srcs = ["release_aws_test.py"],
    data = [":test_image_push"],
    tags = [
        "aws",
        "manual",
    ],
    deps = [
        ":release_lib",
    ],
)
