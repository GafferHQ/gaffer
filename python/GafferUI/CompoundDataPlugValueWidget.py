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

from __future__ import with_statement

import IECore

import Gaffer
import GafferUI

class CompoundDataPlugValueWidget( GafferUI.CompoundPlugValueWidget ) :

	def __init__( self, plug, collapsed=True, label=None, summary=None, editable=True, **kw ) :

		GafferUI.CompoundPlugValueWidget.__init__( self, plug, collapsed, label, summary, **kw )

		self.__editable = True
		self.__footerWidget = None

	def _childPlugWidget( self, childPlug ) :
	
		return _MemberPlugValueWidget( childPlug, self._label( childPlug ) )
		
	def _footerWidget( self ) :
	
		if self.__footerWidget is not None :
			return self.__footerWidget
		
		if self.__class__ is CompoundDataPlugValueWidget : # slight hack so that SectionedCompoundDataPlugValueWidget doesn't get a plus button
			self.__footerWidget = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )
			self.__footerWidget.append( GafferUI.Spacer( IECore.V2i( GafferUI.PlugWidget.labelWidth(), 1 ) ) )
			self.__footerWidget.append(
				GafferUI.MenuButton( image="plus.png", hasFrame=False, menu=GafferUI.Menu( self.__addMenuDefinition() ) )
			)
			self.__footerWidget.append( GafferUI.Spacer( IECore.V2i( 1 ), IECore.V2i( 999999, 1 ) ), expand = True )

		return self.__footerWidget
	
	## May be reimplemented by derived classes to return a suitable label
	# for the member represented by childPlug.
	def _label( self, childPlug ) :
	
		if not childPlug.getFlags( Gaffer.Plug.Flags.Dynamic ) :
			return childPlug["name"].getValue()
		
		return None
		
	def __addMenuDefinition( self ) :
	
		result = IECore.MenuDefinition()
		result.append( "/Add/Bool", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addItem ), "", IECore.BoolData( False ) ) } )
		result.append( "/Add/Float", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addItem ), "", IECore.FloatData( 0 ) ) } )
		result.append( "/Add/Int", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addItem ), "", IECore.IntData( 0 ) ) } )
		result.append( "/Add/NumericDivider", { "divider" : True } )
		
		result.append( "/Add/String", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addItem ), "", IECore.StringData( "" ) ) } )
		result.append( "/Add/StringDivider", { "divider" : True } )

		result.append( "/Add/V2i", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addItem ), "", IECore.V2iData( IECore.V2i( 0 ) ) ) } )
		result.append( "/Add/V3i", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addItem ), "", IECore.V3iData( IECore.V3i( 0 ) ) ) } )
		result.append( "/Add/V2f", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addItem ), "", IECore.V2fData( IECore.V2f( 0 ) ) ) } )
		result.append( "/Add/V3f", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addItem ), "", IECore.V3fData( IECore.V3f( 0 ) ) ) } )
		result.append( "/Add/VectorDivider", { "divider" : True } )
		
		result.append( "/Add/Color3f", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addItem ), "", IECore.Color3fData( IECore.Color3f( 0 ) ) ) } )
		result.append( "/Add/Color4f", { "command" : IECore.curry( Gaffer.WeakMethod( self.__addItem ), "", IECore.Color4fData( IECore.Color4f( 0, 0, 0, 1 ) ) ) } )
		
		return result
		
	def __addItem( self, name, value ) :
	
		with Gaffer.UndoContext( self.getPlug().ancestor( Gaffer.ScriptNode.staticTypeId() ) ) :
			self.getPlug().addOptionalMember( name, value, enabled=True )

class _MemberPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, childPlug, label=None ) :
	
		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )
	
		GafferUI.PlugValueWidget.__init__( self, self.__row, childPlug )
				
		if label is not None or not childPlug.getFlags( Gaffer.Plug.Flags.Dynamic ) :
			nameWidget = GafferUI.LabelPlugValueWidget( 
				childPlug,
				horizontalAlignment = GafferUI.Label.HorizontalAlignment.Right,
				verticalAlignment = GafferUI.Label.VerticalAlignment.Center,
			)
			if label is not None :
				nameWidget.label().setText( label )
			nameWidget.label()._qtWidget().setFixedWidth( GafferUI.PlugWidget.labelWidth() )
			# cheat to get the height of the label to match the height of a line edit
			# so the label and plug widgets align nicely. ideally we'd get the stylesheet
			# sorted for the QLabel so that that happened naturally, but QLabel sizing appears
			# somewhat unpredictable (and is sensitive to HTML in the text as well), making this
			# a tricky task.
			nameWidget.label()._qtWidget().setFixedHeight( 20 )
		else :
			nameWidget = GafferUI.StringPlugValueWidget( childPlug["name"] )
			nameWidget.textWidget()._qtWidget().setFixedWidth( GafferUI.PlugWidget.labelWidth() )
			
		self.__row.append( nameWidget,
			verticalAlignment = GafferUI.Label.VerticalAlignment.Top
		)
		
		if "enabled" in childPlug :
			self.__row.append(
				GafferUI.BoolPlugValueWidget(
					childPlug["enabled"],
					displayMode = GafferUI.BoolWidget.DisplayMode.Switch
				),
				verticalAlignment = GafferUI.Label.VerticalAlignment.Top,
			)
		
		self.__row.append( GafferUI.PlugValueWidget.create( childPlug["value"] ), expand = True )
		
		self._updateFromPlug()
	
	def setPlug( self, plug ) :
	
		GafferUI.PlugValueWidget.setPlug( self, plug )
		
		if isinstance( self.__row[0], GafferUI.LabelPlugValueWidget ) :
			self.__row[0].setPlug( plug )
		else :
			self.__row[0].setPlug( plug["name"] )
		
		if "enabled" in plug :
			self.__row[1].setPlug( plug["enabled"] )
		
		self.__row[-1].setPlug( plug["value"] )
		
	def hasLabel( self ) :
	
		return True

	def childPlugValueWidget( self, childPlug, lazy=True ) :
	
		for w in self.__row :
			if w.getPlug().isSame( childPlug ) :
				return w
				
		return None
	
	def setReadOnly( self, readOnly ) :
	
		if readOnly == self.getReadOnly() :
			return
			
		GafferUI.PlugValueWidget.setReadOnly( self, readOnly )
		
		for w in self.__row :
			w.setReadOnly( readOnly )
	
	def _updateFromPlug( self ) :
	
		if "enabled" in self.getPlug() :
			with self.getContext() :
				enabled = self.getPlug()["enabled"].getValue()
				
			if isinstance( self.__row[0], GafferUI.StringPlugValueWidget ) :
				self.__row[0].setEnabled( enabled )
				
			self.__row[-1].setEnabled( enabled )
						
GafferUI.PlugValueWidget.registerType( Gaffer.CompoundDataPlug.staticTypeId(), CompoundDataPlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.CompoundDataPlug.MemberPlug.staticTypeId(), _MemberPlugValueWidget )
