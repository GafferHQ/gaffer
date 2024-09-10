//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

#include "boost/python.hpp"

#include "VisibleSetBinding.h"

#include "GafferScene/VisibleSet.h"
#include "GafferScene/VisibleSetData.h"

#include "IECorePython/RunTimeTypedBinding.h"
#include "IECorePython/SimpleTypedDataBinding.h"

#include "fmt/format.h"

using namespace boost::python;
using namespace IECore;
using namespace GafferScene;

namespace
{

VisibleSet *constructor( const PathMatcher &expansions, const PathMatcher &inclusions, const PathMatcher &exclusions )
{
	VisibleSet *result = new VisibleSet;
	result->expansions = expansions;
	result->inclusions = inclusions;
	result->exclusions = exclusions;
	return result;
}

std::string visibilityRepr( const VisibleSet::Visibility &visibility )
{
	const std::string drawMode = extract<std::string>( object( visibility.drawMode ).attr( "__str__" )() );
	return fmt::format(
		"GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.{}, {} )",
		drawMode, visibility.descendantsVisible ? "True" : "False"
	);
}

} // namespace

void GafferSceneModule::bindVisibleSet()
{

	IECorePython::RunTimeTypedClass<VisibleSetData>()
		.def( init<>() )
		.def( init<const VisibleSet &>() )
		.add_property( "value", make_function( &VisibleSetData::writable, return_internal_reference<1>() ) )
		.def( "hasBase", &VisibleSetData::hasBase ).staticmethod( "hasBase" )
	;

	IECorePython::TypedDataFromType<VisibleSetData>();

	scope s = class_<VisibleSet>( "VisibleSet" )
		.def( "__init__", make_constructor( constructor, default_call_policies(),
				(
					arg( "expansions" ) = PathMatcher(),
					arg( "inclusions" ) = PathMatcher(),
					arg( "exclusions" ) = PathMatcher()
				)
			)
		)
		.def( init<const VisibleSet &>() )
		.def( "visibility", (VisibleSet::Visibility (VisibleSet ::*)( const std::vector<InternedString> &, const size_t ) const)&VisibleSet::visibility, arg( "minimumExpansionDepth" ) = 0 )
		.def_readwrite( "expansions", &VisibleSet::expansions )
		.def_readwrite( "inclusions", &VisibleSet::inclusions )
		.def_readwrite( "exclusions", &VisibleSet::exclusions )
		.def( "__eq__", &VisibleSet::operator== )
	;

	scope r = class_<VisibleSet::Visibility>( "Visibility" )
		.def( init<>() )
		.def( init<VisibleSet::Visibility::DrawMode, bool>() )
		.def_readwrite( "descendantsVisible", &VisibleSet::Visibility::descendantsVisible )
		.def_readwrite( "drawMode", &VisibleSet::Visibility::drawMode )
		.def( self == self )
		.def( "__repr__", &visibilityRepr )
	;

	enum_<VisibleSet::Visibility::DrawMode>( "DrawMode" )
		.value( "None_", VisibleSet::Visibility::DrawMode::None )
		.value( "Visible", VisibleSet::Visibility::DrawMode::Visible )
		.value( "ExcludedBounds", VisibleSet::Visibility::DrawMode::ExcludedBounds )
	;

}
