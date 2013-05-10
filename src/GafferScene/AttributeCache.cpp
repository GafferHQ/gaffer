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

size_t AttributeCache::g_firstPlugIndex = 0;

AttributeCache::AttributeCache( const std::string &name )
	:	SceneElementProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "fileName" ) );
}

AttributeCache::~AttributeCache()
{
}

Gaffer::StringPlug *AttributeCache::fileNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *AttributeCache::fileNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

void AttributeCache::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	if( input == fileNamePlug() )
	{
		for( ValuePlugIterator it( outPlug() ); it != it.end(); it++ )
		{
			outputs.push_back( it->get() );
		}
	}
}

bool AttributeCache::processesBound() const
{
	return true;
}

void AttributeCache::hashProcessedBound( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	fileNamePlug()->hash( h );
	h.append( context->getFrame() );
}

Imath::Box3f AttributeCache::computeProcessedBound( const ScenePath &path, const Gaffer::Context *context, const Imath::Box3f &inputBound ) const
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

bool AttributeCache::processesTransform() const
{
	return true;
}

void AttributeCache::hashProcessedTransform( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	fileNamePlug()->hash( h );
	h.append( context->getFrame() );
}

Imath::M44f AttributeCache::computeProcessedTransform( const ScenePath &path, const Gaffer::Context *context, const Imath::M44f &inputTransform ) const
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

bool AttributeCache::processesObject() const
{
	return true;
}

void AttributeCache::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	fileNamePlug()->hash( h );
	h.append( context->getFrame() );
}

IECore::ConstObjectPtr AttributeCache::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::ConstObjectPtr inputObject ) const
{	
	IECore::ConstPrimitivePtr inputGeometry = IECore::runTimeCast<const IECore::Primitive>( inputObject );
	if( !inputGeometry )
	{
		return inputObject;
	}

	const std::string fileName = fileNamePlug()->getValue();
	const float frame = context->getFrame();
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
		return inputGeometry;
	}
	
	IECore::PrimitivePtr result = inputGeometry->copy();
	for( std::vector<IECore::InterpolatedCache::AttributeHandle>::const_iterator it = attributeNames.begin(); it!=attributeNames.end(); it++ )
	{
		if( it->value().compare( 0, 8, "primVar:" )==0 )
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
	std::string result = "";
	for( ScenePath::const_iterator it = path.begin(), eIt = path.end(); it != eIt; it++ )
	{
		result += "/" + it->value();
	}
	return result;
}
