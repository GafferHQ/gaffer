//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011, John Haddon. All rights reserved.
//  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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

#include "GafferUI/TypeIds.h"
#include "GafferUI/ButtonEvent.h"
#include "GafferUI/KeyEvent.h"
#include "GafferUI/EventSignalCombiner.h"
#include "GafferUI/DragDropEvent.h"

#include "Gaffer/GraphComponent.h"

#include "IECore/RunTimeTyped.h"
#include "IECore/Renderer.h"

#include "boost/signals.hpp"

namespace GafferUI
{

IE_CORE_FORWARDDECLARE( Gadget );
IE_CORE_FORWARDDECLARE( Style );

/// Gadgets are UI elements implemented on top of the Cortex project infrastructure - 
/// they draw themselves using the Renderer interface, and provide an interface for
/// handling events. They can therefore be used by any code willing to implement the
/// Renderer interface for real time display and provide suitable events - the GadgetWidget
/// python class is an example of such a host.
/// \todo Should there be some base class for this and the Widget class?
///
/// BASIC PLAN :
///
///	* The Gadget passed as the argument to signals is the leaf gadget that received the event.
/// * But events are passed first to the topmost parent of that leaf - and then down the
///   hierarchy till the child is reached.
/// * If any handler returns true then the entire traversal is cut short there.
/// * It is the responsibility of the host (GadgetWidget) to perform this traversal.
/// * ContainerGadget is a base class for all Gadgets which have children. It has a
///   virtual method to return the transform for any given child? It is the responsibility
///   of the host to use this transform to convert the coordinates in the event into the
///   widgets own object space before calling the event? This is my least favourite bit of this
///   scheme, but otherwise the container widget is responsible for passing events on itself, and
///   it gets slightly ugly.
///
/// \todo Why not traverse up from the leaf like Qt does?
class Gadget : public Gaffer::GraphComponent
{

	public :

		Gadget( const std::string &name=staticTypeName() );
		virtual ~Gadget();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gadget, GadgetTypeId, Gaffer::GraphComponent );

		/// @name Parent-child relationships
		////////////////////////////////////////////////////////////////////
		//@{
		/// By default Gadgets do not accept children. Derive from ContainerGadget
		/// if you wish to accept children.
		virtual bool acceptsChild( Gaffer::ConstGraphComponentPtr potentialChild ) const;
		/// Gadgets only accept other Gadgets as parent.
		virtual bool acceptsParent( const Gaffer::GraphComponent *potentialParent ) const;		
		//@}

		/// @name Style
		/// Every Gadget has a Style object to define its appearance. This is set
		/// to the result of Style::getDefaultStyle() on construction but can be
		/// subsequently changed if necessary.
		////////////////////////////////////////////////////////////////////
		//{@
		ConstStylePtr getStyle() const;
		void setStyle( ConstStylePtr style );
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
		/// Renders the Gadget.
		void render( IECore::RendererPtr renderer ) const;
		/// The bounding box of the Gadget before transformation.
		virtual Imath::Box3f bound() const = 0;
		/// The bounding box transformed by the result of getTransform().
		Imath::Box3f transformedBound() const;
		/// The bounding box transformed by the result of fullTransform( ancestor ).
		Imath::Box3f transformedBound( ConstGadgetPtr ancestor ) const;
		typedef boost::signal<void ( Gadget * )> RenderRequestSignal;
		RenderRequestSignal &renderRequestSignal();
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
		
		typedef boost::signal<IECore::RunTimeTypedPtr ( GadgetPtr, const DragDropEvent &event ), EventSignalCombiner<IECore::RunTimeTypedPtr> > DragBeginSignal; 
		typedef boost::signal<bool ( GadgetPtr, const DragDropEvent &event ), EventSignalCombiner<bool> > DragDropSignal; 
		/// \todo Document me!
		DragBeginSignal &dragBeginSignal();
		DragDropSignal &dragUpdateSignal();
		DragDropSignal &dropSignal();
		DragDropSignal &dragEndSignal();
		
		/// A signal used to represent key related events.
		/// \todo We need some sort of focus model to say who gets the events.
		typedef boost::signal<bool ( GadgetPtr, const KeyEvent &key ), EventSignalCombiner<bool> > KeySignal;
		/// The signal triggered by a key press event.
		KeySignal &keyPressSignal();
		/// The signal triggered by a key release event.
		KeySignal &keyReleaseSignal();
		//@}
		
	protected :
	
		/// The subclass specific part of render(). This must be implemented
		/// appropriately by all subclasses. The public render() method
		/// sets the renderer up with the name attribute and transform for
		/// this Gadget and then calls doRender().
		virtual void doRender( IECore::RendererPtr renderer ) const = 0;
		
	private :
		
		Gadget();
		
		ConstStylePtr m_style;
		
		Imath::M44f m_transform;
		
		RenderRequestSignal m_renderRequestSignal;
			
		ButtonSignal m_buttonPressSignal;
		ButtonSignal m_buttonReleaseSignal;

		DragBeginSignal m_dragBeginSignal;
		DragDropSignal m_dragUpdateSignal;
		DragDropSignal m_dragEndSignal;
		DragDropSignal m_dropSignal;

		KeySignal m_keyPressSignal;
		KeySignal m_keyReleaseSignal;

};

} // namespace GafferUI

#endif // GAFFERUI_GADGET_H
