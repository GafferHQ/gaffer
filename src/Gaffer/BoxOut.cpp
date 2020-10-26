//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/BoxOut.h"

#include "Gaffer/BoxIn.h"
#include "Gaffer/Dot.h"

using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

const Dot *dotChainSource( const Plug *plug )
{
	const Dot *result = nullptr;
	while( plug )
	{
		if( const Dot *dot = IECore::runTimeCast<const Dot>( plug->node() ) )
		{
			result = dot;
		}
		else
		{
			break;
		}
		plug = plug->getInput();
	}
	return result;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// BoxOut
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( BoxOut )

BoxOut::BoxOut( const std::string &name )
	:	BoxIO( Plug::Out, name )
{
}

BoxOut::~BoxOut()
{
}

bool BoxOut::acceptsInput( const Plug *plug, const Plug *inputPlug ) const
{
	if( !Node::acceptsInput( plug, inputPlug ) )
	{
		return false;
	}

	if( plug != passThroughPlugInternal() )
	{
		return true;
	}

	// The only input we _really_ want to get into
	// our passThrough plug is from a BoxIn with the
	// same parent as us.

	const BoxIn *boxIn = inputPlug->parent<BoxIn>();
	if(
		boxIn &&
		boxIn->parent() == parent() &&
		inputPlug == boxIn->plug()
	)
	{
		return true;
	}

	// But `acceptsInput()` is also called when connections
	// are being made to the BoxIn's promoted plug (on the
	// outside of the Box), so we just have to suck it up
	// and accept that too.

	const Node *inputNode = inputPlug->node();
	if( sourceBoxIn( passThroughPlug() ) && ( !inputNode || inputNode->parent() != parent() ) )
	{
		return true;
	}

	// And we also want to accept Dots, provided they're
	// either not connected to anything, or just to other
	// dots.

	if( const Dot *dot = dotChainSource( inputPlug ) )
	{
		if( !dot->inPlug()->getInput() || sourceBoxIn( dot->inPlug() ) )
		{
			return true;
		}
	}

	return false;
}

const BoxIn *BoxOut::sourceBoxIn( const Plug *plug ) const
{
	while( plug )
	{
		if( const BoxIn *boxIn = IECore::runTimeCast<const BoxIn>( plug->node() ) )
		{
			if( plug == boxIn->plug() && boxIn->parent() == parent() )
			{
				return boxIn;
			}
		}
		plug = plug->getInput();
	}
	return nullptr;
}
