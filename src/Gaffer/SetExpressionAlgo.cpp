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
#include "boost/container/flat_set.hpp"
#include "boost/fusion/include/adapt_struct.hpp"
#include "boost/phoenix/operator.hpp"
#include "boost/spirit/include/classic_core.hpp"
#include "boost/spirit/include/qi.hpp"
#include "boost/spirit/repository/include/qi_distinct.hpp"
#include "boost/variant/apply_visitor.hpp"
#include "boost/variant/recursive_variant.hpp"

#include "fmt/format.h"

#include <optional>
#include <set>

using namespace IECore;
using namespace Gaffer;

namespace qi = boost::spirit::qi;
namespace ascii = boost::spirit::ascii;

namespace
{

struct BinaryOp;
struct Nil
{
	bool operator==( const Nil & ) const { return true; }
	bool operator<( const Nil & ) const { return false; }
};

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

	bool operator==( const BinaryOp &other ) const
	{
		if( ( op == Intersection || op == Union ) && other.op == op )
		{
			return ( left == other.left && right == other.right ) || ( left == other.right && right == other.left );
		}

		return left == other.left &&
				op == other.op &&
				right == other.right;
	}
	bool operator<( const BinaryOp &other ) const
	{
		if( left < other.left ) return true;
		if( other.left < left ) return false;

		if( op < other.op ) return true;
		if( other.op < op ) return false;

		return right < other.right;
	}
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

// Serialising the AST
// -------------------
struct AstSerialiser
{
	using result_type = std::string;

	std::string operator()( const Nil & ) const
	{
		return "";
	}

	std::string operator()( const std::string &value ) const
	{
		return value;
	}

	std::string operator()( const BinaryOp &expr ) const
	{
		return toString( expr, std::nullopt, false );
	}

	std::string toString( const ExpressionAst &ast, std::optional<Op> parentOp, bool onRightSide ) const
	{
		if( const auto s = boost::get<std::string>( &ast ) )
		{
			return *s;
		}

		if( const auto bin = boost::get<BinaryOp>( &ast ) )
		{
			auto info = opInfo( bin->op );

			std::string left  = toString( bin->left,  bin->op, /* onRightSide = */ false );
			std::string right = toString( bin->right, bin->op, /* onRightSide = */ true );

			bool needParens = false;
			if( parentOp )
			{
				auto parentInfo = opInfo( *parentOp );

				if( info.precedence < parentInfo.precedence )
				{
					needParens = true;
				}
				else if( onRightSide && *parentOp == Difference && bin->op == Difference )
				{
					// We require parenthesis here to differentiate "A - B - C" from "A - (B - C)".
					needParens = true;
				}

				if( *parentOp == In || *parentOp == Containing )
				{
					// For clarity, always wrap BinaryOp children of these ops in parenthesis
					// so the serialised result is "(A B) in (C D)" rather than "A B in C D",
					// which could read as "A (B in C) D" to the user.
					if( boost::get<BinaryOp>( &ast ) )
					{
						needParens = true;
					}
				}
			}

			return fmt::format( needParens ? "({}{}{})" : "{}{}{}", left, info.repr, right );
		}

		return "";
	}

	private :

		struct OpInfo
		{
			int precedence;
			const char *repr;
		};

		OpInfo opInfo( Op op ) const
		{
			switch( op )
			{
				case Difference :
					return { 5, " - " };
				case Intersection :
					return { 4, " & " };
				case Union :
					return { 3, " " };
				case Containing :
					return { 2, " containing " };
				case In :
					return { 1, " in " };
			}
			return { 0, "" };
		}
};

void collectOperands( const ExpressionAst &ast, Op targetOp, std::vector<ExpressionAst> &result )
{
	if( const auto *bin = boost::get<BinaryOp>( &ast ) )
	{
		if( bin->op == targetOp )
		{
			collectOperands( bin->left, targetOp, result );
			collectOperands( bin->right, targetOp, result );
			return;
		}
	}

	if( !boost::get<Nil>( &ast ) )
	{
		result.push_back( ast );
	}
}

ExpressionAst buildTree( Op op, const std::vector<ExpressionAst> &nodes )
{
	if( nodes.empty() )
	{
		return Nil{};
	}

	ExpressionAst result = nodes[0];
	for( size_t i = 1; i < nodes.size(); ++i )
	{
		result = BinaryOp( result, op, nodes[i] );
	}

	return result;
}

// Simplifying the AST
// -------------------
struct SimplifyVisitor
{
	using result_type = ExpressionAst;

	ExpressionAst operator()(const Nil &n) const
	{
		return n;
	}

	ExpressionAst operator()(const std::string &s ) const
	{
		return s;
	}

	ExpressionAst operator()(const BinaryOp &expr ) const
	{
		ExpressionAst left = boost::apply_visitor( *this, expr.left );
		ExpressionAst right = boost::apply_visitor( *this, expr.right );

		if( expr.op == Difference )
		{
			if( isSubsetOf( left, right ) )
			{
				// A - A -> Nil
				// (A [&,in,containing] B) - A -> Nil
				return Nil{};
			}

			if( auto innerRight = boost::get<BinaryOp>( &right ) )
			{
				if( innerRight->op == Union )
				{
					// A - (A | B) -> Nil
					std::vector<ExpressionAst> ops;
					collectOperands( right, Union, ops );

					if( std::any_of( ops.begin(), ops.end(), [&]( const ExpressionAst &r ) { return isSubsetOf( left, r ); } ) )
					{
						return Nil();
					}
				}
			}

			if( auto inner = boost::get<BinaryOp>( &left ) )
			{
				if( inner->op == Union )
				{
					// (A | B | C) - (B | C) -> A - (B | C)
					std::vector<ExpressionAst> ops;
					collectOperands( left, Union, ops );

					std::vector<ExpressionAst> rightOps;
					collectOperands( right, Union, rightOps );

					ops.erase(
						std::remove_if(
							ops.begin(), ops.end(),
							[&]( const ExpressionAst &o ) {
								return std::any_of(
									rightOps.begin(), rightOps.end(),
									[&]( const ExpressionAst &r ) {
										return isSubsetOf( o, r );
									}
								);
							}
						),
						ops.end()
					);

					if( ops.empty() )
					{
						return Nil{};
					}

					return BinaryOp( buildTree( Union, uniqueOperands( ops ) ), Difference, right );
				}
				else if( inner->op == Difference )
				{
					// (A - B) - C -> A - (B | C)
					if( isSubsetOf( inner->right, right ) )
					{
						// inner->right is subset of right and can be entirely replaced by it.
						return BinaryOp( inner->left, Difference, right );
					}

					std::vector<ExpressionAst> ops;
					collectOperands( inner->right, Union, ops );
					collectOperands( right, Union, ops );

					return BinaryOp( inner->left, Difference, buildTree( Union, uniqueOperands( ops ) ) );
				}
			}
		}

		if( left == right )
		{
			// A [|,&,in,containing] A -> A
			return left;
		}

		if( expr.op == Union || expr.op == Intersection )
		{
			// A | B | B | A -> A | B
			// A & B [&|] B & A -> A & B
			std::vector<ExpressionAst> ops;
			collectOperands( left, expr.op, ops );
			collectOperands( right, expr.op, ops );
			ops = uniqueOperands( ops );

			if( expr.op == Union )
			{
				removeSubsets( ops );
			}
			else if( expr.op == Intersection )
			{
				removeSupersets( ops );
			}

			return buildTree( expr.op, ops );
		}

		return BinaryOp( left, expr.op, right );
	}

	private :

		std::vector<ExpressionAst> uniqueOperands( std::vector<ExpressionAst> &operands ) const
		{
			std::set<ExpressionAst> seen;
			std::vector<ExpressionAst> result;
			for( auto &o : operands )
			{
				if( seen.insert( o ).second )
				{
					result.push_back( o );
				}
			}
			return result;
		}

		bool isSubsetOf( const ExpressionAst &a, const ExpressionAst &b ) const
		{
			if( a == b )
			{
				return true;
			}

			if( const auto *binB = boost::get<BinaryOp>( &b ) )
			{
				if( binB->op == Union )
				{
					return isSubsetOf( a, binB->left ) || isSubsetOf( a, binB->right );
				}
				if( binB->op == Intersection )
				{
					return isSubsetOf( a, binB->left ) && isSubsetOf( a, binB->right );
				}
			}

			if( const auto *bin = boost::get<BinaryOp>( &a ) )
			{
				switch( bin->op )
				{
					case Intersection :
						return isSubsetOf( bin->left, b ) || isSubsetOf( bin->right, b );
					case Union :
						return isSubsetOf( bin->left, b ) && isSubsetOf( bin->right, b );
					case In :
					case Containing :
					case Difference :
						return isSubsetOf( bin->left, b );
				}
			}

			return false;
		}

		template<typename Predicate>
		void removeIfAnyMatch( std::vector<ExpressionAst> &items, Predicate pred ) const
		{
			items.erase(
				std::remove_if(
					items.begin(), items.end(),
					[&]( const ExpressionAst &a ) {
						return std::any_of(
							items.begin(), items.end(),
							[&]( const ExpressionAst &b ) {
								return &a != &b && pred( a, b );
							}
						);
					}
				),
				items.end()
			);
		}

		void removeSubsets( std::vector<ExpressionAst> &items ) const
		{
			removeIfAnyMatch(
				items,
				[&]( const ExpressionAst &a, const ExpressionAst &b ) {
					return isSubsetOf( a, b );
				}
			);
		}

		void removeSupersets( std::vector<ExpressionAst> &items ) const
		{
			removeIfAnyMatch(
				items,
				[&]( const ExpressionAst &a, const ExpressionAst &b ) {
					return isSubsetOf( b, a );
				}
			);
		}
};

// Removes the ops in `removalsAst` from the visited AST.
/// \todo This could be exposed as
/// SetExpressionAlgo::remove( const std::string &setExpression, const std::string &removals )`
/// to provide a more robust way of performing operations such as drag-and-drop removal of
/// set names in SetFilterUI or _InspectorColumn. When doing this we'd likely want a mode
/// that does not remove from the RHS of Difference ops, as this currently does.
struct RemovalVisitor
{
	using result_type = ExpressionAst;

	RemovalVisitor( const ExpressionAst &removalsAst )
	{
		std::vector<ExpressionAst> ops;
		collectOperands( removalsAst, Union, ops );

		for( auto &o : ops )
		{
			m_removals.insert( o );
		}
	}

	ExpressionAst operator()( const std::string &s ) const
	{
		return filter( s );
	}

	ExpressionAst operator()( const Nil & ) const
	{
		return Nil{};
	}

	ExpressionAst operator()( const BinaryOp &expr ) const
	{
		if( m_removals.count( expr ) )
		{
			return Nil();
		}

		ExpressionAst filteredLeft = filter( boost::apply_visitor( *this, expr.left ) );
		if( expr.op != Union && boost::get<Nil>( &filteredLeft ) )
		{
			// Omit the operation as the entire left side has been removed.
			return Nil{};
		}

		if( expr.op == Containing || expr.op == In )
		{
			// Removals only affect the left side of these operations.
			return BinaryOp( filteredLeft, expr.op, expr.right );
		}

		ExpressionAst filteredRight = filter( boost::apply_visitor( *this, expr.right ) );
		if( expr.op == Union && boost::get<Nil>( &filteredLeft ) )
		{
			// Union with no remaining left side, so return the right.
			return filteredRight;
		}

		if( boost::get<Nil>( &filteredRight ) )
		{
			if( expr.op == Intersection )
			{
				// Omit the operation as the entire right side has been removed.
				return Nil();
			}

			// Return the left side of the Union or Difference.
			return filteredLeft;
		}

		return BinaryOp( filteredLeft, expr.op, filteredRight );
	}

	private :

		ExpressionAst filter( const ExpressionAst &ast ) const
		{
			std::vector<ExpressionAst> result;
			std::vector<ExpressionAst> ops;
			collectOperands( ast, Union, ops );
			for( auto &o : ops )
			{
				if( !m_removals.count( o ) )
				{
					result.push_back( o );
				}
			}

			return buildTree( Union, result );
		}

		ExpressionAst filter( const std::string &s ) const
		{
			if( m_removals.count( s ) )
			{
				return Nil();
			}

			return s;
		}

		boost::container::flat_set<ExpressionAst> m_removals;

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

ExpressionAst simplifyExpression( ExpressionAst ast )
{
	while( true )
	{
		ExpressionAst simplified = boost::apply_visitor( SimplifyVisitor{}, ast );

		if( simplified == ast )
		{
			return simplified;
		}
		ast = simplified;
	}
}

ExpressionAst includeExpression( const ExpressionAst &ast, const ExpressionAst &inclusions )
{
	// We first apply the RemovalVisitor to remove any ops in inclusions from the input ast
	// before we merge `ast` with `inclusions` and simplify. This ensures the inclusions remain
	// on the right-hand side of the expression after simplification.
	// As the RemovalVisitor acts as a global removal operation on `ast`, it is able to remove
	// all ops in `ast` that are obviated by the ones in `inclusions`, rather than relying on
	// the local cancellation operations performed by `simplifyExpression()`.
	ExpressionAst simplifiedInclusions = simplifyExpression( inclusions );
	ExpressionAst filteredAst = boost::apply_visitor( RemovalVisitor( simplifiedInclusions ), simplifyExpression( ast ) );

	if( boost::get<Nil>( &filteredAst ) )
	{
		// `ast` has been completely replaced by `inclusions` so we can return it directly.
		return simplifiedInclusions;
	}

	return simplifyExpression( BinaryOp( filteredAst, Union, simplifiedInclusions ) );
}

ExpressionAst excludeExpression( const ExpressionAst &ast, const ExpressionAst &exclusions )
{
	// We first apply the RemovalVisitor to remove any ops in exclusions from the input ast
	// before we subtract `exclusions` from `ast` and simplify. This ensures the exclusions
	// remain on the right-hand side of the final expression after simplification.
	ExpressionAst simplifiedExclusions = simplifyExpression( exclusions );
	ExpressionAst filteredAst = boost::apply_visitor( RemovalVisitor( simplifiedExclusions ), simplifyExpression( ast ) );

	if( boost::get<Nil>( &filteredAst ) )
	{
		// Return Nil as it is invalid to subtract from an empty set expression.
		return Nil();
	}

	return simplifyExpression( BinaryOp( filteredAst, Difference, simplifiedExclusions ) );
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

std::string simplify( const std::string &setExpression )
{
	ExpressionAst ast;
	expressionToAST( setExpression, ast );

	return boost::apply_visitor( AstSerialiser{}, simplifyExpression( ast ) );
}

std::string include( const std::string &setExpression, const std::string &inclusions )
{
	if( inclusions == "" )
	{
		return setExpression;
	}

	ExpressionAst ast;
	ExpressionAst inclusionsAst;
	expressionToAST( setExpression, ast );
	expressionToAST( inclusions, inclusionsAst );

	return boost::apply_visitor( AstSerialiser{}, includeExpression( ast, inclusionsAst ) );
}

std::string exclude( const std::string &setExpression, const std::string &exclusions )
{
	if( exclusions == "" )
	{
		return setExpression;
	}

	ExpressionAst ast;
	ExpressionAst exclusionsAst;
	expressionToAST( setExpression, ast );
	expressionToAST( exclusions, exclusionsAst );

	return boost::apply_visitor( AstSerialiser{}, excludeExpression( ast, exclusionsAst ) );
}

} // namespace SetExpressionAlgo

} // namespace Gaffer
