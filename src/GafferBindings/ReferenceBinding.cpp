//////////////////////////////////////////////////////////////////////////
//
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

#include "boost/python.hpp" // must be the first include

#include "Gaffer/Reference.h"
#include "Gaffer/StringPlug.h"

#include "GafferBindings/ReferenceBinding.h"
#include "GafferBindings/NodeBinding.h"
#include "GafferBindings/ExceptionAlgo.h"
#include "GafferBindings/SignalBinding.h"

using namespace boost::python;
using namespace Gaffer;
using namespace GafferBindings;

namespace
{

struct ReferenceLoadedSlotCaller
{
	boost::signals::detail::unusable operator()( boost::python::object slot, ReferencePtr r )
	{
		try
		{
			slot( r );
		}
		catch( const error_already_set &e )
		{
			translatePythonException();
		}
		return boost::signals::detail::unusable();
	}
};

class ReferenceSerialiser : public NodeSerialiser
{

	virtual std::string postConstructor( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, const Serialisation &serialisation ) const
	{
		const Reference *r = static_cast<const Reference *>( graphComponent );

		const std::string &fileName = r->fileName();
		if( fileName.empty() )
		{
			return "";
		};

		return identifier + ".load( \"" + fileName + "\" )\n";
	}

};

} // namespace

void GafferBindings::bindReference()
{
	NodeClass<Reference>()
		.def( "load", &Reference::load )
		.def( "fileName", &Reference::fileName, return_value_policy<copy_const_reference>() )
		.def( "referenceLoadedSignal", &Reference::referenceLoadedSignal, return_internal_reference<1>() )
	;

	SignalClass<Reference::ReferenceLoadedSignal, DefaultSignalCaller<Reference::ReferenceLoadedSignal>, ReferenceLoadedSlotCaller >( "ReferenceLoadedSignal" );

	Serialisation::registerSerialiser( Reference::staticTypeId(), new ReferenceSerialiser );

}
