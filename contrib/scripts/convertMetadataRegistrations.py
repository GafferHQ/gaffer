#! /usr/bin/env python

import re
import sys
import json
import inspect
import argparse

import imath

import IECore
import Gaffer

parser = argparse.ArgumentParser(
	description = inspect.cleandoc(
	"""
	Utility to help convert node metadata registrations from
	old list-based syntax to new dict-based one.

	1. Run `gaffer env python convertMetadataRegistrations.py --store original.json` to save a copy of the original metadata for later comparison.
	2. Run `gaffer env python convertMetadataRegistrations.py --convert filesToConvert` to convert the files in place.
	3. Run `scons build` to install converted metadata.
	4. Rim `gaffer env python convertMetadataRegistrations.py --check original.json` to check that that new registrations create exactly the same
	   result as before.

	> Caution : The parsing done by `--convert` is extremely rudimentary, and relies on consistent
	> formatting of the input. Do you own due diligence in checking the results.
	"""
	),
	formatter_class = argparse.RawDescriptionHelpFormatter,
)

parser.add_argument(
	"--convert",
	help = "Converts a list of python files from the old metadata format to the new.",
	nargs = "*",
	default = [],
)

parser.add_argument(
	"--store",
	help = "Writes all current metadata values into a `.json` file for later verification.",
	nargs = "?",
	default = "",
)

parser.add_argument(
	"--check",
	help = "Checks current metadata values against a previously stored `.json` file.",
	nargs = "?",
	default = "",
)

def convert( fileName ) :

	with open( fileName ) as f :
		lines = f.readlines()

	inRegisterNode = False
	inPlugs = False

	for lineNumber in range( len( lines ) ) :

		line = lines[lineNumber]

		if line.startswith( "Gaffer.Metadata.registerNode(" ) :
			inRegisterNode = True

		if not inRegisterNode :
			continue

		if line == ")\n" :
			inRegisterNode = False
			continue

		if line == "\tplugs = {\n" :
			inPlugs = True

		if not inPlugs :
			continue

		if line.startswith( "\t}" ) :
			inPlugs = False
			break

		line = re.sub( r'^(\t\t"[a-zA-Z0-9_*?:.[\]]+") ?: ?[\[(]', r"\1 : {", line )
		line = re.sub( r"^(\t\t)[\])](,?\n)", r"\1}\2", line )

		line = re.sub( r'^(\t\t\t"[a-zA-Z0-9_:\-. ()]+"),(.*)', r"\1 :\2", line )

		lines[lineNumber] = line

	with open( fileName, "w" ) as f :
		f.writelines( lines )

def allMetadata() :

	appLoader = IECore.ClassLoader.defaultLoader( "GAFFER_APP_PATHS" )
	app = appLoader.load( "gui" )()
	app._executeStartupFiles( "gui" )

	result = {}
	for module in sys.modules.values() :

		for attrName in dir( module ) :

			attr = getattr( module, attrName )
			if not inspect.isclass( attr ) or not issubclass( attr, Gaffer.Node ) :
				continue

			try :
				node = attr()
			except Exception as e :
				continue

			def storeMetadata( target ) :

				for key in Gaffer.Metadata.registeredValues( target ) :
					try :
						value = Gaffer.Metadata.value( target, key )
					except Exception as e :
						value = str( e )

					result[f"{module.__name__}.{target.fullName()}/{key}"] = IECore.repr( value ) if value else  "None"

			storeMetadata( node )
			for child in Gaffer.GraphComponent.RecursiveRange( node ) :
				storeMetadata( child )

	return result

args = parser.parse_args()

if args.store :

	metadata = allMetadata()
	with open( args.store, "w" ) as f :
		json.dump( metadata, f )

	sys.exit( 0 )

if args.check :

	with open( args.check ) as f :
		oldMetadata = json.load( f )
	newMetadata = allMetadata()

	oldKeys = set( oldMetadata.keys() )
	newKeys = set( newMetadata.keys() )

	extraKeys = newKeys - oldKeys
	if extraKeys :
		sys.stderr.write( "Extra metadata :\n " )
		for key in sorted( extraKeys ) :
			sys.stderr.write( f"\t{key}\n" )

	missingKeys = oldKeys - newKeys
	if missingKeys :
		sys.stderr.write( "Missing metadata :\n " )
		for key in sorted( missingKeys ) :
			sys.stderr.write( f"\t{key}\n" )

	commonKeys = oldKeys.intersection( newKeys )
	badKeys = [ k for k in commonKeys if eval( newMetadata[k] ) != eval( oldMetadata[k] ) ]
	if badKeys :
		sys.stderr.write( "Mismatched metadata :\n " )
		for key in sorted( badKeys ) :
			sys.stderr.write( f"\t{key} : {oldMetadata[key]} : {newMetadata[key]}\n" )

	sys.exit( 1 if newKeys or missingKeys or badKeys else 0 )

for file in args.convert :
	convert( file )
