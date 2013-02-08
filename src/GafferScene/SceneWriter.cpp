//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2013, Image Engine Design inc. All rights reserved.
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

#include "GafferScene/SceneWriter.h"
#include "Gaffer/Context.h"

#include "IECore/SceneInterface.h"
#include "IECore/Transform.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( SceneWriter );

size_t SceneWriter::g_firstPlugIndex = 0;

SceneWriter::SceneWriter( const std::string &name )
	:	Node( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "in", Plug::In ) );
	addChild( new StringPlug( "fileName" ) );
}

SceneWriter::~SceneWriter()
{
}

ScenePlug *SceneWriter::inPlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const ScenePlug *SceneWriter::inPlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

StringPlug *SceneWriter::fileNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const StringPlug *SceneWriter::fileNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

void SceneWriter::writeLocation( GafferScene::ScenePlug *scenePlug, const ScenePlug::ScenePath &scenePath, IECore::SceneInterface *output )
{
	ContextPtr context = new Context;
	
	context->set( ScenePlug::scenePathContextName, scenePath );
	
	Context::Scope scopedContext( context );
	
	ConstCompoundObjectPtr attributes = scenePlug->attributesPlug()->getValue();
	for( CompoundObject::ObjectMap::const_iterator it = attributes->members().begin(), eIt = attributes->members().end(); it != eIt; it++ )
	{
		output->writeAttribute( it->first, it->second.get(), 0 );
	}
	
	ConstObjectPtr object = scenePlug->objectPlug()->getValue();
	
	if( object && scenePath.size() > 1 )
	{
		output->writeObject( object, 0 );
	}
	
	Imath::Box3f b = scenePlug->boundPlug()->getValue();
	
	output->writeBound( Imath::Box3d( Imath::V3f( b.min ), Imath::V3f( b.max ) ), 0.0 );
	
	if( scenePath.size() )
	{
		Imath::M44f t = scenePlug->transformPlug()->getValue();
		Imath::M44d transform(
			t[0][0], t[0][1], t[0][2], t[0][3],
			t[1][0], t[1][1], t[1][2], t[1][3],
			t[2][0], t[2][1], t[2][2], t[2][3],
			t[3][0], t[3][1], t[3][2], t[3][3]
		);

		output->writeTransform( new IECore::M44dData( transform ), 0.0 );
	}
	
	ConstInternedStringVectorDataPtr childNames = scenePlug->childNamesPlug()->getValue();
	
	ScenePlug::ScenePath childScenePath = scenePath;
	childScenePath.push_back( InternedString() );
	for( vector<InternedString>::const_iterator it=childNames->readable().begin(); it!=childNames->readable().end(); it++ )
	{
		childScenePath[scenePath.size()] = *it;
		
		SceneInterfacePtr outputChild = output->createChild( *it );
		
		writeLocation( scenePlug, childScenePath, outputChild );
	}	
	
}


void SceneWriter::execute()
{
	ScenePlug* scenePlug = inPlug();

	SceneInterfacePtr output = SceneInterface::create( fileNamePlug()->getValue(), IndexedIO::Write );
	
	writeLocation( scenePlug, ScenePlug::ScenePath(), output.get() );
}
