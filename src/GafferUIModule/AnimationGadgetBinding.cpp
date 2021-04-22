//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017 Matti Gruener. All rights reserved.
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

#include "AnimationGadgetBinding.h"

#include "GafferUIBindings/GadgetBinding.h"

#include "GafferUI/AnimationGadget.h"

#include "GafferBindings/SignalBinding.h"

#include "Gaffer/Context.h"
#include "Gaffer/Node.h"
#include "Gaffer/Plug.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StandardSet.h"

#include "boost/python/suite/indexing/container_utils.hpp"

using namespace boost::python;
using namespace IECorePython;
using namespace GafferUI;
using namespace GafferUIBindings;
using namespace GafferBindings;

namespace
{

Gaffer::StandardSetPtr visiblePlugs( AnimationGadget &a )
{
	return a.visiblePlugs();
}

Gaffer::StandardSetPtr editablePlugs( AnimationGadget &a )
{
	return a.editablePlugs();
}

} // namespace

void GafferUIModule::bindAnimationGadget()
{

	scope s = GadgetClass<AnimationGadget>()
		.def( init<>() )
		.def( "visiblePlugs", &visiblePlugs )
		.def( "editablePlugs", &editablePlugs )
		.def( "setContext", &AnimationGadget::setContext )
		;

}
