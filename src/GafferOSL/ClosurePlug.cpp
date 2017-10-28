//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include "IECore/MurmurHash.h"

#include "Gaffer/SubGraph.h"
#include "Gaffer/Dot.h"

#include "GafferOSL/ClosurePlug.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferOSL;

//////////////////////////////////////////////////////////////////////////
// ClosurePlug
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( ClosurePlug );

ClosurePlug::ClosurePlug( const std::string &name, Direction direction, unsigned flags )
	:	Plug( name, direction, flags )
{
}

ClosurePlug::~ClosurePlug()
{
}

bool ClosurePlug::acceptsChild( const GraphComponent *potentialChild ) const
{
	return false;
}

Gaffer::PlugPtr ClosurePlug::createCounterpart( const std::string &name, Direction direction ) const
{
	return new ClosurePlug( name, direction, getFlags() );
}

bool ClosurePlug::acceptsInput( const Gaffer::Plug *input ) const
{
	if( !Plug::acceptsInput( input ) )
	{
		return false;
	}

	if( !input )
	{
		return true;
	}

	// We only accept connections from other ClosurePlugs
	if( runTimeCast<const ClosurePlug>( input ) )
	{
		return true;
	}

	return false;
}
