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

#include "Gaffer/Context.h"

#include "GafferScene/SceneNode.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace GafferScene;
using namespace Gaffer;

IE_CORE_DEFINERUNTIMETYPED( SceneNode );

size_t SceneNode::g_firstPlugIndex = 0;

SceneNode::SceneNode( const std::string &name )
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "out", Gaffer::Plug::Out ) );
	addChild( new BoolPlug( "enabled", Gaffer::Plug::In, true ) );
}

SceneNode::~SceneNode()
{
}

ScenePlug *SceneNode::outPlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const ScenePlug *SceneNode::outPlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

BoolPlug *SceneNode::enabledPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

const BoolPlug *SceneNode::enabledPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

void SceneNode::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );
	
	if( input == enabledPlug() )
	{
		for( ValuePlugIterator it( outPlug() ); it != it.end(); it++ )
		{
			outputs.push_back( it->get() );
		}
	}
}

void SceneNode::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{	
	const ScenePlug *scenePlug = output->parent<ScenePlug>();
	if( scenePlug && enabledPlug()->getValue() )
	{
		// We don't call ComputeNode::hash() immediately here, because for subclasses which
		// want to pass through a specific hash in the hash*() methods it's a waste of time (the
		// hash will get overwritten anyway). Instead we call ComputeNode::hash() in our
		// hash*() implementations, and allow subclass implementations to not call the base class
		// if they intend to overwrite the hash.
		if( output == scenePlug->boundPlug() )
		{
			const ScenePath &scenePath = context->get<ScenePath>( ScenePlug::scenePathContextName );
			hashBound( scenePath, context, scenePlug, h );
		}
		else if( output == scenePlug->transformPlug() )
		{
			const ScenePath &scenePath = context->get<ScenePath>( ScenePlug::scenePathContextName );
			hashTransform( scenePath, context, scenePlug, h );
		}
		else if( output == scenePlug->attributesPlug() )
		{
			const ScenePath &scenePath = context->get<ScenePath>( ScenePlug::scenePathContextName );
			hashAttributes( scenePath, context, scenePlug, h );
		}
		else if( output == scenePlug->objectPlug() )
		{
			const ScenePath &scenePath = context->get<ScenePath>( ScenePlug::scenePathContextName );
			hashObject( scenePath, context, scenePlug, h );
		}
		else if( output == scenePlug->childNamesPlug() )
		{
			const ScenePath &scenePath = context->get<ScenePath>( ScenePlug::scenePathContextName );
			hashChildNames( scenePath, context, scenePlug, h );
		}
		else if( output == scenePlug->globalsPlug() )
		{
			hashGlobals( context, scenePlug, h );
		}
	}
	else
	{
		ComputeNode::hash( output, context, h );
	}
}

void SceneNode::hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( parent->boundPlug(), context, h );
}

void SceneNode::hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( parent->transformPlug(), context, h );
}

void SceneNode::hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( parent->attributesPlug(), context, h );
}

void SceneNode::hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( parent->objectPlug(), context, h );
}

void SceneNode::hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( parent->childNamesPlug(), context, h );
}

void SceneNode::hashGlobals( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( parent->globalsPlug(), context, h );
}
		
void SceneNode::compute( ValuePlug *output, const Context *context ) const
{
	ScenePlug *scenePlug = output->parent<ScenePlug>();
	if( scenePlug )
	{
		if( enabledPlug()->getValue() )
		{
			if( output == scenePlug->boundPlug() )
			{
				const ScenePath &scenePath = context->get<ScenePath>( ScenePlug::scenePathContextName );
				static_cast<AtomicBox3fPlug *>( output )->setValue(
					computeBound( scenePath, context, scenePlug )
				);
			}
			else if( output == scenePlug->transformPlug() )
			{
				const ScenePath &scenePath = context->get<ScenePath>( ScenePlug::scenePathContextName );
				M44f transform;
				if( scenePath.size() ) // scene root must have identity transform
				{
					transform = computeTransform( scenePath, context, scenePlug );
				}
				static_cast<M44fPlug *>( output )->setValue( transform );
			}
			else if( output == scenePlug->attributesPlug() )
			{
				const ScenePath &scenePath = context->get<ScenePath>( ScenePlug::scenePathContextName );
				CompoundObjectPlug *attributesPlug = static_cast<CompoundObjectPlug *>( output );
				if( scenePath.size() ) // scene root must have no attributes
				{
					attributesPlug->setValue( computeAttributes( scenePath, context, scenePlug ) );
				}
				else
				{
					attributesPlug->setValue( attributesPlug->defaultValue() );
				}
			}
			else if( output == scenePlug->objectPlug() )
			{
				const ScenePath &scenePath = context->get<ScenePath>( ScenePlug::scenePathContextName );
				ObjectPlug *objectPlug = static_cast<ObjectPlug *>( output );
				if( scenePath.size() ) // scene root must have no object
				{
					objectPlug->setValue( computeObject( scenePath, context, scenePlug ) );
				}
				else
				{
					objectPlug->setValue( objectPlug->defaultValue() );
				}
			}
			else if( output == scenePlug->childNamesPlug() )
			{
				const ScenePath &scenePath = context->get<ScenePath>( ScenePlug::scenePathContextName );
				static_cast<InternedStringVectorDataPlug *>( output )->setValue(
					computeChildNames( scenePath, context, scenePlug )
				);
			}
			else if( output == scenePlug->globalsPlug() )
			{
				static_cast<CompoundObjectPlug *>( output )->setValue(
					computeGlobals( context, scenePlug )
				);
			}
		}
		else
		{
			// node is disabled.
			output->setToDefault();
		}
	}
}

IECore::MurmurHash SceneNode::hashOfTransformedChildBounds( const ScenePath &path, const ScenePlug *out ) const
{
	IECore::MurmurHash result;
	ConstInternedStringVectorDataPtr childNamesData = out->childNames( path );
	vector<InternedString> childNames = childNamesData->readable();
	if( childNames.size() )
	{
		ScenePath childPath( path );
		childPath.push_back( InternedString() ); // room for the child name
		for( vector<InternedString>::const_iterator it = childNames.begin(); it != childNames.end(); it++ )
		{
			childPath[path.size()] = *it;
			result.append( out->boundHash( childPath ) );
			result.append( out->transformHash( childPath ) );
		}
	}
	else
	{
		result.append( typeId() );
		result.append( "emptyBound" );
	}
	return result;
}

Imath::Box3f SceneNode::unionOfTransformedChildBounds( const ScenePath &path, const ScenePlug *out ) const
{
	Box3f result;
	ConstInternedStringVectorDataPtr childNamesData = out->childNames( path );
	vector<InternedString> childNames = childNamesData->readable();
	
	ScenePath childPath( path );
	childPath.push_back( InternedString() ); // room for the child name
	for( vector<InternedString>::const_iterator it = childNames.begin(); it != childNames.end(); it++ )
	{
		childPath[path.size()] = *it;
		Box3f childBound = out->bound( childPath );
		childBound = transform( childBound, out->transform( childPath ) );
		result.extendBy( childBound );
	}
	return result;
}
