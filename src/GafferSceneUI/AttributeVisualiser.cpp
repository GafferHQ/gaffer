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

using namespace GafferSceneUI;

namespace
{

ConstAttributeVisualiserPtr foo;

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


void AttributeVisualiser::visualiseFromRegistry( const IECore::CompoundObject *attributes,
            std::vector< IECoreGL::ConstRenderablePtr> &renderables, IECoreGL::State &state )
{
	const AttributeVisualisers &v = visualisers();
	for( unsigned int i = 0; i < v.size(); i++ )
	{
		v[i]->visualise( attributes, renderables, state );
	}
}

void AttributeVisualiser::registerVisualiser( ConstAttributeVisualiserPtr visualiser )
{
	visualisers().push_back( visualiser );
}
