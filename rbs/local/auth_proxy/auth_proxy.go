// Copyright 2018 The Bazel Authors.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// gRPC proxy to inject authentication information.
package main

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"errors"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"net"

	"github.com/mwitkow/grpc-proxy/proxy"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials"
	"google.golang.org/grpc/metadata"
)

const (
	port = ":50051"
)

var (
	crt     = flag.String("crt", "client.crt", "client certificate")
	key     = flag.String("key", "client.key", "client private key")
	ca      = flag.String("ca", "ca.key", "certificate authority")
	verbose = flag.Bool("verbose", false, "verbosity")
	backend = flag.String("backend", "localhost:8098", "backend address")
	listen  = flag.String("listen", ":50051", "address to listen to")
)

func loadCredentials() (credentials.TransportCredentials, error) {
	// Load the client certificates from disk
	certificate, err := tls.LoadX509KeyPair(*crt, *key)
	if err != nil {
		return nil, fmt.Errorf("could not load client key pair: %s", err)
	}

	// Create a certificate pool from the certificate authority
	certPool := x509.NewCertPool()
	ca, err := ioutil.ReadFile(*ca)
	if err != nil {
		return nil, fmt.Errorf("could not read ca certificate: %s", err)
	}

	// Append the certificates from the CA
	if ok := certPool.AppendCertsFromPEM(ca); !ok {
		return nil, errors.New("failed to append ca certs")
	}

	creds := credentials.NewTLS(&tls.Config{
		ServerName:   "buildfarm-server",
		Certificates: []tls.Certificate{certificate},
		RootCAs:      certPool,
	})

	return creds, nil
}

func main() {
	flag.Parse()

	lis, err := net.Listen("tcp", *listen)
	if err != nil {
		log.Fatalf("failed to listen to %s: %v", *listen, err)
	}

	creds, err := loadCredentials()
	if err != nil {
		log.Fatalf("failed to load credentials: %v", err)
	}

	director := func(ctx context.Context, fullMethodName string) (context.Context, *grpc.ClientConn, error) {
		md, ok := metadata.FromIncomingContext(ctx)
		if !ok {
			if *verbose {
				log.Printf("%s: unknown method", fullMethodName)
			}
			return nil, nil, grpc.Errorf(codes.Unimplemented, "Unknown method")
		}
		if *verbose {
			log.Printf(fullMethodName)
		}
		outCtx, _ := context.WithCancel(ctx)
		outCtx = metadata.NewOutgoingContext(outCtx, md.Copy())
		conn, err := grpc.DialContext(
			ctx,
			*backend,
			grpc.WithTransportCredentials(creds),
			grpc.WithCodec(proxy.Codec()))
		return outCtx, conn, err
	}

	if *verbose {
		log.Printf("proxy %s -> %s", *listen, *backend)
	}

	server := grpc.NewServer(
		grpc.CustomCodec(proxy.Codec()),
		grpc.UnknownServiceHandler(proxy.TransparentHandler(director)))
	if err := server.Serve(lis); err != nil {
		log.Fatalf("failed to serve: %v", err)
	}
}
