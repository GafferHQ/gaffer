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

#include "boost/bind.hpp"

#include "IECore/LRUCache.h"

#include "Gaffer/Context.h"

#include "GafferScene/AlembicSource.h"

using namespace Imath;
using namespace IECore;
using namespace IECoreAlembic;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( AlembicSource );

//////////////////////////////////////////////////////////////////////////
// Implementation of an LRUCache of FileIndexedIOs.
//////////////////////////////////////////////////////////////////////////

namespace GafferScene
{

namespace Detail
{

AlembicInputPtr alembicInputGetter( const std::string &fileName, size_t &cost )
{
	cost = 1;
	return new AlembicInput( fileName );
}

typedef LRUCache<std::string, AlembicInputPtr> AlembicInputCache;

AlembicInputCache *alembicInputCache()
{
	static AlembicInputCache *c = new AlembicInputCache( alembicInputGetter, 200 );
	return c;
}

} // namespace Detail

} // namespace GafferScene

//////////////////////////////////////////////////////////////////////////
// AlembicSource implementation
//////////////////////////////////////////////////////////////////////////

using namespace GafferScene::Detail;

AlembicSource::AlembicSource( const std::string &name )
	:	FileSource( name )
{
	plugSetSignal().connect( boost::bind( &AlembicSource::plugSet, this, ::_1 ) );
}

AlembicSource::~AlembicSource()
{
}

void AlembicSource::plugSet( Gaffer::Plug *plug )
{
	if( plug == refreshCountPlug() )
	{
		alembicInputCache()->clear();
	}
}

void AlembicSource::hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	FileSource::hashBound( path, context, parent, h );
	h.append( context->getFrame() );
}

void AlembicSource::hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	FileSource::hashTransform( path, context, parent, h );
	h.append( context->getFrame() );
}

void AlembicSource::hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	FileSource::hashObject( path, context, parent, h );
	h.append( context->getFrame() );
}

Imath::Box3f AlembicSource::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( AlembicInputPtr i = inputForPath( path ) )
	{
		if( i->hasStoredBound() )
		{
			Box3d b = i->boundAtTime( context->getFrame() / fps() );
			return Box3f( b.min, b.max );
		}
		else
		{
			return unionOfTransformedChildBounds( path, parent );
		}
	}
	return Box3f();
}

Imath::M44f AlembicSource::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	M44f result;
	if( AlembicInputPtr i = inputForPath( path ) )
	{
		M44d t = i->transformAtTime( context->getFrame() /fps() );
		/// \todo Maybe we should be using doubles for bounds and transforms anyway?
		result = M44f(
			t[0][0], t[0][1], t[0][2], t[0][3],
            t[1][0], t[1][1], t[1][2], t[1][3],
            t[2][0], t[2][1], t[2][2], t[2][3],
            t[3][0], t[3][1], t[3][2], t[3][3]
		);
	}
	return result;
}

IECore::ConstCompoundObjectPtr AlembicSource::computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	/// \todo Implement support for attributes
	return parent->attributesPlug()->defaultValue();
}

IECore::ConstObjectPtr AlembicSource::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstObjectPtr result = parent->objectPlug()->defaultValue();
	if( AlembicInputPtr i = inputForPath( path ) )
	{
		/// \todo Maybe template objectAtTime and then we don't need the cast.
		ConstRenderablePtr renderable = runTimeCast<Renderable>( i->objectAtTime( context->getFrame() / fps(), IECore::RenderableTypeId ) );
		if( renderable )
		{
			result = renderable;
		}
	}
	return result;
}

IECore::ConstInternedStringVectorDataPtr AlembicSource::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( AlembicInputPtr i = inputForPath( path ) )
	{
		ConstStringVectorDataPtr c = i->childNames();
		InternedStringVectorDataPtr result = new InternedStringVectorData;
		result->writable().insert( result->writable().end(), c->readable().begin(), c->readable().end() );
		return result;
	}
	else
	{
		return parent->childNamesPlug()->defaultValue();
	}
}

IECore::ConstCompoundObjectPtr AlembicSource::computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	return parent->globalsPlug()->defaultValue();
}

IECoreAlembic::AlembicInputPtr AlembicSource::inputForPath( const ScenePath &path ) const
{
	const std::string fileName = fileNamePlug()->getValue();
	if( !fileName.size() )
	{
		return NULL;
	}
	
	AlembicInputPtr result = Detail::alembicInputCache()->get( fileName );
	for( ScenePath::const_iterator it = path.begin(), eIt = path.end(); it != eIt; it++ )
	{	
		result = result->child( it->value() );
	}
	
	return result;
}

float AlembicSource::fps() const
{
	return 24.0f;
}
