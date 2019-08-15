//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "GafferUI/CompoundNodule.h"

#include "GafferUI/NoduleLayout.h"

#include "Gaffer/Plug.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( CompoundNodule );

Nodule::NoduleTypeDescription<CompoundNodule> CompoundNodule::g_noduleTypeDescription;

CompoundNodule::CompoundNodule( Gaffer::PlugPtr plug )
	:	Nodule( plug )
{
	addChild( new NoduleLayout( plug ) );
}

CompoundNodule::~CompoundNodule()
{
}

bool CompoundNodule::acceptsChild( const Gaffer::GraphComponent *potentialChild ) const
{
	return children().size()==0;
}

Nodule *CompoundNodule::nodule( const Gaffer::Plug *plug )
{
	return noduleLayout()->nodule( plug );
}

const Nodule *CompoundNodule::nodule( const Gaffer::Plug *plug ) const
{
	return noduleLayout()->nodule( plug );
}

NoduleLayout *CompoundNodule::noduleLayout()
{
	return getChild<NoduleLayout>( 0 );
}

const NoduleLayout *CompoundNodule::noduleLayout() const
{
	return getChild<NoduleLayout>( 0 );
}

bool CompoundNodule::canCreateConnection( const Gaffer::Plug *endpoint ) const
{
	return false;
}

void CompoundNodule::createConnection( Gaffer::Plug *endpoint )
{
}
