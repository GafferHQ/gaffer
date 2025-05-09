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

using namespace boost::python;
using namespace Gaffer;
using namespace GafferScene;

namespace
{

// Convert return path to string for Python
std::optional< std::string > pathForIDWrapper( RenderManifest *renderManifest, uint32_t id )
{
	// Return a InternedStringVectorDataPtr or None, since our Python bindings don't know how to
	// deal with an optional<ScenePlug::ScenePath>
	auto result = renderManifest->pathForID( id );
	if( !result )
	{
		return std::nullopt;
	}

	return ScenePlug::pathToString( *result );
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
		.def( "acquireIDs", &RenderManifest::acquireIDs )
		.def( "pathsForIDs", &RenderManifest::pathsForIDs )
		.def( "clear", &RenderManifest::clear )
		.def( "size", &RenderManifest::size )
		.def( "loadFromImageMetadata", &loadFromImageMetadataWrapper )
		.staticmethod( "loadFromImageMetadata" )
		.def( "writeEXRManifest", &RenderManifest::writeEXRManifest )
	;

}
