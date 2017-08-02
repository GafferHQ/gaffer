FROM centos:7.0.1406
MAINTAINER Don Boogert <donbo@image-engine.com>
RUN yum install gcc-c++ -y
RUN yum install git -y
RUN yum install cmake -y
RUN yum install wget -y
RUN yum install make -y
RUN yum install m4 -y
RUN yum install libXi-devel -y
RUN yum install patch -y
RUN yum install mesa-libGLU-devel -y
RUN yum install libtool -y
RUN yum install which -y
RUN yum install ncurses-devel -y
RUN yum install libXrandr-devel -y
RUN yum install libXmu-devel -y
RUN yum install byacc -y
RUN yum install bison -y
RUN yum install flex -y
RUN yum install python-devel -y
RUN yum install zlib-devel -y
RUN yum install libXcursor-devel -y
RUN yum install doxygen -y
RUN yum install inkscape -y
RUN yum install epel-release -y
RUN yum install supervisor -y
RUN yum install libcurl-devel -y
RUN yum install libXinerama-devel -y
RUN yum install bzip2-devel -y
RUN yum install freetype-devel -y
RUN wget https://bootstrap.pypa.io/ez_setup.py -O - | python
RUN wget https://pypi.python.org/packages/source/r/requests/requests-2.9.1.tar.gz
RUN tar xvf requests-2.9.1.tar.gz
RUN cd requests-2.9.1 && ls && python setup.py install
RUN wget http://downloads.sourceforge.net/project/scons/scons/2.4.1/scons-2.4.1-1.noarch.rpm
RUN rpm -i -v scons-2.4.1-1.noarch.rpm
RUN wget  https://github.com/sphinx-doc/sphinx/archive/1.5.5.tar.gz
RUN tar xvf 1.5.5.tar.gz
RUN cd /sphinx-1.5.5 && ls && python setup.py install
RUN mkdir /arnold
COPY Arnold-4.2.13.0-linux.tgz /arnold/
RUN cd /arnold && tar xvf Arnold-4.2.13.0-linux.tgz
ENV BUILD_DIR /gafferbuild/
ENV VERSION 0.32.0.0
ENV ARNOLD_ROOT /arnold/
RUN git clone https://github.com/donboie/dependencies.git && cd dependencies && git checkout docker
RUN cd /dependencies && build/buildOpenSSL.sh
RUN cd /dependencies && build/buildPython.sh
RUN cd /dependencies && build/buildSubprocess32.sh
RUN cd /dependencies && build/buildBoost.sh
RUN cd /dependencies && build/buildJPEG.sh
RUN cd /dependencies && build/buildTIFF.sh
RUN cd /dependencies && build/buildPNG.sh
RUN cd /dependencies && build/buildFreeType.sh
RUN cd /dependencies && build/buildTBB.sh
RUN cd /dependencies && build/buildEXR.sh
RUN cd /dependencies && build/buildFonts.sh
RUN cd /dependencies && build/buildGLEW.sh
RUN cd /dependencies && build/buildOCIO.sh
RUN cd /dependencies && build/buildOIIO.sh
RUN cd /dependencies && build/buildVDB.sh
RUN cd /dependencies && build/buildLLVM.sh
RUN cd /dependencies && build/buildOSL.sh
RUN cd /dependencies && build/buildHDF5.sh
RUN cd /dependencies && build/buildAlembic.sh
RUN cd /dependencies && build/buildXerces.sh
RUN cd /dependencies && build/buildAppleseed.sh
RUN cd /dependencies && build/buildResources.sh
RUN cd /dependencies && build/buildCortex.sh
RUN cd /dependencies && build/buildPyOpenGL.sh
RUN cd /dependencies && build/buildQt.sh
RUN cd /dependencies && build/buildPySide.sh
RUN cd /dependencies && build/buildPackage.sh

RUN git clone https://github.com/GafferHQ/gaffer.git
RUN cd gaffer && scons BUILD_DIR=/gafferbuild/ build -j 2
