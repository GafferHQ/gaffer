//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

#include "PathFilterBinding.h"

#include "IECorePython/RunTimeTypedBinding.h"

#include "GafferBindings/SignalBinding.h"

#include "Gaffer/CompoundPathFilter.h"
#include "Gaffer/FileSequencePathFilter.h"
#include "Gaffer/HiddenFilePathFilter.h"
#include "Gaffer/LeafPathFilter.h"
#include "Gaffer/MatchPatternPathFilter.h"
#include "Gaffer/Path.h"
#include "Gaffer/PathFilter.h"

#include "IECorePython/ExceptionAlgo.h"

#include "boost/python/suite/indexing/container_utils.hpp"

using namespace boost::python;
using namespace IECore;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;

namespace
{

// PathFilter
// ==========

template<typename WrappedType>
class PathFilterWrapper : public IECorePython::RunTimeTypedWrapper<WrappedType>
{

	public :

		PathFilterWrapper( PyObject *self, IECore::CompoundDataPtr userData )
			:	IECorePython::RunTimeTypedWrapper<WrappedType>( self, userData )
		{
		}

		void doFilter( std::vector<PathPtr> &paths, const IECore::Canceller *canceller ) const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "_filter" );
					if( f )
					{
						list pythonPaths;
						for( std::vector<PathPtr>::const_iterator it = paths.begin(), eIt = paths.end(); it != eIt; ++it )
						{
							pythonPaths.append( *it );
						}
						// Beware! We are relying on `canceller` living longer than the Python object
						// created by `ptr()`.
						pythonPaths = extract<list>( f( pythonPaths, boost::python::ptr( canceller ) ) );
						paths.clear();
						boost::python::container_utils::extend_container( paths, pythonPaths );
						return;
					}
				}
				catch( const boost::python::error_already_set &e )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
			WrappedType::doFilter( paths, canceller );
		}

};

list filter( PathFilter &f, list pythonPaths, const IECore::Canceller *canceller )
{
	std::vector<PathPtr> paths;
	boost::python::container_utils::extend_container( paths, pythonPaths );
	f.filter( paths, canceller );

	list result;
	for( std::vector<PathPtr>::const_iterator it = paths.begin(), eIt = paths.end(); it != eIt; ++it )
	{
		result.append( *it );
	}
	return result;
}

struct ChangedSlotCaller
{
	void operator()( boost::python::object slot, PathFilterPtr f )
	{
		slot( f );
	}
};

// MatchPatternPathFilter
// ======================

MatchPatternPathFilterPtr constructMatchPatternPathFilter( object pythonPatterns, const char *propertyName, bool leafOnly )
{
	std::vector<StringAlgo::MatchPattern> patterns;
	boost::python::container_utils::extend_container( patterns, pythonPatterns );
	return new MatchPatternPathFilter( patterns, propertyName, leafOnly );
}

void setMatchPatterns( MatchPatternPathFilter &f, object pythonPatterns )
{
	std::vector<StringAlgo::MatchPattern> patterns;
	boost::python::container_utils::extend_container( patterns, pythonPatterns );
	f.setMatchPatterns( patterns );
}

list getMatchPatterns( const MatchPatternPathFilter &f )
{
	list result;
	const std::vector<StringAlgo::MatchPattern> &patterns = f.getMatchPatterns();
	for( std::vector<StringAlgo::MatchPattern>::const_iterator it = patterns.begin(), eIt = patterns.end(); it != eIt; ++it )
	{
		result.append( *it );
	}
	return result;
}

const char *getPropertyName( const MatchPatternPathFilter &f )
{
	return f.getPropertyName().string().c_str();
}

// CompoundPathFilter
// ======================

void setFilters( CompoundPathFilter &f, object pythonFilters )
{
	CompoundPathFilter::Filters filters;
	boost::python::container_utils::extend_container( filters, pythonFilters );
	f.setFilters( filters );
}

list getFilters( const CompoundPathFilter &f )
{
	CompoundPathFilter::Filters filters;
	f.getFilters( filters );

	list result;
	for( CompoundPathFilter::Filters::const_iterator it = filters.begin(), eIt = filters.end(); it != eIt; ++it )
	{
		result.append( *it );
	}
	return result;
}

CompoundPathFilterPtr constructCompoundPathFilter( object filters, CompoundDataPtr userData )
{
	CompoundPathFilterPtr result = new CompoundPathFilter( userData );
	setFilters( *result, filters );
	return result;
}

} // namespace

void GafferModule::bindPathFilter()
{

	// PathFilter

	using Wrapper = PathFilterWrapper<PathFilter>;

	{
		scope s = RunTimeTypedClass<PathFilter, Wrapper>()
			.def( init<IECore::CompoundDataPtr>( ( arg( "userData" ) = object() ) ) )
			.def( "userData", &PathFilter::userData, return_value_policy<CastToIntrusivePtr>() )
			.def( "setEnabled", &PathFilter::setEnabled )
			.def( "getEnabled", &PathFilter::getEnabled )
			.def( "filter", &filter, ( ( args( "paths" ), arg( "canceller" ) = object() ) ) )
			.def( "changedSignal", &PathFilter::changedSignal, return_internal_reference<1>() )
		;

		SignalClass<PathFilter::ChangedSignal, DefaultSignalCaller<PathFilter::ChangedSignal>, ChangedSlotCaller>( "PathChangedSignal" );
	}

	// MatchPatternPathFilter

	RunTimeTypedClass<MatchPatternPathFilter>()
		.def( "__init__", make_constructor( constructMatchPatternPathFilter, default_call_policies(),
				(
					boost::python::arg_( "patterns" ),
					boost::python::arg_( "propertyName" ) = "name",
					boost::python::arg_( "leafOnly" ) = true
				)
			)
		)
		.def( "setMatchPatterns", &setMatchPatterns )
		.def( "getMatchPatterns", &getMatchPatterns )
		.def( "setPropertyName", &MatchPatternPathFilter::setPropertyName )
		.def( "getPropertyName", &getPropertyName )
		.def( "setInverted", &MatchPatternPathFilter::setInverted )
		.def( "getInverted", &MatchPatternPathFilter::getInverted )
	;

	// LeafPathFilter

	RunTimeTypedClass<LeafPathFilter>()
		.def( init<CompoundDataPtr>( ( arg( "userData" ) = object() ) ) )
	;

	// FileSequencePathFilter

	RunTimeTypedClass<FileSequencePathFilter> filterClass( "FileSequencePathFilter" );
	{
		scope s = filterClass;

		enum_<FileSequencePathFilter::Keep>( "Keep" )
			.value( "Files", FileSequencePathFilter::Files )
			.value( "SequentialFiles", FileSequencePathFilter::SequentialFiles )
			.value( "Sequences", FileSequencePathFilter::Sequences )
			.value( "Concise", FileSequencePathFilter::Concise )
			.value( "Verbose", FileSequencePathFilter::Verbose )
			.value( "All", FileSequencePathFilter::All )
		;
	}

	filterClass
		.def( init<FileSequencePathFilter::Keep, CompoundDataPtr>(
			(
				arg( "mode" ) = FileSequencePathFilter::Concise,
				arg( "userData" ) = object()
			)
		) )
		.def( "getMode", &FileSequencePathFilter::getMode )
		.def( "setMode", &FileSequencePathFilter::setMode )
	;

	// CompoundPathFilter

	RunTimeTypedClass<CompoundPathFilter>()
		.def( "__init__", make_constructor( &constructCompoundPathFilter, default_call_policies(),
				(
					arg( "filters" ) = list(),
					arg( "userData" ) = object()
				)
			)
		)
		.def( "addFilter", &CompoundPathFilter::addFilter )
		.def( "removeFilter", &CompoundPathFilter::removeFilter )
		.def( "setFilters", &setFilters )
		.def( "getFilters", &getFilters )
	;

	// HiddenFilePathFilter

	RunTimeTypedClass<HiddenFilePathFilter>()
		.def( init<CompoundDataPtr>( ( arg( "userData" ) = object() ) ) )
		.def( "setInverted", &HiddenFilePathFilter::setInverted )
		.def( "getInverted", &HiddenFilePathFilter::getInverted )
	;

}
