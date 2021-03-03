//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/Private/IECoreScenePreview/Renderer.h"

#include "IECore/Exception.h"

using namespace std;
using namespace IECoreScenePreview;

//////////////////////////////////////////////////////////////////////////
// Registry
//////////////////////////////////////////////////////////////////////////

namespace
{

using Creator = Renderer::Ptr (*)( Renderer::RenderType, const std::string &, const IECore::MessageHandlerPtr & );

vector<IECore::InternedString> &types()
{
	static vector<IECore::InternedString> g_types;
	return g_types;
}

using CreatorMap = map<IECore::InternedString, Creator>;
CreatorMap &creators()
{
	static CreatorMap g_creators;
	return g_creators;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Renderer
//////////////////////////////////////////////////////////////////////////

Renderer::Renderer()
{

}

Renderer::~Renderer()
{

}

Renderer::ObjectInterfacePtr Renderer::camera( const std::string &name,  const std::vector<const IECoreScene::Camera *> &samples, const std::vector<float> &times, const AttributesInterface *attributes )
{
	return camera( name, samples[0], attributes );
}

IECore::DataPtr Renderer::command( const IECore::InternedString name, const IECore::CompoundDataMap &parameters )
{
	throw IECore::NotImplementedException( "Renderer::command" );
}

Renderer::AttributesInterface::~AttributesInterface()
{

}

Renderer::ObjectInterface::~ObjectInterface()
{

}

const std::vector<IECore::InternedString> &Renderer::types()
{
	return ::types();
}

Renderer::Ptr Renderer::create( const IECore::InternedString &type, RenderType renderType, const std::string &fileName, const IECore::MessageHandlerPtr &messageHandler )
{
	const CreatorMap &c = creators();
	CreatorMap::const_iterator it = c.find( type );
	if( it == c.end() )
	{
		return nullptr;
	}
	return it->second( renderType, fileName, messageHandler );
}


void Renderer::registerType( const IECore::InternedString &typeName, Ptr (*creator)( RenderType, const std::string &, const IECore::MessageHandlerPtr & ) )
{
	CreatorMap &c = creators();
	CreatorMap::iterator it = c.find( typeName );
	if( it != c.end() )
	{
		it->second = creator;
		return;
	}
	c[typeName] = creator;
	::types().push_back( typeName );
}
