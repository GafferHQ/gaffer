//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFER_PARAMETERHANDLER_H
#define GAFFER_PARAMETERHANDLER_H

#include "boost/function.hpp"

#include "IECore/Parameter.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Plug );
IE_CORE_FORWARDDECLARE( GraphComponent );
IE_CORE_FORWARDDECLARE( ParameterHandler );

class ParameterHandler : public IECore::RefCounted
{

	public :

		IE_CORE_DECLAREMEMBERPTR( ParameterHandler );

		virtual ~ParameterHandler();
		
		IECore::ParameterPtr parameter();
		IECore::ConstParameterPtr parameter() const;

		virtual void setParameterValue() = 0;
		virtual void setPlugValue() = 0;
		
		/// Returns a handler for the specified parameter, creating plugs on the plugParent.
		static ParameterHandlerPtr create( IECore::ParameterPtr parameter, GraphComponentPtr plugParent );
		/// A function for creating ParameterHandlers which will represent a Parameter with a plug on a given
		/// parent.
		typedef boost::function<ParameterHandlerPtr ( IECore::ParameterPtr, GraphComponentPtr plugParent )> Creator;	
		/// Registers a function which can return a ParameterHandler for a given Parameter type.
		static void registerParameterHandler( IECore::TypeId parameterType, Creator creator );
		
	protected :
		
		ParameterHandler( IECore::ParameterPtr parameter );
		
		/// Create a static instance of this to automatically register a derived class
		/// with the factory mechanism. Derived class must have a constructor of the form
		/// Derived( ParameterType::Ptr parameter, GraphComponentPtr plugParent ).
		template<typename HandlerType, typename ParameterType>
		struct ParameterHandlerDescription
		{
				ParameterHandlerDescription() { ParameterHandler::registerParameterHandler( ParameterType::staticTypeId(), &creator ); };
			private :
				static ParameterHandlerPtr creator( IECore::ParameterPtr parameter, GraphComponentPtr plugParent ) { return new HandlerType( IECore::staticPointerCast<ParameterType>( parameter ), plugParent ); };
		};
		
	private :
	
		typedef std::map<IECore::TypeId, Creator> CreatorMap;
		static CreatorMap &creators();
		
		IECore::ParameterPtr m_parameter;

};

} // namespace Gaffer

#endif // GAFFER_PARAMETERHANDLER_H
