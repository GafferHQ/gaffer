//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
//  Copyright (c) 2011, John Haddon. All rights reserved.
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

#ifndef GAFFERBINDINGS_PARAMETERISEDHOLDERBINDING_H
#define GAFFERBINDINGS_PARAMETERISEDHOLDERBINDING_H

#include "IECore/Parameter.h"
#include "IECorePython/Wrapper.h"

#include "boost/format.hpp"

#include "GafferBindings/NodeBinding.h"

namespace GafferBindings
{

template<typename WrappedType>
class ParameterisedHolderWrapper : public NodeWrapper<WrappedType>
{

	public :
	
		ParameterisedHolderWrapper( PyObject *self, const std::string &name, const boost::python::dict &inputs, const boost::python::tuple &dynamicPlugs )
			:	NodeWrapper<WrappedType>( self, name, inputs, dynamicPlugs )
		{
			WrappedType::loadParameterised();
		}
		
		virtual IECore::RunTimeTypedPtr loadClass( const std::string &className, int classVersion, const std::string &searchPathEnvVar ) const
		{
			IECorePython::ScopedGILLock gilLock;
			boost::python::dict scopeDict;
			scopeDict["IECore"] = boost::python::import( "IECore" );
			std::string toExecute = boost::str(
				boost::format(
					"IECore.ClassLoader.defaultLoader( \"%s\" ).load( \"%s\", %d )()\n"
				) % searchPathEnvVar % className % classVersion
			);
			boost::python::object result = boost::python::eval( toExecute.c_str(), scopeDict, scopeDict );
			return boost::python::extract<IECore::RunTimeTypedPtr>( result );
		}
	
		virtual void parameterChanged( IECore::Parameter *parameter )
		{			
			IECorePython::ScopedGILLock gilLock;
			boost::python::object pythonParameterised( WrappedType::getParameterised() );
			if( PyObject_HasAttrString( pythonParameterised.ptr(), "parameterChanged" ) )
			{
				WrappedType::parameterHandler()->setParameterValue();
				
				typename WrappedType::ParameterModificationContext parameterModificationContext( this );
				
				pythonParameterised.attr( "parameterChanged" )( IECore::ParameterPtr( parameter ) );
			}
		}

};
	
void bindParameterisedHolder();

} // namespace GafferBindings

#endif // GAFFERBINDINGS_PARAMETERISEDHOLDERBINDING_H
