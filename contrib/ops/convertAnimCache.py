##########################################################################
#  
#  Copyright (c) 2012, John Haddon. All rights reserved.
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
#      * Neither the name of John Haddon nor the names of
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
import glob

import IECore

class convertAnimCache( IECore.Op ) :

	def __init__( self ) :
	
		IECore.Op.__init__( self, "Converts animation caches from an old skool format to a nice new one.", IECore.FileSequenceParameter( "result", "" ) )
		
		self.parameters().addParameters(
			
			[
				IECore.FileSequenceParameter(
					"inputSequence",
					"The animation sequence to convert.",
					defaultValue = "",
					allowEmptyString = False,
					check = IECore.FileSequenceParameter.CheckType.MustExist,
					extensions = "fio",
			),
				IECore.FileSequenceParameter(
					"outputSequence",
					"The animation sequence to create",
					defaultValue = "",
					allowEmptyString = False,
					extensions = "fio",
				),
			],
			
		)

	def doOperation( self, args ) :
	
		src = self.parameters()["inputSequence"].getFileSequenceValue()
		dst = self.parameters()["outputSequence"].getFileSequenceValue()
		# if no frame list is specified on the dst parameter, then we use the same as src parameter.
		if isinstance( dst.frameList, IECore.EmptyFrameList ):
			dst.frameList = src.frameList
			
		for ( sf, df ) in zip( src.fileNames(), dst.fileNames() ) :
			
			sc = IECore.AttributeCache( sf, IECore.IndexedIOOpenMode.Read )
			dc = IECore.AttributeCache( df, IECore.IndexedIOOpenMode.Write )
			
			combinedBound = IECore.Box3f()
			for objectName in sc.objects() :
			
				p = b = None
				with IECore.IgnoredExceptions( Exception ) :
					p = sc.read( objectName, "vertCache.P" )
					b = sc.read( objectName, "vertCache.boundingBox" )
				
				if p is not None and b is not None :
					combinedBound.extendBy( b.value )
					dc.write( "-" + objectName, "primVar:P", p )
					dc.write( "-" + objectName, "bound", b )
			
			dc.write( "-", "bound", IECore.Box3fData( combinedBound ) )
				
		return args["outputSequence"].value
			
IECore.registerRunTimeTyped( convertAnimCache )