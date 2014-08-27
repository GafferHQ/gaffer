##########################################################################
#
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

## The ContainerWidget class provides a base for all
# Widgets which may hold other Widgets as children.
class ContainerWidget( GafferUI.Widget ) :

	def __init__( self, topLevelWidget, **kw ) :

		GafferUI.Widget.__init__( self, topLevelWidget, **kw )

	## Must be implemented in subclasses to add a child.
	# This is used by the automatic parenting mechanism.
	# In the case of a Container with a limited number of
	# children, this function should throw an exception when
	# no more children may be added. Please note that after
	# changing the parent of Widget._qtWidget(), you must call
	# Widget._applyVisibility().
	def addChild( self, child, **kw ) :

		raise NotImplementedError

	## Must be implemented in subclasses to remove
	# any references to the specified child. This allows
	# reparenting of that child into another ContainerWidget.
	# Please note that after changing the parent of Widget._qtWidget(),
	# you must call Widget._applyVisibility().
	def removeChild( self, child ) :

		raise NotImplementedError

	## Should be implemented by derived classes where necessary, to
	# ensure the descendant Widget is visible within the area of this
	# Widget. For instance, a scrolling container should scroll to show
	# the widget. This method is used by Widget.reveal().
	def _revealDescendant( self, descendant ) :

		pass

	def __enter__( self ) :

		GafferUI.Widget._pushParent( self )

		return self

	def __exit__( self, type, value, traceBack ) :

		assert( GafferUI.Widget._popParent() is self )
