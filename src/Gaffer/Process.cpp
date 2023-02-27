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

#include "Gaffer/Process.h"

#include "Gaffer/Context.h"
#include "Gaffer/Monitor.h"
#include "Gaffer/Node.h"
#include "Gaffer/Plug.h"
#include "Gaffer/ScriptNode.h"

#include "IECore/Canceller.h"

#include "tbb/enumerable_thread_specific.h"

#include "fmt/format.h"

using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

std::string prefixedWhat( const IECore::Exception &e )
{
	std::string s = std::string( e.type() );
	if( s == "Exception" )
	{
		// Prefixing with type wouldn't add any useful information.
		return e.what();
	}
	s += " : "; s += e.what();
	return s;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Process
//////////////////////////////////////////////////////////////////////////

Process::Process( const IECore::InternedString &type, const Plug *plug, const Plug *destinationPlug )
	:	m_type( type ), m_plug( plug ), m_destinationPlug( destinationPlug ? destinationPlug : plug )
{
	IECore::Canceller::check( context()->canceller() );
	m_parent = m_threadState->m_process;
	m_threadState->m_process = this;

	for( const auto &m : *m_threadState->m_monitors )
	{
		m->processStarted( this );
	}
}

Process::~Process()
{
	for( const auto &m : *m_threadState->m_monitors )
	{
		m->processFinished( this );
	}

	if( context()->canceller() )
	{
		const auto t = context()->canceller()->elapsedTime();
		if( t > std::chrono::seconds( 1 ) )
		{
			IECore::msg(
				IECore::Msg::Warning, "Process::~Process",
				fmt::format(
					"Cancellation for `{}` ({}) took {}s",
					plug()->fullName(), type().string(),
					std::chrono::duration<float>( t ).count()
				)
			);
		}
	}
}

const Process *Process::current()
{
	return ThreadState::current().m_process;
}

void Process::handleException()
{
	try
	{
		// Rethrow the current exception
		// so we can examine it.
		throw;
	}
	catch( const IECore::Cancelled &e )
	{
		// Process is just being cancelled. No need
		// to report via `emitError()`.
		throw;
	}
	catch( const ProcessException &e )
	{
		emitError( e.what(), e.plug() );
		throw;
	}
	catch( const IECore::Exception &e )
	{
		emitError( prefixedWhat( e ) );
		// Wrap in a ProcessException. This allows us to correctly
		// transport the source plug up the call chain, and also
		// provides a more useful error message to the unlucky
		// recipient.
		ProcessException::wrapCurrentException( *this );
	}
	catch( const std::exception &e )
	{
		emitError( e.what() );
		// Wrap in a ProcessException. This allows us to correctly
		// transport the source plug up the call chain, and also
		// provides a more useful error message to the unlucky
		// recipient.
		ProcessException::wrapCurrentException( *this );
	}
	catch( ... )
	{
		emitError( "Unknown error" );
		ProcessException::wrapCurrentException( *this );
	}
}

void Process::emitError( const std::string &error, const Plug *source ) const
{
	const Plug *plug = m_destinationPlug;
	while( plug )
	{
		if( plug->direction() == Plug::Out )
		{
			if( const Node *node = plug->node() )
			{
				node->errorSignal()( plug, source ? source : m_plug, error );
			}
		}
		plug = plug != m_plug ? plug->getInput() : nullptr;
	}
}

bool Process::forceMonitoringInternal( const ThreadState &s, const Plug *plug, const IECore::InternedString &processType )
{
	if( s.m_monitors )
	{
		for( const auto &m : *s.m_monitors )
		{
			if( m->forceMonitoring( plug, processType ) )
			{
				return true;
			}
		}
	}

	return false;
}


//////////////////////////////////////////////////////////////////////////
// ProcessException
//////////////////////////////////////////////////////////////////////////

ProcessException::ProcessException( const ConstPlugPtr &plug, const Context *context, IECore::InternedString processType, const std::exception_ptr &exception, const char *what )
	:	std::runtime_error( formatWhat( plug.get(), what ) ), m_plug( plug ), m_context( new Context( *context ) ), m_processType( processType ), m_exception( exception )
{
}

const Plug *ProcessException::plug() const
{
	return m_plug.get();
}

const Context *ProcessException::context() const
{
	return m_context.get();
}

void ProcessException::rethrowUnwrapped() const
{
	std::rethrow_exception( m_exception );
}

IECore::InternedString ProcessException::processType() const
{
	return m_processType;
}

void ProcessException::wrapCurrentException( const Process &process )
{
	wrapCurrentException( process.plug(), process.context(), process.type() );
}

void ProcessException::wrapCurrentException( const ConstPlugPtr &plug, const Context *context, IECore::InternedString processType )
{
	assert( std::current_exception() );
	try
	{
		throw;
	}
	catch( const IECore::Cancelled &e )
	{
		throw;
	}
	catch( const ProcessException &e )
	{
		throw;
	}
	catch( const IECore::Exception &e )
	{
		const std::string w = prefixedWhat( e );
		throw ProcessException( plug, context, processType, std::current_exception(), w.c_str() );
	}
	catch( const std::exception &e )
	{
		throw ProcessException( plug, context, processType, std::current_exception(), e.what() );
	}
	catch( ... )
	{
		throw ProcessException( plug, context, processType, std::current_exception(), "Unknown error" );
	}
}

std::string ProcessException::formatWhat( const Plug *plug, const char *what )
{
	return plug->relativeName( plug->ancestor<ScriptNode>() ) + " : " + what;
}
