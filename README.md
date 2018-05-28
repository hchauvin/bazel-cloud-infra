# Flexible Remote Build Infrastructure for Bazel

[![Build Status](https://travis-ci.org/hchauvin/bazel-cloud-infra.svg?branch=master)](https://travis-ci.org/hchauvin/bazel-cloud-infra)

This repository is a proof-of-concept turnkey remote build system for
[Bazel](https://github.com/bazelbuild/bazel).  It provides
a [Bazel Buildfarm](https://github.com/bazelbuild/bazel-buildfarm) on an
AWS infrastructure with zero overhead and virtually no fixed cost.

## Motivation

Remote execution in Bazel can be used not only to unburden a bit a local development or CI
machine, but also to compile for a platform different than that of the host, when
cross-compilation is not an option.  This is especially useful when building, for instance,
Docker images on a Mac.

## Design

- A local command-line tool, `bazel_bf`, wraps around `bazel` and provides a seamless
link from the developer's or Continuous Integration machine to the remote build system.

- Almost all the AWS resources are managed using CloudFormation.

- The build cluster is managed by a Lambda function.

- The build server and build workers are deployed on ECS.

- The Lambda function authenticates the users using the local IAM credentials
(the [Sigv4][SIGV4] protocol).  The build server and workers work with mutual TLS authentication.

The mutual TLS authentication mechanism used here is voluntarily simple (and dubbed "Simple Authentication").
When the build cluster is created, static certificates and keys are generated and the story ends
here.  No effort is made to make certificates short-lived or to deal with key rotation.
Implementing a proper Public Key Infrastructure is definitely out of the scope of this project,
but the logic in `rbs.lambda.auth.get_authenticator` can be easily extended to other cases, such
as accessing an instance of the [CloudFlare's PKI/TLS toolkit][CFSSL]
or using an [AWS Private Certificate Authority][AWS_PCA].

[SIGV4]: https://docs.aws.amazon.com/general/latest/gr/signature-version-4.html
[CFSSL]: https://github.com/cloudflare/cfssl
[AWS_PCA]: https://aws.amazon.com/certificate-manager/private-certificate-authority

## Alternative solutions

There are three alternative solutions to the remote build infrastructure presented here:

* Set up the whole infrastructure for supporting
[Bazel Buildfarm](https://github.com/bazelbuild/bazel-buildfarm) from scratch, including
authentication (or protecting the resources with a VPN).
* If the goal is only to build for the Linux platform from Mac OSX:
    * Use the new Docker Bazel sandbox directly, available at Bazel HEAD (which is
what `bazel_bf --local` does).  However, execution remains local because the execroot
is currently mounted as a local volume.
    * Use a Linux box on the side, but this is costly because the machine must be quite
powerful, and cumbersome as an SSH connection must be used all the time and code
synchronized between the development machine and the Linux box.

## Installation

```bash
git clone https://github.com/hchauvin/bazel-cloud-infra
cd bazel-cloud-infra

# Build and install the `bazel_bf` wrapper on the local filesystem
bazel build //rbs/local:bazel_bf.par
rm -f /usr/local/bin/bazel_bf
cp bazel-bin/rbs/local/bazel_bf.par /usr/local/bin/bazel_bf

# Set up simple authentication
bazel run //rbs/auth:simple_auth -- config --region=<region> \
  --s3_bucket=<auth-config-bucket> \
  --s3_key=<auth-config-key>

# Write the cluster configuration, see `rbs/schemas/main_config.yaml`
# for the schema.  Do not forget to set up Simple Authentication with
# the S3 object above.
cat <<EOF > infra_config.json
...
EOF

# Upload the cluster configuration
aws s3 cp infra_config.json s3://<infra-config-bucket>/<infra-config-key>

# Build and push the container images to the ECR registry
bazel run //rbs/images:release self

# Set up the cluster
bazel_bf setup --region=<region> \
  --s3_bucket=<infra-config-bucket> \
  --s3_key=<infra-config-key>
```

## Usage

```bash
# Get full usage
bazel_bf --help

# Get the cluster status
bazel_bf remote status

# Ensure that there are at least two workers in the cluster and launch
# a remote build
cd ../other_project
bazel_bf --workers=2 build //foo:bar

# The worker image can also be used in local mode, using the Docker
# execution strategy (not yet released: to benefit from it, build
# Bazel at HEAD).
bazel_bf --local build //foo:bar

# Scale down
bazel_bf remote down --to=0

# Tear down the whole infrastructure.  Logs are kept.
# (The user is prompted for a confirmation.)
bazel_bf teardown
```

## Docker-in-docker support

It is possible, for tests that require Docker, to run docker-in-docker using
the `//docker/dind:layer` container layer.  This layer is right now only usable
with the Docker spawn strategy (the remote execution system does not currently allow
running in a privileged environment).

On Mac OSX, the Docker storage driver must be set to `"aufs"` for the `dind` layer
to work, e.g.:

```bash
$ cat ~/.docker/daemon.json
{
  "debug" : true,
  "storage-driver" : "aufs",
  "experimental" : true
}
```
