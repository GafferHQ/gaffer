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

#include "OpenEXR/ImathBoxAlgo.h"

#include "Gaffer/Context.h"

#include "GafferScene/GroupScenes.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( GroupScenes );

GroupScenes::GroupScenes( const std::string &name )
	:	SceneProcessor( name )
{
	addChild( new StringPlug( "name", Plug::In, "group" ) );
	addChild( new TransformPlug( "transform" ) );
}

GroupScenes::~GroupScenes()
{
}

Gaffer::StringPlug *GroupScenes::namePlug()
{
	return getChild<StringPlug>( "name" );
}

const Gaffer::StringPlug *GroupScenes::namePlug() const
{
	return getChild<StringPlug>( "name" );
}

Gaffer::TransformPlug *GroupScenes::transformPlug()
{
	return getChild<TransformPlug>( "transform" );
}

const Gaffer::TransformPlug *GroupScenes::transformPlug() const
{
	return getChild<TransformPlug>( "transform" );
}

void GroupScenes::affects( const ValuePlug *input, AffectedPlugsContainer &outputs ) const
{
	SceneProcessor::affects( input, outputs );
	
	if( input == namePlug() || input == inPlug()->childNamesPlug() )
	{
		outputs.push_back( outPlug() );
	}
	else if( transformPlug()->isAncestorOf( input ) )
	{
		/// \todo Strictly speaking I think we should just push outPlug()->transformPlug()
		/// here, but the dirty propagation doesn't work for that just now. Get it working.
		outputs.push_back( outPlug() );
	}
	
}

Imath::Box3f GroupScenes::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	std::string groupName = namePlug()->getValue();
	std::string source = sourcePath( path, groupName );
	
	if( !source.size() )
	{
		Imath::Box3f b = inPlug()->bound( "/" );
		Imath::M44f t = inPlug()->transform( "/" );
		return transform( b, t );	
	}
	else
	{
		return inPlug()->bound( source );
	}
}

Imath::M44f GroupScenes::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	std::string groupName = namePlug()->getValue();
	std::string source = sourcePath( path, groupName );
	
	if( !source.size() )
	{
		return transformPlug()->matrix();
	}
	else
	{
		return inPlug()->transform( source );
	}
}

IECore::PrimitivePtr GroupScenes::computeGeometry( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	std::string groupName = namePlug()->getValue();
	std::string source = sourcePath( path, groupName );
	
	if( !source.size() )
	{
		return 0;
	}
	else
	{
		ConstPrimitivePtr g = inPlug()->geometry( source );
		return g ? g->copy() : 0;
	}
}

IECore::StringVectorDataPtr GroupScenes::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{	
	std::string groupName = namePlug()->getValue();
	std::string source = sourcePath( path, groupName );
	
	if( !source.size() )
	{
		StringVectorDataPtr result = new StringVectorData();
		result->writable().push_back( groupName );
		return result;
	}
	else
	{
		ConstStringVectorDataPtr c = inPlug()->childNames( source );
		return c ? c->copy() : 0;
	}
}

std::string GroupScenes::sourcePath( const std::string &outputPath, const std::string &groupName ) const
{
	// we're a pass through if no group name is given
	if( !groupName.size() )
	{
		return outputPath;
	}
	
	// if the root is requested then we have nowhere from the input to map from.
	// the compute functions will conjure up a new top level node.
	if( outputPath=="/" )
	{
		return "";
	}
	
	if( outputPath.size() == groupName.size() + 1 )
	{
		return "/";
	}
	else
	{
		return std::string( outputPath, groupName.size() + 1 );	
	}
}
