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

if [ -z ${RUNFILES+x} ]; then
  if [[ "$(pwd)" == *.runfiles/infra ]]; then
    RUNFILES=..
  else
    RUNFILES=${TEST_SRCDIR/..:-"${BASH_SOURCE[0]}.runfiles"}
  fi
fi

if [ "$(uname)" = "Linux" ]; then
  BIN=$RUNFILES/certstrap_linux_amd64/file/downloaded
elif [ "$(uname)" == "Darwin" ]; then
  BIN=$RUNFILES/certstrap_darwin_amd64/file/downloaded
else
  echo "Unexpected uname $(uname)"
  exit 1
fi

$BIN "$@"
