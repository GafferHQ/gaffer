# Gaffer & Dependencies Container Build

Using Docker to build Gaffer and it's dependencies provides isolation and reproducibility of the software build process.

#### Notes when using Docker:

* You only need to install docker all other dependencies are downloaded & built by the Dockerfile script.
* You can build on any platform supported by Docker (windows, other linux distros & OSX).
* The build is performed in a centos7 based container

#### To build everything:

* [install docker](https://www.docker.com/community-edition#download)
* Download an Arnold install to `dependencies/build/docker`
  * Currently it uses `Arnold-4.2.13.0-linux.tgz`
  * If you use a different version then you'll need to update the *Dockerfile*
* In the same directory which contains the Dockerfile run:
  * `docker build -t brickie .`

#### To use the build output:

* To run the container:
  * `docker run -it -v ~/gafferbuild:/gafferbuild brickie /bin/bash`
* You should be able to run gaffer from ~/gafferbuild on the host machine
