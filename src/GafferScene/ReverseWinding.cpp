//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/ReverseWinding.h"

#include "IECoreScene/MeshAlgo.h"
#include "IECoreScene/MeshPrimitive.h"

using namespace IECore;
using namespace IECoreScene;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( ReverseWinding );

ReverseWinding::ReverseWinding( const std::string &name )
	:	ObjectProcessor( name )
{
}

ReverseWinding::~ReverseWinding()
{
}

bool ReverseWinding::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	return ObjectProcessor::affectsProcessedObject( input );
}

void ReverseWinding::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ObjectProcessor::hashProcessedObject( path, context, h );
}

IECore::ConstObjectPtr ReverseWinding::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const
{
	const MeshPrimitive *mesh = runTimeCast<const MeshPrimitive>( inputObject );
	if( !mesh )
	{
		return inputObject;
	}

	MeshPrimitivePtr meshCopy = mesh->copy();
	MeshAlgo::reverseWinding( meshCopy.get() );
	return meshCopy;
}
