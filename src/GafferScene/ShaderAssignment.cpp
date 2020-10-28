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

GAFFER_NODE_DEFINE_TYPE( ShaderAssignment );

namespace
{

const InternedString g_oslShader( "osl:shader" );
const InternedString g_oslSurface( "osl:surface" );

const char *g_oslPrefix( getenv( "GAFFERSCENE_SHADERASSIGNMENT_OSL_PREFIX" ) );
const InternedString g_oslTarget( g_oslPrefix ? std::string( g_oslPrefix ) + ":surface" : "osl:surface" );

} // namespace

size_t ShaderAssignment::g_firstPlugIndex = 0;

ShaderAssignment::ShaderAssignment( const std::string &name )
	:	AttributeProcessor( name, PathMatcher::EveryMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ShaderPlug( "shader" ) );
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

bool ShaderAssignment::affectsProcessedAttributes( const Gaffer::Plug *input ) const
{
	return AttributeProcessor::affectsProcessedAttributes( input ) || input == shaderPlug();
}

void ShaderAssignment::hashProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	AttributeProcessor::hashProcessedAttributes( path, context, h );
	ScenePlug::GlobalScope globalScope( context );
	h.append( shaderPlug()->attributesHash() );
}

IECore::ConstCompoundObjectPtr ShaderAssignment::computeProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, const IECore::CompoundObject *inputAttributes ) const
{
	ScenePlug::GlobalScope globalScope( context );
	ConstCompoundObjectPtr attributes = shaderPlug()->attributes();

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

		// Another, bigger kludge for OSL surfaces.
		// It can be unintuitive that OSL shaders are unable to override renderer
		// specific shaders.  OSL shaders are always considered less specific,
		// even when declared further down the hierarchy.  Artists using one only
		// renderer are likely to ignore the distinction between renderer
		// specific and OSL shaders.  To address this, the env var
		// GAFFERSCENE_SHADERASSIGNMENT_OSL_PREFIX allows forcing all OSL shaders to be
		// treated as if they are specific to your chosen renderer, so that they
		// override other shaders for that renderer as expected.
		if( name == g_oslSurface )
		{
			name = g_oslTarget;
		}
		result->members()[name] = attribute.second;
	}

	return result;
}
