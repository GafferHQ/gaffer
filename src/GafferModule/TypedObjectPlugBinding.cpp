//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

#include "TypedObjectPlugBinding.h"

#include "GafferBindings/TypedObjectPlugBinding.h"

#include "Gaffer/TypedObjectPlug.h"

// Deliberately avoiding "using namespace" so that we can be sure
// TypedPlugBinding uses full namespace qualification for all names.

void GafferModule::bindTypedObjectPlug()
{
	GafferBindings::TypedObjectPlugClass<Gaffer::ObjectPlug>();
	GafferBindings::TypedObjectPlugClass<Gaffer::BoolVectorDataPlug>();
	GafferBindings::TypedObjectPlugClass<Gaffer::IntVectorDataPlug>();
	GafferBindings::TypedObjectPlugClass<Gaffer::FloatVectorDataPlug>();
	GafferBindings::TypedObjectPlugClass<Gaffer::StringVectorDataPlug>();
	GafferBindings::TypedObjectPlugClass<Gaffer::InternedStringVectorDataPlug>();
	GafferBindings::TypedObjectPlugClass<Gaffer::V2iVectorDataPlug>();
	GafferBindings::TypedObjectPlugClass<Gaffer::V3fVectorDataPlug>();
	GafferBindings::TypedObjectPlugClass<Gaffer::Color3fVectorDataPlug>();
	GafferBindings::TypedObjectPlugClass<Gaffer::M44fVectorDataPlug>();
	GafferBindings::TypedObjectPlugClass<Gaffer::M33fVectorDataPlug>();
	GafferBindings::TypedObjectPlugClass<Gaffer::ObjectVectorPlug>();
	GafferBindings::TypedObjectPlugClass<Gaffer::CompoundObjectPlug>();
	GafferBindings::TypedObjectPlugClass<Gaffer::AtomicCompoundDataPlug>();
	GafferBindings::TypedObjectPlugClass<Gaffer::PathMatcherDataPlug>();
}
