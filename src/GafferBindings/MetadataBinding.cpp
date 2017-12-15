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

#include "boost/python.hpp"
#include "boost/python/raw_function.hpp"
#include "boost/format.hpp"

#include "IECore/SimpleTypedData.h"
#include "IECorePython/ScopedGILLock.h"

#include "Gaffer/Plug.h"
#include "Gaffer/Node.h"
#include "Gaffer/Metadata.h"

#include "GafferBindings/MetadataBinding.h"
#include "GafferBindings/DataBinding.h"
#include "GafferBindings/Serialisation.h"

using namespace boost::python;
using namespace IECore;
using namespace Gaffer;
using namespace GafferBindings;

namespace GafferBindings
{

void metadataModuleDependencies( const Gaffer::Node *node, std::set<std::string> &modules )
{
	/// \todo Derive from the registered values so we can support
	/// datatypes from other modules.
	modules.insert( "imath" );
	modules.insert( "IECore" );
	modules.insert( "Gaffer" );
}

void metadataModuleDependencies( const Gaffer::Plug *plug, std::set<std::string> &modules )
{
	/// \todo Derive from the registered values so we can support
	/// datatypes from other modules.
	modules.insert( "imath" );
	modules.insert( "IECore" );
	modules.insert( "Gaffer" );
}

std::string metadataSerialisation( const Gaffer::Node *node, const std::string &identifier )
{
	std::vector<InternedString> keys;
	Metadata::registeredValues( node, keys, /* instanceOnly = */ true, /* persistentOnly = */ true );

	std::string result;
	for( std::vector<InternedString>::const_iterator it = keys.begin(), eIt = keys.end(); it != eIt; ++it )
	{
		object pythonKey( it->c_str() );
		std::string key = extract<std::string>( pythonKey.attr( "__repr__" )() );

		ConstDataPtr value = Metadata::value( node, *it );
		object pythonValue = dataToPython( value.get(), /* copy = */ false );

		object repr = boost::python::import( "IECore" ).attr( "repr" );
		std::string stringValue = extract<std::string>( repr( pythonValue ) );

		result += boost::str(
			boost::format( "Gaffer.Metadata.registerNodeValue( %s, %s, %s )\n" ) %
				identifier %
				key %
				stringValue
		);
	}

	return result;
}

std::string metadataSerialisation( const Plug *plug, const std::string &identifier )
{
	std::vector<InternedString> keys;
	Metadata::registeredValues( plug, keys, /* instanceOnly = */ true, /* persistentOnly = */ true );

	std::string result;
	for( std::vector<InternedString>::const_iterator it = keys.begin(), eIt = keys.end(); it != eIt; ++it )
	{
		object pythonKey( it->c_str() );
		std::string key = extract<std::string>( pythonKey.attr( "__repr__" )() );

		ConstDataPtr value = Metadata::value( plug, *it );
		object pythonValue = dataToPython( value.get(), /* copy = */ false );
		std::string stringValue = extract<std::string>( pythonValue.attr( "__repr__" )() );
		const std::string modulePath = Serialisation::modulePath( pythonValue );
		if( modulePath == "imath" )
		{
			stringValue = modulePath + "." + stringValue;
		}

		result += boost::str(
			boost::format( "Gaffer.Metadata.registerPlugValue( %s, %s, %s )\n" ) %
				identifier %
				key %
				stringValue
		);
	}

	return result;
}

} // namespace GafferBindings
