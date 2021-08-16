##########################################################################
#
#  Copyright (c) 2020, John Haddon. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#      * Redistributions of source code must retain the above
#        copyright notice, this list of conditions and the following
#        disclaimer.
#
#      * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided with
#        the distribution.
#
#      * Neither the name of John Haddon nor the names of
#        any other contributors to this software may be used to endorse or
#        promote products derived from this software without specific prior
#        written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

import re

import GafferUI

class _Highlighter( GafferUI.CodeWidget.Highlighter ) :

	__keywords = [
		"closure", "color", "emit", "float",
		"illuminance", "illuminate", "int", "matrix", "normal",
		"output", "point", "public", "string", "struct", "vector",
		"void",
	]

	__controlFlow = [
		"break", "continue", "do", "else", "for", "if", "return", "while",
	]

	__operators = [
		"*", "/", "%", "+", "-", "<<", ">>", "<", "<=", ">", ">=",
		"==", "!=", "&", "^", "|", "&&", "||",
		"-", "~", "!",
		"++", "--",
		"=", "*=", "/=", "+=", "-=", "&=", "|=", "^=", "<<=", ">>=",
	]

	__operatorWords = [ "and", "or", "not" ]

	__reservedWords = [
		"bool", "case", "catch", "char", "class", "const", "delete", "default",
		"double", "enum", "extern", "false", "friend", "goto", "inline", "long",
		"new", "operator", "private", "protected", "short", "signed", "sizeof",
		"static", "switch", "template", "this", "throw", "true", "try", "typedef",
		"uniform", "union", "unsigned", "varying", "virtual", "volatile",
	]

	__preprocessor = [
		"#define", "#undef", "#if", "#ifdef", "#ifndef", "#elif", "#else",
		"#endif", "#include", "#pragma",
	]

	__preprocessorVariables = [
		"OSL_VERSION_MAJOR", "OSL_VERSION_MINOR", "OSL_VERSION_PATCH", "OSL_VERSION",
	]

	__constants = [
		"M_PI", "M_PI_2", "M_PI_4", "M_2_PI", "M_2PI", "M_4PI", "M_2_SQRTPI", "M_E",
		"M_LN2", "M_LN10", "M_LOG2E", "M_LOG10E", "M_SQRT2", "M_SQRT1_2",
	]

	__globals = [
		"P", "I", "N", "Ng", "dPdu", "dPdv", "Ps", "u", "v", "time", "dtime", "dPdtime", "Ci",
	]

	__functions = [
		"radians", "degrees", "cos", "sin", "tan", "sincos", "acos", "asin",
		"atan", "atan2", "cosh", "sinh", "tanh", "pow", "exp", "exp2", "expm1",
		"log", "log2", "log10", "log", "logb", "sqrt", "inversesqrt", "hypot",
		"abs", "fabs", "sign", "floor", "ceil", "round", "trunc", "fmod", "mod",
		"min", "max", "clamp", "mix", "isnan", "isinf", "isfinite", "select",
		"erf", "erfc", "dot", "cross", "length", "distance", "normalize",
		"faceforward", "reflect", "refract", "fresnel", "rotate", "transform",
		"transformu", "luminance", "blackbody", "wavelength_color", "transformc",
		"getmatrix", "determinant", "transpose", "step", "linearstep", "smoothstep",
		"smooth_linearstep", "noise", "pnoise", "snoise", "cellnoise", "hashnoise",
		"hash", "spline", "splineinverse", "Dx", "Dy", "Dz", "filterwidth", "area",
		"calculatenormal", "aastep", "diplace", "bump", "printf", "format", "error",
		"warning", "fprintf", "concat", "strlen", "startswith", "endswith", "stoi",
		"stof", "split", "substr", "getchar", "regex_search", "regex_match",
		"texture", "texture3d", "environment", "gettextureinfo", "pointcloud_search",
		"pointcloud_get", "pointcloud_write", "diffuse", "phong", "oren_nayar",
		"ward", "microfacet", "reflection", "refraction", "transparent", "translucent",
		"isotropic", "henyey_greenstein", "absorption", "emission", "background",
		"holdout", "debug", "getattribute", "setmessage", "getmessage", "surfacearea",
		"raytype", "backfacing", "isconnected", "isconstant", "dict_find", "dict_next",
		"dict_value", "trace", "arraylength", "exit",
	]

	# Sorting places longer strings like `++` before shorter like `+``. This is needed because
	# regex `|` takes the first match it finds, not looking for longer alternatives.

	__keywordsRE = re.compile( "|".join( r"\b{}\b".format( k ) for k in reversed( sorted( __keywords ) ) ) )
	__controlFlowRE = re.compile( "|".join( r"\b{}\b".format( k ) for k in reversed( sorted( __controlFlow ) ) ) )
	__preprocessorRE = re.compile( "|".join( r"^\s*{}\b".format( k ) for k in reversed( sorted( __preprocessor ) ) ) )
	__preprocessorVariablesRE = re.compile( "|".join( r"\b{}\b".format( k ) for k in reversed( sorted( __preprocessorVariables ) ) ) )
	__operatorsRE = re.compile( "|".join( re.escape( k ) for k in reversed( sorted( __operators ) ) ) )
	__operatorWordsRE = re.compile( "|".join( r"\b{}\b".format( k ) for k in reversed( sorted( __operatorWords ) ) ) )
	__reservedWordsRE = re.compile( "|".join( r"\b{}\b".format( k ) for k in reversed( sorted( __reservedWords ) ) ) )
	__stringsRE = re.compile( r'"[^"]*"' )

	__hex = r"[+-]?0x[a-fA-F0-9]+"
	__float =r"[+-]?(\d*\.\d+|\d+\.?)([Ee][+-]?[0-9]+)?"

	__notPrecededByAlpha = r"(?<![a-zA-Z])"
	__notFollowedByAlpha = r"(?![a-zA-Z])"

	__numbersRE = re.compile(
		r"{notPrecededByAlpha}({float}|{hex}){notFollowedByAlpha}".format(
			notPrecededByAlpha = __notPrecededByAlpha,
			float = __float,
			hex = __hex,
			notFollowedByAlpha = __notFollowedByAlpha
		)
	)

	__singleCommentRE = re.compile( r"//.*$|/\*.*\*/" )
	__multiCommentStartRE = re.compile( r"/\*((?!\*/).)*$" )
	__multiCommentEndRE = re.compile( r"^.*\*/")

	def highlights( self, line, previousHighlightType ) :

		result = []
		stringsAndComments = set()

		m = self.__multiCommentStartRE.search( line )
		if m is not None :
			result.append( self.Highlight( m.start(), None, self.Type.Comment ) )
			return result

		if previousHighlightType == self.Type.Comment :
			m = self.__multiCommentEndRE.match( line )
			if m is None :
				result.append( self.Highlight( 0, None, self.Type.Comment ) )
				return result
			else :
				result.append( self.Highlight( m.start(), m.end(), self.Type.Comment ) )
				stringsAndComments.update( range( m.start(), m.end() ) )

		for m in self.__stringsRE.finditer( line ) :
			result.append( self.Highlight( m.start(), m.end(), self.Type.DoubleQuotedString ) )
			stringsAndComments.update( range( m.start(), m.end() ) )

		m = self.__singleCommentRE.search( line )
		if m is not None and m.start() not in stringsAndComments :
			result.append( self.Highlight( m.start(), m.end(), self.Type.Comment ) )
			stringsAndComments.update( range( m.start(), m.end() ) )

		for regex, highlightType in (
			( self.__keywordsRE, self.Type.Keyword ),
			( self.__controlFlowRE, self.Type.ControlFlow ),
			( self.__preprocessorRE, self.Type.Preprocessor ),
			( self.__preprocessorVariablesRE, self.Type.Preprocessor ),
			( self.__operatorsRE, self.Type.Operator ),
			( self.__operatorWordsRE, self.Type.Operator ),
			( self.__reservedWordsRE, self.Type.ReservedWord ),
			( self.__numbersRE, self.Type.Number ),
		) :
			for m in regex.finditer( line ) :
				if m.start() not in stringsAndComments :
					result.append( self.Highlight( m.start(), m.end(), highlightType ) )

		return result
