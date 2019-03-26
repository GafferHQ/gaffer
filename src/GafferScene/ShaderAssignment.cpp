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

#include "GafferScene/ShaderAssignment.h"

#include "Gaffer/Metadata.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( ShaderAssignment );

namespace
{

const InternedString g_oslShader( "osl:shader" );
const InternedString g_oslSurface( "osl:surface" );

/// Historically, we evaluated `ShaderAssignment::shaderPlug()` in a context
/// containing "scene:path". This was undesirable for a couple of reasons :
///
/// - If the user used "scene:path" to vary the shader in some way, it
///   could result in a unique ShaderNetwork for every location assigned, which
///   could translate into huge numbers of unique networks in the renderer.
///   This is a very inefficient way of generating shader variation. A better
///   approach is to use a CustomAttributes node to assign random user attributes
///   and to read from those in a single static shader network.
/// - Even if the user didn't use "scene:path", we still needed to compute the
///   hash for the input network in a potentially huge number of contexts. Since
///   shader networks are often large, this could have significant overhead, particularly
///   during interactive render updates. If we can remove "scene:path" from
///   the context before hashing the shader, we make much more efficient use of the
///   hash cache and get better performance.
///
/// Because of this, we want to evaluate the input shader in a GlobalScope.
/// Unfortunately, we have no way of knowing if a shader network is relying on
/// "scene:path", so we must provide some backwards compatibility while folks migrate
/// to the preferred way of working. Setting the GAFFERSCENE_SHADERASSIGNMENT_CONTEXTCOMPATIBILITY
/// environment variable to "1" provides that compatibility, allowing old ShaderAssignments
/// to operate as they did before. To hasten migration, we don't want the environment variable
/// to allow _new_ ShaderAssignments to operate in the old way, so we use the "__contextCompatibility"
/// plug to provide additional control per node. It defaults to on, but we use a userDefault
/// to turn it off for all newly created nodes.
bool initContextCompatibility()
{
	Gaffer::Metadata::registerValue( ShaderAssignment::staticTypeId(), "__contextCompatibility", "userDefault", new BoolData( false ) );
	const char *e = getenv( "GAFFERSCENE_SHADERASSIGNMENT_CONTEXTCOMPATIBILITY" );
	return e && !strcmp( e, "1" );
}

const bool g_contextCompatibilityEnabled = initContextCompatibility();

} // namespace

size_t ShaderAssignment::g_firstPlugIndex = 0;

ShaderAssignment::ShaderAssignment( const std::string &name )
	:	SceneElementProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ShaderPlug( "shader" ) );
	addChild( new BoolPlug( "__contextCompatibility", Plug::In, true, Plug::Default & ~Plug::AcceptsInputs ) );

	// Fast pass-throughs for the things we don't alter.
	outPlug()->objectPlug()->setInput( inPlug()->objectPlug() );
	outPlug()->transformPlug()->setInput( inPlug()->transformPlug() );
	outPlug()->boundPlug()->setInput( inPlug()->boundPlug() );
}

ShaderAssignment::~ShaderAssignment()
{
}

GafferScene::ShaderPlug *ShaderAssignment::shaderPlug()
{
	return getChild<ShaderPlug>( g_firstPlugIndex );
}

const GafferScene::ShaderPlug *ShaderAssignment::shaderPlug() const
{
	return getChild<ShaderPlug>( g_firstPlugIndex );
}

Gaffer::BoolPlug *ShaderAssignment::contextCompatibilityPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::BoolPlug *ShaderAssignment::contextCompatibilityPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

void ShaderAssignment::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneElementProcessor::affects( input, outputs );

	if( input == shaderPlug() || input == contextCompatibilityPlug() )
	{
		outputs.push_back( outPlug()->attributesPlug() );
	}
}

bool ShaderAssignment::processesAttributes() const
{
	return true;
}

void ShaderAssignment::hashProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( g_contextCompatibilityEnabled && contextCompatibilityPlug()->getValue() )
	{
		h.append( shaderPlug()->attributesHash() );
	}
	else
	{
		ScenePlug::GlobalScope globalScope( context );
		h.append( shaderPlug()->attributesHash() );
	}
}

IECore::ConstCompoundObjectPtr ShaderAssignment::computeProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::ConstCompoundObjectPtr inputAttributes ) const
{
	ConstCompoundObjectPtr attributes;
	if( g_contextCompatibilityEnabled && contextCompatibilityPlug()->getValue() )
	{
		attributes = shaderPlug()->attributes();
	}
	else
	{
		ScenePlug::GlobalScope globalScope( context );
		attributes = shaderPlug()->attributes();
	}

	if( attributes->members().empty() )
	{
		return inputAttributes;
	}

	CompoundObjectPtr result = new CompoundObject;
	// Since we're not going to modify any existing members (only add new ones),
	// and our result becomes const on returning it, we can directly reference
	// the input members in our result without copying. Be careful not to modify
	// them though!
	result->members() = inputAttributes->members();
	for( const auto &attribute : attributes->members() )
	{
		InternedString name = attribute.first;
		if( name == g_oslShader )
		{
			// We are given an "osl:shader" attribute when assigning a generic
			// OSL shader rather than an OSL surface shader. In the absence
			// of other information we assume that the user's intention is to
			// assign it as a surface shader.
			///
			/// \todo Consider ways of making the purpose of the assignment
			/// more explicit. Perhaps shaders need to be plugged into various
			/// inputs of a Material node that groups surface/displacement etc?
			/// This also seems a good time to consider that the mixing of
			/// Arnold and OSL shader assignments has caused confusion
			/// in some environments, because "ai:surface" is considered to take
			/// priority over "osl:surface", even if the OSL assignment is lower
			/// in the hierarchy.
			///
			/// Also bear in mind that OSL has deprecated shader types
			/// entirely - more info at the following links :
			///
			/// - https://groups.google.com/d/msg/osl-dev/bVBZda-UsbI/EvByoI6sBQAJ
			/// - https://github.com/imageworks/OpenShadingLanguage/pull/899
			name = g_oslSurface;
		}
		result->members()[name] = attribute.second;
	}

	return result;
}
