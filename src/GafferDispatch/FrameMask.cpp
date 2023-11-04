//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023 John Haddon. All rights reserved.
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

#include "GafferDispatch/FrameMask.h"

#include "Gaffer/Private/IECorePreview/LRUCache.h"

#include "IECore/FrameList.h"

#include <unordered_set>

using namespace IECore;
using namespace Gaffer;
using namespace GafferDispatch;

namespace
{

// We cache the results of `FrameList.asList()` as a set, to avoid regenerating
// it on every frame, and to avoid linear search in `FrameMask::preTasks()`. This
// gives substantial performance improvements when dispatching large frame
// ranges.

using FrameSet = std::unordered_set<IECore::FrameList::Frame>;
using ConstFrameSetPtr = std::shared_ptr<const FrameSet>;

IECorePreview::LRUCache<std::string, ConstFrameSetPtr> g_frameListCache(

	[] ( const std::string &frameExpression, size_t &cost, const IECore::Canceller *canceller )
	{
		std::vector<FrameList::Frame> frames;
		FrameList::parse( frameExpression )->asList( frames );
		cost = frames.size();
		return std::make_shared<FrameSet>( frames.begin(), frames.end() );
	},

	// Enough for approximately an hour's worth of frames, at a cost of < 10Mb.
	100000

);

} // namespace

GAFFER_NODE_DEFINE_TYPE( FrameMask )

size_t FrameMask::g_firstPlugIndex;

FrameMask::FrameMask( const std::string &name )
	:	TaskNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "mask" ) );
}

FrameMask::~FrameMask()
{
}

Gaffer::StringPlug *FrameMask::maskPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *FrameMask::maskPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

void FrameMask::preTasks( const Gaffer::Context *context, Tasks &tasks ) const
{
	ConstFrameSetPtr frames = g_frameListCache.get( maskPlug()->getValue() );
	if( frames->empty() || frames->find( context->getFrame() ) != frames->end() )
	{
		TaskNode::preTasks( context, tasks );
	}
}

IECore::MurmurHash FrameMask::hash( const Context *context ) const
{
	return MurmurHash();
}

void FrameMask::execute() const
{
}
