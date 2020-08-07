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
#include "GafferScene/SceneAlgo.h"

#include "IECore/Exception.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( SceneElementProcessor );

size_t SceneElementProcessor::g_firstPlugIndex = 0;

SceneElementProcessor::SceneElementProcessor( const std::string &name, IECore::PathMatcher::Result filterDefault )
	:	FilteredSceneProcessor( name, filterDefault )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	outPlug()->childBoundsPlug()->setFlags( Plug::AcceptsDependencyCycles, true );

	// We don't ever want to change the scene hierarchy, globals, or sets,
	// so we make pass-through connections for them. This is quicker than
	// implementing a pass through of the input in the hash and compute
	// methods.
	outPlug()->childNamesPlug()->setInput( inPlug()->childNamesPlug() );
	outPlug()->globalsPlug()->setInput( inPlug()->globalsPlug() );
	outPlug()->setNamesPlug()->setInput( inPlug()->setNamesPlug() );
	outPlug()->setPlug()->setInput( inPlug()->setPlug() );
}

SceneElementProcessor::~SceneElementProcessor()
{
}

void SceneElementProcessor::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	FilteredSceneProcessor::affects( input, outputs );

	if(
		input == filterPlug() ||
		input == inPlug()->boundPlug() ||
		input == inPlug()->childNamesPlug() ||
		input == outPlug()->childBoundsPlug() ||
		input == inPlug()->objectPlug()
	)
	{
		outputs.push_back( outPlug()->boundPlug() );
	}

	if(
		input == filterPlug() ||
		input == inPlug()->transformPlug()
	)
	{
		outputs.push_back( outPlug()->transformPlug() );
	}

	if(
		input == filterPlug() ||
		input == inPlug()->attributesPlug()
	)
	{
		outputs.push_back( outPlug()->attributesPlug() );
	}

	if(
		input == filterPlug() ||
		input == inPlug()->objectPlug()
	)
	{
		outputs.push_back( outPlug()->objectPlug() );
	}
}

void SceneElementProcessor::hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	switch( boundMethod( context ) )
	{
		case Processed :
			FilteredSceneProcessor::hashBound( path, context, parent, h );
			inPlug()->boundPlug()->hash( h );
			hashProcessedBound( path, context, h );
			break;
		case Union :
		{
			ConstInternedStringVectorDataPtr childNames = inPlug()->childNamesPlug()->getValue();
			if( childNames->readable().size() )
			{
				FilteredSceneProcessor::hashBound( path, context, parent, h );
				outPlug()->childBoundsPlug()->hash( h );
				inPlug()->objectPlug()->hash( h );
			}
			else
			{
				h = inPlug()->boundPlug()->hash();
			}
			break;
		}
		case PassThrough :
			h = inPlug()->boundPlug()->hash();
			break;
	}
}

Imath::Box3f SceneElementProcessor::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	switch( boundMethod( context ) )
	{
		case Processed :
			return computeProcessedBound( path, context, inPlug()->boundPlug()->getValue() );
		case Union :
		{
			// We want to return the union of all the transformed child bounds and the
			// bound for the object at this location. But we want to avoid computing the
			// object itself at all costs for obvious reasons - a bound should be a thing
			// you compute cheaply before deciding if you want the object or not.
			Imath::Box3f result;
			ConstInternedStringVectorDataPtr childNames = inPlug()->childNamesPlug()->getValue();
			if( childNames->readable().size() )
			{
				result = outPlug()->childBoundsPlug()->getValue();
				// We do have to resort to computing the object here, but its exceedingly
				// rare to have an object at a location which also has children, so typically
				// we should be receiving a NullObject cheaply.
				result.extendBy( SceneAlgo::bound( inPlug()->objectPlug()->getValue().get() ) );
			}
			else
			{
				// Because there are no children, we know that the input bound is the
				// bound of the input object on its own, and can just pass that through
				// directly.
				result = inPlug()->boundPlug()->getValue();
			}
			return result;
		}
		default :
			return inPlug()->boundPlug()->getValue();
	}
}

void SceneElementProcessor::hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	IECore::PathMatcher::Result match = IECore::PathMatcher::NoMatch;
	if( processesTransform() )
	{
		match = filterValue( context );
	}

	if( match & IECore::PathMatcher::ExactMatch )
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

Imath::M44f SceneElementProcessor::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( filterValue( context ) & IECore::PathMatcher::ExactMatch )
	{
		return computeProcessedTransform( path, context, inPlug()->transformPlug()->getValue() );
	}
	else
	{
		return inPlug()->transformPlug()->getValue();
	}
}

void SceneElementProcessor::hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	IECore::PathMatcher::Result match = IECore::PathMatcher::NoMatch;
	if( processesAttributes() )
	{
		match = filterValue( context );
	}

	if( match & IECore::PathMatcher::ExactMatch )
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

IECore::ConstCompoundObjectPtr SceneElementProcessor::computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( filterValue( context ) & IECore::PathMatcher::ExactMatch )
	{
		return computeProcessedAttributes( path, context, inPlug()->attributesPlug()->getValue() );
	}
	else
	{
		return inPlug()->attributesPlug()->getValue();
	}
}

void SceneElementProcessor::hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	IECore::PathMatcher::Result match = IECore::PathMatcher::NoMatch;
	if( processesObject() )
	{
		match = filterValue( context );
	}

	if( match & IECore::PathMatcher::ExactMatch )
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

IECore::ConstObjectPtr SceneElementProcessor::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( filterValue( context ) & IECore::PathMatcher::ExactMatch )
	{
		return computeProcessedObject( path, context, inPlug()->objectPlug()->getValue() );
	}
	else
	{
		return inPlug()->objectPlug()->getValue();
	}
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

SceneElementProcessor::BoundMethod SceneElementProcessor::boundMethod( const Gaffer::Context *context ) const
{
	const bool pBound = processesBound();
	const bool pTransform = processesTransform();

	if( pBound || pTransform )
	{
		const IECore::PathMatcher::Result f = filterValue( context );
		if( pBound && (f & IECore::PathMatcher::ExactMatch) )
		{
			return Processed;
		}

		if( f & IECore::PathMatcher::DescendantMatch )
		{
			return Union;
		}
	}

	return PassThrough;
}
