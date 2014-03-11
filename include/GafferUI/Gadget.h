//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2013, John Haddon. All rights reserved.
//  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
//  
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//  
//      * Redistributions of source code must retain the above
//        copyright notice, this list of conditions and the following
//        disclaimer.
//  
//      * Redistributions in binary form must reproduce the above
//        copyright notice, this list of conditions and the following
//        disclaimer in the documentation and/or other materials provided with
//        the distribution.
//  
//      * Neither the name of John Haddon nor the names of
//        any other contributors to this software may be used to endorse or
//        promote products derived from this software without specific prior
//        written permission.
//  
//  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
//  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
//  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
//  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
//  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
//  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
//  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
//  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
//  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
//  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
//  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//  
//////////////////////////////////////////////////////////////////////////

#ifndef GAFFERUI_GADGET_H
#define GAFFERUI_GADGET_H

#include "OpenEXR/ImathBox.h"

#include "IECoreGL/GL.h"

#include "Gaffer/GraphComponent.h"

#include "GafferUI/TypeIds.h"
#include "GafferUI/ButtonEvent.h"
#include "GafferUI/KeyEvent.h"
#include "GafferUI/EventSignalCombiner.h"
#include "GafferUI/DragDropEvent.h"

namespace GafferUIBindings
{

// forward declaration for friendship
void bindGadget();

}

namespace GafferUI
{

IE_CORE_FORWARDDECLARE( Gadget );
IE_CORE_FORWARDDECLARE( Style );

/// Gadgets are zoomable UI elements. They draw themselves using OpenGL, and provide an interface for
/// handling events. To present a Gadget in the user interface, it should be placed in the viewport of
/// a GadgetWidget.
/// \todo I'm not sure I like having the transform on the Gadget - perhaps ContainerGadget
/// should have a virtual childTransform() method instead?
class Gadget : public Gaffer::GraphComponent
{

	public :

		Gadget( const std::string &name=defaultName<Gadget>() );
		virtual ~Gadget();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferUI::Gadget, GadgetTypeId, Gaffer::GraphComponent );

		/// Returns the Gadget with the specified name, where name has been retrieved
		/// from an IECoreGL::HitRecord after rendering some Gadget in GL_SELECT mode.
		/// \todo Consider better mechanisms.
		static GadgetPtr select( const std::string &name );

		/// @name Parent-child relationships
		////////////////////////////////////////////////////////////////////
		//@{
		/// By default Gadgets do not accept children. Derive from ContainerGadget
		/// if you wish to accept children.
		virtual bool acceptsChild( const Gaffer::GraphComponent *potentialChild ) const;
		/// Gadgets only accept other Gadgets as parent.
		virtual bool acceptsParent( const Gaffer::GraphComponent *potentialParent ) const;		
		//@}

		/// @name Style
		/// Gadgets use Style objects to define their appearance. Styles may
		/// may be set on individual Gadgets, and are inherited by child Gadgets
		/// from their parents.
		////////////////////////////////////////////////////////////////////
		//{@
		/// Explicitly sets the Style for this Gadget, overriding any inherited
		/// Style.
		void setStyle( ConstStylePtr style );
		/// Returns any Style explicitly applied to this Gadget using setStyle().
		/// Note that this may return 0, meaning that the Gadget is inheriting the
		/// Style from the parent Gadget.
		const Style *getStyle() const;
		/// Returns the Style in effect for this Gadget, after inheriting any
		/// Style from the parent and applying possible overrides from setStyle().
		const Style *style() const;
		//@}

		/// @name State
		/// \todo Add setEnabled()/getEnabled() and setVisible()/getVisible()
		/// methods matching those we have on the Widget class.
		////////////////////////////////////////////////////////////////////
		//@{
		/// Sets whether or not this Gadget should be rendered in a highlighted
		/// state. This status is not inherited by child Gadgets. Note that highlighted
		/// drawing has not yet been implemented for all Gadget types. Derived
		/// classes may reimplement this method as necessary, but must call the base
		/// class method in their reimplementation.
		/// \todo Implement highlighted drawing for all Gadget subclasses.
		virtual void setHighlighted( bool highlighted );
		bool getHighlighted() const;
		//@}

		/// @name Transform
		/// Every Gadget has a transform which dictates how it is positioned
		/// relative to its parent.
		////////////////////////////////////////////////////////////////////
		//@{
		const Imath::M44f &getTransform() const;
		void setTransform( const Imath::M44f &matrix );
		/// Returns the full transform of this Gadget relative to the
		/// specified ancestor. If ancestor is not specified then the
		/// transform from the root of the hierarchy is returned.
		Imath::M44f fullTransform( ConstGadgetPtr ancestor = 0 ) const;
		//@}

		/// @name Display
		////////////////////////////////////////////////////////////////////
		//@{
		/// Renders the Gadget into the current OpenGL context. If currentStyle
		/// is passed then it must already have been bound with Style::bind(),
		/// and will be used if and only if not overridden by a Style applied
		/// specifically to this Gadget. Typically users will not pass currentStyle -
		/// but it must be passed by Gadget implementations when rendering child
		/// Gadgets in doRender().
		void render( const Style *currentStyle = 0 ) const;
		/// The bounding box of the Gadget before transformation.
		virtual Imath::Box3f bound() const = 0;
		/// The bounding box transformed by the result of getTransform().
		Imath::Box3f transformedBound() const;
		/// The bounding box transformed by the result of fullTransform( ancestor ).
		Imath::Box3f transformedBound( ConstGadgetPtr ancestor ) const;
		typedef boost::signal<void ( Gadget * )> RenderRequestSignal;
		RenderRequestSignal &renderRequestSignal();
		//@}
		
		/// @name Tool tips
		/// Gadgets may have tool tips - they are not responsible for displaying
		/// them but instead just need to provide the text to be displayed.
		////////////////////////////////////////////////////////////////////
		//@{
		/// Returns the tool tip to be displayed. Derived classes may
		/// reimplement this, in which case they should return Base::getToolTip()
		/// if it is non-empty (ie has been set by setToolTip()) and otherwise
		/// return some automatically generated tip.
		virtual std::string getToolTip( const IECore::LineSegment3f &position ) const;
		/// Sets the tool tip - pass the empty string if you wish to reset this
		/// and revert to default behaviour.
		void setToolTip( const std::string &toolTip );
		//@}
		
		/// @name Events
		/// Events are specified as boost::signals. This allows anything to
		/// react to an event rather than just the Gadget receiving it,
		/// which makes for much more flexible customisation of the UI.
		////////////////////////////////////////////////////////////////////
		//@{
		/// A signal used to represent button related events.
		typedef boost::signal<bool ( GadgetPtr, const ButtonEvent &event ), EventSignalCombiner<bool> > ButtonSignal; 
		/// The signal triggered by a button press event.
		ButtonSignal &buttonPressSignal();
		/// The signal triggered by a button release event.
		ButtonSignal &buttonReleaseSignal();
		/// The signal triggered by a button double click event.
		ButtonSignal &buttonDoubleClickSignal();
		/// The signal triggered by the mouse wheel.
		ButtonSignal &wheelSignal();
		
		typedef boost::signal<void ( GadgetPtr, const ButtonEvent &event )> EnterLeaveSignal; 
		/// The signal triggered when the mouse enters the Gadget.
		EnterLeaveSignal &enterSignal();
		/// The signal triggered when the mouse leaves the Gadget.
		EnterLeaveSignal &leaveSignal();	
		/// A signal emitted whenever the mouse moves within a Gadget.
		ButtonSignal &mouseMoveSignal();
		
		typedef boost::signal<IECore::RunTimeTypedPtr ( GadgetPtr, const DragDropEvent &event ), EventSignalCombiner<IECore::RunTimeTypedPtr> > DragBeginSignal; 
		typedef boost::signal<bool ( GadgetPtr, const DragDropEvent &event ), EventSignalCombiner<bool> > DragDropSignal; 
		
		/// This signal is emitted if a previous buttonPressSignal() returned true, and the
		/// user has subsequently moved the mouse with the button down. To initiate a drag
		/// a Gadget must return an IECore::RunTimeTypedPtr representing the data being
		/// dragged.
		DragBeginSignal &dragBeginSignal();
		/// Emitted when a drag enters this Gadget.
		DragDropSignal &dragEnterSignal();
		/// Upon initiation of a drag with dragBeginSignal(), this signal will be triggered
		/// to update the drag with the new mouse position.
		DragDropSignal &dragMoveSignal();
		/// Emitted when a drag leaves this Gadget.
		DragDropSignal &dragLeaveSignal();
		/// This signal is emitted when a drag has been released over this Gadget.
		DragDropSignal &dropSignal();
		/// After the dropSignal() has been emitted on the destination of the drag, the
		/// dragEndSignal() is emitted on the Gadget which provided the source of the
		/// drag.
		DragDropSignal &dragEndSignal();
		
		/// A signal used to represent key related events.
		/// \todo We need some sort of focus model to say who gets the events.
		typedef boost::signal<bool ( GadgetPtr, const KeyEvent &key ), EventSignalCombiner<bool> > KeySignal;
		/// The signal triggered by a key press event.
		KeySignal &keyPressSignal();
		/// The signal triggered by a key release event.
		KeySignal &keyReleaseSignal();
		
		/// A signal emitted when the host event loop is idle. Connections
		/// to this should be limited in duration because idle events consume
		/// CPU when the program would otherwise be inactive.
		typedef boost::signal<void ()> IdleSignal; 
		static IdleSignal &idleSignal();
		//@}
		
	protected :
	
		/// The subclass specific part of render(). This must be implemented
		/// appropriately by all subclasses. The public render() method
		/// sets the GL state up with the name attribute and transform for
		/// this Gadget, makes sure the style is bound and then calls doRender().
		virtual void doRender( const Style *style ) const = 0;
		
	private :
		
		void styleChanged();
		
		ConstStylePtr m_style;
		
		bool m_highlighted;
		
		Imath::M44f m_transform;
		
		RenderRequestSignal m_renderRequestSignal;
		
		IECore::InternedString m_toolTip;
			
		ButtonSignal m_buttonPressSignal;
		ButtonSignal m_buttonReleaseSignal;
		ButtonSignal m_buttonDoubleClickSignal;
		ButtonSignal m_wheelSignal;
		
		EnterLeaveSignal m_enterSignal;
		EnterLeaveSignal m_leaveSignal;
		ButtonSignal m_mouseMoveSignal;

		DragBeginSignal m_dragBeginSignal;
		DragDropSignal m_dragEnterSignal;
		DragDropSignal m_dragMoveSignal;
		DragDropSignal m_dragLeaveSignal;
		DragDropSignal m_dragEndSignal;
		DragDropSignal m_dropSignal;

		KeySignal m_keyPressSignal;
		KeySignal m_keyReleaseSignal;
		
		GLuint m_glName;

		// used by the bindings to know when the idleSignal()
		// has been accessed, and only use an idle timer
		// when absolutely necessary (when slots are connected).
		static IdleSignal &idleSignalAccessedSignal();
		friend void GafferUIBindings::bindGadget();

};

} // namespace GafferUI

#endif // GAFFERUI_GADGET_H
