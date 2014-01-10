//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/Transform.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( Transform );

size_t Transform::g_firstPlugIndex = 0;

Transform::Transform( const std::string &name )
	:	SceneElementProcessor( name, Filter::NoMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new IntPlug( "space", Plug::In, World, World, Object ) );
	addChild( new TransformPlug( "transform" ) );
}

Transform::~Transform()
{
}

Gaffer::IntPlug *Transform::spacePlug()
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *Transform::spacePlug() const
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex );
}

Gaffer::TransformPlug *Transform::transformPlug()
{
	return getChild<Gaffer::TransformPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::TransformPlug *Transform::transformPlug() const
{
	return getChild<Gaffer::TransformPlug>( g_firstPlugIndex + 1 );
}

void Transform::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneElementProcessor::affects( input, outputs );
	
	if( input == spacePlug() || transformPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( outPlug()->transformPlug() );
		outputs.push_back( outPlug()->boundPlug() );
	}
}

bool Transform::processesTransform() const
{
	return true;
}

void Transform::hashProcessedTransform( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	spacePlug()->hash( h );
	transformPlug()->hash( h );
}

Imath::M44f Transform::computeProcessedTransform( const ScenePath &path, const Gaffer::Context *context, const Imath::M44f &inputTransform ) const
{
	Space space = static_cast<Space>( spacePlug()->getValue() );
	Imath::M44f matrix = transformPlug()->matrix();
	if( space == World )
	{
		return inputTransform * matrix;
	}
	else
	{
		return matrix * inputTransform;
	}
}
