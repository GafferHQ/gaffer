//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/Context.h"

#include "GafferScene/SceneElementProcessor.h"
#include "GafferScene/Filter.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( SceneElementProcessor );

size_t SceneElementProcessor::g_firstPlugIndex = 0;

SceneElementProcessor::SceneElementProcessor( const std::string &name, Filter::Result filterDefault )
	:	FilteredSceneProcessor( name, filterDefault )
{
	storeIndexOfNextChild( g_firstPlugIndex );
}

SceneElementProcessor::~SceneElementProcessor()
{
}
		
void SceneElementProcessor::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	/// \todo Our base classes will say that enabledPlug() affects all children of outPlug() - perhaps
	/// we can do better by affecting only the plugs we know we're going to process?
	FilteredSceneProcessor::affects( input, outputs );
	
	const ScenePlug *in = inPlug();
	if( input->parent<ScenePlug>() == in )
	{
		outputs.push_back( outPlug()->getChild<ValuePlug>( input->getName() ) );
	}
	else if( input == filterPlug() )
	{
		for( ValuePlugIterator it( outPlug() ); it != it.end(); it++ )
		{
			outputs.push_back( it->get() );
		}
	}
}

void SceneElementProcessor::hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	switch( boundMethod() )
	{
		case Direct :
			FilteredSceneProcessor::hashBound( path, context, parent, h );
			inPlug()->boundPlug()->hash( h );
			hashProcessedBound( path, context, h );
			break;
		case Union :
			h = hashOfTransformedChildBounds( path, outPlug() );
			break;
		case PassThrough :
			h = inPlug()->boundPlug()->hash();
			break;
	}
}

void SceneElementProcessor::hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	Filter::Result match = Filter::NoMatch;
	if( processesTransform() )
	{
		match = (Filter::Result)filterPlug()->getValue();
	}

	if( match == Filter::Match )
	{
		FilteredSceneProcessor::hashTransform( path, context, parent, h );
		inPlug()->transformPlug()->hash( h );
		hashProcessedTransform( path, context, h );
	}
	else
	{
		// pass through
		h = inPlug()->transformPlug()->hash();
	}
}

void SceneElementProcessor::hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	Filter::Result match = Filter::NoMatch;
	if( processesAttributes() )
	{
		match = (Filter::Result)filterPlug()->getValue();
	}

	if( match == Filter::Match )
	{
		FilteredSceneProcessor::hashAttributes( path, context, parent, h );
		inPlug()->attributesPlug()->hash( h );
		hashProcessedAttributes( path, context, h );
	}
	else
	{
		// pass through
		h = inPlug()->attributesPlug()->hash();
	}
}

void SceneElementProcessor::hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	Filter::Result match = Filter::NoMatch;
	if( processesObject() )
	{
		match = (Filter::Result)filterPlug()->getValue();
	}

	if( match == Filter::Match )
	{
		FilteredSceneProcessor::hashObject( path, context, parent, h );
		inPlug()->objectPlug()->hash( h );
		hashProcessedObject( path, context, h );
	}
	else
	{
		// pass through
		h = inPlug()->objectPlug()->hash();
	}
}

void SceneElementProcessor::hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	h = inPlug()->childNamesPlug()->hash();
}

void SceneElementProcessor::hashGlobals( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	h = inPlug()->globalsPlug()->hash();
}

Imath::Box3f SceneElementProcessor::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	switch( boundMethod() )
	{
		case Direct :
			return computeProcessedBound( path, context, inPlug()->boundPlug()->getValue() );
		case Union :
			return unionOfTransformedChildBounds( path, outPlug() );
		default :
			return inPlug()->boundPlug()->getValue();
	}
}

Imath::M44f SceneElementProcessor::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( filterPlug()->getValue() == Filter::Match )
	{
		return computeProcessedTransform( path, context, inPlug()->transformPlug()->getValue() );
	}
	else
	{
		return inPlug()->transformPlug()->getValue();
	}
}

IECore::ConstCompoundObjectPtr SceneElementProcessor::computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( filterPlug()->getValue() == Filter::Match )
	{
		return computeProcessedAttributes( path, context, inPlug()->attributesPlug()->getValue() );
	}
	else
	{
		return inPlug()->attributesPlug()->getValue();
	}
}

IECore::ConstObjectPtr SceneElementProcessor::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( filterPlug()->getValue() == Filter::Match )
	{
		return computeProcessedObject( path, context, inPlug()->objectPlug()->getValue() );
	}
	else
	{
		return inPlug()->objectPlug()->getValue();
	}
}

IECore::ConstInternedStringVectorDataPtr SceneElementProcessor::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	return inPlug()->childNamesPlug()->getValue();
}

IECore::ConstCompoundObjectPtr SceneElementProcessor::computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	return inPlug()->globalsPlug()->getValue();
}

bool SceneElementProcessor::processesBound() const
{
	return false;
}

void SceneElementProcessor::hashProcessedBound( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
}

Imath::Box3f SceneElementProcessor::computeProcessedBound( const ScenePath &path, const Gaffer::Context *context, const Imath::Box3f &inputBound ) const
{
	return inputBound;
}

bool SceneElementProcessor::processesTransform() const
{
	return false;
}

void SceneElementProcessor::hashProcessedTransform( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
}

Imath::M44f SceneElementProcessor::computeProcessedTransform( const ScenePath &path, const Gaffer::Context *context, const Imath::M44f &inputTransform ) const
{
	return inputTransform;
}

bool SceneElementProcessor::processesAttributes() const
{
	return false;
}

void SceneElementProcessor::hashProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
}

IECore::ConstCompoundObjectPtr SceneElementProcessor::computeProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::ConstCompoundObjectPtr inputAttributes ) const
{
	return inputAttributes;
}

bool SceneElementProcessor::processesObject() const
{
	return false;
}

void SceneElementProcessor::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
}

IECore::ConstObjectPtr SceneElementProcessor::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::ConstObjectPtr inputObject ) const
{
	return inputObject;
}

SceneElementProcessor::BoundMethod SceneElementProcessor::boundMethod() const
{
	const bool pBound = processesBound();
	const bool pTransform = processesTransform();
	
	if( pBound || pTransform )
	{
		Filter::Result f = (Filter::Result)filterPlug()->getValue();
		if( f == Filter::Match )
		{
			if( pBound )
			{
				return Direct;
			}
			else
			{
				// changing only the transform at a matched location has no effect
				// on the bound of that location - fall through to default case.
			}
		}
		else if( f == Filter::DescendantMatch )
		{
			return Union;
		}
	}
	
	return PassThrough;
}
