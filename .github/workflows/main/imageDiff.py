#!/usr/bin/env python
##########################################################################
#
#  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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

# Compares images produced by the current build (such as icons and documentation
# screenshots) against those from a reference build. This is used on CI to catch
# unintended changes.

import argparse
import hashlib
import html
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile

parser = argparse.ArgumentParser()

parser.add_argument(
	"--buildDir",
	required = True,
	type = pathlib.Path,
	help = "The Gaffer build directory containing the freshly generated images "
		"(also used to locate `oiiotool`)."
)

parser.add_argument(
	"--referenceDir",
	type = pathlib.Path,
	help = "An existing Gaffer build directory to compare against. When "
		"provided, no GitHub release is looked up or downloaded, and `--variant` "
		"and `--branch` are ignored."
)

parser.add_argument(
	"--branch",
	help = "The branch the pull request is targeting. Determines which release "
		"is used as the reference : `main` uses the latest `nightly`, a "
		"`<version>_maintenance` branch uses the latest release for that version. "
		"Required unless `--referenceDir` is given."
)

parser.add_argument(
	"--variant",
	help = "The build variant (e.g. `linux`, `windows`). Used to select the "
		"matching asset from the reference release. Required unless `--referenceDir` "
		"is given."
)

parser.add_argument(
	"--repo",
	default = os.environ.get( "GITHUB_REPOSITORY", "GafferHQ/gaffer" ),
	help = "The GitHub organisation/repo to query for the reference release."
)

parser.add_argument(
	"--github-access-token",
	dest = "githubAccessToken",
	default = os.environ.get( "GITHUB_ACCESS_TOKEN", None ),
	help = "A suitable access token to authenticate the GitHub API."
)

parser.add_argument(
	"--outputDir",
	default = pathlib.Path( "imageDiff" ),
	type = pathlib.Path,
	help = "A directory to write difference images and the html report to."
)

parser.add_argument(
	"--fail",
	type = float,
	default = 0.1,
	help = "Per-channel difference above which a pixel is counted as failing "
		"(passed to `oiiotool --fail`)."
)

parser.add_argument(
	"--failpercent",
	type = float,
	default = 2.0,
	help = "Percentage of failing pixels tolerated before an image is reported as "
		"changed (passed to `oiiotool --failpercent`)."
)

args = parser.parse_args()

if not args.referenceDir :
	missing = [ name for name in ( "variant", "branch" ) if not getattr( args, name ) ]
	if missing :
		parser.error( "the following arguments are required unless --referenceDir is given: " + ", ".join( "--" + m for m in missing ) )
	if not args.githubAccessToken :
		parser.exit( 1, "No --github-access-token/GITHUB_ACCESS_TOKEN set" )

# Store environment so it can be reused for each use of `oiiotool`.
gafferEnv = subprocess.run(
	[ str( args.buildDir / "bin" / ( "gaffer" if os.name != "nt" else "gaffer.cmd" ) ), "env" ],
	capture_output = True, universal_newlines = True, check = True
)

env = {}
for line in gafferEnv.stdout.splitlines() :
	key, separator, value = line.partition( "=" )
	if separator :
		env[key] = value

oiiotool = args.buildDir / "bin" / ( "oiiotool.exe" if sys.platform == "win32" else "oiiotool" )
if not oiiotool.exists() :
	parser.exit( 1, "Could not find 'oiiotool'." )

# Determine the reference release and the asset for our variant.
def referenceAsset( repo, branch, variant ) :

	suffix = "-{}.{}".format( variant, "zip" if variant.startswith( "windows" ) else "tar.gz" )

	if branch == "main" :

		# Nightly builds for `main` are published as assets on a single release
		# tagged `nightly`. Pick the most recently created asset matching our variant.
		release = repo.get_release( "nightly" )
		if not release :
			return None, None

		assets = [ a for a in release.get_assets() if a.name.endswith( suffix ) ]
		assets.sort( key = lambda a : a.created_at, reverse = True )
		return ( release, assets[0] ) if assets else ( release, None )

	# For maintenance branches we want the most recent release from that branch.
	match = re.match( r"^(\d+\.\d+)_maintenance$", branch )
	if not match :
		return None, None

	releases = [
		r for r in repo.get_releases()
		if r.tag_name.startswith( match.group( 1 ) + "." ) and not r.draft
	]
	releases.sort( key = lambda r : r.created_at, reverse = True )

	for release in releases :
		for asset in release.get_assets() :
			if asset.name.endswith( suffix ) :
				return release, asset

	return None, None

if args.referenceDir :

	if not args.referenceDir.is_dir() :
		parser.exit( 1, "Reference directory '{}' does not exist.".format( args.referenceDir ) )

	referenceRoot = args.referenceDir
	referenceName = str( args.referenceDir )

else :

	import github
	import requests

	githubClient = github.Github( args.githubAccessToken )
	repo = githubClient.get_repo( args.repo )

	release, asset = referenceAsset( repo, args.branch, args.variant )

	if asset is None :
		sys.stderr.write(
			"::notice::No build found for branch '{}' (variant '{}'). "
			"Skipping image comparison.\n".format( args.branch, args.variant )
		)
		sys.exit( 0 )

	referenceName = asset.name
	print( "Using build '{}' from release '{}' as reference".format( asset.name, release.tag_name ) )

	# Download and extract the reference archive.

	workDir = pathlib.Path( tempfile.mkdtemp( prefix = "gafferImageDiff" ) )
	archivePath = workDir / asset.name

	print( "Downloading {}".format( asset.browser_download_url ) )

	download = requests.get(
		asset.url,
		headers = {
			"Authorization" : "token {}".format( args.githubAccessToken ),
			"Accept" : "application/octet-stream",
		},
		stream = True,
	)
	download.raise_for_status()
	with open( archivePath, "wb" ) as outFile :
		shutil.copyfileobj( download.raw, outFile )

	referenceRoot = workDir / "reference"
	referenceRoot.mkdir()

	if archivePath.suffix == ".zip" :
		with zipfile.ZipFile( archivePath ) as archive :
			archive.extractall( referenceRoot )
	else :
		with tarfile.open( archivePath ) as archive :
			archive.extractall( referenceRoot )

	topLevel = [ e for e in referenceRoot.iterdir() if e.is_dir() ]
	if len( topLevel ) == 1 :
		referenceRoot = topLevel[0]

# Compare the images.

def listImages( directory ) :

	return { image.relative_to( directory ) for image in directory.rglob( "*" ) if image.suffix.lower() == ".png" }

def imageResolution( imagePath ) :

	result = subprocess.run(
		[ oiiotool, str( imagePath ), "--echo", "{TOP.width} x {TOP.height}" ],
		capture_output = True, universal_newlines = True, env = env
	)

	if result.returncode != 0 :
		return None

	return result.stdout.strip()

changed = []
added = []
removed = []

# Directories that contain image files to compare.
# Paths are relative to the root of a Gaffer build.
imageDirectories = [
	pathlib.PurePath( "graphics" ),
	pathlib.PurePath( "doc", "gaffer", "html", "_images" ),
]

for imageDirectory in imageDirectories :

	currentDir = args.buildDir / imageDirectory
	referenceDir = referenceRoot / imageDirectory

	currentImages = listImages( currentDir )
	referenceImages = listImages( referenceDir )

	for image in sorted( currentImages - referenceImages ) :
		added.append( imageDirectory / image )
		( args.outputDir / imageDirectory ).mkdir( parents = True, exist_ok = True )
		shutil.copyfile( currentDir / image, args.outputDir / imageDirectory / image )

	for image in sorted( referenceImages - currentImages ) :
		removed.append( imageDirectory / image )
		( args.outputDir / imageDirectory ).mkdir( parents = True, exist_ok = True )
		shutil.copyfile( referenceDir / image, args.outputDir / imageDirectory / image )

	for image in sorted( currentImages & referenceImages ) :

		referenceImage = referenceDir / image
		currentImage = currentDir / image

		# First compare image file hashes and early out if they match.
		with open( currentImage, mode = "rb" ) as f1, open( referenceImage, mode = "rb" ) as f2 :
			h1 = hashlib.md5()
			h2 = hashlib.md5()
			h1.update( f1.read() )
			h2.update( f2.read() )
			if h1.digest() == h2.digest() :
				continue

		diff = subprocess.run( [
				oiiotool, str( referenceImage ), str( currentImage ),
				"--fail", str( args.fail ), "--failpercent", str( args.failpercent ),
				"--diff",
			],
			capture_output = True,
			universal_newlines = True,
			env = env
		)

		# `oiiotool --diff` returns non-zero when the images differ.
		if diff.returncode != 0 :

			relativePath = imageDirectory / image
			# Write the reference, current and diff images into the output
			# directory so the HTML report below can display them side by side.
			outputImage = args.outputDir / relativePath
			outputImage.parent.mkdir( parents = True, exist_ok = True )
			referenceOutput = outputImage.with_suffix( ".reference.png" )
			currentOutput = outputImage.with_suffix( ".current.png" )
			diffOutput = outputImage.with_suffix( ".diff.png" )

			shutil.copyfile( referenceImage, referenceOutput )
			shutil.copyfile( currentImage, currentOutput )

			subprocess.run(
				[
					oiiotool, str( referenceImage ), "-ch", "R,G,B", str( currentImage ), "-ch", "R,G,B",
					"--absdiff", "-ch", "R,G,B", "-o", str( diffOutput ),
				],
				capture_output = True,
				universal_newlines = True,
				env = env
			)

			changed.append( {
				"path" : relativePath,
				"reference" : referenceOutput.relative_to( args.outputDir ),
				"current" : currentOutput.relative_to( args.outputDir ),
				"diff" : diffOutput.relative_to( args.outputDir ) if diffOutput.exists() else None,
				"referenceResolution" : imageResolution( referenceImage ),
				"currentResolution" : imageResolution( currentImage ),
			} )

# Markdown formatted summary report for the GitHub Actions run.

def writeSummary( lines ) :

	text = "\n".join( lines ) + "\n"
	sys.stdout.write( text )
	summaryFile = os.environ.get( "GITHUB_STEP_SUMMARY" )
	if summaryFile :
		with open( summaryFile, "a" ) as f :
			f.write( text )

summary = [
	"## Image comparison",
	"",
	"Compared `{}` against reference build `{}`.".format(
		"`, `".join( d.as_posix() for d in imageDirectories ), referenceName
	),
	"",
	"| Status | Count |",
	"| --- | --- |",
	"| Changed | {} |".format( len( changed ) ),
	"| Removed | {} |".format( len( removed ) ),
	"| Added | {} |".format( len( added ) ),
]

for title, images in (
	( "Changed", [ c["path"] for c in changed ] ),
	( "Removed", removed ),
	( "Added", added ),
) :
	if images :
		summary.append( "" )
		summary.append( "### {} ({})".format( title, len( images ) ) )
		summary += [ "- `{}`".format( image.as_posix() ) for image in images ]

writeSummary( summary )

# HTML report, written into the output directory. It shows the
# reference, current and difference images side by side for comparison.

def imageCell( label, source, resolution = "", resolutionDifference = False, imageTags = "" ) :

	resolution = "<div class='resolution{}'>({})</div>".format( " difference" if resolutionDifference else "", resolution ) if resolution else ""
	return (
		"<td><div class='label'>{label}</div>{resolution}"
		"<br/><div class='background'><a href='{src}'><img {tags} src='{src}'></a></div></td>"
	).format( label = html.escape( label ), resolution = resolution, tags = imageTags, src = html.escape( source.as_posix() ) )

changedRows = []
for entry in changed :
	changedRows.append(
		"<tr><th colspan='3'>{path}</th></tr>\n<tr>{cells}</tr>".format(
			path = html.escape( entry["path"].as_posix() ),
			cells = "".join( [
				imageCell( "Reference", entry["reference"], resolution = entry["referenceResolution"] ),
				imageCell( "Current", entry["current"], resolution = entry["currentResolution"], resolutionDifference = entry["referenceResolution"] != entry["currentResolution"] ),
				imageCell( "Difference", entry["diff"], imageTags = "class='diff'" ),
			] ),
		)
	)

removedRows = []
for entry in removed :
	removedRows.append(
		"<tr><th colspan='1'>{path}</th></tr>\n<tr>{cell}</tr>".format(
			path = html.escape( entry.as_posix() ),
			cell = imageCell( "Removed", entry ),
		)
	)

addedRows = []
for entry in added :
	addedRows.append(
		"<tr><th colspan='1'>{path}</th></tr>\n<tr>{cell}</tr>".format(
			path = html.escape( entry.as_posix() ),
			cell = imageCell( "Newly Added", entry ),
		)
	)

reportHtml = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Gaffer image comparison</title>
<style>
	body {{ font-family: sans-serif; margin: 2em; color: #222; }}
	h1 {{ font-size: 1.4em; }}
	p.meta {{ color: #555; }}
	table.images {{ border-collapse: collapse; width: 100%; margin-bottom: 2em; }}
	table.images th {{ text-align: left; background: #f0f0f0; padding: 0.4em 0.6em; font-family: monospace; }}
	table.images td {{ vertical-align: top; padding: 0.6em; width: 33%; }}
	.label {{ display: inline-block; font-weight: bold; margin-bottom: 0.4em; }}
	.resolution {{ display: inline-block; color: #777; font-family: monospace; font-size: 0.85em; margin-left: 0.5em; }}
	.resolution.difference {{ color: #ff0000; font-weight: bold; }}
	table.images img {{ max-width: 100%; min-width: var( --img-min-width, 0 ); image-rendering: pixelated; border 1px solid #ddd; display: block; }}
	table.images img.diff {{ filter: url( #diffGamma ) brightness( var( --diff-gain, 1 ) ); }}
	.images .background {{ display: inline-block; }}
	body.bg-white .images .background {{ background: #fff; }}
	body.bg-black .images .background {{ background: #000; }}
	body.bg-checker .images .background {{
		background-image:
			linear-gradient( 45deg, #ccc 25%, transparent 25% ),
			linear-gradient( -45deg, #ccc 25%, transparent 25% ),
			linear-gradient( 45deg, transparent 75%, #ccc 75% ),
			linear-gradient( -45deg, transparent 75%, #ccc 75% );
		background-size: 16px 16px;
		background-position: 0 0, 0 8px, 8px -8px, -8px 0;
	}}
	.controls {{
		position: fixed; top: 1em; right: 1em; z-index: 10;
		background: rgba( 255, 255, 255, 0.95 );
		border: 1px solid #ccc; border-radius: 6px;
		padding: 0.5em 0.75em; box-shadow: 0 1px 4px rgba( 0, 0, 0, 0.2 );
		font-size: 0.85em;
	}}
	.controls button {{ margin-left: 0.3em; cursor: pointer; }}
	.controls button.active {{ font-weight: bold; outline: 2px solid #4080c0; }}
	.controls .control-row {{ height: 2em; }}
	.controls .control-label {{ display: inline-block; width: 9em; }}
</style>
</head>
<body class="bg-checker">
<svg style="position: absolute; width: 0; height: 0" aria-hidden="true">
	<filter id="diffGamma" color-interpolation-filters="sRGB">
		<feComponentTransfer>
			<feFuncR type="gamma" exponent="1" amplitude="1" offset="0"/>
			<feFuncG type="gamma" exponent="1" amplitude="1" offset="0"/>
			<feFuncB type="gamma" exponent="1" amplitude="1" offset="0"/>
		</feComponentTransfer>
	</filter>
</svg>
<div class="controls">
	<div class="control-row">
		<span class="control-label">Background:</span>
		<button type="button" class="active" data-bg="bg-checker" onclick="setBackground( this )">Checker</button>
		<button type="button" data-bg="bg-white" onclick="setBackground( this )">White</button>
		<button type="button" data-bg="bg-black" onclick="setBackground( this )">Black</button>
	</div>
	<div class="control-row">
		<span class="control-label">Min Image Width:</span>
		<button type="button" class="active" data-width=0 onclick="setMinWidth( this )">None</button>
		<button type="button" data-width=64 onclick="setMinWidth( this )">64</button>
		<button type="button" data-width=256 onclick="setMinWidth( this )">256</button>
		<button type="button" data-width=512 onclick="setMinWidth( this )">512</button>
	</div>
	<div class="control-row">
		<span class="control-label">Diff Gamma:</span>
		<input type="number" id="gamma" class="textbox" value="1" min="0.1" max="64" step="1" oninput="setDiffGamma( 0 )">
		<input type="range" id="gamma-slider" class="slider" value="1" min="1" max="16" step="0.05" oninput="setDiffGamma( 1 )">
	</div>
	<div class="control-row">
		<span class="control-label">Diff Gain:</span>
		<input type="number" id="gain" class="textbox" value="1" min="0.1" max="64" step="1" oninput="setDiffGain( 0 )">
		<input type="range" id="gain-slider" class="slider" value="1" min="1" max="16" step="0.05" oninput="setDiffGain( 1 )">
	</div>
</div>
<h1>Gaffer image comparison</h1>
<p class="meta">Build <code>{build}</code> compared against reference build <code>{reference}</code>.<br>
{changedCount} <a href="#changed">changed</a>, {removedCount} <a href="#removed">removed</a>, {addedCount} <a href="#added">added</a>.</p>
<h2 id="changed">Changed: ({changedCount})</h2>
{changedSection}
<h2 id="removed">Removed: ({removedCount})</h2>
{removedSection}
<h2 id="added">Added: ({addedCount})</h2>
{addedSection}
<script>
function activate( button )
{{
	for( const other of button.parentElement.querySelectorAll( "button" ) )
	{{
		other.classList.toggle( "active", other === button );
	}}
}}
function setBackground( button )
{{
	document.body.className = button.dataset.bg;
	activate( button );
}}
function setMinWidth( button )
{{
	document.body.style.setProperty( "--img-min-width", `${{button.dataset.width}}px` );
	activate( button );
}}
function setDiffGain( slider )
{{
	const gain = document.getElementById( slider ? "gain-slider" : "gain" ).value;
	document.getElementById( slider ? "gain" : "gain-slider" ).value = gain;
	document.body.style.setProperty( "--diff-gain", gain );
}}
function setDiffGamma( slider )
{{
	const gamma = document.getElementById( slider ? "gamma-slider" : "gamma" ).value;
	document.getElementById( slider ? "gamma" : "gamma-slider" ).value = gamma;
	for( const func of document.querySelectorAll( "#diffGamma feFuncR, #diffGamma feFuncG, #diffGamma feFuncB" ) )
	{{
		func.setAttribute( "exponent", 1.0 / gamma );
	}}
}}
</script>
</body>
</html>
""".format(
	build = html.escape( os.environ.get( "GAFFER_BUILD_NAME", "build" ) ),
	reference = html.escape( referenceName ),
	changedCount = len( changed ),
	addedCount = len( added ),
	removedCount = len( removed ),
	changedSection = (
		"<table class='images'>\n{}\n</table>".format( "\n".join( changedRows ) )
		if changedRows else "<p>No images failed the comparison.</p>"
	),
	removedSection = (
		"<table class='images'>\n{}\n</table>".format( "\n".join( removedRows ) )
		if removedRows else "<p>No images removed.</p>"
	),
	addedSection = (
		"<table class='images'>\n{}\n</table>".format( "\n".join( addedRows ) )
		if addedRows else "<p>No images added.</p>"
	)
)

if changed or added or removed :
	args.outputDir.mkdir( parents = True, exist_ok = True )
	report = args.outputDir / "index.html"
	report.write_text( reportHtml )
	print( "Wrote HTML report to {}".format( report ) )

# Flag any changes from the reference.
if changed or removed :
	sys.stderr.write(
		"::error::Found {} changed and {} removed image(s) compared to the reference build. "
		"See the job summary and the uploaded `imageDiff` artifact.\n".format(
			len( changed ), len( removed )
		)
	)
elif added :
	sys.stderr.write(
		"::notice::Found {} new image(s) compared to the reference build. "
		"See the job summary and the uploaded `imageDiff` artifact.\n".format(
			len( added )
		)
	)
else :
	print( "No image differences found." )
