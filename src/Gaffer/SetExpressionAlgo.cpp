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

#include "Gaffer/SetExpressionAlgo.h"

#include "IECore/MessageHandler.h"
#include "IECore/StringAlgo.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/fusion/include/adapt_struct.hpp"
#include "boost/phoenix/operator.hpp"
#include "boost/spirit/include/classic_core.hpp"
#include "boost/spirit/include/qi.hpp"
#include "boost/spirit/repository/include/qi_distinct.hpp"
#include "boost/variant/apply_visitor.hpp"
#include "boost/variant/recursive_variant.hpp"

#include "fmt/format.h"

using namespace IECore;
using namespace Gaffer;

namespace qi = boost::spirit::qi;
namespace ascii = boost::spirit::ascii;

namespace
{

struct BinaryOp;
struct Nil {};

// Determine which Ops are supported in SetExpressions
// and provide a way to print them for debugging.
enum Op { Intersection, Union, Difference, In, Containing };

std::ostream & operator<<( std::ostream &out, const Op &op )
{
	switch( op )
	{
		case Union :
			out << "|"; break;
		case Intersection :
			out << "&"; break;
		case Difference :
			out << "-"; break;
		case In :
			out << "in"; break;
		case Containing :
			out << "containing"; break;
	}
	return out;
}

using ExpressionAst = boost::variant<
	Nil,
	std::string, // identifier
	boost::recursive_wrapper<BinaryOp>
>;

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

	using result_type = ExpressionAst &;

	ExpressionAst & operator()( ExpressionAst &lhs, Op op, ExpressionAst &rhs ) const
	{
		lhs = BinaryOp( lhs, op, rhs );
		return lhs;
	}

};

// Function that we can use as a semantic action in the parser, inserting
// a BinaryOp into the current ExpressionAst.
boost::phoenix::function<CreateBinaryOpImplementation> createBinaryOp;

// Visiting the AST
// ----------------
// For a simple AST with only one operation (Intersection) on two sets (A and B)
// the output will look like this: op:&(A, B).
// If one of the operands is an operation itself: op:&(A, op:|(B, C))
struct AstPrinter
{
	using result_type = void;

	AstPrinter()
		: stream( std::cout ) {}

	AstPrinter( std::ostream &stream )
		: stream( stream ) {}

	void operator()( const std::string &n ) const
	{
		stream << n;
	}

	void operator()( const Nil &nil ) const
	{
	}

	void operator()( const BinaryOp &expr ) const
	{
		stream << "op:" << expr.op << "(";
		boost::apply_visitor( *this, expr.left );
		stream << ", ";
		boost::apply_visitor( *this, expr.right );
		stream << ')';
	}

	std::ostream &stream;
};

#ifdef BOOST_SPIRIT_DEBUG
// support for printing ExpressionsAst's for debugging through BOOST_SPIRIT_DEBUG
std::ostream& operator<<( std::ostream& stream, const ExpressionAst& expr )
{
	boost::apply_visitor( AstPrinter( stream ), expr );
	return stream;
}
#endif

// Evaluating the AST
// ------------------
struct AstEvaluator
{
	using result_type = PathMatcher;

	AstEvaluator( const SetExpressionAlgo::SetProvider &setProvider )
		: m_setProvider( setProvider )
	{
	}

	result_type operator()( const std::string &identifier ) const
	{
		if( identifier[0] == '/' )
		{
			// Object name
			PathMatcher result;
			if( StringAlgo::hasWildcards( identifier ) )
			{
				throw IECore::Exception( fmt::format( "Object name \"{}\" contains wildcards", identifier ) );
			}
			result.addPath( identifier );
			return result;
		}
		else
		{
			// Set name

			if( !StringAlgo::hasWildcards( identifier ) )
			{
				return m_setProvider.paths( identifier );
			}

			result_type result;

			const std::vector<IECore::InternedString> &setNames = m_setProvider.setNames()->readable();
			if( setNames.empty() )
			{
				return result;
			}

			for( const IECore::InternedString &setName : setNames )
			{
				if( StringAlgo::match( setName.string(), identifier ) )
				{
					result.addPaths( m_setProvider.paths( setName.string() ) );
				}
			}
			return result;
		}
	}

	result_type operator()( const Nil &nil ) const
	{
		PathMatcher result;
		return result;
	}

	result_type operator()( const BinaryOp &expr ) const
	{
		PathMatcher left = boost::apply_visitor( *this, expr.left );
		PathMatcher right = boost::apply_visitor( *this, expr.right );

		switch( expr.op )
		{
			case Union :
			{
				PathMatcher result = PathMatcher( left );
				result.addPaths( right );
				return result;
			}
			case Intersection :
			{
				return left.intersection( right );
			}
			case Difference :
			{
				PathMatcher result = PathMatcher( left );
				result.removePaths( right );
				return result;
			}
			case In :
			{
				PathMatcher result;
				for( PathMatcher::Iterator it = right.begin(), eIt = right.end(); it != eIt; ++it )
				{
					result.addPaths( left.subTree( *it ), *it );
					it.prune();
				}
				return result;
			}
			case Containing :
			{
				PathMatcher result;
				for( PathMatcher::Iterator it = left.begin(), eIt = left.end(); it != eIt; ++it )
				{
					if( right.match( *it ) & ( PathMatcher::ExactMatch | PathMatcher::DescendantMatch ) )
					{
						result.addPath( *it );
					}
				}
				return result;
			}
			default :
				return PathMatcher();
		}
	}

	const SetExpressionAlgo::SetProvider &m_setProvider;

};

// Hashing the AST
// ---------------
struct AstHasher
{
	using result_type = void;

	AstHasher( const SetExpressionAlgo::SetProvider &setProvider, IECore::MurmurHash &h )
		: m_setProvider( setProvider ), m_hash( h )
	{
	}

	void operator()( const std::string &identifier )
	{
		if( identifier[0] == '/' )
		{
			// Object name
			m_hash.append( identifier );
		}
		else
		{
			if( !StringAlgo::hasWildcards( identifier ) )
			{
				m_setProvider.hash( identifier, m_hash );
				return;
			}

			const std::vector<IECore::InternedString> &setNames = m_setProvider.setNames()->readable();
			if( setNames.empty() )
			{
				return;
			}

			for( const IECore::InternedString &setName : setNames )
			{
				if( StringAlgo::match( setName.string(), identifier ) )
				{
					m_setProvider.hash( setName.string(), m_hash );
				}
			}
		}
	}

	void operator()( const BinaryOp &expr )
	{
		m_hash.append( expr.op );
		boost::apply_visitor( *this, expr.left );
		boost::apply_visitor( *this, expr.right );
	}

	void operator()( const Nil &nil )
	{
	}

	const SetExpressionAlgo::SetProvider &m_setProvider;
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
		using boost::spirit::repository::distinct;

		/* Grammar Specification

			expression    ->   intersection ( '|' intersection | intersection )
			intersection  ->   difference '&' difference
			difference    ->   element '-' element
			element       ->   identifier | '(' expression ')'

			This gives us implicit operator precedence in this order: -, &, |
			It also supports space separated lists (implicit union).
			Note that sets can not have a name that starts with '/'.

		*/

		// grammar                                                     bindings
		// -----------------------------------------------------------------------
		expression =
			inExpression                                               [_val  = _1];

		inExpression =
			containingExpression                                       [_val  = _1]
			>> *(     ( inKeyword >> containingExpression              [createBinaryOp( _val, In, _1 )] )
				);

		containingExpression =
			unionExpression                                            [_val  = _1]
			>> *(     ( containingKeyword >> unionExpression           [createBinaryOp( _val, Containing, _1 )] )
				);

		unionExpression =
			intersectionExpression                                     [_val  = _1]
			>> *(     ( '|' >> intersectionExpression                  [createBinaryOp( _val, Union, _1 )] )
				|     ( intersectionExpression                         [createBinaryOp( _val, Union, _1 )] )
				);

		intersectionExpression =
			differenceExpression                                       [_val  = _1]
			>> *(     ( '&' >> differenceExpression                    [createBinaryOp( _val, Intersection, _1 )] )
				);

		differenceExpression =
			element                                                    [_val  = _1]
			>> *(     ( '-' >> element                                 [createBinaryOp( _val, Difference, _1 )] )
				);

		element =
			identifier                                                 [_val  = _1]
			| lit('(') >> expression                                   [_val  = _1] >> lit(')');

		const char *identifierCharacters = "a-zA-Z_0-9/:.*?[]!\\";
		identifier %= !reservedWords >> +char_( identifierCharacters );

		inKeyword = distinct( char_( identifierCharacters ) )["in"];
		containingKeyword = distinct( char_( identifierCharacters ) )["containing"];
		reservedWords = inKeyword | containingKeyword;

		// these have no effect unless BOOST_SPIRIT_DEBUG is defined
		BOOST_SPIRIT_DEBUG_NODE(expression);
		BOOST_SPIRIT_DEBUG_NODE(inExpression);
		BOOST_SPIRIT_DEBUG_NODE(containingExpression);
		BOOST_SPIRIT_DEBUG_NODE(differenceExpression);
		BOOST_SPIRIT_DEBUG_NODE(intersectionExpression);
		BOOST_SPIRIT_DEBUG_NODE(unionExpression);
		BOOST_SPIRIT_DEBUG_NODE(identifier);
	}

	qi::rule<Iterator> inKeyword, containingKeyword, reservedWords;
	qi::rule<Iterator, std::string()> identifier;
	qi::rule<Iterator, ExpressionAst(), ascii::space_type> expression, inExpression, containingExpression, differenceExpression, intersectionExpression, unionExpression, element;
};

void expressionToAST( const std::string &setExpression, ExpressionAst &ast)
{
	if( std::all_of( setExpression.begin(), setExpression.end(), isspace ) )
	{
		return;
	}

	using iterator_type = std::string::const_iterator;
	using ExpressionGrammar = ExpressionGrammar<iterator_type>;

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
		std::cout << ast;
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

		throw IECore::Exception( fmt::format( "Syntax error in indicated part of SetExpression.\n{}\n{}\n.", setExpression, errorIndication ) );
	}
}

} // namespace

namespace Gaffer
{

namespace SetExpressionAlgo
{

PathMatcher evaluateSetExpression( const std::string &setExpression, const SetProvider &setProvider )
{
	ExpressionAst ast;
	expressionToAST( setExpression, ast );
	return boost::apply_visitor( AstEvaluator( setProvider ), ast );
}

void setExpressionHash( const std::string &setExpression, const SetProvider &setProvider, IECore::MurmurHash &h )
{
	ExpressionAst ast;
	expressionToAST( setExpression, ast );
	AstHasher hasher = AstHasher( setProvider, h );
	boost::apply_visitor( hasher, ast );
}

IECore::MurmurHash setExpressionHash( const std::string &setExpression, const SetProvider &setProvider )
{
	IECore::MurmurHash h = IECore::MurmurHash();
	setExpressionHash( setExpression, setProvider, h );
	return h;
}

} // namespace SetExpressionAlgo

} // namespace Gaffer
