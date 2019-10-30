//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

// uncomment to get additional debug output when parsing an expression
// #define BOOST_SPIRIT_DEBUG

#include "GafferScene/SetAlgo.h"

#include "IECore/MessageHandler.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/fusion/include/adapt_struct.hpp"
#include "boost/spirit/include/classic_core.hpp"
#include "boost/spirit/include/phoenix_operator.hpp"
#include "boost/spirit/include/qi.hpp"
#include "boost/variant/apply_visitor.hpp"
#include "boost/variant/recursive_variant.hpp"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

namespace qi = boost::spirit::qi;
namespace ascii = boost::spirit::ascii;

namespace
{

struct BinaryOp;
struct Nil {};

// Wrap a string into a SetName struct that gives it semantic meaning
struct SetName
{
	std::string name;
};

// Wrap a string into an ObjectName struct that gives it semantic meaning
struct ObjectName
{
	std::string name;
};

// Determine which Ops are supported in SetExpressions
// and provide a way to print them for debugging.
enum Op { And, Or, AndNot };

std::ostream & operator<<( std::ostream &out, const Op &op )
{
	switch( op )
	{
		case Or :
			out << "|"; break;
		case And :
			out << "&"; break;
		case AndNot :
			out << "-"; break;
	}
	return out;
}

struct ExpressionAst
{
	typedef
	boost::variant<
		Nil,
		SetName,
		ObjectName,
		boost::recursive_wrapper<ExpressionAst>,
		boost::recursive_wrapper<BinaryOp>
		>
	type;

	ExpressionAst()
		: expr( Nil() ) {}

	template <typename Expr>
	ExpressionAst( const Expr &expr )
		: expr( expr ) {}

	type expr;
};

struct BinaryOp
{
	BinaryOp(
		const ExpressionAst &left,
		Op op,
		const ExpressionAst &right
	)
		: left( left ), op( op ), right( right ) {}

	ExpressionAst left;
	Op op;
	ExpressionAst right;
};

struct CreateBinaryOpImplementation
{

	typedef ExpressionAst & result_type;

	ExpressionAst & operator()( ExpressionAst &lhs, Op op, ExpressionAst &rhs ) const
	{
		lhs.expr = BinaryOp( lhs.expr, op, rhs );
		return lhs;
	}

};

// Function that we can use as a semantic action in the parser, inserting
// a BinaryOp into the current ExpressionAst.
boost::phoenix::function<CreateBinaryOpImplementation> createBinaryOp;

// Visiting the AST
// ----------------
// For a simple AST with only one operation (AND) on two sets (A and B)
// the output will look like this: op:&(A, B)
// If one of the operands is an operation itself: op:&(A, op:|(B, C))
struct AstPrinter
{
	typedef void result_type;

	AstPrinter()
		: stream( std::cout ) {}

	AstPrinter( std::ostream &stream )
		: stream( stream ) {}

	void operator()( const std::string &n ) const
	{
		stream << n;
	}

	void operator()( const ObjectName &n ) const
	{
		stream << n.name;
	}

	void operator()( const SetName &n ) const
	{
		stream << n.name;
	}

	void operator()( const ExpressionAst &ast ) const
	{
		boost::apply_visitor( *this, ast.expr );
	}

	void operator()( const Nil &nil ) const
	{
	}

	void operator()( const BinaryOp &expr ) const
	{
		stream << "op:" << expr.op << "(";
		boost::apply_visitor( *this, expr.left.expr );
		stream << ", ";
		boost::apply_visitor( *this, expr.right.expr );
		stream << ')';
	}

	std::ostream &stream;
};

#ifdef BOOST_SPIRIT_DEBUG
// support for printing ExpressionsAst's for debugging through BOOST_SPIRIT_DEBUG
std::ostream& operator<<( std::ostream& stream, const ExpressionAst& expr )
{
	AstPrinter printer( stream );
	printer( expr );
	return stream;
}
#endif

// Evaluating the AST
// ------------------
struct AstEvaluator
{
	typedef PathMatcher result_type;

	AstEvaluator( const ScenePlug *scene )
		: m_scene( scene )
	{
	}

	result_type operator()( const SetName &set ) const
	{
		if( !StringAlgo::hasWildcards( set.name ) )
		{
			return m_scene->set( set.name )->readable();
		}

		result_type result;

		IECore::ConstInternedStringVectorDataPtr setNamesData = m_scene->setNamesPlug()->getValue();
		const std::vector<IECore::InternedString> &setNames = setNamesData->readable();
		if( setNames.empty() )
		{
			return result;
		}

		ScenePlug::SetScope setScope( Context::current() );
		for( const IECore::InternedString &setName : setNames )
		{
			if( !StringAlgo::match( setName.string(), set.name ) )
			{
				continue;
			}

			setScope.setSetName( setName );
			ConstPathMatcherDataPtr setData = m_scene->setPlug()->getValue();
			result.addPaths( setData->readable() );
		}

		return result;
	}

	result_type operator()( const ObjectName &object ) const
	{
		PathMatcher result;
		result.addPath( object.name );
		return result;
	}

	result_type operator()( const ExpressionAst &ast ) const
	{
		return boost::apply_visitor( *this, ast.expr );
	}

	result_type operator()( const Nil &nil ) const
	{
		PathMatcher result;
		return result;
	}

	result_type operator()( const BinaryOp &expr ) const
	{
		PathMatcher left = boost::apply_visitor( *this, expr.left.expr );
		PathMatcher right = boost::apply_visitor( *this, expr.right.expr );

		switch( expr.op )
		{
			case Or :
			{
				PathMatcher result = PathMatcher( left );
				result.addPaths( right );
				return result;
			}
			case And :
			{
				return left.intersection( right );
			}
			case AndNot :
			{
				PathMatcher result = PathMatcher( left );
				result.removePaths( right );
				return result;
			}
			default:
				return PathMatcher();
		}
	}

	const ScenePlug *m_scene;

};

// Hashing the AST
// ---------------
struct AstHasher
{
	typedef void result_type;

	AstHasher( const ScenePlug *scene, IECore::MurmurHash &h ) : m_scene( scene ), m_hash( h )
	{
	}

	void operator()( const ObjectName &n )
	{
		m_hash.append( n.name );
	}

	void operator()( const SetName &n )
	{
		if( !m_scene )
		{
			throw IECore::Exception( "SetAlgo: Invalid scene given. Can not hash set expression." );
		}

		if( !StringAlgo::hasWildcards( n.name ) )
		{
			m_hash.append( m_scene->setHash( n.name ) );
			return;
		}

		IECore::ConstInternedStringVectorDataPtr setNamesData = m_scene->setNamesPlug()->getValue();
		const std::vector<IECore::InternedString> &setNames = setNamesData->readable();
		if( setNames.empty() )
		{
			return;
		}

		ScenePlug::SetScope setScope( Context::current() );
		for( const IECore::InternedString &setName : setNames )
		{
			if( !StringAlgo::match( setName.string(), n.name ) )
			{
				continue;
			}

			setScope.setSetName( setName );
			m_hash.append( m_scene->setPlug()->hash() );
		}
	}

	void operator()( const ExpressionAst &ast )
	{
		boost::apply_visitor( *this, ast.expr );
	}

	void operator()( const BinaryOp &expr )
	{
		m_hash.append( expr.op );
		boost::apply_visitor( *this, expr.left.expr );
		boost::apply_visitor( *this, expr.right.expr );
	}

	void operator()( const Nil &nil )
	{
	}

	const ScenePlug* m_scene;
	IECore::MurmurHash &m_hash;

};

template <typename Iterator>
struct ExpressionGrammar : qi::grammar<Iterator, ExpressionAst(), ascii::space_type>
{
	ExpressionGrammar() : ExpressionGrammar::base_type( expression )
	{
		using qi::_val;
		using qi::_1;
		using qi::char_;
		using qi::lit;

		/* Grammar Specification

			 expression ->   andExpr  ( '|' andExpr | andExpr  )
			 andExpr    ->   andNotExpr '&' andNotExpr
			 andNotExpr ->   element    '-' element
			 element    ->   set | object | '(' expression ')'

			 This gives us implicit operator precedence in this order: -, &, |
			 It also supports space separated lists (implicit OR).
			 Note that sets can not have a name that starts with '/'.
		 */

		// grammar                                                     bindings
		// -----------------------------------------------------------------------
		expression =
			orExpression                                               [_val  = _1];

		orExpression =
			andExpression                                              [_val  = _1]
			>> *(     ( '|' >> andExpression                           [createBinaryOp( _val, Or, _1 )] )
			    |     ( andExpression                                  [createBinaryOp( _val, Or, _1 )] )
			    );

		andExpression =
			andNotExpression                                           [_val  = _1]
			>> *(     ( '&' >> andNotExpression                        [createBinaryOp( _val, And, _1 )] )
			    );

		andNotExpression =
			element                                                    [_val  = _1]
			>> *(     ( '-' >> element                                 [createBinaryOp( _val, AndNot, _1 )] )
			    );

		element =
			  objectName                                               [_val  = _1]
			| setName                                                  [_val  = _1]
			| lit('(') >> expression                                   [_val  = _1] >> lit(')');


		setName %= setNameToken;
		setNameToken %= char_( "a-zA-Z_*?[\\" ) >> *char_( "a-zA-Z_0-9:.*?[]!\\" );

		objectName %= objectNameToken;
		objectNameToken %= char_( "/" ) >> *char_( "a-zA-Z_0-9/:." );


		// these have no effect unless BOOST_SPIRIT_DEBUG is defined
		BOOST_SPIRIT_DEBUG_NODE(expression);
		BOOST_SPIRIT_DEBUG_NODE(andNotExpression);
		BOOST_SPIRIT_DEBUG_NODE(andExpression);
		BOOST_SPIRIT_DEBUG_NODE(orExpression);
		BOOST_SPIRIT_DEBUG_NODE(setName);
		BOOST_SPIRIT_DEBUG_NODE(objectName);
	}

	qi::rule<Iterator, SetName()> setName;
	qi::rule<Iterator, ObjectName()> objectName;
	qi::rule<Iterator, std::string()> setNameToken, objectNameToken;
	qi::rule<Iterator, ExpressionAst(), ascii::space_type> expression, andNotExpression, andExpression, orExpression, element;
};

void expressionToAST( const std::string &setExpression, ExpressionAst &ast)
{
	if( setExpression == "" )
	{
		return;
	}

	typedef std::string::const_iterator iterator_type;
	typedef ExpressionGrammar<iterator_type> ExpressionGrammar;

	ExpressionGrammar grammar;

	std::string::const_iterator iter = setExpression.begin();
	std::string::const_iterator end = setExpression.end();

	bool r = phrase_parse( iter, end, grammar, ascii::space, ast );

	if (r && iter == end)
	{
		#ifdef BOOST_SPIRIT_DEBUG
		std::cout << "-------------------------\n";
		std::cout << "Parsing of '" << setExpression <<"' succeeded.\n";
		std::cout << "Resulting AST:\n";
		AstPrinter printer;
		printer(ast);
		std::cout << "\n-------------------------\n";
		#endif
	}
	else
	{
		int offset = iter - setExpression.begin();
		std::string errorIndication( offset, ' ' );
		int indicationSize = setExpression.end() - iter;
		if( indicationSize <= 2 )
		{
			errorIndication += std::string( indicationSize, '|');
		}
		else
		{
			errorIndication += '|' + std::string( indicationSize - 2, '-') + '|';
		}

		throw IECore::Exception( boost::str( boost::format( "Syntax error in indicated part of SetExpression.\n%s\n%i\n." ) % setExpression % errorIndication ) ) ;
	}
}

} // namespace

BOOST_FUSION_ADAPT_STRUCT(
	ObjectName,
	(std::string, name)
)

BOOST_FUSION_ADAPT_STRUCT(
	SetName,
	(std::string, name)
)

namespace GafferScene
{

namespace SetAlgo
{

PathMatcher evaluateSetExpression( const std::string &setExpression, const ScenePlug *scene )
{
	ExpressionAst ast;
	expressionToAST( setExpression, ast );

	AstEvaluator eval( scene );
	return eval( ast );
}

void setExpressionHash( const std::string &setExpression, const ScenePlug* scene, IECore::MurmurHash &h )
{
	ExpressionAst ast;
	expressionToAST( setExpression, ast );

	AstHasher hasher = AstHasher( scene, h );
	hasher(ast);
}

IECore::MurmurHash setExpressionHash( const std::string &setExpression, const ScenePlug* scene)
{
	IECore::MurmurHash h = IECore::MurmurHash();
	setExpressionHash( setExpression, scene, h );
	return h;
}

bool affectsSetExpression( const Plug *scenePlugChild )
{
	const ScenePlug *parent = scenePlugChild->parent<ScenePlug>();

	if( parent->setPlug() == scenePlugChild )
	{
		return true;
	}

	return false;
}

} // namespace SetAlgo

} // namespace Gaffer
