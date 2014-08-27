//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

#include "IECoreGL/Font.h"

#include "IECorePython/RunTimeTypedBinding.h"

#include "GafferUI/StandardStyle.h"

#include "GafferUIBindings/StandardStyleBinding.h"

using namespace boost::python;
using namespace GafferUIBindings;
using namespace GafferUI;

static IECoreGL::FontPtr getFont( StandardStyle &s, Style::TextType textType )
{
	return const_cast<IECoreGL::Font *>( s.getFont( textType ) );
}

void GafferUIBindings::bindStandardStyle()
{
	scope s = IECorePython::RunTimeTypedClass<StandardStyle>()
		.def( init<>() )
		.def( "setColor", &StandardStyle::setColor )
		.def( "getColor", &StandardStyle::getColor, return_value_policy<copy_const_reference>() )
		.def( "setFont", &StandardStyle::setFont )
		.def( "getFont", &getFont )
	;

	enum_<StandardStyle::Color>( "Color" )
		.value( "BackgroundColor", StandardStyle::BackgroundColor )
		.value( "SunkenColor", StandardStyle::SunkenColor )
		.value( "RaisedColor", StandardStyle::RaisedColor )
		.value( "ForegroundColor", StandardStyle::ForegroundColor )
		.value( "HighlightColor", StandardStyle::HighlightColor )
		.value( "ConnectionColor", StandardStyle::ConnectionColor )
		.value( "LastColor", StandardStyle::LastColor )
	;
}
