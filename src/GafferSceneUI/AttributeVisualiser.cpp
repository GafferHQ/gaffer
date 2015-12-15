//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine. All rights reserved.
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

#include "GafferSceneUI/AttributeVisualiser.h"
#include "IECoreGL/Group.h"
#include "IECoreGL/State.h"

using namespace GafferSceneUI;

namespace
{

typedef std::vector<ConstAttributeVisualiserPtr> AttributeVisualisers;

AttributeVisualisers &visualisers()
{
	static AttributeVisualisers v;
	return v;
}

} // namespace

AttributeVisualiser::AttributeVisualiser()
{
}

AttributeVisualiser::~AttributeVisualiser()
{
}


IECoreGL::ConstRenderablePtr AttributeVisualiser::allVisualisations( const IECore::CompoundObject *attributes,
	IECoreGL::ConstStatePtr &state )
{
	const AttributeVisualisers &v = visualisers();

	IECoreGL::GroupPtr resultGroup = NULL;
	IECoreGL::StatePtr resultState = NULL;

	for( unsigned int i = 0; i < v.size(); i++ )
	{
		IECoreGL::ConstStatePtr curState = NULL;
		IECoreGL::ConstRenderablePtr curVis = v[i]->visualise( attributes, curState );

		if( curVis )
		{
			if( !resultGroup )
			{
				resultGroup = new IECoreGL::Group();
			}
			// resultGroup will be returned as const, so const-casting the children in order to add them
			// is safe
			resultGroup->addChild( const_cast<IECoreGL::Renderable*>( curVis.get() ) );
		}

		if( curState )
		{
			if( !resultState )
			{
				resultState = new IECoreGL::State( false );
			}
			resultState->add( const_cast<IECoreGL::State*>( curState.get() ) );
		}
	}

	state = resultState;
	return resultGroup;
}

void AttributeVisualiser::registerVisualiser( ConstAttributeVisualiserPtr visualiser )
{
	visualisers().push_back( visualiser );
}
