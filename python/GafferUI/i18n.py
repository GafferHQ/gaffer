import functools
import gettext
import json
import os
import pathlib
import re
import unicodedata


# ---------------------------------------------------------------------------
# i18n preferences config file
# ---------------------------------------------------------------------------
# Stored at ~/gaffer/i18n.json so it can be read *before* the full
# Preferences node is available.  The file is a small JSON dict:
#   { "language": "es", "translateNodeNames": true, "translateTooltips": true }

_I18N_CONF = pathlib.Path( "~/gaffer/i18n.json" ).expanduser()

def _readConf() :
	"""Return the persisted i18n preferences dict, or empty dict."""
	try :
		with open( _I18N_CONF, "r", encoding = "utf-8" ) as f :
			return json.load( f )
	except Exception :
		return {}

def saveConf( language, translateNodeNames, translateTooltips ) :
	"""Persist the i18n preferences to ~/gaffer/i18n.json."""
	_I18N_CONF.parent.mkdir( parents = True, exist_ok = True )
	with open( _I18N_CONF, "w", encoding = "utf-8" ) as f :
		json.dump(
			{
				"language" : language,
				"translateNodeNames" : translateNodeNames,
				"translateTooltips" : translateTooltips,
			},
			f, indent = 2
		)

# ---------------------------------------------------------------------------
# Determine effective language
# ---------------------------------------------------------------------------
# Priority: stored preference > GAFFER_LANG env var > "en"

_conf = _readConf()
_LANG = _conf.get( "language", os.environ.get( "GAFFER_LANG", "en" ) )
# Publish back so other code can query it
os.environ["GAFFER_LANG"] = _LANG

_translateNodeNames = _conf.get( "translateNodeNames", True )
_translateTooltips  = _conf.get( "translateTooltips", True )

# ---------------------------------------------------------------------------
# Load gettext catalog
# ---------------------------------------------------------------------------

_LOCALE_DIR = os.path.join( os.path.dirname( __file__ ), "locale" )

_trans = gettext.translation(
	"gaffer",
	_LOCALE_DIR,
	languages = [ _LANG ],
	fallback = True,
)

# ---------------------------------------------------------------------------
# Translation functions
# ---------------------------------------------------------------------------

def _normalize( text ) :
	"""Collapse whitespace so triple-quoted source strings match
	single-line .po msgid entries."""
	return " ".join( text.split() )

def _( text ) :
	normalized = _normalize( text )
	translated = _trans.gettext( normalized )
	if translated != normalized :
		return translated
	# Fallback: try original text in case .po uses the raw form
	return _trans.gettext( text )

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

def pgettext( context, text ) :
	"""Translate *text* with a disambiguating *context* (msgctxt).

	Uses the standard gettext convention of storing the lookup key
	as ``context + "\\x04" + text``.  If no translation is found the
	original *text* is returned (never the combined key).
	"""
	msgid = context + "\x04" + text
	translated = _trans.gettext( msgid )
	if translated == msgid :
		return text
	return translated

# ---------------------------------------------------------------------------
# Query helpers – used by the UI to check toggle states
# ---------------------------------------------------------------------------

def language() :
	return _LANG

def translateNodeNames() :
	return _translateNodeNames

def translateTooltips() :
	return _translateTooltips

# ---------------------------------------------------------------------------
# Node type label helper
# ---------------------------------------------------------------------------

_camelCaseRe = re.compile( r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|(?<=[a-zA-Z])(?=[0-9])" )

def _camelToSpaced( name ) :
	"""Convert CamelCase to spaced form: ``SystemCommand`` → ``System Command``."""
	return _camelCaseRe.sub( " ", name )

# Standard acronym / display corrections applied to shader names.
# Matches the replacements used by Cycles and Arnold ShaderMenu.py.
_SHADER_DISPLAY_CORRECTIONS = [
	( "Hsv", "HSV" ), ( "Rgb", "RGB" ), ( "Xyz", "XYZ" ), ( "Bw", "BW" ),
	( " To ", " to " ), ( "Aov", "AOV" ), ( "Uvmap", "UV Map" ),
	( "Ies", "IES" ), ( "Bsdf", "BSDF" ), ( "Non Uniform", "Nonuniform" ),
	( "Uv ", "UV " ), ( "Osl", "OSL" ),
]

def getNodeLabel( typeName, node = None ) :
	"""Return the translated UI label for a node type name.

	*typeName* is the short C++ class name, e.g. ``"Rectangle""
	or ``"SystemCommand"``.  The name is converted to spaced form
	(``"System Command"``) before lookup so that existing menu
	translations are reused.  When ``translateNodeNames`` is
	disabled the spaced English name is returned unchanged.

	If *node* is provided and it has a ``"name"`` StringPlug (i.e.
	it is a Shader or Light node), the specific shader/light name
	is used instead of the generic C++ wrapper type, so that e.g.
	each USD shader shows its own name rather than all of them
	showing "USD Shader".
	"""
	# Extract the shader name (a hashable string) so the expensive
	# work can be memoized by _getNodeLabelCached.
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
	"""Cached inner implementation of getNodeLabel.

	Both arguments are hashable strings (or None).  The regex
	splitting, acronym corrections, and gettext lookup are
	performed once per unique (typeName, shaderName) pair.
	"""
	if shaderName is not None :
		# Strip category path — only show the leaf name.
		# Original Gaffer sets the node name to the leaf via
		# __nodeName() which does shaderName.rpartition("/")[-1].
		if "/" in shaderName :
			shaderName = shaderName.rsplit( "/", 1 )[-1]

		parts = shaderName.split( "_" )
		spacedParts = [ _camelToSpaced( x ) for x in parts ]
		# Title-case each part so display corrections ("Bsdf" → "BSDF")
		# and .po lookups ("Principled BSDF") work for lowercase shader
		# names like "principled_bsdf".
		spacedParts = [
			p[0].upper() + p[1:] if p and p[0].islower() else p
			for p in spacedParts
		]
		spaced = " ".join( spacedParts )

		if not _translateNodeNames :
			for orig, repl in _SHADER_DISPLAY_CORRECTIONS :
				spaced = spaced.replace( orig, repl )
			return spaced

		tr = _( spaced )
		if tr != spaced :
			return tr
		for orig, repl in _SHADER_DISPLAY_CORRECTIONS :
			spaced = spaced.replace( orig, repl )
		return _( spaced )

	spaced = _camelToSpaced( typeName )
	if not _translateNodeNames :
		return spaced
	return _( spaced )

# ---------------------------------------------------------------------------
# Word-by-word label translation for dynamic plug/parameter names
# ---------------------------------------------------------------------------

# Color / vector component translation (RGB → RVA, XYZ unchanged)
_COLOR_COMPONENT_MAP = {
	"r" : "R", "g" : "V", "b" : "A",
	"x" : "X", "y" : "Y", "z" : "Z",
}

def translateColorComponent( name ) :
	"""Translate a single-char color/vector component name.

	Returns the translated character or None if not applicable.
	"""
	if not _translateNodeNames :
		return None
	lower = name.lower()
	if lower in _COLOR_COMPONENT_MAP :
		return _COLOR_COMPONENT_MAP[lower]
	return None

# Common multi-word phrases that require Spanish noun-adjective order.
# Checked BEFORE word-by-word fallback in translateLabel().
_PHRASE_MAP = {
	"default value" : "valor predeterminado",
	"default values" : "valores predeterminados",
	"default color" : "color predeterminado",
	"default name" : "nombre predeterminado",
	"default label" : "etiqueta predeterminada",
	"default mode" : "modo predeterminado",
	"total internal reflection" : "reflexión interna total",
	"channel name" : "nombre de canal",
	"file name" : "nombre de archivo",
	"custom value" : "valor personalizado",
	"custom name" : "nombre personalizado",
	"enabled value" : "valor habilitado",
	"active value" : "valor activo",
	"input value" : "valor de entrada",
	"output value" : "valor de salida",
	"source value" : "valor de origen",
	"constant value" : "valor constante",
	"maximum value" : "valor máximo",
	"minimum value" : "valor mínimo",
	"specular color" : "color especular",
	"specular colour" : "color especular",
	"diffuse color" : "color difuso",
	"diffuse colour" : "color difuso",
	"emission color" : "color de emisión",
	"emission colour" : "color de emisión",
	"refraction color" : "color de refracción",
	"refraction colour" : "color de refracción",
	"reflection color" : "color de reflexión",
	"reflection colour" : "color de reflexión",
	"ambient occlusion" : "oclusión ambiental",
	"focal length" : "longitud focal",
	"aspect ratio" : "proporción de aspecto",
	"pattern match" : "coincidencia de patrón",
	"pass through" : "pasar a través",
}

_WORD_MAP = {
	# Common plug/parameter words
	"color" : "color", "colour" : "color",
	"colors" : "colores", "colours" : "colores",
	"values" : "valores", "value" : "valor",
	"names" : "nombres", "name" : "nombre",
	"visible" : "visible",
	"in" : "en", "of" : "de", "the" : "el", "a" : "un", "an" : "un",
	"and" : "y", "or" : "o", "to" : "a", "for" : "para", "with" : "con",
	"from" : "desde", "by" : "por", "on" : "en", "at" : "en",
	"diffuse" : "difuso", "reflections" : "reflexiones", "refractions" : "refracciones",
	"reflection" : "reflexión", "refraction" : "refracción",
	"specular" : "especular", "glossy" : "brillante",
	"emission" : "emisión", "emissive" : "emisivo",
	"ambient" : "ambiental", "occlusion" : "oclusión",
	"shadow" : "sombra", "shadows" : "sombras",
	"light" : "luz", "lights" : "luces",
	"camera" : "cámara", "cameras" : "cámaras",
	"input" : "entrada", "output" : "salida",
	"inputs" : "entradas", "outputs" : "salidas",
	"image" : "imagen", "images" : "imágenes",
	"scene" : "escena", "scenes" : "escenas",
	"object" : "objeto", "objects" : "objetos",
	"filter" : "filtro", "filters" : "filtros",
	"pass" : "pase", "passes" : "pases",
	"render" : "render", "renderer" : "renderer",
	"shader" : "shader", "shaders" : "shaders",
	"material" : "material", "materials" : "materiales",
	"texture" : "textura", "textures" : "texturas",
	"normal" : "normal", "normals" : "normales",
	"position" : "posición", "positions" : "posiciones",
	"rotation" : "rotación", "scale" : "escala",
	"transform" : "transformación", "translation" : "traslación",
	"matrix" : "matriz",
	"width" : "ancho", "height" : "alto", "depth" : "profundidad",
	"size" : "tamaño", "radius" : "radio", "angle" : "ángulo",
	"distance" : "distancia", "offset" : "desplazamiento",
	"min" : "mín", "max" : "máx", "minimum" : "mínimo", "maximum" : "máximo",
	"default" : "predeterminado", "custom" : "personalizado",
	"enabled" : "habilitado", "disabled" : "deshabilitado",
	"enable" : "habilitar", "disable" : "deshabilitar",
	"type" : "tipo", "mode" : "modo", "method" : "método",
	"source" : "origen", "destination" : "destino", "target" : "objetivo",
	"weight" : "peso", "weights" : "pesos",
	"intensity" : "intensidad", "brightness" : "brillo",
	"exposure" : "exposición", "gamma" : "gamma",
	"contrast" : "contraste", "saturation" : "saturación",
	"hue" : "tono", "opacity" : "opacidad",
	"transparency" : "transparencia", "alpha" : "alfa",
	"red" : "rojo", "green" : "verde", "blue" : "azul",
	"white" : "blanco", "black" : "negro",
	"clamp" : "limitar", "clamps" : "limitaciones",
	"multiply" : "multiplicar", "divide" : "dividir",
	"add" : "añadir", "subtract" : "restar",
	"mix" : "mezclar", "blend" : "mezclar",
	"invert" : "invertir", "reverse" : "invertir",
	"flip" : "voltear", "mirror" : "espejo",
	"smooth" : "suave", "smoothing" : "suavizado",
	"interpolation" : "interpolación", "samples" : "muestras", "sample" : "muestra",
	"density" : "densidad", "frequency" : "frecuencia",
	"amplitude" : "amplitud", "phase" : "fase",
	"seed" : "semilla", "random" : "aleatorio",
	"threshold" : "umbral", "tolerance" : "tolerancia",
	"boundary" : "límite", "bounds" : "límites",
	"subdivision" : "subdivisión", "iterations" : "iteraciones",
	"count" : "cantidad", "number" : "número",
	"index" : "índice", "level" : "nivel",
	"layer" : "capa", "layers" : "capas",
	"channel" : "canal", "channels" : "canales",
	"mask" : "máscara", "masks" : "máscaras",
	"area" : "área", "volume" : "volumen",
	"surface" : "superficie", "mesh" : "malla",
	"vertex" : "vértice", "vertices" : "vértices",
	"edge" : "arista", "edges" : "aristas",
	"face" : "cara", "faces" : "caras",
	"point" : "punto", "points" : "puntos",
	"curve" : "curva", "curves" : "curvas",
	"line" : "línea", "lines" : "líneas",
	"primitive" : "primitiva", "variable" : "variable",
	"attribute" : "atributo", "attributes" : "atributos",
	"option" : "opción", "options" : "opciones",
	"parameter" : "parámetro", "parameters" : "parámetros",
	"property" : "propiedad", "properties" : "propiedades",
	"set" : "conjunto", "sets" : "conjuntos",
	"group" : "grupo", "groups" : "grupos",
	"path" : "ruta", "paths" : "rutas",
	"file" : "archivo", "files" : "archivos",
	"directory" : "directorio",
	"format" : "formato", "resolution" : "resolución",
	"frame" : "fotograma", "frames" : "fotogramas",
	"time" : "tiempo", "duration" : "duración",
	"start" : "inicio", "end" : "fin",
	"near" : "cercano", "far" : "lejano",
	"clip" : "recortar", "crop" : "recorte",
	"top" : "superior", "bottom" : "inferior",
	"left" : "izquierda", "right" : "derecha",
	"front" : "frontal", "back" : "posterior",
	"up" : "arriba", "down" : "abajo",
	"inside" : "interior", "outside" : "exterior",
	"global" : "global", "local" : "local",
	"world" : "mundo", "space" : "espacio",
	"coordinate" : "coordenada", "coordinates" : "coordenadas",
	"axis" : "eje", "pivot" : "pivote",
	"center" : "centro", "origin" : "origen",
	"visibility" : "visibilidad",
	"display" : "visualización", "compare" : "comparación",
	"preview" : "previsualización",
	"background" : "fondo", "foreground" : "primer plano",
	"scatter" : "dispersión", "absorption" : "absorción",
	"roughness" : "rugosidad", "metallic" : "metálico",
	"clearcoat" : "barniz", "sheen" : "brillo sedoso",
	"subsurface" : "subsuperficie", "transmission" : "transmisión",
	"anisotropic" : "anisotrópico", "anisotropy" : "anisotropía",
	"tangent" : "tangente", "tangents" : "tangentes",
	"bitangent" : "bitangente",
	"displacement" : "desplazamiento",
	"bump" : "relieve",
	"mapping" : "mapeo", "projection" : "proyección",
	"repeat" : "repetición", "tile" : "mosaico",
	"wrap" : "envolver", "clipping" : "acotamiento",
	"blur" : "desenfoque", "sharp" : "nítido",
	"noise" : "ruido", "pattern" : "patrón",
	"falloff" : "atenuación", "decay" : "decaimiento",
	"cone" : "cono", "sphere" : "esfera",
	"cylinder" : "cilindro", "disk" : "disco", "disc" : "disco",
	"quad" : "cuadrilátero", "rectangle" : "rectángulo",
	"cube" : "cubo", "box" : "caja",
	"spot" : "foco", "directional" : "direccional",
	"distant" : "distante", "dome" : "domo",
	"environment" : "entorno",
	"volume" : "volumen", "fog" : "niebla",
	"absolute" : "absoluto", "relative" : "relativo",
	"auto" : "automático", "manual" : "manual",
	"order" : "orden", "priority" : "prioridad",
	"label" : "etiqueta", "description" : "descripción",
	"version" : "versión",
	"prefix" : "prefijo", "suffix" : "sufijo",
	"category" : "categoría",
	"user" : "usuario",
	"data" : "datos",
	"result" : "resultado", "results" : "resultados",
	"context" : "contexto",
	"expression" : "expresión",
	"condition" : "condición",
	"active" : "activo", "inactive" : "inactivo",
	"exists" : "existe", "missing" : "faltante",
	"exact" : "exacto", "match" : "coincidencia",
	"inherit" : "heredar", "inherited" : "heredado",
	"override" : "sobrescribir",
	"delete" : "eliminar", "remove" : "eliminar",
	"copy" : "copiar", "paste" : "pegar",
	"connect" : "conectar", "disconnect" : "desconectar",
	"connection" : "conexión", "connections" : "conexiones",
	# Hierarchy terms (fixed convention)
	"parent" : "primario", "child" : "secundario",
	"children" : "secundarios",
	# Gaffer architecture terms (fixed convention)
	"plug" : "conector", "plugs" : "conectores",
	"widget" : "componente", "widgets" : "componentes",
	"gadget" : "grafeto", "gadgets" : "grafetos",
	# Additional plug/parameter words
	"window" : "ventana",
	"variables" : "variables",
	"row" : "fila", "rows" : "filas",
	"cells" : "celdas", "cell" : "celda",
	"resolved" : "resueltas",
	"compression" : "compresión",
	"command" : "comando",
	"deep" : "profundo",
	"globals" : "globales",
	"batch" : "lote",
	"strength" : "fuerza",
	"shutter" : "obturador",
	"elevation" : "elevación",
	"product" : "producto",
	"sum" : "suma",
	"immediate" : "inmediato",
	"isolated" : "aislado",
	"process" : "procesar",
	"calculate" : "calcular",
	"pixel" : "píxel",
	"aspect" : "aspecto",
	"ratio" : "proporción",
	"aperture" : "apertura",
	"focal" : "focal",
	"length" : "longitud",
	"field" : "campo",
	"factor" : "factor",
	"quality" : "calidad",
	"triangle" : "triángulo",
	"rule" : "regla",
	"overwrite" : "sobrescribir",
	"existing" : "existente",
	"hide" : "ocultar",
	"ignore" : "ignorar",
	"keep" : "mantener",
	"reference" : "referencia",
	"use" : "usar",
	"regular" : "regular",
	"scaling" : "escalado",
	"require" : "requerir",
	"requires" : "requiere",
	"sequence" : "secuencia",
	"execution" : "ejecución",
	"multiplier" : "multiplicador",
	"setting" : "ajuste", "settings" : "ajustes",
	"affect" : "afectar",
	"polygon" : "polígono",
	"part" : "parte",
	"optional" : "opcional",
	"orthographic" : "ortográfico",
	"override" : "sobrescritura", "overrides" : "sobrescrituras",
	"look" : "ver",
	"through" : "a través",
	"planes" : "planos",
	"non" : "no",
	"dynamic" : "dinámico",
	"script" : "script",
	"load" : "cargar",
	"errors" : "errores",
	"environment" : "entorno",
	# Scene Inspector property names
	"bound" : "límite", "topology" : "topología",
	"constant" : "constante", "uniform" : "uniforme",
	"varying" : "variable",
	"corners" : "esquinas", "creases" : "pliegues",
	"interpolate" : "interpolar",
	"linear" : "lineal", "per" : "por",
	"ids" : "IDs", "boolean" : "booleano",
	"indices" : "índices", "sharpnesses" : "agudezas del pliegue",
	"lengths" : "longitudes", "sharpness" : "agudeza del pliegue",
	"shear" : "sesgar",
	# Technical terms kept as-is
	"tir" : "TIR",
	"aov" : "VAS", "uv" : "UV", "rgb" : "RVA", "rgba" : "RVAA",
	"hsv" : "TSV",
	"sss" : "SSS", "ior" : "IOR", "hdri" : "HDRI",
	"id" : "ID",
	"overscan" : "overscan",
	"frustum" : "frustum",
	"spline" : "spline",
	"fallback" : "respaldo",
	# Shader material words
	"coating" : "recubrimiento",
	"thin" : "delgado", "thick" : "grueso",
	"flat" : "plano",
	"glass" : "vidrio", "metal" : "metal",
	"skin" : "piel", "hair" : "cabello",
	"fabric" : "tela", "velvet" : "terciopelo", "satin" : "satén",
	"matte" : "mate",
	"grain" : "granulación",
	"bias" : "sesgo", "power" : "potencia",
	"range" : "rango",
	"filename" : "nombre de archivo",
	"gain" : "ganancia",
	"success" : "éxito",
	"normalize" : "normalizar",
	"bright" : "brillo",
	"diameter" : "diámetro",
	"orientation" : "orientación",
	"backscatter" : "retrodispersión",
	"flame" : "llama",
	"extension" : "extensión",
}

def translateLabel( label ) :
	"""Translate a UI label, using exact .po match first, then word-by-word fallback.

	Useful for dynamic labels like shader parameter names that can't all be
	pre-added to the .po file.
	"""
	if not _translateNodeNames or _LANG == "en" :
		return label

	# USD / Cycles attribute names use namespace:name format
	# (e.g. "Shadow:color", "Cycles:use glossy") — never translate.
	if ":" in label :
		return label

	# Try exact match first
	exact = _( label )
	if exact != label :
		return exact

	# Expand CamelCase into spaced form before word-by-word translation
	expanded = _camelCaseRe.sub( " ", label )
	# Replace underscores with spaces so words like "Refraction_" match
	expanded = expanded.replace( "_", " " )
	expanded = " ".join( expanded.split() )  # collapse extra spaces

	# Try exact match on expanded form
	if expanded != label :
		exact2 = _( expanded )
		if exact2 != expanded :
			return exact2

	# Try display-name form (capitalize each word) to match .po entries
	# that use "Cast Shadow" while CamelCase expansion gives "cast Shadow".
	displayForm = " ".join( w.capitalize() for w in expanded.split() )
	if displayForm != expanded :
		exact3 = _( displayForm )
		if exact3 != displayForm :
			return exact3

	# Check phrase map (Spanish noun-adjective reordering)
	expLower = expanded.lower()
	if expLower in _PHRASE_MAP :
		tr = _PHRASE_MAP[expLower]
		# Capitalise first letter to match original label casing
		if expanded and expanded[0].isupper() and tr and tr[0].islower() :
			tr = tr[0].upper() + tr[1:]
		return tr

	# Word-by-word fallback with n-gram phrase matching.
	# Tries 3-word, then 2-word phrases from _PHRASE_MAP before
	# falling back to single-word _WORD_MAP lookup.
	words = expanded.split( " " )
	translated = []
	idx = 0
	while idx < len( words ) :

		# Try 3-word phrase
		if idx + 2 < len( words ) :
			tri = " ".join( words[idx:idx+3] ).lower()
			if tri in _PHRASE_MAP :
				tr = _PHRASE_MAP[tri]
				if idx == 0 and tr and tr[0].islower() :
					tr = tr[0].upper() + tr[1:]
				translated.append( tr )
				idx += 3
				continue

		# Try 2-word phrase
		if idx + 1 < len( words ) :
			bi = " ".join( words[idx:idx+2] ).lower()
			if bi in _PHRASE_MAP :
				tr = _PHRASE_MAP[bi]
				if idx == 0 and tr and tr[0].islower() :
					tr = tr[0].upper() + tr[1:]
				translated.append( tr )
				idx += 2
				continue

		word = words[idx]

		# Single-character words: translate color components, keep others
		if len( word ) <= 1 :
			lw = word.lower()
			if lw in _COLOR_COMPONENT_MAP :
				translated.append( _COLOR_COMPONENT_MAP[lw] )
			else :
				translated.append( word )
			idx += 1
			continue

		# Handle dotted compound labels (e.g. "Fallback.r" → "Respaldo.R")
		if "." in word :
			parts = word.split( "." )
			trParts = []
			for j, part in enumerate( parts ) :
				lp = part.lower()
				if len( part ) == 1 and lp in _COLOR_COMPONENT_MAP :
					trParts.append( _COLOR_COMPONENT_MAP[lp] )
				elif lp in _WORD_MAP :
					tp = _WORD_MAP[lp]
					if idx == 0 and j == 0 and tp and tp[0].islower() :
						tp = tp[0].upper() + tp[1:]
					trParts.append( tp )
				else :
					trParts.append( part )
			translated.append( ".".join( trParts ) )
			idx += 1
			continue

		lower = word.lower()
		if lower in _WORD_MAP :
			tr = _WORD_MAP[lower]
			# Capitalise first word only (Spanish rule)
			if idx == 0 and tr and tr[0].islower() :
				tr = tr[0].upper() + tr[1:]
			translated.append( tr )
		else :
			# Keep untranslatable words as-is (proper nouns, acronyms, etc.)
			translated.append( word )
		idx += 1

	return " ".join( translated )

# ---------------------------------------------------------------------------
# Search helper – accent-stripping normalisation
# ---------------------------------------------------------------------------

def normalizeForSearch( text ) :
	"""Lower-case *text* and strip combining diacritical marks."""
	nfkd = unicodedata.normalize( "NFKD", text )
	return "".join( c for c in nfkd if not unicodedata.combining( c ) ).lower()
