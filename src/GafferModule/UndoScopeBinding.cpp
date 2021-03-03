//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011, John Haddon. All rights reserved.
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "UndoScopeBinding.h"

#include "Gaffer/ScriptNode.h"
#include "Gaffer/UndoScope.h"

#include "IECorePython/ScopedGILRelease.h"

#include <memory>

using namespace boost::python;
using namespace Gaffer;

namespace
{

using UndoScopePtr = std::shared_ptr<UndoScope>;

void deleter( UndoScope *undoScope )
{
	// The destructor for the undo scope may trigger a dirty
	// propagation, and observers of plugDirtiedSignal() may
	// well invoke a compute. We need to release the GIL so that
	// if that compute is multithreaded, those threads can acquire
	// the GIL for python based nodes and expressions.
	IECorePython::ScopedGILRelease gilRelease;
	delete undoScope;
}

UndoScopePtr construct( ScriptNodePtr script, UndoScope::State state, const char *mergeGroup )
{
	return UndoScopePtr( new UndoScope( script, state, mergeGroup ), deleter );
}

} // namespace

void GafferModule::bindUndoScope()
{
	class_<UndoScope, UndoScopePtr, boost::noncopyable> cls( "_UndoScope", no_init );

	// Must bind enum before constructor, because we need to
	// use an enum value for a default value.
	scope s( cls );
	enum_<UndoScope::State>( "State" )
		.value( "Invalid", UndoScope::Invalid )
		.value( "Enabled", UndoScope::Enabled )
		.value( "Disabled", UndoScope::Disabled )
	;

	cls.def(
		"__init__",
		make_constructor(
			construct,
			default_call_policies(),
			(
				boost::python::arg_( "script" ),
				boost::python::arg_( "state" ) = UndoScope::Enabled,
				boost::python::arg_( "mergeGroup" ) = ""
			)
		)
	);
}
