//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "Gaffer/Context.h"

#include "GafferScene/SceneProcedural.h"
#include "GafferScene/ScenePlug.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

SceneProcedural::SceneProcedural( ScenePlugPtr scenePlug, const Gaffer::Context *context, const std::string &scenePath, const IECore::StringVectorData *pathsToExpand )
	:	m_scenePlug( scenePlug ), m_context( new Context( *context ) ), m_scenePath( scenePath )
{
	m_context->set( "scene:path", m_scenePath );
	
	if( pathsToExpand )
	{
		m_pathsToExpand = boost::shared_ptr<ExpandedPathsSet>( new ExpandedPathsSet );
		for( std::vector<std::string>::const_iterator it = pathsToExpand->readable().begin(); it != pathsToExpand->readable().end(); it++ )
		{
			m_pathsToExpand->insert( *it );
		}
	}	
}

SceneProcedural::SceneProcedural( const SceneProcedural &other, const std::string &scenePath )
	:	m_scenePlug( other.m_scenePlug ), m_context( new Context( *(other.m_context) ) ), m_scenePath( scenePath ), m_pathsToExpand( other.m_pathsToExpand )
{
	m_context->set( "scene:path", m_scenePath );
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
	/// if fixed.
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
	AttributeBlock attributeBlock( renderer );
	Context::Scope scopedContext( m_context );
	
	renderer->setAttribute( "name", new StringData( m_scenePath ) );
	
	/// \todo See above.
	try
	{
		renderer->concatTransform( m_scenePlug->transformPlug()->getValue() );
		
		ConstObjectVectorPtr state = runTimeCast<const ObjectVector>( m_scenePlug->statePlug()->getValue() );
		if( state )
		{
			for( ObjectVector::MemberContainer::const_iterator it = state->members().begin(), eIt = state->members().end(); it != eIt; it++ )
			{
				const StateRenderable *s = runTimeCast<const StateRenderable>( it->get() );
				if( s )
				{
					s->render( renderer );
				}
			}
		}
		
		ConstPrimitivePtr primitive = runTimeCast<const Primitive>( m_scenePlug->objectPlug()->getValue() );
		if( primitive )
		{
			primitive->render( renderer );
		}
		
		bool expand = true;
		if( m_pathsToExpand )
		{
			expand = m_pathsToExpand->find( m_scenePath ) != m_pathsToExpand->end();
		}
				
		ConstStringVectorDataPtr childNames = m_scenePlug->childNamesPlug()->getValue();
		if( childNames && childNames->readable().size() )
		{		
			if( expand )
			{
				if( childNames )
				{
					for( vector<string>::const_iterator it=childNames->readable().begin(); it!=childNames->readable().end(); it++ )
					{
						string childScenePath = m_scenePath;
						if( m_scenePath.size() > 1 )
						{
							childScenePath += "/";
						}
						childScenePath += *it;
						renderer->procedural( new SceneProcedural( *this, childScenePath ) );
					}	
				}
			}
			else
			{
				renderer->setAttribute( "gl:primitive:wireframe", new BoolData( true ) );
				renderer->setAttribute( "gl:primitive:solid", new BoolData( false ) );
				renderer->setAttribute( "gl:curvesPrimitive:useGLLines", new BoolData( true ) );
				Box3f b = m_scenePlug->boundPlug()->getValue();
				CurvesPrimitive::createBox( b )->render( renderer );	
			}
		}
	}
	catch( const std::exception &e )
	{
		IECore::msg( IECore::Msg::Error, "SceneProcedural::render()", e.what() );
	}	
}
