#! /bin/bash
# BuildTarget: images/mouseLeftClick.png
# BuildTarget: images/mouseRightClick.png
# BuildTarget: images/mouseMiddleClick.png
# BuildTarget: images/mouseWheelUpDown.png

set -e

cp $GAFFER_ROOT/doc/gaffer/graphics/mouseLeftClick.png images
cp $GAFFER_ROOT/doc/gaffer/graphics/mouseRightClick.png images
cp $GAFFER_ROOT/doc/gaffer/graphics/mouseMiddleClick.png images
cp $GAFFER_ROOT/doc/gaffer/graphics/mouseWheelUpDown.png images
