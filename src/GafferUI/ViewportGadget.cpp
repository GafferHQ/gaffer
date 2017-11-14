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

#include <sys/time.h>

#include "boost/bind.hpp"
#include "boost/bind/placeholders.hpp"

#include "OpenEXR/ImathBoxAlgo.h"
#include "OpenEXR/ImathMatrixAlgo.h"

#include "IECore/Transform.h"
#include "IECore/NullObject.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/AngleConversion.h"
#include "IECore/MessageHandler.h"

#include "IECoreGL/ToGLCameraConverter.h"
#include "IECoreGL/PerspectiveCamera.h"
#include "IECoreGL/State.h"
#include "IECoreGL/Selector.h"

#include "GafferUI/ViewportGadget.h"
#include "GafferUI/Style.h"

using namespace Imath;
using namespace IECore;
using namespace IECoreGL;
using namespace GafferUI;

//////////////////////////////////////////////////////////////////////////
// CameraController
//////////////////////////////////////////////////////////////////////////

class ViewportGadget::CameraController : public boost::noncopyable
{

	public :

		CameraController( IECore::CameraPtr camera )
		{
			setCamera( camera );
		}

		void setCamera( IECore::CameraPtr camera )
		{
			m_camera = camera;
			m_camera->addStandardParameters(); // subsequent casts are safe because of this
			m_resolution = boost::static_pointer_cast<V2iData>( m_camera->parameters()["resolution"] );
			m_screenWindow = boost::static_pointer_cast<Box2fData>( m_camera->parameters()["screenWindow"] );
			m_clippingPlanes = boost::static_pointer_cast<V2fData>( m_camera->parameters()["clippingPlanes"] );
			m_projection = boost::static_pointer_cast<StringData>( m_camera->parameters()["projection"] );
			if( m_projection->readable()=="perspective" )
			{
				m_fov = boost::static_pointer_cast<FloatData>( m_camera->parameters()["projection:fov"] );
			}
			else
			{
				m_fov = nullptr;
			}

			m_centreOfInterest = 1;
		}

		IECore::Camera *getCamera()
		{
			return m_camera.get();
		}

		const IECore::Camera *getCamera() const
		{
			return m_camera.get();
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
		void setCentreOfInterest( float centreOfInterest )
		{
			m_centreOfInterest = centreOfInterest;
		}

		float getCentreOfInterest()
		{
			return m_centreOfInterest;
		}

		enum ScreenWindowAdjustment
		{
			/// Crop/extend the screen window to accommodate
			/// the new resolution without scaling the content.
			CropScreenWindow,
			/// Preserve the horizontal framing and change the
			/// vertical framing to maintain aspect ratio.
			ScaleScreenWindow
		};

		/// Changes the camera resolution, modifying the screen window
		/// in a manner determined by the adjustment argument.
		void setResolution( const Imath::V2i &resolution, ScreenWindowAdjustment adjustment )
		{
			const V2i oldResolution = m_resolution->readable();
			const Box2f oldScreenWindow = m_screenWindow->readable();

			m_resolution->writable() = resolution;

			Box2f newScreenWindow;
			if( adjustment == ScaleScreenWindow )
			{
				const float oldAspect = (float)oldResolution.x/(float)oldResolution.y;
				const float badAspect = (float)resolution.x/(float)resolution.y;
				const float yScale = oldAspect / badAspect;

				newScreenWindow = oldScreenWindow;
				newScreenWindow.min.y *= yScale;
				newScreenWindow.max.y *= yScale;
			}
			else
			{
				const V2f screenWindowCenter = oldScreenWindow.center();
				const V2f scale = V2f( resolution ) / V2f( oldResolution );
				newScreenWindow.min = screenWindowCenter + (oldScreenWindow.min - screenWindowCenter) * scale;
				newScreenWindow.max = screenWindowCenter + (oldScreenWindow.max - screenWindowCenter) * scale;
			}

			m_screenWindow->writable() = newScreenWindow;
		}

		const Imath::V2i &getResolution() const
		{
			return m_resolution->readable();
		}

		/// Moves the camera to frame the specified box, keeping the
		/// current viewing direction unchanged.
		void frame( const Imath::Box3f &box )
		{
			V3f z( 0, 0, -1 );
			V3f y( 0, 1, 0 );
			M44f t = m_transform;
			t.multDirMatrix( z, z );
			t.multDirMatrix( y, y );
			frame( box, z, y );
		}

		/// Moves the camera to frame the specified box, viewing it from the
		/// specified direction, and with the specified up vector.
		void frame( const Imath::Box3f &box, const Imath::V3f &viewDirection,
			const Imath::V3f &upVector = Imath::V3f( 0, 1, 0 ) )
		{
			// make a matrix to centre the camera on the box, with the appropriate view direction
			M44f cameraMatrix = rotationMatrixWithUpDir( V3f( 0, 0, -1 ), viewDirection, upVector );
			M44f translationMatrix;
			translationMatrix.translate( box.center() );
			cameraMatrix *= translationMatrix;

			// translate the camera back until the box is completely visible
			M44f inverseCameraMatrix = cameraMatrix.inverse();
			Box3f cBox = transform( box, inverseCameraMatrix );

			Box2f screenWindow = m_screenWindow->readable();
			if( m_projection->readable()=="perspective" )
			{
				// perspective. leave the field of view and screen window as is and translate
				// back till the box is wholly visible. this currently assumes the screen window
				// is centred about the camera axis.
				float z0 = cBox.size().x / screenWindow.size().x;
				float z1 = cBox.size().y / screenWindow.size().y;

				m_centreOfInterest = std::max( z0, z1 ) / tan( M_PI * m_fov->readable() / 360.0 ) + cBox.max.z +
					m_clippingPlanes->readable()[0];

				cameraMatrix.translate( V3f( 0.0f, 0.0f, m_centreOfInterest ) );
			}
			else
			{
				// orthographic. translate to front of box and set screen window
				// to frame the box, maintaining the aspect ratio of the screen window.
				m_centreOfInterest = cBox.max.z + m_clippingPlanes->readable()[0] + 0.1; // 0.1 is a fudge factor
				cameraMatrix.translate( V3f( 0.0f, 0.0f, m_centreOfInterest ) );

				float xScale = cBox.size().x / screenWindow.size().x;
				float yScale = cBox.size().y / screenWindow.size().y;
				float scale = std::max( xScale, yScale );

				V2f newSize = screenWindow.size() * scale;
				screenWindow.min.x = cBox.center().x - newSize.x / 2.0f;
				screenWindow.min.y = cBox.center().y - newSize.y / 2.0f;
				screenWindow.max.x = cBox.center().x + newSize.x / 2.0f;
				screenWindow.max.y = cBox.center().y + newSize.y / 2.0f;
			}

			m_transform = cameraMatrix;
			m_screenWindow->writable() = screenWindow;

		}

		/// Computes the points on the near and far clipping planes that correspond
		/// with the specified raster position. Points are computed in world space.
		void unproject( const Imath::V2f rasterPosition, Imath::V3f &near, Imath::V3f &far ) const
		{
			V2f ndc = V2f( rasterPosition ) / m_resolution->readable();
			const Box2f &screenWindow = m_screenWindow->readable();
			V2f screen(
				lerp( screenWindow.min.x, screenWindow.max.x, ndc.x ),
				lerp( screenWindow.max.y, screenWindow.min.y, ndc.y )
			);

			const V2f &clippingPlanes = m_clippingPlanes->readable();
			if( m_projection->readable()=="perspective" )
			{
				float fov = m_fov->readable();
				float d = tan( degreesToRadians( fov / 2.0f ) ); // camera x coordinate at screen window x==1
				V3f camera( screen.x * d, screen.y * d, -1.0f );
				near = camera * clippingPlanes[0];
				far = camera * clippingPlanes[1];
			}
			else
			{
				near = V3f( screen.x, screen.y, -clippingPlanes[0] );
				far = V3f( screen.x, screen.y, -clippingPlanes[1] );
			}

			near = near * m_transform;
			far = far * m_transform;
		}

		/// Projects the point in world space into a raster space position.
		Imath::V2f project( const Imath::V3f &worldPosition ) const
		{
			M44f inverseCameraMatrix = m_transform.inverse();
			V3f cameraPosition = worldPosition * inverseCameraMatrix;

			const V2i &resolution = m_resolution->readable();
			const Box2f &screenWindow = m_screenWindow->readable();
			if( m_projection->readable() == "perspective" )
			{
				V3f screenPosition = cameraPosition / cameraPosition.z;
				float fov = m_fov->readable();
				float d = tan( degreesToRadians( fov / 2.0f ) ); // camera x coordinate at screen window x==1
				screenPosition /= d;
				V2f ndcPosition(
					lerpfactor( screenPosition.x, screenWindow.max.x, screenWindow.min.x ),
					lerpfactor( screenPosition.y, screenWindow.min.y, screenWindow.max.y )
				);
				return V2f(
					ndcPosition.x * resolution.x,
					ndcPosition.y * resolution.y
				);
			}
			else
			{
				V2f ndcPosition(
					lerpfactor( cameraPosition.x, screenWindow.min.x, screenWindow.max.x ),
					lerpfactor( cameraPosition.y, screenWindow.max.y, screenWindow.min.y )
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
			Dolly
		};

		/// Starts a motion of the specified type.
		void motionStart( MotionType motion, const Imath::V2f &startPosition )
		{
			m_motionType = motion;
			m_motionStart = startPosition;
			m_motionMatrix = m_transform;
			m_motionScreenWindow = m_screenWindow->readable();
			m_motionCentreOfInterest = m_centreOfInterest;
		}

		/// Updates the camera position based on a changed mouse position. Can only
		/// be called after motionStart() and before motionEnd().
		void motionUpdate( const Imath::V2f &newPosition )
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
					dolly( newPosition );
					break;
				default :
					throw Exception( "CameraController not in motion." );
			}
		}

		/// End the current motion, ready to call motionStart() again if required.
		void motionEnd( const Imath::V2f &endPosition )
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
					dolly( endPosition );
					break;
				default :
					break;
			}
			m_motionType = None;
		}

	private:

		void track( const Imath::V2f &p )
		{
			V2i resolution = m_resolution->readable();
			Box2f screenWindow = m_screenWindow->readable();

			V2f d = p - m_motionStart;
			V3f translate( 0.0f );
			translate.x = -screenWindow.size().x * d.x/(float)resolution.x;
			translate.y = screenWindow.size().y * d.y/(float)resolution.y;
			if( m_projection->readable()=="perspective" && m_fov )
			{
				translate *= tan( M_PI * m_fov->readable() / 360.0f ) * (float)m_centreOfInterest;
			}
			M44f t = m_motionMatrix;
			t.translate( translate );
			m_transform = t;
		}

		void tumble( const Imath::V2f &p )
		{
			V2f d = p - m_motionStart;

			V3f centreOfInterestInWorld = V3f( 0, 0, -m_centreOfInterest ) * m_motionMatrix;
			V3f xAxisInWorld = V3f( 1, 0, 0 );
			m_motionMatrix.multDirMatrix( xAxisInWorld, xAxisInWorld );
			xAxisInWorld.normalize();

			M44f t;
			t.translate( centreOfInterestInWorld );

				t.rotate( V3f( 0, -d.x / 100.0f, 0 ) );

				M44f xRotate;
				xRotate.setAxisAngle( xAxisInWorld, -d.y / 100.0f );

				t = xRotate * t;

			t.translate( -centreOfInterestInWorld );

			m_transform = m_motionMatrix * t;
		}

		void dolly( const Imath::V2f &p )
		{
			V2i resolution = m_resolution->readable();
			V2f dv = V2f( (p - m_motionStart) ) / resolution;
			float d = dv.x - dv.y;

			if( m_projection->readable()=="perspective" )
			{
				// perspective
				m_centreOfInterest = m_motionCentreOfInterest * expf( -1.9f * d );

				M44f t = m_motionMatrix;
				t.translate( V3f( 0, 0, m_centreOfInterest - m_motionCentreOfInterest ) );

				m_transform = t;
			}
			else
			{
				// orthographic
				Box2f screenWindow = m_motionScreenWindow;

				V2f centreNDC = V2f( m_motionStart ) / resolution;
				V2f centre(
					lerp( screenWindow.min.x, screenWindow.max.x, centreNDC.x ),
					lerp( screenWindow.max.y, screenWindow.min.y, centreNDC.y )
				);

				float newWidth = m_motionScreenWindow.size().x * expf( -1.9f * d );
				newWidth = std::max( newWidth, 0.01f );

				float scale = newWidth / screenWindow.size().x;

				screenWindow.min = (screenWindow.min - centre) * scale + centre;
				screenWindow.max = (screenWindow.max - centre) * scale + centre;
				m_screenWindow->writable() = screenWindow;
			}
		}

		// Parts of the camera we manipulate
		IECore::CameraPtr m_camera;
		V2iDataPtr m_resolution;
		Box2fDataPtr m_screenWindow;
		ConstStringDataPtr m_projection;
		ConstFloatDataPtr m_fov;
		ConstV2fDataPtr m_clippingPlanes;
		float m_centreOfInterest;
		M44f m_transform;

		// Motion state
		MotionType m_motionType;
		Imath::V2f m_motionStart;
		Imath::M44f m_motionMatrix;
		float m_motionCentreOfInterest;
		Imath::Box2f m_motionScreenWindow;

};

//////////////////////////////////////////////////////////////////////////
// ViewportGadget
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( ViewportGadget );

ViewportGadget::ViewportGadget( GadgetPtr primaryChild )
	: Gadget(),
	  m_cameraController( new CameraController( new IECore::Camera ) ),
	  m_cameraInMotion( false ),
	  m_cameraEditable( true ),
	  m_dragTracking( false )
{
	// Viewport visibility is managed by GadgetWidgets,
	setVisible( false );

	setPrimaryChild( primaryChild );

	childRemovedSignal().connect( boost::bind( &ViewportGadget::childRemoved, this, ::_1, ::_2 ) );

	buttonPressSignal().connect( boost::bind( &ViewportGadget::buttonPress, this, ::_1,  ::_2 ) );
	buttonReleaseSignal().connect( boost::bind( &ViewportGadget::buttonRelease, this, ::_1,  ::_2 ) );
	buttonDoubleClickSignal().connect( boost::bind( &ViewportGadget::buttonDoubleClick, this, ::_1,  ::_2 ) );
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

	std::vector<GadgetPtr> gadgets;
	gadgetsAt( V2f( line.p0.x, line.p0.y ), gadgets );
	for( std::vector<GadgetPtr>::const_iterator it = gadgets.begin(), eIt = gadgets.end(); it != eIt; it++ )
	{
		Gadget *gadget = it->get();
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
	return m_cameraController->getResolution();
}

void ViewportGadget::setViewport( const Imath::V2i &viewport )
{
	if( viewport == m_cameraController->getResolution() )
	{
		return;
	}

	CameraController::ScreenWindowAdjustment adjustment = CameraController::ScaleScreenWindow;
	if( const StringData *projection = getCamera()->parametersData()->member<StringData>( "projection" ) )
	{
		if( projection->readable() == "orthographic" )
		{
			adjustment = CameraController::CropScreenWindow;
		}
	}

	m_cameraController->setResolution( viewport, adjustment );

	m_viewportChangedSignal( this );
}

ViewportGadget::UnarySignal &ViewportGadget::viewportChangedSignal()
{
	return m_viewportChangedSignal;
}

const IECore::Camera *ViewportGadget::getCamera() const
{
	return m_cameraController->getCamera();
}

void ViewportGadget::setCamera( const IECore::Camera *camera )
{
	if( m_cameraController->getCamera()->isEqualTo( camera ) )
	{
		return;
	}
	// Remember the viewport size
	const V2i viewport = getViewport();
	// Because the incoming camera resolution might not be right
	m_cameraController->setCamera( camera->copy() );
	// So we must reset the viewport to update the camera
	setViewport( viewport );
	m_cameraChangedSignal( this );
}

const Imath::M44f &ViewportGadget::getCameraTransform() const
{
	return m_cameraController->getTransform();
}

void ViewportGadget::setCameraTransform( const Imath::M44f &transform )
{
	if( transform == getCameraTransform() )
	{
		return;
	}
	m_cameraController->setTransform( transform );
	m_cameraChangedSignal( this );
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

void ViewportGadget::frame( const Imath::Box3f &box )
{
	m_cameraController->frame( box );
	m_cameraChangedSignal( this );
	requestRender();
}

void ViewportGadget::frame( const Imath::Box3f &box, const Imath::V3f &viewDirection,
	const Imath::V3f &upVector )
{
	m_cameraController->frame( box, viewDirection, upVector );
	m_cameraChangedSignal( this );
	requestRender();
}

void ViewportGadget::setDragTracking( bool dragTracking )
{
	m_dragTracking = dragTracking;
}

bool ViewportGadget::getDragTracking() const
{
	return m_dragTracking;
}

void ViewportGadget::gadgetsAt( const Imath::V2f &rasterPosition, std::vector<GadgetPtr> &gadgets ) const
{
	std::vector<HitRecord> selection;
	{
		SelectionScope selectionScope( this, rasterPosition, selection, IECoreGL::Selector::IDRender );
		const Style *s = style();
		s->bind();

		for( Layer layer = Layer::Back; layer < Layer::Last; ++layer )
		{
			Gadget::doRenderLayer( layer, s );
		}
	}

	for( std::vector<HitRecord>::const_iterator it = selection.begin(); it!= selection.end(); it++ )
	{
		GadgetPtr gadget = Gadget::select( it->name );
		if( gadget )
		{
			gadgets.push_back( gadget );
		}
	}

	if( !gadgets.size() )
	{
		if( const Gadget *g = getPrimaryChild() )
		{
			gadgets.push_back( const_cast<Gadget *>( g ) );
		}
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

ViewportGadget::UnarySignal &ViewportGadget::preRenderSignal()
{
	return m_preRenderSignal;
}

void ViewportGadget::doRenderLayer( Layer layer, const Style *style ) const
{
	// \todo Camera setup is needed for each layer. Maybe we should cache the
	// converted camera, though, and only do the conversion when we hit the Back
	// layer.
	IECoreGL::ToGLConverterPtr converter = new IECoreGL::ToGLCameraConverter(
		m_cameraController->getCamera()
	);
	IECoreGL::CameraPtr camera = boost::static_pointer_cast<IECoreGL::Camera>( converter->convert() );
	camera->setTransform( getCameraTransform() );
	if( m_cameraController->getCamera()->getTransform() )
	{
		IECore::msg( IECore::Msg::Warning, "ViewportGadget", "Camera has unexpected transform" );
	}
	camera->render( nullptr );

	if( layer == Layer::Back )
	{
		glClearColor( 0.3f, 0.3f, 0.3f, 0.0f );
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
	}

	Gadget::doRenderLayer( layer, style );
}

void ViewportGadget::childRemoved( GraphComponent *parent, GraphComponent *child )
{
	const Gadget *childGadget = static_cast<const Gadget *>( child );

	if( childGadget == m_lastButtonPressGadget || childGadget->isAncestorOf( m_lastButtonPressGadget.get() ) )
	{
		m_lastButtonPressGadget = nullptr;
	}

	if( childGadget == m_gadgetUnderMouse || childGadget->isAncestorOf( m_gadgetUnderMouse.get() ) )
	{
		m_gadgetUnderMouse = nullptr;
	}
}

bool ViewportGadget::buttonPress( GadgetPtr gadget, const ButtonEvent &event )
{
	if( event.modifiers == ModifiableEvent::Alt )
	{
		// accept press so we get a dragBegin opportunity for camera movement
		return true;
	}

	std::vector<GadgetPtr> gadgets;
	gadgetsAt( V2f( event.line.p0.x, event.line.p0.y ), gadgets );

	GadgetPtr handler;
	m_lastButtonPressGadget = nullptr;
	bool result = dispatchEvent( gadgets, &Gadget::buttonPressSignal, event, handler );
	if( result )
	{
		m_lastButtonPressGadget = handler;
		return true;
	}

	if ( event.buttons == ButtonEvent::Middle && event.modifiers == ModifiableEvent::None )
	{
		// accept press so we get a dragBegin opportunity for camera movement
		return true;
	}

	return false;
}

bool ViewportGadget::buttonRelease( GadgetPtr gadget, const ButtonEvent &event )
{
	bool result = false;
	if( m_lastButtonPressGadget )
	{
		result = dispatchEvent( m_lastButtonPressGadget, &Gadget::buttonReleaseSignal, event );
	}

	m_lastButtonPressGadget = nullptr;
	return result;
}

bool ViewportGadget::buttonDoubleClick( GadgetPtr gadget, const ButtonEvent &event )
{
	/// \todo Implement me. I'm not sure who this event should go to - probably
	/// the last button press gadget, but we erased that in buttonRelease.
	return false;
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
			lowestUnchanged = oldGadgetUnderMouse->commonAncestor<Gadget>( newGadgetUnderMouse.get() );
		}
	}

	// emit leave events, innermost first
	if( oldGadgetUnderMouse )
	{
		GadgetPtr leaveTarget = oldGadgetUnderMouse;
		while( leaveTarget != lowestUnchanged )
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
		while( enterTarget != lowestUnchanged )
		{
			enterTargets.push_back( enterTarget );
			enterTarget = enterTarget->parent<Gadget>();
		}
		for( std::vector<GadgetPtr>::const_reverse_iterator it = enterTargets.rbegin(); it!=enterTargets.rend(); it++ )
		{
			dispatchEvent( *it, &Gadget::enterSignal, event );
		}
	}
};

bool ViewportGadget::mouseMove( GadgetPtr gadget, const ButtonEvent &event )
{
	// find the gadget under the mouse
	std::vector<GadgetPtr> gadgets;
	gadgetsAt( V2f( event.line.p0.x, event.line.p0.y ), gadgets );

	GadgetPtr newGadgetUnderMouse;
	if( gadgets.size() )
	{
		newGadgetUnderMouse = gadgets[0];
	}

	if( m_gadgetUnderMouse != newGadgetUnderMouse )
	{
		emitEnterLeaveEvents( newGadgetUnderMouse, m_gadgetUnderMouse, event );
		m_gadgetUnderMouse = newGadgetUnderMouse;
	}

	// pass the signal through
	if( m_gadgetUnderMouse )
	{
		std::vector<GadgetPtr> gadgetUnderMouse( 1, m_gadgetUnderMouse );
		GadgetPtr handler;
		return dispatchEvent( gadgetUnderMouse, &Gadget::mouseMoveSignal, event, handler );
	}

	return false;
}

IECore::RunTimeTypedPtr ViewportGadget::dragBegin( GadgetPtr gadget, const DragDropEvent &event )
{
	m_dragTrackingThreshold = limits<float>::max();

	if ( !(event.modifiers == ModifiableEvent::Alt) && m_lastButtonPressGadget )
	{
		// see if a child gadget would like to start a drag
		RunTimeTypedPtr data = dispatchEvent( m_lastButtonPressGadget, &Gadget::dragBeginSignal, event );
		if( data )
		{
			const_cast<DragDropEvent &>( event ).sourceGadget = m_lastButtonPressGadget;

			return data;
		}
	}

	if ( event.modifiers == ModifiableEvent::Alt || ( event.buttons == ButtonEvent::Middle && event.modifiers == ModifiableEvent::None ) )
	{
		// start camera motion

		CameraController::MotionType motionType = CameraController::None;
		switch( event.buttons )
		{
			case ButtonEvent::Left :
				motionType = CameraController::Tumble;
				break;
			case ButtonEvent::Middle :
				motionType = CameraController::Track;
				break;
			case ButtonEvent::Right :
				motionType = CameraController::Dolly;
				break;
			default :
				motionType = CameraController::None;
				break;
		}

		const StringData *projection = getCamera()->parametersData()->member<StringData>( "projection" );
		if( motionType == CameraController::Tumble && ( !projection || projection->readable()=="orthographic" ) )
		{
			motionType = CameraController::Track;
		}

		if( motionType )
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
				m_cameraController->motionStart( motionType, V2i( (int)event.line.p1.x, (int)event.line.p1.y ) );
			}

			// we have to return something to start the drag, but we return something that
			// noone else will accept to make sure we keep the drag to ourself.
			return IECore::NullObject::defaultNullObject();
		}
		else
		{
			return nullptr;
		}
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
		std::vector<GadgetPtr> gadgets;
		gadgetsAt( V2f( event.line.p0.x, event.line.p0.y ), gadgets );

		GadgetPtr dragDestination = updatedDragDestination( gadgets, event );
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
	if( m_cameraInMotion )
	{
		if( getCameraEditable() )
		{
			m_cameraController->motionUpdate( V2i( (int)event.line.p1.x, (int)event.line.p1.y ) );
			m_cameraChangedSignal( this );
			requestRender();
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
			std::vector<GadgetPtr> gadgets;
			gadgetsAt( V2f( event.line.p0.x, event.line.p0.y ), gadgets );

			// update drag destination
			GadgetPtr updatedDestination = updatedDragDestination( gadgets, event );
			if( updatedDestination != event.destinationGadget )
			{
				GadgetPtr previousDestination = event.destinationGadget;
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
			return dispatchEvent( event.destinationGadget, &Gadget::dragMoveSignal, event );
		}
	}

	return false;
}

static double currentTime()
{
	timeval t;
	gettimeofday( &t, nullptr ) ;
	return (double)t.tv_sec + (double)t.tv_usec / 1000000.0;
}

void ViewportGadget::trackDrag( const DragDropEvent &event )
{
	// early out if tracking is off for any reason, or
	// the drag didn't originate from within the viewport.

	if(
		!getDragTracking() ||
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
		offset = V2f( offset3.x, offset3.y );
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
			m_dragTrackingTime = currentTime();
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
	double now = currentTime();
	float duration = (float)(now - m_dragTrackingTime);

	m_cameraController->motionStart( CameraController::Track, V2f( 0 ) );
	m_cameraController->motionEnd( m_dragTrackingVelocity * duration * 20.0f );

	m_dragTrackingTime = now;

	// although the mouse hasn't moved, moving the camera will have moved it
	// relative to our child gadgets, so we fake a move event to update any
	// visual representation of the drag.
	dragMove( this, m_dragTrackingEvent );

	m_cameraChangedSignal( this );
	requestRender();
}

GadgetPtr ViewportGadget::updatedDragDestination( std::vector<GadgetPtr> &gadgets, const DragDropEvent &event )
{
	for( std::vector<GadgetPtr>::const_iterator it = gadgets.begin(), eIt = gadgets.end(); it != eIt; it++ )
	{
		GadgetPtr gadget = *it;
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
		return event.destinationGadget;
	}

	// and if that's not the case then give the drag source another chance
	// to become the destination again.
	if( event.sourceGadget )
	{
		if( dispatchEvent( event.sourceGadget, &Gadget::dragEnterSignal, event ) )
		{
			return event.sourceGadget;
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
		dispatchEvent( previousDestination, &Gadget::dragLeaveSignal, event );
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
			return dispatchEvent( event.destinationGadget, &Gadget::dropSignal, event );
		}
		else
		{
			return false;
		}
	}
}

bool ViewportGadget::dragEnd( GadgetPtr gadget, const DragDropEvent &event )
{
	if( m_cameraInMotion )
	{
		m_cameraInMotion = false;
		if( getCameraEditable() )
		{
			m_cameraController->motionEnd( V2i( (int)event.line.p1.x, (int)event.line.p1.y ) );
			m_cameraChangedSignal( this );
			requestRender();
		}
		return true;
	}
	else
	{
		m_dragTrackingIdleConnection.disconnect();
		if( event.sourceGadget )
		{
			return dispatchEvent( event.sourceGadget, &Gadget::dragEndSignal, event );
		}
	}
	return false;
}

bool ViewportGadget::wheel( GadgetPtr gadget, const ButtonEvent &event )
{
	if( m_cameraInMotion )
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
	position.x += event.wheelRotation * getViewport().x / 140.0f;
	m_cameraController->motionUpdate( position );
	m_cameraController->motionEnd( position );

	m_cameraChangedSignal( this );
	requestRender();

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
typename Signal::result_type ViewportGadget::dispatchEvent( std::vector<GadgetPtr> &gadgets, Signal &(Gadget::*signalGetter)(), const Event &event, GadgetPtr &handler )
{
	for( std::vector<GadgetPtr>::const_iterator it = gadgets.begin(), eIt = gadgets.end(); it != eIt; it++ )
	{
		GadgetPtr gadget = *it;
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
typename Signal::result_type ViewportGadget::dispatchEvent( GadgetPtr gadget, Signal &(Gadget::*signalGetter)(), const Event &event )
{
	Event transformedEvent( event );
	eventToGadgetSpace( transformedEvent, gadget.get() );
	Signal &s = (gadget.get()->*signalGetter)();
	return s( gadget.get(), transformedEvent );
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

ViewportGadget::SelectionScope::SelectionScope( const ViewportGadget *viewportGadget, const Imath::V2f &rasterPosition, std::vector<IECoreGL::HitRecord> &selection, IECoreGL::Selector::Mode mode )
	:	m_selection( selection )
{
	begin( viewportGadget, rasterPosition, M44f(), mode );
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
	V2f viewport = viewportGadget->getViewport();
	Box2f ndcRegion( rasterRegion.min / viewport, rasterRegion.max / viewport );

	IECoreGL::ToGLConverterPtr converter = new IECoreGL::ToGLCameraConverter(
		viewportGadget->m_cameraController->getCamera()
	);
	IECoreGL::CameraPtr camera = boost::static_pointer_cast<IECoreGL::Camera>( converter->convert() );
	camera->setTransform( viewportGadget->getCameraTransform() );
	/// \todo It would be better to base this on whether we have a depth buffer or not, but
	/// we don't have access to that information right now.
	m_depthSort = camera->isInstanceOf( IECoreGL::PerspectiveCamera::staticTypeId() );
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
