//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "GafferUI/ViewportGadget.h"

#include "GafferUI/Style.h"
#include "GafferUI/Pointer.h"

#include "IECoreGL/Camera.h"
#include "IECoreGL/Selector.h"
#include "IECoreGL/State.h"
#include "IECoreGL/ToGLCameraConverter.h"

#include "IECoreScene/Transform.h"

#include "IECore/AngleConversion.h"
#include "IECore/MessageHandler.h"
#include "IECore/NullObject.h"
#include "IECore/SimpleTypedData.h"

#include "OpenEXR/ImathBoxAlgo.h"
#include "OpenEXR/ImathMatrixAlgo.h"

#include "boost/bind/bind.hpp"
#include "boost/bind/placeholders.hpp"

#include <chrono>
#include <cmath>

using namespace boost::placeholders;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreGL;
using namespace GafferUI;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

float ceilSignificantDigits( float x, int significantDigits )
{
	const int ceilLog10 = ceil( log10( x ) );
	const float magnitude = pow( 10, ceilLog10 - significantDigits );
	return ceil( x / magnitude ) * magnitude;
}

float floorSignificantDigits( float x, int significantDigits )
{
	const int ceilLog10 = ceil( log10( x ) );
	const float magnitude = pow( 10, ceilLog10 - significantDigits );
	return floor( x / magnitude ) * magnitude;
}

// This horrible function is just because theoretically someone could call
// setCamera while in planarMovement mode, requiring us to reverse engineer
// a planarScale based on the current resolution.  This is pretty useless,
// setting planarScale directly would be far more useful - but since the
// interface exists, we have to deal with someone potentially calling it.
V2f planarScaleFromCamera( const IECoreScene::Camera *cam )
{
	if( cam->getProjection() != "orthographic" )
	{
		return V2f( 1.0f );
	}

	return cam->getAperture() / V2f( cam->getResolution() );
}

M44f g_identityMatrix;

const Box3f initInfiniteBox()
{
	Box3f r;
	r.makeInfinite();
	return r;
}

Box3f g_infiniteBox( initInfiniteBox() );

} // namespace

//////////////////////////////////////////////////////////////////////////
// CameraController
//////////////////////////////////////////////////////////////////////////

class ViewportGadget::CameraController : public boost::noncopyable
{

	public :

		CameraController()
			:	m_planarMovement( true ), m_tumblingEnabled( true ), m_dollyingEnabled( true ),
				m_camera( new IECoreScene::Camera() ), m_maxPlanarZoom( 0.0f ), m_planarScale( 1.0f ),
				m_centerOfInterest( 1.0f )
		{
			// Force existence of parameter (see `getViewportResolution()`)
			m_camera->setResolution( m_camera->getResolution() );
		}

		void setCamera( IECoreScene::CameraPtr camera )
		{
			// Public API treats viewport resolution as independent of camera,
			// but we store it on the camera so must transfer it over.
			camera->setResolution( m_camera->getResolution() );
			if( m_planarMovement )
			{
				m_planarScale = planarScaleFromCamera( camera.get() );
			}
			m_camera = camera;
		}

		IECoreScene::ConstCameraPtr getCamera() const
		{
			if( m_planarMovement )
			{
				IECoreScene::CameraPtr viewportCamera = m_camera->copy();
				viewportCamera->setProjection( "orthographic" );
				viewportCamera->setAperture( m_planarScale * V2f( m_camera->getResolution() ) );
				return viewportCamera;
			}
			return m_camera;
		}

		void setPlanarMovement( bool planarMovement )
		{
			if( planarMovement && !m_planarMovement )
			{
				m_planarScale = planarScaleFromCamera( m_camera.get() );
			}
			m_planarMovement = planarMovement;
		}

		bool getPlanarMovement() const
		{
			return m_planarMovement;
		}

		void setTumblingEnabled( bool tumblingEnabled )
		{
			m_tumblingEnabled = tumblingEnabled;
		}

		bool getTumblingEnabled() const
		{
			return m_tumblingEnabled;
		}

		void setDollyingEnabled( bool dollyingEnabled )
		{
			m_dollyingEnabled = dollyingEnabled;
		}

		bool getDollyingEnabled() const
		{
			return m_dollyingEnabled;
		}

		void setTransform( const M44f &transform )
		{
			m_transform = transform;
		}

		const M44f &getTransform() const
		{
			return m_transform;
		}

		/// Positive.
		void setCenterOfInterest( float centerOfInterest )
		{
			m_centerOfInterest = centerOfInterest;
		}

		float getCenterOfInterest()
		{
			return m_centerOfInterest;
		}

		void setMaxPlanarZoom( const Imath::V2f &scale )
		{
			m_maxPlanarZoom = scale;
		}

		Imath::V2f getMaxPlanarZoom()
		{
			return m_maxPlanarZoom;
		}

		/// Set the resolution of the viewport we are working in
		void setViewportResolution( const Imath::V2i &viewportResolution )
		{
			m_camera->setResolution( viewportResolution );
		}

		const Imath::V2i &getViewportResolution() const
		{
			// Can't call `getResolution()` because we need to return a reference.
			return m_camera->parametersData()->member<V2iData>( "resolution" )->readable();
		}

		void setClippingPlanes( const Imath::V2f &clippingPlanes )
		{
			m_camera->setClippingPlanes( clippingPlanes );
		}

		const Imath::V2f getClippingPlanes() const
		{
			return m_camera->getClippingPlanes();
		}

		/// Moves the camera to frame the specified box, keeping the
		/// current viewing direction unchanged.
		void frame( const Imath::Box3f &box, bool variableAspectZoom = false )
		{
			V3f z( 0, 0, -1 );
			V3f y( 0, 1, 0 );
			M44f t = m_transform;
			t.multDirMatrix( z, z );
			t.multDirMatrix( y, y );
			frame( box, z, y, variableAspectZoom );
		}

		/// Moves the camera to frame the specified box, viewing it from the
		/// specified direction, and with the specified up vector.
		void frame( const Imath::Box3f &box, const Imath::V3f &viewDirection,
			const Imath::V3f &upVector = Imath::V3f( 0, 1, 0 ), bool variableAspectZoom = false )
		{
			// Make a matrix to center the camera on the box, with the appropriate view direction.
			M44f cameraMatrix = rotationMatrixWithUpDir( V3f( 0, 0, -1 ), viewDirection, upVector );
			M44f translationMatrix;
			translationMatrix.translate( box.center() );
			cameraMatrix *= translationMatrix;

			// Now translate the camera back until the box is completely visible. How
			// we do this exactly depends on the camera projection.
			M44f inverseCameraMatrix = cameraMatrix.inverse();
			Box3f cBox = transform( box, inverseCameraMatrix );

			if( m_planarMovement )
			{
				// Orthographic. Translate to front of box.
				// The 0.1 is just a fudge factor to ensure we don't accidentally clip
				// the front of the box.
				m_centerOfInterest = cBox.max.z + m_camera->getClippingPlanes()[0] + 0.1;

				// Adjust the planar scale so the entire bound can be seen.
				V2f ratio = V2f( cBox.size().x, cBox.size().y ) / V2f( m_camera->getResolution() );
				if( variableAspectZoom )
				{
					m_planarScale = ratio;
				}
				else
				{
					m_planarScale = V2f( std::max( ratio.x, ratio.y ) );
				}
			}
			else
			{
				if( m_camera->getProjection()=="perspective" )
				{
					// Perspective. leave the field of view and screen window as is and translate
					// back till the box is wholly visible. this currently assumes the screen window
					// is centered about the camera axis.
					const Box2f &normalizedScreenWindow = m_camera->frustum();
					// Compute a distance to push back in z in order to see the whole width and height of cBox
					float z0 = cBox.size().x / normalizedScreenWindow.size().x;
					float z1 = cBox.size().y / normalizedScreenWindow.size().y;

					m_centerOfInterest = std::max( z0, z1 ) + cBox.max.z + m_camera->getClippingPlanes()[0];
				}
				else
				{
					// Orthographic.

					// Translate to front of box.
					// We need to clamp the near clipping plane to >= 0.0f because
					// the LightToCamera node creates hugely negative near clipping
					// planes that would otherwise send us way out into space. The
					// 0.1 is just a fudge factor to ensure we don't accidentally clip
					// the front of the box.
					m_centerOfInterest = cBox.max.z + std::max( m_camera->getClippingPlanes()[0], 0.0f ) + 0.1;

					// The user might want to tumble around the thing
					// they framed. Translate back some more to make
					// room to tumble around the entire bound.
					if( getTumblingEnabled() )
					{
						m_centerOfInterest += cBox.size().length();
					}

					// If dollying is enabled, then we have permission to modify the
					// aperture. Adjust it so that we can see the whole bound.
					if( getDollyingEnabled() )
					{
						m_camera->setAperture( V2f( cBox.size().x, cBox.size().y ) );
					}
				}
			}

			cameraMatrix.translate( V3f( 0.0f, 0.0f, m_centerOfInterest ) );
			m_transform = cameraMatrix;

		}

		/// Computes the points on the near and far clipping planes that correspond
		/// with the specified raster position. Points are computed in world space.
		void unproject( const Imath::V2f rasterPosition, Imath::V3f &near, Imath::V3f &far ) const
		{
			const V2f clippingPlanes = m_camera->getClippingPlanes();
			if( m_planarMovement )
			{
				V2f rasterCenter = 0.5f * V2f( m_camera->getResolution() );
				V2f unscaled = ( rasterPosition - rasterCenter ) * m_planarScale;
				near = V3f( unscaled.x, -unscaled.y, -clippingPlanes[0] );
				far = V3f( unscaled.x, -unscaled.y, -clippingPlanes[1] );
			}
			else
			{
				V2f ndc = V2f( rasterPosition ) / V2f( m_camera->getResolution() );
				const Box2f &normalizedScreenWindow = m_camera->frustum();
				V2f screen(
					lerp( normalizedScreenWindow.min.x, normalizedScreenWindow.max.x, ndc.x ),
					lerp( normalizedScreenWindow.max.y, normalizedScreenWindow.min.y, ndc.y )
				);

				if( m_camera->getProjection()=="perspective" )
				{
					V3f camera( screen.x, screen.y, -1.0f );
					near = camera * clippingPlanes[0];
					far = camera * clippingPlanes[1];
				}
				else
				{
					near = V3f( screen.x, screen.y, -clippingPlanes[0] );
					far = V3f( screen.x, screen.y, -clippingPlanes[1] );
				}
			}

			near = near * m_transform;
			far = far * m_transform;
		}

		/// Projects the point in world space into a raster space position.
		Imath::V2f project( const Imath::V3f &worldPosition ) const
		{
			M44f inverseCameraMatrix = m_transform.inverse();
			V3f cameraPosition = worldPosition * inverseCameraMatrix;

			if( m_planarMovement )
			{
				V2f rasterCenter = 0.5f * V2f( getViewportResolution() );
				return rasterCenter + V2f( cameraPosition.x, -cameraPosition.y ) / m_planarScale;
			}
			else
			{
				const V2i resolution = getViewportResolution();
				const Box2f &normalizedScreenWindow = m_camera->frustum();
				if( m_camera->getProjection() == "perspective" )
				{
					cameraPosition = cameraPosition / -cameraPosition.z;
				}

				V2f ndcPosition(
					lerpfactor( cameraPosition.x, normalizedScreenWindow.min.x, normalizedScreenWindow.max.x ),
					lerpfactor( cameraPosition.y, normalizedScreenWindow.max.y, normalizedScreenWindow.min.y )
				);
				return V2f(
					ndcPosition.x * resolution.x,
					ndcPosition.y * resolution.y
				);
			}
		}

		/// Motion
		/// ======
		///
		/// These functions facilitate the implementation of maya style
		/// camera movement controls within a UI. All coordinates passed
		/// are mouse coordinates in raster space (0,0 at top left).

		enum MotionType
		{
			None,
			Track,
			Tumble,
			Dolly,
		};

		enum class ZoomAxis
		{
			Undefined,
			X,
			Y
		};

		/// Starts a motion of the specified type.
		void motionStart( MotionType motion, const Imath::V2f &startPosition )
		{
			if( motion == Tumble && m_planarMovement )
			{
				motion = Track;
			}

			m_motionType = motion;
			m_motionStart = startPosition;
			m_motionMatrix = m_transform;
			m_motionPlanarScale = m_planarScale;
			m_motionCenterOfInterest = m_centerOfInterest;
			m_motionOrthoAperture = m_camera->getAperture();
		}

		/// Updates the camera position based on a changed mouse position. Can only
		/// be called after motionStart() and before motionEnd().
		void motionUpdate( const Imath::V2f &newPosition, bool variableAspect = false )
		{
			switch( m_motionType )
			{
				case Track :
					track( newPosition );
					break;
				case Tumble :
					tumble( newPosition );
					break;
				case Dolly :
					dolly( newPosition, variableAspect );
					break;
				default :
					throw Exception( "CameraController not in motion." );
			}
		}

		/// End the current motion, ready to call motionStart() again if required.
		void motionEnd( const Imath::V2f &endPosition, bool variableAspect = false )
		{
			switch( m_motionType )
			{
				case Track :
					track( endPosition );
					break;
				case Tumble :
					tumble( endPosition );
					break;
				case Dolly :
					dolly( endPosition, variableAspect );
					break;
				default :
					break;
			}
			m_motionType = None;
			m_zoomAxis = ZoomAxis::Undefined;
			Pointer::setCurrent( "" );
		}

		/// Determine the type of motion based on current events
		/// \todo: The original separation of responsibilities was that
		/// CameraController knew how to perform camera movement, and
		/// ViewportGadgets knew how to handle events, and decided how to map
		/// those to camera movement requests. This breaks that original
		/// separation. Full separation would mean that the CameraController
		/// made its own connections to buttonPressSignal/dragBeginSignal etc,
		/// "stealing" any events it wanted before they were processed by the
		/// ViewportGadget. There are a few complications regarding drag
		/// tracking and unmodified MMB drags, though.
		MotionType cameraMotionType( const ButtonEvent &event, bool variableAspectZoom, bool preciseMotionAllowed )
		{
			if(
				( ( event.modifiers == ModifiableEvent::Alt ) || ( preciseMotionAllowed && ( event.modifiers == ModifiableEvent::ShiftAlt ) ) ) ||
				( event.buttons == ButtonEvent::Middle && ( event.modifiers == ModifiableEvent::None || ( preciseMotionAllowed && ( event.modifiers == ModifiableEvent::Shift ) ) ) ) ||
				( variableAspectZoom && event.modifiers & ModifiableEvent::Alt && event.modifiers & ModifiableEvent::Control && event.buttons == ButtonEvent::Right )
			)
			{
				switch( event.buttons )
				{
					case ButtonEvent::Left :
						return ViewportGadget::CameraController::Tumble;
					case ButtonEvent::Middle :
						return CameraController::Track;
					case ButtonEvent::Right :
						return CameraController::Dolly;
					default :
						return CameraController::None;
				}
			}

			return CameraController::None;
		}

	private:

		void track( const Imath::V2f &p )
		{
			V2f d = p - m_motionStart;

			V3f translate( 0.0f );
			if( m_planarMovement )
			{
				translate = V3f( -d[0] * m_planarScale[0], d[1] * m_planarScale[1], 0.0f );
			}
			else
			{
				const V2i resolution = getViewportResolution();
				const Box2f &normalizedScreenWindow = m_camera->frustum();

				translate.x = -normalizedScreenWindow.size().x * d.x/(float)resolution.x;
				translate.y = normalizedScreenWindow.size().y * d.y/(float)resolution.y;
				if( m_camera->getProjection()=="perspective" )
				{
					translate *= m_centerOfInterest;
				}
			}
			M44f t = m_motionMatrix;
			t.translate( translate );
			m_transform = t;
		}

		void tumble( const Imath::V2f &p )
		{
			if( !m_tumblingEnabled )
			{
				return;
			}

			V2f d = p - m_motionStart;

			V3f centerOfInterestInWorld = V3f( 0, 0, -m_centerOfInterest ) * m_motionMatrix;
			V3f xAxisInWorld = V3f( 1, 0, 0 );
			m_motionMatrix.multDirMatrix( xAxisInWorld, xAxisInWorld );
			xAxisInWorld.normalize();

			M44f t;
			t.translate( centerOfInterestInWorld );

				t.rotate( V3f( 0, -d.x / 100.0f, 0 ) );

				M44f xRotate;
				xRotate.setAxisAngle( xAxisInWorld, -d.y / 100.0f );

				t = xRotate * t;

			t.translate( -centerOfInterestInWorld );

			m_transform = m_motionMatrix * t;
		}

		void dolly( const Imath::V2f &p, bool variableAspect )
		{
			if( !m_dollyingEnabled )
			{
				return;
			}

			const V2i resolution = m_camera->getResolution();
			V2f dv = V2f( (p - m_motionStart) ) / resolution;
			float d = dv.x - dv.y;

			if( m_planarMovement )
			{
				V2f mult;
				if( !variableAspect )
				{
					mult = V2f( expf( -1.9f * d ) );
					Pointer::setCurrent( "" );
				}
				else
				{
					if( abs( dv.x ) >= abs( dv.y ) )
					{
						m_zoomAxis = ZoomAxis::X;
						Pointer::setCurrent( "moveHorizontally" );
						mult = V2f( expf( -1.9f * dv.x ), 1.0f );
					}
					else
					{
						m_zoomAxis = ZoomAxis::Y;
						Pointer::setCurrent( "moveVertically" );
						mult = V2f( 1.0f, expf( 1.9f * dv.y ) );
					}
				}
				m_planarScale = m_motionPlanarScale * mult;

				if( m_maxPlanarZoom != V2f( 0.0f ) )
				{
					m_planarScale = V2f(
						std::max( m_planarScale.x, 1.0f / m_maxPlanarZoom.x ),
						std::max( m_planarScale.y, 1.0f / m_maxPlanarZoom.y )
					);
				}

				// Also apply a transform to keep the origin of the scale centered on the
				// starting cursor position
				V2f offset = V2f( -1, 1 ) * ( m_planarScale - m_motionPlanarScale ) *
					( m_motionStart - V2f( 0.5 ) * resolution );
				M44f t = m_motionMatrix;
				t.translate( V3f( offset.x, offset.y, 0 ) );
				m_transform = t;
			}
			else if( m_camera->getProjection()=="perspective" )
			{
				m_centerOfInterest = m_motionCenterOfInterest * expf( -1.9f * d );

				M44f t = m_motionMatrix;
				t.translate( V3f( 0, 0, m_centerOfInterest - m_motionCenterOfInterest ) );

				m_transform = t;
			}
			else
			{
				// Orthographic
				const float oldWidth = m_camera->getAperture().x;
				const float newWidth = std::max( oldWidth * expf( -1.9f * d ), 0.01f );
				m_camera->setAperture( m_motionOrthoAperture * newWidth / oldWidth );
			}
		}

		// If m_planarMovement is true, we are doing a 2D view with a fixed scaling
		// between world units and pixels, independ of viewport resolution
		// ( and m_sourceCamera will be null ).
		bool m_planarMovement;
		bool m_tumblingEnabled;
		bool m_dollyingEnabled;

		// The camera we are manipulating.
		IECoreScene::CameraPtr m_camera;
		// Additional properties we manipulate, which don't have a standard
		// representation in the Camera class.
		Imath::V2f m_maxPlanarZoom;
		Imath::V2f m_planarScale;
		float m_centerOfInterest;
		M44f m_transform;

		// Motion state
		MotionType m_motionType;
		Imath::V2f m_motionStart;
		Imath::M44f m_motionMatrix;
		float m_motionCenterOfInterest;
		Imath::V2f m_motionPlanarScale;
		Imath::V2f m_motionOrthoAperture;

		ZoomAxis m_zoomAxis;
};

//////////////////////////////////////////////////////////////////////////
// ViewportGadget
//////////////////////////////////////////////////////////////////////////

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( ViewportGadget );

ViewportGadget::ViewportGadget( GadgetPtr primaryChild )
	:	Gadget(),
		m_cameraController( new CameraController() ),
		m_cameraInMotion( false ),
		m_cameraEditable( true ),
		m_preciseMotionAllowed( true ),
		m_preciseMotionEnabled( false ),
		m_dragTracking( DragTracking::NoDragTracking ),
		m_variableAspectZoom( false ),
		m_dragButton( ButtonEvent::None ),
		m_cameraMotionDuringDrag( false )
{

	// Viewport visibility is managed by GadgetWidgets,
	setVisible( false );

	setPrimaryChild( primaryChild );

	childRemovedSignal().connect( boost::bind( &ViewportGadget::childRemoved, this, ::_1, ::_2 ) );

	buttonPressSignal().connect( boost::bind( &ViewportGadget::buttonPress, this, ::_1,  ::_2 ) );
	buttonReleaseSignal().connect( boost::bind( &ViewportGadget::buttonRelease, this, ::_1,  ::_2 ) );
	buttonDoubleClickSignal().connect( boost::bind( &ViewportGadget::buttonDoubleClick, this, ::_1,  ::_2 ) );
	enterSignal().connect( boost::bind( &ViewportGadget::enter, this, ::_2 ) );
	leaveSignal().connect( boost::bind( &ViewportGadget::leave, this, ::_2 ) );
	mouseMoveSignal().connect( boost::bind( &ViewportGadget::mouseMove, this, ::_1,  ::_2 ) );
	dragBeginSignal().connect( boost::bind( &ViewportGadget::dragBegin, this, ::_1, ::_2 ) );
	dragEnterSignal().connect( boost::bind( &ViewportGadget::dragEnter, this, ::_1, ::_2 ) );
	dragMoveSignal().connect( boost::bind( &ViewportGadget::dragMove, this, ::_1, ::_2 ) );
	dragLeaveSignal().connect( boost::bind( &ViewportGadget::dragLeave, this, ::_1, ::_2 ) );
	dropSignal().connect( boost::bind( &ViewportGadget::drop, this, ::_1, ::_2 ) );
	dragEndSignal().connect( boost::bind( &ViewportGadget::dragEnd, this, ::_1, ::_2 ) );
	wheelSignal().connect( boost::bind( &ViewportGadget::wheel, this, ::_1, ::_2 ) );
	keyPressSignal().connect( boost::bind( &ViewportGadget::keyPress, this, ::_1, ::_2 ) );
	keyReleaseSignal().connect( boost::bind( &ViewportGadget::keyRelease, this, ::_1, ::_2 ) );

}

ViewportGadget::~ViewportGadget()
{
}

bool ViewportGadget::acceptsParent( const Gaffer::GraphComponent *potentialParent ) const
{
	return false;
}

std::string ViewportGadget::getToolTip( const IECore::LineSegment3f &line ) const
{
	std::string result = Gadget::getToolTip( line );
	if( result.size() )
	{
		return result;
	}

	std::vector<Gadget*> gadgets = gadgetsAtInternal( V2f( line.p0.x, line.p0.y ), false );
	for( Gadget *it : gadgets )
	{
		Gadget *gadget = it;
		while( gadget && gadget != this )
		{
			IECore::LineSegment3f lineInGadgetSpace = rasterToGadgetSpace( V2f( line.p0.x, line.p0.y), gadget );
			result = gadget->getToolTip( lineInGadgetSpace );
			if( result.size() )
			{
				return result;
			}
			gadget = gadget->parent<Gadget>();
		}
	}

	return result;
}

void ViewportGadget::setPrimaryChild( GadgetPtr gadget )
{
	if( gadget )
	{
		setChild( "__primary", gadget );
	}
	else
	{
		if( Gadget *existingChild = getChild<Gadget>( "__primary" ) )
		{
			removeChild( existingChild );
		}
	}
}

Gadget *ViewportGadget::getPrimaryChild()
{
	return getChild<Gadget>( "__primary" );
}

const Gadget *ViewportGadget::getPrimaryChild() const
{
	return getChild<Gadget>( "__primary" );
}

const Imath::V2i &ViewportGadget::getViewport() const
{
	return m_cameraController->getViewportResolution();
}

void ViewportGadget::setViewport( const Imath::V2i &viewport )
{
	if( viewport == m_cameraController->getViewportResolution() )
	{
		return;
	}

	m_cameraController->setViewportResolution( viewport );

	m_viewportChangedSignal( this );
}

ViewportGadget::UnarySignal &ViewportGadget::viewportChangedSignal()
{
	return m_viewportChangedSignal;
}

bool ViewportGadget::getPlanarMovement() const
{
	return m_cameraController->getPlanarMovement();
}

void ViewportGadget::setPlanarMovement( bool planarMovement )
{
	m_cameraController->setPlanarMovement( planarMovement );
}

void ViewportGadget::setPreciseMotionAllowed( bool allowed )
{
	m_preciseMotionAllowed = allowed;
}

bool ViewportGadget::getPreciseMotionAllowed() const
{
	return m_preciseMotionAllowed;
}


IECoreScene::ConstCameraPtr ViewportGadget::getCamera() const
{
	return m_cameraController->getCamera();
}

void ViewportGadget::setCamera( IECoreScene::CameraPtr camera )
{
	if( !camera )
	{
		throw Exception( "Cannot use null camera in ViewportGadget." );
	}

	if( m_cameraController->getCamera()->isEqualTo( camera.get() ) )
	{
		return;
	}
	m_cameraController->setCamera( camera->copy() );
	m_cameraChangedSignal( this );
	dirty( DirtyType::Render );
}

const Imath::M44f &ViewportGadget::getCameraTransform() const
{
	return m_cameraController->getTransform();
}

void ViewportGadget::setCameraTransform( const Imath::M44f &transform )
{
	const Imath::M44f viewTransform = Imath::sansScalingAndShear( transform );
	if( viewTransform == getCameraTransform() )
	{
		return;
	}
	m_cameraController->setTransform( viewTransform );
	m_cameraChangedSignal( this );
	dirty( DirtyType::Render );
}

ViewportGadget::UnarySignal &ViewportGadget::cameraChangedSignal()
{
	return m_cameraChangedSignal;
}

bool ViewportGadget::getCameraEditable() const
{
	return m_cameraEditable;
}

void ViewportGadget::setCameraEditable( bool editable )
{
	m_cameraEditable = editable;
}

void ViewportGadget::setCenterOfInterest( float centerOfInterest )
{
	m_cameraController->setCenterOfInterest( centerOfInterest );
	m_cameraChangedSignal( this );
}

float ViewportGadget::getCenterOfInterest() const
{
	return m_cameraController->getCenterOfInterest();
}

float ViewportGadget::getCenterOfInterest()
{
	return m_cameraController->getCenterOfInterest();
}

void ViewportGadget::setTumblingEnabled( bool tumblingEnabled )
{
	m_cameraController->setTumblingEnabled( tumblingEnabled );
}

bool ViewportGadget::getTumblingEnabled() const
{
	return m_cameraController->getTumblingEnabled();
}

void ViewportGadget::setDollyingEnabled( bool dollyingEnabled )
{
	m_cameraController->setDollyingEnabled( dollyingEnabled );
}

bool ViewportGadget::getDollyingEnabled() const
{
	return m_cameraController->getDollyingEnabled();
}

void ViewportGadget::setMaxPlanarZoom( const Imath::V2f &scale )
{
	m_cameraController->setMaxPlanarZoom( scale );
}

Imath::V2f ViewportGadget::getMaxPlanarZoom() const
{
	return m_cameraController->getMaxPlanarZoom();
}

Imath::V2f ViewportGadget::getMaxPlanarZoom()
{
	return m_cameraController->getMaxPlanarZoom();
}

void ViewportGadget::frame( const Imath::Box3f &box )
{
	m_cameraController->frame( box, m_variableAspectZoom );
	m_cameraChangedSignal( this );
	dirty( DirtyType::Render );
}

void ViewportGadget::frame( const Imath::Box3f &box, const Imath::V3f &viewDirection,
	const Imath::V3f &upVector )
{
	m_cameraController->frame( box, viewDirection, upVector );
	m_cameraChangedSignal( this );
	dirty( DirtyType::Render );
}

void ViewportGadget::fitClippingPlanes( const Imath::Box3f &box )
{
	// Transform bound to camera space.
	Box3f b = transform( box, getCameraTransform().inverse() );
	// Choose a far plane that should still be
	// sufficient no matter how we orbit about the
	// center of the bound.
	const float bRadius = b.size().length() / 2.0;
	float far = b.center().z - bRadius;
	if( far >= 0.0f )
	{
		// Far plane behind the camera - not much we
		// can sensibly do.
		return;
	}
	else
	{
		// Far will be -ve because camera looks down -ve
		// Z, but clipping is specified as +ve.
		far *= -1;
	}
	// Round up to 2 significant digits, so we have a tiny
	// bit of padding and a neatish number.
	far = ceilSignificantDigits( far, 2 );

	// We try to keep near close to the camera, regardless of what we do for
	// far as otherwise, if you dolly in, everything disappears.
	float near = far / 100000.0f;
	near = floorSignificantDigits( near, 2 );
	near = std::max( 0.01f, near );

	m_cameraController->setClippingPlanes( V2f( near, far ) );
	m_cameraChangedSignal( this );
	dirty( DirtyType::Render );
}

void ViewportGadget::setDragTracking( unsigned dragTracking )
{
	m_dragTracking = dragTracking;
}

unsigned ViewportGadget::getDragTracking() const
{
	return m_dragTracking;
}

void ViewportGadget::setVariableAspectZoom( bool variableAspectZoom )
{
	m_variableAspectZoom = variableAspectZoom;
}

bool ViewportGadget::getVariableAspectZoom() const
{
	return m_variableAspectZoom;
}

std::vector< Gadget* > ViewportGadget::gadgetsAt( const Imath::V2f &rasterPosition ) const
{
	return gadgetsAtInternal( Box2f( rasterPosition - V2f( 1 ), rasterPosition + V2f( 1 ) ), Layer::None, false );
}

std::vector< Gadget* > ViewportGadget::gadgetsAt( const Imath::Box2f &rasterRegion, Gadget::Layer filterLayer ) const
{
	return gadgetsAtInternal( rasterRegion, filterLayer, false );
}
std::vector< Gadget* > ViewportGadget::gadgetsAtInternal( const Imath::V2f &rasterPosition, bool dragging ) const
{
	return gadgetsAtInternal( Box2f( rasterPosition - V2f( 1 ), rasterPosition + V2f( 1 ) ), Layer::None, dragging );
}

std::vector< Gadget* > ViewportGadget::gadgetsAtInternal( const Imath::Box2f &rasterRegion, Gadget::Layer filterLayer, bool dragging ) const
{
	std::vector<HitRecord> selection;
	{
		SelectionScope selectionScope( this, rasterRegion, selection, IECoreGL::Selector::IDRender );
		renderInternal( dragging ? RenderReason::DragSelect : RenderReason::Select, filterLayer );
	}

	std::vector< Gadget* > gadgets;
	for( const HitRecord &it : selection )
	{
		// We can assume that renderInternal has populated m_renderItem, so we can just index into it
		// using the index passed to loadName ( reversing the increment-by-one used to avoid the reserved
		// name "0" )
		gadgets.push_back( const_cast<Gadget*>( m_renderItems[ it.name - 1 ].gadget ) );
	}

	if( !gadgets.size() )
	{
		if( const Gadget *g = getPrimaryChild() )
		{
			gadgets.push_back( const_cast<Gadget *>( g ) );
		}
	}
	return gadgets;
}

// DEPRECATED
void ViewportGadget::gadgetsAt( const Imath::V2f &rasterPosition, std::vector<GadgetPtr> &gadgets ) const
{
	std::vector< Gadget* > retGadgets = gadgetsAt( rasterPosition );
	for( Gadget *g : retGadgets )
	{
		gadgets.push_back( g );
	}
}

IECore::LineSegment3f ViewportGadget::rasterToGadgetSpace( const Imath::V2f &position, const Gadget *gadget ) const
{
	LineSegment3f result;
	m_cameraController->unproject( position, result.p0, result.p1 );
	if( gadget )
	{
		M44f m = gadget->fullTransform();
		m.invert( true );
		result = result * m;
	}
	return result;
}

Imath::V2f ViewportGadget::gadgetToRasterSpace( const Imath::V3f &gadgetPosition, const Gadget *gadget ) const
{
	M44f gadgetTransform = gadget->fullTransform();
	V3f worldSpacePosition = gadgetPosition * gadgetTransform;
	return m_cameraController->project( worldSpacePosition );
}

IECore::LineSegment3f ViewportGadget::rasterToWorldSpace( const Imath::V2f &rasterPosition ) const
{
	LineSegment3f result;
	m_cameraController->unproject( rasterPosition, result.p0, result.p1 );
	return result;
}

Imath::V2f ViewportGadget::worldToRasterSpace( const Imath::V3f &worldPosition ) const
{
	return m_cameraController->project( worldPosition );
}

void ViewportGadget::render() const
{
	const_cast<ViewportGadget *>( this )->preRenderSignal()(
		const_cast<ViewportGadget *>( this )
	);

	IECoreGL::ToGLConverterPtr converter = new IECoreGL::ToGLCameraConverter(
		m_cameraController->getCamera()
	);
	IECoreGL::CameraPtr camera = boost::static_pointer_cast<IECoreGL::Camera>( converter->convert() );
	camera->setTransform( getCameraTransform() );
	camera->render( nullptr );

	glClearColor( 0.26f, 0.26f, 0.26f, 0.0f );
	glClearDepth( 1.0f );
	glClear( GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT );

	// Set up the camera to world matrix in gl_TextureMatrix[0] so that we can
	// reference world space positions in shaders
	// This should be more appropriately named in a uniform buffer, but the
	// easiest time to get this right is probably when we switch everything
	// away from using fixed function stuff
	glActiveTexture( GL_TEXTURE0 );
	glMatrixMode( GL_TEXTURE );
	glLoadIdentity();
	glMultMatrixf( camera->getTransform().getValue() );
	glMatrixMode( GL_MODELVIEW );

	renderInternal( RenderReason::Draw );
}

void ViewportGadget::childDirtied( DirtyType dirtyType )
{
	if( dirtyType == DirtyType::Layout || dirtyType == DirtyType::RenderBound )
	{
		// We need to rebuild the render items list
		m_renderItems.clear();
	}

	renderRequestSignal()( this );
}

void ViewportGadget::renderInternal( RenderReason reason, Gadget::Layer filterLayer ) const
{

	bound(); // Updates layout if necessary

	if( !m_renderItems.size() )
	{
		getRenderItems( this, M44f(), style(), m_renderItems );
	}

	M44f viewTransform;
	glGetFloatv( GL_MODELVIEW_MATRIX, viewTransform.getValue() );
	M44f projectionTransform;
	glGetFloatv( GL_PROJECTION_MATRIX, projectionTransform.getValue() );

	M44f combinedInverse = projectionTransform.inverse() * viewTransform.inverse();
	Box3f bound = transform( Box3f( V3f( -1 ), V3f( 1 ) ), combinedInverse );
	IECoreGL::Selector *selector = IECoreGL::Selector::currentSelector();

	const Style *currentStyle = nullptr;

	for( int layerIndex = (int)Layer::Back; layerIndex <= (int)Layer::Front; layerIndex <<= 1 )
	{
		Layer layer = Layer(layerIndex);
		if( filterLayer != Layer::None && layer != filterLayer )
		{
			continue;
		}

		for( unsigned int i = 0; i < m_renderItems.size(); i++ )
		{
			const RenderItem &renderItem = m_renderItems[i];
			if( !( renderItem.layerMask & layerIndex ) )
			{
				continue;
			}

			if( !renderItem.bound.intersects( bound ) )
			{
				continue;
			}

			glLoadMatrixf( viewTransform.getValue() );
			glMultMatrixf( renderItem.transform.getValue() );
			if( selector )
			{
				// 0 is a reserved name for when nothing is selected, so start at 1
				selector->loadName( i + 1 );
			}

			if( renderItem.style != currentStyle )
			{
				renderItem.style->bind( currentStyle );
				currentStyle = renderItem.style;
			}

			renderItem.gadget->renderLayer( layer, currentStyle, reason );
		}
	}
	glLoadMatrixf( viewTransform.getValue() );
}

void ViewportGadget::getRenderItems( const Gadget *gadget, M44f transform, const Style *style, std::vector<RenderItem> &renderItems )
{
	const Box3f bound = gadget->renderBound();
	bool boundSpecial = bound.isEmpty() || bound == g_infiniteBox;

	if( gadget->getStyle() )
	{
		style = gadget->getStyle();
	}

	if( gadget->m_transform != g_identityMatrix )
	{
		transform = gadget->m_transform * transform;
	}

	unsigned layerMask = gadget->layerMask();
	if( layerMask )
	{
		renderItems.push_back( {
			gadget, style, transform,
			boundSpecial ? bound : Imath::transform( bound, transform ),
			layerMask
		} );
	}

	for( const auto &i : gadget->children() )
	{
		// Cast is safe because of the guarantees acceptsChild() gives us
		const Gadget *c = static_cast<const Gadget *>( i.get() );
		if( !c->getVisible() )
		{
			continue;
		}
		getRenderItems( c, transform, style, renderItems );
	}
}

ViewportGadget::UnarySignal &ViewportGadget::preRenderSignal()
{
	return m_preRenderSignal;
}

ViewportGadget::UnarySignal &ViewportGadget::renderRequestSignal()
{
	return m_renderRequestSignal;
}

void ViewportGadget::childRemoved( GraphComponent *parent, GraphComponent *child )
{
	const Gadget *childGadget = static_cast<const Gadget *>( child );

	if( childGadget == m_lastButtonPressGadget || childGadget->isAncestorOf( m_lastButtonPressGadget.get() ) )
	{
		m_lastButtonPressGadget = nullptr;
	}

	if( childGadget == m_previousClickGadget || childGadget->isAncestorOf( m_previousClickGadget.get() ) )
	{
		m_previousClickGadget = nullptr;
	}

	if( childGadget == m_gadgetUnderMouse || childGadget->isAncestorOf( m_gadgetUnderMouse.get() ) )
	{
		m_gadgetUnderMouse = nullptr;
	}
}

bool ViewportGadget::buttonPress( GadgetPtr gadget, const ButtonEvent &event )
{
	if( m_dragButton != ButtonEvent::None && m_dragButton != ButtonEvent::Middle && event.buttons == ( m_dragButton | ButtonEvent::Middle ) )
	{
		m_cameraMotionDuringDrag = true;

		if( getCameraEditable() )
		{
			updateMotionState( event, true );
			m_cameraController->motionStart( CameraController::Track, motionPositionFromEvent( event ) );
		}
		return true;
	}

	// A child's interaction with an unmodifier MMB drag takes precedence over camera moves
	bool unmodifiedMiddleDrag = event.buttons == ButtonEvent::Middle && event.modifiers == ModifiableEvent::None;

	if( !unmodifiedMiddleDrag && m_cameraController->cameraMotionType( event, m_variableAspectZoom, m_preciseMotionAllowed ) )
	{
		// accept press so we get a dragBegin opportunity for camera movement
		return true;
	}

	std::vector<Gadget*> gadgets = gadgetsAtInternal( V2f( event.line.p0.x, event.line.p0.y ), false );

	Gadget* handler;
	m_lastButtonPressGadget = nullptr;
	m_previousClickGadget = nullptr;
	bool result = dispatchEvent( gadgets, &Gadget::buttonPressSignal, event, handler );
	if( result )
	{
		m_lastButtonPressGadget = handler;
		m_previousClickGadget = handler;
		return true;
	}

	if( unmodifiedMiddleDrag )
	{
		// accept press so we get a dragBegin opportunity for camera movement
		return true;
	}

	return false;
}

bool ViewportGadget::buttonRelease( GadgetPtr gadget, const ButtonEvent &event )
{
	if( m_cameraMotionDuringDrag && !( event.buttons & ButtonEvent::Middle ) )
	{
		m_cameraMotionDuringDrag = false;

		if( getCameraEditable() )
		{
			updateMotionState( event );
			m_cameraController->motionEnd( motionPositionFromEvent( event ), m_variableAspectZoom && ( event.modifiers & ModifiableEvent::Control ) != 0 );
			m_cameraChangedSignal( this );
			m_preciseMotionEnabled = false;
			dirty( DirtyType::Render );
		}
		return true;
	}

	bool result = false;
	if( m_lastButtonPressGadget )
	{
		result = dispatchEvent( m_lastButtonPressGadget.get(), &Gadget::buttonReleaseSignal, event );
	}

	m_lastButtonPressGadget = nullptr;
	return result;
}

bool ViewportGadget::buttonDoubleClick( GadgetPtr gadget, const ButtonEvent &event )
{
	if( m_previousClickGadget )
	{
		return dispatchEvent( m_previousClickGadget.get(), &Gadget::buttonDoubleClickSignal, event );
	}

	return false;
}

void ViewportGadget::updateGadgetUnderMouse( const ButtonEvent &event )
{
	std::vector<Gadget*> gadgets = gadgetsAtInternal( V2f( event.line.p0.x, event.line.p0.y ), false );

	Gadget* newGadgetUnderMouse = nullptr;
	if( gadgets.size() )
	{
		newGadgetUnderMouse = gadgets[0];
	}

	if( m_gadgetUnderMouse != newGadgetUnderMouse )
	{
		emitEnterLeaveEvents( newGadgetUnderMouse, m_gadgetUnderMouse, event );
		m_gadgetUnderMouse = newGadgetUnderMouse;
	}
}

void ViewportGadget::emitEnterLeaveEvents( GadgetPtr newGadgetUnderMouse, GadgetPtr oldGadgetUnderMouse, const ButtonEvent &event )
{

	// figure out the lowest point in the hierarchy where the entered status is unchanged.
	GadgetPtr lowestUnchanged = this;
	if( oldGadgetUnderMouse && newGadgetUnderMouse )
	{
		if( oldGadgetUnderMouse->isAncestorOf( newGadgetUnderMouse.get() ) )
		{
			lowestUnchanged = oldGadgetUnderMouse;
		}
		else if( newGadgetUnderMouse->isAncestorOf( oldGadgetUnderMouse.get() ) )
		{
			lowestUnchanged = newGadgetUnderMouse;
		}
		else
		{
			if( Gadget *commonAncestor = oldGadgetUnderMouse->commonAncestor<Gadget>( newGadgetUnderMouse.get() ) )
			{
				lowestUnchanged = commonAncestor;
			}
		}
	}

	// emit leave events, innermost first
	if( oldGadgetUnderMouse )
	{
		GadgetPtr leaveTarget = oldGadgetUnderMouse;
		while( leaveTarget && leaveTarget != lowestUnchanged )
		{
			dispatchEvent( leaveTarget.get(), &Gadget::leaveSignal, event );
			leaveTarget = leaveTarget->parent<Gadget>();
		}
	}

	// emit enter events, outermost first
	if( newGadgetUnderMouse )
	{
		std::vector<GadgetPtr> enterTargets;
		GadgetPtr enterTarget = newGadgetUnderMouse;
		while( enterTarget && enterTarget != lowestUnchanged )
		{
			enterTargets.push_back( enterTarget );
			enterTarget = enterTarget->parent<Gadget>();
		}
		for( GadgetPtr &it : enterTargets )
		{
			dispatchEvent( it.get(), &Gadget::enterSignal, event );
		}
	}

};

void ViewportGadget::enter( const ButtonEvent &event )
{
	updateGadgetUnderMouse( event );
}

void ViewportGadget::leave( const ButtonEvent &event )
{
	if( m_gadgetUnderMouse )
	{
		emitEnterLeaveEvents( nullptr, m_gadgetUnderMouse, event );
		m_gadgetUnderMouse = nullptr;
	}
}

bool ViewportGadget::mouseMove( GadgetPtr gadget, const ButtonEvent &event )
{
	// find the gadget under the mouse
	updateGadgetUnderMouse( event );

	// pass the signal through
	if( m_gadgetUnderMouse )
	{
		std::vector<Gadget*> gadgetUnderMouse( 1, m_gadgetUnderMouse.get() );
		Gadget* handler;
		return dispatchEvent( gadgetUnderMouse, &Gadget::mouseMoveSignal, event, handler );
	}

	return false;
}

IECore::RunTimeTypedPtr ViewportGadget::dragBegin( GadgetPtr gadget, const DragDropEvent &event )
{
	m_dragButton = event.buttons;
	m_dragTrackingThreshold = limits<float>::max();

	CameraController::MotionType cameraMotionType = m_cameraController->cameraMotionType( event, m_variableAspectZoom, m_preciseMotionAllowed );
	bool unmodifiedMiddleDrag = event.buttons == ButtonEvent::Middle && event.modifiers == ModifiableEvent::None;

	if( ( !cameraMotionType || unmodifiedMiddleDrag ) && m_lastButtonPressGadget )
	{
		// see if a child gadget would like to start a drag because the camera doesn't handle the event
		RunTimeTypedPtr data = dispatchEvent( m_lastButtonPressGadget.get(), &Gadget::dragBeginSignal, event );
		if( data )
		{
			const_cast<DragDropEvent &>( event ).sourceGadget = m_lastButtonPressGadget;

			return data;
		}
	}

	if( cameraMotionType )
	{
		m_cameraInMotion = true;

		// the const_cast is necessary because we don't want to give all the other
		// Gadget types non-const access to the event, but we do need the ViewportGadget
		// to assign destination and source gadgets. the alternative would be a different
		// set of non-const signals on the ViewportGadget, or maybe even having ViewportGadget
		// not derived from Gadget at all. this seems the lesser of two evils.
		const_cast<DragDropEvent &>( event ).sourceGadget = this;

		// we only actually update the camera if it's editable, but we still go through
		// the usual dragEnter/dragMove/dragEnd process so that we can swallow the events.
		// it would be confusing for users if they tried to edit a non-editable camera and
		// their gestures fell through and affected the viewport contents.
		if( getCameraEditable() )
		{
			updateMotionState( event, true );
			m_cameraController->motionStart( cameraMotionType, motionPositionFromEvent( event ) );
		}

		// we have to return something to start the drag, but we return something that
		// noone else will accept to make sure we keep the drag to ourself.
		return IECore::NullObject::defaultNullObject();
	}
	else
	{
		return nullptr;
	}

	return nullptr;
}

bool ViewportGadget::dragEnter( GadgetPtr gadget, const DragDropEvent &event )
{
	if( m_cameraInMotion )
	{
		// it's a drag for moving the camera
		return true;
	}
	else
	{
		std::vector<Gadget*> gadgets = gadgetsAtInternal( V2f( event.line.p0.x, event.line.p0.y ), true );

		Gadget* dragDestination = updatedDragDestination( gadgets, event );
		if( dragDestination )
		{
			const_cast<DragDropEvent &>( event ).destinationGadget = dragDestination;
			return true;
		}
	}
	return false;
}

bool ViewportGadget::dragMove( GadgetPtr gadget, const DragDropEvent &event )
{
	if( m_cameraInMotion || m_cameraMotionDuringDrag )
	{
		if( getCameraEditable() )
		{
			updateMotionState( event );
			m_cameraController->motionUpdate( motionPositionFromEvent( event ), m_variableAspectZoom && ( event.modifiers & ModifiableEvent::Control ) != 0 );
			m_cameraChangedSignal( this );
			dirty( DirtyType::Render );
		}
		return true;
	}
	else
	{
		// perform drag tracking if necessary
		trackDrag( event );

		// update the destination gadget. if the drag data is a NullObject then we know
		// that it isn't intended for use outside of the source gadget, and can skip this
		// step as an optimisation.
		if( !event.destinationGadget || !event.data->isInstanceOf( IECore::NullObjectTypeId ) )
		{
			std::vector<Gadget*> gadgets = gadgetsAtInternal( V2f( event.line.p0.x, event.line.p0.y ), true );

			// update drag destination
			Gadget* updatedDestination = updatedDragDestination( gadgets, event );
			if( updatedDestination != event.destinationGadget )
			{
				Gadget* previousDestination = event.destinationGadget.get();
				const_cast<DragDropEvent &>( event ).destinationGadget = updatedDestination;
				if( previousDestination )
				{
					dispatchEvent( previousDestination, &Gadget::dragLeaveSignal, event );
				}
			}
		}

		// dispatch drag move to current destination
		if( event.destinationGadget )
		{
			return dispatchEvent( event.destinationGadget.get(), &Gadget::dragMoveSignal, event );
		}
	}

	return false;
}

void ViewportGadget::trackDrag( const DragDropEvent &event )
{
	// early out if tracking is off for any reason, or
	// the drag didn't originate from within the viewport.

	if(
		getDragTracking() == DragTracking::NoDragTracking ||
		!getCameraEditable() ||
		!this->isAncestorOf( event.sourceGadget.get() )
	)
	{
		m_dragTrackingIdleConnection.disconnect();
		return;
	}

	// we automatically scroll to track drags when the mouse is
	// near the edge of our viewport. figure out an inset box within
	// which we _don't_ perform tracking - if the mouse leaves this then
	// we'll track it.

	const V2i viewport = getViewport();
	const float borderWidth = std::min( std::min( viewport.x, viewport.y ) / 8.0f, 60.0f );

	const Box3f viewportBox(
		V3f( borderWidth, borderWidth, -1000.0f ),
		V3f( viewport.x - borderWidth, viewport.y - borderWidth, 1000.0f )
	);

	// figure out the offset, if any, of the mouse outside this central box.

	V2f offset( 0.0f );
	if( !viewportBox.intersects( event.line.p0 ) )
	{
		const V3f offset3 = event.line.p0 - closestPointOnBox( event.line.p0, viewportBox );
		offset = V2f(
			getDragTracking() & DragTracking::XDragTracking ? offset3.x : 0,
			getDragTracking() & DragTracking::YDragTracking ? offset3.y : 0
		);
	}

	const float offsetLength = clamp( offset.length(), 0.0f, borderWidth );

	// update our tracking threshold. the mouse has to go past this offset before
	// tracking starts. this allows us to avoid tracking too early when a drag is
	// started inside the tracking area, but the user is dragging back into the
	// center of frame.

	m_dragTrackingThreshold = std::min( offsetLength, m_dragTrackingThreshold );

	// figure out our drag velocity. we ramp up the speed of the scrolling from 0
	// to a maximum at the edge of the viewport, and clamp it so it doesn't get any
	// faster outside of the viewport. although getting even faster when the mouse
	// is outside the viewport might be nice, it results in an inconsistent
	// experience where a viewport edge is at the edge of the screen and the mouse
	// can't go any further.

	m_dragTrackingVelocity = -offset.normalized() * borderWidth * lerpfactor( offsetLength, m_dragTrackingThreshold, borderWidth );

	// we don't actually do the scrolling in this function - instead we ensure that
	// trackDragIdle will be called to apply the scrolling on idle events.
	// this allows the scrolling to happen even when the mouse isn't moving.

	if( m_dragTrackingVelocity.length() > 0.0001 )
	{
		m_dragTrackingEvent = event;
		if( !m_dragTrackingIdleConnection.connected() )
		{
			m_dragTrackingTime = std::chrono::steady_clock::now();
			m_dragTrackingIdleConnection = idleSignal().connect( boost::bind( &ViewportGadget::trackDragIdle, this ) );
		}
	}
	else
	{
		m_dragTrackingIdleConnection.disconnect();
	}
}

void ViewportGadget::trackDragIdle()
{
	if( m_cameraMotionDuringDrag )
	{
		// If the user engages an explicit track using the middle mouse button, don't do autoscrolling
		return;
	}

	std::chrono::steady_clock::time_point now = std::chrono::steady_clock::now();
	std::chrono::duration<float> duration( now - m_dragTrackingTime );
	// Avoid excessive movements if some other process causes a large delay
	// between idle events.
	duration = std::min( duration, std::chrono::duration<float>( 0.1 ) );

	m_cameraController->motionStart( CameraController::Track, V2f( 0 ) );
	m_cameraController->motionEnd( m_dragTrackingVelocity * duration.count() * 20.0f );

	m_dragTrackingTime = now;

	// although the mouse hasn't moved, moving the camera will have moved it
	// relative to our child gadgets, so we fake a move event to update any
	// visual representation of the drag.
	dragMove( this, m_dragTrackingEvent );

	m_cameraChangedSignal( this );
	dirty( DirtyType::Render );
}

void ViewportGadget::updateMotionState( const ButtonEvent &event, bool initialEvent )
{
	if( !m_preciseMotionAllowed )
	{
		m_preciseMotionEnabled = false;
		return;
	}

	// Every time we transition from coarse to fine motion (or the reverse) we
	// begin a new 'motion segment', we then adjust the actual movement
	// relative to the beginning of the segment, either 1:1 or 10:1. This means
	// that toggling between precise/normal motion doesn't cause jumps in
	// position.  We have to track the absolute event origin (m_motionSegmentEventOrigin)
	// and the relative position (m_motionSegmentOrigin) at the start of the
	// segment to calculate this.

	const bool shiftHeld = event.modifiers & ModifiableEvent::Shift;

	if( initialEvent )
	{
		m_motionSegmentEventOrigin = V2f( event.line.p1.x, event.line.p1.y );
		m_motionSegmentOrigin = m_motionSegmentEventOrigin;
	}
	else if( m_preciseMotionEnabled != shiftHeld )
	{
		m_motionSegmentOrigin = motionPositionFromEvent( event );
		m_motionSegmentEventOrigin = V2f( event.line.p1.x, event.line.p1.y );
	}

	m_preciseMotionEnabled = shiftHeld;
}

V2f ViewportGadget::motionPositionFromEvent( const ButtonEvent &event ) const
{
	V2f eventPosition( event.line.p1.x, event.line.p1.y );
	if( m_preciseMotionAllowed )
	{
		const float scaleFactor = m_preciseMotionEnabled ? 0.1f : 1.0f;
		return m_motionSegmentOrigin + ( ( eventPosition - m_motionSegmentEventOrigin ) * scaleFactor );
	}
	else
	{
		return eventPosition;
	}
}

Gadget* ViewportGadget::updatedDragDestination( std::vector<Gadget*> &gadgets, const DragDropEvent &event )
{
	for( Gadget *it : gadgets )
	{
		Gadget* gadget = it;
		while( gadget && gadget != this )
		{
			if( gadget == event.destinationGadget )
			{
				// no need to emit enter events when the current destination
				// hasn't changed.
				return gadget;
			}

			bool result = dispatchEvent( gadget, &Gadget::dragEnterSignal, event );
			if( result )
			{
				return gadget;
			}
			gadget = gadget->parent<Gadget>();
		}
	}

	// there's nothing under the mouse that wants the drag. if the event source
	// is a gadget, and we're the owner of that gadget, then there's some more
	// things to try, but otherwise we should get out now.
	if( !event.sourceGadget || !this->isAncestorOf( event.sourceGadget.get() ) )
	{
		return nullptr;
	}

	// keep the existing destination if it's also the source.
	if( event.destinationGadget && event.destinationGadget == event.sourceGadget )
	{
		return event.destinationGadget.get();
	}

	// and if that's not the case then give the drag source another chance
	// to become the destination again.
	if( event.sourceGadget )
	{
		if( dispatchEvent( event.sourceGadget.get(), &Gadget::dragEnterSignal, event ) )
		{
			return event.sourceGadget.get();
		}
	}

	// and if that failed, we have no current destination
	return nullptr;
}

bool ViewportGadget::dragLeave( GadgetPtr gadget, const DragDropEvent &event )
{
	if( event.destinationGadget )
	{
		GadgetPtr previousDestination = event.destinationGadget;
		const_cast<DragDropEvent &>( event ).destinationGadget = nullptr;
		dispatchEvent( previousDestination.get(), &Gadget::dragLeaveSignal, event );
	}
	return true;
}

bool ViewportGadget::drop( GadgetPtr gadget, const DragDropEvent &event )
{
	if( m_cameraInMotion )
	{
		return true;
	}
	else
	{
		if( event.destinationGadget )
		{
			return dispatchEvent( event.destinationGadget.get(), &Gadget::dropSignal, event );
		}
		else
		{
			return false;
		}
	}
}

bool ViewportGadget::dragEnd( GadgetPtr gadget, const DragDropEvent &event )
{
	m_dragButton = ButtonEvent::None;
	m_cameraMotionDuringDrag = false;

	if( m_cameraInMotion )
	{
		m_cameraInMotion = false;
		if( getCameraEditable() )
		{
			updateMotionState( event );
			m_cameraController->motionEnd( motionPositionFromEvent( event ), m_variableAspectZoom && ( event.modifiers & ModifiableEvent::Control ) != 0 );
			m_cameraChangedSignal( this );
			m_preciseMotionEnabled = false;
			dirty( DirtyType::Render );
		}
		return true;
	}
	else
	{
		m_dragTrackingIdleConnection.disconnect();
		if( event.sourceGadget )
		{
			return dispatchEvent( event.sourceGadget.get(), &Gadget::dragEndSignal, event );
		}
	}
	return false;
}

bool ViewportGadget::wheel( GadgetPtr gadget, const ButtonEvent &event )
{
	if( m_cameraInMotion || m_cameraMotionDuringDrag )
	{
		// we can't embed a dolly inside whatever other motion we already
		// started - we get here when the user accidentally rotates
		// the wheel while middle dragging, so it's fine to do nothing.
		return false;
	}

	if( !getCameraEditable() )
	{
		return true;
	}

	V2f position( event.line.p0.x, event.line.p0.y );

	m_cameraController->motionStart( CameraController::Dolly, position );
	const float scaleFactor = event.modifiers & ModifiableEvent::Modifiers::Shift ? 1400.0f : 140.0f;
	position.x += event.wheelRotation * getViewport().x / scaleFactor ;
	m_cameraController->motionUpdate( position );
	m_cameraController->motionEnd( position );

	m_cameraChangedSignal( this );
	dirty( DirtyType::Render );

	return true;
}

bool ViewportGadget::keyPress( GadgetPtr gadget, const KeyEvent &event )
{
	/// \todo We might want some sort of focus model to say who gets the keypress.
	if( Gadget *child = getPrimaryChild() )
	{
		return child->keyPressSignal()( child, event );
	}

	return false;
}

bool ViewportGadget::keyRelease( GadgetPtr gadget, const KeyEvent &event )
{
	if( Gadget *child = getPrimaryChild() )
	{
		return child->keyReleaseSignal()( child, event );
	}

	return false;
}

void ViewportGadget::eventToGadgetSpace( Event &event, Gadget *gadget )
{
	// no need to do anything
}

void ViewportGadget::eventToGadgetSpace( ButtonEvent &event, Gadget *gadget )
{
	event.line = rasterToGadgetSpace( V2f( event.line.p0.x, event.line.p0.y ), gadget );
}

template<typename Event, typename Signal>
typename Signal::result_type ViewportGadget::dispatchEvent( std::vector<Gadget*> &gadgets, Signal &(Gadget::*signalGetter)(), const Event &event, Gadget* &handler )
{
	for( Gadget* it : gadgets )
	{
		Gadget* gadget = it;
		if( !gadget->enabled() )
		{
			continue;
		}
		while( gadget && gadget != this )
		{
			typename Signal::result_type result = dispatchEvent( gadget, signalGetter, event );
			if( result )
			{
				handler = gadget;
				return result;
			}
			gadget = gadget->parent<Gadget>();
		}
	}
	return typename Signal::result_type();
}

template<typename Event, typename Signal>
typename Signal::result_type ViewportGadget::dispatchEvent( Gadget* gadget, Signal &(Gadget::*signalGetter)(), const Event &event )
{
	Event transformedEvent( event );
	eventToGadgetSpace( transformedEvent, gadget );
	Signal &s = (gadget->*signalGetter)();
	return s( gadget, transformedEvent );
}

//////////////////////////////////////////////////////////////////////////
// SelectionScope implementation
//////////////////////////////////////////////////////////////////////////

ViewportGadget::SelectionScope::SelectionScope( const IECore::LineSegment3f &lineInGadgetSpace, const Gadget *gadget, std::vector<IECoreGL::HitRecord> &selection, IECoreGL::Selector::Mode mode )
	:	m_selection( selection )
{
	const ViewportGadget *viewportGadget = gadget->ancestor<ViewportGadget>();
	V2f rasterPosition = viewportGadget->gadgetToRasterSpace( lineInGadgetSpace.p1, gadget );
	begin( viewportGadget, rasterPosition, gadget->fullTransform(), mode );
}

ViewportGadget::SelectionScope::SelectionScope( const Imath::V3f &corner0InGadgetSpace, const Imath::V3f &corner1InGadgetSpace, const Gadget *gadget, std::vector<IECoreGL::HitRecord> &selection, IECoreGL::Selector::Mode mode )
	:	m_selection( selection )
{
	const ViewportGadget *viewportGadget = gadget->ancestor<ViewportGadget>();

	Box2f rasterRegion;
	rasterRegion.extendBy( viewportGadget->gadgetToRasterSpace( corner0InGadgetSpace, gadget ) );
	rasterRegion.extendBy( viewportGadget->gadgetToRasterSpace( corner1InGadgetSpace, gadget ) );

	begin( viewportGadget, rasterRegion, gadget->fullTransform(), mode );
}

ViewportGadget::SelectionScope::SelectionScope( const ViewportGadget *viewportGadget, const Imath::Box2f &rasterRegion, std::vector<IECoreGL::HitRecord> &selection, IECoreGL::Selector::Mode mode )
	:	m_selection( selection )
{
	begin( viewportGadget, rasterRegion, M44f(), mode );
}

ViewportGadget::SelectionScope::~SelectionScope()
{
	end();
}

IECoreGL::State *ViewportGadget::SelectionScope::baseState()
{
	return m_selector->baseState();
}

void ViewportGadget::SelectionScope::begin( const ViewportGadget *viewportGadget, const Imath::V2f &rasterPosition, const Imath::M44f &transform, IECoreGL::Selector::Mode mode )
{
	begin(
		viewportGadget,
		Box2f( rasterPosition - V2f( 1 ), rasterPosition + V2f( 1 ) ),
		transform,
		mode
	);
}

void ViewportGadget::SelectionScope::begin( const ViewportGadget *viewportGadget, const Imath::Box2f &rasterRegion, const Imath::M44f &transform, IECoreGL::Selector::Mode mode )
{
	glPushAttrib( GL_ALL_ATTRIB_BITS );
	glPushClientAttrib( GL_CLIENT_ALL_ATTRIB_BITS );

	V2f viewport = viewportGadget->getViewport();
	Box2f ndcRegion( rasterRegion.min / viewport, rasterRegion.max / viewport );

	IECoreGL::ToGLConverterPtr converter = new IECoreGL::ToGLCameraConverter(
		viewportGadget->m_cameraController->getCamera()
	);
	IECoreGL::CameraPtr camera = boost::static_pointer_cast<IECoreGL::Camera>( converter->convert() );
	camera->setTransform( viewportGadget->getCameraTransform() );
	/// \todo It would be better to base this on whether we have a depth buffer or not, but
	/// we don't have access to that information right now.

	/// \todo Resolve when to sort or not. For historical reasons this is
	/// currently hardcoded to `false` and to-sort or not-to-sort is handled by clients
	/// of `SceneGadget::objectAt()`. For context, see :
	/// https://github.com/GafferHQ/gaffer/pull/4570#issuecomment-1044709782
	m_depthSort = false;
	camera->render( nullptr );

	glClearColor( 0.3f, 0.3f, 0.3f, 0.0f );
	glClearDepth( 1.0f );
	glClear( GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT );

	m_selector = SelectorPtr( new IECoreGL::Selector( ndcRegion, mode, m_selection ) );

	glPushMatrix();
	glMultMatrixf( transform.getValue() );
}

void ViewportGadget::SelectionScope::end()
{
	glPopMatrix();
	m_selector = SelectorPtr();

	glPopClientAttrib();
	glPopAttrib();

	if( m_depthSort )
	{
		std::sort( m_selection.begin(), m_selection.end() );
	}
	else
	{
		std::reverse( m_selection.begin(), m_selection.end() );
	}
}

ViewportGadget::RasterScope::RasterScope( const ViewportGadget *viewportGadget )
{
	V2f viewport = viewportGadget->getViewport();

	glMatrixMode( GL_PROJECTION );
	glPushMatrix();
	glLoadIdentity();

	if( IECoreGL::Selector *selector = IECoreGL::Selector::currentSelector() )
	{
		glMultMatrixd( selector->postProjectionMatrix().getValue() );
	}

	glOrtho( 0, viewport.x, viewport.y, 0, -1, 1 );

	glMatrixMode( GL_MODELVIEW );
	glPushMatrix();
	glLoadIdentity();
	glTranslatef( 0, 0, 1 );
}

ViewportGadget::RasterScope::~RasterScope()
{
	glPopMatrix();

	glMatrixMode( GL_PROJECTION );
	glPopMatrix();

	glMatrixMode( GL_MODELVIEW );
}
