//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#ifdef GAFFER_VTUNE

#include "Gaffer/VTuneMonitor.h"

#include "Gaffer/Node.h"
#include "Gaffer/Plug.h"
#include "Gaffer/Process.h"

#include "ittnotify.h"

#include <stdio.h>

namespace
{
	const IECore::InternedString hashProcessType( "computeNode:hash" );
	__itt_domain* g_domain = NULL;
}

using namespace Gaffer;

VTuneMonitor::VTuneMonitor(bool monitorHashProcess /* = false */ )
: m_monitorHashProcess( monitorHashProcess )
{
	if (!g_domain)
	{
		g_domain = __itt_domain_create( "org.gafferhq.gaffer" );
	}
}

VTuneMonitor::~VTuneMonitor()
{
}

void VTuneMonitor::processStarted( const Process *process )
{
	if (!m_monitorHashProcess && process->type() != hashProcessType)
	{
		return;
	}

	const Node* node = process->plug()->node();

	const char* typeName = node->typeName();
	__itt_string_handle* handle = __itt_string_handle_create( typeName );
	__itt_task_begin(g_domain, __itt_null, __itt_null, handle );
}

void VTuneMonitor::processFinished( const Process *process )
{
	if (!m_monitorHashProcess && process->type() != hashProcessType)
	{
		return;
	}

	__itt_task_end( g_domain);

}

#endif //GAFFER_VTUNE
