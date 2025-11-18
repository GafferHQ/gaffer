#!/bin/sh

set -e

# We are running inside a minimal Rocky container in order to preserve disk
# space on the GitHub runners. Install the bare minimum of packages required by
# Gaffer/RenderMan.

microdnf install -y lcms2 mesa-libGL mesa-libGLU libglvnd-opengl fontconfig libgomp

# Run the tests.
## \todo Run GafferRenderManUITest as well. To do this we need to install some
# additional packages above, and modify the `podman run` call in `main.yml` so
# that this container can connect to the X server running in the parent container.

echo "::add-matcher::./.github/workflows/main/problemMatchers/unittest.json"
$GAFFER_BUILD_DIR/bin/gaffer test IECoreRenderManTest GafferRenderManTest
echo "::remove-matcher owner=unittest::"
