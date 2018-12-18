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

#include "Gaffer/MonitorAlgo.h"

#include "Gaffer/PerformanceMonitor.h"
#include "Gaffer/Plug.h"

#include <iomanip>

using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Metrics. These are simple structs whose operator() can
// retrieve some information from a Statistics object.
//////////////////////////////////////////////////////////////////////////

namespace
{

struct InvalidMetric
{

	typedef size_t ResultType;

	ResultType operator() ( const PerformanceMonitor::Statistics &s ) const
	{
		return 0;
	}

	const char *description() const
	{
		return "invalid";
	}

	const char *key() const
	{
		return "invalid";
	}

};

struct HashCountMetric
{

	typedef size_t ResultType;

	ResultType operator() ( const PerformanceMonitor::Statistics &s ) const
	{
		return s.hashCount;
	}

	const char *description() const
	{
		return "number of hash processes";
	}

	const char *key() const
	{
		return "num_hash_processes";
	}

};

struct ComputeCountMetric
{

	typedef size_t ResultType;

	ResultType operator() ( const PerformanceMonitor::Statistics &s ) const
	{
		return s.computeCount;
	}

	const char *description() const
	{
		return "number of compute processes";
	}

	const char *key() const
	{
		return "num_compute_processes";
	}
};

struct HashDurationMetric
{

	typedef boost::chrono::duration<double> ResultType;

	ResultType operator() ( const PerformanceMonitor::Statistics &s ) const
	{
		return s.hashDuration;
	}

	const char *description() const
	{
		return "time spent in hash processes";
	}

	const char *key() const
	{
		return "time_hash_processes";
	}

};

struct ComputeDurationMetric
{

	typedef boost::chrono::duration<double> ResultType;

	ResultType operator() ( const PerformanceMonitor::Statistics &s ) const
	{
		return s.computeDuration;
	}

	const char *description() const
	{
		return "time spent in compute processes";
	}

	const char *key() const
	{
		return "time_compute_processes";
	}

};

struct TotalDurationMetric
{

	typedef boost::chrono::duration<double> ResultType;

	ResultType operator() ( const PerformanceMonitor::Statistics &s ) const
	{
		return s.hashDuration + s.computeDuration;
	}

	const char *description() const
	{
		return "sum of time spent in hash and compute processes";
	}

	const char *key() const
	{
		return "time_compute_hash_processes";
	}

};

struct PerHashDurationMetric
{

	typedef boost::chrono::duration<double> ResultType;

	ResultType operator() ( const PerformanceMonitor::Statistics &s ) const
	{
		return ResultType( s.hashDuration ) / std::max( 1.0, static_cast<double>( s.hashCount ) );
	}

	const char *description() const
	{
		return "time spent per hash process";
	}

	const char *key() const
	{
		return "time_per_hash";
	}

};

struct PerComputeDurationMetric
{

	typedef boost::chrono::duration<double> ResultType;

	ResultType operator() ( const PerformanceMonitor::Statistics &s ) const
	{
		return ResultType( s.computeDuration ) / std::max( 1.0, static_cast<double>( s.computeCount ) );
	}

	const char *description() const
	{
		return "time spent per compute process";
	}

	const char *key() const
	{
		return "time_per_compute";
	}
};

struct HashesPerComputeMetric
{

	typedef double ResultType;

	ResultType operator() ( const PerformanceMonitor::Statistics &s ) const
	{
		return static_cast<double>( s.hashCount ) / std::max( 1.0, static_cast<double>( s.computeCount ) );
	}

	const char *description() const
	{
		return "number of hash processes per compute process";
	}

	const char *key() const
	{
		return "hashes_per_compute";
	}

};

// Utility for invoking a templated functor with a particular metric.
template<typename F>
typename F::ResultType dispatchMetric( const F &f, MonitorAlgo::PerformanceMetric performanceMetric )
{
	switch( performanceMetric )
	{
		case MonitorAlgo::HashCount :
			return f( HashCountMetric() );
		case MonitorAlgo::ComputeCount :
			return f( ComputeCountMetric() );
		case MonitorAlgo::HashDuration :
			return f( HashDurationMetric() );
		case MonitorAlgo::ComputeDuration :
			return f( ComputeDurationMetric() );
		case MonitorAlgo::TotalDuration :
			return f( TotalDurationMetric() );
		case MonitorAlgo::PerHashDuration :
			return f( PerHashDurationMetric() );
		case MonitorAlgo::PerComputeDuration :
			return f( PerComputeDurationMetric() );
		case MonitorAlgo::HashesPerCompute :
			return f( HashesPerComputeMetric() );
		default :
			return f( InvalidMetric() );
	}
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Formatting utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

struct PlugAndStatistics
{

	PlugAndStatistics( const PerformanceMonitor::StatisticsMap::value_type &v )
		:	plug( v.first.get() ), statistics( v.second )
	{
	}

	const Plug *plug;
	PerformanceMonitor::Statistics statistics;

};

template<typename Metric>
struct MetricGreater
{

	bool operator() ( const PlugAndStatistics &lhs, const PlugAndStatistics &rhs ) const
	{
		return metric( lhs.statistics ) > metric( rhs.statistics );
	}

	Metric metric;

};

template<typename T>
std::string formatItem(const T& i)
{
	std::stringstream ss;
	ss << i;
	return ss.str();
}

template<>
std::string formatItem(const boost::chrono::duration<double>& i)
{
	std::stringstream ss;
	ss << i.count();
	return ss.str();
}

template<typename Item>
void outputItems( const std::vector<std::string> &names, const std::vector<Item> &items, std::ostream &os )
{
	size_t maxSize = 0;
	for( std::vector<std::string>::const_iterator it = names.begin(), eIt = names.end(); it != eIt; ++it )
	{
		maxSize = std::max( maxSize, it->size() );
	}

	os << std::fixed;
	for( size_t i = 0, e = names.size(); i < e; ++i )
	{
		os << "[ \"" << names[i] << "\"," << formatItem(items[i]) << "]";
		if ( i == ( e - 1 ) )
		{
			continue;
		}
		os << ",\n";
	}
}

struct FormatStatistics
{

	FormatStatistics( const PerformanceMonitor::StatisticsMap &statistics, size_t maxLines )
		:	statistics( statistics ), maxLines( maxLines )
	{
	}

	typedef std::string ResultType;

	template<typename Metric>
	std::string operator() ( const Metric &metric ) const
	{
		std::vector<PlugAndStatistics> v( statistics.begin(), statistics.end() );
		std::sort( v.begin(), v.end(), MetricGreater<Metric>() );

		std::vector<std::string> plugNames; plugNames.reserve( maxLines );
		std::vector<typename Metric::ResultType> metrics; metrics.reserve( maxLines );

		ResultType result;
		for( size_t i = 0; i < maxLines && i < v.size(); ++i )
		{
			typename Metric::ResultType m = metric( v[i].statistics );
			if( m == typename Metric::ResultType( 0 ) )
			{
				break;
			}
			plugNames.push_back( v[i].plug->relativeName( v[i].plug->ancestor( (IECore::TypeId)ScriptNodeTypeId ) ) );
			metrics.push_back( m );
		}

		if( plugNames.empty() )
		{
			return "";
		}

		std::stringstream s;

		s << "\"" << metric.key() << "\": [";

		outputItems( plugNames, metrics, s );

		s << "]";
		return s.str();
	}

	const PerformanceMonitor::StatisticsMap &statistics;
	const size_t maxLines;

};

struct FormatTotalStatistics
{

	FormatTotalStatistics( const PerformanceMonitor::Statistics &combinedStatistics )
		:	combinedStatistics( combinedStatistics )
	{
	}

	typedef std::pair< std::string, std::string > ResultType;

	template<typename Metric>
	ResultType operator() ( const Metric &metric ) const
	{
		std::stringstream s;

		s << formatItem( metric( combinedStatistics ) );

		return ResultType( std::string( "total_" ) + metric.key(), s.str() );
	}

	const PerformanceMonitor::Statistics &combinedStatistics;
};

} // namespace

//////////////////////////////////////////////////////////////////////////
// Implementation of public functions
//////////////////////////////////////////////////////////////////////////

namespace Gaffer
{

namespace MonitorAlgo
{

std::string formatStatistics( const PerformanceMonitor &monitor, size_t maxLinesPerMetric )
{
	// First show totals
	std::vector<std::string> names;
	std::vector<std::string> values;
	for( int m = First; m <= Last; ++m )
	{
		PerformanceMetric metric = static_cast<PerformanceMetric>( m );
		FormatTotalStatistics::ResultType p =
			dispatchMetric<FormatTotalStatistics>( FormatTotalStatistics( monitor.combinedStatistics() ), metric );
		names.push_back( p.first );
		values.push_back( p.second );
	}

	std::stringstream ss;

	ss << "{\"summary\": [";
	outputItems( names, values, ss );
	ss << "], " << std::endl;

	// Now show breakdowns by plugs in each category
	std::string s = ss.str();
	for( int m = First; m <= Last; ++m )
	{
		s += formatStatistics( monitor, static_cast<PerformanceMetric>( m ), maxLinesPerMetric );
		if( m != Last )
		{
			s += ",\n";
		}
	}
	s += "}";

	return s;
}

std::string formatStatistics( const PerformanceMonitor &monitor, PerformanceMetric metric, size_t maxLines  )
{
	return dispatchMetric<FormatStatistics>( FormatStatistics( monitor.allStatistics(), maxLines ), metric );
}

} // namespace MonitorAlgo

} // namespace Gaffer
