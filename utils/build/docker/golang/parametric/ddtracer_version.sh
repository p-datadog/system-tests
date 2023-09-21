#!/bin/bash

set -eu

go mod tidy

# Read the library version out of the version.go file
mod_dir=$(go list -f '{{.Dir}}' -m gopkg.in/DataDog/dd-trace-go.v1)
version=$(sed -nrE 's#.*"v(.*)".*#\1#p' "$mod_dir"/internal/version/version.go) # Parse the version string content "v.*"
echo "$version" > SYSTEM_TESTS_LIBRARY_VERSION