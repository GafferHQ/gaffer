//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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
#include "boost/python/slice.hpp"
#include "boost/python/suite/indexing/container_utils.hpp"

#include "MessagesBinding.h"

#include "Gaffer/Private/IECorePreview/MessagesData.h"

#include "IECorePython/RunTimeTypedBinding.h"
#include "IECorePython/RunTimeTypedBinding.inl"

#include "IECorePython/SimpleTypedDataBinding.h"

#include "boost/functional/hash.hpp"

using namespace boost::python;
using namespace IECorePreview;

namespace
{

Message getItem( Messages &m, long index )
{
	const long size = m.size();

	if( index < 0 )
	{
		index = size + index;
	}

	if( index < 0 || index >= size )
	{
		PyErr_SetString( PyExc_IndexError, "Index out of range" );
		throw_error_already_set();
	}

	return m[ index ];

}

long hashMessage( const Message &m )
{
	IECore::MurmurHash h;
	m.hash( h );
	return boost::hash<IECore::MurmurHash>()( h );
}

object firstDifferenceWrapper( const Messages &m, const Messages &others )
{
	IECorePython::ScopedGILRelease gilRelease;
	auto d = m.firstDifference( others );
	return d ? object( *d ) : object();
}

long hashMessages( const Messages &m )
{
	return boost::hash<IECore::MurmurHash>()( m.hash() );
}

std::string reprMessagesData( const MessagesData *m )
{
	if( m->readable().size() > 0 )
	{
		throw IECore::NotImplementedException( "MessagesData::repr Not implemented for non-empty containers" );
	}

	return std::string( "Gaffer.Private.IECorePreview.MessagesData()" );
}

}

void GafferModule::bindMessages()
{
	object privateModule( borrowed( PyImport_AddModule( "Gaffer.Private" ) ) );
	scope().attr( "Private" ) = privateModule;

	object ieCorePreviewModule( borrowed( PyImport_AddModule( "Gaffer.Private.IECorePreview" ) ) );
	scope().attr( "Private" ).attr( "IECorePreview" ) = ieCorePreviewModule;

	scope previewScope( ieCorePreviewModule );

	class_<Message>( "Message", no_init )
		.def(
			init<IECore::MessageHandler::Level, const std::string &, const std::string &>(
				( arg( "level" ), arg( "context" ), arg( "message" ) )
			)
		)
		.add_property( "level", &Message::level )
		.add_property( "context", &Message::context )
		.add_property( "message", &Message::message )
		.def( "hash", &Message::hash )
		.def( self == self )
		.def( self != self )
		.def( "__hash__", &hashMessage )
	;

	class_<Messages>( "Messages" )
		.def( init<>() )
		.def( init<const Messages &>( ( arg("other") ) ) )
		.def( "size", &Messages::size )
		.def( "count", &Messages::count )
		.def( "clear", &Messages::clear )
		.def( "hash", &Messages::hash )
		.def( "add", &Messages::add )
		.def( "firstDifference", &firstDifferenceWrapper )
		.def( self == self )
		.def( self != self )
		.def( "__len__", &Messages::size )
		.def( "__getitem__", &getItem )
		.def( "__hash__", &hashMessages )
	;

	IECorePython::RunTimeTypedClass<MessagesData>()
		.def( init<>() )
		.def( init<const IECorePreview::Messages &>() )
		.add_property( "value", make_function( &MessagesData::writable, return_internal_reference<1>() ) )
		.def( "hasBase", &MessagesData::hasBase ).staticmethod( "hasBase" )
		.def( "__repr__", &reprMessagesData )
	;

	IECorePython::TypedDataFromType<MessagesData>();
}
