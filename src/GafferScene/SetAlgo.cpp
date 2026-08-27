//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/SetAlgo.h"

#include "Gaffer/SetExpressionAlgo.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

namespace
{

struct SceneSetProvider : public Gaffer::SetExpressionAlgo::SetProvider
{
	SceneSetProvider( const ScenePlug *scene )
		: m_scene( scene )
	{
	}

	IECore::ConstInternedStringVectorDataPtr setNames() const override
	{
		return m_scene->setNames();
	}

	const IECore::PathMatcher paths( const std::string &setName ) const override
	{
		return m_scene->set( setName )->readable();
	}

	void hash( const std::string &setName, IECore::MurmurHash &h ) const override
	{
		h.append( m_scene->setHash( setName ) );
	}

	const ScenePlug *m_scene;
};

} // namespace

namespace GafferScene
{

namespace SetAlgo
{

PathMatcher evaluateSetExpression( const std::string &setExpression, const ScenePlug *scene )
{
	return SetExpressionAlgo::evaluateSetExpression( setExpression, SceneSetProvider( scene ) );
}

void setExpressionHash( const std::string &setExpression, const ScenePlug *scene, IECore::MurmurHash &h )
{
	SetExpressionAlgo::setExpressionHash( setExpression, SceneSetProvider( scene ), h );
}

IECore::MurmurHash setExpressionHash( const std::string &setExpression, const ScenePlug *scene )
{
	IECore::MurmurHash h = IECore::MurmurHash();
	setExpressionHash( setExpression, scene, h );
	return h;
}

bool affectsSetExpression( const Plug *scenePlugChild )
{
	if( auto parent = scenePlugChild->parent<ScenePlug>() )
	{
		return
			scenePlugChild == parent->setPlug() ||
			scenePlugChild == parent->setNamesPlug()
		;
	}
	return false;
}

} // namespace SetAlgo

} // namespace GafferScene
