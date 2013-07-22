//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012-2013, John Haddon. All rights reserved.
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

#ifndef GAFFER_CONTEXT_H
#define GAFFER_CONTEXT_H

#include "IECore/CompoundData.h"
#include "IECore/InternedString.h"

#include "boost/signals.hpp"

namespace Gaffer
{

/// This class defines the context in which a computation is performed. The most basic element
/// common to all Contexts is the frame number, but a context may hold entirely arbitrary
/// information useful to specific types of computation. Contexts are made current using the
/// nested Scope class - any computation triggered by ValuePlug::getValue() calls will be
/// made with respect to the current Context. Each thread maintains a stack of contexts,
/// allowing computations in different contexts to be performed in parallel, and allowing
/// contexts to be changed temporarily for a specific computation.
class Context : public IECore::RefCounted
{

	public :

		Context();
		Context( const Context &other );
		~Context();
		
		IE_CORE_DECLAREMEMBERPTR( Context )
		
		typedef boost::signal<void ( const Context *context, const IECore::InternedString & )> ChangedSignal;
	
		template<typename T, typename Enabler=void>
		struct Accessor;
		
		/// Calling with simple types (e.g float) will automatically
		/// create a TypedData<T> to store the value.
		template<typename T>
		void set( const IECore::InternedString &name, const T &value );
		/// Can be used to retrieve simple types :
		///		float f = context->get<float>( "myFloat" )
		/// And also IECore::Data types :
		///		const FloatData *f = context->get<FloatData>( "myFloat" )
		template<typename T>
		typename Accessor<T>::ResultType get( const IECore::InternedString &name ) const;
		/// As above but returns defaultValue when an entry is not found, rather than throwing
		/// an Exception.
		template<typename T>
		typename Accessor<T>::ResultType get( const IECore::InternedString &name, typename Accessor<T>::ResultType defaultValue ) const;
		
		/// Fills the specified vector with the names of all items in the Context.
		void names( std::vector<IECore::InternedString> &names ) const;
		
		/// Convenience method returning get<float>( "frame" ).
		float getFrame() const;
		/// Convenience method calling set<float>( "frame", frame ).
		void setFrame( float frame );

		/// A signal emitted when an element of the context is changed.
		ChangedSignal &changedSignal();
		
		IECore::MurmurHash hash() const;
		
		bool operator == ( const Context &other ) const;
		bool operator != ( const Context &other ) const;
		
		/// Performs variable substitution of $name, ${name} and ###
		/// keys in input, using values from the context.
		/// \todo I'm not entirely sure this belongs here. If we had
		/// an abstract base class for dictionary-style access to things
		/// then we could have a separate substitute() function capable
		/// of accepting Contexts, CompoundData, CompoundObjects etc.
		std::string substitute( const std::string &input ) const;
		
		/// The Scope class is used to push and pop the current context on
		/// the calling thread.
		class Scope
		{
			
			public :
			
				/// Constructing the Scope pushes the current context.
				Scope( const Context *context );
				/// Destruction of the Scope pops the previously pushed context. 
				~Scope();
		
		};
		
		/// Returns the current context for the calling thread.
		static const Context *current();
		
	private :

		void substituteInternal( const std::string &s, std::string &result, const int recursionDepth ) const;
	
		IECore::CompoundDataPtr m_data;
		ChangedSignal *m_changedSignal;

};

IE_CORE_DECLAREPTR( Context );

} // namespace Gaffer

#include "Gaffer/Context.inl"

#endif // GAFFER_CONTEXT_H
