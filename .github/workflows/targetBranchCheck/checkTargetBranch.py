#!/usr/bin/env python
##########################################################################
#
#  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#      * Redistributions of source code must retain the above
#        copyright notice, this list of conditions and the following
#        disclaimer.
#
#      * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided with
#        the distribution.
#
#      * Neither the name of Cinesite VFX Ltd. nor the names of
#        any other contributors to this software may be used to endorse or
#        promote products derived from this software without specific prior
#        written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

import os
import sys
from unittest import expectedFailure

with open( "Changes.md" ) as changes :
	firstLine = changes.readline()

version = firstLine.split()[0]
print( "Version : {}".format( version ) )

targetBranch = os.environ["GITHUB_BASE_REF"]
print( "Target Branch : {}".format( targetBranch ) )

milestoneVersion, majorVersion = version.split( "." )[:2]
if majorVersion == "x" :
	expectedTargetBranch = "main"
else :
	expectedTargetBranch = "{}.{}_maintenance".format( milestoneVersion, majorVersion )
print( "Expected target branch : {}".format( expectedTargetBranch ) )

if expectedTargetBranch != targetBranch :
	print( "ERROR : Target branch should be {}".format( expectedTargetBranch ) )
	sys.exit( 1 )
