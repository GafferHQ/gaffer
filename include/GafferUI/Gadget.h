//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2014, John Haddon. All rights reserved.
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

#pragma once

#include "GafferUI/ButtonEvent.h"
#include "GafferUI/DragDropEvent.h"
#include "GafferUI/EventSignalCombiner.h"
#include "GafferUI/KeyEvent.h"
#include "GafferUI/TypeIds.h"

#include "Gaffer/FilteredChildIterator.h"
#include "Gaffer/FilteredRecursiveChildIterator.h"
#include "Gaffer/GraphComponent.h"

#include "IECoreGL/GL.h"

#include "IECore/Export.h"

IECORE_PUSH_DEFAULT_VISIBILITY
#include "OpenEXR/OpenEXRConfig.h"
#if OPENEXR_VERSION_MAJOR < 3
#include "OpenEXR/ImathBox.h"
#else
#include "Imath/ImathBox.h"
#endif
IECORE_POP_DEFAULT_VISIBILITY

#include <functional>

namespace GafferUIModule
{

// forward declaration for friendship
void bindGadget();

}

namespace GafferUI
{

IE_CORE_FORWARDDECLARE( Gadget );
IE_CORE_FORWARDDECLARE( Style );
IE_CORE_FORWARDDECLARE( ViewportGadget );

/// Gadgets are zoomable UI elements. They draw themselves using OpenGL, and provide an interface for
/// handling events. To present a Gadget in the user interface, it should be placed in the viewport of
/// a GadgetWidget.
class GAFFERUI_API Gadget : public Gaffer::GraphComponent
{

	public :

		explicit Gadget( const std::string &name=defaultName<Gadget>() );
		~Gadget() override;

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( GafferUI::Gadget, GadgetTypeId, Gaffer::GraphComponent );

		enum class Layer
		{
			None = 0,
			Back = 1,
			BackMidBack = 2,
			MidBack = 4,
			Main = 8,
			MidFront = 16,
			Front = 32,
		};

		/// @name Parent-child relationships
		////////////////////////////////////////////////////////////////////
		//@{
		/// Gadgets accept any number of other Gadgets as children. Derived classes
		/// may further restrict this if they wish, but they must not accept non-Gadget children.
		bool acceptsChild( const Gaffer::GraphComponent *potentialChild ) const override;
		/// Gadgets only accept other Gadgets as parent.
		bool acceptsParent( const Gaffer::GraphComponent *potentialParent ) const override;
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
		////////////////////////////////////////////////////////////////////
		//@{
		/// Sets the visibility status for this Gadget. Note that even if this
		/// Gadget has getVisible() == true, it will not be visible on screen
		/// unless the same is true for all its ancestors.
		void setVisible( bool visible );
		/// Returns the visibility status for this Gadget.
		bool getVisible() const { return m_visible; }
		/// Returns true if this Gadget and all its parents up to the specified
		/// ancestor are visible.
		bool visible( Gadget *relativeTo = nullptr ) const;
		using VisibilityChangedSignal = Gaffer::Signals::Signal<void ( Gadget * ), Gaffer::Signals::CatchingCombiner<void>>;
		/// Emitted when the result of `Gadget::visible()` changes.
		VisibilityChangedSignal &visibilityChangedSignal();
		/// Sets whether or not this Gadget is enabled. Disabled gadgets
		/// do not receive events and are should be rendered greyed out.
		/// \todo Implement disabled drawing for all Gadget subclasses.
		void setEnabled( bool enabled );
		/// Returns the enabled status for this gadget. Note that even if
		/// `getEnabled() == true`, the gadget may still be disabled due
		/// to having a disabled ancestor.
		bool getEnabled() const;
		/// Returns true if this gadget and all its parents up to the
		/// specified ancestor are enabled.
		bool enabled( Gadget *relativeTo = nullptr ) const;
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
		Imath::M44f fullTransform( const Gadget *ancestor = nullptr ) const;
		//@}

		/// @name Display
		////////////////////////////////////////////////////////////////////
		//@{
		/// The bounding box of the Gadget before transformation. The default
		/// implementation returns the union of the transformed bounding boxes
		/// of all the children.
		virtual Imath::Box3f bound() const;
		/// The bounding box transformed by the result of getTransform().
		Imath::Box3f transformedBound() const;
		/// The bounding box transformed by the result of fullTransform( ancestor ).
		Imath::Box3f transformedBound( const Gadget *ancestor ) const;
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
		using ButtonSignal = Gaffer::Signals::Signal<bool ( Gadget *, const ButtonEvent &event ), EventSignalCombiner<bool>>;
		/// The signal triggered by a button press event.
		ButtonSignal &buttonPressSignal();
		/// The signal triggered by a button release event.
		ButtonSignal &buttonReleaseSignal();
		/// The signal triggered by a button double click event.
		ButtonSignal &buttonDoubleClickSignal();
		/// The signal triggered by the mouse wheel.
		ButtonSignal &wheelSignal();

		using EnterLeaveSignal = Gaffer::Signals::Signal<void ( Gadget *, const ButtonEvent &event ), Gaffer::Signals::CatchingCombiner<void>>;
		/// The signal triggered when the mouse enters the Gadget.
		EnterLeaveSignal &enterSignal();
		/// The signal triggered when the mouse leaves the Gadget.
		EnterLeaveSignal &leaveSignal();
		/// A signal emitted whenever the mouse moves within a Gadget.
		ButtonSignal &mouseMoveSignal();

		using DragBeginSignal = Gaffer::Signals::Signal<IECore::RunTimeTypedPtr ( Gadget *, const DragDropEvent &event ), EventSignalCombiner<IECore::RunTimeTypedPtr>>;
		using DragDropSignal = Gaffer::Signals::Signal<bool ( Gadget *, const DragDropEvent &event ), EventSignalCombiner<bool>>;

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
		using KeySignal = Gaffer::Signals::Signal<bool ( Gadget *, const KeyEvent &key ), EventSignalCombiner<bool>>;
		/// The signal triggered by a key press event.
		KeySignal &keyPressSignal();
		/// The signal triggered by a key release event.
		KeySignal &keyReleaseSignal();

		/// A signal emitted when the host event loop is idle. Connections
		/// to this should be limited in duration because idle events consume
		/// CPU when the program would otherwise be inactive.
		using IdleSignal = Gaffer::Signals::Signal<void (), Gaffer::Signals::CatchingCombiner<void>>;
		static IdleSignal &idleSignal();
		//@}

	protected :

		enum class DirtyType
		{
			/// A re-render is needed, but the bounding box
			/// and layout remain the same.
			Render,
			/// The result of renderBound() has changed, but the layout bounds have not.
			/// Internal render caches which depend on the render bounds need to be rebuilt,
			/// but we don't need to re-layout
			RenderBound,
			/// The layout bounding box has changed. Implies RenderBound and Render.
			Bound,
			/// Parameters used by `updateLayout()` have changed.
			/// Implies Bound, RenderBound and Render.
			Layout,
		};


		/// Must be called by derived classes to reflect changes
		/// affecting `renderLayer()`, `bound()` or `updateLayout().
		void dirty( DirtyType dirtyType );

		/// May be implemented by derived classes to position child widgets.
		/// This is called automatically prior to rendering or bound computation.
		virtual void updateLayout() const;

		enum class RenderReason
		{
			Draw,       // A render that will display to the screen
			Select,     // A render to determine what Gadget the cursor is over
			DragSelect, // A render to determine what Gadget a drag is over
		};

		inline static bool isSelectionRender( RenderReason reason )
		{
			return reason == RenderReason::Select || reason == RenderReason::DragSelect;
		}

		/// Should be implemented by subclasses to draw themselves as appropriate
		/// for the specified layer. Child gadgets will be drawn automatically
		/// _after_ the parent gadget has been drawn.  Whenever overriding this,
		/// you must override layerMask and renderBound() as well.
		virtual void renderLayer( Layer layer, const Style *style, RenderReason reason ) const;

		/// Returns a bitmask built from the flags in the Layer enum.
		/// Any subclass which implements renderLayer must also implement layerMask
		/// to indicate which layers renderLayer should be called for.
		/// layerMask must currently return a constant value.  In the future, we
		/// may implement a new DirtyType to allow dirtying the layerMask
		virtual unsigned layerMask() const;

		/// The bound of everything drawn by renderLayer
		virtual Imath::Box3f renderBound() const;

		/// Implemented to dirty the layout for both the old and the new parent.
		void parentChanged( GraphComponent *oldParent ) override;

	private :
		void styleChanged();
		void emitDescendantVisibilityChanged();

		ConstStylePtr m_style;
		Gaffer::Signals::ScopedConnection m_styleChangedConnection;

		bool m_visible;
		bool m_enabled;
		bool m_highlighted;

		Imath::M44f m_transform;

		mutable Imath::Box3f m_bound;
		mutable bool m_layoutDirty;

		IECore::InternedString m_toolTip;

		struct MemberSignals;
		MemberSignals *signals();
		std::unique_ptr<MemberSignals> m_signals;

		// used by the bindings to know when the idleSignal()
		// has been accessed, and only use an idle timer
		// when absolutely necessary (when slots are connected).
		static IdleSignal &idleSignalAccessedSignal();
		friend void GafferUIModule::bindGadget();

		/// ViewportGadget performs the actual rendering, and needs access to the internals of all the gadgets it renders
		friend ViewportGadget;

};


/// Allow for clients to succinctly write bitmasks as Back | Main | Front
inline unsigned operator| ( Gadget::Layer a, Gadget::Layer b )
{
	return (unsigned)a | (unsigned)b;
}

inline unsigned operator| ( unsigned a, Gadget::Layer b )
{
	return a | (unsigned)b;
}

} // namespace GafferUI
