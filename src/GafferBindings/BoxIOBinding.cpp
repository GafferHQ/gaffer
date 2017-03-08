//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/BoxIn.h"
#include "Gaffer/BoxOut.h"
#include "Gaffer/Plug.h"

#include "GafferBindings/DependencyNodeBinding.h"
#include "GafferBindings/BoxIOBinding.h"

using namespace boost::python;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;

namespace
{

class BoxIOSerialiser : public NodeSerialiser
{

	virtual std::string postScript( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, const Serialisation &serialisation ) const
	{
		std::string result = NodeSerialiser::postScript( graphComponent, identifier, serialisation );

		const BoxIO *boxIO = static_cast<const BoxIO *>( graphComponent );
		if( !boxIO->plug<Plug>() )
		{
			// BoxIO::setup() hasn't been called yet.
			return result;
		}

		const Plug *promoted = boxIO->promotedPlug<Plug>();
		if( promoted && serialisation.identifier( promoted ) != "" )
		{
			return result;
		}

		// The BoxIO node has been set up, but its promoted plug isn't
		// being serialised (for instance, because someone is copying a
		// selection from inside a box). Add a setup() call to the
		// serialisation so that the promoted plug will be created upon
		// pasting into another box.

		if( !result.empty() )
		{
			result += "\n";
		}
		result += identifier + ".setup()\n";

		return result;
	}

};

PlugPtr plug( BoxIO &b )
{
	return b.plug<Plug>();
}

PlugPtr promotedPlug( BoxIO &b )
{
	return b.promotedPlug<Plug>();
}

} // namespace

void GafferBindings::bindBoxIO()
{

	NodeClass<BoxIO>( NULL, no_init )
		.def( "setup", &BoxIO::setup, ( arg( "plug" ) = object() ) )
		.def( "plug", &plug )
		.def( "promotedPlug", &promotedPlug )
	;

	Serialisation::registerSerialiser( BoxIO::staticTypeId(), new BoxIOSerialiser );

	NodeClass<BoxIn>();
	NodeClass<BoxOut>();

}
