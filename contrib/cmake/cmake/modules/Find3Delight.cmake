#==========
#
# Copyright (c) 2010-2018, Dan Bethell, Alex Fuller.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#     * Neither the name of Dan Bethell nor the names of any
#       other contributors to this software may be used to endorse or
#       promote products derived from this software without specific prior
#       written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
# IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#==========
#
# Variables defined by this module:
#   3Delight_FOUND
#   3Delight_INCLUDE_DIR
#   3Delight_LIBRARIES
#   3Delight_LIBRARY_DIR
#
# Usage:
#   FIND_PACKAGE( 3Delight )
#   FIND_PACKAGE( 3Delight REQUIRED )
#
# Note:
# You can tell the module where 3Delight is installed by setting
# the 3Delight_INSTALL_PATH (or setting the DELIGHT environment
# variable before calling FIND_PACKAGE.
#
# E.g.
#   SET( 3Delight_INSTALL_PATH "/usr/local/3delight-9.0.0/Linux-x86_64" )
#   FIND_PACKAGE( 3Delight REQUIRED )
#
#==========

# our includes
find_path( 3Delight_INCLUDE_DIR nsi.h
  ${DELIGHT_ROOT}/include
  ${3Delight_INSTALL_PATH}/include
  )

# our library itself
find_library( 3Delight_LIBRARIES 3delight
  ${DELIGHT_ROOT}/lib
  ${3Delight_INSTALL_PATH}/lib
  )

# our library path
get_filename_component( 3Delight_LIBRARY_DIR ${3Delight_LIBRARIES} PATH )

# did we find everything?
include( FindPackageHandleStandardArgs )
FIND_PACKAGE_HANDLE_STANDARD_ARGS( "_3Delight" DEFAULT_MSG
  3Delight_INCLUDE_DIR
  3Delight_LIBRARIES
  3Delight_LIBRARY_DIR
  )