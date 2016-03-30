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

#include "boost/python.hpp"
#include "boost/format.hpp"

#include "Gaffer/Monitor.h"
#include "Gaffer/PerformanceMonitor.h"
#include "Gaffer/Plug.h"

#include "GafferBindings/MonitorBinding.h"

using namespace boost::python;
using namespace Gaffer;
using namespace GafferBindings;

namespace
{

void enterScope( Monitor &m )
{
	m.setActive( true );
}

void exitScope( Monitor &m, object type, object value, object traceBack )
{
	m.setActive( false );
}

std::string repr( PerformanceMonitor::Statistics &s )
{
	return boost::str(
		boost::format( "Gaffer.PerformanceMonitor.Statistics( hashCount = %d, computeCount = %d )" )
			% s.hashCount
			% s.computeCount
	);
}

dict allStatistics( PerformanceMonitor &m )
{
	dict result;
	const PerformanceMonitor::StatisticsMap &s = m.allStatistics();
	for( PerformanceMonitor::StatisticsMap::const_iterator it = s.begin(), eIt = s.end(); it != eIt; ++it )
	{
		result[boost::const_pointer_cast<Plug>( it->first)] = it->second;
	}
	return result;
}

} // namespace

void GafferBindings::bindMonitor()
{

	class_<Monitor, boost::noncopyable>( "Monitor", no_init )
		.def( "setActive", &Monitor::setActive )
		.def( "getActive", &Monitor::getActive )
		.def( "__enter__", &enterScope, return_self<>() )
		.def( "__exit__", &exitScope )
	;

	scope s = class_<PerformanceMonitor, bases<Monitor>, boost::noncopyable >( "PerformanceMonitor" )
		.def( "allStatistics", &allStatistics )
		.def( "plugStatistics", &PerformanceMonitor::plugStatistics, return_value_policy<copy_const_reference>() )
	;

	class_<PerformanceMonitor::Statistics>( "Statistics" )
		.def( init<size_t, size_t>( ( arg( "hashCount" ) = 0, arg( "computeCount" ) = 0 ) ) )
		.def_readwrite( "hashCount", &PerformanceMonitor::Statistics::hashCount )
		.def_readwrite( "computeCount", &PerformanceMonitor::Statistics::computeCount )
		.def( self == self )
		.def( self != self )
		.def( "__repr__", &repr )
	;

}
