//////////////////////////////////////////////////////////////////////////
//
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

#include "GafferSceneTest/TestShader.h"

#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/SplinePlug.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferSceneTest;

GAFFER_NODE_DEFINE_TYPE( TestShader )

TestShader::TestShader( const std::string &name )
	:	Shader( name )
{
	// The base class expects us to serialise a `loadShader()`
	// call to set the values for these, but we just represent
	// a fixed shader. Turn serialisation back on.
	namePlug()->setFlags( Plug::Serialisable, true );
	typePlug()->setFlags( Plug::Serialisable, true );

	addChild( new Color3fPlug( "out", Plug::Out ) );
	parametersPlug()->addChild( new IntPlug( "i" ) );
	parametersPlug()->addChild( new Color3fPlug( "c" ) );
	parametersPlug()->addChild( new SplinefColor3fPlug( "spline" ) );
}

TestShader::~TestShader()
{
}
