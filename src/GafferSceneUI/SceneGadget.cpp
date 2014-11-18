//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

#include "tbb/task.h"

#include "boost/bind.hpp"
#include "boost/algorithm/string/predicate.hpp"

#include "IECore/Light.h"
#include "IECore/CoordinateSystem.h"
#include "IECore/VisibleRenderable.h"
#include "IECore/AngleConversion.h"
#include "IECore/CurvesPrimitive.h"

#include "IECoreGL/Renderable.h"
#include "IECoreGL/CachedConverter.h"
#include "IECoreGL/Primitive.h"
#include "IECoreGL/Selector.h"
#include "IECoreGL/CurvesPrimitive.h"
#include "IECoreGL/Group.h"

#include "Gaffer/Node.h"

#include "GafferUI/ViewportGadget.h"

#include "GafferSceneUI/SceneGadget.h"

using namespace std;
using namespace Imath;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferScene;
using namespace GafferSceneUI;

//////////////////////////////////////////////////////////////////////////
// IECore::Object -> IECoreGL::Renderable conversion
// \todo Expose a registry mechanism to allow this to be customised
// for different types.
//////////////////////////////////////////////////////////////////////////

namespace
{

IECoreGL::ConstRenderablePtr cameraToRenderable( const IECore::Camera *camera )
{
	IECore::CameraPtr fullCamera = camera->copy();
	fullCamera->addStandardParameters();

	IECoreGL::GroupPtr group = new IECoreGL::Group();
	group->getState()->add( new IECoreGL::Primitive::DrawWireframe( true ) );
	group->getState()->add( new IECoreGL::Primitive::DrawSolid( false ) );
	group->getState()->add( new IECoreGL::CurvesPrimitive::UseGLLines( true ) );
	group->getState()->add( new IECoreGL::WireframeColorStateComponent( Color4f( 0, 0.25, 0, 1 ) ) );

	IECore::V3fVectorDataPtr pData = new IECore::V3fVectorData;
	IECore::IntVectorDataPtr vertsPerCurveData = new IECore::IntVectorData;
	vector<V3f> &p = pData->writable();
	vector<int> &vertsPerCurve = vertsPerCurveData->writable();

	// box for the camera body

	const Box3f b( V3f( -0.5, -0.5, 0 ), V3f( 0.5, 0.5, 2.0 ) );

	vertsPerCurve.push_back( 5 );
	p.push_back( b.min );
	p.push_back( V3f( b.max.x, b.min.y, b.min.z ) );
	p.push_back( V3f( b.max.x, b.min.y, b.max.z ) );
	p.push_back( V3f( b.min.x, b.min.y, b.max.z ) );
	p.push_back( b.min );

	vertsPerCurve.push_back( 5 );
	p.push_back( V3f( b.min.x, b.max.y, b.min.z ) );
	p.push_back( V3f( b.max.x, b.max.y, b.min.z ) );
	p.push_back( V3f( b.max.x, b.max.y, b.max.z ) );
	p.push_back( V3f( b.min.x, b.max.y, b.max.z ) );
	p.push_back( V3f( b.min.x, b.max.y, b.min.z ) );

	vertsPerCurve.push_back( 2 );
	p.push_back( b.min );
	p.push_back( V3f( b.min.x, b.max.y, b.min.z ) );

	vertsPerCurve.push_back( 2 );
	p.push_back( V3f( b.max.x, b.min.y, b.min.z ) );
	p.push_back( V3f( b.max.x, b.max.y, b.min.z ) );

	vertsPerCurve.push_back( 2 );
	p.push_back( V3f( b.max.x, b.min.y, b.max.z ) );
	p.push_back( V3f( b.max.x, b.max.y, b.max.z ) );

	vertsPerCurve.push_back( 2 );
	p.push_back( V3f( b.min.x, b.min.y, b.max.z ) );
	p.push_back( V3f( b.min.x, b.max.y, b.max.z ) );

	// frustum

	const std::string &projection = fullCamera->parametersData()->member<IECore::StringData>( "projection" )->readable();
	const Box2f &screenWindow = fullCamera->parametersData()->member<IECore::Box2fData>( "screenWindow" )->readable();
	/// \todo When we're drawing the camera by some means other than creating a primitive for it,
	/// use the actual clippings planes. Right now that's not a good idea as it results in /huge/
	/// framing bounds when the viewer frames a selected camera.
	V2f clippingPlanes( 0, 5 );

	Box2f near( screenWindow );
	Box2f far( screenWindow );

	if( projection == "perspective" )
	{
		float fov = fullCamera->parametersData()->member<IECore::FloatData>( "projection:fov" )->readable();
		float d = tan( IECore::degreesToRadians( fov / 2.0f ) );
		near.min *= d * clippingPlanes[0];
		near.max *= d * clippingPlanes[0];
		far.min *= d * clippingPlanes[1];
		far.max *= d * clippingPlanes[1];
	}

	vertsPerCurve.push_back( 5 );
	p.push_back( V3f( near.min.x, near.min.y, -clippingPlanes[0] ) );
	p.push_back( V3f( near.max.x, near.min.y, -clippingPlanes[0] ) );
	p.push_back( V3f( near.max.x, near.max.y, -clippingPlanes[0] ) );
	p.push_back( V3f( near.min.x, near.max.y, -clippingPlanes[0] ) );
	p.push_back( V3f( near.min.x, near.min.y, -clippingPlanes[0] ) );

	vertsPerCurve.push_back( 5 );
	p.push_back( V3f( far.min.x, far.min.y, -clippingPlanes[1] ) );
	p.push_back( V3f( far.max.x, far.min.y, -clippingPlanes[1] ) );
	p.push_back( V3f( far.max.x, far.max.y, -clippingPlanes[1] ) );
	p.push_back( V3f( far.min.x, far.max.y, -clippingPlanes[1] ) );
	p.push_back( V3f( far.min.x, far.min.y, -clippingPlanes[1] ) );

	vertsPerCurve.push_back( 2 );
	p.push_back( V3f( near.min.x, near.min.y, -clippingPlanes[0] ) );
	p.push_back( V3f( far.min.x, far.min.y, -clippingPlanes[1] ) );

	vertsPerCurve.push_back( 2 );
	p.push_back( V3f( near.max.x, near.min.y, -clippingPlanes[0] ) );
	p.push_back( V3f( far.max.x, far.min.y, -clippingPlanes[1] ) );

	vertsPerCurve.push_back( 2 );
	p.push_back( V3f( near.max.x, near.max.y, -clippingPlanes[0] ) );
	p.push_back( V3f( far.max.x, far.max.y, -clippingPlanes[1] ) );

	vertsPerCurve.push_back( 2 );
	p.push_back( V3f( near.min.x, near.max.y, -clippingPlanes[0] ) );
	p.push_back( V3f( far.min.x, far.max.y, -clippingPlanes[1] ) );

	IECoreGL::CurvesPrimitivePtr curves = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), false, vertsPerCurveData );
	curves->addPrimitiveVariable( "P", IECore::PrimitiveVariable( IECore::PrimitiveVariable::Vertex, pData ) );
	group->addChild( curves );

	return group;
}

IECoreGL::ConstRenderablePtr lightToRenderable( const IECore::Light *light )
{
	static IECoreGL::GroupPtr group = NULL;
	if( !group )
	{
		group = new IECoreGL::Group();

		group->getState()->add( new IECoreGL::Primitive::DrawWireframe( true ) );
		group->getState()->add( new IECoreGL::Primitive::DrawSolid( false ) );
		group->getState()->add( new IECoreGL::CurvesPrimitive::UseGLLines( true ) );
		group->getState()->add( new IECoreGL::WireframeColorStateComponent( Color4f( 0.5, 0, 0, 1 ) ) );

		const float a = 0.5f;
		const float phi = 1.0f + sqrt( 5.0f ) / 2.0f;
		const float b = 1.0f / ( 2.0f * phi );

		// icosahedron points
		IECore::V3fVectorDataPtr pData = new IECore::V3fVectorData;
		vector<V3f> &p = pData->writable();
		p.resize( 24 );
		p[0] = V3f( 0, b, -a );
		p[2] = V3f( b, a, 0 );
		p[4] = V3f( -b, a, 0 );
		p[6] = V3f( 0, b, a );
		p[8] = V3f( 0, -b, a );
		p[10] = V3f( -a, 0, b );
		p[12] = V3f( 0, -b, -a );
		p[14] = V3f( a, 0, -b );
		p[16] = V3f( a, 0, b );
		p[18] = V3f( -a, 0, -b );
		p[20] = V3f( b, -a, 0 );
		p[22] = V3f( -b, -a, 0 );

		for( size_t i = 0; i<12; i++ )
		{
			p[i*2] = 2.0f * p[i*2].normalized();
			p[i*2+1] = V3f( 0 );
		}

		IECore::IntVectorDataPtr vertsPerCurve = new IECore::IntVectorData;
		vertsPerCurve->writable().resize( 12, 2 );

		IECoreGL::CurvesPrimitivePtr curves = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), false, vertsPerCurve );
		curves->addPrimitiveVariable( "P", IECore::PrimitiveVariable( IECore::PrimitiveVariable::Vertex, pData ) );

		group->addChild( curves );
	}

	return group;
}

IECoreGL::ConstRenderablePtr coordinateSystemToRenderable( const IECore::CoordinateSystem *coordinateSystem )
{
	static IECoreGL::GroupPtr group = NULL;
	if( !group )
	{
		group = new IECoreGL::Group();

		group->getState()->add( new IECoreGL::Primitive::DrawWireframe( true ) );
		group->getState()->add( new IECoreGL::Primitive::DrawSolid( false ) );
		group->getState()->add( new IECoreGL::CurvesPrimitive::UseGLLines( true ) );
		group->getState()->add( new IECoreGL::WireframeColorStateComponent( Color4f( 0.06, 0.2, 0.56, 1 ) ) );
		group->getState()->add( new IECoreGL::CurvesPrimitive::GLLineWidth( 2.0f ) );

		IECore::V3fVectorDataPtr pData = new IECore::V3fVectorData;
		vector<V3f> &p = pData->writable();
		p.reserve( 6 );
		p.push_back( V3f( 0 ) );
		p.push_back( V3f( 1, 0, 0 ) );
		p.push_back( V3f( 0 ) );
		p.push_back( V3f( 0, 1, 0 ) );
		p.push_back( V3f( 0 ) );
		p.push_back( V3f( 0, 0, 1 ) );

		IECore::IntVectorDataPtr vertsPerCurve = new IECore::IntVectorData;
		vertsPerCurve->writable().resize( 3, 2 );

		IECoreGL::CurvesPrimitivePtr curves = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), false, vertsPerCurve );
		curves->addPrimitiveVariable( "P", IECore::PrimitiveVariable( IECore::PrimitiveVariable::Vertex, pData ) );
		group->addChild( curves );
	}

	return group;
}

IECoreGL::ConstRenderablePtr visibleRenderableToRenderable( const IECore::VisibleRenderable *visibleRenderable )
{
	IECoreGL::GroupPtr group = new IECoreGL::Group();
	group->getState()->add( new IECoreGL::Primitive::DrawWireframe( true ) );
	group->getState()->add( new IECoreGL::Primitive::DrawSolid( false ) );
	group->getState()->add( new IECoreGL::CurvesPrimitive::UseGLLines( true ) );

	IECore::V3fVectorDataPtr pData = new IECore::V3fVectorData;
	IECore::IntVectorDataPtr vertsPerCurveData = new IECore::IntVectorData;
	vector<V3f> &p = pData->writable();
	vector<int> &vertsPerCurve = vertsPerCurveData->writable();

	// box representing the location of the renderable

	const Box3f b = visibleRenderable->bound();

	vertsPerCurve.push_back( 5 );
	p.push_back( b.min );
	p.push_back( V3f( b.max.x, b.min.y, b.min.z ) );
	p.push_back( V3f( b.max.x, b.min.y, b.max.z ) );
	p.push_back( V3f( b.min.x, b.min.y, b.max.z ) );
	p.push_back( b.min );

	vertsPerCurve.push_back( 5 );
	p.push_back( V3f( b.min.x, b.max.y, b.min.z ) );
	p.push_back( V3f( b.max.x, b.max.y, b.min.z ) );
	p.push_back( V3f( b.max.x, b.max.y, b.max.z ) );
	p.push_back( V3f( b.min.x, b.max.y, b.max.z ) );
	p.push_back( V3f( b.min.x, b.max.y, b.min.z ) );

	vertsPerCurve.push_back( 2 );
	p.push_back( b.min );
	p.push_back( V3f( b.min.x, b.max.y, b.min.z ) );

	vertsPerCurve.push_back( 2 );
	p.push_back( V3f( b.max.x, b.min.y, b.min.z ) );
	p.push_back( V3f( b.max.x, b.max.y, b.min.z ) );

	vertsPerCurve.push_back( 2 );
	p.push_back( V3f( b.max.x, b.min.y, b.max.z ) );
	p.push_back( V3f( b.max.x, b.max.y, b.max.z ) );

	vertsPerCurve.push_back( 2 );
	p.push_back( V3f( b.min.x, b.min.y, b.max.z ) );
	p.push_back( V3f( b.min.x, b.max.y, b.max.z ) );

	IECoreGL::CurvesPrimitivePtr curves = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), false, vertsPerCurveData );
	curves->addPrimitiveVariable( "P", IECore::PrimitiveVariable( IECore::PrimitiveVariable::Vertex, pData ) );
	group->addChild( curves );

	return group;
}

IECoreGL::ConstRenderablePtr objectToRenderable( const IECore::Object *object )
{
	switch( object->typeId() )
	{
		case IECore::CameraTypeId :
			return cameraToRenderable( static_cast<const IECore::Camera *>( object ) );
		case IECore::LightTypeId :
			return lightToRenderable( static_cast<const IECore::Light *>( object ) );
		case IECore::CoordinateSystemTypeId :
			return coordinateSystemToRenderable( static_cast<const IECore::CoordinateSystem *>( object ) );
		case IECore::ExternalProceduralTypeId :
			return visibleRenderableToRenderable( static_cast<const IECore::VisibleRenderable *>( object ) );
		default :
			try
			{
				IECore::ConstRunTimeTypedPtr glObject = IECoreGL::CachedConverter::defaultCachedConverter()->convert( object );
				return IECore::runTimeCast<const IECoreGL::Renderable>( glObject.get() );
			}
			catch( ... )
			{
				return NULL;
			}
	}
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// SceneGraph implementation
//////////////////////////////////////////////////////////////////////////

class SceneGadget::SceneGraph
{

	public :

		SceneGraph()
			:	m_selected( false ), m_visible( true ), m_expanded( false )
		{
		}

		~SceneGraph()
		{
			clearChildren();
		}

		void render( IECoreGL::State *currentState, IECoreGL::Selector *selector = NULL ) const
		{
			if( !m_visible )
			{
				return;
			}

			const bool haveTransform = m_transform != M44f();
			if( haveTransform )
			{
				glPushMatrix();
				glMultMatrixf( m_transform.getValue() );
			}

				{
					IECoreGL::State::ScopedBinding scope( *m_state, *currentState );
					IECoreGL::State::ScopedBinding selectionScope( selectionState(), *currentState, m_selected );

					if( selector )
					{
						m_selectionId = selector->loadName();
					}

					if( m_renderable )
					{
						m_renderable->render( currentState );
					}

					if( m_boundRenderable )
					{
						IECoreGL::State::ScopedBinding wireframeScope( wireframeState(), *currentState );
						m_boundRenderable->render( currentState );
					}

					for( std::vector<SceneGraph *>::const_iterator it = m_children.begin(), eIt = m_children.end(); it != eIt; ++it )
					{
						(*it)->render( currentState, selector );
					}
				}

			if( haveTransform )
			{
				glPopMatrix();
			}
		}

		void applySelection( const PathMatcher &selection )
		{
			ScenePlug::ScenePath rootPath;
			applySelectionWalk( selection, rootPath, true );
		}

		bool pathFromSelectionId( GLuint selectionId, ScenePlug::ScenePath &path ) const
		{
			path.clear();
			const bool result = pathFromSelectionIdWalk( selectionId, path );
			std::reverse( path.begin(), path.end() );
			return result;
		}

		const Box3f &bound() const
		{
			return m_bound;
		}

		Box3f selectionBound() const
		{
			if( m_selected )
			{
				return m_bound;
			}
			else
			{
				Box3f childSelectionBound;
				for( std::vector<SceneGraph *>::const_iterator it = m_children.begin(), eIt = m_children.end(); it != eIt; ++it )
				{
					const Box3f childBound = transform( (*it)->selectionBound(), (*it)->m_transform );
					childSelectionBound.extendBy( childBound );
				}
				return childSelectionBound;
			}
		}

	private :

		friend class UpdateTask;

		void clearChildren()
		{
			for( std::vector<SceneGraph *>::const_iterator it = m_children.begin(), eIt = m_children.end(); it != eIt; ++it )
			{
				delete *it;
			}
			m_children.clear();
		}

		void applySelectionWalk( const PathMatcher &selection, const ScenePlug::ScenePath &path, bool check )
		{
			const unsigned m = check ? selection.match( path ) : 0;

			m_selected = m & Filter::ExactMatch;

			ScenePlug::ScenePath childPath = path;
			childPath.push_back( IECore::InternedString() ); // space for the child name
			for( std::vector<SceneGraph *>::const_iterator it = m_children.begin(), eIt = m_children.end(); it != eIt; ++it )
			{
				childPath.back() = (*it)->m_name;
				(*it)->applySelectionWalk( selection, childPath, m & Filter::DescendantMatch );
			}
		}

		bool pathFromSelectionIdWalk( GLuint selectionId, ScenePlug::ScenePath &path ) const
		{
			if( m_selectionId == selectionId )
			{
				path.push_back( m_name );
				return true;
			}
			else
			{
				for( std::vector<SceneGraph *>::const_iterator it = m_children.begin(), eIt = m_children.end(); it != eIt; ++it )
				{
					/// \todo Should be able to prune recursion based on knowledge that child
					/// selection ids are always greater than parent selection ids.
					if( (*it)->pathFromSelectionIdWalk( selectionId, path ) )
					{
						if( m_name != IECore::InternedString() )
						{
							path.push_back( m_name );
						}
						return true;
					}
				}
			}

			return false;
		}

		static const IECoreGL::State &selectionState()
		{
			static IECoreGL::StatePtr s;
			if( !s )
			{
				s = new IECoreGL::State( false );
				s->add( new IECoreGL::Primitive::DrawWireframe( true ), /* override = */ true );
				s->add( new IECoreGL::WireframeColorStateComponent( Color4f( 0.466f, 0.612f, 0.741f, 1.0f ) ), /* override = */ true );
			}
			return *s;
		}

		static const IECoreGL::State &wireframeState()
		{
			static IECoreGL::StatePtr s;
			if( !s )
			{
				s = new IECoreGL::State( false );
				s->add( new IECoreGL::Primitive::DrawWireframe( true ), /* override = */ true );
				s->add( new IECoreGL::Primitive::DrawSolid( false ), /* override = */ true );
				s->add( new IECoreGL::CurvesPrimitive::UseGLLines( true ), /* override = */ true );
			}
			return *s;
		}

		Imath::Box3f m_bound;
		Imath::M44f m_transform;
		IECore::InternedString m_name;
		IECoreGL::ConstStatePtr m_state;
		IECoreGL::ConstRenderablePtr m_renderable;
		IECoreGL::ConstRenderablePtr m_boundRenderable;
		std::vector<SceneGraph *> m_children;
		mutable GLuint m_selectionId;
		bool m_selected;
		bool m_visible;
		bool m_expanded;

		IECore::MurmurHash m_objectHash;

};

class SceneGadget::UpdateTask : public tbb::task
{

	public :

		enum DirtyFlags
		{
			NothingDirty = 0,
			BoundDirty = 1,
			TransformDirty = 2,
			AttributesDirty = 4,
			ObjectDirty = 8,
			ChildNamesDirty = 16,
			ExpansionDirty = 32,
			AllDirty = BoundDirty | TransformDirty | AttributesDirty | ObjectDirty | ChildNamesDirty | ExpansionDirty
		};

		UpdateTask( const SceneGadget *sceneGadget, SceneGraph *sceneGraph, unsigned dirtyFlags, const ScenePlug::ScenePath &scenePath )
			:	m_sceneGadget( sceneGadget ),
				m_sceneGraph( sceneGraph ),
				m_dirtyFlags( dirtyFlags ),
				m_scenePath( scenePath )
		{
		}

		virtual task *execute()
		{
			ContextPtr context = new Context( *m_sceneGadget->m_context, Context::Borrowed );
			context->set( ScenePlug::scenePathContextName, m_scenePath );
			Context::Scope scopedContext( context.get() );

			// Update attributes, and compute visibility.

			const bool previouslyVisible = m_sceneGraph->m_visible;
			if( m_dirtyFlags & AttributesDirty )
			{
				IECore::ConstCompoundObjectPtr attributes = m_sceneGadget->m_scene->attributesPlug()->getValue();
				const IECore::BoolData *visibilityData = attributes->member<IECore::BoolData>( "scene:visible" );
				m_sceneGraph->m_visible = visibilityData ? visibilityData->readable() : true;

				IECore::ConstRunTimeTypedPtr glState = IECoreGL::CachedConverter::defaultCachedConverter()->convert( attributes.get() );
				m_sceneGraph->m_state = IECore::runTimeCast<const IECoreGL::State>( glState );
			}

			if( !m_sceneGraph->m_visible )
			{
				// No need to update further since we're not visible.
				return NULL;
			}
			else if( !previouslyVisible )
			{
				// We didn't perform any updates when we were invisible,
				// so we need to update everything now.
				m_dirtyFlags = AllDirty;
			}

			// Update the object - converting it into an IECoreGL::Renderable

			if( m_dirtyFlags & ObjectDirty )
			{
				IECore::MurmurHash objectHash = m_sceneGadget->m_scene->objectPlug()->hash();
				if( objectHash != m_sceneGraph->m_objectHash )
				{
					IECore::ConstObjectPtr object = m_sceneGadget->m_scene->objectPlug()->getValue( &objectHash );
					m_sceneGraph->m_renderable = NULL;
					if( !object->isInstanceOf( IECore::NullObjectTypeId ) )
					{
						m_sceneGraph->m_renderable = objectToRenderable( object.get() );
					}
					m_sceneGraph->m_objectHash = objectHash;
				}
			}

			// Update the transform and bound

			if( m_dirtyFlags & TransformDirty )
			{
				m_sceneGraph->m_transform = m_sceneGadget->m_scene->transformPlug()->getValue();
			}

			m_sceneGraph->m_bound = m_sceneGraph->m_renderable ? m_sceneGraph->m_renderable->bound() : Box3f();

			// Update the expansion state

			const bool previouslyExpanded = m_sceneGraph->m_expanded;
			if( m_dirtyFlags & ExpansionDirty )
			{
				m_sceneGraph->m_expanded = m_sceneGadget->m_minimumExpansionDepth >= m_scenePath.size();
				if( !m_sceneGraph->m_expanded )
				{
					m_sceneGraph->m_expanded = m_sceneGadget->m_expandedPaths->readable().match( m_scenePath ) & Filter::ExactMatch;
				}
			}

			// If we're not expanded, then we can early out after creating a bounding box.

			m_sceneGraph->m_boundRenderable = NULL;
			if( !m_sceneGraph->m_expanded )
			{
				// We're not expanded, so we early out before updating the children.
				// We do however need to see if we have any children, and arrange to
				// draw their bounding box if we do.
				bool haveChildren = m_sceneGraph->m_children.size();
				if( m_dirtyFlags & ChildNamesDirty || !previouslyExpanded )
				{
					IECore::ConstInternedStringVectorDataPtr childNamesData = m_sceneGadget->m_scene->childNamesPlug()->getValue();
					haveChildren = childNamesData->readable().size();
				}

				m_sceneGraph->clearChildren();

				m_sceneGraph->m_bound.extendBy( m_sceneGadget->m_scene->boundPlug()->getValue() );

				if( haveChildren )
				{
					IECore::CurvesPrimitivePtr curvesBound = IECore::CurvesPrimitive::createBox( m_sceneGraph->m_bound );
					m_sceneGraph->m_boundRenderable = boost::static_pointer_cast<const IECoreGL::Renderable>(
						IECoreGL::CachedConverter::defaultCachedConverter()->convert( curvesBound.get() )
					);
				}
				return NULL;
			}

			// We are expanded, so we need to visit all the children
			// and update those too.

			if( !previouslyExpanded )
			{
				m_dirtyFlags = AllDirty;
			}

			// Make sure we have a child for each child name

			if( m_dirtyFlags & ChildNamesDirty )
			{
				IECore::ConstInternedStringVectorDataPtr childNamesData = m_sceneGadget->m_scene->childNamesPlug()->getValue();
				const std::vector<IECore::InternedString> &childNames = childNamesData->readable();
				if( !existingChildNamesValid( childNames ) )
				{
					m_sceneGraph->clearChildren();

					for( std::vector<IECore::InternedString>::const_iterator it = childNames.begin(), eIt = childNames.end(); it != eIt; ++it )
					{
						SceneGraph *child = new SceneGraph();
						child->m_name = *it;
						m_sceneGraph->m_children.push_back( child );
					}

					m_dirtyFlags = AllDirty; // We've made brand new children, so they need a full update.
				}
			}

			// And then update each child

			if( m_sceneGraph->m_children.size() )
			{
				set_ref_count( 1 + m_sceneGraph->m_children.size() );

				ScenePlug::ScenePath childPath = m_scenePath;
				childPath.push_back( IECore::InternedString() ); // space for the child name
				for( std::vector<SceneGraph *>::const_iterator it = m_sceneGraph->m_children.begin(), eIt = m_sceneGraph->m_children.end(); it != eIt; ++it )
				{
					childPath.back() = (*it)->m_name;
					UpdateTask *t = new( allocate_child() ) UpdateTask( m_sceneGadget, *it, m_dirtyFlags, childPath );
					spawn( *t );
				}

				wait_for_all();
			}

			// Finally compute our bound from the child bounds.

			for( std::vector<SceneGraph *>::const_iterator it = m_sceneGraph->m_children.begin(), eIt = m_sceneGraph->m_children.end(); it != eIt; ++it )
			{
				const Box3f childBound = transform( (*it)->m_bound, (*it)->m_transform );
				m_sceneGraph->m_bound.extendBy( childBound );
			}

			return NULL;
		}

	private :

		bool existingChildNamesValid( const vector<IECore::InternedString> &childNames )
		{
			if( m_sceneGraph->m_children.size() != childNames.size() )
			{
				return false;
			}
			for( size_t i = 0, e = childNames.size(); i < e; ++i )
			{
				if( m_sceneGraph->m_children[i]->m_name != childNames[i] )
				{
					return false;
				}
			}
			return true;
		}

		const SceneGadget *m_sceneGadget;
		SceneGraph *m_sceneGraph;
		unsigned m_dirtyFlags;
		ScenePlug::ScenePath m_scenePath;

};

//////////////////////////////////////////////////////////////////////////
// SceneGadget implementation
//////////////////////////////////////////////////////////////////////////

SceneGadget::SceneGadget()
	:	Gadget( defaultName<SceneGadget>() ),
		m_scene( NULL ),
		m_context( NULL ),
		m_dirtyFlags( UpdateTask::AllDirty ),
		m_expandedPaths( new PathMatcherData ),
		m_minimumExpansionDepth( 0 ),
		m_baseState( new IECoreGL::State( true ) ),
		m_sceneGraph( new SceneGraph ),
		m_selection( new PathMatcherData )
{
	setContext( new Context );
}

SceneGadget::~SceneGadget()
{
}

void SceneGadget::setScene( GafferScene::ConstScenePlugPtr scene )
{
	if( scene == m_scene )
	{
		return;
	}

	m_scene = scene;
	if( Gaffer::Node *node = const_cast<Gaffer::Node *>( scene->node() ) )
	{
		m_plugDirtiedConnection = node->plugDirtiedSignal().connect( boost::bind( &SceneGadget::plugDirtied, this, ::_1 ) );
	}
	else
	{
		m_plugDirtiedConnection.disconnect();
	}

	m_dirtyFlags = UpdateTask::AllDirty;
	renderRequestSignal()( this );
}

const GafferScene::ScenePlug *SceneGadget::getScene() const
{
	return m_scene.get();
}

void SceneGadget::setContext( Gaffer::ContextPtr context )
{
	if( context == m_context )
	{
		return;
	}

	m_context = context;
	m_contextChangedConnection = m_context->changedSignal().connect( boost::bind( &SceneGadget::contextChanged, this, ::_2 ) );
	renderRequestSignal()( this );
}

Gaffer::Context *SceneGadget::getContext()
{
	return m_context.get();
}

const Gaffer::Context *SceneGadget::getContext() const
{
	return m_context.get();
}

void SceneGadget::setExpandedPaths( GafferScene::ConstPathMatcherDataPtr expandedPaths )
{
	m_expandedPaths = expandedPaths;
	m_dirtyFlags |= UpdateTask::ExpansionDirty;
	renderRequestSignal()( this );
}

const GafferScene::PathMatcherData *SceneGadget::getExpandedPaths() const
{
	return m_expandedPaths.get();
}

void SceneGadget::setMinimumExpansionDepth( size_t depth )
{
	if( depth == m_minimumExpansionDepth )
	{
		return;
	}
	m_minimumExpansionDepth = depth;
	m_dirtyFlags |= UpdateTask::ExpansionDirty;
	renderRequestSignal()( this );
}

size_t SceneGadget::getMinimumExpansionDepth() const
{
	return m_minimumExpansionDepth;
}

IECoreGL::State *SceneGadget::baseState()
{
	return m_baseState.get();
}

bool SceneGadget::objectAt( const IECore::LineSegment3f &lineInGadgetSpace, GafferScene::ScenePlug::ScenePath &path ) const
{
	updateSceneGraph();

	std::vector<IECoreGL::HitRecord> selection;
	{
		ViewportGadget::SelectionScope selectionScope( lineInGadgetSpace, this, selection, IECoreGL::Selector::IDRender );
		m_sceneGraph->render( const_cast<IECoreGL::State *>( m_baseState.get() ), IECoreGL::Selector::currentSelector() );
	}

	if( !selection.size() )
	{
		return false;
	}

	return m_sceneGraph->pathFromSelectionId( selection[0].name, path );
}

size_t SceneGadget::objectsAt(
	const Imath::V3f &corner0InGadgetSpace,
	const Imath::V3f &corner1InGadgetSpace,
	GafferScene::PathMatcher &paths
) const
{
	updateSceneGraph();

	std::vector<IECoreGL::HitRecord> selection;
	{
		ViewportGadget::SelectionScope selectionScope( corner0InGadgetSpace, corner1InGadgetSpace, this, selection, IECoreGL::Selector::OcclusionQuery );
		m_sceneGraph->render( const_cast<IECoreGL::State *>( m_baseState.get() ), IECoreGL::Selector::currentSelector() );
	}

	size_t result = 0;
	ScenePlug::ScenePath path;
	for( std::vector<IECoreGL::HitRecord>::const_iterator it = selection.begin(), eIt = selection.end(); it != eIt; ++it )
	{
		if( m_sceneGraph->pathFromSelectionId( it->name, path ) )
		{
			result += paths.addPath( path );
		}
	}

	return result;
}

const GafferScene::PathMatcherData *SceneGadget::getSelection() const
{
	return m_selection.get();
}

void SceneGadget::setSelection( ConstPathMatcherDataPtr selection )
{
	m_selection = selection;
	m_sceneGraph->applySelection( m_selection->readable() );
	renderRequestSignal()( this );
}

Imath::Box3f SceneGadget::selectionBound() const
{
	updateSceneGraph();
	return m_sceneGraph->selectionBound();
}

std::string SceneGadget::getToolTip( const IECore::LineSegment3f &line ) const
{
	std::string result = Gadget::getToolTip( line );
	if( result.size() )
	{
		return result;
	}

	ScenePlug::ScenePath path;
	if( objectAt( line, path ) )
	{
		ScenePlug::pathToString( path, result );
	}

	return result;
}

Imath::Box3f SceneGadget::bound() const
{
	updateSceneGraph();
	return m_sceneGraph->bound();
}

void SceneGadget::doRender( const GafferUI::Style *style ) const
{
	if( !m_scene || IECoreGL::Selector::currentSelector() )
	{
		return;
	}

	updateSceneGraph();

	GLint prevProgram;
	glGetIntegerv( GL_CURRENT_PROGRAM, &prevProgram );
	glPushAttrib( GL_ALL_ATTRIB_BITS );

		IECoreGL::State::bindBaseState();
		m_baseState->bind();
		m_sceneGraph->render( const_cast<IECoreGL::State *>( m_baseState.get() ) );

	glPopAttrib();
	glUseProgram( prevProgram );
}

void SceneGadget::plugDirtied( const Gaffer::Plug *plug )
{
	if( plug == m_scene->boundPlug() )
	{
		m_dirtyFlags |= UpdateTask::BoundDirty;
	}
	else if( plug == m_scene->transformPlug() )
	{
		m_dirtyFlags |= UpdateTask::TransformDirty;
	}
	else if( plug == m_scene->attributesPlug() )
	{
		m_dirtyFlags |= UpdateTask::AttributesDirty;
	}
	else if( plug == m_scene->objectPlug() )
	{
		m_dirtyFlags |= UpdateTask::ObjectDirty;
	}
	else if( plug == m_scene->childNamesPlug() )
	{
		m_dirtyFlags |= UpdateTask::ChildNamesDirty;
	}
	else
	{
		return;
	}

	renderRequestSignal()( this );
}

void SceneGadget::contextChanged( const IECore::InternedString &name )
{
	if( !boost::starts_with( name.string(), "ui:" ) )
	{
		m_dirtyFlags = UpdateTask::AllDirty;
		renderRequestSignal()( this );
	}
}

void SceneGadget::updateSceneGraph() const
{
	if( !m_dirtyFlags )
	{
		return;
	}

	UpdateTask *task = new( tbb::task::allocate_root() ) UpdateTask( this, m_sceneGraph.get(), m_dirtyFlags, ScenePlug::ScenePath() );
	tbb::task::spawn_root_and_wait( *task );

	if( m_dirtyFlags && UpdateTask::ChildNamesDirty )
	{
		m_sceneGraph->applySelection( m_selection->readable() );
	}

	m_dirtyFlags = UpdateTask::NothingDirty;
}
