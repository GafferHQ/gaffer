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

#ifndef GAFFER_MONITORALGO_H
#define GAFFER_MONITORALGO_H

#include "Gaffer/Export.h"

#include <string>

namespace Gaffer
{

class ContextMonitor;
class Node;
class PerformanceMonitor;

namespace MonitorAlgo
{

enum PerformanceMetric
{
	Invalid,
	TotalDuration,
	HashDuration,
	ComputeDuration,
	PerHashDuration,
	PerComputeDuration,
	HashCount,
	ComputeCount,
	HashesPerCompute,

	First = TotalDuration,
	Last = HashesPerCompute
};

GAFFER_API std::string formatStatistics( const PerformanceMonitor &monitor, size_t maxLinesPerMetric = 50 );
GAFFER_API std::string formatStatistics( const PerformanceMonitor &monitor, PerformanceMetric metric, size_t maxLines = 50 );

GAFFER_API void annotate( Node &root, const PerformanceMonitor &monitor, bool persistent );
/// \todo Remove, and default `persistent = true` above.
GAFFER_API void annotate( Node &root, const PerformanceMonitor &monitor );

GAFFER_API void annotate( Node &root, const PerformanceMonitor &monitor, PerformanceMetric metric, bool persistent );
/// \todo Remove, and default `persistent = true` above.
GAFFER_API void annotate( Node &root, const PerformanceMonitor &monitor, PerformanceMetric metric );

GAFFER_API void annotate( Node &root, const ContextMonitor &monitor, bool persistent );
/// \todo Remove, and default `persistent = true` above.
GAFFER_API void annotate( Node &root, const ContextMonitor &monitor );

} // namespace MonitorAlgo

} // namespace Gaffer

#endif // GAFFER_MONITORALGO_H
