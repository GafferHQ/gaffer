#! /bin/bash

set -e

gaffer screengrab \
 	-script scripts/blank.gfr \
	-selection OSLCode \
	-editor GafferUI.NodeEditor \
	-image images/blank.png

gaffer screengrab \
	-script scripts/parameters.gfr \
	-selection OSLCode \
	-editor GafferUI.NodeEditor \
	-image images/parameters.png

gaffer screengrab \
	-script scripts/simpleStripes.gfr \
	-selection OSLCode \
	-delay 5 \
	-editor GafferUI.Viewer \
	-image images/shaderBallStripes.png

gaffer screengrab \
	-script scripts/coloredStripes.gfr \
	-selection OSLCode \
	-delay 5 \
	-editor GafferUI.Viewer \
	-image images/shaderBallColoredStripes.png

cp $GAFFER_ROOT/graphics/plus.png images
