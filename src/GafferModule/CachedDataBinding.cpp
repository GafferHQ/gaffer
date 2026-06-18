//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

#include "boost/python.hpp"

#include "CachedDataBinding.h"

#include "GafferBindings/DependencyNodeBinding.h"
#include "GafferBindings/ValuePlugBinding.h"

#include "Gaffer/CachedDataNode.h"


#include "fmt/format.h"
#include "fmt/ranges.h"

using namespace boost::python;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;

namespace
{

class CachedDataNodeSerialiser : public NodeSerialiser
{
	std::string constructor( const Gaffer::GraphComponent *graphComponent, Serialisation &serialisation ) const override
	{
		const CachedDataNode *node = IECore::runTimeCast<const CachedDataNode>( graphComponent );

		serialisation.addModule( "IECore" );
		if( serialisation.cacheDir() )
		{
			node->save( *serialisation.cacheDir(), serialisation.usedCaches(), serialisation.warning() );
		}
		else
		{
			if( node->hasLiveEntries() )
			{
				throw IECore::Exception( "Cannot copy nodes that include caches that haven't yet been saved." );
			}
		}

		// TODO - I haven't confirmed exactly why using ValuePlugSerialiser::valueRepr here results in:
		// TypeError: No to_python (by-value) converter found for C++ type: IECore::CompoundObject
		// But maybe it's better to use a hardcoded C++ serialisation of this CompoundData holding
		// StringData anyway?

		auto caches = node->entryHashes();
		std::vector<std::string> cacheTokens;
		for( const auto &it : caches )
		{
			cacheTokens.push_back( fmt::format( R"("{}" : IECore.StringData( "{}" ))", it.first, it.second.toString() ) );
			//cacheTokens.push_back( fmt::format( "{} : {}", it.first, it.second.toString() ) );
		}
		std::string cachesRepr = fmt::format( "IECore.CompoundData( {{ {} }} )", fmt::join( cacheTokens, ", " ) );

		std::string mySerial = fmt::format(
			"Gaffer.CachedDataNode( \"{}\", \"{}\", {} )",
			node->getName().string(), std::filesystem::absolute( node->sourceDirectory() ).string(), cachesRepr
		);


		return mySerial;
	}
};

IECore::ObjectPtr getEntryWrapper( const CachedDataNode &cachedDataNode, const IECore::InternedString &key, bool throwExceptions )
{
	return cachedDataNode.getEntry( key, throwExceptions )->copy();
}

} // namespace

void GafferModule::bindCachedData()
{

	scope s = DependencyNodeClass<CachedDataNode>()
		.def( init<std::string, std::string, IECore::CompoundDataPtr>( ( arg( "name" )=GraphComponent::defaultName<CachedDataNode>(), arg( "sourceDirectory") = "", arg( "caches" ) = object() ) ) )
		.def( "save", &CachedDataNode::save )
		.def( "setEntry", &CachedDataNode::setEntry )
		.def( "getEntry", &getEntryWrapper, ( arg_( "key" ), arg_( "throwExceptions" ) = true ) )
		.def( "hasLiveEntries", &CachedDataNode::hasLiveEntries )
	;

	Serialisation::registerSerialiser( Gaffer::CachedDataNode::staticTypeId(), new CachedDataNodeSerialiser );

}
