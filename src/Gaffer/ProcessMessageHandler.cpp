//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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
//      * Neither the name of Image Engine Design Inc nor the names of
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

#include "Gaffer/ProcessMessageHandler.h"

#include "Gaffer/Context.h"
#include "Gaffer/Plug.h"
#include "Gaffer/Process.h"

#include "IECore/FilteredMessageHandler.h"
#include "IECore/VectorTypedData.h"

#include "boost/algorithm/string/join.hpp"
#include "boost/range/adaptor/transformed.hpp"

#include <sstream>

using namespace Gaffer;
using namespace std;

using boost::adaptors::transformed;
using boost::algorithm::join;

namespace
{

IECore::InternedString g_frame( "frame" );
IECore::InternedString g_scenePath( "scene:path" );

} // namespace

ProcessMessageHandler::ProcessMessageHandler( IECore::MessageHandlerPtr handler ) : IECore::FilteredMessageHandler( handler )
{
}

ProcessMessageHandler::~ProcessMessageHandler()
{
}

void ProcessMessageHandler::handle( Level level, const string &context, const string &message )
{
	m_handler->handle( level, context, message );

	if( const Process *p = Process::current() )
	{
		stringstream ss;

		ss << "[ plug: '" << p->plug()->fullName() << "'";

		if( const float *frame = p->context()->getPointer<float>( g_frame ) )
		{
			ss << ", frame: " << *frame;
		}

		if( auto path = p->context()->getPointer< std::vector<IECore::InternedString> >( g_scenePath ) )
		{
			std::string strPath = std::string("/") + join(
				*path | transformed(
					[]( const IECore::InternedString &s )
					{
						return s.string();
					}
				), "/"
			);
			ss << ", path: '" << strPath << "'";
		}

		ss << " ]";

		m_handler->handle( Level::Debug, "Gaffer::Process", ss.str() );
	}
}
