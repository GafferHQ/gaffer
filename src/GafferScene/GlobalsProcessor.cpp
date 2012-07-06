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

#include "GafferScene/GlobalsProcessor.h"

using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( GlobalsProcessor );

GlobalsProcessor::GlobalsProcessor( const std::string &name )
	:	SceneProcessor( name )
{
}

GlobalsProcessor::~GlobalsProcessor()
{
}

void GlobalsProcessor::affects( const ValuePlug *input, AffectedPlugsContainer &outputs ) const
{
	SceneProcessor::affects( input, outputs );
	
	const ScenePlug *in = inPlug();
	if( input->parent<ScenePlug>() == in )
	{
		outputs.push_back( outPlug()->getChild<ValuePlug>( input->getName() ) );
	}
}

Imath::Box3f GlobalsProcessor::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	return inPlug()->boundPlug()->getValue();
}

Imath::M44f GlobalsProcessor::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	return inPlug()->transformPlug()->getValue();
}

IECore::ObjectVectorPtr GlobalsProcessor::computeState( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	IECore::ConstObjectVectorPtr s = inPlug()->statePlug()->getValue();
	return s ? s->copy() : 0;
}

IECore::ObjectPtr GlobalsProcessor::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	IECore::ConstObjectPtr o = inPlug()->objectPlug()->getValue();
	return o ? o->copy() : 0;
}

IECore::StringVectorDataPtr GlobalsProcessor::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	IECore::ConstStringVectorDataPtr names = inPlug()->childNamesPlug()->getValue();
	return names ? names->copy() : 0;
}

IECore::ObjectVectorPtr GlobalsProcessor::computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	IECore::ConstObjectVectorPtr globals = inPlug()->globalsPlug()->getValue();
	return processGlobals( context, globals );
}
