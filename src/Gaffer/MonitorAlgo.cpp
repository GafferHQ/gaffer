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

#include "Gaffer/ContextMonitor.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/Node.h"
#include "Gaffer/PerformanceMonitor.h"
#include "Gaffer/Plug.h"

#include "IECore/SimpleTypedData.h"

#include "boost/lexical_cast.hpp"

#include <iomanip>

using namespace Imath;
using namespace IECore;
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

	const std::string description = "invalid";
	const std::string annotation = "invalid";
	const std::string annotationPrefix = "invalid";

};

struct HashCountMetric
{

	typedef size_t ResultType;

	ResultType operator() ( const PerformanceMonitor::Statistics &s ) const
	{
		return s.hashCount;
	}

	const std::string description = "number of hash processes";
	const std::string annotation = "performanceMonitor:hashCount";
	const std::string annotationPrefix = "Hash count : ";

};

struct ComputeCountMetric
{

	typedef size_t ResultType;

	ResultType operator() ( const PerformanceMonitor::Statistics &s ) const
	{
		return s.computeCount;
	}

	const std::string description = "number of compute processes";
	const std::string annotation = "performanceMonitor:computeCount";
	const std::string annotationPrefix = "Compute count : ";

};

struct HashDurationMetric
{

	typedef boost::chrono::duration<double> ResultType;

	ResultType operator() ( const PerformanceMonitor::Statistics &s ) const
	{
		return s.hashDuration;
	}

	const std::string description = "time spent in hash processes";
	const std::string annotation = "performanceMonitor:hashDuration";
	const std::string annotationPrefix = "Hash time : ";

};

struct ComputeDurationMetric
{

	typedef boost::chrono::duration<double> ResultType;

	ResultType operator() ( const PerformanceMonitor::Statistics &s ) const
	{
		return s.computeDuration;
	}

	const std::string description = "time spent in compute processes";
	const std::string annotation = "performanceMonitor:computeDuration";
	const std::string annotationPrefix = "Compute time : ";

};

struct TotalDurationMetric
{

	typedef boost::chrono::duration<double> ResultType;

	ResultType operator() ( const PerformanceMonitor::Statistics &s ) const
	{
		return s.hashDuration + s.computeDuration;
	}

	const std::string description = "sum of time spent in hash and compute processes";
	const std::string annotation = "performanceMonitor:totalDuration";
	const std::string annotationPrefix = "Time : ";

};

struct PerHashDurationMetric
{

	typedef boost::chrono::duration<double> ResultType;

	ResultType operator() ( const PerformanceMonitor::Statistics &s ) const
	{
		return ResultType( s.hashDuration ) / std::max( 1.0, static_cast<double>( s.hashCount ) );
	}

	const std::string description = "time spent per hash process";
	const std::string annotation = "performanceMonitor:perHashDuration";
	const std::string annotationPrefix = "Time per hash : ";

};

struct PerComputeDurationMetric
{

	typedef boost::chrono::duration<double> ResultType;

	ResultType operator() ( const PerformanceMonitor::Statistics &s ) const
	{
		return ResultType( s.computeDuration ) / std::max( 1.0, static_cast<double>( s.computeCount ) );
	}

	const std::string description = "time spent per compute process";
	const std::string annotation = "performanceMonitor:perComputeDuration";
	const std::string annotationPrefix = "Time per compute : ";

};

struct HashesPerComputeMetric
{

	typedef double ResultType;

	ResultType operator() ( const PerformanceMonitor::Statistics &s ) const
	{
		return static_cast<double>( s.hashCount ) / std::max( 1.0, static_cast<double>( s.computeCount ) );
	}

	const std::string description = "number of hash processes per compute process";
	const std::string annotation = "performanceMonitor:hashesPerCompute";
	const std::string annotationPrefix = "Hashes per compute : ";

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
		os << "  " << std::left << std::setw( maxSize + 4 ) << names[i] << items[i] << "\n";
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
		s << "Top " << plugNames.size() << " plugs by " << metric.description << " :\n\n";

		outputItems( plugNames, metrics, s );

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

		s << std::fixed << ": " <<  metric( combinedStatistics );

		return ResultType( "Total " + metric.description, s.str() );
	}

	const PerformanceMonitor::Statistics &combinedStatistics;
};

} // namespace

//////////////////////////////////////////////////////////////////////////
// Annotation utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

template<typename T>
double toDouble( const T &v )
{
	return static_cast<double>( v );
}

template<>
double toDouble( const boost::chrono::duration<double> &v )
{
	return v.count();
}

template<typename T>
Color3f heat( const T &v, const T &m )
{
	const double heatFactor = toDouble( v ) / toDouble( m );
	return lerp( Color3f( 0 ), Color3f( 0.5, 0, 0 ), heatFactor );
}

struct Annotate
{

	Annotate( Node &root, const PerformanceMonitor::StatisticsMap &statistics, bool persistent )
		:	m_root( root ), m_statistics( statistics ), m_persistent( persistent )
	{
	}

	typedef void ResultType;

	template<typename Metric>
	ResultType operator() ( const Metric &metric ) const
	{
		walk<Metric>( m_root, metric );
	}

	private :

		Node &m_root;
		const PerformanceMonitor::StatisticsMap &m_statistics;
		const bool m_persistent;

		template<typename Metric>
		PerformanceMonitor::Statistics walk( Node &node, const Metric &metric ) const
		{
			using Value = typename Metric::ResultType;
			using ChildStatistics = std::pair<Node &, PerformanceMonitor::Statistics>;

			// Accumulate the statistics for all plugs belonging to this node.

			PerformanceMonitor::Statistics result;
			for( Plug::RecursiveIterator plugIt( &node ); !plugIt.done(); ++plugIt )
			{
				auto it = m_statistics.find( plugIt->get() );
				if( it != m_statistics.end() )
				{
					result += it->second;
				}
			}

			// Gather statistics for all child nodes.

			std::vector<ChildStatistics> childStatistics;
			Value maxChildValue( 0 );

			for( Node::Iterator childNodeIt( &node ); !childNodeIt.done(); ++childNodeIt )
			{
				Node &childNode = **childNodeIt;
				const auto cs = walk( childNode, metric );
				childStatistics.push_back( ChildStatistics( childNode, cs ) );
				maxChildValue = std::max( maxChildValue, metric( cs ) );
			}

			// Apply metadata for child nodes. We must do this
			// after gathering because we need `maxChildValue` to
			// calculate the heat map.

			for( const auto &cs : childStatistics )
			{
				const Value value = metric( cs.second );
				if( value == Value( 0 ) )
				{
					continue;
				}

				MetadataAlgo::addAnnotation(
					&cs.first,
					metric.annotation,
					MetadataAlgo::Annotation(
						metric.annotationPrefix + boost::lexical_cast<std::string>( value ),
						heat( value, maxChildValue )
					),
					m_persistent
				);

				result += cs.second;
			}

			return result;
		}

};

const std::string g_contextAnnotationName = "annotation:contextMonitor";

ContextMonitor::Statistics annotateContextWalk( Node &node, const ContextMonitor::StatisticsMap &statistics, bool persistent )
{

	using ChildStatistics = std::pair<Node &, ContextMonitor::Statistics>;

	// Accumulate the statistics for all plugs belonging to this node.

	ContextMonitor::Statistics result;
	for( Plug::RecursiveIterator plugIt( &node ); !plugIt.done(); ++plugIt )
	{
		auto it = statistics.find( plugIt->get() );
		if( it != statistics.end() )
		{
			result += it->second;
		}
	}

	// Gather statistics for all child nodes.

	std::vector<ChildStatistics> childStatistics;
	size_t maxUniqueContexts( 0 );

	for( Node::Iterator childNodeIt( &node ); !childNodeIt.done(); ++childNodeIt )
	{
		Node &childNode = **childNodeIt;
		const auto cs = annotateContextWalk( childNode, statistics, persistent );
		childStatistics.push_back( ChildStatistics( childNode, cs ) );
		maxUniqueContexts = std::max( maxUniqueContexts, cs.numUniqueContexts() );
	}

	// Apply metadata for child nodes. We must do this
	// after gathering because we need `childStatisticsSum` to
	// calculate the heat map.

	for( const auto &cs : childStatistics )
	{
		if( !cs.second.numUniqueContexts() )
		{
			continue;
		}

		std::string text = "Contexts : " + std::to_string( cs.second.numUniqueContexts() ) + "\n";

		auto variableNames = cs.second.variableNames();
		for( const auto &name : variableNames )
		{
			const size_t n = cs.second.numUniqueValues( name );
			if( n > 1 )
			{
				text += "\n  " + name.string() + " : " + std::to_string( n );
			}
		}

		MetadataAlgo::addAnnotation(
			&cs.first,
			g_contextAnnotationName,
			MetadataAlgo::Annotation( text, heat( cs.second.numUniqueContexts(), maxUniqueContexts ) ),
			persistent
		);

		result += cs.second;
	}

	return result;

}

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

	ss << "PerformanceMonitor Summary :\n\n";
	outputItems( names, values, ss );
	ss << "\n";

	// Now show breakdowns by plugs in each category
	std::string s = ss.str();
	for( int m = First; m <= Last; ++m )
	{
		s += formatStatistics( monitor, static_cast<PerformanceMetric>( m ), maxLinesPerMetric );
		if( m != Last )
		{
			s += "\n";
		}
	}
	return s;
}

std::string formatStatistics( const PerformanceMonitor &monitor, PerformanceMetric metric, size_t maxLines )
{
	return dispatchMetric<FormatStatistics>( FormatStatistics( monitor.allStatistics(), maxLines ), metric );
}

void annotate( Node &root, const PerformanceMonitor &monitor, bool persistent )
{
	for( int m = First; m <= Last; ++m )
	{
		annotate( root, monitor, static_cast<PerformanceMetric>( m ), persistent );
	}
}

void annotate( Node &root, const PerformanceMonitor &monitor, PerformanceMetric metric, bool persistent )
{
	dispatchMetric<Annotate>( Annotate( root, monitor.allStatistics(), persistent ), metric );
}

void annotate( Node &root, const ContextMonitor &monitor, bool persistent )
{
	annotateContextWalk( root, monitor.allStatistics(), persistent );
}

} // namespace MonitorAlgo

} // namespace Gaffer
