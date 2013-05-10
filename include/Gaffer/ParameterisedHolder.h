//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

#ifndef GAFFER_PARAMETERISEDHOLDER_H
#define GAFFER_PARAMETERISEDHOLDER_H

#include "Gaffer/ComputeNode.h"

namespace IECore
{

class ParameterisedInterface;
class Parameter;

} // namespace IECore

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( CompoundParameterHandler );

template<typename BaseType>
class ParameterisedHolder : public BaseType
{

	public :

		IECORE_RUNTIMETYPED_DECLARETEMPLATE( ParameterisedHolder<BaseType>, BaseType );
		IE_CORE_DECLARERUNTIMETYPEDDESCRIPTION( ParameterisedHolder<BaseType> );		

		ParameterisedHolder( const std::string &name=staticTypeName() );
		virtual ~ParameterisedHolder();
		
		/// May be overridden by derived classes, but they must call the base class implementation
		/// first.
		virtual void setParameterised( IECore::RunTimeTypedPtr parameterised, bool keepExistingValues=false );
		void setParameterised( const std::string &className, int classVersion, const std::string &searchPathEnvVar, bool keepExistingValues=false );
		IECore::RunTimeTypedPtr getParameterised( std::string *className = 0, int *classVersion = 0, std::string *searchPathEnvVar = 0 ) const;
		/// Convenience method to return dynamic_cast<const IECore::ParameterisedInterface *>( getParameterised().get() )
		IECore::ParameterisedInterface *parameterisedInterface( std::string *className = 0, int *classVersion = 0, std::string *searchPathEnvVar = 0 );

		CompoundParameterHandlerPtr parameterHandler();
		ConstCompoundParameterHandlerPtr parameterHandler() const;
		
		/// \todo Do we need this now we have parameterHandler()? Do we keep this so that
		/// we're consistent with the interface provided in IECoreMaya?
		void setParameterisedValues();
		
		/// \todo Is this even needed? Can we just use an UndoContext instead?
		class ParameterModificationContext
		{
			public :
				ParameterModificationContext( Ptr parameterisedHolder );
				~ParameterModificationContext();
			private :
				Ptr m_parameterisedHolder;
		};
	
	protected :
	
		/// Returns a new instance of the specified class. This is implemented to throw an
		/// Exception in libGaffer, but the libGafferBindings library implements it
		/// by using the IECore.ClassLoader in python. This allows us to keep libGaffer from
		/// having a python dependency.
		virtual IECore::RunTimeTypedPtr loadClass( const std::string &className, int classVersion, const std::string &searchPathEnvVar ) const;	
		/// Called whenever a plug representing a parameter has changed. This is implemented to do
		/// nothing in libGaffer, but the libGafferBindings library implements it to call
		/// the parameterChanged() python method on the held class, if it exists. This allows
		/// us to keep libGaffer from having a python dependency. In future,
		/// Parameterised::parameterChanged() might become a part of the Cortex C++ API,
		/// in which case we can do all the work in libGaffer.
		virtual void parameterChanged( IECore::RunTimeTyped *parameterised, IECore::Parameter *parameter );
		
	private :
	
		void plugSet( PlugPtr plug );
		
		friend class ParameterModificationContext;
	
		IECore::RunTimeTypedPtr m_parameterised;
		CompoundParameterHandlerPtr m_parameterHandler;
	
		boost::signals::connection m_plugSetConnection;

};

typedef ParameterisedHolder<Node> ParameterisedHolderNode;
typedef ParameterisedHolder<DependencyNode> ParameterisedHolderDependencyNode;
typedef ParameterisedHolder<ComputeNode> ParameterisedHolderComputeNode;

IE_CORE_DECLAREPTR( ParameterisedHolderNode )
IE_CORE_DECLAREPTR( ParameterisedHolderDependencyNode )
IE_CORE_DECLAREPTR( ParameterisedHolderComputeNode )

} // namespace Gaffer

#endif // GAFFER_PARAMETERISEDHOLDER_H
