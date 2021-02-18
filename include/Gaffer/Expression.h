//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFER_EXPRESSION_H
#define GAFFER_EXPRESSION_H

#include "Gaffer/ComputeNode.h"
#include "Gaffer/TypedObjectPlug.h"

#include <functional>

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( StringPlug )

class GAFFER_API Expression : public ComputeNode
{

	public :

		Expression( const std::string &name=defaultName<Expression>() );
		~Expression() override;

		GAFFER_NODE_DECLARE_TYPE( Gaffer::Expression, ExpressionTypeId, ComputeNode );

		/// Fills the vector with the names of all currently available languages.
		static void languages( std::vector<std::string> &languages );

		/// Returns an identity expression which will set the plug to
		/// its current value using the specified language. Returns ""
		/// if the language does not support the plug.
		static std::string defaultExpression( const ValuePlug *output, const std::string &language );

		/// Sets the node up to evaluate the given expression in the given language.
		/// This is achieved by creating local plugs which are connected to the plugs
		/// referenced by the expression, and executing the expression to provide
		/// output values on demand in compute().
		/// \undoable
		void setExpression( const std::string &expression, const std::string &language );
		/// Returns the expression this node is currently set up to evaluate.
		std::string getExpression( std::string &language ) const;

		typedef boost::signal<void (Expression *)> ExpressionChangedSignal;
		/// Signal emitted whenever the expression has changed.
		ExpressionChangedSignal &expressionChangedSignal();

		/// Returns a string which can be used to refer to the
		/// plug in the current expression. Returns "" if the
		/// plug cannot be supported.
		std::string identifier( const ValuePlug *plug ) const;

		IE_CORE_FORWARDDECLARE( Engine )

		/// Abstract base class for adding languages
		/// for use in the Expression node. All methods
		/// are protected as Engines are for the internal
		/// use of the Expression node only.
		class Engine : public IECore::RefCounted
		{

			public :

				IE_CORE_DECLAREMEMBERPTR( Engine );

			protected :

				/// @name Parsing and execution
				///
				/// These methods are used to set up a particular expression on
				/// this Engine instance and later execute it. They rely on the
				/// Engine maintaining internal state to represent the last
				/// parsed expression.
				///
				////////////////////////////////////////////////////////////////////
				//@{
				/// Parses the given expression to prepare the Engine for execution.
				/// Implementations must fill the inputs and outputs array with plugs
				/// that are read from and written to by the expression, and the
				/// contextVariables array with the names of context variables the
				/// expression will access.
				virtual void parse( Expression *node, const std::string &expression, std::vector<ValuePlug *> &inputs, std::vector<ValuePlug *> &outputs, std::vector<IECore::InternedString> &contextVariables ) = 0;
				/// Executes the last parsed expression in the specified context, using the values
				/// provided by proxyInputs and returning an array containing a value for
				/// each output plug. The results returned will later be passed to apply()
				/// to apply them to each of the individual output plugs.
				/// \threading This function may be called concurrently.
				virtual IECore::ConstObjectVectorPtr execute( const Context *context, const std::vector<const ValuePlug *> &proxyInputs ) const = 0;
				/// What cache policy should be used for executing the expression
				virtual Gaffer::ValuePlug::CachePolicy executeCachePolicy() const = 0;
				//@}

				/// @name Language utilities
				///
				/// These methods provide general utilities pertaining to the language
				/// the engine implements, and should not depend on any particular
				/// expression state.
				///
				////////////////////////////////////////////////////////////////////
				//@{
				/// Sets the `proxyOutput` plug using the `value` computed previously in execute().
				/// Note that if a compound plug is written to by the expression, apply()
				/// will be called for each of the children of the compound, and it is the
				/// responsibility of the engine to decompose the value for each child plug
				/// suitably. In this case the `topLevelProxyOutput` argument provides the
				/// proxy for the compound plug itself.
				/// \threading This function may be called concurrently.
				virtual void apply( ValuePlug *proxyOutput, const ValuePlug *topLevelProxyOutput, const IECore::Object *value ) const = 0;
				/// Used to implement Expression::identifier.
				virtual std::string identifier( const Expression *node, const ValuePlug *plug ) const = 0;
				/// Returns a new expression, equivalent to the original but now acting on the
				/// new plugs rather than the old ones. New plugs may be null in the event that
				/// a user has manually disconnected plugs. Note that this should not modify
				/// the current engine in any way, but just return a new expression.
				virtual std::string replace( const Expression *node, const std::string &expression, const std::vector<const ValuePlug *> &oldPlugs, const std::vector<const ValuePlug *> &newPlugs ) const = 0;
				/// Used to implement Expression::defaultExpression().
				virtual std::string defaultExpression( const ValuePlug *output ) const = 0;
				//@}

				/// Creates an engine of the specified type.
				static EnginePtr create( const std::string engineType );

				typedef std::function<EnginePtr ()> Creator;
				static void registerEngine( const std::string engineType, Creator creator );
				static void registeredEngines( std::vector<std::string> &engineTypes );

				template<class T>
				struct EngineDescription
				{
					EngineDescription( const std::string &engineType ) { registerEngine( engineType, &creator ); };
					static EnginePtr creator() { return new T; };
				};

			private :

				friend class Expression;

				typedef std::map<std::string, Creator> CreatorMap;
				static CreatorMap &creators();

		};

		void affects( const Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const override;
		void compute( ValuePlug *output, const Context *context ) const override;

		Gaffer::ValuePlug::CachePolicy computeCachePolicy( const Gaffer::ValuePlug *output ) const override;

	private :

		static size_t g_firstPlugIndex;

		/// Private plug for storing the type of the engine.
		StringPlug *enginePlug();
		const StringPlug *enginePlug() const;

		/// Private plug for storing the expression text.
		StringPlug *expressionPlug();
		const StringPlug *expressionPlug() const;

		// For each input to the expression, we add a child plug
		// below this one, and connect it to the outside world.
		ValuePlug *inPlug();
		const ValuePlug *inPlug() const;

		// For each output from the expression, we add a child plug
		// below this one, and connect it to the outside world.
		ValuePlug *outPlug();
		const ValuePlug *outPlug() const;

		// We want to allow an expression to write to multiple output
		// plugs, but a compute() may only be performed for one child
		// of outPlug() at a time. This intermediate plug is used to
		// cache all the results of Engine::execute(), and then we
		// can dole them out individually for each outPlug() child
		// compute.
		ObjectVectorPlug *executePlug();
		const ObjectVectorPlug *executePlug() const;

		void updatePlugs( const std::vector<ValuePlug *> &inPlugs, const std::vector<ValuePlug *> &outPlugs );
		void updatePlug( ValuePlug *parentPlug, size_t childIndex, ValuePlug *plug );
		void removeChildren( ValuePlug *parentPlug, size_t startChildIndex );

		std::string transcribe( const std::string &expression, bool toInternalForm ) const;

		void plugSet( const Plug *plug );

		EnginePtr m_engine;
		std::vector<IECore::InternedString> m_contextNames;

		ExpressionChangedSignal m_expressionChangedSignal;

};

IE_CORE_DECLAREPTR( Expression )

} // namespace Gaffer

#endif // GAFFER_EXPRESSION_H
