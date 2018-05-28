#!/bin/bash
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

set -eou pipefail

# Set up AWS shared credentials and test config when on Travis
setup_aws_credentials() {
  HAS_AWS=false
  if ! ${TRAVIS:-false}; then
    echo "TRAVIS=false: assuming end-to-end tests on AWS can run"
    HAS_AWS=true
  elif ${TRAVIS:-false} && [ -n "${SECRET__AWS_ACCESS_KEY_ID:-}" ]; then
    echo "Set up AWS support for Travis for running end-to-end-tests"
    if [ -d "$HOME/.aws" ]; then
      echo '~/.aws should not exist.  Abort!'
      exit 1
    fi
    if [ -d "$HOME/.bazel_bf" ]; then
      echo '~/.bazel_bf should not exist.  Abort!'
      exit 1
    fi
    HAS_AWS=true
    mkdir ~/.aws
    cat <<EOF > ~/.aws/config
[default]
region = ${SECRET__AWS_REGION}
output = json
EOF
    cat <<EOF > ~/.aws/credentials
[default]
aws_access_key_id = ${SECRET__AWS_ACCESS_KEY_ID}
aws_secret_access_key = ${SECRET__AWS_SECRET_ACCESS_KEY}
EOF
    mkdir ~/.bazel_bf
    echo "${SECRET__INFRA_TEST_CONFIG}" > ~/.bazel_bf/test_config.json
    mkdir ~/.docker
    cat <<EOF > ~/.docker/config.json
{
  "auths" : {
  },
  "credHelpers" : {
    "184213156179.dkr.ecr.eu-west-1.amazonaws.com" : "ecr-login"
  }
}
EOF
  else
    echo "TRAVIS=true but no AWS credential was found: no end-to-end test will be run on AWS"
  fi
}

setup_docker() {
  # On Travis, Docker is only supported on Linux.
  if [ "$(uname)" = "Darwin" ] && ${TRAVIS:-false}; then
    HAS_DOCKER=false
  else
    HAS_DOCKER=true
  fi
}

build_all() {
  if $HAS_DOCKER; then
    bazel build //...
  else
    bazel build //... --build_tag_filters=-docker --test_output=errors
  fi
}

test_base() {
  bazel test //... --build_tag_filters=-docker --test_tag_filters=-docker,-aws,-manual --test_output=errors
}

test_with_docker() {
  if $HAS_DOCKER; then
    bazel test //... --test_tag_filters=docker,-aws,-manual --test_output=errors
  fi
}

test_docker_sandbox() {
  # The Docker Bazel sandbox is not generally available.
  if ! ${TRAVIS:-false}; then
    bazel test //rbs/test:docker_test --test_output=errors
  fi
}

test_e2e_aws() {
  if ${HAS_AWS:-false}; then
    # TODO: make it work outside of standalone strategy on Linux
    if [ "$(uname)" = "Darwin" ] && ${TRAVIS:-false}; then
      bazel test //... --test_tag_filters=aws --test_output=errors
    else
      bazel test //... --test_tag_filters=aws --test_output=errors --spawn_strategy=standalone
    fi
  fi
}

setup_aws_credentials
setup_docker
build_all
test_base
test_with_docker
test_docker_sandbox
test_e2e_aws
