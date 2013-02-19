//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012-2013, John Haddon. All rights reserved.
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

#include "OpenEXR/ImathBoxAlgo.h"

#include "IECore/AttributeBlock.h"
#include "IECore/MessageHandler.h"
#include "IECore/CurvesPrimitive.h"
#include "IECore/StateRenderable.h"
#include "IECore/AngleConversion.h"

#include "Gaffer/Context.h"

#include "GafferScene/SceneProcedural.h"
#include "GafferScene/ScenePlug.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

SceneProcedural::SceneProcedural( ScenePlugPtr scenePlug, const Gaffer::Context *context, const ScenePlug::ScenePath &scenePath, const IECore::PathMatcherData *pathsToExpand )
	:	m_scenePlug( scenePlug ), m_context( new Context( *context ) ), m_scenePath( scenePath ), m_pathsToExpand( pathsToExpand ? pathsToExpand->copy() : 0 )
{
	m_context->set( ScenePlug::scenePathContextName, m_scenePath );
}

SceneProcedural::SceneProcedural( const SceneProcedural &other, const ScenePlug::ScenePath &scenePath )
	:	m_scenePlug( other.m_scenePlug ), m_context( new Context( *(other.m_context) ) ), m_scenePath( scenePath ), m_pathsToExpand( other.m_pathsToExpand )
{
	m_context->set( ScenePlug::scenePathContextName, m_scenePath );
}

SceneProcedural::~SceneProcedural()
{
}

Imath::Box3f SceneProcedural::bound() const
{
	Context::Scope scopedContext( m_context );
	/// \todo I think we should be able to remove this exception handling in the future.
	/// Either when we do better error handling in ValuePlug computations, or when 
	/// the bug in IECoreGL that caused the crashes in SceneProceduralTest.testComputationErrors
	/// is fixed.
	try
	{
		Box3f b = m_scenePlug->boundPlug()->getValue();
		M44f t = m_scenePlug->transformPlug()->getValue();
		return transform( b, t );
	}
	catch( const std::exception &e )
	{
		IECore::msg( IECore::Msg::Error, "SceneProcedural::bound()", e.what() );
	}
	return Box3f();
}

void SceneProcedural::render( RendererPtr renderer ) const
{	
	Context::Scope scopedContext( m_context );
	
	// get all the attributes, and early out if we're not visibile
	
	ConstCompoundObjectPtr attributes = m_scenePlug->attributesPlug()->getValue();
	const BoolData *visibilityData = attributes->member<BoolData>( "gaffer:visibility" );
	if( visibilityData && !visibilityData->readable() )
	{
		return;
	}

	// if we are visible then make an attribute block to contain everything, set the name
	// and get on with generating things.

	AttributeBlock attributeBlock( renderer );
	
	std::string name = "";
	for( ScenePlug::ScenePath::const_iterator it = m_scenePath.begin(), eIt = m_scenePath.end(); it != eIt; it++ )
	{
		name += "/" + it->string();
	}
	renderer->setAttribute( "name", new StringData( name ) );

	/// \todo See above.
	try
	{
		// transform
		
		renderer->concatTransform( m_scenePlug->transformPlug()->getValue() );
		
		// attributes
		
		for( CompoundObject::ObjectMap::const_iterator it = attributes->members().begin(), eIt = attributes->members().end(); it != eIt; it++ )
		{
			if( const StateRenderable *s = runTimeCast<const StateRenderable>( it->second.get() ) )
			{
				s->render( renderer );
			}
			else if( const ObjectVector *o = runTimeCast<const ObjectVector>( it->second.get() ) )
			{
				for( ObjectVector::MemberContainer::const_iterator it = o->members().begin(), eIt = o->members().end(); it != eIt; it++ )
				{
					const StateRenderable *s = runTimeCast<const StateRenderable>( it->get() );
					if( s )
					{
						s->render( renderer );
					}
				}
			}
			else if( const Data *d = runTimeCast<const Data>( it->second.get() ) )
			{
				renderer->setAttribute( it->first, d );
			}
		}
		
		// object
		
		ConstObjectPtr object = m_scenePlug->objectPlug()->getValue();
		if( const Primitive *primitive = runTimeCast<const Primitive>( object.get() ) )
		{
			primitive->render( renderer );
		}
		else if( const Camera *camera = runTimeCast<const Camera>( object.get() ) )
		{
			/// \todo This absolutely does not belong here, but until we have
			/// a mechanism for drawing manipulators, we don't have any other
			/// means of visualising the cameras.
			if( renderer->isInstanceOf( "IECoreGL::Renderer" ) )
			{
				drawCamera( camera, renderer.get() );
			}
		}
		else if( const Light *light = runTimeCast<const Light>( object.get() ) )
		{
			/// \todo This doesn't belong here.
			if( renderer->isInstanceOf( "IECoreGL::Renderer" ) )
			{
				drawLight( light, renderer.get() );
			}
		}
	
		// children

		ConstInternedStringVectorDataPtr childNames = m_scenePlug->childNamesPlug()->getValue();
		if( childNames->readable().size() )
		{		
			bool expand = true;
			if( m_pathsToExpand )
			{
				expand = m_pathsToExpand->readable().match( m_scenePath ) == Filter::Match;
			}
			
			if( !expand )
			{
				renderer->setAttribute( "gl:primitive:wireframe", new BoolData( true ) );
				renderer->setAttribute( "gl:primitive:solid", new BoolData( false ) );
				renderer->setAttribute( "gl:curvesPrimitive:useGLLines", new BoolData( true ) );
				Box3f b = m_scenePlug->boundPlug()->getValue();
				CurvesPrimitive::createBox( b )->render( renderer );	
			}
			else
			{
				ScenePlug::ScenePath childScenePath = m_scenePath;
				childScenePath.push_back( InternedString() ); // for the child name
				for( vector<InternedString>::const_iterator it=childNames->readable().begin(); it!=childNames->readable().end(); it++ )
				{
					childScenePath[m_scenePath.size()] = *it;
					renderer->procedural( new SceneProcedural( *this, childScenePath ) );
				}
			}	
		}
	}
	catch( const std::exception &e )
	{
		IECore::msg( IECore::Msg::Error, "SceneProcedural::render()", e.what() );
	}	
}

void SceneProcedural::drawCamera( const IECore::Camera *camera, IECore::Renderer *renderer ) const
{
	CameraPtr fullCamera = camera->copy();
	fullCamera->addStandardParameters();
	
	AttributeBlock attributeBlock( renderer );

	renderer->setAttribute( "gl:primitive:wireframe", new BoolData( true ) );
	renderer->setAttribute( "gl:primitive:solid", new BoolData( false ) );
	renderer->setAttribute( "gl:curvesPrimitive:useGLLines", new BoolData( true ) );
	renderer->setAttribute( "gl:primitive:wireframeColor", new Color4fData( Color4f( 0, 0.25, 0, 1 ) ) );

	CurvesPrimitive::createBox( Box3f(
		V3f( -0.5, -0.5, 0 ),
		V3f( 0.5, 0.5, 2.0 )		
	) )->render( renderer );

	const std::string &projection = fullCamera->parametersData()->member<StringData>( "projection" )->readable();
	const Box2f &screenWindow = fullCamera->parametersData()->member<Box2fData>( "screenWindow" )->readable();
	/// \todo When we're drawing the camera by some means other than creating a primitive for it,
	/// use the actual clippings planes. Right now that's not a good idea as it results in /huge/
	/// framing bounds when the viewer frames a selected camera.
	V2f clippingPlanes( 0, 5 );
	
	Box2f near( screenWindow );
	Box2f far( screenWindow );
	
	if( projection == "perspective" )
	{
		float fov = fullCamera->parametersData()->member<FloatData>( "projection:fov" )->readable();
		float d = tan( degreesToRadians( fov / 2.0f ) );
		near.min *= d * clippingPlanes[0];
		near.max *= d * clippingPlanes[0];
		far.min *= d * clippingPlanes[1];
		far.max *= d * clippingPlanes[1];
	}
			
	V3fVectorDataPtr p = new V3fVectorData;
	IntVectorDataPtr n = new IntVectorData;
	
	n->writable().push_back( 5 );
	p->writable().push_back( V3f( near.min.x, near.min.y, -clippingPlanes[0] ) );
	p->writable().push_back( V3f( near.max.x, near.min.y, -clippingPlanes[0] ) );
	p->writable().push_back( V3f( near.max.x, near.max.y, -clippingPlanes[0] ) );
	p->writable().push_back( V3f( near.min.x, near.max.y, -clippingPlanes[0] ) );
	p->writable().push_back( V3f( near.min.x, near.min.y, -clippingPlanes[0] ) );

	n->writable().push_back( 5 );
	p->writable().push_back( V3f( far.min.x, far.min.y, -clippingPlanes[1] ) );
	p->writable().push_back( V3f( far.max.x, far.min.y, -clippingPlanes[1] ) );
	p->writable().push_back( V3f( far.max.x, far.max.y, -clippingPlanes[1] ) );
	p->writable().push_back( V3f( far.min.x, far.max.y, -clippingPlanes[1] ) );
	p->writable().push_back( V3f( far.min.x, far.min.y, -clippingPlanes[1] ) );

	n->writable().push_back( 2 );
	p->writable().push_back( V3f( near.min.x, near.min.y, -clippingPlanes[0] ) );
	p->writable().push_back( V3f( far.min.x, far.min.y, -clippingPlanes[1] ) );

	n->writable().push_back( 2 );
	p->writable().push_back( V3f( near.max.x, near.min.y, -clippingPlanes[0] ) );
	p->writable().push_back( V3f( far.max.x, far.min.y, -clippingPlanes[1] ) );

	n->writable().push_back( 2 );
	p->writable().push_back( V3f( near.max.x, near.max.y, -clippingPlanes[0] ) );
	p->writable().push_back( V3f( far.max.x, far.max.y, -clippingPlanes[1] ) );
	
	n->writable().push_back( 2 );
	p->writable().push_back( V3f( near.min.x, near.max.y, -clippingPlanes[0] ) );
	p->writable().push_back( V3f( far.min.x, far.max.y, -clippingPlanes[1] ) );
	
	CurvesPrimitivePtr c = new IECore::CurvesPrimitive( n, CubicBasisf::linear(), false, p );
	c->render( renderer );
}

void SceneProcedural::drawLight( const IECore::Light *light, IECore::Renderer *renderer ) const
{	
	AttributeBlock attributeBlock( renderer );

	renderer->setAttribute( "gl:primitive:wireframe", new BoolData( true ) );
	renderer->setAttribute( "gl:primitive:solid", new BoolData( false ) );
	renderer->setAttribute( "gl:curvesPrimitive:useGLLines", new BoolData( true ) );
	renderer->setAttribute( "gl:primitive:wireframeColor", new Color4fData( Color4f( 0.5, 0, 0, 1 ) ) );

	const float a = 0.5f;
	const float phi = 1.0f + sqrt( 5.0f ) / 2.0f;
	const float b = 1.0f / ( 2.0f * phi );
	
	// icosahedron points
	IECore::V3fVectorDataPtr pData = new V3fVectorData;
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
	
	IntVectorDataPtr vertIds = new IntVectorData;
	vertIds->writable().resize( 12, 2 );
	
	CurvesPrimitivePtr c = new IECore::CurvesPrimitive( vertIds, CubicBasisf::linear(), false, pData );
	c->render( renderer );
}
