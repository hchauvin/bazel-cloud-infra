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
    "@bazel_tools//tools/build_defs/repo:http.bzl",
    "http_file",
)

DEBIAN8_DOCKER = {
    "libltdl7": {
        "urls": [
            "http://httpredir.debian.org/debian/pool/main/libt/libtool/libltdl7_2.4.2-1.11+b1_amd64.deb"
        ],
        "sha256": "a1ff3f476eb52161a65ab879aa9b56fff32dac986642ffc885d4cec714a6f577",
    },
    "libnfnetlink0": {
        "urls": [
            "http://httpredir.debian.org/debian/pool/main/libn/libnfnetlink/libnfnetlink0_1.0.1-3_amd64.deb"
        ],
        "sha256": "5d486022cd9e047e9afbb1617cf4519c0decfc3d2c1fad7e7fe5604943dbbf37",
    },
    "init-system-helpers": {
        "urls": [
            "http://httpredir.debian.org/debian/pool/main/i/init-system-helpers/init-system-helpers_1.22_all.deb"
        ],
        "sha256": "bd10514a4fb6b377ec5fddb6f3dcdefe30d840c32d3dd5376d09e5a2dfc953dd",
    },
    "libxtables10": {
        "urls": [
            "http://httpredir.debian.org/debian/pool/main/i/iptables/libxtables10_1.4.21-2+b1_amd64.deb"
        ],
        "sha256": "6783f316af4cbf3ada8b9a2b7bb5f53a87c0c2575c1903ce371fdbd45d3626c6",
    },
    "iptables": {
        "urls": [
            "http://httpredir.debian.org/debian/pool/main/i/iptables/iptables_1.4.21-2+b1_amd64.deb"
        ],
        "sha256": "7747388a97ba71fede302d70361c81d486770a2024185514c18b5d8eab6aaf4e",
    },
    "aufs-tools": {
        "urls": [
            "http://httpredir.debian.org/debian/pool/main/a/aufs-tools/aufs-tools_3.2+20130722-1.1_amd64.deb"
        ],
        "sha256": "843fd190f83ee37e3fcf8f482b4d67383b23fa84f348d6ca51b7b866c1d2077d",
    },
    "docker-ce": {
        "urls": [
            "https://download.docker.com/linux/debian/dists/jessie/pool/stable/amd64/docker-ce_18.03.1~ce-0~debian_amd64.deb"
        ],
        "sha256": "f943311d415cc295815706ee13cc84c54739cc8f8f2daaaaa39fd5b7aed20f73",
    },
}

_DEBIAN_PACKAGE_BUILD = """
package(default_visibility = ["//visibility:public"])
filegroup(
    name = "package",
    srcs = ["package.deb"],
)
"""

def _remote_debian_impl(ctx):
  ctx.download(ctx.attr.urls, "package/package.deb", ctx.attr.sha256)
  ctx.file("WORKSPACE", "workspace(name = \"{name}\")".format(name = ctx.name))
  ctx.file("package/BUILD", _DEBIAN_PACKAGE_BUILD)

_remote_debian = repository_rule(
    attrs = {
        "sha256": attr.string(),
        "urls": attr.string_list(mandatory = True),
    },
    implementation = _remote_debian_impl,
)

def dependencies():
  [
      _remote_debian(
          name = "docker_dep_" + name,
          urls = attrs["urls"],
          sha256 = attrs["sha256"],
      ) for (name, attrs) in DEBIAN8_DOCKER.items()
  ]
