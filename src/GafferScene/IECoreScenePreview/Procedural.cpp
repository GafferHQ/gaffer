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

#include "GafferScene/Private/IECoreScenePreview/Procedural.h"

#include "IECore/MessageHandler.h"

using namespace IECore;
using namespace IECoreScene;
using namespace IECoreScenePreview;

IE_CORE_DEFINEOBJECTTYPEDESCRIPTION( Procedural );

Procedural::Procedural()
{
}

Procedural::~Procedural()
{
}

bool Procedural::isEqualTo( const IECore::Object *other ) const
{
	return VisibleRenderable::isEqualTo( other );
}

void Procedural::hash( IECore::MurmurHash &h ) const
{
	VisibleRenderable::hash( h );
}

void Procedural::copyFrom( const IECore::Object *other, IECore::Object::CopyContext *context )
{
	VisibleRenderable::copyFrom( other, context );
}

void Procedural::save( IECore::Object::SaveContext *context ) const
{
	VisibleRenderable::save( context );
}

void Procedural::load( IECore::Object::LoadContextPtr context )
{
	VisibleRenderable::load( context );
}

void Procedural::memoryUsage( IECore::Object::MemoryAccumulator &accumulator ) const
{
	VisibleRenderable::memoryUsage( accumulator );
}
