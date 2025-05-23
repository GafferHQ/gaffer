//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Image Engine Design Inc. All rights reserved.
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

#include "RenderManifestBinding.h"

#include "GafferScene/RenderManifest.h"

#include "boost/python/suite/indexing/container_utils.hpp"

using namespace boost::python;
using namespace Gaffer;
using namespace GafferScene;

namespace
{

object pathForIDWrapper( const RenderManifest &renderManifest, uint32_t id )
{
	if( auto result = renderManifest.pathForID( id ) )
	{
		return object( ScenePlug::pathToString( *result ) );
	}
	return object();
}

list idList( const std::vector<uint32_t> &ids )
{
	list result;
	for( auto id : ids )
	{
		result.append( id );
	}
	return result;
}

list acquireIDsWrapper( RenderManifest &manifest, const IECore::PathMatcher &paths )
{
	return idList( manifest.acquireIDs( paths ) );
}

list idsForPathsWrapper( const RenderManifest &manifest, const IECore::PathMatcher &paths )
{
	return idList( manifest.idsForPaths( paths ) );
}

IECore::PathMatcher pathsForIDsWrapper( const RenderManifest &manifest, object &pythonIds )
{
	std::vector<uint32_t> ids;
	boost::python::container_utils::extend_container( ids, pythonIds );
	return manifest.pathsForIDs( ids );
}

std::shared_ptr<RenderManifest> loadFromImageMetadataWrapper( const IECore::CompoundData *metadata, const std::string &cryptomatteLayerName )
{
	return std::const_pointer_cast<RenderManifest>( RenderManifest::loadFromImageMetadata( metadata, cryptomatteLayerName ) );
}

} // namespace

void GafferSceneModule::bindRenderManifest()
{

	class_<RenderManifest, boost::noncopyable, std::shared_ptr<RenderManifest>>( "RenderManifest" )
		.def( "acquireID", &RenderManifest::acquireID )
		.def( "idForPath", &RenderManifest::idForPath )
		.def( "pathForID", &pathForIDWrapper )
		.def( "acquireIDs", &acquireIDsWrapper )
		.def( "idsForPaths", &idsForPathsWrapper )
		.def( "pathsForIDs", &pathsForIDsWrapper )
		.def( "clear", &RenderManifest::clear )
		.def( "size", &RenderManifest::size )
		.def( "loadFromImageMetadata", &loadFromImageMetadataWrapper )
		.staticmethod( "loadFromImageMetadata" )
		.def( "writeEXRManifest", &RenderManifest::writeEXRManifest )
	;

}
