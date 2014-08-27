##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import GafferUI

class _Section( GafferUI.CompoundDataPlugValueWidget ) :

	def __init__( self, plug, label, summary, names, labels, **kw ) :

		GafferUI.CompoundDataPlugValueWidget.__init__( self, plug, True, label, summary, **kw )

		self.__names = set( names )
		self.__namesToLabels = dict( zip( names, labels ) )

	def _childPlugs( self ) :

		return [ p for p in self.getPlug().children() if p["name"].getValue() in self.__names ]

	def _label( self, childPlug ) :

		return self.__namesToLabels[childPlug["name"].getValue()]

class SectionedCompoundDataPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, sections, **kw ) :

		self.__column = GafferUI.ListContainer( spacing = 8 )

		GafferUI.PlugValueWidget.__init__( self, self.__column, plug, **kw )

		self.__sections = []

		with self.__column :
			for section in sections :
				self.__sections.append( _Section(
						plug,
						label = section["label"],
						summary = section.get( "summary", None ),
						names = [ e[0] for e in section["namesAndLabels"] ],
						labels = [ e[1] for e in section["namesAndLabels"] ],
					)
				)

	def setPlug( self, plug ) :

		super( SectionedCompoundDataPlugValueWidget, self ).setPlug( plug )

		for s in self.__sections:
			s.setPlug( plug )

	def hasLabel( self ) :

		return True

	def childPlugValueWidget( self, childPlug, lazy=True ) :

		for section in self.__column :
			result = section.childPlugValueWidget( childPlug, lazy )
			if result is not None :
				return result

		return None

	def setReadOnly( self, readOnly ) :

		if readOnly == self.getReadOnly() :
			return

		GafferUI.PlugValueWidget.setReadOnly( self, readOnly )

		for section in self.__column :
			section.setReadOnly( readOnly )

	def _updateFromPlug( self ) :

		pass
