#! /bin/bash

set -e

version=1.1.12
directory=free/beta/2018-11-01-oIDoJTpO

if [[ `uname` = "Linux" ]] ; then
	package=3DelightNSI-$version-Linux-x86_64
	curl https://3delight-downloads.s3-us-east-2.amazonaws.com/$directory/$package.tar.xz > $package.tar.xz
	tar -xf $package.tar.xz
	mv ./$package/3delight/Linux-x86_64 ./3delight
else
	package=3DelightNSI-$version-Darwin-Universal
	curl https://3delight-downloads.s3-us-east-2.amazonaws.com/$directory/$package.dmg > $package.dmg
	sudo hdiutil mount $package.dmg
	sudo installer -pkg /Volumes/3Delight\ NSI\ $version/3DelightNSI-$version-Darwin-x86_64.pkg -target /
	sudo mv /Applications/3Delight ./3delight
fi
