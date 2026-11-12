import functools
import gettext
import locale
import os
import re
import unicodedata


# ---------------------------------------------------------------------------
# Determine effective language
# ---------------------------------------------------------------------------
# Priority: GAFFER_LANG env var > system locale > "en"

def _detectLanguage() :
	"""Detect language from environment or system locale."""
	lang = os.environ.get( "GAFFER_LANG" )
	if lang :
		return lang
	try :
		sysLocale = locale.getdefaultlocale()[0] or ""
		if "_" in sysLocale :
			return sysLocale.split( "_" )[0]
	except Exception :
		pass
	return "en"

_LANG = _detectLanguage()
os.environ["GAFFER_LANG"] = _LANG

# ---------------------------------------------------------------------------
# Load gettext catalogue
# ---------------------------------------------------------------------------

_LOCALE_DIR = os.path.join( os.path.dirname( __file__ ), "locale" )

def _ensureMo() :
	"""Compile .mo from .po if missing or outdated."""
	poFile = os.path.join( _LOCALE_DIR, _LANG, "LC_MESSAGES", "gaffer.po" )
	moFile = os.path.join( _LOCALE_DIR, _LANG, "LC_MESSAGES", "gaffer.mo" )
	if not os.path.isfile( poFile ) :
		return
	if os.path.isfile( moFile ) and os.path.getmtime( moFile ) >= os.path.getmtime( poFile ) :
		return
	try :
		import subprocess
		subprocess.run(
			[ "msgfmt", "-o", moFile, poFile ],
			check = True, capture_output = True
		)
	except Exception :
		try :
			import polib
			po = polib.pofile( poFile )
			po.save_as_mofile( moFile )
		except Exception :
			pass

if _LANG != "en" :
	_ensureMo()

_trans = gettext.translation(
	"gaffer",
	_LOCALE_DIR,
	languages = [ _LANG ],
	fallback = True,
)

# ---------------------------------------------------------------------------
# Core translation function
# ---------------------------------------------------------------------------

def _normalize( text ) :
	"""Collapse whitespace so triple-quoted source strings match
	single-line .po msgid entries."""
	return " ".join( text.split() )

def translate( text ) :
	"""Look up *text* in the gettext catalogue.

	Returns the translated string if found, otherwise the original text.
	This is the primary function used by consumer widgets (Menu, Window,
	Label, PlugLayout, etc.) to translate UI strings at display time.
	"""
	if not text :
		return text or ""
	if _LANG == "en" :
		return text
	normalized = _normalize( text )
	if not normalized :
		return text
	translated = _trans.gettext( normalized )
	if translated != normalized :
		return translated
	# Fallback: try original text in case .po uses the raw form
	return _trans.gettext( text )

# Keep `_` as an alias for translate, for use in format strings
# and dynamic messages that still need explicit wrapping.
_ = translate

def ngettext( singular, plural, n ) :
	"""Translate with plural support."""
	if _LANG == "en" :
		return singular if n == 1 else plural
	return _trans.ngettext( singular, plural, n )

def pgettext( context, text ) :
	"""Translate *text* with a disambiguating *context* (msgctxt).

	Uses the standard gettext convention of storing the lookup key
	as ``context + "\\x04" + text``.
	"""
	if _LANG == "en" :
		return text
	msgid = context + "\x04" + text
	translated = _trans.gettext( msgid )
	if translated == msgid :
		return text
	return translated

# ---------------------------------------------------------------------------
# IECoreGL rendering workaround
# ---------------------------------------------------------------------------

def stripAccents( text ) :
	"""Remove diacritical marks AND ñ/Ñ for IECoreGL rendering.

	IECoreGL::Font indexes glyphs via ``char c`` which iterates
	over raw UTF-8 bytes.  Multi-byte characters like ñ (0xC3 0xB1)
	produce two wrong glyphs instead of one correct one.  So we must
	replace ñ→n, Ñ→N in addition to stripping combining marks.
	"""
	text = text.replace( "\u00f1", "n" ).replace( "\u00d1", "N" )
	nfd = unicodedata.normalize( "NFD", text )
	return "".join( c for c in nfd if unicodedata.category( c ) != "Mn" )

# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def language() :
	"""Return the active language code."""
	return _LANG

def isEnabled() :
	"""Return True if translation is active (language is not English)."""
	return _LANG != "en"

# ---------------------------------------------------------------------------
# Node type label helper (for Graph Editor)
# ---------------------------------------------------------------------------

_camelCaseRe = re.compile( r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|(?<=[a-zA-Z])(?=[0-9])" )

def _camelToSpaced( name ) :
	"""Convert CamelCase to spaced form: ``SystemCommand`` → ``System Command``."""
	return _camelCaseRe.sub( " ", name )

_SHADER_DISPLAY_CORRECTIONS = [
	( "Hsv", "HSV" ), ( "Rgb", "RGB" ), ( "Xyz", "XYZ" ), ( "Bw", "BW" ),
	( " To ", " to " ), ( "Aov", "AOV" ), ( "Uvmap", "UV Map" ),
	( "Ies", "IES" ), ( "Bsdf", "BSDF" ), ( "Non Uniform", "Nonuniform" ),
	( "Uv ", "UV " ), ( "Osl", "OSL" ),
]

def getNodeLabel( typeName, node = None ) :
	"""Return the translated UI label for a node type name.

	*typeName* is the short C++ class name, e.g. ``"Rectangle"``
	or ``"SystemCommand"``.  The name is converted to spaced form
	(``"System Command"``) before lookup so that existing menu
	translations are reused.

	If *node* is provided and it is a Shader or Light node, the
	specific shader/light name is used instead of the generic type.
	"""
	shaderName = None
	if node is not None :
		try :
			import GafferScene
			isShaderOrLight = isinstance( node, ( GafferScene.Shader, GafferScene.Light ) )
		except Exception :
			isShaderOrLight = False

		if isShaderOrLight :
			try :
				import GafferOSL
				if isinstance( node, GafferOSL.OSLCode ) :
					isShaderOrLight = False
			except Exception :
				pass

		if isShaderOrLight :
			try :
				shaderName = node["name"].getValue() or None
			except Exception :
				pass

	return _getNodeLabelCached( typeName, shaderName )

@functools.lru_cache( maxsize = 512 )
def _getNodeLabelCached( typeName, shaderName ) :
	"""Cached inner implementation of getNodeLabel."""

	if shaderName is not None :
		if "/" in shaderName :
			shaderName = shaderName.rsplit( "/", 1 )[-1]

		parts = shaderName.split( "_" )
		spacedParts = [ _camelToSpaced( x ) for x in parts ]
		spacedParts = [
			p[0].upper() + p[1:] if p and p[0].islower() else p
			for p in spacedParts
		]
		spaced = " ".join( spacedParts )

		for orig, repl in _SHADER_DISPLAY_CORRECTIONS :
			spaced = spaced.replace( orig, repl )

		if _LANG == "en" :
			return spaced
		tr = translate( spaced )
		return tr if tr != spaced else spaced

	spaced = _camelToSpaced( typeName )
	if _LANG == "en" :
		return spaced
	return translate( spaced )

# ---------------------------------------------------------------------------
# Nodule label translation for Graph Editor
# ---------------------------------------------------------------------------

def translateNoduleLabel( label ) :
	"""Translate a nodule label for the Graph Editor canvas.

	Performs gettext lookup and strips accents for IECoreGL.
	Returns None if no translation is needed.
	"""
	if _LANG == "en" :
		return None
	translated = translate( label )
	safe = stripAccents( translated )
	if safe == label :
		return None
	return safe

# ---------------------------------------------------------------------------
# Search helper
# ---------------------------------------------------------------------------

def normalizeForSearch( text ) :
	"""Lower-case *text* and strip combining diacritical marks."""
	nfkd = unicodedata.normalize( "NFKD", text )
	return "".join( c for c in nfkd if not unicodedata.combining( c ) ).lower()
