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

#include "GafferSceneTest/CompoundObjectSource.h"

#include "boost/tokenizer.hpp"

using namespace IECore;
using namespace Gaffer;
using namespace GafferSceneTest;

GAFFER_NODE_DEFINE_TYPE( CompoundObjectSource )

CompoundObjectSource::CompoundObjectSource( const std::string &name )
	:	SceneNode( name )
{
	addChild( new ObjectPlug( "in", Plug::In, new CompoundObject() ) );
}

CompoundObjectSource::~CompoundObjectSource()
{
}

Gaffer::ObjectPlug *CompoundObjectSource::inPlug()
{
	return getChild<ObjectPlug>( "in" );
}

const Gaffer::ObjectPlug *CompoundObjectSource::inPlug() const
{
	return getChild<ObjectPlug>( "in" );
}

void CompoundObjectSource::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneNode::affects( input, outputs );
	if( input == inPlug() )
	{
		for( ValuePlug::Iterator it( outPlug() ); !it.done(); ++it )
		{
			outputs.push_back( it->get() );
		}
	}
}

void CompoundObjectSource::hashBound( const ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneNode::hashBound( path, context, parent, h );
	h.append( &path.front(), path.size() );
	inPlug()->hash( h );
}

Imath::Box3f CompoundObjectSource::computeBound( const ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent ) const
{
	return entryForPath( path )->member<Box3fData>( "bound", true /* throw exceptions */ )->readable();
}

void CompoundObjectSource::hashTransform( const ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneNode::hashTransform( path, context, parent, h );
	h.append( &path.front(), path.size() );
	inPlug()->hash( h );
}

Imath::M44f CompoundObjectSource::computeTransform( const ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent ) const
{
	ConstM44fDataPtr transform = entryForPath( path )->member<M44fData>( "transform" );
	if( transform )
	{
		return transform->readable();
	}
	return Imath::M44f();
}

void CompoundObjectSource::hashAttributes( const ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneNode::hashAttributes( path, context, parent, h );
	h.append( &path.front(), path.size() );
	inPlug()->hash( h );
}

IECore::ConstCompoundObjectPtr CompoundObjectSource::computeAttributes( const ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent ) const
{
	ConstCompoundObjectPtr a = entryForPath( path )->member<CompoundObject>( "attributes" );
	if( a )
	{
		return a;
	}
	else
	{
		return outPlug()->attributesPlug()->defaultValue();
	}
}

void CompoundObjectSource::hashObject( const ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneNode::hashObject( path, context, parent, h );
	h.append( &path.front(), path.size() );
	inPlug()->hash( h );
}

IECore::ConstObjectPtr CompoundObjectSource::computeObject( const ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent ) const
{
	ConstObjectPtr o = entryForPath( path )->member<Object>( "object" );
	if( o )
	{
		return o;
	}
	else
	{
		return outPlug()->objectPlug()->defaultValue();
	}
}

void CompoundObjectSource::hashChildNames( const ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneNode::hashChildNames( path, context, parent, h );
	h.append( &path.front(), path.size() );
	inPlug()->hash( h );
}

IECore::ConstInternedStringVectorDataPtr CompoundObjectSource::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent ) const
{
	ConstCompoundObjectPtr entry = entryForPath( path );
	ConstCompoundObjectPtr children = entry->member<CompoundObject>( "children" );
	if( !children )
	{
		return outPlug()->childNamesPlug()->defaultValue();
	}
	InternedStringVectorDataPtr result = new InternedStringVectorData;
	for( CompoundObject::ObjectMap::const_iterator it = children->members().begin(); it!=children->members().end(); it++ )
	{
		result->writable().push_back( it->first.value() );
	}
	return result;
}

void CompoundObjectSource::hashGlobals( const Gaffer::Context *context, const GafferScene::ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneNode::hashGlobals( context, parent, h );
	inPlug()->hash( h );
}

IECore::ConstCompoundObjectPtr CompoundObjectSource::computeGlobals( const Gaffer::Context *context, const GafferScene::ScenePlug *parent ) const
{
	ConstCompoundObjectPtr compoundObject = inObject();

	if( ConstCompoundObjectPtr globals = compoundObject->member<CompoundObject>( "globals" ) )
	{
		return globals;
	}
	return outPlug()->globalsPlug()->defaultValue();
}

void CompoundObjectSource::hashSetNames( const Gaffer::Context *context, const GafferScene::ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneNode::hashSetNames( context, parent, h );
	inPlug()->hash( h );
}

IECore::ConstInternedStringVectorDataPtr CompoundObjectSource::computeSetNames( const Gaffer::Context *context, const GafferScene::ScenePlug *parent ) const
{
	ConstCompoundObjectPtr compoundObject = inObject();

	if( ConstCompoundObjectPtr sets = compoundObject->member<CompoundObject>( "sets" ) )
	{
		InternedStringVectorDataPtr resultData = new InternedStringVectorData;
		std::vector<InternedString> &result = resultData->writable();
		for( CompoundObject::ObjectMap::const_iterator it = sets->members().begin(), eIt = sets->members().end(); it != eIt; ++it )
		{
			result.push_back( it->first );
		}
		return resultData;
	}

	return outPlug()->setNamesPlug()->defaultValue();
}

void CompoundObjectSource::hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const GafferScene::ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneNode::hashSet( setName, context, parent, h );
	inPlug()->hash( h );
	h.append( setName );
}

IECore::ConstPathMatcherDataPtr CompoundObjectSource::computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const GafferScene::ScenePlug *parent ) const
{
	ConstCompoundObjectPtr compoundObject = inObject();

	if( ConstCompoundObjectPtr sets = compoundObject->member<CompoundObject>( "sets" ) )
	{
		CompoundObject::ObjectMap::const_iterator it = sets->members().find( setName );
		if( it != sets->members().end() )
		{
			if( ConstPathMatcherDataPtr result = runTimeCast<const PathMatcherData>( it->second ) )
			{
				return result;
			}
		}
	}

	return outPlug()->setPlug()->defaultValue();
}

IECore::ConstCompoundObjectPtr CompoundObjectSource::inObject() const
{
	ConstCompoundObjectPtr result = runTimeCast<const CompoundObject>( inPlug()->getValue() );
	if( !result )
	{
		throw Exception( "Input value is not a CompoundObject" );
	}
	return result;
}

IECore::ConstCompoundObjectPtr CompoundObjectSource::entryForPath( const ScenePath &path ) const
{
	ConstCompoundObjectPtr result = inObject();

	for( ScenePath::const_iterator it=path.begin(); it!=path.end(); it++ )
	{
		result = result->member<CompoundObject>( "children", true /* throw exceptions */ );
		result = result->member<CompoundObject>( *it, true /* throw exceptions */ );
	}

	return result;
}
