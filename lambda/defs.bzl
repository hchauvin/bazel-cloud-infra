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

def _prepend_workspace(path, ctx):
  """Given a path, prepend the workspace name as the parent directory"""
  # It feels like there should be an easier, less fragile way.
  if path.startswith('../'):
    # External workspace, for example
    # '../protobuf/python/google/protobuf/any_pb2.py'
    stored_path = path[len('../'):]
  elif path.startswith('external/'):
    # External workspace, for example
    # 'external/protobuf/python/__init__.py'
    stored_path = path[len('external/'):]
  else:
    # Main workspace, for example 'mypackage/main.py'
    stored_path = ctx.workspace_name + '/' + path
  if stored_path.startswith("bazel_cloud_infra/rbs/lambda/"):
    stored_path = stored_path[len("bazel_cloud_infra/rbs/lambda/"):]
  if stored_path.startswith("pypi__"):
    pkg = stored_path[len("pypi__"):stored_path.index("/")]
    if pkg in ctx.attr.exclude:
      return None
    stored_path = stored_path[stored_path.index("/") + 1:]
  if stored_path == "__init__.py":
    return None
  return stored_path

DEFAULT_EXCLUDE = [
    "boto3_1_7_0",
    "jmespath_0_9_3",
    "botocore_1_9_3",
    "python_dateutil_2_7_3",
    "docutils_0_14",
    "s3transfer_0_1_13",
    "futures_3_2_0",
    "six_1_10_0",
]

def _pkg_lambda_py_impl(ctx):
  build_lambda_py = ctx.executable.build_lambda_py
  args = [
      "--output=" + ctx.outputs.out.path,
  ]
  inputs = list(ctx.attr.src.default_runfiles.files)
  exclude = ctx.attr.exclude
  for f in inputs:
    dest = _prepend_workspace(f.short_path, ctx)
    if dest:
      args.append("--file=%s=%s" % (f.path, dest))
  # Add the zero-length __init__.py files
  for empty in ctx.attr.src.default_runfiles.empty_filenames:
    dest = _prepend_workspace(empty, ctx)
    if dest:
      args.append("--empty_file=%s" % dest)
  arg_file = ctx.actions.declare_file(ctx.label.name + ".args")
  ctx.actions.write(arg_file, "\n".join(args))

  ctx.actions.run(
      executable = build_lambda_py,
      arguments = [arg_file.path],
      inputs = inputs + [arg_file],
      outputs = [ctx.outputs.out],
      mnemonic = "PackageLambdaPy",
      use_default_shell_env = True,
  )

pkg_lambda_py = rule(
    implementation = _pkg_lambda_py_impl,
    attrs = {
        "src": attr.label(allow_files = True),
        "build_lambda_py": attr.label(
            default = Label("//lambda:build_lambda_py"),
            cfg = "host",
            executable = True,
            allow_files = True),
        "exclude": attr.string_list(default = DEFAULT_EXCLUDE),
    },
    outputs = {
        "out": "%{name}.zip",
    },
)
