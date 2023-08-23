//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

#include "boost/python.hpp"

#include "ValuePlugTest.h"

#include "Gaffer/Context.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/TypedObjectPlug.h"
#include "Gaffer/ValuePlug.h"

#include "tbb/parallel_for.h"

#include "IECorePython/ScopedGILRelease.h"


using namespace boost::python;
using namespace Gaffer;

namespace
{

template<typename T>
void repeatGetValue( const T *plug, int iterations )
{
	IECorePython::ScopedGILRelease gilRelease;
	for( int i = 0; i < iterations; i++ )
	{
		plug->getValue();
	}
}

template<typename T>
void repeatGetValueWithVar( const T *plug, int iterations, const IECore::InternedString iterationVar )
{
	IECorePython::ScopedGILRelease gilRelease;
	Context::EditableScope scope( Context::current() );
	for( int i = 0; i < iterations; i++ )
	{
		scope.set( iterationVar, &i );
		plug->getValue();
	}
}

// Call getValue() on the given plug many times in parallel.
//
// Evaluating the same value over and over again is obviously not useful,
// but it can help turn up performance issues that can happen when a
// downstream graph ends up repeatedly evaluating something which turn out
// not to vary.
template<typename T>
void parallelGetValue( const T *plug, int iterations )
{
	IECorePython::ScopedGILRelease gilRelease;
	const ThreadState &threadState = ThreadState::current();
	tbb::parallel_for(
		tbb::blocked_range<int>( 0, iterations ),
		[&]( const tbb::blocked_range<int> &r ) {
			ThreadState::Scope scope( threadState );
			for( int i = r.begin(); i < r.end(); ++i )
			{
				plug->getValue();
			}
		}
	);
}

// Variant of the above which stores the iteration in a context variable, allowing
// the parallel evaluates to vary
template<typename T>
void parallelGetValueWithVar( const T *plug, int iterations, const IECore::InternedString iterationVar )
{
	IECorePython::ScopedGILRelease gilRelease;
	const ThreadState &threadState = ThreadState::current();
	tbb::parallel_for(
		tbb::blocked_range<int>( 0, iterations ),
		[&plug, &iterationVar, &threadState]( const tbb::blocked_range<int> &r ) {
			Context::EditableScope scope( threadState );
			for( int i = r.begin(); i < r.end(); ++i )
			{
				scope.set( iterationVar, &i );
				plug->getValue();
			}
		}
	);
}

} // namespace

void GafferTestModule::bindValuePlugTest()
{
	def( "repeatGetValue", &repeatGetValue<IntPlug> );
	def( "repeatGetValue", &repeatGetValue<FloatPlug> );
	def( "repeatGetValue", &repeatGetValue<ObjectPlug> );
	def( "repeatGetValue", &repeatGetValue<PathMatcherDataPlug> );
	def( "repeatGetValue", &repeatGetValueWithVar<IntPlug> );
	def( "repeatGetValue", &repeatGetValueWithVar<FloatPlug> );
	def( "repeatGetValue", &repeatGetValueWithVar<ObjectPlug> );
	def( "repeatGetValue", &repeatGetValueWithVar<PathMatcherDataPlug> );
	def( "parallelGetValue", &parallelGetValue<IntPlug> );
	def( "parallelGetValue", &parallelGetValue<FloatPlug> );
	def( "parallelGetValue", &parallelGetValue<ObjectPlug> );
	def( "parallelGetValue", &parallelGetValue<PathMatcherDataPlug> );
	def( "parallelGetValue", &parallelGetValueWithVar<IntPlug> );
	def( "parallelGetValue", &parallelGetValueWithVar<FloatPlug> );
	def( "parallelGetValue", &parallelGetValueWithVar<ObjectPlug> );
	def( "parallelGetValue", &parallelGetValueWithVar<PathMatcherDataPlug> );
}
