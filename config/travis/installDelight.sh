#! /bin/bash

set -e

version=13.0.18

if [[ `uname` = "Linux" ]] ; then
	package=3delight-$version-Linux-x86_64
	curl -A Mozilla/4.0 http://www.3delight.com/downloads/free/$package.tar.xz > $package.tar.xz
	tar -xf $package.tar.xz
	mv ./$package/3delight/Linux-x86_64 ./3delight
else
	package=3delight-$version-Darwin-Universal
	curl -A Mozilla/4.0 http://www.3delight.com/downloads/free/$package.dmg > $package.dmg
	sudo hdiutil mount $package.dmg
	sudo installer -pkg /Volumes/3Delight\ $version/$package.pkg -target /
	sudo mv /Applications/3Delight ./3delight
fi
