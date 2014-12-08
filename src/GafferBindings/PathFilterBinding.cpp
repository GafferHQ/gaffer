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
#include "boost/python/suite/indexing/container_utils.hpp"

#include "IECorePython/RunTimeTypedBinding.h"

#include "Gaffer/Path.h"
#include "Gaffer/PathFilter.h"

#include "GafferBindings/PathFilterBinding.h"
#include "GafferBindings/SignalBinding.h"

using namespace boost::python;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;

namespace
{

template<typename WrappedType>
class PathFilterWrapper : public IECorePython::RunTimeTypedWrapper<WrappedType>
{

	public :

		PathFilterWrapper( PyObject *self, IECore::CompoundDataPtr userData )
			:	IECorePython::RunTimeTypedWrapper<WrappedType>( self, userData )
		{
		}

		virtual void doFilter( std::vector<PathPtr> &paths ) const
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "_filter" );
				if( f )
				{
					list pythonPaths;
					for( std::vector<PathPtr>::const_iterator it = paths.begin(), eIt = paths.end(); it != eIt; ++it )
					{
						pythonPaths.append( *it );
					}
					pythonPaths = extract<list>( f( pythonPaths ) );
					paths.clear();
					boost::python::container_utils::extend_container( paths, pythonPaths );
					return;
				}
			}
			WrappedType::doFilter( paths );
		}

};

list filter( PathFilter &f, list pythonPaths )
{
	std::vector<PathPtr> paths;
	boost::python::container_utils::extend_container( paths, pythonPaths );
	f.filter( paths );

	list result;
	for( std::vector<PathPtr>::const_iterator it = paths.begin(), eIt = paths.end(); it != eIt; ++it )
	{
		result.append( *it );
	}
	return result;
}

struct ChangedSlotCaller
{
	boost::signals::detail::unusable operator()( boost::python::object slot, PathFilterPtr f )
	{
		slot( f );
		return boost::signals::detail::unusable();
	}
};

} // namespace

void GafferBindings::bindPathFilter()
{
	typedef PathFilterWrapper<PathFilter> Wrapper;

	scope s = RunTimeTypedClass<PathFilter, Wrapper>()
		.def( init<IECore::CompoundDataPtr>( ( arg( "userData" ) = object() ) ) )
		.def( "userData", &PathFilter::userData, return_value_policy<CastToIntrusivePtr>() )
		.def( "setEnabled", &PathFilter::setEnabled )
		.def( "getEnabled", &PathFilter::getEnabled )
		.def( "filter", &filter )
		.def( "changedSignal", &PathFilter::changedSignal, return_internal_reference<1>() )
	;

	SignalBinder<PathFilter::ChangedSignal, DefaultSignalCaller<PathFilter::ChangedSignal>, ChangedSlotCaller>::bind( "PathChangedSignal" );
}
