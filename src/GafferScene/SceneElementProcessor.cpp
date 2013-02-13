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

#include "GafferScene/SceneElementProcessor.h"
#include "GafferScene/Filter.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( SceneElementProcessor );

size_t SceneElementProcessor::g_firstPlugIndex = 0;

SceneElementProcessor::SceneElementProcessor( const std::string &name )
	:	SceneProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new IntPlug( "filter", Plug::In, Filter::Match, Filter::NoMatch, Filter::Match ) );
}

SceneElementProcessor::~SceneElementProcessor()
{
}

Gaffer::IntPlug *SceneElementProcessor::filterPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *SceneElementProcessor::filterPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}
		
void SceneElementProcessor::affects( const ValuePlug *input, AffectedPlugsContainer &outputs ) const
{
	SceneProcessor::affects( input, outputs );
	
	const ScenePlug *in = inPlug();
	if( input->parent<ScenePlug>() == in )
	{
		outputs.push_back( outPlug()->getChild<ValuePlug>( input->getName() ) );
	}
	else if( input == filterPlug() )
	{
		outputs.push_back( outPlug() );
	}
}

bool SceneElementProcessor::acceptsInput( const Gaffer::Plug *plug, const Gaffer::Plug *inputPlug ) const
{
	if( !SceneProcessor::acceptsInput( plug, inputPlug ) )
	{
		return false;
	}
	
	if( plug == filterPlug() )
	{
		const Node *n = inputPlug->source<Plug>()->node();	
		if( !n || !n->isInstanceOf( Filter::staticTypeId() ) )
		{
			return false;
		}
	}
	return true;
}

void SceneElementProcessor::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( output->parent<ScenePlug>() == outPlug() )
	{
		if( output == outPlug()->globalsPlug() ||
			output == outPlug()->childNamesPlug()
		)
		{
			// pass through
			h = inPlug()->getChild<ValuePlug>( output->getName() )->hash();
		}
		else if( output == outPlug()->boundPlug() )
		{
			if( processesBound() || processesTransform() )
			{
				SceneProcessor::hash( output, context, h );
				inPlug()->boundPlug()->hash( h );
				hashBound( context, h );
				hashTransform( context, h );
			}
			else
			{
				// pass through
				h = inPlug()->boundPlug()->hash();
			}
		}
		else
		{
			// transform, attributes or object
			Filter::Result match = Filter::NoMatch;
			if( ( output == outPlug()->transformPlug() && processesTransform() ) ||
				( output == outPlug()->attributesPlug() && processesAttributes() ) ||
				( output == outPlug()->objectPlug() && processesObject() )
			)
			{
				match = (Filter::Result)filterPlug()->getValue();
			}
			
			if( match == Filter::Match )
			{
				SceneProcessor::hash( output, context, h );
				inPlug()->getChild<ValuePlug>( output->getName() )->hash( h );
				if( output == outPlug()->transformPlug() )
				{
					hashTransform( context, h );
				}
				else if( output == outPlug()->attributesPlug() )
				{
					hashAttributes( context, h );
				}
				else
				{
					// object plug
					hashObject( context, h );
				}
			}
			else
			{
				// pass through
				h = inPlug()->getChild<ValuePlug>( output->getName() )->hash();
			}
		}
	}
	else
	{
		SceneProcessor::hash( output, context, h );
	}
}

Imath::Box3f SceneElementProcessor::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( processesBound() )
	{
		Filter::Result f = (Filter::Result)filterPlug()->getValue();
		if( f == Filter::Match )
		{
			return processBound( path, context, inPlug()->boundPlug()->getValue() );
		}
		else if( f == Filter::DescendantMatch )
		{
			return unionOfTransformedChildBounds( path, outPlug() );
		}
	}
	
	return inPlug()->boundPlug()->getValue();
}

Imath::M44f SceneElementProcessor::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( filterPlug()->getValue() == Filter::Match )
	{
		return processTransform( path, context, inPlug()->transformPlug()->getValue() );
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
		return processAttributes( path, context, inPlug()->attributesPlug()->getValue() );
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
		return processObject( path, context, inPlug()->objectPlug()->getValue() );
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

void SceneElementProcessor::hashBound( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
}

Imath::Box3f SceneElementProcessor::processBound( const ScenePath &path, const Gaffer::Context *context, const Imath::Box3f &inputBound ) const
{
	return inputBound;
}

bool SceneElementProcessor::processesTransform() const
{
	return false;
}

void SceneElementProcessor::hashTransform( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
}

Imath::M44f SceneElementProcessor::processTransform( const ScenePath &path, const Gaffer::Context *context, const Imath::M44f &inputTransform ) const
{
	return inputTransform;
}

bool SceneElementProcessor::processesAttributes() const
{
	return false;
}

void SceneElementProcessor::hashAttributes( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
}

IECore::ConstCompoundObjectPtr SceneElementProcessor::processAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::ConstCompoundObjectPtr inputAttributes ) const
{
	return inputAttributes;
}

bool SceneElementProcessor::processesObject() const
{
	return false;
}

void SceneElementProcessor::hashObject( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
}

IECore::ConstObjectPtr SceneElementProcessor::processObject( const ScenePath &path, const Gaffer::Context *context, IECore::ConstObjectPtr inputObject ) const
{
	return inputObject;
}
