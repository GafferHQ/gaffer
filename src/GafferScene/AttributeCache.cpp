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

#include "IECore/InterpolatedCache.h"
#include "IECore/LRUCache.h"

#include "Gaffer/Context.h"

#include "GafferScene/AttributeCache.h"

using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( AttributeCache );

//////////////////////////////////////////////////////////////////////////
// Implementation of an LRUCache of InterpolatedCaches.
//////////////////////////////////////////////////////////////////////////

static IECore::InterpolatedCachePtr interpolatedCacheGetter( const std::string &fileSequence, size_t &cost )
{
	cost = 1;
	return new IECore::InterpolatedCache( fileSequence, IECore::InterpolatedCache::Linear );
}

typedef IECore::LRUCache<std::string, IECore::InterpolatedCachePtr> InterpolatedCacheCache;

static InterpolatedCacheCache g_interpolatedCacheCache( interpolatedCacheGetter, 200 );

//////////////////////////////////////////////////////////////////////////
// Implementation of AttributeCache.
//////////////////////////////////////////////////////////////////////////

AttributeCache::AttributeCache( const std::string &name )
	:	SceneProcessor( name )
{
	addChild( new StringPlug( "fileName" ) );
}

AttributeCache::~AttributeCache()
{
}

Gaffer::StringPlug *AttributeCache::fileNamePlug()
{
	return getChild<StringPlug>( "fileName" );
}

const Gaffer::StringPlug *AttributeCache::fileNamePlug() const
{
	return getChild<StringPlug>( "fileName" );
}

void AttributeCache::affects( const Gaffer::ValuePlug *input, AffectedPlugsContainer &outputs ) const
{
	if( input == fileNamePlug() )
	{
		outputs.push_back( outPlug() );
	}
}

Imath::Box3f AttributeCache::processBound( const ScenePath &path, const Gaffer::Context *context, const Imath::Box3f &inputBound ) const
{
	IECore::InterpolatedCachePtr cache = g_interpolatedCacheCache.get( fileNamePlug()->getValue() );
	try
	{
		std::string cacheObjectName = entryForPath( path );
		IECore::Box3fDataPtr bound = IECore::runTimeCast<IECore::Box3fData>( cache->read( context->getFrame(), cacheObjectName, "bound" ) );
		if( bound )
		{
			return bound->readable();
		}
	}
	catch( const std::exception &e )
	{
		// we assume it's ok to not have a bound - it's up to the author of the cache to make
		// sure there is a valid bound if necessary.
	}
	
	return inputBound;
}

Imath::M44f AttributeCache::processTransform( const ScenePath &path, const Gaffer::Context *context, const Imath::M44f &inputTransform ) const
{
	IECore::InterpolatedCachePtr cache = g_interpolatedCacheCache.get( fileNamePlug()->getValue() );
	try
	{
		std::string cacheObjectName = entryForPath( path );
		IECore::M44fDataPtr transform = IECore::runTimeCast<IECore::M44fData>( cache->read( context->getFrame(), cacheObjectName, "transform" ) );
		if( transform )
		{
			return transform->readable();
		}
	}
	catch( const std::exception &e )
	{
		// it's ok to not have a transform.
	}
	
	return inputTransform;
}

IECore::PrimitivePtr AttributeCache::processGeometry( const ScenePath &path, const Gaffer::Context *context, IECore::ConstPrimitivePtr inputGeometry ) const
{
	// we're obliged to pull on these whether we need them or not, so this
	// comes before the early out for the no input geometry case.
	const std::string fileName = fileNamePlug()->getValue();
	const float frame = context->getFrame();
	
	if( !inputGeometry )
	{
		return 0;
	}

	std::string cacheObjectName = entryForPath( path );

	IECore::InterpolatedCachePtr cache = g_interpolatedCacheCache.get( fileName );
	std::vector<IECore::InterpolatedCache::AttributeHandle> attributeNames;
	try
	{
		cache->attributes( frame, cacheObjectName, attributeNames );
	}
	catch( const std::exception &e )
	{
		// it's ok to have no attributes
	}
	
	IECore::PrimitivePtr result = inputGeometry->copy();
	for( std::vector<IECore::InterpolatedCache::AttributeHandle>::const_iterator it = attributeNames.begin(); it!=attributeNames.end(); it++ )
	{
		if( it->compare( 0, 8, "primVar:" )==0 )
		{
			std::string name( *it, 8 );
			IECore::DataPtr value = IECore::runTimeCast<IECore::Data>( cache->read( frame, cacheObjectName, *it ) );
			if( value )
			{
				IECore::PrimitiveVariable::Interpolation interpolation = result->inferInterpolation( value );
				if( interpolation != IECore::PrimitiveVariable::Invalid )
				{
					result->variables[name] = IECore::PrimitiveVariable( interpolation, value );
				}
			}
		}
	}

	return result;
}

std::string AttributeCache::entryForPath( const ScenePath &path ) const
{
	std::string result = path;
	std::replace( result.begin(), result.end(), '/', '-' );
	return result;
}
