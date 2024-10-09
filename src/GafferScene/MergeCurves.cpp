//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2024, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/MergeCurves.h"

#include "tbb/task_arena.h"

#include "GafferScene/Private/IECoreScenePreview/PrimitiveAlgo.h"
#include "IECoreScene/CurvesPrimitive.h"
#include "IECore/NullObject.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( MergeCurves );

size_t MergeCurves::g_firstPlugIndex = 0;

MergeCurves::MergeCurves( const std::string &name )
	:	MergeObjects( name, "/mergedCurves" )
{
	storeIndexOfNextChild( g_firstPlugIndex );
}

MergeCurves::~MergeCurves()
{
}

IECore::ConstObjectPtr MergeCurves::computeMergedObject( const std::vector< std::pair< IECore::ConstObjectPtr, Imath::M44f > > &sources, const Gaffer::Context *context ) const
{
	std::vector< std::pair< const IECoreScene::Primitive *, Imath::M44f > > curves;

	for( const auto &[object, transform] : sources )
	{
		const IECoreScene::CurvesPrimitive * m = IECore::runTimeCast< const IECoreScene::CurvesPrimitive >( object.get() );
		if( !m )
		{
			// Just skip anything that's not a curve
			continue;
		}

		curves.push_back( std::make_pair( m, transform ) );
	}

	if( !curves.size() )
	{
		return IECore::NullObject::defaultNullObject();
	}

	return IECoreScenePreview::PrimitiveAlgo::mergePrimitives( curves, context->canceller() );
}
