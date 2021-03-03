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

#include "GafferScene/Private/IECoreGLPreview/AttributeVisualiser.h"

#include "IECoreGL/Group.h"
#include "IECoreGL/State.h"

using namespace IECoreGLPreview;

namespace
{

using AttributeVisualisers = std::vector<ConstAttributeVisualiserPtr>;

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

Visualisations AttributeVisualiser::allVisualisations( const IECore::CompoundObject *attributes, IECoreGL::ConstStatePtr &state ) {
	const AttributeVisualisers &v = visualisers();

	Visualisations resultVis;
	IECoreGL::StatePtr resultState = nullptr;

	for( unsigned int i = 0; i < v.size(); i++ )
	{
		IECoreGL::ConstStatePtr curState = nullptr;
		const Visualisations curVis = v[i]->visualise( attributes, curState );

		if( !curVis.empty() )
		{
			resultVis.insert( resultVis.end(), curVis.begin(), curVis.end() );
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
	return resultVis;
}

void AttributeVisualiser::registerVisualiser( ConstAttributeVisualiserPtr visualiser )
{
	visualisers().push_back( visualiser );
}
