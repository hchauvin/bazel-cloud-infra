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

workspace(name = "bazel_cloud_infra")

load(
    "@bazel_tools//tools/build_defs/repo:http.bzl",
    "http_archive",
    "http_file",
)

git_repository(
    name = "subpar",
    commit = "07ff5feb7c7b113eea593eb6ec50b51099cf0261",
    remote = "https://github.com/google/subpar",
)

http_archive(
    name = "bazel_toolchains",
    sha256 = "21c94c714c719613f31bfba5f066ee3eb38bc148ba1fc809571c8faa5016152e",
    strip_prefix = "bazel-toolchains-e45c1eff559abfc22f6a748d2d5835fe0f544536",
    urls = [
        "https://mirror.bazel.build/github.com/bazelbuild/bazel-toolchains/archive/e45c1eff559abfc22f6a748d2d5835fe0f544536.tar.gz",
        "https://github.com/bazelbuild/bazel-toolchains/archive/e45c1eff559abfc22f6a748d2d5835fe0f544536.tar.gz",
    ],
)

http_archive(
    name = "build_buildfarm",
    sha256 = "f5ede324d0ab656f20ed5b102296c274f5afd6df0677a1da4ae2d4ffb6d5416b",
    strip_prefix = "bazel-buildfarm-f97a69f33aea042cce9940023d405cc8e4b13ec3",
    urls = [
        "https://github.com/hchauvin/bazel-buildfarm/archive/f97a69f33aea042cce9940023d405cc8e4b13ec3.tar.gz",
    ],
)

load(
    "@build_buildfarm//:dependencies.bzl",
    build_buildfarm_dependencies = "dependencies",
)

build_buildfarm_dependencies()

git_repository(
    name = "io_bazel_rules_python",
    commit = "c741df316b9eab2c9160835398394c854e753b91",
    remote = "https://github.com/hchauvin/rules_python.git",
)

load("@io_bazel_rules_python//python:pip.bzl", "pip_import")

pip_import(
    name = "py_deps",
    requirements = "//rbs:requirements.txt",
)

load("@py_deps//:requirements.bzl", "pip_install")

pip_install()

http_archive(
    name = "build_bazel_integration_testing",
    sha256 = "f872c979df8f44954cdb415c22cd8da4c5ad3aef6319ba8f7988b0eff39d0358",
    strip_prefix = "bazel-integration-testing-1bad547fd814c7642e8edfd4f0974ed8a25b5252",
    urls = ["https://github.com/bazelbuild/bazel-integration-testing/archive/1bad547fd814c7642e8edfd4f0974ed8a25b5252.zip"],
)

load(
    "@build_bazel_integration_testing//tools:repositories.bzl",
    "bazel_binaries",
)

bazel_binaries(versions = ["0.12.0"])

git_repository(
    name = "bazel_gazelle",
    commit = "0401a4e2814b8190bdf0c49d6b494d483d0750da",
    remote = "https://github.com/bazelbuild/bazel-gazelle.git",
)

http_archive(
    name = "io_bazel_rules_go",
    sha256 = "c1f52b8789218bb1542ed362c4f7de7052abcf254d865d96fb7ba6d44bc15ee3",
    url = "https://github.com/bazelbuild/rules_go/releases/download/0.12.0/rules_go-0.12.0.tar.gz",
)

load(
    "//docker/compose:defs.bzl",
    docker_compose_repositories = "repositories",
)

docker_compose_repositories()

git_repository(
    name = "io_bazel_rules_docker",
    commit = "74441f0d7000dde42ce02c30ce2d1bf6c0c1eebc",
    remote = "https://github.com/bazelbuild/rules_docker.git",
)

load(
    "@io_bazel_rules_docker//container:container.bzl",
    "container_pull",
    container_repositories = "repositories",
)

container_repositories()

container_pull(
    name = "rbe_debian8",
    digest = "sha256:0d5db936f8fa04638ca31e4fc117415068dca43dc343d605c0db2a15f433a327",  # 17 May 2018 at 23:42:25 UTC+2
    registry = "gcr.io/cloud-marketplace",
    repository = "google/rbe-debian8",
)

# Used for testing pushing to an ECR registry
container_pull(
    name = "busybox",
    registry = "index.docker.io",
    repository = "library/busybox",
    tag = "1.28.4-uclibc",
)

git_repository(
    name = "distroless",
    commit = "3cda1707e86ac6160444fded894e712f85619c05",
    remote = "https://github.com/GoogleContainerTools/distroless.git",
)

load(
    "//rbs/images:defs.bzl",
    images_dependencies = "dependencies",
)

images_dependencies()

git_repository(
    name = "runtimes_common",
    remote = "https://github.com/GoogleCloudPlatform/runtimes-common.git",
    tag = "v0.1.0",
)

http_file(
    name = "certstrap_darwin_amd64",
    executable = True,
    sha256 =
        "4b9eab000e459419b8da09e4fa0023fd5a6469668953b66e70ccd269366273ae",
    urls = [
        "https://github.com/square/certstrap/releases/download/v1.1.1/certstrap-v1.1.1-darwin-amd64",
    ],
)

http_file(
    name = "certstrap_linux_amd64",
    executable = True,
    sha256 =
        "274c3e746761014df4b014103a36f8e8adad26a282fdd294d886a1e305cbfaa7",
    urls = [
        "https://github.com/square/certstrap/releases/download/v1.1.1/certstrap-v1.1.1-linux-amd64",
    ],
)

load("@io_bazel_rules_go//go:def.bzl", "go_rules_dependencies", "go_register_toolchains")

go_rules_dependencies()

go_register_toolchains()

load("@bazel_gazelle//:deps.bzl", "gazelle_dependencies", "go_repository")

gazelle_dependencies()

go_repository(
    name = "com_github_mwitkow_grpc_proxy",
    commit = "2555aec3ddbfed4dd0e4ce021480060c1ed23ea9",
    importpath = "github.com/mwitkow/grpc-proxy",
    remote = "https://github.com/JackWink/grpc-proxy",
    vcs = "git",
)

load(
    "//docker/dind:defs.bzl",
    dind_dependencies = "dependencies",
)

dind_dependencies()
