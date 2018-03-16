//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012-2014, John Haddon. All rights reserved.
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERUI_VIEWPORTGADGET_H
#define GAFFERUI_VIEWPORTGADGET_H

#include "IECore/Camera.h"
#include "IECore/CameraController.h"

#include "IECoreGL/Selector.h"

#include "GafferUI/IndividualContainer.h"

namespace GafferUI
{

/// Provides a viewport through which to view and interact with Gadgets - typically this
/// will be the top level Gadget in any hierarchy. The ViewportGadget is typically hosted
/// within a Widget UI via a GadgetWidget, and forwards all event signals it receives to
/// its child gadgets, transforming the event from the 2d space of the widget to the 3d
/// space of the gadget as it goes. The framing of the child gadgets is specified using a
/// Camera, which may be specified both programatically and through user interaction.
class ViewportGadget : public Gadget
{

	public :

		typedef boost::signal<void (ViewportGadget *)> UnarySignal;

		ViewportGadget( GadgetPtr primaryChild = NULL );
		virtual ~ViewportGadget();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferUI::ViewportGadget, ViewportGadgetTypeId, Gadget );

		/// Accepts no parents - the ViewportGadget must always be the topmost Gadget.
		virtual bool acceptsParent( const Gaffer::GraphComponent *potentialParent ) const;
		virtual std::string getToolTip( const IECore::LineSegment3f &position ) const;

		/// Typically mouse event signals are emitted for the gadget under
		/// the mouse, but in the case that there is no such gadget, they
		/// are emitted on the primary child. The primary child is currently
		/// also the only gadget to have key press/release signals emitted on
		/// it.
		/// \todo It might be nice in future to remove this concept and to have
		/// all children treated equally - at present we need the concept so that
		/// the node graph and viewer can use clicks in empty space to perform selection,
		/// but there may be other ways of achieving that.
		void setPrimaryChild( GadgetPtr gadget );
		Gadget *getPrimaryChild();
		const Gadget *getPrimaryChild() const;

		const Imath::V2i &getViewport() const;
		void setViewport( const Imath::V2i &viewport );
		/// A signal emitted when the viewport is changed by
		/// a call to setViewport().
		UnarySignal &viewportChangedSignal();

		const IECore::Camera *getCamera() const;
		/// A copy is taken.
		void setCamera( const IECore::Camera *camera );
		/// A signal emitted when the camera is changed, either by
		/// a setCamera() call or through user interaction.
		UnarySignal &cameraChangedSignal();

		/// If the camera is editable, the user can move it around
		/// using Alt+drag. The camera is editable by default.
		bool getCameraEditable() const;
		void setCameraEditable( bool editable );

		void frame( const Imath::Box3f &box );
		void frame( const Imath::Box3f &box, const Imath::V3f &viewDirection,
			const Imath::V3f &upVector = Imath::V3f( 0, 1, 0 ) );

		void fitClippingPlanes( const Imath::Box3f &box );

		/// When drag tracking is enabled, the camera will automatically
		/// move to follow drags that would otherwise be exiting the viewport.
		void setDragTracking( bool dragTracking );
		bool getDragTracking() const;

		/// Fills the passed vector with all the Gadgets below the specified position.
		/// The first Gadget in the list will be the frontmost, determined either by the
		/// depth buffer if it exists or the drawing order if it doesn't.
		/// \todo Would it be more convenient for this and the space conversion functions below
		/// to use V3fs?
		void gadgetsAt( const Imath::V2f &rasterPosition, std::vector<GadgetPtr> &gadgets ) const;

		IECore::LineSegment3f rasterToGadgetSpace( const Imath::V2f &rasterPosition, const Gadget *gadget ) const;
		Imath::V2f gadgetToRasterSpace( const Imath::V3f &gadgetPosition, const Gadget *gadget ) const;

		IECore::LineSegment3f rasterToWorldSpace( const Imath::V2f &rasterPosition ) const;
		Imath::V2f worldToRasterSpace( const Imath::V3f &worldPosition ) const;

		/// The SelectionScope class can be used by child Gadgets to perform
		/// OpenGL selection from event signal callbacks.
		class SelectionScope
		{

			public :

				/// Start an OpenGL selection operation for the specified position in the specified gadget. After construction,
				/// perform drawing as usual in the object space of the Gadget, and upon destruction the selection
				/// vector will have been filled with the specified hits.
				SelectionScope(
					const IECore::LineSegment3f &lineInGadgetSpace, const Gadget *gadget,
					std::vector<IECoreGL::HitRecord> &selection,
					IECoreGL::Selector::Mode mode = IECoreGL::Selector::GLSelect
				);
				/// As above, but selecting within a rectangle in screen space, defined by two corners in gadget space.
				SelectionScope(
					const Imath::V3f &corner0InGadgetSpace, const Imath::V3f &corner1InGadgetSpace, const Gadget *gadget,
					std::vector<IECoreGL::HitRecord> &selection,
					IECoreGL::Selector::Mode mode = IECoreGL::Selector::GLSelect
				);
				~SelectionScope();

				/// Returns the IECoreGL::State which should be used for rendering while selecting.
				IECoreGL::State *baseState();

			private :

				/// Private constructor for use by ViewportGadget.
				SelectionScope( const ViewportGadget *viewportGadget, const Imath::V2f &rasterPosition, std::vector<IECoreGL::HitRecord> &selection, IECoreGL::Selector::Mode mode );
				friend class ViewportGadget;

				void begin( const ViewportGadget *viewportGadget, const Imath::V2f &rasterPosition, const Imath::M44f &transform, IECoreGL::Selector::Mode mode );
				void begin( const ViewportGadget *viewportGadget, const Imath::Box2f &rasterRegion, const Imath::M44f &transform, IECoreGL::Selector::Mode mode );
				void end();

				bool m_depthSort;
				typedef boost::shared_ptr<IECoreGL::Selector> SelectorPtr;
				SelectorPtr m_selector;
				std::vector<IECoreGL::HitRecord> &m_selection;

		};

		/// The RasterScope class can be used to perform drawing in raster space.
		class RasterScope
		{

			public :

				RasterScope( const ViewportGadget *viewportGadget );
				~RasterScope();

		};

		/// A signal emitted just prior to rendering the viewport each time. This
		/// provides an opportunity for clients to make last minute adjustments to
		/// the viewport or its children.
		UnarySignal &preRenderSignal();

	protected :

		virtual void doRender( const Style *style ) const;

	private :

		void childRemoved( GraphComponent *parent, GraphComponent *child );

		bool buttonPress( GadgetPtr gadget, const ButtonEvent &event );
		bool buttonRelease( GadgetPtr gadget, const ButtonEvent &event );
		bool buttonDoubleClick( GadgetPtr gadget, const ButtonEvent &event );
		bool mouseMove( GadgetPtr gadget, const ButtonEvent &event );
		IECore::RunTimeTypedPtr dragBegin( GadgetPtr gadget, const DragDropEvent &event );
		bool dragEnter( GadgetPtr gadget, const DragDropEvent &event );
		bool dragMove( GadgetPtr gadget, const DragDropEvent &event );
		bool dragLeave( GadgetPtr gadget, const DragDropEvent &event );
		bool drop( GadgetPtr gadget, const DragDropEvent &event );
		bool dragEnd( GadgetPtr gadget, const DragDropEvent &event );
		bool wheel( GadgetPtr gadget, const ButtonEvent &event );
		bool keyPress( GadgetPtr gadget, const KeyEvent &event );
		bool keyRelease( GadgetPtr gadget, const KeyEvent &event );

		void eventToGadgetSpace( Event &event, Gadget *gadget );
		void eventToGadgetSpace( ButtonEvent &event, Gadget *gadget );

		void emitEnterLeaveEvents( GadgetPtr newGadgetUnderMouse, GadgetPtr oldGadgetUnderMouse, const ButtonEvent &event );

		GadgetPtr updatedDragDestination( std::vector<GadgetPtr> &gadgets, const DragDropEvent &event );

		void trackDrag( const DragDropEvent &event );
		void trackDragIdle();

		template<typename Event, typename Signal>
		typename Signal::result_type dispatchEvent( std::vector<GadgetPtr> &gadgets, Signal &(Gadget::*signalGetter)(), const Event &event, GadgetPtr &handler );

		template<typename Event, typename Signal>
		typename Signal::result_type dispatchEvent( GadgetPtr gadget, Signal &(Gadget::*signalGetter)(), const Event &event );

		IECore::CameraController m_cameraController;
		bool m_cameraInMotion;
		bool m_cameraEditable;

		GadgetPtr m_lastButtonPressGadget;
		GadgetPtr m_gadgetUnderMouse;

		bool m_dragTracking;
		boost::signals::connection m_dragTrackingIdleConnection;
		DragDropEvent m_dragTrackingEvent;
		float m_dragTrackingThreshold;
		Imath::V2f m_dragTrackingVelocity;
		double m_dragTrackingTime;

		UnarySignal m_viewportChangedSignal;
		UnarySignal m_cameraChangedSignal;
		UnarySignal m_preRenderSignal;

};

IE_CORE_DECLAREPTR( ViewportGadget );

} // namespace GafferUI

#endif // GAFFERUI_VIEWPORTGADGET_H
