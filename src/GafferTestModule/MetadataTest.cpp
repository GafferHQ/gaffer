//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

#include "MetadataTest.h"

#include "GafferTest/Assert.h"

#include "Gaffer/Metadata.h"
#include "Gaffer/Node.h"
#include "Gaffer/Plug.h"

#include "IECore/SimpleTypedData.h"

#include "tbb/parallel_for.h"

using namespace tbb;
using namespace IECore;
using namespace Gaffer;

void GafferTestModule::testConcurrentAccessToDifferentInstances()
{
	// This test simulates many different scripts being loaded concurrently in
	// separate threads, with each script registering per-instance metadata for
	// its members. This is similar to what happens on a smaller scale when the
	// UI loads a script on a background thread to provide cancellable loading.
	//
	// As a side-effect, we are also testing a historical issue with the
	// signalling of metadata changes. Our Signal class is not intended to be
	// thread-safe (and neither was its `boost::signals` predecessor). This is
	// OK for the newer `Metadata::NodeValueChangedSignal` where each node
	// instance has its own signal - signalling will occur on the loading
	// thread, and other threads have not had a chance to connect yet. But
	// `Metadata::LegacyNodeValueChangedSignal` is another matter; it is global,
	// emitted for all nodes, and connected to many UI components. This leads to
	// multiple threads emitting the _same_ non-empty signal concurrently, which
	// is not something we intend to support.
	//
	// Here we use `legacyConnection` to assert that such concurrent signalling
	// is currently reliable (see details in SlotBase). Note that there is no
	// such guarantee for connection/disconnection on one thread while the
	// signal is being emitted on another - we are relying on this being
	// a vanishingly rare event.
	//
	/// \todo Rid ourselves of `Metadata::LegacyNodeValueChangedSignal`.

	std::atomic_size_t callCount = 0;
	Signals::ScopedConnection legacyConnection = Metadata::nodeValueChangedSignal().connect(
		[&callCount]( IECore::TypeId nodeTypeId, IECore::InternedString key, Gaffer::Node *node ) {
			GAFFERTEST_ASSERT( node );
			callCount++;
		}
	);

	const size_t iterations = 100000;
	parallel_for(
		blocked_range<size_t>( 0, iterations ),
		[]( const blocked_range<size_t> &r ) {
			for( size_t i=r.begin(); i!=r.end(); ++i )
			{
				NodePtr n = new Node();
				PlugPtr p = new Plug();

				GAFFERTEST_ASSERT( Metadata::value( n.get(), "threadingTest" ) == nullptr );
				GAFFERTEST_ASSERT( Metadata::value( p.get(), "threadingTest" ) == nullptr );

				Metadata::registerValue( n.get(), "threadingTest", new IECore::IntData( 1 ) );
				Metadata::registerValue( p.get(), "threadingTest", new IECore::IntData( 2 ) );

				GAFFERTEST_ASSERT( Metadata::value<IntData>( n.get(), "threadingTest" )->readable() == 1 );
				GAFFERTEST_ASSERT( Metadata::value<IntData>( p.get(), "threadingTest" )->readable() == 2 );
			}
		}
	);

	GAFFERTEST_ASSERTEQUAL( callCount.load(), iterations );
}
