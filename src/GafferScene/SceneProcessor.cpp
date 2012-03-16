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

#include "GafferScene/SceneProcessor.h"

using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( SceneProcessor );

SceneProcessor::SceneProcessor( const std::string &name )
	:	SceneNode( name )
{
	addChild( new ScenePlug( "in", Gaffer::Plug::In ) );
}

SceneProcessor::~SceneProcessor()
{
}

ScenePlug *SceneProcessor::inPlug()
{
	return getChild<ScenePlug>( "in" );
}

const ScenePlug *SceneProcessor::inPlug() const
{
	return getChild<ScenePlug>( "in" );
}

void SceneProcessor::affects( const ValuePlug *input, AffectedPlugsContainer &outputs ) const
{
	SceneNode::affects( input, outputs );
	
	const ScenePlug *in = inPlug();
	if( input->parent<ScenePlug>() == in )
	{
		outputs.push_back( outPlug()->getChild<ValuePlug>( input->getName() ) );
	}
}

Imath::Box3f SceneProcessor::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	return processBound( path, context, inPlug()->boundPlug()->getValue() );
}

Imath::M44f SceneProcessor::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	return processTransform( path, context, inPlug()->transformPlug()->getValue() );
}

IECore::PrimitivePtr SceneProcessor::computeGeometry( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	return processGeometry( path, context, inPlug()->geometryPlug()->getValue() );
}

IECore::StringVectorDataPtr SceneProcessor::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	IECore::ConstStringVectorDataPtr names = inPlug()->childNamesPlug()->getValue();
	if( names )
	{
		return names->copy();
	}
	return 0;
}

Imath::Box3f SceneProcessor::processBound( const ScenePath &path, const Gaffer::Context *context, const Imath::Box3f &inputBound ) const
{
	return inputBound;
}

Imath::M44f SceneProcessor::processTransform( const ScenePath &path, const Gaffer::Context *context, const Imath::M44f &inputTransform ) const
{
	return inputTransform;
}

IECore::PrimitivePtr SceneProcessor::processGeometry( const ScenePath &path, const Gaffer::Context *context, IECore::ConstPrimitivePtr inputGeometry ) const
{
	if( inputGeometry )
	{
		return inputGeometry->copy();
	}
	return 0;
}
