//////////////////////////////////////////////////////////////////////////
//  
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

#include "tbb/mutex.h"

#include "boost/bind.hpp"

#include "IECore/FileIndexedIO.h"
#include "IECore/LRUCache.h"
#include "IECore/SceneInterface.h"
#include "IECore/SharedSceneInterfaces.h"
#include "IECore/InternedString.h"
#include "IECore/SceneCache.h"

#include "Gaffer/Context.h"
#include "GafferScene/SceneReader.h"

using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( SceneReader );

//////////////////////////////////////////////////////////////////////////
// SceneReader implementation
//////////////////////////////////////////////////////////////////////////

/// \todo hard coded framerate should be replaced with a getTime() method on Gaffer::Context or something
const double SceneReader::g_frameRate( 24 );
static IECore::BoolDataPtr g_trueBoolData = new IECore::BoolData( true );

SceneReader::SceneReader( const std::string &name )
	:	FileSource( name )
{
	plugSetSignal().connect( boost::bind( &SceneReader::plugSet, this, ::_1 ) );
}

SceneReader::~SceneReader()
{
}

Imath::Box3f SceneReader::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	std::string fileName = fileNamePlug()->getValue();
	if( !fileName.size() )
	{
		return Box3f();
	}
	
	ConstSceneInterfacePtr s = SharedSceneInterfaces::get( fileName );
	s = s->scene( path );
	
	Box3d b = s->readBound( context->getFrame() / g_frameRate );
	
	if( b.isEmpty() )
	{
		return Box3f();
	}
	
	return Box3f( b.min, b.max );
}

Imath::M44f SceneReader::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	std::string fileName = fileNamePlug()->getValue();
	if( !fileName.size() )
	{
		return M44f();
	}
	
	ConstSceneInterfacePtr s = SharedSceneInterfaces::get( fileName );
	s = s->scene( path );
	
	M44d t = s->readTransformAsMatrix( context->getFrame() / g_frameRate );
	
	return M44f(
		t[0][0], t[0][1], t[0][2], t[0][3],
		t[1][0], t[1][1], t[1][2], t[1][3],
		t[2][0], t[2][1], t[2][2], t[2][3],
		t[3][0], t[3][1], t[3][2], t[3][3]
	);
}

IECore::ConstCompoundObjectPtr SceneReader::computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	std::string fileName = fileNamePlug()->getValue();
	if( !fileName.size() )
	{
		return parent->attributesPlug()->defaultValue();
	}
	
	ConstSceneInterfacePtr s = SharedSceneInterfaces::get( fileName );
	s = s->scene( path );
	
	// read attributes
	
	SceneInterface::NameList nameList;
	s->attributeNames( nameList );
	
	CompoundObjectPtr result = new CompoundObject;
	
	for( SceneInterface::NameList::iterator it = nameList.begin(); it != nameList.end(); ++it )
	{
		// these internal attributes should be ignored:
		if( *it == SceneCache::animatedObjectTopologyAttribute )
		{
			continue;
		}
		if( *it == SceneCache::animatedObjectPrimVarsAttribute )
		{
			continue;
		}
		
		// the const cast is ok, because we're only using it to put the object into a CompoundObject that will
		// be treated as forever const after being returned from this function.
		result->members()[ std::string( *it ) ] = constPointerCast<Object>( s->readAttribute( *it, context->getFrame() / g_frameRate ) );
	}

	// read tags and turn them into attributes of the form "user:tag:tagName"
	
	nameList.clear();
	s->readTags( nameList, false );
	for( SceneInterface::NameList::const_iterator it = nameList.begin(); it != nameList.end(); ++it )
	{
		if( it->string().compare( 0, 11, "ObjectType:" ) == 0 )
		{
			continue;
		}
		result->members()["user:tag:"+it->string()] = g_trueBoolData;
	}

	return result;
}

IECore::ConstObjectPtr SceneReader::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	std::string fileName = fileNamePlug()->getValue();
	if( !fileName.size() )
	{
		return parent->objectPlug()->defaultValue();
	}
	
	ConstSceneInterfacePtr s = SharedSceneInterfaces::get( fileName );
	s = s->scene( path );
	
	ObjectPtr o;
	
	if( s->hasObject() )
	{
		ConstObjectPtr o = s->readObject( context->getFrame() / g_frameRate );
		return o ? o : ConstObjectPtr( parent->objectPlug()->defaultValue() );
	}
	
	return parent->objectPlug()->defaultValue();
}

IECore::ConstInternedStringVectorDataPtr SceneReader::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	std::string fileName = fileNamePlug()->getValue();
	if( !fileName.size() )
	{
		return parent->childNamesPlug()->defaultValue();
	}
	
	ConstSceneInterfacePtr s = SharedSceneInterfaces::get( fileName );
	s = s->scene( path );

	InternedStringVectorDataPtr result = new InternedStringVectorData;
	s->childNames( result->writable() );
	
	return result;
}

IECore::ConstCompoundObjectPtr SceneReader::computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	return parent->globalsPlug()->defaultValue();
}

void SceneReader::plugSet( Gaffer::Plug *plug )
{
	// this clears the cache every time the refresh count is updated, so you don't get entries
	// from old files hanging around and screwing up the hierarchy.
	/// \todo The fact that this clears the cache for all nodes, ever is a problem - find a better
	// way of doing this!
	if( plug == refreshCountPlug() )
	{
		SharedSceneInterfaces::clear();
	}
}

/// \todo this hash needs to be smarter - it should detect if the scene cache is animated or not
void SceneReader::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FileSource::hash( output, context, h );
	h.append( context->getFrame() / g_frameRate );
}
