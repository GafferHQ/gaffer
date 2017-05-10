//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERUI_RENDERABLEGADGET_H
#define GAFFERUI_RENDERABLEGADGET_H

#include "IECore/VisibleRenderable.h"

#include "GafferUI/Export.h"
#include "GafferUI/Gadget.h"

namespace IECoreGL
{

IE_CORE_FORWARDDECLARE( Scene )
IE_CORE_FORWARDDECLARE( State )
IE_CORE_FORWARDDECLARE( Group )
IE_CORE_FORWARDDECLARE( StateComponent )

} // namespace IECoreGL

namespace GafferUI
{

IE_CORE_FORWARDDECLARE( RenderableGadget );

/// \todo Either remove this or move it to GafferCortexUI.
class GAFFERUI_API RenderableGadget : public Gadget
{

	public :

		RenderableGadget( IECore::VisibleRenderablePtr renderable = 0 );
		virtual ~RenderableGadget();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferUI::RenderableGadget, RenderableGadgetTypeId, Gadget );

		virtual Imath::Box3f bound() const;

		void setRenderable( IECore::ConstVisibleRenderablePtr renderable );
		IECore::ConstVisibleRenderablePtr getRenderable() const;

		/// Returns the IECoreGL::State object used as the base display
		/// style for the Renderable. This may be modified freely to
		/// change the display style.
		IECoreGL::State *baseState();

		/// Returns the name of the frontmost object intersecting the specified line
		/// through gadget space, or "" if there is no such object.
		std::string objectAt( const IECore::LineSegment3f &lineInGadgetSpace ) const;
		/// Fills objectNames with all objects intersected by a rectangle in screen space,
		/// defined by two corners in gadget space (as required for drag selection).
		size_t objectsAt(
			const Imath::V3f &corner0InGadgetSpace,
			const Imath::V3f &corner1InGadgetSpace,
			std::vector<std::string> &objectNames
		) const;

		/// @name Selection
		/// The RenderableGadget maintains a set of selected object, based
		/// on object name. The user can manipulate the selection with the
		/// mouse, and the selected objects are drawn in a highlighted fashion.
		/// The selection may be queried and set programatically, and the
		/// SelectionChangedSignal can be used to provide notifications of
		/// such changes.
		////////////////////////////////////////////////////////////////////
		//@{
		/// The selection is simply stored as a set of object names.
		typedef std::set<std::string> Selection;
		/// Returns the selection.
		Selection &getSelection();
		const Selection &getSelection() const;
		/// Sets the selection, triggering selectionChangedSignal() if
		/// necessary.
		void setSelection( const std::set<std::string> &selection );
		/// A signal emitted when the selection has changed, either through
		/// a call to setSelection() or through user action.
		typedef boost::signal<void ( RenderableGadgetPtr )> SelectionChangedSignal;
		SelectionChangedSignal &selectionChangedSignal();
		/// Returns the bounding box of all the selected objects.
		Imath::Box3f selectionBound() const;
		//@}

		/// Implemented to return the name of the object under the mouse as
		/// a tooltip.
		virtual std::string getToolTip( const IECore::LineSegment3f &line ) const;

	protected :

		virtual void doRender( const Style *style ) const;

	private :

		bool buttonPress( GadgetPtr gadget, const ButtonEvent &event );
		IECore::RunTimeTypedPtr dragBegin( GadgetPtr gadget, const DragDropEvent &event );
		bool dragEnter( GadgetPtr gadget, const DragDropEvent &event );
		bool dragMove( GadgetPtr gadget, const DragDropEvent &event );
		bool dragEnd( GadgetPtr gadget, const DragDropEvent &event );

		void applySelection( IECoreGL::Group *group = 0 );
		Imath::Box3f selectionBound( IECoreGL::Group *group ) const;

		IECore::ConstVisibleRenderablePtr m_renderable;
		IECoreGL::ScenePtr m_scene;
		IECoreGL::StatePtr m_baseState;
		IECoreGL::StateComponentPtr m_selectionColor;
		IECoreGL::StateComponentPtr m_wireframeOn;

		Selection m_selection;
		SelectionChangedSignal m_selectionChangedSignal;

		Imath::V3f m_dragStartPosition;
		Imath::V3f m_lastDragPosition;
		bool m_dragSelecting;

};

typedef Gaffer::FilteredChildIterator<Gaffer::TypePredicate<RenderableGadget> > RenderableGadgetIterator;
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::TypePredicate<RenderableGadget> > RecursiveRenderableGadgetIterator;

} // namespace GafferUI

#endif // GAFFERUI_RenderableGadget_H
