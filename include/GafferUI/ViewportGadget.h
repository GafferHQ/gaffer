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

#pragma once

#include "GafferUI/IndividualContainer.h"

#include "IECoreGL/Selector.h"
#include "IECoreGL/Shader.h"

#include "IECoreScene/Camera.h"

#include <array>
#include <chrono>

namespace GafferUI
{

/// Provides a viewport through which to view and interact with Gadgets - typically this
/// will be the top level Gadget in any hierarchy. The ViewportGadget is typically hosted
/// within a Widget UI via a GadgetWidget, and forwards all event signals it receives to
/// its child gadgets, transforming the event from the 2D space of the widget to the 3D
/// space of the gadget as it goes. The framing of the child gadgets is specified using a
/// Camera, which may be specified both programatically and through user interaction.
class GAFFERUI_API ViewportGadget : public Gadget
{

	public :

		using UnarySignal = Gaffer::Signals::Signal<void (ViewportGadget *), Gaffer::Signals::CatchingCombiner<void>>;

		explicit ViewportGadget( GadgetPtr primaryChild = nullptr );
		~ViewportGadget() override;

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( GafferUI::ViewportGadget, ViewportGadgetTypeId, Gadget );

		/// Accepts no parents - the ViewportGadget must always be the topmost Gadget.
		bool acceptsParent( const Gaffer::GraphComponent *potentialParent ) const override;
		std::string getToolTip( const IECore::LineSegment3f &position ) const override;

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

		/// Camera projection
		/// =================
		///
		/// The ViewportGadget uses a camera projection to draw Gadgets in the
		/// 2D space of the Viewport. It has two primary modes of operation,
		/// controlled by the `setPlanarMovement()` method. Use
		/// `setPlanarMovement( true )` for hosting gadgets that are inherently
		/// flat (e.g. GraphGadget) and `setPlanarMovement( false )` for hosting
		/// gadgets that are inherently 3-dimensional (e.g. SceneGadget).
		/// Below we will refer to these two modes as "2D camera" and "3D camera"
		/// respectively.
		///
		/// \todo This might all be much clearer if we had separate 2DViewport
		/// and 3DViewport subclasses.

		/// Common methods
		/// --------------
		///
		/// These methods are relevant to both 2D and 3D camera modes.

		/// If the camera is editable, the user can move it around using
		/// Alt+drag. The camera is editable by default.
		void setCameraEditable( bool editable );
		bool getCameraEditable() const;

		/// Sets whether the Viewport supports precise motion mode via modifier
		/// keys.
		/// > Note : This defaults to `true`, and causes the viewport to
		/// > consume button press events using the corresponding modifiers.
		void setPreciseMotionAllowed( bool allowed );
		/// Return whether the viewport currently allows precise motion.
		bool getPreciseMotionAllowed() const;

		/// Modifies the camera so that the specified box is in view.
		void frame( const Imath::Box3f &box );

		/// Determines if the viewport is in 2D camera mode (`planarMovement==true`)
		/// or 3D camera mode (`planarMovement==false`).
		void setPlanarMovement( bool planarMovement );
		/// Return whether the viewport is currently in planar movement mode
		bool getPlanarMovement() const;

		/// 2D camera methods
		/// -----------------
		///
		/// These methods should be used with `setPlanarMovement( true )`.

		// The max planar zoom is the maximum size in viewport pixels that a
		// unit distance can be expanded to. Used to avoid zooming in so close
		// that the gadgets don't make any sense.
		void setMaxPlanarZoom( const Imath::V2f &scale );
		Imath::V2f getMaxPlanarZoom() const;
		/// \todo Remove.
		Imath::V2f getMaxPlanarZoom();

		/// When drag tracking is enabled, the camera will automatically
		/// move to follow drags that would otherwise be exiting the viewport.
		enum DragTracking
		{
			NoDragTracking = 0,
			XDragTracking = 1,
			YDragTracking = 2
		};

		void setDragTracking( unsigned dragTracking );
		unsigned getDragTracking() const;

		/// When variable aspect zoom is enabled, the two axes can be scaled
		/// independently when performing a 2D zoom.
		void setVariableAspectZoom( bool variableAspectZoom );
		bool getVariableAspectZoom() const;

		/// 3D camera methods
		/// -----------------
		///
		/// These methods should be used with `setPlanarMovement( false )`.

		/// Return the camera currently used to render the viewport.
		/// This bakes in aperture and clipping planes based on tweaks
		/// made using the ViewportGadget.
		IECoreScene::ConstCameraPtr getCamera() const;
		/// A copy is taken.
		void setCamera( IECoreScene::CameraPtr camera );

		/// Sets the transform that positions the camera in world space.
		/// > Note : Scale and shear is removed from the camera
		/// > matrix to prevent unstable interaction.
		void setCameraTransform( const Imath::M44f &transform );
		const Imath::M44f &getCameraTransform() const;

		/// The center of interest is the depth (in camera space)
		/// of a pivot about which the Alt+drag camera motion operates.
		void setCenterOfInterest( float centerOfInterest );
		float getCenterOfInterest() const;
		/// \todo Remove.
		float getCenterOfInterest();

		enum class CameraFlags
		{
			None = 0,
			Camera = 1,
			Transform = 2,
			CenterOfInterest = 4,
			All = Camera | Transform | CenterOfInterest
		};

		using CameraChangedSignal = Gaffer::Signals::Signal<void ( ViewportGadget *, CameraFlags ), Gaffer::Signals::CatchingCombiner<void>>;
		/// A signal emitted when the camera is changed, either via the API or
		/// through user interaction. The CameraFlags bitmask is used to specify
		/// what aspects of the camera changed.
		CameraChangedSignal &cameraChangedSignal();

		/// If tumbling is enabled, the user can rotate the camera
		/// freely using Alt+left-drag.
		void setTumblingEnabled( bool tumblingEnabled );
		bool getTumblingEnabled() const;

		/// If dollying is enabled (and `getCameraEditable()` is true), the user
		/// can move the camera forwards and backwards using Alt+right-drag or
		/// the mouse wheel.
		/// > Note : Orthographic cameras are "dollied" by adjusting the aperture
		/// > rather than moving the camera.
		void setDollyingEnabled( bool dollyingEnabled );
		bool getDollyingEnabled() const;

		/// Moves the camera to view the box using the specified view direction.
		void frame( const Imath::Box3f &box, const Imath::V3f &viewDirection,
			const Imath::V3f &upVector = Imath::V3f( 0, 1, 0 ) );

		void fitClippingPlanes( const Imath::Box3f &box );

		/// Projection
		/// ==========
		///
		/// These methods provide conversions between the viewport's 2D raster space
		/// and the 3D space that Gadgets live in.

		IECore::LineSegment3f rasterToGadgetSpace( const Imath::V2f &rasterPosition, const Gadget *gadget ) const;
		Imath::V2f gadgetToRasterSpace( const Imath::V3f &gadgetPosition, const Gadget *gadget ) const;

		IECore::LineSegment3f rasterToWorldSpace( const Imath::V2f &rasterPosition ) const;
		Imath::V2f worldToRasterSpace( const Imath::V3f &worldPosition ) const;

		/// Rendering
		/// =========

		/// Sets the resolution (in pixels) of the area that will be rendered
		/// into. Should be called by hosts such as GadgetWidget.
		void setViewport( const Imath::V2i &viewport );
		const Imath::V2i &getViewport() const;
		/// A signal emitted when the viewport is changed by
		/// a call to setViewport().
		UnarySignal &viewportChangedSignal();

		/// Emitted by the viewport when a render is needed to a reflect a
		/// change in its state. Hosts such as GadgetWidget are then responsible
		/// for calling `render()` at an appropriate time.
		UnarySignal &renderRequestSignal();

		/// Renders the children of the viewport into the current OpenGL context.
		void render() const;

		/// A signal emitted just prior to rendering the viewport each time. This
		/// provides an opportunity for clients to make last minute adjustments to
		/// the viewport or its children.
		UnarySignal &preRenderSignal();

		/// The RasterScope class can be used to perform drawing in raster space.
		class GAFFERUI_API RasterScope : boost::noncopyable
		{

			public :

				RasterScope( const ViewportGadget *viewportGadget );
				~RasterScope();

		};

		/// A post processing shader can be used to process all the pixels for a
		/// specific layer as they are transferred to the screen. The main use
		/// case for this is applying a color transform, but other uses are
		/// possible.
		///
		/// The `postProcessShader` must have the following interface :
		///
		/// ```
		/// // Texture containing the layer to be drawn to the screen.
		/// uniform sampler2D framebufferTexture;
		/// // To be passed directly to `gl_Position`
		/// in vec3 vertexP;
		/// // Coordinates to be used to access `framebufferTexture`
		/// in vec2 vertexuv;
		/// ```
		void setPostProcessShader( Layer layer, const IECoreGL::Shader::ConstSetupPtr &postProcessShader );
		IECoreGL::Shader::ConstSetupPtr getPostProcessShader( Layer layer ) const;

		/// Selection
		/// =========
		///
		/// These methods and classes are used to query what Gadgets are visible
		/// in particular region of the viewport.

		/// Fills the passed vector with all the Gadgets below the specified position.
		/// The first Gadget in the list will be the frontmost, determined either by the
		/// depth buffer if it exists or the drawing order if it doesn't.
		/// \todo Would it be more convenient for this and the space conversion functions below
		/// to use V3fs?
		std::vector<Gadget*> gadgetsAt( const Imath::V2f &rasterPosition ) const;
		/// A more flexible form of the above, this allows specifying a region to test instead of a point,
		/// and optionally accepts filterLayer - if set, only Gadgets in this layer will be rendered
		std::vector<Gadget*> gadgetsAt( const Imath::Box2f &rasterRegion, Layer filterLayer = Layer::None ) const;

		/// The SelectionScope class can be used by child Gadgets to perform
		/// OpenGL selection from event signal callbacks.
		class GAFFERUI_API SelectionScope : boost::noncopyable
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
				SelectionScope( const ViewportGadget *viewportGadget, const Imath::Box2f &rasterRegion, std::vector<IECoreGL::HitRecord> &selection, IECoreGL::Selector::Mode mode );
				friend class ViewportGadget;

				void begin( const ViewportGadget *viewportGadget, const Imath::V2f &rasterPosition, const Imath::M44f &transform, IECoreGL::Selector::Mode mode );
				void begin( const ViewportGadget *viewportGadget, const Imath::Box2f &rasterRegion, const Imath::M44f &transform, IECoreGL::Selector::Mode mode );
				void end();

				bool m_depthSort;
				using SelectorPtr = std::unique_ptr<IECoreGL::Selector>;
				SelectorPtr m_selector;
				std::vector<IECoreGL::HitRecord> &m_selection;

		};

	private :

		// Called by `Gadget::dirty()` to notify ViewportGadget of changes
		// that may affect the rendering it is responsible for.
		void childDirtied( DirtyType dirtyType );

		friend class Gadget;

		struct RenderItem
		{
			const Gadget *gadget;
			const Style *style;
			const Imath::M44f transform;
			const Imath::Box3f bound;
			const unsigned layerMask;
		};
		mutable std::vector<RenderItem> m_renderItems;

		static void getRenderItems( const Gadget *gadget,  Imath::M44f transform, const Style *parentStyle, std::vector<RenderItem> &renderItems );

		void renderInternal( RenderReason reason, Layer filterLayer = Layer::None ) const;
		void renderLayerInternal( RenderReason reason, Layer layer, const Imath::M44f &viewTransform, const Imath::Box3f &bound, IECoreGL::Selector *selector ) const;
		GLuint acquireFramebuffer() const;

		void childRemoved( GraphComponent *parent, GraphComponent *child );

		bool buttonPress( GadgetPtr gadget, const ButtonEvent &event );
		bool buttonRelease( GadgetPtr gadget, const ButtonEvent &event );
		bool buttonDoubleClick( GadgetPtr gadget, const ButtonEvent &event );
		void enter( const ButtonEvent &event );
		void leave( const ButtonEvent &event );
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

		// If dragging is true, then the gadgets will be tested in DragSelect mode.
		std::vector<Gadget*> gadgetsAtInternal( const Imath::V2f &rasterPosition, bool dragging ) const;
		std::vector<Gadget*> gadgetsAtInternal( const Imath::Box2f &rasterRegion, Layer filterLayer, bool dragging ) const;

		void updateGadgetUnderMouse( const ButtonEvent &event );
		void emitEnterLeaveEvents( GadgetPtr newGadgetUnderMouse, GadgetPtr oldGadgetUnderMouse, const ButtonEvent &event );

		void updateMotionState( const ButtonEvent &event, bool initialEvent = false );
		Imath::V2f motionPositionFromEvent( const ButtonEvent &event ) const;

		Gadget* updatedDragDestination( std::vector<Gadget*> &gadgets, const DragDropEvent &event );

		void trackDrag( const DragDropEvent &event );
		void trackDragIdle();

		template<typename Event, typename Signal>
		typename Signal::result_type dispatchEvent( std::vector<Gadget*> &gadgets, Signal &(Gadget::*signalGetter)(), const Event &event, Gadget* &handler );

		template<typename Event, typename Signal>
		typename Signal::result_type dispatchEvent( Gadget* gadget, Signal &(Gadget::*signalGetter)(), const Event &event );

		class CameraController;
		std::unique_ptr<CameraController> m_cameraController;
		bool m_cameraInMotion;
		bool m_cameraEditable;

		bool m_preciseMotionAllowed;
		bool m_preciseMotionEnabled;
		Imath::V2f m_motionSegmentOrigin;
		Imath::V2f m_motionSegmentEventOrigin;

		GadgetPtr m_lastButtonPressGadget;
		GadgetPtr m_previousClickGadget;
		GadgetPtr m_gadgetUnderMouse;

		unsigned m_dragTracking;
		Gaffer::Signals::Connection m_dragTrackingIdleConnection;
		DragDropEvent m_dragTrackingEvent;
		float m_dragTrackingThreshold;
		Imath::V2f m_dragTrackingVelocity;
		std::chrono::steady_clock::time_point m_dragTrackingTime;

		bool m_variableAspectZoom;

		ButtonEvent::Buttons m_dragButton;
		bool m_cameraMotionDuringDrag;

		UnarySignal m_viewportChangedSignal;
		CameraChangedSignal m_cameraChangedSignal;
		UnarySignal m_preRenderSignal;
		UnarySignal m_renderRequestSignal;

		// Framebuffer used for intermediate renders before
		// transferring to the output framebuffer using the
		// post-process shaders.
		mutable GLuint m_framebuffer;
		mutable Imath::V2i m_framebufferSize;
		mutable GLuint m_colorBuffer;
		mutable GLuint m_depthBuffer;
		mutable GLuint m_downsampledFramebuffer;
		mutable GLuint m_downsampledFramebufferTexture;

		struct PostProcessShader
		{
			PostProcessShader() = default;
			PostProcessShader( const IECoreGL::Shader::ConstSetupPtr &setup );
			IECoreGL::Shader::ConstSetupPtr setup;
			const IECoreGL::Shader::Parameter *textureParameter = nullptr;
			const IECoreGL::Shader::Parameter *pParameter = nullptr;
			const IECoreGL::Shader::Parameter *uvParameter = nullptr;
			static const PostProcessShader *defaultPostProcessShader();
		};

		// PostProcessShaders for each individual layer.
		std::array<PostProcessShader, 6> m_postProcessShaders;

		static PostProcessShader *defaultPostProcessShader();

};

IE_CORE_DECLAREPTR( ViewportGadget );

/// Bitwise operators for CameraFlags
/// \todo Perhaps it's time we introduced a standard way of implementing bitmask enums. Currently I'm
/// favouring simple operators over a separate `template class Flags<Enum>`.
inline ViewportGadget::CameraFlags operator| ( ViewportGadget::CameraFlags a, ViewportGadget::CameraFlags b )
{
	using Underlying = std::underlying_type_t<ViewportGadget::CameraFlags>;
	return static_cast<ViewportGadget::CameraFlags>( static_cast<Underlying>( a ) | static_cast<Underlying>( b ) );
}

inline ViewportGadget::CameraFlags operator& ( ViewportGadget::CameraFlags a, ViewportGadget::CameraFlags b )
{
	using Underlying = std::underlying_type_t<ViewportGadget::CameraFlags>;
	return static_cast<ViewportGadget::CameraFlags>( static_cast<Underlying>( a ) & static_cast<Underlying>( b ) );
}

inline ViewportGadget::CameraFlags operator|= ( ViewportGadget::CameraFlags &a, ViewportGadget::CameraFlags b )
{
	return a = a | b;
}

} // namespace GafferUI
