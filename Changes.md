1.2.x.x (relative to 1.2.1.1)
=======

Improvements
------------

- Playback :
  - Added <kbd>Ctrl</kbd>+<kbd>Right</kbd> hotkey toggle for forward playback.
  - Added <kbd>Ctrl</kbd>+<kbd>Left</kbd> hotkey toggle for backward playback.
  - Pressing either of <kbd>Right</kbd> or <kbd>Left</kbd> will also stop playback.
- Transform Tools : Added <kbd>O</kbd> shortcut to cycle through the orientation modes.

Fixes
-----

- Reference : Fixed bug reloading a Reference after changing the number of points in a SplinePlug. The complete edited spline is now maintained across a reload. If the spline has not been edited, then the value is updated from the `.grf` file as before (#5170).
- DispatchDialogue : Fixed `AttributeError: '__Implementation' object has no attribute 'message'` error.
- MultiLineStringPlugValueWidget : Fixed bug handling <kbd>Esc</kbd>.

Documentation
-------------

- Updated the "Assembling The Gaffer Bot" tutorial to use Cycles instead of Appleseed.

1.2.1.1 (relative to 1.2.1.0)
=======

Fixes
-----

- TractorDispatcher : Fixed `TypeError : unsupported operand types` error that prevented dispatch.
- ImageReader : Made error message more descriptive when trying to access a channel that doesn't exist.

1.2.1.0 (relative to 1.2.0.2)
=======

Features
--------

- SetEditor : Added a new editor UI for inspecting sets. This can be found in the tab next to the SceneInspector in the Standard layouts. Sets are displayed hierarchically using ":" characters in set names as separators.
- ImageToPoints : Added a new node for converting images to points primitives.
- MeshSplit : Added node for splitting a mesh into multiple meshes based on the values of a primitive variable. May be combined with the recently added MeshSegments to split meshes into connected parts.

Improvements
------------

- USD : Added translation of UsdUVTexture's `scale`, `bias` and `fallback` parameters to Arnold.
- StringPlugValueWidget : Added support for converting StringVectorData values pasted or dropped onto the widget. The string value is formed by joining the string array using spaces.
- Spreadsheet : Improved support for converting StringVectorData to StringData when dropping values on cells. The string value is formed by joining the string array using spaces.
- CompoundPathFilter : Canceller is now passed to member filters.
- PathListingWidget : Improved performance when sorting items based on the name column.
- Scene : Improved performance computing the bounding box for a primitive.
- aiQuadLight : Added `width` and `height` parameters.

Fixes
-----

- Locale :
  - Reintroduced `LC_NUMERIC=C` environment variable assignment to wrapper. This was removed in `1.2.0.0` but is still necessary due to a [bug in Cortex](https://github.com/ImageEngine/cortex/issues/1338).
  - Fixed serialisation of `.gfr` files in locales with non-default numeric formatting (#5158).
- Tweak nodes : Fixed bugs which prevented the creation of new tweaks when an existing tweak had an input connection.
- Preferences : Fixed bug which caused UI metadata to be serialised unnecessarily into `~/gaffer/startup/gui/preferences.py`.
- OpenGL Texture shader : Fixed bug which allowed transparent regions to obscure objects behind them.
- Viewer :
  - Fixed visualisation of Arnold `image` nodes with non-default UV Coordinates settings.
  - Fixed Arnold selection bugs caused by the `ai:fis_filter` option.
- SceneReader : Invalid primitive variables in USD files are now skipped during loading, with a warning being emitted instead.
- DeleteFaces : Fixed sudivision crease handling bug.
- USD RectLight : Fixed the orientation of textures applied to the light to be oriented with the top-left of the image at the top-left of the quad light when viewed from an object receiving illumination.

Documentation
-------------

 - Added more Python examples to the Scripting Reference "Common Operations" article.
 - Added instructions for installing and configuring Gaffer on Windows to the "Getting Started" guide.

API
---

- RGBAChannelsPlugValueWidget : Added support for `rgbaChannelsPlugValueWidget:allowNone` metadata.

Build
-----

- Cortex : Updated to version 10.4.6.0.
- Added support for Inkscape versions greater than 1.0.

1.2.0.2 (relative to 1.2.0.1)
=======

Fixes
-----

- Viewer : Fixed flickering and empty menu in the channel selector for the image view.
- RGBAChannelsPlugValueWidget, ChannelPlugValueWidget, ChannelMaskPlugValueWidget :
  - Fixed unnecessary updates when channel data changed.
- RGBAChannelsPlugValueWidget : Fixed bug that prevented errors being shown.
- Cycles : Fixed crash triggered by unsupported shader parameters (#5147).
- CompoundPlugValueWidget : Fixed errors when refreshing the widget.

1.2.0.1 (relative to 1.2.0.0)
=======

Fixes
-----

- Viewer : Fixed crash displaying Arnold quad lights in portal mode.

1.2.0.0 (relative to 1.1.9.0)
=======

This version enables Cycles support by default, as we believe we have made sufficient progress to allow wider testing. We may continue to make behaviour-changing updates if necessary though, so support is not yet considered final.

> Note : Python 2 support has been removed. All builds are now using Python 3.

Features
--------

- Windows : Added official builds for Windows.
- HierarchyView : Added control over the Visible Set, which defines the locations within the scene that are loaded and rendered by the Viewer.
  - The Inclusions column adds locations to the Visible Set, so that they and their descendants are rendered in the Viewer without needing to be expanded in the HierarchyView.
  - The Exclusions column excludes locations from the Visible Set, so that they and their descendants are never rendered in the Viewer, regardless of any other expansions or inclusions.
  - Locations can have their Visible Set inclusion or exclusion toggled by clicking within the appropriate column. <kbd>Shift</kbd>-clicking will remove the location and any of its descendants from the Visible Set. When multiple locations are selected, edits to any of the selected locations will affect all selected locations.
- Mute/Solo : Added the ability to mute and solo lights.
  - A light can be muted by setting the `light:mute` attribute. If that attribute is not present, the light will not be muted.
  - One or more lights can be enabled exclusively via membership in the `soloLights` set. If that set has one or more members, only the lights in that set will emit. If the set is empty, all lights emit according to their mute state. If a light is both muted and in the `soloLights` set, it will emit.
  - Light Editor :
    - Added a "Mute" column for toggling a light's mute attribute on and off.
    - Added a "Solo" column to quickly add and remove lights from the `soloLights` set.
  - Lights : Added a `mute` toggle, which can be accessed in the node editor from the `Light Linking` tab.
  - Added a visual indication to lights in the viewport when they are muted. Muted lights use a dark gray outline instead of yellow.
  - Cycles : Muted lights are disabled in renders.
  - Arnold : Muted lights are disabled in renders.
- Animation :
  - Added new curve extrapolation modes to determine the shape of a curve outside the range of its keys.
    - Constant : Curve is extended as a flat line.
    - Linear : Curve is extended as a line with slope matching tangent in direction of extrapolation.
    - Cycle : Curve is repeated indefinitely.
    - CycleOffset : Curve is repeated indefinitely with each repetition offset in value to preserve continuity.
    - CycleFlop : Curve is repeated indefinitely with each repetition mirrored in time.
    - CycleFlip : Curve is repeated indefinitely with each repetition inverted in value and offset to preserve continuity.
  - Added new curve tab in Animation Editor with controls for setting the extrapolation modes of a curve.

Improvements
------------

- Cycles : Updated to Cycles 3.4.
- OSLObject, OSLImage : Improved performance when running heavy shaders on Linux (by 3x in one benchmark). This is achieved using OSL's recently added batched shading API. In the event of any problem, the optimisation may be disabled by setting the environment variable `GAFFEROSL_USE_BATCHED=0`.
- NodeEditor : Improved interactivity by moving computations onto background threads. The UI will no longer hang while the NodeEditor waits for the result of a slow computation.
- LightEditor :
  - Added a "Disable Edit" command to the right-click menu, to easily disable tweaks in EditScopes (shortcut <kbd>D</kbd>).
  - Added a "Remove Attribute" command to the right-click menu, to delete attributes using the EditScope (shortcut <kbd>Delete</kbd>).
  - Adjustments made to the width of the "Name" column are now preserved when switching between sections.
- Isolate : The `keepLights` setting now also keeps light filters.
- AttributeTweaks : Added `Remove` mode.
- PathListingWidget : Added support for columns that can automatically stretch to make use of available space.
- Animation Editor : For protruding tangents the slope and scale controls are now disabled (non editable) and display constrained values.
- Expression : `pathlib.Path` values may now be assigned to StringPlugs.
- Render : An error is now emitted if the render camera is hidden, instead of rendering through a default camera instead (#5131).
- ResamplePrimitiveVariables : Extended the supported data types when resampling from a Constant primitive variable.
- Viewer : If Arnold is available, then it is preferred over Appleseed for performing OSL shader previews. If neither is available, then Cycles will be used (#5084).
- FormatPlugValueWidget, ChannelPlugValueWidget, ChannelMaskPlugValueWidget, RGBAChannelsPlugValueWidget, ViewPlugValueWidget : Added support for showing multiple plugs at once, as needed when multiple Spreadsheet cells are selected for editing.
- SceneReader :
  - Improved read performance for sets in USD files, with a benchmark reading a moderately large set seeing more than 2x speedup.
  - Improved cancellation responsiveness when reading large sets from USD files.
- SceneWriter : Improved performance when writing sets to USD files.
- Spreadsheet : Improved display of image formats.

Fixes
-----

- Layouts : Fixed bug applying window size and position from saved layouts (#5042).
- Arnold :
  - Fixed input connections to individual color and vector components when rendering with a GPU device.
  - The `ai:GI_diffuse_depth` and `ai:GI_specular_depth` options now default to `2` when they are left unspecified, matching the default values on the ArnoldOptions node.
- CompoundNumericPlugValueWidget : Fixed failure to construct with an empty list of plugs.
- ChannelPlugValueWidget : Fixed compatibility with multi-view images.
- FilteredSceneProcessor :
  - Fixed bugs which allowed read-only nodes to be edited.
  - Fixed undo for `Remove` menu item in Filter tab.
- NodeEditor : Fixed bugs in handling of "green dot" non-default-value indicators with nested plugs.
- 3Delight : Fixed rendering with recent versions of 3Delight, which no longer use the `DL_DISPLAYS_PATH` to search for display drivers.
- Metadata :
  - Fixed memory leak.
  - Fixed thread safety bug that prevented concurrent access to metadata for the _same_ plug or node from multiple threads.
- ShufflePrimitiveVariables, ShuffleAttributes, OptionQuery, PrimitiveVariableQuery, ShaderQuery, ContextQuery, CreateViews, SetVisualiser, OSLImage, OSLObject, OSLCode, Outputs : Fixed bugs which allowed read-only nodes to be edited.
- CodeWidget : Fixed auto-complete for `pathlib.Path` objects, and any other classes which throw `AttributeError` for an attribute advertised by `dir()`.
- Expression : Fixed non-deterministic parsing order for Python expressions (#4935).
- FileSequencePathFilter : Fixed bug whereby files were considered to be part of a sequence if they were in a numbered directory. Now only numbers in the file's name are considered.
- BoolWidget : Fixed bug triggered by calling `setImage()` from within a `with widgetContainer` block.
- LevelSetOffset, MeshToLevelSet, LevelSetToMesh, SphereLevelSet : Fixed bugs which could cause unnecessary repeated computations, or in the worst case, lead to deadlock.
- ValuePlug : Fixed rare deadlock when a TaskParallel compute recurses to a Legacy compute with the _same_ hash.
- GafferTest : Fixed bug which caused `parallelGetValue()` to use the wrong context.
- LightEditor : Fixed bug which could cause attribute edits to be made for a parent location instead of the desired one.
- BackgroundMethod : Fixed bug that could cause the `postCall` to be called on a widget that had already been removed from the UI.

API
---

- Filesystem path handling : Adopted `std::filesystem::path` and `pathlib.Path` in the C++ and Python APIs respectively, with automatic conversion between the two. These simplify common use cases, and provide for more elegant cross-platform path handling.
  - ScriptNode : `serialiseToFile()`, `executeFile()` and `importFile()` now take `filesystem::path` arguments.
  - Reference :
    - `load()` now takes a `filesystem::path` argument.
    - `fileName()` now returns a `filesystem::path` argument.
  - Box : `exportForReference()` now takes a `filesystem::path` argument.
  - ApplicationRoot :
    - `savePreferences()` now takes a `filesystem::path` argument.
    - `preferencesLocation()` now returns a `filesystem::path`.
  - FileSystemPath :
    - Added a constructor that accepts a `filesystem::path`.
    - Added a `standardPath()` method returning a `std::filesystem::path` object in C++ and a `pathlib.Path` object in Python.
  - StringPlug : Added a `setValue()` overload taking a `filesystem::path`.
  - Dispatcher : `jobDirectory()` now returns a `filesystem::path`.
  - Backups : File names are now represented using `pathlib.Path`.
  - TestCase : `temporaryDirectory()` now returns a `pathlib.Path`.
  - ShaderView : `registerReferenceScene()` now takes a `filesystem::path`.
  - Catalogue : `save()` and `load()` take a `filesystem::path`, and `generateFileName()` returns one.
  - ExtensionAlgo : `exportExtension()` now takes a `pathlib.Path` in the `directory` argument.
- PlugValueWidget : Added new API to provide asynchronous updates. The old `_updateFromPlugs()` and `_plugConnections()` methods are deprecated, and support for them will be removed in a future version.
- PathColumn : Added `setSizeMode()` and `getSizeMode()` methods, and `sizeMode` constructor argument. These allow the size behaviour of a PathColumn to be configured.
- EditScopeAlgo : Added `acquireSetEdits()` method.
- TestCase : Added `scopedLocale()` method.
- Animation :
  - The slope and scale of protruding tangents is now constrained to match the values of the sibling tangent.
  - Added `curve.extrapolationChangedSignal()` function, returns a signal that is called when a curve's extrapolation has changed.
  - Added new api for curve extrapolation modes (see header `Animation.h` for full details).
  - Added `description` metadata for curve extrapolation modes that is used to generate UI tooltips.
- PlugAlgo : Added `findDestination()` utility method.
- Style : `renderAnimationCurve()` function now takes a vector of curve vertices and an `inKeyRange` argument that indicates whether the specified curve vertices lie within the time range of the curve's keys.
- PlugAlgo : Added `dependsOnCompute()` utility method.
- PathColumn : Added `buttonPressSignal()`, `buttonReleaseSignal()` and `buttonDoubleClickSignal()`. These allow a PathColumn to implement its own event handling.
- Capsule : Removed attempts to detect invalidated Capsules.
- VisibleSet/VisibleSetData : Added struct used to define a subset of the scene to be rendered based on expansions, inclusions, and exclusions. This is used to allow scene locations to be defined as always or never renderable, overriding the usual UI expansion behaviour.
- ContextAlgo : Added `setVisiblesSet()`, `getVisibleSet()`, and `affectsVisibleSet()` methods.
- SceneGadget : Added `setVisibleSet()`, and `getVisibleSet()` methods.
- EditScopeAlgo : Added methods to modify and query modifications to set members in an Edit Scope.
- Widget : Added support for a `_postContructor()` method, which is called after the widget is fully constructed. This can be useful for performing post-initialisation work from a base class.
- GafferTest : Added ObjectPlug overloads for `repeatGetValue()` and `parallelGetValue()`.
- SceneTestCase : Added `assertParallelGetValueComputesObjectOnce()`. This can be used to check that expensive computes are using an appropriate cache policy.
- Gaffer ( Python module ) : Added `rootPath()` and `executablePath()` methods.
- TestLightFilter : Added new node to GafferSceneTest, to aid in testing of scenarios involving LightFilters.

Breaking Changes
----------------

- Python : Removed support for Python 2.
- MaterialX : The majority of OSL shaders in `shaders/MaterialX` are no longer provided, as the `OpenShadingLanguage` project removed them and no direct equivalent exists in the `MaterialX` project itself. We recommend using alternative shaders, or if necessary, sourcing them from a previous Gaffer release.
- Arnold : Changed the default values for the `ai:GI_diffuse_depth` and `ai:GI_specular_depth` options.
- Locale : Removed `LC_NUMERIC=C` environment variable assignment from wrapper. This was a workaround for an OpenColorIO bug that has since been fixed.
- Style : Changed the signature of the `renderAnimationCurve()` virtual function.
- Signal : Removed `disconnect( slot )` method. This was a performance hazard because it was linear in the number of connections. Use `Connection::disconnect()` instead, which is constant time.
- GafferTest : Removed `expectedFailure()` decorator. Use `unittest.expectedFailure()` instead.
- SceneWriter :
  - Sets are now only written on the first frame for each file written.
  - `SceneInterface::writeSet()` is now used in preference to `SceneInterface::writeTags()` for all non-legacy file formats.
- SceneReader : `SceneInterface::readSet()` is now used in preference to `SceneInterface::readTags()` for all non-legacy formats.
- CatalogueUI : Hid OutputIndexColumn from public API.
- ContextAlgo : Removed use of the `ui:scene:expandedPaths` context variable. Any code directly accessing `ui:scene:expandedPaths` should instead use the `getExpandedPaths()/setExpandedPaths()/expand()/expandDescendants()` methods provided by `ContextAlgo`.
- SceneGadget : Removed `setExpandedPaths()` and `getExpandedPaths()` methods. `setVisibleSet()` and `getVisibleSet()` are now used instead.
- GafferUI : Removed the `setReadOnly()` and `getReadOnly()` methods from the following widgets :
  - `GafferUI.PlugValueWidget`
  - `GafferUI.NodeEditor`
  - `GafferUI.NodeUI`
  - `GafferUI.PlugLayout`
- Reference : The `fileName()` Python binding now returns a `pathlib.Path` argument, or `None` for empty file names.
- ApplicationRoot : The `preferencesLocation()` Python binding now returns a `pathlib.Path` argument.
- StringPlug : `setValue( std::filesystem::path & )` now uses `path.generic_string()` for the value, whereas before an automatic conversion would have used `path.string()` (the native string).
- Dispatcher : the `jobDirectory()` Python binding now returns a `pathlib.Path`, or `None` if it is empty.
- `Context::EditableScope`, `ImagePlug::ChannelDataScope`, `ScenePlug::PathScope/SetScope` : Removed deprecated functions which didn't take pointers and required duplication of data.
- ViewportGadget : Removed deprecated `gadgetsAt()` signature.
- Isolate : The `keepLights` setting now also keeps light filters.

Build
-----

- Updated to GafferHQ/dependencies 6.0.0 :
  - Cortex : Updated to version 10.4.5.0.
  - Cycles : Updated to version 3.4.
  - Embree : Updated to version 3.13.4.
  - Expat : Added version 2.5.0.
  - Fmt : Added version 9.1.0.
  - OpenColorIO : Updated to version 2.1.2.
  - OpenImageIO : Updated to version 2.4.8.0.
  - OpenShadingLanguage : Updated to version 1.12.9.0.
  - OpenSubdiv : Updated to version 3.4.4.
  - PyString : Added version 1.1.4.
  - USD :
    - Updated to version 23.02.
    - Enabled the OpenImageIO plugin. Among other things, this allows OpenEXR textures to be shown in `usdview`.
  - YAML-CPP : Added version 0.7.0.
- 3Delight : Updated to 3Delight version 2.9.17.

1.1.9.x (relative to 1.1.9.3)
=======

1.1.9.3 (relative to 1.1.9.2)
=======

Fixes
-----

- ImageReader : Made error message more descriptive when trying to access a channel that doesn't exist.


1.1.9.2 (relative to 1.1.9.1)
=======

Fixes
-----

- Tweak nodes : Fixed bugs which prevented the creation of new tweaks when an existing tweak had an input connection.
- Preferences : Fixed bug which caused UI metadata to be serialised unnecessarily into `~/gaffer/startup/gui/preferences.py`.
- OpenGL Texture shader : Fixed bug which allowed transparent regions to obscure objects behind them.
- Viewer :
  - Fixed visualisation of Arnold `image` nodes with non-default UV Coordinates settings.
  - Fixed Arnold selection bugs caused by the `ai:fis_filter` option.

1.1.9.1 (relative to 1.1.9.0)
=======

Fixes
-----

- Cycles : Fixed crash triggered by unsupported shader parameters (#5147).
- CompoundPlugValueWidget : Fixed errors when refreshing the widget.

1.1.9.0 (relative to 1.1.8.0)
=======

Improvements
------------

- Arnold : Disabled ADP more thoroughly, using `ARNOLD_ADP_DISABLE=1` for Arnold 7.1.4.0 and greater. Set `ARNOLD_ADP_DISABLE=0` before running Gaffer if you wish to use ADP.
- Cycles :
  - Added warning when a shader contains a parameter which does not exist in Cycles.
  - Added warning when a shader contains a parameter with an unsupported datatype.
  - Added warning when a shader contains an enum parameter with an invalid value.
  - Added support for passing InternedStringData to enum and string parameters.

Fixes
-----

- Backups : Fixed error when a backup file contained characters that couldn't be represented using the current locale. This could be triggered by a separate bug in OpenShadingLanguage that caused the locale to be changed unnecessarily (#5048).
- Viewer :
  - Fixed crash when switching from Cycles to OpenGL rendering (#5051).
  - Fixed potential crash when destroying a raytraced viewport.
- Cyles :
  - Fixed crashes caused by providing unsupported data types in shader parameters.
  - Fixed support for Color4f values on colour shader parameters. This can be useful when loading non-standard USD files.
  - Fixed support for V[23]i values on vector shader parameters.
  - Fixed handling of colour array parameters.

API
---

- TestCase : Added `scopedLocale()` method.

1.1.8.0 (relative to 1.1.7.0)
=======

Features
--------

- MeshSegments : Added a node for identifying faces in contiguous segments.

Improvements
------------

- USD :
  - Added support for Arnold-USD's convention for representing connections to individual indices of an array.
  - Added loading of `float4` USD shader parameters as `Color4` parameters in Gaffer.

Fixes
-----

- Viewer : Fixed bug which made it impossible to switch back to a previously used display transform.
- Cycles : Disabled auto-tiling mode for the viewport/interactive render mode, which caused odd/glitchy behaviour on larger than 2k renders.
- HierarchyView : Fixed <kbd>P</kbd> and <kbd>N</kbd> editor focus hotkeys.

Build
-----

- Cortex : Updated to 10.4.4.0.

1.1.7.0 (relative to 1.1.6.1)
=======

Features
--------

- ContextVariableTweaks : Added a new node for tweaking the context used to evaluate upstream nodes.

Improvements
------------

- Cycles :
  - Replaced `size` on portals and quad lights with separate `width` and `height` parameters, and renamed `size` parameter of disk lights to `width`.
  - Added `use_camera`, `use_caustics` and `normalize` parameters to lights.
- TweakPlug : Added a `CreateIfMissing` mode, to only create a new value if one does not currently exist.
- OSLObject : Added support for attribute substitutions using `<attr:myAttrName>` syntax in string parameters, provided that `useAttributes` is turned on.
- UIEditor : Increased maximum size of the "Button Click Code" editor.

Improvements
------------

- NodeEditor : Added "Promote Value and Switch" context menu item for promoting NameValuePlugs to Boxes.

Fixes
-----

- Viewer :
  - Fixed Default display transform so that it updates correctly when the default is changed via the Preferences dialogue, and when the context changes.
  - Fixed drawing of image pixels to the left of the display window.
- Cycles :
  - Fixed custom AOVs (for SVM shading mode only, Cycles doesn't support custom AOVs in OSL mode) (#5044).
  - Fixed units for distant light angle (now degrees and not radians).
  - Fixed assignment of `emission` shader. Previously this was being assigned as a `cycles:light` attribute instead of `cycles:surface` (#5058).
  - Hid internal shader plugs which shouldn't be exposed to the user (e.g. `surface_mix_weight`).
- UVInspector : Fixed update delay when changing display transform.
- Random : Fixed GIL management bug which could lead to hangs.
- ShaderTweaks : Fixed `Remove` mode.
- FilterQuery : Fixed bug which prevented the output from updating when the input scene changed (#5066).
- Arnold : Fixed rendering of `token` enum parameter values loaded from USD.

1.1.6.1 (relative to 1.1.6.0)
=======

Fixes
-----

- NodeEditor : Fixed updates for the green "non-default-value" dots in plug labels.
- Cycles :
  - Fixed handling of OSL shader component connections (#4926).
  - Fixed crash when attempting to use a non-existent OSL shader.
  - Fixed `Unsupported socket "tiles"` warning when loading the `image_texture` shader.

1.1.6.0 (relative to 1.1.5.0)
=======

Features
--------

- SetQuery : Added a new node for querying the set memberships of a location.

Improvements
------------

- UIEditor : Added `Allow Custom Values` checkbox to the Widget Settings section for the Presets Menu widget. When on, this allows the user to enter their own custom values in addition to choosing presets from the menu.
- Image View : Added support for custom presets for choosing catalogue outputs to compare to.  This can be set up like `Gaffer.Metadata.registerNodeValue( GafferImageUI.ImageView, "compare.catalogueOutput", "preset:MyPreset", "myNamespace:specialImage" )`.  The Catalogue won't know how to deal with a request for "myNamespace:specialImage", and will just output an error image, but this could be useful in pipelines where Catalogue's are wrapped in custom nodes that can respond to this special value of the `catalogue:imageName`.  If you want to provide a custom icon for your custom mode, Gaffer will search for an icon name `catalogueOutput{preset name}.png`.
- Animation Editor : Added UI tooltips to menu items for TieMode and Interpolation.
- CopyPrimitiveVariables : Added `ignoreIncompatible` plug which will cause the node to not error when attempting to copy primitive variables from the source object that are imcompatible with the destination object.
- Arnold : Enabled support for using the `layerName` parameter with non-LPE outputs. This requires a minimum of Arnold 7.1.3.0, because it contains a fix for ARNOLD-12282.
- ShaderQuery : Added "From Selection" menu item to the popup menus for the `shader` plug and parameter adder.
- File browsers : Excessively long filter labels are now truncated, instead of making the widget too wide.
- PathParameterValueWidget : The `extensions` specified by the parameter are now translated to `fileSystemPath:extensions` metadata, enabling filtering in the Gaffer file browser.

Fixes
-----

- Viewer : Added missing bookmarks 1-4 to the image comparison menu.
- MessagesBinding : Fixed GIL management bug that could cause crashes when performing an interactive render.
- Spreadsheet : Fixed crash when connecting a StringVectorDataPlug to a row's `name` plug.
- Documentation : Fixed "In this article" navigation column contents on pages containing figures.

API
---

- Animation :
  - Added `description` metadata for `Animation.Interpolation` enum values that is used to generate UI tooltips.
  - Added `description` metadata for `Animation.TieMode` enum values that is used to generate UI tooltips.

1.1.5.0 (relative to 1.1.4.0)
=======

Features
--------

- PrimitiveVariableQuery : Added new node to query multiple primitive variables from a scene location.
  - Each query specifies the name and type of the primitive variable
  - Each query has a corresponding output plug with `exists`, `interpolation`, `type` and `value` child plugs.

Improvements
------------

- ArnoldOptions : Added support for `texture_use_existing_tx`, `texture_auto_generate_tx` and `texture_auto_tx_path`.
- Arnold : Added support for attributes containing InternedStringData, as would be obtained by loading `token` primvars from a USD file.
- Random : Added the `outFloat` plug to the NodeEditor, and moved output plugs into their own `Outputs` section.

Fixes
-----

- Arnold :
  - Fixed deletion of `ai:transform_type` attribute during interactive renders. The object now reverts to the default transform type in this case.
  - Fixed broken Viewer after Arnold encountered an error (such as a missing texture).
  - Fixed `Tools/Arnold/Flush Cache` not working when no interactive renders are running.

API
---

- TypedObjectPlug : Added V2fVectorDataPlug and V3iVectorDataPlug.
- PlugAlgo : Added support for V2iVectorData, V3fVectorData and Color3fVectorData types in `canSetValueFromData()` and `setValueFromData()` functions.
- VectorDataPlugValueWidget : Added support for V2iVectorData and Color3fVectorData plug types.

1.1.4.0 (relative to 1.1.3.0)
=======

Improvements
------------

- Cycles : Added support for custom attributes with either a `user:` or `render:` prefix. These can be authored in Gaffer and then read at render time using Cycle's attribute shader.

Fixes
-----

- Catalogue : Fixed crashes when using the <kbd>↑</kbd> or <kbd>↓</kbd> keys immediately after adding or removing a column.
- PathListingWidget : Fixed bug tracking the last selected path, which could cause crashes if the path was deleted or the columns were changed.
- Image Viewer : Fixed dragging a color from the image view using a context with the wrong time, and an error that could show up when deleting the currently viewed image.
- Cycles :
  - Fixed background shader bug that could cause a crash, or cause the initial render in the Cycles viewport to be blank.
  - Fixed light bug that triggered an assertion in Cycles debug builds.

1.1.3.0 (relative to 1.1.2.0)
=======

Features
--------

- Image Viewer :
  - Added "Match Display Windows" option to Compare Mode menu. This allows the comparison mode to directly view a low-res render over a high-res plate, providing better performance than scaling up the render using the node graph.
  - The Color Inspector now shows color values for both images when comparing. Picking a color by dragging from the image now selects the composited on-screen color, taking into account  "Compare Mode" and the wipe.

Improvements
------------

- EditScope Menu :
  - Changed the order of listed EditScopes to be alphabetical.
  - Added an icon to menu items that are ancestors of the active EditScope.
  - Menu items that only have a single item in their sub-menu are now collapsed into the parent item.

Fixes
-----

- Shader Viewer : Fixed (was broken in 1.1.2.0).
- Image Viewer :
  - Fixed visual artifact when using a wipe with Replace compare mode on images with mismatched pixel aspect ratios.
  - Fixed context used to compute the view menu for the image being shown. On the first update, an empty context was being used instead of the script's context.
  - Color Inspector :
    - Corrected half-pixel offset in measured pixel values.
    - Pixel location indicators are no longer affected by the display color transform.
- GraphEditor : Fixed crash when focussing an empty ContextVariables, NameSwitch or Loop node (#4944).
- UI :
  - Fixed tooltips containing raw HTML.
  - Fixed stalls caused by Qt repeatedly accessing the same icon files.
- DocumentationAlgo : Fixed handling of raw HTML by `markdownToHTML()`.
- Reference : Fixed unnecessary serialisation of connections from internal plugs to external plugs. These are serialised in the `.grf` file already, so do not need to be duplicated on the Reference node itself. This bug prevented changes to the internal connections from taking effect when reloading a modified `.grf` file, and could cause load failures when the connections were from an internal Expression (#4935).
- MeshToLevelSet, LevelSetOffset : Fixed bug that could cause partial results to be returned if a previous operation was cancelled.
- PlugValueWidget : Fixed unnecessary updates when calling `setContext()` with the same context.

API
---

- MenuDefinition : Added `icon` attribute support to `subMenu` items.

1.1.2.0 (relative to 1.1.1.0)
=======

Improvements
------------

- Viewer : Added support for selecting an image comparison node. This can be accessed by selecting the focus or selected node from the comparison widget at the top of the viewer, or by dragging an image node to the comparison widget.
- Catalogue :
  - Improved performance when interacting with large Catalogues.
  - Added hover state to the output index column, to indicate clickability.
  - Improved default column layout, so output index column is more compact.
- Sets : Added "Select Affected Objects" to the following plugs' right click menu :
  - Set expression and set name plugs
  - Spreadsheet cells connected to a set expression or set name plug
  - Plugs promoted from a set expression or set name plug
- PathFilter : Added "Select Affected Objects" to the following plugs' right click menu :
  - Plugs promoted from a `PathFilter.paths` plug (an unpromoted `PathFilter.paths` plug supports this since 0.61.13.0)
  - Spreadsheet cells connected to a `PathFilter.paths` plug.
  - Spreadsheet row names when the spreadsheet selector is set to `scene:path`.
- Spreadsheet : Added support for metadata on the `name` and `enabled` plug of each row. Metadata registered on plugs in the default row is mirrored automatically onto all other rows.
- ShuffleAttributes, ShufflePrimitiveVariables :
  - Added `replaceDestination` plugs that may be used to specify whether each shuffle replaces existing destination data with the same name.
  - Shuffles are now performed in the order they are defined, and separate shuffles may write to the same destination.

Fixes
-----

- Catalogue : Removed incorrect error message on empty Catalogues.
- Cycles :
  - Fixed crash rendering a scene containing a CoordinateSystem (#4865).
  - Fixed crash rendering a PointPrimitive with `N` primitive variable (#4876).
  - Fixed handling of `Varying` primitive variable interpolation (#4849).
  - Fixed handling of `Constant Color3f` primitive variables.
  - Fixed handling of indexed primitive variables.
  - Fixed `"attribute edit required geometry to be regenerated"` error when changing attributes on a camera.
  - Fixed `cycles:shader:displacement_method` attribute handling (#4893).
  - Fixed shader attribute substitutions (#4921).
- PathFilter : Fixed error when selecting a path element from a promoted `PathFilter.paths` plug (introduced in 0.61.13.0).
- ImageView : Fixed error with display of negative colors.
- NodeEditor : Fixed updated of section summaries when they are changed in the UI Editor.
- ArnoldColorManager : Fixed broken presets for `color_space_narrow` and `color_space_linear`.
- Spreadsheet :
  - Fixed bugs with inconsistent column ordering.
  - Fixed bug that allowed operations on hidden columns included through shift-selection (was seen by users as the disable hotkey unexpectedly affecting columns on other tabs).
- ArnoldDisplacement : Removed irrelevant shader name widget and `Reload` button.

API
---

- PathColumn : Added support for a different icon to be shown when a cell is hovered.
- SetUI : Removed `ui:scene:acceptsSet*` metadata from entries that are promoted along with a plug.
- MetadataAlgo : Added `isPromotable()` method.
- StandardLightVisualiser : Added a `muted` boolean to wireframe light drawing methods.

1.1.1.0 (relative to 1.1.0.0)
=======

Improvements
------------

- LightEditor : Improved update performance, as a result of general improvements to the PathListingWidget that may improve performance elsewhere too.

Fixes
-----

- Viewer : Fixed rendering of background in `Replace` comparison mode.

Build
-----

- Fixed backwards compatibility with Boost 1.73 (broken in 1.1.0.0).

1.1.0.0
=======

Features
--------

- Image Viewer : Added image comparisons and wipes. Press <kbd>Q</kbd> in Viewer to enable. The primary image is compared to an Output Index set on the currently viewed Catalogue. Comparison modes including `Over`, `Under`, `Difference` and `Replace` can be selected from a dropdown menu. A wipe can be positioned by dragging in the viewer, and toggled using <kbd>W</kbd>.
- Catalogue : Added Output Index column which can be used to set particular images as numbered outputs that can be referenced from the Viewer and CatalogueSelect nodes.

Fixes
-----

- Plug : Fixed bug that could prevent `plugDirtiedSignal()` from ever being emitted again if an exception was thrown during parenting. This could cause the UI to stop updating.
- FileSystemPath (Windows only) :
  - `.` characters are now excluded from the path entries. These were being inserted in some cases even when the user did not input one.
  - Fix browsing UNC paths in file browsers.
- UI :
	- Fixed one pixel alignment issue with highlighted and disabled icons.
	- Improved appearance of adjoined widgets.
	- Clicking on a button no longer assigns focus to it.
  - Fixed appearance of disabled MenuButtons, so that they match the appearance of disabled Buttons.

API
---

- Signals :
  - Added `Trackable::disconnectTrackedConnections()` method.
  - Added `ScopedConnection` move constructor and move assignment operator.
- ViewportGadget : Added `setPostProcessShader()`.  This allows the main layer to be rendered to a framebuffer, and processed by a shader before being displayed.  Useful for applying color transforms on the GPU after rendering.
- GafferImageUI : Added `OpenColorIOAlgo::displayTransformToFramebufferShader()`.  Converts an OCIO processor to a shader suitable for use with `setPostProcessShader()`.
- ImageView : ImageView now uses a color transform on the viewport instead of ImageGadget.  Should not impact user visible behaviour, but paves the way for future work.
- ImageGadget : Added functions for setting wipe and blend mode.
- Path : Added virtual `rootAndNames()` method. This can be overridden to modify the `root` and `names` values as set by `setFromString()`.
- FileSystemPath :
  - Added support for Windows paths.
  - Added `nativeString()` function to return the path as an OS-specific string.
  - (Windows only) Paths beginning with a single `/` or `\` not followed by a drive letter are interpreted as UNC paths.
- WidgetAlgo : Improved `joinEdges()` to support a wider range of widget types.
- OpenColorIOTransform : Consolidated the duplicate `Direction` enums from CDL, LookTransform and LUT in to a single `OpenColorIOTransform::Direction` enum.

Breaking Changes
----------------

- ImageGadget : Removed setters and getters for `DisplayTransform`, `UseGPU`, `Clipping`, `Exposure`, `Gamma`.  Instead use `ViewportGadget::setPostProcessShader()` to set up a GPU color transform, or set the plug values on `ImageView`.
- ImageView : Using CPU color transforms is now deprecated.  We can't properly support wipes in CPU mode, and OCIO now offers full quality on the GPU, in addition to the performance being much better.  While the CPU functionality still exists, the UI has been hidden.
- Signals : Removed flawed `ScopedConnection` copy constructor and assignment operator. Use move construction and assignment instead.
- ImagePlug : Removed unused `viewName` argument from `viewNames()` and `viewNamesHash()` methods.
- StandardAttributes : Removed backwards compatibility for StandardAttributes nodes saved from Gaffer `0.95.0` (May 2014) and earlier. If necessary, resave affected files using a recent Gaffer version.

1.0.6.6 (relative to 1.0.6.5)
=======

- ShaderTweaks : Fixed `Remove` mode.
- FilterQuery : Fixed bug which prevented the output from updating when the input scene changed (#5066).
- Random : Fixed GIL management bug which could lead to hangs.
- Arnold : Fixed rendering of `token` enum parameter values loaded from USD.

1.0.6.5 (relative to 1.0.6.4)
=======

Fixes
-----

- NodeEditor : Fixed updates for the green "non-default-value" dots in plug labels.

1.0.6.4 (relative to 1.0.6.3)
=======

Fixes
-----

- MessagesBinding : Fixed GIL management bug that could cause crashes when performing an interactive render.
- Spreadsheet : Fixed crash when connecting a StringVectorDataPlug to a row's `name` plug.
- Documentation : Fixed "In this article" navigation column contents on pages containing figures.

1.0.6.3 (relative to 1.0.6.2)
=======

Fixes
-----

- Catalogue : Fixed crashes when using the <kbd>↑</kbd> or <kbd>↓</kbd> keys immediately after adding or removing a column.
- PathListingWidget : Fixed bug tracking the last selected path, which could cause crashes if the path was deleted or the columns were changed.

1.0.6.2 (relative to 1.0.6.1)
=======

Fixes
-----

- GraphEditor : Fixed crash when focussing an empty ContextVariables, NameSwitch or Loop node (#4944).
- UI :
  - Fixed tooltips containing raw HTML.
  - Fixed stalls caused by Qt repeatedly accessing the same icon files.
- Viewer : Fixed context used to compute the view menu for the image being shown. On the first update, an empty context was being used instead of the script's context.
- DocumentationAlgo : Fixed handling of raw HTML by `markdownToHTML()`.
- Reference : Fixed unnecessary serialisation of connections from internal plugs to external plugs. These are serialised in the `.grf` file already, so do not need to be duplicated on the Reference node itself. This bug prevented changes to the internal connections from taking effect when reloading a modified `.grf` file, and could cause load failures when the connections were from an internal Expression (#4935).
- MeshToLevelSet, LevelSetOffset : Fixed bug that could cause partial results to be returned if a previous operation was cancelled.
- PlugValueWidget : Fixed unnecessary updates when calling `setContext()` with the same context.

1.0.6.1 (relative to 1.0.6.0)
=======

Fixes
-----

- NodeEditor : Fixed update of section summaries when they are changed in the UI Editor.
- ArnoldColorManager : Fixed broken presets for `color_space_narrow` and `color_space_linear`.
- ArnoldDisplacement : Removed irrelevant shader name widget and `Reload` button.
- ImageView : Fixed error with display of negative colors.
- Spreadsheet :
  - Fixed bugs with inconsistent column ordering.
  - Fixed bug that allowed operations on hidden columns included through shift-selection (was seen by users as the disable hotkey unexpectedly affecting columns on other tabs).

1.0.6.0 (relative to 1.0.5.1)
=======

Improvements
------------

- Constraint :
  - Added `maintainReferencePosition` plug. This allows the constraint to maintain the original position of the object at a specifed reference time.
  - Improved performance for UV constraints where the target has static geometry but an animated transform. One such benchmark shows a greater than 40x speedup.

Fixes
-----

- Shape : Fixed unnecessary serialisation of internal connection.
- ScaleTool :
  - Fixed oversensitive scaling when zoomed out in the Viewer.
  - Prevented uniform scaling from becoming negative.

1.0.5.1 (relative to 1.0.5.0)
=======

Fixes
-----

- GafferImage : Fixed `Context has no variable named "image:viewName"` errors. If `image:viewName` is not provided by a context, GafferImage automatically falls back to a value of `default`.

API
---

- GUI config : Stopped adding an `image:viewName` variable to `Script.variables`. This was an attempt to provide fallbacks for legacy code that didn't provide the `image:viewName` context variable, but it was only partially effective. It is unnecessary now that GafferImage has internal fallbacks instead.

1.0.5.0 (relative to 1.0.4.0)
=======

Features
--------

- Rename : Added a new node for renaming scene locations (#1201).
- LookTransform : Added a new node for applying OpenColorIO looks to images.

Improvements
------------

- SplinePlug : Added `Constant` interpolation mode.
- SceneReader : Added reading of more Alembic GeomParam types. Specifically `unsigned char`, `uint16`, `int16` and `uint32` GeomParams are loaded as `UCharVectorData`, `UShortVectorData`, `ShortVectorData` and `UIntVectorData` PrimitiveVariables respectively.
- SceneWriter : Added writing of more Alembic GeomParam types, mirroring the improved reading mentioned above.
- Light Editor : Added the ability to select linked objects and to delete lights. Both commands can can be accessed by right-clicking a light name and selecting either 'Select Linked Objects' or 'Delete'.
- Graph Editor : When changing the root of the Graph Editor (such as entering or exiting a Box), framing is now restored specifically for the current Graph Editor. Previously, a single framing history was used for all Graph Editors.

Fixes
-----

- GraphEditor : Fixed handling of errors on `Dot.labelType` and `Dot.label` plugs.
- EditScope : Fixed mislocated plug nodules when connecting a new `EditScope` to a `BoxIn`, `BoxOut` or `Box` node.
- Backdrop : Fixed bug selecting or moving a backdrop when zoomed out in the GraphEditor, where drag-resizing the top edge was incorrectly being given precedence.
- CDL : Fixed handling of values for the `direction` plug. Previously, `OCIO::TransformDirection` enum values were being used directly as plug values, but OpenColorIO 2 broke compatibility by changing the enum. A new `GafferImage::CDL::Direction` enum provides stable values for use in the `CDL.direction` plug, insulating Gaffer from future changes.
- ViewPlugValueWidget :
  - Fixed bug which caused images to be evaluated in the wrong context.
  - Fixed error handling bug which could prevent the NodeEditor from building.
- CropWindowTool :
  - Fixed bug which caused images to be evaluated in the wrong context.
  - Fixed bug handling images with non-default views.
- Cycles : Fixed rendering with a non-default crop window.
- Arnold : Fixed handling of closure shader connections in USD materials exported from Maya.

Build
-----

- Cortex : Updated to 10.4.2.1.

1.0.4.0 (relative to 1.0.3.0)
=======

Features
--------

- Edit Menu : Added "Duplicate with Inputs" menu item, with <kbd>Ctrl</kbd>+<kbd>D</kbd> shortcut.
- OptionTweaks : Added node for tweaking options in a scene.
- OptionQuery : Added node for querying options from a scene.
- StandardAttributes : Added `automaticInstancing` plug to allow instancing to be disabled on selected locations. Currently supported only by the Arnold renderer.

Improvements
------------

- TweakPlug : Added the ability to set `InternedStringData` from `StringData`.
- GraphEditor : Added a warning for attempts to open the node creation menu in a read-only graph.
- Light Editor :
  - Added explanation to cell popup when a parameter cannot be edited because there are no editable sources.
  - Added an error icon to a cell with an explanation in the tooltip when there is an error computing its value (#4805).

Fixes
-----

- SceneReader :
  - Fixed reading of Alembic files with animated visibility.
  - Fixed reading of primitive variables from UsdGeomPointInstancers.
- GraphEditor : Fixed bugs which allowed new connections to be made in read-only graphs.
- NodeEditor : Fixed bugs which allowed plugs to be added to read-only tweaks nodes.
- CyclesOptions : Fixed errors in section summaries.
- NoduleLayout : Fixed shutdown crashes triggered by custom gadgets implemented in Python.
- ShaderTweaks : Fixed error when attempting to use a `:` in a parameter name.

Build
-----

- Cortex : Updated to 10.4.1.2.

1.0.3.0 (relative to 1.0.2.1)
=======

This release introduces support for the open source [Cycles](https://www.cycles-renderer.org/) renderer. This is introduced as an opt-in feature preview intended for early testing and feedback as breaking changes can be expected while we continue to improve Cycles integration in future releases. As such, the use of Cycles is disabled by default but can be enabled via an environment variable. Additionally we've added support for viewing parameter history in the Light Editor, automatic render-time translation of UsdPreviewSurface shaders and UsdLuxLights for Arnold and made the usual small fixes and improvements.

> Note :
>
> The Cycles feature preview can be enabled by setting the `GAFFERCYCLES_FEATURE_PREVIEW` environment variable to `1`.

Features
--------

- Cycles : Added initial support for the Cycles renderer.
- Light Editor : Added a non-modal dialog to view the history of a parameter. It can be accessed by right-clicking a parameter in the Light Editor and selecting `Show History...`. Within the dialogue :
  - Double clicking a node name will open a Node Editor popup.
  - Dragging a node name into the Graph Editor will zoom to the node.
  - Double clicking, pressing <kbd>Return</kbd> or <kbd>Enter</kbd> on a parameter value or operation will open a plug popup to edit the value.

Improvements
------------

- USD :
  - Added automatic render-time translation of UsdPreviewSurface shaders and UsdLuxLights for Arnold.
  - The SceneReader now loads all UsdLuxLights into the `defaultLights` set so that they are linked by default.
- SceneReader :
  - Added support for Alembic visibility attributes.
  - Added loading of `treatAsPoint` and `treatAsLine` parameters from UsdLux lights.
- SceneWriter : Added support for Alembic visibility attributes.
- ColorPlugValueWidget : Hid the color chooser button (sliders) for output plugs.
- Arnold : Added metadata for new `standard_volume` shader parameters introduced in Arnold 7.1.3.0.
- VectorDataWidget : Added a color swatch column for `Color3f` and `Color4f` elements. These are currently included in the `RandomChoice` node when `choices` is set to a list of colors, and for color primitive variables in the Primitive Inspector.
- NameWidget : Added a check to prevent users from setting a node or plug name to a value starting with a double underscore.
- ShaderTweaks : Added Create and Remove tweak modes.

Fixes
-----

- Qt : Added missing QtUiTools module.
- SceneReader : Fixed shader type for UsdLux lights. It was `surface` and is now `light`.
- Fixed a bug in `SceneAlgo::attributeHistory` that would return a branching history from a `ShaderTweaks` node with `inherit` enabled.
- Arnold : Fixed errors when making interactive render edits to lights with component-level connections between OSL shaders.
- PathListingWidget :
  - Fixed bug where one more rows at the bottom of the list could not be selected.
  - Fixed error when dragging from shader browser name columns, shader browser input columns and Catalogue columns.
- PathFilter : Improved positioning of PathFilters created by dropping paths onto a node.
- GraphEditor :
  - Improved handling of Backdrops when laying out nodes. Individual nodes are no longer pushed outside backdrops, and backdrops themselves are positioned as a group containing all their child nodes.
  - Improved positioning of pasted nodes, so that they are less likely to overlap with any node they are automatically connected to.

API
---

- StandardLightVisualiser :
  - Added support for parameters specifying the width and height of quad lights, and the length of cylinder lights.
  - The `coneAngleParameter` metadata is now supported for all light types.

Documentation
-------------

- Improved "Controls and Shortcuts" and added link in help menu.

Build
-----

- Cortex : Updated to 10.4.1.0.

1.0.2.1 (relative to 1.0.2.0)
=======

Fixes
-----

- TweakPlug : Added `Min` and `Max` tweak modes to the UI for numeric tweaks. These were previously only available through Python.
- Arnold : Fixed rendering error for cubic curves with Vertex interpolation Quatf primitive variables.
- ImageReader : Fixed reading of signed integer TIFF files, which were failing due to a missing colorspace configuration. Signed integer files are now assumed to contain linear data (#4772).

1.0.2.0 (relative to 1.0.1.0)
=======

Improvements
------------

- TweakPlug : Using the `ListAppend` and `ListPrepend` modes to add to a non-existent list now creates a list with the new values. Using the `ListRemove` mode to modify a non-existent list results in a non-existent list. All other modes retain their current `missingMode` behavior.
- ImageWriter : The `openexr.dataType` plug now accepts an expression or spreadsheet input to set per-channel data types.

Fixes
-----

- ImageWriter : Fixed bug with color transform alpha handling when the alpha channel was not the last channel.
- Viewer : Fixed images not displaying when the display window was offscreen.
- UV Inspector : Fixed texture display (broken in 1.0.0.0).
- Animation : Prevented negative zero slope.
- Animation Editor :
  - Fixed glitch when dragging a tangent having an opposite tangent with (+/-) inf slope.
  - Fixed bug that caused exception to be raised when the parent node of an editable curve was removed.
  - Fixed bug that prevented signals from being disconnected when a key was deleted.

1.0.1.0 (relative to 1.0.0.0)
=======

Improvements
------------

- TweakPlug : Added new tweak modes.
  - Min : Resulting value will be the lesser of the existing value and the tweak value. For values with multiple components, such as `Color3f`, each component is compared individually.
  - Max : Same as `Min` except the resulting value is the greater of the existing value and the tweak value.
  - ListAppend : Values in the tweak list are added to the end of the existing list. If a value is in both the existing list and the tweak list, it is removed from the existing list before being added.
  - ListPrepend : Same as `ListAppend` except the tweak list is added to the beginning of the existing list.
  - ListRemove : Values in the tweak list are removed from the existing list.
- Added horizontal scroll bars to the Light Editor, Scene Inspector and Shader Browser when their content is too wide to fit within the widget.

Fixes
-----

- LightEditor :
  - Fixed error when pressing <kbd>Return</kbd> or <kbd>Enter</kbd> with no cells selected.
  - Fixed error when double-clicking the `Name` column.
- Catalogue :
  - Fixed bug that prevented saving of images.
  - Fixed bugs in column listing for multi-view images.
- ShaderQuery and ShaderTweaks : Fixed error `TypeError: object of type 'NoneType' has no len()` when clicking "Input" column of a shader row.
- OSLObject/OSLImage : Fixed bug which resulted in undefined values for derivatives.

1.0.0.0 (relative to 0.61.x.x)
=======

> Note : This release requires Arnold version 7.1.0.0 or newer.

Features
--------

- Viewer :
  - Added optional raytraced rendering, to provide high quality preview of lighting and shading. Initially only Arnold is supported, but other renderers will be added in future.
  - Added FPS counter option to Gadget menu.
- ImageReader : Improved support for multi-part OpenEXR files, including fixes for reading many non-standard-conforming files from 3rd party software (#4559). The new `channelInterpretation` plug controls the naming of channels loaded from multi-part files.
- ImageWriter : Added support for writing multi-part OpenEXR files using a new `layout` plug. This includes presets for standard conforming single-part and multi-part files, and several presets that match Nuke's behaviour.
- ImageNode : Added support for multi-view images.
  - ImageNodes can now output multiple "views". Views are effectively independent images, and may have separate data windows, formats, channels and metadata, and even be mixtures of deep and flat images.
  - The multi-view feature was originally intended for storing stereo renders, but may also may used for general processing where it is convenient to group multiple images into one stream.
  - A new `image:viewName` context variable specifies which view is currently being processed. This can be used to process each view with different settings, for instance via an Expression or Spreadsheet.
  - Multi-view images can be read from and written to EXR files via the ImageReader and ImageWriter nodes.
  - Added new nodes specifically for working with multi-view images :
    - CreateViews : For combining single view images into a multi-view image.
    - SelectView : For choosing one view from a multi-view image as a single view image.
    - CopyViews : For combining views from multi-view sources.
    - DeleteViews : For removing views from multi-view images.
    - Anaglyph : For viewing stereo images in a format appropriate for red-blue anaglyph glasses.
  - A new dropdown menu in the Viewer chooses which view is being displayed.
- ContextQuery : Added node to access a context variable value directly without needing to use an expression.

Improvements
------------

- Viewer : Improved accuracy of OpenColorIO display transforms when applied using the GPU.
- Outputs :
  - Added support for `layerName` string parameter, which can be used to customise the naming of channels in EXR outputs. Currently only supported for Arnold renders.
  - Added support for `layerPerLightGroup` boolean parameter, which automatically splits the outputs into separate layers, one for each light group.
- USD :
  - Added support for purpose-based material assignments in SceneReader and SceneWriter. To render or author such assignments, a ShuffleAttributes node must currently be used to shuffle to and from the standard shader attributes.
  - Added basic support for loading UsdLux lights. The data is available in Gaffer, but needs manual conversion to meet the requirements of a specific renderer.
- ImageReader/ImageWriter : Added support for JPEG 2000 (`.jp2`) images.
- Spreadsheet : Added `activeRowIndex` plug, which outputs the index of the currently active row.
- InteractiveArnoldRender : Added support for an `updateInteractively` bool parameter for render outputs. This can be used to request more frequent updates for AOVs other than the beauty image.
- ChannelPlugValueWidget : Improved the ordering of channel names presented in the menu.
- PresetsPlugValueWidget : The children of compound plugs are now shown when in "Custom" mode.
- LightEditor/SceneViewInspector : Improved performance when viewing complex scenes, by improving cache usage during history queries.
- Node menu : Removed unsupported Arnold shaders `ramp_rgb` and `ramp_float`. The OSL `ColorSpline` and `FloatSpline` shaders should be used instead.
- Image Channel Selectors : Channel names are now shown in "natural order". This means a numerical part of the name is compared numerically, instead of alphabetically (so "channel13" comes after "channel2").

Fixes
-----

- Seeds : Fixed point distribution generated on MacOS to match the point distribution generated on Linux.
- RenderController : Fixed duplicate `callback( Completed )` calls from `updateInBackground()` when priority paths are specified.
- PresetsPlugValueWidget/FormatPlugValueWidget : Fixed handling of evaluation errors (now turns red instead of failing to draw).
- ImageTestCase : Fixed bug in `assertImagesEqual()` where bad pixel data could go undetected when using `ignoreDataWindow`.
- Merge : Fixed rare failure to update when changing which channels existed on input.
- CollectScenes : An empty `rootNameVariable` value no longer causes the creation of a context variable named `""`. Instead, no context variable is created (but the scenes are still collected).
- TransformQuery : Removed unnecessary elements from hash.
- ViewportGadget :
  - Fixed bug which could cause `setCamera()` to emit `cameraChangedSignal()` even when the camera was unchanged.
  - Fixed `setCenterOfInterest()` so that it doesn't emit `cameraChangedSignal()` if the center of interest is unchanged.
  - Added GIL release in `setViewport()` Python bindings.
- AnimationEditor : Fixed glitches in the drawing of tangent handles during drags.
- ArnoldMeshLight : Fixed bug which caused `ai:autobump_visibility` attributes to be inadvertently modified.
- ArnoldShader/ArnoldLight : Fixed potential buffer overrun when loading color parameters with `gaffer.plugType` metadata.
- Plug :
  - The `removeOutputs()` method now also removes any outputs from child plugs. This is consistent with the `setInput()` method, which has always managed child plug inputs.
  - Fixed bug which meant that child output connections were not removed when a plug was removed from a node.
- Expression : Fixed error when updating an expression which was previously connected to a deleted spreadsheet row (#4614).
- ArnoldRender : Fixed rendering of single-channel AOVs specified using Gaffer's generic `float|int|uint <name>` syntax. Outputs specified using Arnold's `<name> FLOAT|INT|UINT` syntax will now issue a warning, and should be updated to use the generic syntax.
- Constraint : Restricted `targetVertex` to positive integers.
- ScriptContainer : Fixed `typeName()`, which was omitting the `Gaffer::` prefix.
- Text : Fixed wrapping bug that caused blank lines to be inserted if a single word was too long for the line.
- SceneReader : Fixed loading of USD asset paths containing `<UDIM>` tokens.

API
---

- ImageNode : Added virtual `hashViewNames()` and `computeViewNames()` methods which must be implemented by derived classes (unless an input connection is made for `out.viewNames`).
- ImagePlug :
  - Added `viewNames` plug for outputting the names of the views in an image.
  - Added ViewScope class for specifying the `image:viewName` context variable.
  - Added optional `viewName` arguments to the convenience accessors such as `channelNames()` and `channelData()`.
- ImageAlgo :
  - Added optional `viewName` arguments to `image()`, `imageHash()` and `tiles()`.
  - Added `viewIsValid()` function.
  - Added `sortedChannelNames()` function.
- PlugAlgo : Added optional `value` argument to `canSetValueFromData()`.
- RenderController :
  - Added Python bindings for optional `callback` argument to `update()` and `updateMatchingPaths()`.
  - Added Python binding for `updateInBackground()`.
  - Added `pathForID()`, `pathsForIDs()`, `idForPath()` and `idsForPaths()` methods. These make it possible to identify an object in the scene from a `uint id` AOV.
- TestCase : Added `assertNodeIsDocumented()` method.
- ImageTestCase : Added `metadataBlacklist` argument to `assertImagesEqual()`.
- MenuButton : Added `setErrored()` and `getErrored()` methods.
- SceneView :
  - Added `registerRenderer()` and `registeredRenderers()` methods. These allow any suitable `IECoreScenePreview::Renderer` to be used to draw the scene.
  - Added `renderer.name` plug to control which renderer is used.
  - Added `renderer.arnold` plug to control Arnold render settings.
- PlugLayout : Improved activator support. The `layout:activator` and `layout:visibilityActivator` metadata may now take boolean values to control activation directly. This is useful when an activator only applies to one plug, or it applies to several but depends on properties of each plug. String values are treated as before, referring to a predefined activator.
- ViewportGadget : Added a `CameraFlags` enum, which is used in `cameraChangedSignal()` to specify what aspects of the camera have changed.
- NodeAlgo : Added support for presets on compound plugs. If all child plugs have a particular preset then the parent plug is considered to have it too, and calling `applyPreset( parent, preset )` will apply it to all the children.
- Signals :
  - Added a new Signals namespace with Signal, Connection, ScopedConnection and Trackable classes. This provides significant performance and memory usage improvements over the old `boost::signals` library.
  - Removed usage of `boost::signals::detail::unusable` as a substitute for the `void` return type in the Signal bindings. Custom SlotCallers may now use a standard `void` return type.
  - The following signals now use a `CatchingCombiner` so that exceptions in one slot will not interfere with calls to other slots :
    - ApplicationRoot : ClipboardSignal.
    - GraphComponent : UnarySignal and BinarySignal.
    - Gadget : VisibilityChangedSignal, EnterLeaveSignal and IdleSignal.
    - Node : UnaryPlugSignal, BinaryPlugSignal, ErrorSignal.
    - ScriptNode : ActionSignal, UndoAddedSignal.
    - ViewportGadget : UnarySignal.
  - The following signals now handle exceptions thrown from C++ slots as well as Python slots :
    - Gadget : ButtonSignal, DragBeginSignal, DragDropSignal, KeySignal.
  - The following signals no longer suppress exceptions thrown from Python slots :
    - StandardSet : MemberAcceptanceSignal.
- Monitor : Subclasses may now override `mightForceMonitoring()` and `forceMonitoring()` in order to ensure the monitored processes always run, instead of being skipped when they are cached.
- ValuePlug : Added `hashCacheTotalUsage()` function.
- ScriptContainer : Added Python binding.
- Version.h : Added `versionString()` function.

Breaking Changes
----------------

- ImagePlug : The `image:viewName` context variable must now be set when evaluating plugs other than `viewNamesPlug()`. The `gui` app provides a default, but standalone scripts may need to be adjusted to specify `image:viewName` explicitly.
- ImageWriter/SceneWriter : The overrides for TaskNode virtual methods are now `protected` rather than `public`. Use the `TaskPlug` API instead.
- ShaderQuery : `addQuery()` now creates `query` and `out` plugs with numeric suffixes starting at 0 (rather than 1).
- TweakPlug and TweaksPlug :
  - Moved to `Gaffer` module.
  - Removed methods for tweaking shader networks.
  - Backwards compatibility is provided when loading old `.gfr` files.
- Arnold : Removed support for Arnold versions prior to 7.1.0.0.
- CollectScenes : Changed behaviour when `rootNameVariable` is empty.
- PopupWindow :
  - Removed `sizeMode` and `closeOnLeave` constructor arguments.
  - Removed visibility animation.
  - Removed drag&drop positioning.
- ViewportGadget : Added a `changes` argument to CameraChangedSignal.
- ImageReader : Changed the default interpretation of channel names in multi-part OpenEXR files. Set the `channelInterpretation` plug to `Legacy` to preserve the old behaviour.
- ImageWriter : Multi-part OpenEXR files are now written by default. Set the `layout` plug to `Single Part` to write a single-part file instead.
- SubTree : Removed the `/` root location from generated sets, because root membership is unsupported elsewhere in Gaffer.
- OSLShader : Removed `prepareSplineCVsForOSL()` method. Use `IECoreScene::ShaderNetworkAlgo::expandSplineParameters()` instead.
- ArnoldMeshLight : The `ai:autobump_visibility` attributes are no longer modified. Use a separate ArnoldAttributes node if necessary.
- Spreadsheet :
  - Renamed `activeRowNames` plug to `enabledRowNames`. Backwards compatibility is provided when loading old `.gfr` files.
  - Renamed `ui:spreadsheet:activeRowNamesConnection` metadata to `ui:spreadsheet:enabledRowNamesConnection`.
- Signals :
  - Replaced all usage of `boost::signals` with `Gaffer::Signals`. These are largely source-compatible, with the following changes :
    - Boost `snake_case` naming has been replaced with `CamelCase`.
    - Connection groups are not supported. Use `connectFront()` to connect in front of existing slots.
    - The Connection class has simple `setBlocked()/getBlocked()` accessors, rather than `block()/unblock()/blocked()` methods.
  - Removed the `Gaffer/BlockedConnection.h` header file. BlockedConnection can now be found in the Signals namespace provided by `Gaffer/Signals.h`.
  - Remove the `Gaffer/CatchingSignalCombiner.h` header file. CatchingSignalCombiner can now be found as `Signals::CatchingCombiner` in `Gaffer/Signals.h`.
  - Moved all Python classes into the `Gaffer.Signals` submodule.
  - Deprecated the default value for the `scoped` argument to `Signal.connect()`. Pass `scoped = True` to maintain the previous behaviour, or consider using an unscoped connection.
- ViewportGadget : Removed `RenderRequestSignal` type. Use the identical `UnarySignal` instead.
- Replaced all usage of `boost::optional` with `std::optional`.
- Random : Renamed `contextEntry` plug to `seedVariable`. Old `.gfr` files will be converted automatically on loading.
- SceneAlgo : Removed `historyIDContextName()` function. `history()` no longer uses an ID in the context to ensure fresh evaluations, it instead uses `Monitor::forceMonitoring()` to temporarily disable caching.

Build
-----

- Moved minimum required C++ standard to C++17.
- Updated to GCC 9.3.1 for Linux builds.
- Updated to GafferHQ/dependencies 5.0.0 :
  - Alembic : Updated to version 1.8.3.
  - Blosc : Updated to 1.21.1.
  - Boost : Updated to version 1.76.0.
  - CMark : Updated to 0.29.0.
  - Cortex : Updated to 10.4.0.0.
  - CMark : Updated to 0.29.0.
  - HDF5 : Updated to 1.12.0.
  - LibFFI : Updated to 3.4.2.
  - LibPNG : Updated to 1.6.37.
  - LLVM : Updated to version 11.1.0.
  - OpenColorIO : Updated to version 2.1.1.
  - OpenJPEG : Added version 2.4.0.
  - OpenImageIO : Updated to version 2.3.11.0.
  - OpenShadingLanguage : Updated to version 1.11.17.0.
  - OpenSSL : Updated to 1.1.1i.
  - OpenVDB : Updated to version 9.1.0, and added nanovdb.
  - PySide : Updated to 5.15.4.
  - Python : Updated to 3.8.13 (MacOS only).
  - Qt : Updated to 5.15.4.
  - Subprocess32 : Now packaged as a regular module rather than as a `.egg` package.
  - TBB : Updated to version 2020.3.
  - USD : Updated to version 21.11.

0.61.14.7 (relative to 0.61.14.6)
=========

Fixes
-----

- Shape : Fixed unnecessary serialisation of internal connection.
- ScaleTool :
  - Fixed oversensitive scaling when zoomed out in the Viewer.
  - Prevented uniform scaling from becoming negative.

0.61.14.6 (relative to 0.61.14.5)
=========

Fixes
-----

- GraphEditor : Fixed handling of errors on `Dot.labelType` and `Dot.label` plugs.

0.61.14.5 (relative to 0.61.14.4)
=========

Fixes
------

- SceneReader : Fixed reading of primitive variables from UsdGeomPointInstancers.
- NoduleLayout : Fixed shutdown crashes triggered by custom gadgets implemented in Python.

Build
-----

- Updated to Cortex 10.3.7.2.

0.61.14.4 (relative to 0.61.14.3)
=========

Fixes
-----

- PathFilter : Improved positioning of PathFilters created by dropping paths onto a node.
- GraphEditor :
  - Improved handling of Backdrops when laying out nodes. Individual nodes are no longer pushed outside backdrops, and backdrops themselves are positioned as a group containing all their child nodes.
  - Improved positioning of pasted nodes, so that they are less likely to overlap with any node they are automatically connected to.

0.61.14.3 (relative to 0.61.14.2)
=========

Fixes
------

- Arnold : Fixed rendering error for cubic curves with Vertex interpolation Quatf primitive variables.
- ImageReader : Fixed reading of signed integer TIFF files, which were failing due to a missing colorspace configuration. Signed integer files are now assumed to contain linear data (#4772).

0.61.14.2 (relative to 0.61.14.1)
=========

Fixes
-----

- Animation : Prevented negative zero slope.
- Animation Editor :
  - Fixed glitch when dragging a tangent having an opposite tangent with (+/-) inf slope.
  - Fixed bug that caused exception to be raised when the parent node of an editable curve was removed.
  - Fixed bug that prevented signals from being disconnected when a key was deleted.

0.61.14.1 (relative to 0.61.14.0)
=========

Fixes
-----

- TweakPlug : Fixed loading of files saved from Gaffer 1.0.0.0 and above.
- ShaderQuery and ShaderTweaks : Fixed error `TypeError: object of type 'NoneType' has no len()` when clicking "Input" column of a shader row.
- OSLObject/OSLImage : Fixed bug which resulted in undefined values for derivatives.

0.61.14.0 (relative to 0.61.13.1)
=========

Improvements
------------

- Light Editor :
  - Added the ability to edit multiple values at one time. With multiple cells selected, pressing <kbd>Return</kbd> or <kbd>Enter</kbd> will open a popup to edit the values for all cells.
  - Added the ability to drag from a cell and drop that cell's value on an appropriate target.
  - Added the ability to select individual cells with the mouse and keyboard. Cells can be selected by clicking or using the up <kbd>&uarr;</kbd>, down <kbd>&darr;</kbd>, left <kbd>&larr;</kbd> and right <kbd>&rarr;</kbd> keys. For both the keyboard and mouse, holding <kbd>Control</kbd> toggles the next selection. Holding <kbd>Shift</kbd> range-selects the next selection.

Fixes
-----

- ShaderQuery :
  - Fixed bug when attempting to browse shader parameters for a non-existent location.
  - Fixed bug when attempting to use the context menu to set the name of the shader to query for a non-existent location.
- LightEditor : Removed non-functional "Name" column from Arnold section.

API
---

- PathListingWidget :
  - Deprecated `allowMultipleSelection` constructor argument. Use `selectionMode` argument instead.
  - Added modes to `selectionMode` allowing single and multiple cell selections.
  - `setSelection` and `getSelection` now accept and return different types depending on the `selectionMode`. For `Row` and `Rows` modes, a single `PathMatcher` object represents the selection for all columns, maintaining backwards compatiblity. For `Cell` and `Cells` modes, a list of `PatchMatcher` objects, one per column, represents the selection.
- PlugValueWidget : Added new exception types `MultipleWidgetCreatorsError` and `MultiplePlugTypesError`.

0.61.13.1 (relative to 0.61.13.0)
=========

Fixes
-----

- SelectionTool : Fixed bug where the drawing mode overrides (Wireframe, Solid and Points) were ignored when selecting objects. This could cause a wireframe (or invisible) object to be selected instead of the visible object behind it.
- StringPlug : Fixed crashes caused by incoming connections from StringVectorDataPlugs.
- SceneViewInspector : Fixed bug where a non-existent location's parameters were being inspected. This caused `Invalid child name` errors, typically when switching focus to a node where the currently selected locations didn't exist.

API
---

- StringPlug : Deprecated `precomputedHash` argument to `getValue()` method.

0.61.13.0 (relative to 0.61.12.0)
=========

Features
--------

- USDLayerWriter : Added a new node for baking the difference between two Gaffer scenes into a minimal USD layer on disk.
- USDAttributes : Added a new node for setting USD's `kind` and `purpose`.

Improvements
------------

- Light Editor : Added support for editing visualisation attributes of lights.
- CameraTweaks : Added `Create` mode. This should be used in preference to `Replace` mode when the parameter may not exist.
- PathFilter : Added the ability to select scene locations from currently selected filter entries.

Fixes
-----

- SceneWriter : Fixed bug which caused sibling locations to be reordered.
- ShaderQuery :
  - Fixed error `ShaderQuery : "outPlug" is missing` when promoting a child plug of a query to a `Spreadsheet`.
  - Adding a child plug of a query to a `Spreadsheet` now uses the default name for the spreadsheet column.
- Spreadsheet : Fixed missing `Remove` TweakPlug mode presets.
- SceneAlgo : Fixed `attributeHistory()` results involving an `AttributeTweaks` node with `localise` enabled.

API
---

- EditScopeAlgo : Added support for editing attributes.
- TweakPlug : Added `Create` mode.
- VectorDataWidget : Added `dataMenuSignal` for constructing the context menu. Classes can add their own slots to this signal to modify the context menu. Derived classes should use it in favor of `_contextMenuDefinition()`.

0.61.12.0 (relative to 0.61.11.0)
=========

Improvements
------------

- StringPlug : Added support for input connections from StringVectorDataPlugs. The string value is formed by joining the string array using spaces.
- StringVectorDataPlug : Added support for input connections from StringPlugs. The array value is formed by splitting the string on spaces.

Fixes
-----

- PlugLayout : Fixed visibility of collapsible layouts with nesting (#4694).
- Image Node Mix : Fixed incorrect results outside mask data window, and incorrect results when changing inputs.
- ColorSwatchPlugValueWidget : Fixed popup dialogue for plugs belonging to Tools.
- Spreadsheet : Fixed loading of files saved in Gaffer 0.62.0.0a2 and later.

0.61.11.0 (relative to 0.61.10.0)
=========

Features
--------

- AttributeTweaks : Added node to tweak scene location attributes.

Improvements
------------

- ShaderQuery and ShaderTweaks : Improved labels of menu items that open shader browsers by adding "..." to the item name.

Fixes
-----

- SetFilter : Fixed missing set names in `setExpression` context menu. Sets were being listed for nodes directly connected to the filter, but not for nodes downstream of an intermediate filter such as a UnionFilter (#2678).
- Fixed `NameValue` plugs having a `delete` menu item in their popup menu when they shouldn't. This was broken in 0.61.9.0.
- PythonEditor : Fixed autocompletion errors triggered by dictionaries with non-string keys.
- ColorChooserPlugValueWidget/ColorSwatchPlugValueWidget : Fixed handling of errors when computing the plug value.
- PlugAlgo : Fixed crash in `setValueFromData()` when setting the value of a BoxPlug (other than a Box2iPlug).

API
---

- TweakPlug : Added functor-based variation of `applyTweak` allowing greater control of how users get and set the data being tweaked. `TweaksPlug::applyTweaks` now uses that method and can be used as a reference implementation.
- ColorChooser/ColorSwatch : Added `setErrored()` and `getErrored()` methods.

0.61.10.0 (relative to 0.61.9.0)
=========

Features
--------

- Tools Menu : Added item to populate the Arnold GPU cache, which may improve startup times for GPU renders.

Improvements
------------

- Viewer : Tool hotkeys now work as toggles for non-exclusive tools. This is currently noticeable on the Camera Tool - pressing <kbd>T</kbd> again will deactivate it.
- ArnoldShader and ArnoldLight : Added activators and sections to the UI.
- ImageWriter : Options are only displayed for the file format being written. If the extension is unknown, all format options are shown.
- Light Editor : Added keyboard shortcuts for selected light.
  - <kbd>Alt+E</kbd> : Edit source node.
  - <kbd>Shift+Alt+E</kbd> : Edit tweaks node.
- Edit Menu : Added item to rename one or more selected nodes, with accompanying keyboard shortcut (#4286).
- Box : Rename plug dialogue now ensures names are valid as they are typed.

Fixes
-----

- ArnoldMeshLight : Fixed illumination from textured mesh lights. This was broken in 0.61.2.0.

API
---

- ArnoldShader : Added support for `gaffer.layout.activator` and `gaffer.layout.visibilityActivator` in `.mtd` files.
- PlugLayout : User interface sections are now hidden if all plugs in that section are hidden.

0.61.9.0 (relative to 0.61.8.0)
========

Features
--------

- ShaderQuery : Added new node for querying parameters from a shader at a location.

Improvements
------------

- USD :
  - Added support for reading `.usdz` files.
  - Added support for `doubleSided` attribute.
- ShaderTweaks : Added dialogue for choosing parameters to tweak instead of popup menus.

Fixes
-----

- USD : Fixed reading and writing of Color4f shader parameters.
- InteractiveArnoldRender : Fixed crash triggered by changing the filter on an ArnoldMeshLight.
- NodeEditor : Stopped applying "green dot" non-default plug annotations to output plugs.
- Dot : Fixed a case where adding a Dot node between a `BoxIn` node and a downstream node would reverse the input and output nodules' sides on the Dot.

API
---

- PlugAlgo :
  - Deprecated `extractDataFromPlug`. Use the equivalent `getValueAsData` instead.
  - Added `setValueFromData` to set the value of an existing plug.
  - Added `canSetValueFromData` to return whether or not a plug's value can be set from Data.
- PathColumn : Add color swatch to cells containing `Color3fData` or `Color4fData`.

Build
------

- Cortex : Updated to version 10.3.6.1.

0.61.8.0 (relative to 0.61.7.0)
========

Improvements
------------

- Profiling menu :
  - Added menu item to start the ContextMonitor for all nodes, not just the selected one.
  - Added "Clear Caches" menu item.

Fixes
-----

- ArnoldRender : Fixed volume motion rendering by setting `options.reference_time`. This had been broken by changes in Arnold `7.0.0.3`, but Arnold `7.1.0.0` or later is required for the fix to work.
- NameValuePlug : Fixed bug where making a connection by drag and drop would connect the `name` plug as well as `enabled` and `value`. This caused confusion because making connections like `overscanLeft -> overscanRight` on the StandardOptions node meant that _both_ plugs ended up specifying the left overscan option.

0.61.7.0 (relative to 0.61.6.0)
========

Improvements
------------

- Arnold : Added support for Arnold 7.1.
- SubTree : Added `inheritTransform`, `inheritAttributes` and `inheritSetMembership` plugs.

Fixes
-----

- ArnoldRender : Fixed crash caused by lights with a non-existent shader.
- TransformTool : Fixed glitch that could cause a more distant handle to be drawn on top of a closer one.
- CameraTool : Fixed bug which allowed a parent of the camera to be moved, instead of the camera itself. This was particularly evident when looking through a camera loaded from a SceneReader, where the entire scene would be moved unexpectedly.

0.61.6.0 (relative to 0.61.5.0)
========

Improvements
------------

- Viewer :
  - Added standard Top, Front and Side orthographic cameras, accessible from the Camera menu (#4523).
  - Clicking on the gnomon now toggles between the standard orthographic cameras and the perspective camera.
- CameraTool : The "dolly" operation (<kbd>Alt</kbd>+right-drag) no longer moves orthographic cameras (or distant lights) along their Z axis. This was confusing, as there was no visual feedback in the viewer due to the nature of the projection. Instead, dollying is disabled until such a time as the CameraTool can make appropriate aperture edits in the node graph.
- Spreadsheet : Improved drag and drop of lists of strings. <kbd>Shift</kbd> may now be held to add to the current list, and <kbd>Control</kbd> may be held to remove from the current list (#3894). This is particularly useful when a PathFilter has been added to a spreadsheet.
- USD :
  - Added support for SdfAssetPath attributes, which are now loaded as StringData attributes containing the resolved asset path.
  - Improved loading speed for stages where the same material is bound to many prims. This gives a 10x improvement when loading the Moana Island scene.

Fixes
-----

- GraphEditor : Fixed active-branch-highlighting bug, where newly created GraphEditors wouldn't update correctly until the focus node was set again.
- Spreadsheet : Fixed attempts to edit non-editable plugs when double-clicking on a boolean cell.
- MessageWidget : Modified so that we no longer trigger UI updates while handling messages. This fixes some weird behaviour in rare cases when UI elements were evaluated in the wrong context.
- ResamplePrimitiveVariables : Fixed vertex-to-varying and varying-to-vertex resampling of V2f primitive variables on CurvesPrimitives.
- Arnold : Fixed rendering of curves with V2f vertex primitive variables.
- USD : Fixed loading of materials containing shaders with exposed inputs.

API
---

- SpreadsheetUI : Added `addColumnButtonMenuSignal()`, which can be used to customise the column creation menu for spreadsheets.
- TextGadget :
  - Added Python binding for `setDimmed()`.
  - Added missing `getDimmed()` accessor.
- Pointer : Added `add` and `remove` pointers for use with `setCurrent()`.
- MessageWidget : We no longer update the UI immediately when a message is emitted on the UI thread. If you have a slow process that you want to receive messages from interactively, you should run it on a background thread (perhaps using BackgroundTaskDialogue). If you have old code that runs something slow on the UI thread, it will still run, but you will only see messages from it once it finishes.
- ViewportGadget :
  - Added const overloads of `getCenterOfInterest()` and `getMaxPlanarZoom()`. The non-const versions will be removed in a future version.
  - Added `setTumblingEnabled()` and `getTumblingEnabled()` methods.
  - Added `setDollyingEnabled()` and `getDollyingEnabled()` methods.
  - `cameraChangedSignal()` is now emitted by `setCenterOfInterest()` in addition to `setCamera()` and `setCameraTransform()`.

Build
-----

- Cortex : Updated to version 10.3.4.0.

0.61.5.0 (relative to 0.61.4.0)
========

Fixes
-----

- Spreadsheet : Fixed errors computing `resolvedRows` when the Spreadsheet contains a NameValuePlug (#4583).
- Viewer : Fixed points drawing mode for CurvesPrimitives.

API
---

- Tool : Added support for subclassing in Python.
- View : Added `tools()` method which returns a container of all connected Tools.
- Container : Added constructor with a `name` argument.
- PlugAlgo : Added support for NameValuePlug in `extractDataFromPlug()`.

Build
-----

- Cortex : Updated to version 10.3.3.0.

0.61.4.0 (relative to 0.61.3.0)
========

Features
--------

- FormatQuery : Added new node for querying the format of an image and outputting its displayWindow, pixelAspect, center and size.

Improvements
------------

- GraphEditor : The focus gadget is now toggled when the button is released rather than when it is pressed. This helps avoid accidental toggling when performing marquee selection.
- ErrorDialogue : Improved error text for SyntaxError exceptions, and added debug log messages containing Python stack traces.

Fixes
-----

- GraphEditor : Fixed bug which could prevent the active node highlighting updating when the focus node was deleted.
- InteractiveArnoldRender : Fixed warnings when editing a parameter of a light with a connected OSL shader.
- ScriptNode : Fixed bug which meant that `focusChangedSignal()` wasn't emitted when the focus node was deleted.
- Viewer : Fixed visualisation of IES lights.

0.61.3.0 (relative to 0.61.2.0)
========

Features
--------

- RandomChoice : Added new node for choosing a random value from a list of weighted choices.
- ArnoldImager : Added new node for adding Arnold imagers to the scene globals.

Improvements
------------

- LightEditor/SceneViewInspector : Improved performance when viewing complex scenes.
- GraphEditor :
  - The focus widget now ignores right clicks, avoiding situations where attempting to open a context menu could accidentally change focus.
  - Removed the focus widget from Expression, Random, Spreadsheet and Animation nodes.
- StandardAttributes : Added `attributes.displayColor` plug, for controlling the colour of objects in the Viewer.
- UI : The UI is now scaled automatically for high-resolution monitors on Linux (#2157). Set the `QT_ENABLE_HIGHDPI_SCALING` environment variable to `0` to disable.
- ArnoldOptions : Added `ignore_imagers` option.

Fixes
-----

- Viewer : Fixed gnomon, which went missing in Gaffer 0.61.0.0.
- PathListingWidget : Fixed hangs triggered by hiding a widget while Python-based columns were being queried.
- VectorDataWidget :
  - Fixed header visibility when `setHeader()` is called after construction.
  - Fixed errors displaying vectors of differing lengths. Note : it is not yet possible to _edit_ vectors of differing lengths.
- PrimitiveInspector :
  - Fixed errors displaying Constant primitive variables with differing array lengths.
  - Fixed header tooltip formatting to match the SceneInspector.
- LightEditor : Fixed column widths. This was only an issue in Qt 5.12 builds, not the official GafferHQ builds.
- USD :
  - Fixed `Failed to load attribute` warnings caused by attributes without an authored value.
  - Fixed loading of Houdini-style paired primitive variables used to represent varying-length-arrays per vertex/face.

API
---

- StandardNodeGadget : Added `nodeGadget:focusGadgetVisible` metadata.
- VectorDataPlugValueWidget :
  - Added support for showing plugs with children, with each child forming a column in the UI.
  - Added `vectorDataPlugValueWidget:elementDefaultValue` metadata, used to provide the initial
    value for newly added rows.

Build
-----

- Cortex : Updated to version 10.3.2.0.
- Arnold : Added source compatibility for Arnold 7.1.

0.61.2.0 (relative to 0.61.1.1)
========

Features
--------

- LightEditor : Added a new editor UI for inspecting and editing lights. This can be found in the tab next to the GraphEditor in the standard layouts.
- Cryptomatte : Added a new node to output a matte generated from IDs selected from Cryptomatte AOVs.
- USD : Added support for reading and writing shader assignments via UsdShade.

Improvements
------------

- NodeEditor : Added embedded colour choosers for all colour plugs. These can be shown and hidden by clicking on the slider icon.
- Spreadsheet/SceneViewInspector : Added embedded colour choosers to popup editor windows.
- CopyPrimitiveVariables : Added `prefix` plug, which applies a prefix to the names of the copied primitive variables.
- Rendering : Added `gaffer:version` metadata to the headers of all rendered images.
- PathListingWidget : Added subtle lines between columns.
- SceneViewInspector :
  - Updated to align colour scheme and interaction patterns with the LightEditor.
  - Reduced overhead when the Viewer is not visible in the UI.
- Spreadsheet : Improved interaction with read-only spreadsheets. Previously it was impossible to switch between sections or scroll the cells (#4529).
- Focus Node : Added <kbd>Alt+1</kbd>-<kbd>Alt+9</kbd> hotkeys for setting focus to a bookmark (also available in the "Edit/Assign Focus" menu).

Fixes
-----

- PathListingWidget :
  - Fixed the <kbd>Ctrl</kbd>+<kbd>A</kbd> shortcut for selecting all visible paths. This was broken since Gaffer 0.61.0.0.
  - Fixed the deprecated `getSelectedPaths()` and `getExpandedPaths()` methods in the case that the PathListingWidget's root isn't `/` (#4510).
- NodeEditor : Fixed subtle label alignment differences between plugs with default and non-default values.
- Instancer : Fixed RootsPerVertex mode in the case that the input object has no vertices. Previously an empty `prototypeRoots` variable would cause an unnecessary error in this case, which was incompatible with the output from DeletePoints.
- Viewer/HierarchyView : Fixed "Edit Source" operation when the source node is inside a Reference. Previously the Reference node was shown, but now the node itself will be (albeit in read-only form).
- ValuePlugSerialiser : Fixed crash if `valueRepr()` was called with a CompoundObject value and a null `serialisation`.
- Button : Fixed bug triggered by calling `setImage()` from within a `with widgetContainer` block.
- ArnoldRender : Stopped instancing of polygon meshes when both `ai:subdivide_polygons` and adaptive subdivision are on.
- GLWidget : Fixed bug which made overlays unresponsive on high resolution displays.
- CropWindowTool : Fixed bug (introduced in 0.61.0.0) which prevented the free drawing of a new crop region outside the current one (#4530).
- SceneViewInspector : Fixed excessive memory usage when viewing complex scenes.

API
---

- PlugPopup : Added new class for editing plugs in a popup window.
- ColorChooserPlugValueWidget : Added a new class to allow colours to be edited directly using a ColorChooser.
- ColorChooser : Added `setSwatchesVisible()` and `getSwatchesVisible()` methods.
- PathColumn : Added new class for adding custom columns to PathListingWidget.
- CatalogueUI :
  - Column subclasses may now define background colours and tooltips.
  - Deprecated IconColumn class.
- ShaderView : Added `deregisterRenderer()` method.

Build
-----

- Cortex : Updated to version 10.3.2.0.

0.61.1.1 (relative to 0.61.1.0)
========

Fixes
-----

- InteractiveArnoldRender : Fixed Arnold 7 crash when stopping a render with global AOV shaders.

0.61.1.0 (relative to 0.61.0.0)
========

Improvements
------------

- OSLCode : Improved error reporting for cases where empty `.oso` files are produced.

Fixes
-----

- HierarchyView : Fixed unwanted expansion when an item is selected.
- Viewer : Fixed scroll wheel handling for overlay widgets. In particular this means that the mouse wheel can now be used to scroll through the parameters of the scene inspector.
- GraphEditor : Fixed highlighting of input connections for promoted ArrayPlugs.
- BranchCreator : Fixed bug in bounding box computation which could cause excessive evaluation of the input scene.

API
---

- PathListingWidget : Added `columnAt()` method.

0.61.0.0
========

Features
--------

- Arnold : Added support for Arnold 7, including multiple simultaneous interactive renders. This is in addition to continuing support for Arnold 6.2 - the appropriate version of GafferArnold is chosen automatically on startup based on the `$ARNOLD_ROOT` environment variable.
- GraphEditor :
  - Added new "Focus Node" concept. Clicking on the top right of a node tags it as the focus node, and editors and viewers can be set to follow the focus node. This is useful when you have several viewers that you want to view the same node, but you don't want them to follow selection.
  - Nodes and connections which don't contribute to computing the Focus Node are now dimmed. This helps see what part of the graph is active, taking into account the current context.
- Image Viewer : Added Luminance option to the channel selection menu.
- Animation :
  - Added new "Cubic" and "Bezier" interpolation modes which will smoothly interpolate between key values. The shape of the interpolated curves can
    be controlled by adjusting the slope and scale of key tangents, which are displayed and can be interactively manipulated in the Animation Editor.
  - Added new user interface panel in the Animation Editor with controls for key value, time, interpolation mode and tangent slope, scale and tie mode.

Improvements
------------

- HierarchyView : Moved processing to a background thread, so that displaying slow scenes does not cause the HierarchyView to lock up the UI.
- GraphEditor :
  - Improved drawing performance for large node graphs. Gains of about 40% are typical, with much greater gains when looking at a small region of a large graph or performing selection tests (for example when hovering over something or dragging a connection).
  - Added support for middle-drag panning while dragging nodes and connections using <kbd>G</kbd>.
  - Made connections slightly more visible when zoomed out.
- Cancellation : Improved responsiveness of cancellation of tasks waiting on results from another thread.
- ImageReader : Channels from EXR subimages named `rgb`, `rgba` or `depth` (either uppercase or lowercase) are now loaded into Gaffer's primary image layer.
- PathFilter : Removed `scene:filter:inputScene` and `scene:path` variables from the context used to evaluate the `paths` plug. This improves performance in some scenarios, and prevents the creation of invalid filters where the paths themselves depend on the current scene location.
- Switch : Removed variables such as `scene:path` and `image:channelName` from the context used to evaluate the `enabled` plug. This improves performance in some scenarios, and prevents the creation of invalid switches.
- NodeEditor : Added option in node editor context menu to set interpolation of an animated value.
- Animation : Added new `ConstantNext` interpolation mode, evaluates to the value of the next key for all times greater than the time of the key.
- USD : Added support for loading constant primvars from non-geometric prims. These are represented in Gaffer as attributes with a `render:` prefix.
- Arnold : Added support for `render:` prefixed attributes. For example, a Color3f attribute called `render:displayColor` will be readable as `displayColor` from a `user_data_rgb` shader.

Fixes
-----

- PathListingWidget :
  - Fixed subtle bugs in the underlying Qt model, although they haven't been observed to cause problems in practice.
  - Fixed potential hangs when displaying Paths which launch threaded computes.
- Animation :
  - Fixed bug in `Key.setType()`. Previously it modified the value instead of the type.
  - Fixed crash when dragging multiple keys around in editor.
  - Fixed bug which resulted in preview key being incorrectly drawn at the origin.
  - Fixed bug that cleared key selection when selecting multiple curves via path listing or gadget.
  - Fixed bug when pressing <kbd>f</kbd> to frame viewport which resulted in a blank background in certain cases (#4410).
  - Inserting a new key in editor (Hold "Ctrl" and left click on curve) is now undone/redone as a distinct step.
  - Fixed bug when selecting curve for first time via gadget, keys appear, then disappear (#4443)
  - Fixed bug where curves would not become visible in gadget until the path listing expansion was changed (#4408)
- ParallelAlgo : Fixed deadlock in `callOnUIThread()`.
- NameSwitch : Fixed context management bug that allowed variables such as `scene:path` to leak into the context used to evaluate the `selector` plug.
- GafferTest.TestCase : Fixed `assertNodesConstructWithDefaultValues()` to recurse through all plugs.
- NodeBinding : Fixed bug that could cause type queries to fail if types derived from Switch or ContextProcessor were wrapped for subclassing in Python.
- Arnold : Fixed bug that prevented the type of a `user:` attribute from being changed during an interactive render.

API
---

- ScriptNode : Added focus node API.
- GraphComponent : Inlined `children()` method, yielding 20-40% improvements in various child iteration benchmarks.
- Gadget :
  - Added `layerMask()` and `renderBound()` virtual functions.
  - Added `BackMidBack` render layer.
- ViewportGadget :
  - Added `gadgetsAt()` overload which returns the gadgets rather than taking an output parameter by reference.
  - Added `gadgetsAt()` overload taking a raster space region (rather than position) and an optional layer filter.
  - Add support for Gadget's double click signal.
- PathListingWidget :
  - `setSortable()` and `getSortable()` are no longer deprecated. The underlying bug that made them unreliable
    has been fixed.
  - Path processing has been moved to a background thread. The API remains unchanged, but updates to the displayed
    data are made asynchronously with respect to calls to methods of the PathListingWidget.
- GafferTest.TestCase : Added `assertFloat32Equal()` function, raises AssertionError if two values do not compare equal after conversion to single precision float.
- GafferUITest.TestCase : Unexpected Qt messages are now reported as test failures.
- Context : Modified `ChangedSignal` to use a `CatchingSignalCombiner`, which prevents exceptions from one slot preventing the execution of another.
- Menu : callable passed as the "checkBox" parameter of a menu item can now return None.
- Path :
  - Added optional `canceller` argument to `isValid()`, `isLeaf()`, `propertyNames()`, `property()` and `children()` methods.
  - Added `cancellationSubject()` virtual function that must be implemented by any paths which access the node graph.
- ScenePath : Added support for cancellation of calls to `isValid()` and `children()`.
- FileSystemPath : Added support for cancellation of calls to `children()` and `property()`.
- PathFilter : Added support for cancellation of calls to `filter()`.
- Animation :
  - `curve.addKey()` and `key.setTime()` now return active clashing key
  - `curve.addKey()` now has optional remove parameter that defaults to true, if false active clashing key is not removed and becomes inactive.
  - `key.setTime()` will not remove active clashing key, instead it becomes become inactive. inactive key at old time becomes active.
  - Added `curve.removeInactiveKeys()` function, removes all the inactive keys parented to a curve.
  - Added `key.isActive()` function, returns true if key is parented to curve and is the active key at its current time.
  - Added `curve.insertKey()` functions, insert key at specified time with optionally specified value.
  - Added `curve.keyTimeChangedSignal()` function, returns a signal that is called when a key's time has changed
  - Added `curve.keyValueChangedSignal()` function, returns a signal that is called when a key's value has changed
  - Added `curve.keyInterpolationChangedSignal()` function, returns a signal that is called when a key's interpolation has changed
  - Added new api for cubic interpolation modes, key tangents and tie mode (see header `Animation.h` for full details)
- AnimationGadget :
  - Added `selectedKeys()` function, returns current set of selected keys.
  - Added `onTimeAxis()` function, returns true if specified line is over the time axis of the gadget.
  - Added `onValueAxis()` function, returns true if specified line is over the value axis of the gadget.

Breaking Changes
----------------

- ImageReader : Channels from EXR subimages named `rgb`, `rgba` or `depth` (either uppercase or lowercase) are now loaded into Gaffer's primary image layer.
- FilteredChildIterator/FilteredRecursiveChildIterator : Removed all namespace-level typedefs, which were deprecated in Gaffer 0.59.0.0. Use the class-level typedefs instead, for example `Plug::Iterator` in place of `PlugIterator`.
- Gadget :
  - Moved `render()` and `renderRequestSignal()` to ViewportGadget.
  - Removed `select()` method.
  - Replaced `hasLayer()` virtual function with `layerMask()`.
  - Added `renderBound()` virtual function.
  - Renamed `doRenderLayer()` to `renderLayer()`, and added new `renderReason` argument, which can be used to check for selection renders without needing to query `Selector::currentSelector()`.
- ViewportGadget : Deprecated old `gadgetsAt()` signature. Please use the new form instead.
- ArnoldOptions : Removed support for the `ai:ignore_motion_blur` option. Turn off the `sampleMotion` option using a StandardOptions node instead.
- DotNodeGadget and AuxiliaryNodeGadget now use more inherited functionality from StandardNodeGadget, which could cause problems if anyone has subclassed the gadgets
- Fullscreen hotkey is now <kbd>F11</kbd> instead of <kbd>`</kbd>.
- Removed support for linking editors (following the focus node replaces most practical uses of this feature).
- Animation :
  - Renamed `Type` enum to `Interpolation`.
  - Interpolation of a key now affects span to next instead of previous key.
  - Renamed Key's `set/getType()` accessors to `set/getInterpolation()`.
  - Renamed `Step` interpolation mode to `Constant`.
  - Removed customised Key equality operators, the default operators compare on object identity.
- Path : Added `canceller` arguments to virtual methods. Note that Python subclasses can be made compatible with both Gaffer 0.60 and 0.61 simply by adding a `canceller = None` argument.
- PathFilter : Added `canceller` argument to `doFilter()` method. Note that Python subclasses can be made compatible with both Gaffer 0.60 and 0.61 simply by adding a `canceller = None` argument.
- CopyAttributes : Removed backwards compatibility for accessing input and source scenes as `in[0]` and `in[1]` respectively. Use `in` and `source` instead.

Build
-----

- Updated to GafferHQ/dependencies 4.0.0 :
  - OpenVDB : Updated to version 8.1.0.
  - TBB : Updated to version 2020.2.
  - Qt : Updated to version 5.15.2.
  - PySide : Updated to version 5.15.2.
  - Cortex : Updated to version 10.3.0.0.

0.60.12.2 (relative to 0.60.12.1)
=========

Fixes
-----

- Instancer : Fixed RootsPerVertex mode in the case that the input object has no vertices. Previously an empty `prototypeRoots` variable would cause an unnecessary error in this case, which was incompatible with the output from DeletePoints.
- Viewer/HierarchyView : Fixed "Edit Source" operation when the source node is inside a Reference. Previously the Reference node was shown, but now the node itself will be (albeit in read-only form).
- ValuePlugSerialiser : Fixed crash if `valueRepr()` was called with a CompoundObject value and a null `serialisation`.

0.60.12.1 (relative to 0.60.12.0)
=========

Fixes
-----

- BranchCreator : Fixed bug in bounding box computation which could cause excessive evaluation of the input scene.

0.60.12.0 (relative to 0.60.11.0)
=========

Improvements
------------

- Animation : Added basic support for loading animation saved from Gaffer 0.61. Caution : `Bezier` and `Cubic` interpolation will be converted to `Linear`, because they are features available in Gaffer 0.61 only.

Fixes
-----

- SceneReader :
  - Fixed loading of indexed UVs from Alembic curves.
  - Fixed loading of custom attributes from USD files.
- SceneWriter : Fixed writing of indexed primitive variables to Alembic caches.

Build
-----

- Updated to GafferHQ/dependencies 3.2.0 :
  - Cortex : Updated to version 10.2.3.0.

0.60.11.0 (relative to 0.60.10.0)
=========

Improvements
------------

- ArnoldAttributes : Added control over Arnold's `polymesh.subdiv_frustum_ignore` parameter. This is accessible from the Subdivision section in the NodeEditor.

0.60.10.0 (relative to 0.60.9.0)
=========

Improvements
------------

- Backdrop : Added a dedicated title bar for selection and moving Backdrops. This is smaller but more obvious than the previous region, reducing the likelihood of accidental movement.
- NodeEditor : Added <kbd>Alt</kbd>+<kbd>E</kbd> and <kbd>Alt</kbd>+<kbd>Shift</kbd>+<kbd>E</kbd> shortcuts for editing source and tweak nodes respectively. These are similar to the equivalent shortcuts in the Viewer and HierarchyView, but pin an existing NodeEditor instead of creating a new one.
- Animation : Added compatibility for loading animation from Gaffer 0.61 where Step has been renamed to Constant.

Fixes
-----

- PrimitiveInspector : Fixed update when all primitive variables with a particular interpolation are removed.

0.60.9.0 (relative to 0.60.8.0)
========

Improvements
------------

- Viewer : Added settings to control aperture and clipping planes when looking through lights. This can be customised on a per-light basis using the new visualiser settings on the Light node.
- Light : Added visualiser settings to control aperture and clipping planes when looking through the light in the Viewer. These settings override the defaults specified in the Viewer itself.
- LightToCamera : Added `distantAperture` and `clippingPlanes` plugs.
- Arnold Render : Changed warnings for invalid mesh lights to be one descriptive warning per light, instead of repeating an unclear warning for every surface that links to the light.

Fixes
-----

- Viewer : Framing the scene while looking through a light no longer tries to frame the light itself.
- SceneReader : Fixed bug attempting to read unsupported custom attribute types from USD files. This caused an obscure `Cannot compute hash from a CompoundObject will NULL data pointers!` error, but now prints a warning instead.
- GafferTest.TestCase :
  - Fixed `assertNodesAreDocumented()` to work for Nodes with multiple base classes.
  - Fixed `assertTypeNamesArePrefixed()` to work for Nodes in Python submodules.

API
---

- GafferTest.TestCase : Added `plugsToIgnore` argument to `assertNodesConstructWithDefaultValues()`.
- OpenGLRenderer : The `gl:queryBound` command now supports an `omitted` parameter containing a PathMatcher with paths to skip when computing the bound.
- SceneGadget : Added new `bound( selected, omitted = nullptr )` signature, which allows certain paths to be omitted from the bound computation, with or without limiting to selection. The previous `selectionBound()` method is now deprecated.

0.60.8.0 (relative to 0.60.7.1)
========

Improvements
------------

- Catalogue : Added support for naming incoming images using a `catalogue:imageName` display driver parameter. The default `Interactive/Beauty` output now includes this parameter so that it can be specified via the Outputs node.

Fixes
-----

- OSL Expression : Fixed crash due to exception in upstream computation.
- OSLShader : Fixed loading of a further 85 MaterialX shaders which were renamed by https://github.com/AcademySoftwareFoundation/OpenShadingLanguage/pull/909.
- StandardNodeGadget : Changes to `nodeGadget:minWidth` metadata now take immediate effect in all GraphEditors.

0.60.7.1 (relative to 0.60.7.0)
========

Fixes
-----

- OSLShader : Fixed loading of `mx_invert_float` shaders. These were renamed to `mx_invert_float_float` in the OpenShadingLanguage project.
- PythonEditor : Fixed bug where the input widget didn't scroll to show the new line when <kbd>Return</kbd> was pressed.
- TypedObjectPlug : Fixed bug in the serialisation of some `IECore.CompoundObject` values (the necessary `import IECore` was sometimes missing). This was particularly likely to affect CustomAttributes nodes where the `extraAttributes` plug was used.

0.60.7.0 (relative to 0.60.6.1)
========

Improvements
------------

- Spreadsheet : The popup editor for lists of items (e.g. scene paths) is now at least as wide as the spreadsheet column itself.
- VectorDataWidget : Added <kbd>Backspace</kbd> shortcut for deleting the selected rows.
- GraphEditor : Simplified logic for drawing strike-throughs on disabled nodes. The strike-through is now only drawn for nodes which have a constant value for their `enabled` plug. This avoids blocking the UI waiting for computes that drive the `enabled` plug, and avoids erroneously drawing the strike-through when the appropriate context to evaluate the plug in is not known.
- Animation : Added compatibility for loading animation from Gaffer 0.61.

Fixes
-----

- Viewer : Fixed drawing of CoordinateSystems (bug introduced in 0.60.0.0).
- ErrorDialogue : Fixed Python 3 incompatibility in `displayException()`.

0.60.6.1 (relative to 0.60.6.0)
========

Fixes
-----

- Fixed crash triggered by cancellation of long running computes (bug introduced in Gaffer 0.60.6.0).
- Window : Fixed errors printed by floating child windows at shutdown (bug introduced in 0.60.3.0).
- GraphEditor : Fixed annotation drawing glitch triggered by annotations with empty text. Empty annotations are now ignored.

0.60.6.0 (relative to 0.60.5.0)
========

Improvements
------------

- Viewer : Added <kbd>PgDn</kbd> and <kbd>PgUp</kbd> hotkeys for switching to the previous and next image layer respectively.
- Shader : Added "label" blindData which should be used in preference to "gaffer:nodeName" blindData.
- ShaderAssignment : Added `label` plug to optionally override the shader's "label" blindData.

Fixes
-----

- Fixed crash that could be triggered by exceptions being thrown during parallel evaluation. This could potentially happen while rendering Instancers where some locations were invalid.

0.60.5.0 (relative to 0.60.4.0)
========

Improvements
------------

- PythonCommand : Added syntax highlighting and auto-complete.

Fixes
-----

- Instancer :
  - Fixed crash caused by engine being evicted from the cache.
  - Fixed crash caused by points disappearing within the shutter range.

0.60.4.0 (relative to 0.60.3.0)
========

Features
--------

- ArnoldAttributes : Added Displacement section with plugs for controlling Arnold's `disp_autobump` and `autobump_visibility` parameters.

Fixes
-----

- GraphEditor : The Dot created when you <kbd>Ctrl</kbd>+click on a connection is now selected automatically, so it can be repositioned by an immediate drag.
- MetadataAlgo : Numeric bookmarks are no longer loaded inside nodes with `childNodesAreReadOnly` metadata, to prevent them "stealing" bookmarks from other nodes. Previously this only applied to nodes inside References.
- Reference :
  - Moved the `childNodesAreReadOnly` metadata registration to the Gaffer module, so it applies even without `GafferUI` being imported.
  - Prevented `childNodesAreReadOnly` metadata baked into a referenced file from overriding the Reference node's own metadata.

Breaking Changes
----------------

- ArnoldDisplacement : Deprecated the `autoBump` plug, use `ArnoldAttributes.autoBump` instead.

Build
-----

- Updated to GafferHQ/dependencies 3.1.0 :
  - Fixed missing `ssl` module in Python 3 builds.
  - USD : Enabled OpenVDB support.
- Added `BOOST_PYTHON_LIB_SUFFIX` option. This matches the approach used in Cortex.

0.60.3.0 (relative to 0.60.2.1)
========

Features
--------

- Drag and drop : Added <kbd>G</kbd> hotkey for starting and stopping drags without using buttons on the mouse or stylus. This can be used for any drag and drop operation in Gaffer, including making connections in the GraphEditor. Press <kbd>G</kbd> to start a drag, and press <kbd>G</kbd> again to drop.

Improvements
------------

- PythonEditor :
  - Added syntax highlighting and tab completion.
  - Added <kbd>Ctrl</kbd> + <kbd>]</kbd> hotkey for indenting and <kbd>Ctrl</kbd> + <kbd>[</kbd> for unindenting the selection.
  - Added <kbd>Ctrl</kbd> + <kbd>/</kbd> hotkey for commenting and uncommenting the selection.
  - Added context menus to input and output widgets.
  - All Gaffer and IECore modules are now imported by default.
- UIEditor : Added syntax highlighting and tab completion to the code editor for button widgets.
- OSLCode : Added syntax highlighting.
- ImageMetadata : Added `extraMetadata` plug, which is useful for generating arbitrary metadata from an expression, and for using types which are not supported by the standard `metadata` plug (timecodes for instance).

Fixes
-----

- ImageReader/ImageWriter : The `name`, `oiio:subimagename` and `oiio:subimages` metadata items are now ignored because they are ambiguous, and caused ImageWriter to write incorrect images. The same information is available in Gaffer via the image's `channelNames`.

Fixes
-----

- GraphEditor : Fixed bug in <key>D</key> shortcut.

API
---

- CodeWidget : Added new class for displaying/editing code.
- PlugLayout : Added a warning for plugs that reference activators that have not been registered.
- ImageTestCase : Added `ignoreChannelNamesOrder` keyword argument to `assertImagesEqual()`. This defaults to `False`, maintaining the previous behaviour.
- MultiLineTextWidget : Added `cursorBound()` method.
- WidgetAlgo : `joinEdges()` now accepts an arbitrary list of widgets rather than requiring a `ListContainer`. In this case, the orientation must be passed as an additional argument.
- PythonEditor : Added a `namespace()` method, which returns the globals/locals used by `execute()`.

0.60.2.1 (relative to 0.60.2.0)
========

Fixes
-----

- Shader : Fixed metadata signalling performance issue that could cause very poor load times for scripts containing many Shader nodes.
- GraphEditor : Removed unnecessary metadata tracking overhead.

0.60.2.0 (relative to 0.60.1.0)
========

Features
--------

- UVSampler : Added a new node sampling primitive variables from specific UV positions on a source object.
- Saturation : Added a new node to adjust image saturation.  This could previously be done using the CDL node, but using a specific node is sometimes clearer.

Improvements
------------

- Render : In addition to the compute cache, the hash cache is now cleared prior to rendering.
- Spreadsheet : Added interim support for adding a `Spreadsheet::RowsPlug` to a custom node. The previous doubling up of columns on reload can now be avoided by registering `False` for the new `spreadsheet:columnsNeedSerialisation` metadata item.

Fixes
-----

- Viewer : Fixed bug which prevented the "Expand Selection Fully" operation from working.
- Timeline : Fixed errors when the end frame is the same as the start frame (#4294).
- GafferUI : Fixed edge artifacts when rendering transparent icons.
- Render : Added workaround for hangs caused by specific chains of Expressions being evaluated after completion of the render.
- NodeEditor : Fixed `Internal C++ object already deleted` errors in Python 3 builds.
- Merge : Fixed failure to update when only the dataWindow of an input changed.

Build
-----

- Cortex : Updated to version 10.2.2.0.

0.60.1.0 (relative to 0.60.0.0)
========

Features
--------

- AttributeQuery : Added a new node for querying the value of an attribute at a location.
- Constraint : New target modes constrain to a vertex id or uv coordinate.

Improvements
------------

- SceneReader/SceneWriter : Added limited support for reading and writing custom attributes via USD. Currently attributes are only supported if they are marked as `custom` in the USD file, and if their name contains a colon-delimited namespace, for example `custom int foo:bar = 10`.
- Spreadsheet :
  - Added tooltips for column headers and sections. These can be edited using the new "Set Description..."
    option in the right-click popup menus.
  - Removed distracting "rows" tooltip.
  - Added value tooltips for boolean cells.
  - Added "Empty" tooltip for empty array values.
  - Fixed status bar to use the custom column label if it exists.
- UVInspector : Added ability to drag and drop UV values out of the inspector.
- Process : Added warning messages for processes which don't respond promptly to cancellation.
- Expression : Added "Show Name" menu item to GraphEditor context menu.

Fixes
-----

- Render : Fixed typo and improved clarity of warning when a context variable can't be added to an image header.

API
---

- TextInputDialogue : Added `multiLine` constructor argument, to allow input of multi-line values.

Build
-----

- Cortex : Updated to version 10.2.1.0.

0.60.0.0
========

> Note : This version is built against Arnold 6.2.0.1, and is not compatible with earlier Arnold versions.

Features
--------

- Spreadsheet : Added drag and drop reordering of rows.
- InteractiveRender : Added support for motion blur.
- Profiling : Added "Tools/Profiling" menu to annotate nodes with performance metrics.

Improvements
------------

- Serialisation : Reduced script save times by around 50%.
- Cancellation : Improved responsiveness by supporting cancellation of long computes in the following nodes :
  - SceneReader
  - LevelSetOffset
  - MeshToLevelSet
  - Plane
  - Sphere
  - DeleteFaces
  - MeshDistortion
  - MeshTangents
  - MeshType
  - PrimitiveSampler
  - ResamplePrimitiveVariables
  - ReverseWinding
  - Seeds
- Expression :
  - Improved performance of Python expression evaluation when the same result is required in multiple threads. Specific expression benchmarks have shown a 10x speedup and some production scenes show an overall 15-30% improvement. Caution : This can expose pre-existing bugs in other nodes - see Breaking Changes for details.
  - Improved error message when Python expression assigns an invalid value.
- Numeric Bookmarks : Changed the Editor <kbd>1</kbd>-<kbd>9</kbd> hotkeys to follow the bookmark rather than pinning it (#4074).
- Editors : Simplified the Editor Focus Menu, removing some seldom used (but potentially ambiguous) modes (#4074).
- Timeline :
  - Added support for sub-frame dragging with a <kbd>Ctrl</kbd> modifier, and fixed snapping of the frame indicator for regular drag operations.
  - The current frame is now drawn next to the playhead.
- Increased image processing tile size from 64 pixels to 128 pixels. This reduces per-tile overhead on large images, dramatically increasing effective image performance in many cases.
- SceneNode/SceneProcessor : Enforced that the value of the `enabled` plug may not be varied using the `scene:path` context variable. Attempts to do so could result in the generation of invalid scenes. Filters are the appropriate way to enable or disable a node on a per-location basis, and should be used instead. This change yielded a 5-10% performance improvement for a moderately complex scene.
- OSLImage : Avoided some unnecessary computes and hashing when calculating channel names or passing through channel data unaltered.
- Context : Optimized `hash()` method, and reduced overhead in `EditableScope`.
- NameSwitch/Spreadsheet : Rows with an empty name are now treated as if they were disabled. See Breaking Changes for further details.
- ContextVariables : Improved performance by around 50%.
- FilterResults : Improved performance.
- SceneAlgo : Reduced threading overhead for `parallelProcessLocations()`, `parallelTraverse()` and `filteredParallelTraverse()`. This is particularly noticeable when visiting locations with many children.
- Set : Added wildcard support to the `name` plug.
- GraphEditor : Added tool menu with options to control visibility of annotations.
- Render : Improved scene generation times for renders that use `dispatcher.batchSize` to
  render multiple frames at once. Previously Gaffer's cache was cleared after scene generation
  on each frame, but this is now only done for single-frame batches.

Fixes
-----

- Instancer : Fixed variation of prototype root attributes using context variables.
- ScriptNode : Fixed bugs that allowed global variables to remain in the context after they had been disabled, renamed or deleted.
- SceneReader :
  - Fixed crash when reading Alembic caches with non-scalar `userProperties`.
  - Fixed crash when reading Alembic caches with invalid primitive variables.
- UDIMQuery and OSLImage : Fixed incorrectly isolated TBB which could cause hang when other nodes use Standard cache policy. Now uses TaskCollaboration to improve performance.
- Wrapper : Removed the `PYTHONHOME` environment variable. This fixes problems running Gaffer in python-enabled versions of `gdb`.
- CompoundNumericPlug : Fixed serialisation of dynamic plugs with non-default interpretations.

API
---

- Context :
  - Refactored to allow EditableScope to avoid memory allocation where possible.
  - Added fast non-allocating `EditableScope::set( name, const T * )` overload. This should be used in preference to the old `set( name, const T & )` method.
  - Added `EditableScope::setAllocated()` method to replace the old `set()` method in the rare circumstance where allocation is required.
  - Added `variableHash()` method, which returns the hash for an individual variable.
  - Added `getIfExists()` method, which returns `nullptr` if a variable doesn't exist.
  - Added `getAsData()` method, which returns a copy of a variable as `IECore::Data`.
  - Added `TypeDescription` registration class, which must be used to register any custom data types used in context variables.
- GraphComponent : Added `reorderChildren()` and `childrenReorderedSignal()` methods.
- Serialisation : Added `addModule()` method, for adding imports to the serialisation.
- Slider :
  - Added optional value snapping for drag and button press operations. This is controlled via the `setSnapIncrement()` and `getSnapIncrement()` methods.
  - Added `setHoverPositionVisible()` and `getHoverPositionVisible()` accessors to control an optional position indicator drawn under the pointer.
- Expression : Added `Engine::executeCachePolicy()` method which must be implemented by subclasses.
- ImageAlgo : Added constants for the default channel names - `channelNameR` etc.
- SceneAlgo : Added optional `root` argument to `filteredParallelTraverse( scene, pathMatcher )`.
- MetadataAlgo :
  - Added optional `user` argument to `addAnnotationTemplate()`.
  - Added optional `userOnly` argument to `annotationTemplates()`.
- AnnotationsGadget : Added `setVisibleAnnotations()` and `getVisibleAnnotations()` methods to allow filtering of annotations.
- MonitorAlgo : Added `removePerformanceAnnotations()` and `removeContextAnnotations()` methods.
- Deformer : Added `affectsProcessedObjectBound()`, `hashProcessedObjectBound()` and `computeProcessedObjectBound()` virtual
  methods. These can optionally be overridden by derived classes to compute faster approximate bounds where possible.

Breaking Changes
----------------

- NameSwitch/Spreadsheet : Rows with an empty name are now treated as if they were disabled. Previously they would cause confusion by being matched against empty selectors. Use the default row for empty selectors instead, or alternatively use a catch-all `*` row.
- Context :
  - Removed `Ownership` enum. The copy constructor now always performs a full copy.
  - Removed `changed()` method.
  - Removed `_copy` argument from `get()` Python binding.
- Slider/NumericSlider :
  - Refactored Slider to provide all the functionality of NumericSlider, and removed NumericSlider.
  - Renamed initial constructor argument from `value` to `values`.
  - Removed `setPositions()/getPositions()` and `setPosition()/getPosition()` methods from `Slider`. Use `setValues()/getValues()` and `setValue()/getValue()` instead.
  - Removed `positionChangedSignal()` from `Slider`. Use `valueChangedSignal()` instead.
  - Removed `PositionChangedReason` from `Slider`. Use `ValueChangedReason` instead.
  - Removed `setPositionIncrement()/getPositionIncrement()` from `Slider`. Use `setIncrement()/getIncrement()` instead.
  - Replaced `_drawPosition()` method with `_drawValue()`.
- StandardOptions : Removed `cameraBlur` plug. This never functioned as advertised, as the regular `transformBlur` and `deformationBlur` blur settings were applied to cameras instead. As before, a StandardAttributes node may be used to customise blur for individual cameras.
- SceneAlgo :
  - Changed signature of the following methods to use `GafferScene::FilterPlug` : `matchingPaths`, `filteredParallelTraverse`, `Detail::ThreadableFilteredFunctor`.
  - Removed `filteredParallelTraverse()` overload which accepted a `Filter *`. Pass `filter->outPlug()` instead.
- DeleteFaces / DeletePoints / DeleteCurves : The PrimitiveVariable name is now taken verbatim, rather than stripping whitespace.
- Serialisation :
  - Disabled copy construction.
  - The following methods now take a `const object &` where they used to take `object &` :
    - `modulePath()`
    - `classPath()`
  - The following methods now take a `Serialisation &` argument where they used to take `const Serialisation &` :
    - `constructor()`
    - `postConstructor()`
    - `postHierarchy()`
    - `postScript()`
- ValuePlugBinding :
  - `repr()` now takes a `Serialisation *` where it used to take a `const Serialisation *`.
  - `valueRepr()` now has an optional `serialisation` argument.
- Metadata : Renamed signal types :
  - `NodeValueChangedSignal` -> `LegacyNodeValueChangedSignal`
  - `PlugValueChangedSignal` -> `LegacyPlugValueChangedSignal`
  - `NodeValueChangedSignal2` -> `NodeValueChangedSignal`
  - `PlugValueChangedSignal2` -> `PlugValueChangedSignal`
- MetadataBinding :
  - Added `serialisation` required argument to `metadataSerialisation()`.
  - Removed `metadataModuleDependencies()` method. Module dependencies are now declared automatically by `metadataSerialisation()`.
- Editors : Removed the 'Follow Scene Selection' mode from the Node Editor Focus menu (#4074).
- GafferSceneUI : Removed `SourceSet`.
- ScriptNode : Added private member data.
- Expression : Changed the Python expression cache policy to `Standard`. This executes expressions behind a lock, and can cause hangs if buggy upstream nodes perform TBB tasks without an appropriate `TaskIsolation` or `TaskCollaboration` policy. In this case, the `GAFFER_PYTHONEXPRESSION_CACHEPOLICY` environment variable may be set to `Legacy` or `TaskIsolation` while the bugs are fixed.
- Node : Removed `plugFlagsChangedSignal()`. We aim to phase flags out completely in future, and none of the current flags are expected to be changed after construction.
- ContextProcessor : Added `storage` argument to `processContext()` method.
- FilteredChildIterator/FilteredRecursiveChildIterator : Annotated all namespace-level typedefs with `[[deprecated]]`. These were already documented as deprecated in Gaffer 0.59.0.0, but their use will now trigger compiler warnings. Please use the class-level typedefs instead, for example `Plug::Iterator` in place of `PlugIterator`.
- RendererAlgo : Removed from the API. The render adaptor registry and `applyCameraGlobals()` are still available, but have been moved to SceneAlgo.
- MonitorAlgo : Removed deprecated `annotate()` overloads. Source compatibility is retained.
- Instancer : Attributes from the prototype root are now placed at the instance root, rather than on the instance group. This allows context variation to potentially vary these attributes. Usually attribute inheritance will mean that this behaves the same, but scenes which explicitly override attributes at specific locations in the hierarchy after an instancer could see modified behaviour.
- PointsGridToPoints : Changed default value of `filter` input, so that a filter must now be connected to specify the objects to modify.
- GafferVDB : Changed base class of the following nodes :
  - LevelSetToMesh
  - MeshToLevelSet
  - LevelSetOffset
  - PointsGridToPoints
- LevelSetToMesh : Changed default value for `adjustBounds` plug.

Build
-----

- Moved minimum required C++ standard to C++14.
- Moved minimum required TBB version to 2018 Update 3.
- Dependencies : Updated to GafferHQ/dependencies 3.0.0 :
  - USD 21.05.
  - OpenImageIO 2.2.15.1.
  - OpenShadingLanguage 1.11.14.1.
  - LibTIFF 4.1.0.
  - LLVM 10.0.1.
  - OpenVDB 7.2.2.
  - Cortex 10.2.0.0.

0.59.9.5 (relative to 0.59.9.4)
========

Fixes
-----

- OSL Expression : Fixed crash due to exception in upstream computation.

0.59.9.4 (relative to 0.59.9.3)
========

Fixes
-----

- Reference : Added support for Spreadsheets promoted inside another plug.

0.59.9.3 (relative to 0.59.9.2)
========

Fixes
-----

- Shader : Fixed metadata signalling performance issue that could cause very poor load times for scripts containing many Shader nodes.
- GraphEditor : Removed unnecessary metadata tracking overhead.

0.59.9.2 (relative to 0.59.9.1)
========

Fixes
-----

- Merge : Fixed failure to update when only the dataWindow of an input changed.

0.59.9.1 (relative to 0.59.9.0)
========

Fixes
-----

- ArnoldShader : Fixed loading of shaders with matrix outputs.

0.59.9.0 (relative to 0.59.8.0)
========

Features
--------

- TransformQuery : Added a new node to query the transform for a scene location.
- BoundQuery : Added a new node to query the bound for a scene location.
- ExistenceQuery : Added a new node to query whether a scene location exists.

Improvements
------------

- OSLShader : Reduced loading times where many nodes reference the same shader.
- Spreadsheet : Added `activeRowNames` plug to the Node Editor UI, in the Advanced tab.

Fixes
-----

- ArnoldMeshLight : Fixed label for `cameraVisibility` plug.

Documentation
-------------

- Fixed code samples in "Tutorials : Querying a Scene".

0.59.8.0 (relative to 0.59.7.0)
========

Features
--------

- Viewer : Added multiple color inspectors. <kbd>Ctrl</kbd>+click on an image
  to create a pixel inspector, or <kbd>Ctrl</kbd>+drag to create an area
  inspector. The image footer now shows the results from all your inspectors,
  and allows you to add or delete them.
- FilterQuery : Added a new node for querying the results of a filter at a specific location.
- GraphEditor : Added "Annotate..." item to the node context menu. This can be configured with
  multiple annotation templates using the `MetadataAlgo` API.

Improvements
------------

- Set : Added `setVariable` plug to allow the input filter to be varied depending on the set name.
- TabbedContainer : Added menu button to allow selection of tabs that are not
  visible due to a lack of horizontal space.

Fixes
-----

- Arnold : Fixed rendering of encapsulated objects for which automatic instancing
  is not possible. Examples include curves with non-zero `ai:curves:min_pixel_width`
  and meshes with non-zero `ai:polymesh:subdiv_adaptive_error`.
- PlugValueWidget : Fixed bug that tried to update the widget before all graph edits were complete.
- GraphEditor : Fixed framing of nodes dropped into the editor. This was incorrect when the editor was
  not at the default zoom.
- OSL Constant : Fixed usage as a surface shader in Arnold.

API
---

- Context :
  - Added forwards compatibility for methods added to provide enhanced
    performance in Gaffer 0.60. This allows the same code to be compiled for
    both Gaffer 0.60 and Gaffer 0.59 (but with only the Gaffer 0.60 build
    benefiting from improved performance).
  - Added support for `IECore::InternedString` variables in `substitute()`.
- MetadataAlgo : Added functions for managing annotations on nodes.
- MonitorAlgo : Added `persistent` argument to `annotate()` functions.

0.59.7.0 (relative to 0.59.6.0)
========

Improvements
------------

- Parent :
  - Added `parentVariable` plug, to create a context variable that passes the
    parent location to nodes upstream of the `children` plug. This allows the children
    to be varied procedurally according to what they are parented to.
  - Added `destination` plug, to allow children to be placed elsewhere in the scene
    while still inheriting the transform of the "parent". This is particularly useful
    when parenting lights to geometry.
- Seeds : Added `destination` plug, to control where the points are placed in the scene
  relative to the meshes they are generated from.
- Duplicate :
  - Added `filter` input, allowing multiple objects to be duplicated at once.
  - Added `destination` plug, to control where the copies are placed relative to the
    original.
  - Improved performance for large numbers of copies.
  - Deprecated the `target` plug. Please use filters instead.
- Outputs : Reduced the time taken to show the NodeEditor by around 90%.
- NodeEditor : The "Node Name" label is now draggable. For instance, it can be dragged to the PythonEditor to get a reference to the node or to the GraphEditor to find the node in the graph.
- GraphEditor : Improved framing of nodes dragged and dropped onto the GraphEditor :
  - Changed pointer to indicate that framing will take place.
  - Nodes are framed directly under the pointer instead of at the centre of the widget.
  - Fixed framing of nodes not currently in the GraphEditor.
  - Removed framing of _plugs_ dragged to the GraphEditor. This was unintuitive and interacted poorly with the dragging of plugs to make
    connections. The NodeEditor's "Node Name" label can be dragged instead to locate a node from the NodeEditor.
- SceneInspector : Improved history view :
  - Added the full path to nodes so that nodes nested in Boxes can be identified.
  - Added edit button to open a NodeEditor for nodes in the history.
  - Fixed gap in between sections.
- FilterResults : Added `root` plug. This can be used to limit the results to `root` and its descendants.
- CollectScenes : Added tab completion and a scene browser to the UI for the `sourceRoot` plug.
- BackgroundTaskDialogue :
  - Removed focus from "Cancel" button to make it harder to cancel accidentally.
  - Added <kbd>Esc</kbd> cancellation shortcut.

Fixes
-----

- Widget : Fixed drag handling bug that could cause `dragEnterSignal()` to be emitted again on a widget that had already accepted the drag.
- FilterResults : Fixed bug handling matches at the root location.
- NodeEditor : Fixed activator and summary updates which were skipped if the layout was not visible when the node was edited.
- Dispatcher : Fixed dispatching when `dispatcher.batchSize` or `dispatcher.immediate` are driven by context variables.
- SceneNode : Fixed bug hashing the transform for the root location.

API
---

- SceneAlgo :
  - Added overloads with `root` argument for `parallelTraverse()`, `filteredParallelTraverse()`, `matchingPaths()` and `matchingPathsHash()`.
  - Deprecated `matchingPaths()` overloads taking `Filter *`. Pass a `Filter.out` plug instead.
  - Added Python bindings for `matchingPathsHash()`.
- ScenePlug :
  - Added support for `..` in `stringToPath()`.
  - Added `stringToPath()` and `pathToString()` overloads that return a result rather than passing it by reference.
- GafferUI.FileMenu : Added `dialogueParentWindow` argument to `addScript()`.
- Spreadsheet : Added support for per-plug `ui:spreadsheet:selectorValue` metadata. This defines the initial value for `selector` when the UI is used to create a spreadsheet for the plug.

0.59.6.0 (relative to 0.59.5.0)
========

Improvements
------------

- CameraTweaks : Added support for Arnold's advanced camera parameters, including `shutter_curve`
  and `aperture_blades`.

Fixes
-----

- FileMenu : Fixed thread-safety bug in file save operation.
- TweaksPlugValueWidget : Fixed vertical alignment of `mode` widget.
- CameraTweaks : Fixed UI metadata.

API
---

- CameraTweaksUI : Added `registerTweak()` method.

Build
-----

- Cortex : Updated to version 10.1.5.0.

0.59.5.0 (relative to 0.59.4.0)
========

Improvements
------------

- Viewer : Added "Light Links" submenu with "Select Linked Lights" and "Select Linked Objects"
  operations.
- FileMenu : File loading and saving no longer locks the UI, and can be cancelled.
- MapProjection : Added `position` plug to allow a custom position to be used for the projection.
- Spreadsheet :
  - Added `resolvedRows` output plug, containing the resolved cell values
    for all active rows. This allows expressions to work with all the data in the spreadsheet,
    independently of the `selector` mechanism.
  - Added <kbd>+</kbd> button for adding new columns directly. Existing plugs may be dragged on
    to it and new plugs can be created from a popup menu.
- CustomOptions : Added `extraOptions` plug to facilitate the creation of dynamic numbers of options
  from a single expression.
- Outputs : Added `motionvector` preset for Arnold.

Fixes
-----

- Instancer : Fixed crash evaluating `variations` when there are no prototypes.
- ArnoldRender : Fixed rendering with `StandardOptions.sampleMotion` off. This now controls Arnold's `options.ignore_motion_blur` parameter, where previously it set the shutter duration to `0`.
- EventLoop : Fixed rare failures in `executeOnUIThread()`. Symptoms included a failure to display
  updates from interactive renders.
- Prune : Fixed bounds computation in the case that the filter claims to match descendants that don't
  exist. A common cause was the usage of `...` or a non-existent path in a PathFilter.
- ImageGadget : Fixed bug which prevented `stateChangedSignal()` from being emitted when
  `setPaused( false )` was called.
- InteractiveRender : Fixed error handling during render startup. Errors are now shown in the render
  log and the terminal output.
- ShaderView : Pausing the viewer now stops the renderer.
- Expression : Fixed OSL expression parsing bug triggered by plug names which were
  prefixes of other plug names. This caused a very confusing `Syntax error: syntax error`
  error.
- ExtensionAlgo :
  - Fixed copy/paste of nodes exported by ExtensionAlgo (#3886).
  - Fixed bug which prevented the use of internal Expression nodes.

API
---

- BackgroundTaskDialogue : Added a new modal dialogue to assist in running tasks in the background.
- EventLoop : Added `BlockedUIThreadExecution` context manager.
- ScriptNode : Added support for cancellation of execution and serialisation.
- ValuePlug : Improved warning emitted if cached value has unexpected type.
- SceneAlgo : Added `linkedLights()` and `linkedObjects()` functions.
- ImageView : Added `imageGadget()` accessor.

0.59.4.0 (relative to 0.59.3.0)
========

Features
--------

- Instancer : Added support for generating procedural variation via context variables.
  - Time offsets for animation.
  - Seeds for randomisation.
  - Arbitrary context variables driven by primitive variables.

Improvements
------------

- FrameMask : Improved performance when dealing with long frame ranges.
- Node : Improved performance of type queries related to dispatch processes.
- FilterResults :
  - Added `outStrings` plug, which provides the result converted to a list of strings.
  - Improved performance of hash.
- PrimitiveInspector : Improved responsiveness by performing work in the background instead of locking the UI.
- Graph Editor : Prevented zooming in so far you can't see nodes.
- FileMenu : Increased the maximum number of items in the "Open Recent" menu to 25.
- StringPlug : Improved accuracy of hashes for strings not containing substitutions.

Fixes
-----

- Layouts : Fixed broken keyboard shortcuts in floating editors.
- EventLoop : Fixed potential problem with UI thread execution.

API
---

- SceneAlgo : Added `matchingPathsHash()` function.
- ViewportGadget : Added `setMaxPlanarZoom()` and `getMaxPlanarZoom()` methods to limit zooming in.

0.59.3.0 (relative to 0.59.2.0)
========

Features
--------

- MotionPath : Added a node to generate curves representing location transforms tracked over a frame range.

Improvements
------------

- ArnoldOptions :
  - Added `options.enableProgressiveRender` to allow progressive rendering to be disabled completely.
  - Added sensible min/max limits to `options.progressiveMinAASamples`.
  - Grouped interactive rendering options in a new section.
- CollectScenes : Added `mergeGlobals` plug. This allows the globals from all collected scenes to be merged, whereas before only the globals from the first scene were passed through.

Fixes
-----

- InteractiveArnoldRender : Fixed interactive updates to `ArnoldOptions.progressiveMinAASamples`.
- NodeEditor : Fixed width of widgets for integer plugs with minimum values that require more space than maximum values.
- Reference : Fixed bugs triggered by changing the number of columns in a referenced spreadsheet.
- NumericWidget : Fixed editing bug in Qt 5.12.
- Dispatch App : Fixed UI imports when not running in GUI mode.
- Op App : Fixed UI imports when not running in GUI mode.

API
---

- LayoutPlugValueWidget : Added support for `layoutPlugValueWidget:orientation` metadata, with values of either `vertical` or `horizontal`.
- SpreadsheetUI : Added `addRowButtonMenuSignal` to allow customisation of Spreadsheet row addition within the UI (#4123).

Build
-----

- Qt : Updated to version 5.12.10.

0.59.2.0 (relative to 0.59.1.0)
========

Improvements
------------

- ImageWriter : Added `openexr.dwaCompressionLevel` plug. This controls the size/quality tradeoff when using DWAA or DWAB compression.
- Reference : Rows may now be added to and removed from referenced spreadsheets. Initially this is only allowed if the spreadsheet was published without any rows, to avoid anticipated problems merging referenced rows and user-edited rows.
- Metadata : Reduced signalling overhead, particularly when loading a script while the UI is open. One benchmark shows a reduction of 97%.

Fixes
-----

- Reference : Fixed loss of additional CompoundDataPlug children during reloading.
- UIEditor : Fixed Python 3 compatibility in plug presets editor.
- NodeGadget : Fixed intermittent shutdown crash.
- Expression : Fixed handling of expressions which assign CompoundData to `Attributes.extraAttributes`.

API
---

- SetUI : Added `setMenuPathFunction()` & `getMenuPathFunction()` to allow Set names to be transformed before display in Gaffer menus.
- SceneView : Added support for adaptors registered via `RendererAlgo::registerAdaptor()`.
- RendererAlgo : Improved handling of null adaptors. These now issue a warning instead of causing a crash.
- Metadata : Added new signals which are emitted with per-node granularity. These provide significantly reduced overhead compared to _all_ metadata observers being notified of _all_ metadata changes.
- MetadataAlgo : Added `readOnlyAffectedByChange()` overload suitable for use with new metadata signals.

0.59.1.0 (relative to 0.59.0.0)
========

Features
--------

- Spreadsheet : Added support for drag and drop. Values and Plugs can be dragged from outside a Spreadsheet to a cell to set its value or connect to its value plug.
- Instancer : Added `encapsulateInstanceGroups` plug, which outputs the instances within capsules. This has the same performance benefits as using an Encapsulate node downstream, with the following additional benefits :
  - Significantly improved performance when the prototypes define sets. A benchmarch with 1 million instances saw set generation time go from 10s using a downstream Encapsulate node to 0.002s using `encapsulateInstanceGroups`.
  - Fewer unnecessary capsule invalidations, resulting in fewer interactive rendering updates.
  - Convenience.

Improvements
------------

- ArnoldRender : Added support for animated camera parameters, such as field of view.
- DeleteFaces/DeletePoints/DeleteCurves : Added `ignoreMissingVariable` plug which allows users to opt-out of errors.
- Constraint : Added `targetScene` plug, to allow constraining to locations in another scene.
- OSLObject :
  - Added support for connecting to the individual components of Vector, Point, Normal, UV and Color primitive variable inputs.
  - Added `prototypeIndex` to primitive variable creation menus.
- OSLImage : Added support for connecting to the individual components of channel inputs.
- SceneReader :
  - Added support for USD skinning and blendshapes, which are now applied automatically to meshes during loading.
  - Added interpolation for animated cameras loaded from Alembic caches.
  - PointsPrimitive variables with Varying interpolation are now conformed to Vertex interpolation on load. This is particularly helpful when loading points written from Houdini.
- SceneWriter : Added support for writing cameras to Alembic caches.

Fixes
-----

- Viewer :
  - Fixed bug that caused the Inspector to edit the wrong node when SetFilters were in use.
  - Fixed bugs when using the CameraTool to manipulate scaled cameras or lights. Note: the Viewport projection will no longer display the effects of scale or shear components in the view matrix.
- Widget : Fixed incorrect `ButtonEvent` coordinate origin for mouse signals under certain widget configurations.
- CatalogueSelect : Fixed broken presets for promoted `imageName` plugs.
- PlugAlgo : Fixed metadata handling when promoting plugs which were themselves promoted from the constructor of a custom node.
- NodeAlgo : Fixed corner case where a preset could be listed twice if it was specified by both `preset:<name>` and `presetNames`.
- GafferUI : Fixed incorrect Tree/TableView horizontal header height.
- Spreadsheet : Fixed bug that allowed values to be pasted onto plugs with inputs.
- Render/InteractiveRender : Fixed bug in light filter context handling. This could result in light filters not being linked to the correct lights, or cause exceptions during scene translation.

API
---

- M33fVectorDataPlug : Added new plug type for specifying arrays of 3x3 matrices.
- FilterPlug : Added `match` method to evaluate the filter for the specified `ScenePlug`.
- PlugAlgo :
  - `extractDataFromPlug()` now supports M33fPlug and M33fVectorDataPlug.
  - `promote()` allows metadata to be excluded from promotion by registering a `<metadataName>:promotable` metadata value of `false`.
- NodeAlgo : If an input plug does not have presets of its own, it now inherits them from its first output. This is particularly useful
  when promoting plugs which have dynamic presets which are computed on demand. Previously the presets would have been baked in
  to the promoted plug, but by preventing promotion using `presetNames:promotable = false` and `presetValues:promotable = false`
  the promoted plug can continue to use the dynamic presets.
- MetadataAlgo :
  - Added `copyIf()` function, to copy metadata matching an arbitrary predicate.
  - Deprecated the complex form of `copy()` in favour of a simpler overload and the new `copyIf()` function.
- ViewportGadget : `setCameraTransform` now properly removes scale and shear from the supplied matrix.
- RendererAlgo :
  - Added `objectSamples()` overload which fills `vector<ConstObjectPtr>` rather than `vector<ConstVisibleRenderablePtr>`.
  - Deprecated original `objectSamples()` method.

Build
-----

- Cortex : Updated to version 10.1.4.0.

0.59.0.0
========

This release provides substantial improvements to USD support, an upgrade to Qt 5.12, and builds for both Python 2 and 3.

> Caution :
>
> - The current plug values are now omitted when exporting a Box for referencing. See Improvements section for more details.
> - Serialisation fixes for dynamic TransformPlugs and Transform2DPlugs mean that files saved in Gaffer 0.59 may not load
>   in Gaffer 0.58. This only affects plugs with customised default values.

Features
--------

- Unencapsulate : Added new node to expand capsules created by Encapsulate back into regular scene hierarchy. This discards the performance advantages of working with capsules, but is useful for debugging, or when it is necessary to alter a capsule's contents downstream.

Improvements
------------

- USD :
  - Mesh : Added automatic conversion of USD's `st` primitive variables to and from Gaffer's `uv` primitive variable.
  - Curves : Added support for widths, type, wrap and basis.
  - Points : Added support for widths and ids.
  - Primitives :
    - Added support for normals, velocity and acceleration.
    - Added automatic conversion of USD's `displayColor` primitive variable to and from Gaffer's `Cs` primitive variable.
  - Camera : Added reading of cameras and the standard cameras set.
  - Instancing :
    - Improved interoperability with UsdGeomPointInstancers :
      - A new "usd:pointInstancers" set is automatically generated on reading, allowing a single Gaffer Instancer/SetFilter to target all point instancers.
      - Renamed point instancer primitive variables to align with the defaults on the Instancer node.
    - Improved performance and memory usage when reading scenes using USD's scenegraph instancing.
  - Attributes :
    - Added support for USD's visibility attribute, converting it to and from Gaffer's `scene:visible` attribute.
    - Added support for USD's `purpose` attribute, converting it to and from a `usd:purpose` string attribute in Gaffer.
    - Added support for USD's `kind` attribute, converting it to and from a `usd:kind` string attribute in Gaffer.
  - Sets :
    - All UsdCollections can now be loaded as Gaffer sets.
    - Gaffer sets are now written to standard UsdCollections, and not to an unusable default prim.
    - Substantially improved performance for both reading and writing.
  - Untyped prims are now loaded as empty locations instead of being ignored.
  - Improved warning logging.
- Box :
  - Improved strategy used for exporting for referencing. Before, the current values of the Box plugs were converted into the default values of the Reference during export. This was error prone as it was too easy to export new defaults after changing values for testing. We now export default values as they are, and omit current values completely. Two new menu items allow the default values to be authored explicitly from the current values at any time.
  - Added "Reset Default Values" item to NodeEditor tool menu. This sets the default values for all plugs from their current values.
  - Added "Reset Default Value" item to plug context menu. This sets the default value from the current value.
- ImageReader : Added initial support for reading RAW files.
- CustomAttributes : `extraAttributes` is now a CompoundObjectPlug, allowing it to define complex attribute values including shading networks.
- GraphEditor : Improved performance slightly for large graphs.
- Warp : Defaulted `useDerivatives` to off for nodes created via the UI. Using derivatives is only beneficial when the warp is highly anisotropic, and it has a significant performance impact.
- CopyChannels : Improved performance for the special case of a single input.
- Catalogue/Viewer : Improved tile throughput for interactive renders.
- Performance : Replaced standard memory allocator with [jemalloc](http://jemalloc.net/). Set `GAFFER_JEMALLOC=0` to disable this and use the standard allocator.
- Merge : Optimized image merging.  This has been tackled in several ways, with different levels of impact.  Some extreme cases, such as using a multiply to merge two large datawindows with little overlap, now produce much smaller data windows.  Other cases can benefit a lot from being able to pass through input tiles unmodified.  For cases without a huge shortcut, there is an approximately 20% speedup from lower level optimization.
- Checkerboard : Optimized image generation when rotation is 0.
- InteractiveRender : Added a warning when attribute edits require geometry to be regenerated, as this can have a performance impact. Examples in Arnold include subdivision changes or changes to attributes inherited by procedurals.
- NodeMenu : Removed Loop node. This node can have severe consequences for performance if used inappropriately. Depending on the use case, the Collect nodes and others often provide a more performant alternative. The Loop node can still be created via the scripting API, but we recommend you consider the alternatives and/or request advice before using it.
- TransformTool : Improved tool state messaging to include node names and/or paths.

Fixes
-----

- USD :
  - Fixed writing of animated creases and corners.
  - Fixed writing of animated sphere radius.
  - Fixed various animation reading bugs.
  - Fixed handling of interpolation for normals.
  - Fixed writing of indexed primitive variables to non-indexed USD attributes.
  - Fixed handling of GeometricInterpretation/Role.
- TransformTools : Fixed bug finding existing nodes inside EditScopes.
- Viewer : Fixed bug that caused mouse clicks in empty toolbar regions to be ignored.
- PlugAlgo/BoxIO : Fixed bug handling nested compound plugs.
- Resample : Fixed hash of intermediate `deep` plug.
- String matching :
  - Fixed erroneous matches in specific cases involving multiple space-separated patterns and the `*` wildcard.
  - Fixed severe performance problem caused by many `*` wildcards in space-separated match patterns.
- Box/Reference :
  - Fixed export and referencing of TransformPlugs with modified default values (#3946).
  - Fixed export and referencing of CompoundDataPlugs with modified default values (#3907).
  - Fixed loss of spreadsheet values when using "Duplicate as Box" (#3972).
  - Fixed export and referencing of SplinePlugs.
  - Fixed incorrect presentation of referenced CompoundDataPlugs (#4020).
- Encapsulate : Fixed incorrect motion blur when deformation blur is turned on for the Capsule itself (#3557).
- Spreadsheet : Fixed serialisation of default values which do not match those of the default row.
- Checkerboard : Checker colors are now exactly equal to the colorA and colorB parameters.  Previously, there were very tiny floating point errors which grew larger as the distance from origin increased.
- Transform2DPlug : Fixed serialisation of dynamic plugs, such as plugs promoted to a Box.
- SplinePlug : Fixed bug that meant `isSetToDefault()` could return true even if it had computed inputs. It now returns false in this case, and never triggers an upstream compute.

API
---

- Gadget :
  - Added `updateLayout()` virtual method to simplify implementation of container types.
  - Added `dirty()` method for finer grained tracking of changes than `requestRender()` provided.
  - Deprecated `requestRender()` method. Use `dirty()` instead.
- OSLShader : Added `registerCompatibleShader()` method to allow connections from non-OSL shaders
 to be made.
- ImageGadget : Added `tileUpdateCount()` and `resetTileUpdateCount()` methods. These are useful for measuring performance.
- TestRunner : Added `PerformanceScope.setNumIterations()` method.
- TestCase/TestRunner : The hash cache is now cleared before running each test.
- TransformPlug/Transform2DPlug : Added constructor arguments for specifying child plug default values.
- ValuePlug :
  - Added `defaultHash()` virtual method.
  - Added `dirtyCount()` public method.
- ValuePlugSerialiser :
  - Added `valueRepr()` method.
  - Added support for `valuePlugSerialiser:omitParentNodePlugValues` context variable. This is used for exporting Boxes for referencing, and by ExtensionAlgo.
- CompoundObjectPlug : AtomicCompoundDataPlugs are now accepted as inputs.
- ImageAlgo : `tiles()` now returns a top level dictionary containing all the tileOrigins as a V2iVectorData, and each channel as an ObjectVectorData of channelDatas with corresponding indices. This allows `tiles()` to run substantially faster, more than twice as fast if the input network is very cheap.
- ConfirmationDialogue : Added optional `details` constructor argument which accepts text to be shown in a collapsed "Details" section.
- Node :
  - Improved speed of `RecursiveIterator` and `RecursiveRange` for nodes.
  - Added new `GAFFER_NODE_DECLARE_TYPE` and `GAFFER_NODE_DEFINE_TYPE` macros. Subclasses should use these in preference to `GAFFER_GRAPHCOMPONENT_DECLARE_TYPE` and `GAFFER_GRAPHCOMPONENT_DEFINE_TYPE`.
  - Deprecated all namespace-level iterator typedefs for Node and its subclasses. Use the class-level typedefs instead.
- Plug : Deprecated all namespace-level iterator typedefs for Plug and its subclasses. Use the class-level typedefs instead.
- RendererAlgo :
  - Moved RendererAlgo bindings into a `GafferScene.RendererAlgo` submodule. The old names are provided for temporary backwards compatibility but are considered deprecated and will be removed in the future.
  - Added Python binding for `objectSamples()` function.
- SceneTestCase : Changed base class to ImageTestCase, to provide methods for comparing images.
- Capsule : Expiry is no longer detected based on the dirtyCount of the source scene. This removes a debugging tool that could be useful, but allows nodes that create Capsules to have more granular hashing behaviour. If the behaviour of the source scene is captured by a hash that can be used by the capsule, then we can reuse the capsule when that hash matches, and we don't need to invalidate if the capsule is changed back to a cached value.

Breaking Changes
----------------

- USD :
  - The `st`, `displayColor` and UsdGeomPointInstancer primitive variables have been renamed.
  - Removed reading/writing of `cortex:` prefixed attributes.
- Gadget : Added new virtual method and private member variables.
- ImageGadget : Removed/moved private member variables.
- OpenColorIOTransform : Made `transform()` method protected rather than public.
- BackgroundMethodTest : Removed public visibility from private `TestWidget` and `WaitingSlot`.
- Box : The current plug values are now omitted when exporting for referencing, rather than being transformed into new default values.
- Reference : Removed support for boxes exported prior to version 0.9.0.0.
- TransformPlug/Transform2DPlug : Added constructor arguments.
- ValuePlug : Added virtual method.
- ValuePlugSerialiser : Removed support for `valuePlugSerialiser:resetParentPlugDefaults` context variable.
- NameValuePlugValueWidget : Removed support for using the `Plug.Dynamic` flag to determine whether or not the `name` plug is shown. Use `nameValuePlugValueWidget:ignoreNamePlug` metadata instead.
- Attributes : Changed type of `extraAttributes` plug from AtomicCompoundDataPlug to CompoundObjectPlug.
- Light/Camera : Removed button for adding custom plugs in the "Visualisation" section.
- Metadata : Removed compatibility for loading graph bookmarks created in versions prior to 0.33.0.0. Resave the file from Gaffer 0.58.0.0 to preserve the bookmarks if necessary.
- RendererAlgo :
  - Objects which don't support deformation blur are now always sampled at the integer frame time. Previously they were sampled at shutter open time if deformation blur was turned on.
  - Changed type used to represent sample times from `std::set<float>` to `std::vector<float>`, to align with the `IECoreScenePreview::Renderer` API.
- Encapsulate : Removed private data member.

Build
-----

- Dependencies : Updated to version 2.1.1
  - Qt 5.12.8
  - Boost 1.68
  - Cortex 10.1.2.0
  - OpenEXR 2.4.1
  - Appleseed 2.1.0-beta
  - USD 20.11
  - OpenSSL 1.1.1h
  - See https://github.com/GafferHQ/dependencies/releases/tag/2.1.1 for full details.

0.58.6.7 (relative to 0.58.6.6)
========

Fixes
-----

- ArnoldMeshLight : Fixed label for `cameraVisibility` plug.

0.58.6.6 (relative to 0.58.6.5)
========

Fixes
-----

- Arnold : Fixed rendering of encapsulated objects for which automatic instancing
  is not possible. Examples include curves with non-zero `ai:curves:min_pixel_width`
  and meshes with non-zero `ai:polymesh:subdiv_adaptive_error`.

0.58.6.5 (relative to 0.58.6.4)
========

Fixes
-----

- Expression : Fixed OSL expression parsing bug triggered by plug names which were
  prefixes of other plug names. This caused a very confusing `Syntax error: syntax error`
  error.
- ExtensionAlgo :
  - Fixed copy/paste of nodes exported by ExtensionAlgo (#3886).
  - Fixed bug which prevented the use of internal Expression nodes.

0.58.6.4 (relative to 0.58.6.3)
========

Fixes
-----

- Layouts : Fixed broken keyboard shortcuts in floating editors.

0.58.6.3 (relative to 0.58.6.2)
========

Fixes
-----

- NumericWidget : Fixed editing bug in Qt 5.12.
- Dispatch App : Fixed UI imports when not running in GUI mode.
- Op App : Fixed UI imports when not running in GUI mode.

0.58.6.2 (relative to 0.58.6.1)
========

Fixes
-----

- NodeGadget : Fixed intermittent shutdown crash.

0.58.6.1 (relative to 0.58.6.0)
========

Fixes
-----

- Viewer :
  - Fixed bug that caused the Inspector to edit the wrong node when SetFilters were in use.
  - Fixed bugs when using the CameraTool to manipulate scaled cameras or lights. Note: the Viewport projection will no longer display the effects of scale or shear components in the view matrix.
- Render/InteractiveRender : Fixed bug in light filter context handling. This could result in light filters not being linked to the correct lights, or cause exceptions during scene translation.

API
---

- FilterPlug : Added `match` method to evaluate the filter for the specified `ScenePlug`.
- ViewportGadget : `setCameraTransform` now properly removes scale and shear from the supplied matrix.

0.58.6.0 (relative to 0.58.5.2)
========

Improvements
------------

- Spreadsheet :
  - Enabled cell selection, editing is now achieved with a double-click.
  - Added menu items to cells & defaults sections to copy/paste the enabled state and value(s) of selected cells.
  - Added menu items to the row names section to disable, copy/paste or delete the selected rows.
  - Added menu items to edit the values for all selected cells of the same type simultaneously.
  - Added menu items to the section chooser to quickly select a specific section.
- Stats app : Added `-serialise` argument to measure the time taken to serialise the script.
- Viewer : Improved highlighting of EditScope selector when an EditScope is active.

Fixes
-----

- Viewer :
  - Render controls should now work when viewing a render after it has passed through a compositing network, providing `gaffer:sourceScene` and `gaffer:isRendering` metadata is preserved (#3888).
  - Fixed corruption of the GL stack and potential crash caused by exceptions thrown during draw.
- SplinePlug :
  - Fixed bugs affecting default values. All child plugs are now at their default values following construction and following a call to either `setToDefault()` or `resetDefault()`.
  - Fixed bug that prevented a spline from being promoted to a Box if it had a non-default number of points. This also affected the use of a spline as the input to an Expression.
- LRUCache : Fixed bug which could cause hangs during scene generation (#4016).
- ArnoldShader : Moved the toon shader's `rim_light_tint` and `aov_prefix` parameters to appropriate sections in the UI.
- Attributes : Added support for loading `extraAttributes` values and connections from Gaffer 0.59 and above.
- Spreadsheet :
  - Fixed bug that caused sections to overflow the available space.
  - Fixed bug that prevented Set Expression helper menu items from appearing when accessed from a Spreadsheet cell.

API
---

- Catalogue : Added `gaffer:isRendering` metadata, set to `True` if the viewed image is still receiving data from a display driver.
- LRUCache : Added `getIfCached()` method.

0.58.5.2 (relative to 0.58.5.1)
========

Fixes
-----

- ArnoldAttributes : Fixed minimum value for `subdivIterations` plug. It is now `0` rather than `1`.
- Spline editor : Fixed bug that prevented dragging of spline points.

0.58.5.1 (relative to 0.58.5.0)
========

Fixes
-----

- Plug : Fixed performance regression in dirtiness handling vs version 0.57. This affected script saving performance and GraphEditor navigation performance in particular.
- ArnoldShader : Moved Arnold 6.1's new `standard_surface.dielectic_priority` parameter to the Transmission section of the UI.
- SpreadsheetUI : Fixed bug that prevented column headers from updating.

0.58.5.0 (relative to 0.58.4.0)
========

> Caution : A performance enhancement introduced in BranchCreator may reveal latent bugs in derived classes.
> If a derived class implements `computeBranchSet()` it is now essential that it also implements
> `computeBranchSetNames()` appropriately. It is no longer sufficient to rely on the set names existing on
> the main input.

Improvements
------------

- Stats app :
  - Added `-context` argument to specify additional context variables for the processes being measured.
  - Improved accuracy of timings produced by `-scene` and `-image`.
- CameraTool : Improved performance when moving lights/cameras in look-through mode.
- Instancer/Parent :
  - Improved performance when computing sets which do not exist on the prototypes/children.
  - Improved interactive performance by reducing likelihood of cache eviction for set hashes.
- SetFilter : Improved interactive performance for CameraTool/TransformTool by enabling use of cached values.

Fixes
-----

- Viewer :
  - Fixed bug that caused the Inspector to grow very wide when inspecting long strings.
  - Fixed bug that caused a second click to be required to apply edits when closing an Inspector edit window by clicking outside the popup.
- NumericPlugValueWidget : Fixed bug that caused plug values to be set to 0 if editing completed with invalid text.
- StringPlugValueWidget : Fixed bug that could cause plug values to be overwritten when editing multiple plugs and focus was lost without change, or the value state changed to mixed via external action.
- TypedObjectPlug : Fixed serialisation of values for which `repr()` is not available (#106).
- Editor : Fixed bug that caused child widgets to lose focus when the mouse re-enters an Editor that already has focus.
- Stats app : The `-canceller` argument is now honoured when using `-task` to measure task execution time.

API
---

- Serialisation : Added `objectToBase64()` and `objectFromBase64()` methods to provide base64 encoding and decoding for all `IECore::Objects`.
- NumericWidget : Fixed bug that caused `editingFinished` to be called with the wrong `reason` when the widget was left with an invalid value. `Invalid` is now passed in these cases.
- PlugValueWidget : Improved support for legacy widgets in `PlugValueWidget.create` when used to create widgets for single plugs supplied in a set.
- NameLabel : Added support for multiple graph components in the constructor, added `setGraphComponents`/`getGraphComponents` methods.
- LabelPlugValueWidget, NameValuePlugValuePlug : Added support for multiple plugs.
- SceneAlgo : Added Python binding for `historyIDContextName()`. Woe betide you if you find a need for it.

0.58.4.0 (relative to 0.58.3.2)
========

Improvements
------------

- Arnold Renderer : Improved performance when instancing large numbers of objects. A benchmark with 1 million instances shows a 25% reduction in scene generation time.
- Encapsulate : Fixed bugs in shader/attribute inheritance when rendering in Arnold (#3559).
- Arnold Renderer :
  - Fixed OSLShader connections between color components.
  - Fixed hangs when instancing the output of an Encapsulate node.
- CropWindowTool : Fixed error handling bugs.
- ImageReader : Fixed bug which caused fileName to be evaluated in unnecessary contexts.

0.58.3.2 (relative to 0.58.3.1)
========

Fixes
-----

- BranchCreator : Fixed bugs affecting set computation.

0.58.3.1 (relative to 0.58.3.0)
========

Fixes
-----

- Viewer : Fixed crash when viewing a rapidly changing monochrome image or soloed channel.

0.58.3.0 (relative to 0.58.2.0)
========

Improvements
------------

- Preferences : Added support for OpenColorIO context variables. These may contain references to Gaffer context variables via the standard `${variable}` syntax, but please note that such variables are only available in the Viewer and not in the rest of the UI (for instance, colour swatches and pickers).
- Viewer : Increased the size of transform tool handle hit areas.
- Arnold : Moved debug log messages into the Debug severity and added support for Memory and Timestamp options.

Fixes
-----

- Node Editor : Fix bug in section decoration when a plug was set to its user default.
- ErrorDialogue : Fixed extremely slow display of warning and error messages. This was particularly apparent when showing errors that occurred while opening files.
- Viewer : Fixed Default display transform so that it updates correctly when the default is changed via the Preferences dialogue, and when the context changes.
- UVView : Fixed a performance regression vs 0.57 when displaying many UDIM textures.
- OpDialogue, DispatchDialogue, ErrorDialogue : Fixed missing filtering controls for progress messages.
- Encapsulate : Fixed bug where globals and render sets were evaluated in the wrong context.
- OSLObject : Fixed invalid reads from Constant array primitive variables.
- PresetsPlugValueWidget/PlugValueWidget : Fixed bugs handling context-sensitive presets.

API
---

- MessageWidget : `setMessages()` now also accepts messages in the format used by IECore.CapturingMessageHandler.
- WidgetAlgo : Added `keepUntilIdle()` method.
- OpenColorIOTransform : Added `processor()` and `processorHash()` public methods.

0.58.2.0 (relative to 0.58.1.0)
========

Improvements
------------

- CollectScenes : Added support for collecting at roots of arbitrary depth.
- AttributeVisualiser : Added support for V2f, V3f, V2i, V3i, V2d and V3d data types.
- Node Editor : Added decoration to collapsed sections when any of their children have non-default values.
- HierarchyView : Added <kbd>Ctrl + C</kbd> shortcut/context menu action to copy the selected paths to the clipboard.
- UI : Added support for basic math operators (`+`, `-`, `/`, `*`, `%`) in numeric fields.

Fixes
-----

- PrimitiveInspector :
  - Fixed bug that caused data lists to lose their scroll position during updates.
  - Fixed bug that could cause the inspector to show a different location to other Editors.
  - Fixed bug when the selected location doesn't exist in the input scene.
- Attributes : Fixed bug that could prevent interactive updates when the `global` plug was on.
- CollectScenes : Fixed childNames hashing bug.
- NodeAlgo : Fixed bug that caused `isSetToUserDefault()` to return `True` when the plug's input was from a ComputeNode.
  Like `ValuePlug::isSetToDefault()`, `isSetToUserDefault()` will now never trigger a compute, and all computed inputs
  are treated as non-default.
- GafferArnold : Added missing GafferOSL Python bindings import.
- Plug : Fixed bug that could break IPR updates following a node graph edit (#3911).
- Viewer : Fixed CropWindow tool reset button size.

API
---

- OpenImageIOReader : Added methods for controlling the maximum number of images files to keep open at one time.

0.58.1.0 (relative to 0.58.0.1)
========

- Catalogue : Added <kbd>Ctrl-D</kbd> shortcut to duplicate selected images (#3545).
- Viewer :
  - Added <kbd>Ctrl-D</kbd> shortcut to duplicate currently viewed image when viewing the output of Catalogue node (#3545).
  - Added enabled/reset controls to the Crop Window Tool.
  - Improved display of the edited plug in the Inspector's pop-up edit windows.

Fixes
-----

- Viewer :
  - Fixed bug preventing the Inspector from finding shaders when assigned via a Switch.
  - Fixed bug that caused the wrong plug to be edited by the Inspector with nested EditScopes.
  - Fixed bug that prevented selecting an Edit Scope that contained other Edit Scopes.
  - Fixed bug that caused an exception when simultaneously editing multiple plugs the Inspector.
- Box : Fixed GIL management bug that could cause hangs when promoting a plug.
- SetFilter : Added missing set expression operators to node reference/tooltip.
- UIEditor : Fixed bug which allowed the creation of non-selectable presets.
- EditScopes : Fixed crash in `EditScope::processors()` if intermediate nodes had no corresponding input.
- ShaderAssignment : Fixed bug in `shader` plug connection acceptance that could cause crashes at shutdown.

API
---

- EditScopeUI : Added support for listing user nodes in the Edit Scope navigation menu when their `editScope:includeInNavigationMenu` metadata entry is set to `True`.
- CropWindowTool : Added `plug()` and `enabledPlug()` methods to return the currently edited plugs or `nullptr`.

0.58.0.1 (relative to 0.58.0.0)
========

Fixes
-----

- Catalogue : Fixed missing error icon.

Build
-----

- Fixed compilation with TBB versions prior to 2018 Update 1.

0.58.0.0
========

> Caution : References containing promoted Spreadsheets, when saved from Gaffer 0.58, can not be loaded in previous versions of Gaffer.

Features
--------

- InteractiveRender : Added message log to the node's UI, displaying output from the last render (#3419).
- Viewer : Added a floating inspector to allow quick inspection and editing of lights and other shaders (#3661).
- Viewer : Added GPU support for gamma/exposure and OCIO display transforms.

Improvements
------------

- Caching : Improved interactive performance using an improved hash cache invalidation strategy.
- SceneNode : Improved performance for all nodes that must propagate bounds from children to parents.
- PointsType : Removed unnecessary bounds computation overhead.
- OSLObject/ClosestPointSampler/CurveSampler : Improved performance for cases where multiple downstream computes require the same upstream object.
- Stats app : Added `-location` argument, to allow profiling of a single location in a scene.
- AnimationEditor : Improved performance.
- MessageWidget : Added alternate presentation options allowing log-style message display, search, etc.
- Viewer : Added warning/error message count to Render Control overlay.

Fixes
-----

- GraphEditor : Implemented undo for node drags (#423).
- Reference (#3810) :
  - Fixed bug which caused promoted Spreadsheet values to be lost when exporting a Box for referencing.
  - Fixed bug which caused promoted Spreadsheet cells to be duplicated by copy/paste.
  - Prevented addition and removal of rows and columns for promoted Spreadsheets, as changes will be lost when reloading the reference.
- DeleteSets : Fixed bug which allowed the deletion of Gaffer's internal `__lights`, `__cameras` and `__lightFilters` sets. These are now always preserved, because they are needed to output the scene for rendering.
- TransformTool :
  - Fixed handle orientation for transforms with negative scaling.
  - Fixed handle positions for locations with PointConstraints or ParentConstraints applied.
  - Fixed translation and rotation of locations with a ParentConstraint applied.
  - Fixed rotation of locations with negative scaling.
- ImageReader/ImageWriter : Fixed handling of errors in Python functions registered using `setDefaultColorSpaceFunction()`.
- StyleSheet : Fixed monospace font stack.
- GafferUI : Fixed lingering highlight state if a Button was disabled whilst the cursor was over it.
- Signal : Fixed hang which could occur if a result combiner implemented in Python tried to handle exceptions.
- NumericWidget : Fixed errors when trying to use a virtual slider with an empty value.
- GraphComponent : Fixed return value for `items()` method. The returned keys are now regular `str()` objects rather than `InternedString`.
- Fixed dependency tracking bugs in the following nodes :
  - UDIMQuery
  - Shader
  - FilterResults
  - FreezeTransform
  - ImageMetadata
  - FlatImageProcessor
  - FlatToDeep
  - OpenImageIOReader
  - LevelSetOffset
  - MeshToLevelSet
  - CopyPrimitiveVariables
  - CopyAttributes
  - SubTree
  - MergeScenes
  - CollectScenes
  - Instancer
  - Duplicate
  - ClosestPointSampler
  - CurveSampler
  - DeleteSets
- SetAlgo : Fixed `affectsSetExpression()` to return `True` for `ScenePlug::setNamesPlug()`.
- GafferTractor: Fixed evaluation of 'tag' and 'service' plugs on Task nodes. Previously, these plugs were evaluated in the default context, which prevented one from using custom context variables (e.g. from Wedge node) to compute tags or service keys dynamically.
- NodeEditor : Reduced layout flicker when switching between nodes.
- Spreadsheet : Fixed bug that could result in editor windows being placed partially off screen.
- ValuePlug : Fixed bug that could cause the wrong plug to be reported in `ProcessExceptions`.

API
---

- ValuePlug
  - Improved interactive performance by not clearing the entire hash cache every time a plug is dirtied. Beware : this can reveal subtle bugs in `DependencyNode::affects()` implementations, causing hashes to be reused if a plug has not been dirtied appropriately. These bugs may previously have gone unnoticed but will now need fixing as a matter of urgency. The GAFFER_HASHCACHE_MODE environment variable may be set to "Legacy" to enable legacy behaviour in the interim, or to "Checked" to enable a slow mode which throws exceptions at the source of hash cache cache errors caused by bad `affects()` implementations.
  - Added `clearHashCache()` static method.
  - Added `resetDefault()` method.
- ScenePlug :
  - Added `existsPlug()` accessor, and deprecated the argumentless overload of the `exists()` method.
  - Added `childBoundsPlug()`, `childBounds()` and `childBoundsHash()` methods.
- ObjectProcessor : Added `processedObjectComputeCachePolicy()` virtual method. This should be overridden to choose an appropriate cache policy when `computeProcessedObject()` spawns TBB tasks.
- SceneNode :
  - Deprecated `hashOfTransformedChildBounds()`. Use `ScenePlug::childBoundsHash()` instead.
  - Deprecated `unionOfTransformedChildBounds()`. Use `ScenePlug::childBounds()` instead.
- IECorePreview::Renderer : Added optional message handler to renderer construction to allow output message streams to be re-directed if required (#3419).
- InteractiveRender :
  - Changed base to `Gaffer::ComputeNode` (#3419).
  - Added messages plug containing the output of the node's renderer output (#3419).
- InteractiveRenderTest :
  - Scoped a `UIThreadCallHandler` for all test methods, available via `self.uiThreadCallHandler`.
  - Refactored `_createInteractiveRender` method to provide a default implementation that creates a render node with suitable error propagation.
- Graphics : Renamed `errorNotificationSmall` icon to `errorSmall`.
- NotificationMessageHandler : Constructor now accepts `GafferUI.MessageWidget` constructor kwargs to configure the widget.
- PlugValueWidget : Added the capability to edit more than one plug at a time.
  - Added `setPlugs()` and `getPlugs()` methods. The previous `setPlug()` and `getPlug()` methods remain as a convenience.
  - Derived classes should now override `setPlugs()` rather than `setPlug()`, but backwards compatibility is preserved for classes which have not been converted yet.
  - Derived classes should now implement `_updateFromPlugs()` rather than `_updateFromPlug()`, but backwards compatibility is preserved for classes which have not been converted yet.
  - `create()` now optionally accepts a list of plugs in place of a single plug.
  - Updated the following subclasses to fully support multiple plugs :
    - NumericPlugValueWidget
    - CompoundNumericPlugValueWidget
    - ColorSwatchPlugValueWidget
    - ColorPlugValueWidget
    - StringPlugValueWidget
    - TweakPlugValueWidget
    - BoolPlugValueWidget
    - PresetsPlugValueWidget
- SetAlgo : Added Python binding for `affectsSetExpression()`.
- Shader : Added `affectsAttributes()` protected method.
- MessageWidget :
  - Added MessageSummaryWidget class to simplify the display of message counts in other UIs.
  - Added `scrollToNextMessage()` and `scrollToPreviousMessage()` methods.
- MetadataAlgo : Added `readOnlyReason`, returning the outer-most `GraphComponent` that causes the specified component to be read-only.
- EditScopeAlgo : Added `prunedReadOnlyReason`, `transformEditReadOnlyReason` and `parameterEditReadOnlyReason` to determine the outer-most `GraphComponent` causing and edit (or potential edit) to be read-only.
- Window : Changed `setPosition` such that the whole window will remain on screen. Set `forcePosition` to `False` to disable this behaviour.
- ImageGadget : Added support for GPU-based clipping, exposure, gamma and display transform.
- TestCase : Added `failureMessageLevel` attribute to control which messages trigger test failures.
- GafferSceneTest : Added `exposure` `FloatPlug` to `TestLight`.

Breaking Changes
----------------

- Filter : Removed virtual `sceneAffectsMatch()` method. Derived classes should implement `affects()` instead.
- FilterPlug : Replaced `sceneAffectsMatch()` method with a more general `sceneAffects()` method. This should be used to replace any calls to the old method.
- PointsType : Changed base class from Deformer to ObjectProcessor.
- Gaffer : Removed `lazyImport()` method.
- GafferUI : Removed deprecated `_qtImport()` method. Use `from Qt import` instead.
- Startup :
  - Removed several compatibility shims for loading files from Gaffer versions prior to 0.20.0.0. Either resave the file from version 0.57.0.0 or adopt the appropriate shim into your own configuration. The following are affected :
     - RemoveChannels nodes.
     - OpenColorIO nodes.
     - Certain ImageWriter settings from version 0.17.0.0 and prior.
     - Expression nodes from version 0.18.0.0 and prior.
     - Invalid `Node.user` plug inputs from version 0.18.0.0 and prior.
     - Reformat nodes from version 0.19.0.0 and prior.
     - Crop nodes from version 0.20.0.0 and prior.
     - TaskNodes from version 0.20.0.0 and prior.
  - Removed several compatibility shims for running old Python code without modification. Either update your code or adopt the appropriate shim into your own configuration.
    - `Gaffer.MetadataAlgo` and `Gaffer.MonitorAlgo` can no longer be accessed without namespace qualification.
    - `GafferImage.ImageAlgo` and `GafferImage.BufferAlgo` can no longer be accessed without namespace qualification.
    - `GafferScene.SceneAlgo` can no longer be accessed without namespace qualification.
    - `GafferDispatch` attributes can no longer be accessed via the `Gaffer` namespace.
    - `Gaffer.UndoContext` is no longer an alias for `Gaffer.UndoScope`.
    - `GafferDispatchUI` attributes can no longer be accessed via the `GafferUI` namespace.
    - `GafferDispatch.ExecutableNode` is no longer an alias for `GafferDispatch.TaskNode`.
    - `GafferCortex.ParameterisedHolderExecutableNode` is no longer an alias for `GafferCortex.ParameterisedHolderTaskNode`.
    - `GafferCortex` attributes can no longer be accessed via the `Gaffer` namespace.
    - `GafferCortexUI` attributes can no longer be accessed via the `GafferUI` namespace.
- RecursiveChildIterator : Changed private member data. Source compatibility is maintained.
- IECorePreview::Renderer : Changed signature for `create` and `registerType` to include optional message handler.
- ObjectProcessor : Added a virtual method.
- PlugValueWidget :
  - Renamed `create()` argument from `plug` to `plugs`. A single plug may still be passed.
  - Renamed constructor argument from `plug` to `plugs`. A single plug may still be passed. The same applies to the constructors for the following subclasses :
    - NumericPlugValueWidget
    - CompoundNumericPlugValueWidget
    - ColorSwatchPlugValueWidget
    - ColorPlugValueWidget
    - StringPlugValueWidget
    - TweakPlugValueWidget
    - BoolPlugValueWidget
    - PresetsPlugValueWidget
  - Removed connections to `plugFlagsChangedSignal()`. In the unlikely event that a derived class depends on plug flags, it must now manage the updates itself.
- InteractiveRender :
  - Changed base class from Node to ComputeNode, added members.
  - `state` and `renderer` plugs can no longer be connected to compute node outputs due to dirty propagation constraints.
- InteractiveRenderTest : Added `interactiveRenderNodeClass` member that must be populated with render node class by derived test cases (#3803).
- MessageWidget : Removed deprecated `appendMessage` method, use `messageHandler().handle()` instead.
- Shader : Added virtual method.
- MetadataAlgo : `readOnly( None )` will now raise an Exception instead of returning `False`.
- FormatPlug :
  - Removed private member.
  - Changed signature of `defaultValue()` method.
- ValuePlug : Added virtual method.

Build
-----

- Updated to GafferHQ/dependencies 1.6.0.

0.57.7.6 (relative to 0.57.7.5)
========

Fixes
-----

- Viewer : Fixed corruption of the GL stack and potential crash caused by exceptions thrown during draw.

0.57.7.5 (relative to 0.57.7.4)
========

Fixes
-----

- Arnold Renderer : Fixed hangs when instancing the output of an Encapsulate node.
- CropWindowTool : Fixed error handling bugs.

0.57.7.4 (relative to 0.57.7.3)
========

- BranchCreator : Fixed bugs affecting set computation.

0.57.7.3 (relative to 0.57.7.2)
========

Fixes
-----

- Encapsulate : Fixed bug where globals and render sets were evaluated in the wrong context.
- OSLObject : Fixed invalid reads from Constant array primitive variables.
- PresetsPlugValueWidget/PlugValueWidget : Fixed bugs handling context-sensitive presets.

0.57.7.2 (relative to 0.57.7.1)
========

- PrimitiveInspector :
  - Fixed bug that caused data lists to lose their scroll position during updates.
  - Fixed bug that could cause the inspector to show a different location to other Editors.
  - Fixed bug when the selected location doesn't exist in the input scene.
- Attributes : Fixed bug that could prevent interactive updates when the `global` plug was on.
- CollectScenes : Fixed childNames hashing bug.
- SceneWriter : Fixed error caused by computed filenames with a dependency on time. This
  makes it possible to write to a sequence of cache files rather than one monolithic file.
- GafferArnold : Added missing GafferOSL Python bindings import.

0.57.7.1 (relative to 0.57.7.0)
========

Fixes
-----

- Box : Fixed GIL management bug that could cause hangs when promoting a plug.
- SetFilter : Added missing set expression operators to node reference/tooltip.
- UIEditor : Fixed bug which allowed the creation of non-selectable presets.
- EditScopes : Fixed crash in `EditScope::processors()` if intermediate nodes had no corresponding input.
- ShaderAssignment : Fixed bug in `shader` plug connection acceptance that could cause crashes at shutdown.

0.57.7.0 (relative to 0.57.6.0)
========

Improvements
------------

- Dispatch app : Added support for setting CompoundDataPlugs via the `-settings` argument.
- Viewer : Made light gobos selectable.

Fixes
-----

- Viewer :
 - Fixed crashes that could be caused by invalid pixel values.
 - Fixed bug that caused gobos to ignore the light visualisation mode of their parent light.

API
---

- CompoundEditor :
  - Added `visibleOnly` argument to `editor()` method.
  - Improved `editor()` logic, so that visible editors are always preferred to hidden ones.

0.57.6.0 (relative to 0.57.5.0)
========

Fixes
-----

- Catalogue :
  - Fixed incorrect column values when an image is renamed in a promoted Catalogue (#3815).
  - Fixed dependency tracking and hashing bugs.
  - Improved handling of missing images (#3808).
- SetFilter : Sanitised context used to evaluate set expressions, by removing `scene:filter:inputScene` variable.
- SceneAlgo : Removed cancellers from contexts referenced by history objects.
- Context : Fixed Python `Canceller` lifetime management bug.

API
---

- Context : Added copy constructor that allows an existing canceller to be omitted.

0.57.5.0 (relative to 0.57.4.1)
========

Improvements
------------

- ArnoldShader :
  - Added support for `gaffer.icon STRING "name.png"` metadata in `.mtd` files.
  - Added support for `gaffer.iconScale FLOAT scale` metadata in `.mtd` files.
- ImageStats : Parallelised compute for improved performance.
- Documentation : Added Spreadsheet article.

Fixes
-----

- TransformTool : Fixed blank status message for certain non-editable selections.
- Dispatcher : Fixed dispatch of two or more Switches or ContextProcessors connected together directly.
- ArnoldTextureBake : Fixed recursion depth exception caused by more than ~300 meshes in a UDIM.
- MergeScenes : Fixed bug in set computations which could trigger crashes with an overloaded cache.

0.57.4.1 (relative to 0.57.4.0)
========

Fixes
-----

- NodeEditor : Fixed hangs when switching to "Follow Scene Selection" mode.
- SourceSet : Fixed GIL management bug in constructor binding.

0.57.4.0 (relative to 0.57.3.0)
========

Improvements
------------

- Spreadsheet :
  - The enabled/disabled state of a cell may now be edited directly via a new switch in the popup editing window.
  - When promoting plugs - such as those from Attributes node - which have their own "enabled" switch, this switch is now adopted by the spreadsheet, instead of having an additional "enabled" switch on the cell.
  - Added support for creating columns from tweaks in ShaderTweaks nodes. This allows the mode and value to be grouped in a single column.
  - Added colour swatches for columns containing a switch as well as a colour value.
- ShaderTweaks : Added a preset for tweaking OpenGL surface shaders.
- Documentation : Added Contexts article.

Fixes
-----

- NodeEditor : Fixed "Connect to Spreadsheet" tool menu item to work with Spreadsheets that have sections. Previously, the submenu showed the sections unnecessarily, and selecting a section triggered an error.
- Fixed hangs caused by bad GIL management in Path bindings.
- OSLObject : Fixed bug that could cause string comparisons to fail for strings fetched using the InString shader or `inString()` function.
- Fixed potential shutdown crashes when custom Metadata or View registrations have been made via Python.
- Backdrop : Fixed bug which caused unnecessary plugs to be added during copy/paste.
- TweakPlug : Fixed bugs which prevented the creation of output TweakPlugs.
- Fixed crash when rendering unknown lights in 3Delight.

API
---

- EditScopeAlgo : Added functions for creating edits on shader parameters.
- Spreadsheet : Added an `addColumn()` overload with an `adoptEnabledPlug` boolean argument. This allows cells to reuse the `enabled` plug from their `value` plug if it has one.
- SpreadsheetUI :
  - Added `formatValue()` and `registerValueFormatter()` methods to support custom formatting for extension plug types.
  - Added `decoration()` and `registerDecoration()` methods to support decorations for extension plug types.
  - Added `registerValueWidget()` method to support customisation of widgets used for editing.
  - Added `spreadsheet:plugMenu:includeAsAncestor` and `spreadsheet:plugMenu:ancestorLabel` metadata, to allow ancestor plugs to be promoted from the popup menu for their descendants.
- BackdropNodeGadget : Added `setBound()` and `getBound()` methods.

0.57.3.0 (relative to 0.57.2.0)
========

Fixes
-----

- Viewer : Fixed a bug in the render control widget which caused the entire Viewer to fail if there was an error computing the metadata for an image.
- Arnold : Added workaround for Arnold bug which prevented interactive edits to quad light colour textures.
- CopyAttributes : Fixed bugs triggered by non-existent source locations. CopyAttributes now matches the behavior of CopyPrimitiveVariables : if the source location does not exist, nothing is copied and no error is caused.
- Viewer : Fixed bugs in the "Edit Tweaks..." menu item. The wrong ShaderTweaks node could be displayed for certain upstream configurations of nodes like CopyAttributes, ShuffleAttributes and MergeScenes.
- OSLCode : Removed string substitutions on code, so that symbols such as `#` can be used directly. Substitutions were of no use anyway, because they were not being applied in a suitable context.
- SceneAlgo : Fixed `shaderTweaks()` bugs that could cause the wrong node to be returned.

API
---

- SceneAlgo : Added an `attributeHistory()` method which returns a computation history for one specific attribute.

0.57.2.0 (relative to 0.57.1.0)
========

Improvements
------------

- ArnoldTextureBake : Added `udims` plug.

Build
-----

- Dependencies :
  - Updated to GafferHQ/dependencies 1.3.0.
  - Added dependency on the `six` Python module, to enable progress towards support for Python 3.
- Fixed compilation with GCC 4.8.

0.57.1.0 (relative to 0.57.0.0)
========

Features
--------

- ClosestPointSampler : Added a new node for sampling primitive variables from the closest point on a source primitive.
- CurveSampler : Added a new node for sampling primitive variables from parametric positions on some source curves.
- ArnoldColorManager : Added a new node for specifying the colour manager for use in Arnold renders (#3523).
- Viewer : Added overlay to Image views to control interactive renders where available (#3419).

Improvements
------------

- Spreadsheet : Added a popup menu item for promoting spreadsheet plugs.
- InteractiveRender : Improved presentation of render control buttons (#3419).

Fixes
-----

- Spreadsheet : Fixed pattern matching bugs when using `${scene:path}` as the selector. In this case, `*` no longer matches `/`, and `...` is now supported.
- TranslateTool : Fixed problems translating an object with a downstream AimConstraint applied.
- Instancer : Fixed crashes caused by attempts to instance onto a location without a primitive (#3715).
- Script Settings :
  - Fixed errors showing the popup menu for the `frameRange` plug.
  - Fixed Spreadsheet menu items.
- UI : Fixed appearance of button icons when disabled.
- FilterResults : Fixed the UI to show the connected filter instead of a meaningless numeric value. This also avoids triggering spurious errors on PathFilter nodes.
- Viewer :
  - Fixed crash displaying and/or manipulating objects with zero scale transform components.
  - Fixed EditScope menu to include scopes nested inside Boxes.
  - Fixed EditScope menu button so it updates when the EditScope is renamed.
- NodeAlgo : Fixed bugs that prevented visitation of nodes nested inside Boxes.
- ColorSwatch : Fixed highlighted appearance (#3735).

API
---

- PrimitiveSampler : Added a new base class for nodes which sample primitive variables using an `IECoreScene::PrimitiveEvaluator`.
- Arnold Renderer : Added support for an `ai:color_manager` option.

0.57.0.0
========

Features
--------

- EditScope : Added new node which provides a container for node graph edits made by interactive tools in the UI (#3467).
  - The current EditScope may be chosen from a new menu in the Viewer toolbar.
  - The TransformTools and CameraTool will now automatically create edits in the chosen EditScope, enabling edits without the need to manually create a Transform node.
  - Added a <kbd>Ctrl + Delete</kbd> hotkey which prunes the currently selected objects using the current EditScope.
- LocaliseAttributes : Added new node which makes local copies of inherited attributes.

Improvements
------------

- PathFilter : Added `roots`, an optional filter input to provide multiple root locations which the `paths` are relative to. This can be useful when working on a single asset in isolation, and then placing it into multiple locations within a layout.
- Spreadsheet : Improved performance of Spreadsheets with many rows.
- CopyPrimitiveVariables : Improved performance. In one benchmark, scene generation time has been reduced by 50%.
- MergeScenes : Improved performance when merging overlapping hierarchies.
- Serialisation : Reduced file size and load time by omitting redundant `setInput()` calls from serialisations.
- ShaderTweaks : Added `localise` option to allow location-specific tweaks to be made to inherited shaders.

Fixes
-----

- Filter : Fixed bug which prevented "Select Affected Objects" menu items from working in cases where there was another filter in between the filter and the nodes it was applied to.
- RotateTool : Fixed bug which caused aiming clicks to change the selection in some circumstances.
- TranslateTool : Fixed bug which caused snapping clicks to change the selection in some circumstances.
- Viewer : Fixed problems displaying the "Cs" primitive variable.
- Alembic :
  - Fixed loading of "N" and "uv" for curves.
  - Fixed writing of "N", "uv" and "width" for curves.
  - Fixed round-tripping of interpretation for secondary UV sets.
- Stats app :
  - Fixed bug which caused the `-scene` and `-image` arguments to evaluate a node's input rather than its output. In particular this affected nodes like ContextVariables.
  - Fixed bug which meant that the `-scene` and `image` arguments didn't support nested output plugs.
- ReverseWinding : Fixed incorrect results when two or more primitive variables referenced the same data.

API
---

- EditScopeAlgo : Added new namespace with utility functions for editing scenes using EditScope nodes.
- ScenePlug : Added `exists()` method. This provides fast existence queries for locations.
- SceneAlgo :
  - Added `filteredNodes()` function, returning all the FilteredSceneProcessors affected by a
    particular filter.
  - Deprecated `exists()` function. Use `ScenePlug::exists()` instead
- Spreadsheet :
  - Added `RowsPlug::row( rowName )` method.
  - Added support for `spreadsheet:defaultRowVisible` metadata, which can be used to hide the default row.
- AttributeProcessor : Refactored to be more widely useful.
- Spacer : Added optional `preferredSize` constructor argument.
- View : Added `editScope` plug and `editScope()` accessor method.
- TransformTool :
  - Added `Selection::editable()` method.
  - Added `Selection::warning()` method.
  - Added `selectionEditable()` method.
- TweakPlug : Changed `applyTweak(s)` return type to `bool` - indicating if any tweaks were actually performed (#3699).

Breaking Changes
----------------

- AttributeProcessor :
  - Removed `names` and `invertNames` plugs.
  - Rederived from FilteredSceneProcessor rather than SceneElementProcessor.
  - Added new pure virtual methods that must be implemented by derived classes.
  - Changed base class of several nodes from SceneElementProcessor to AttributeProcessor :
    - Attributes
    - ShuffleAttributes
    - DeleteAttributes
    - ShaderTweaks
    - ShaderAssignment
    - SetVisualiser
    - AttributeVisualiser
    - CollectTransforms
- Context : Removed `Substitutions`, `substitutions()` and `hasSubstitutions()`. Use the `IECore.StringAlgo` equivalents instead.
- TransformTool : The `Selection` class now uses accessor methods rather than exposing data members directly.
- Stats app : The `-scene` and `-image` arguments now ignore input plugs.
- Spreadsheet : Broke binary compatibility. Full source compatibility is retained.
- NodeUI : Removed `lazy` argument from `plugValueWidget()` method.
- PlugValueWidget : Removed `lazy` argument from `plugValueWidget()` method.
- PlugLayout : Removed `lazy` argument from `plugValueWidget()` and `customWidget()` methods.

Build
-----

- Cortex : Updated to version 10.0.0-a76.

0.56.2.6 (relative to 0.56.2.5)
========

- Viewer : Fixed crashes that could be caused by invalid pixel values.

0.56.2.5 (relative to 0.56.2.4)
========

- Catalogue :
  - Fixed incorrect column values when an image is renamed in a promoted Catalogue (#3815).
  - Fixed dependency tracking and hashing bugs.
  - Improved handling of missing images (#3808).
- SetFilter : Sanitised context used to evaluate set expressions, by removing `scene:filter:inputScene` variable.

0.56.2.4 (relative to 0.56.2.3)
========

Fixes
-----

- Dispatcher : Fixed dispatch of two or more Switches or ContextProcessors connected together directly.
- ArnoldTextureBake : Fixed recursion depth exception caused by more than ~300 meshes in a UDIM.
- MergeScenes : Fixed bug in set computations which could trigger crashes with an overloaded cache.

0.56.2.3 (relative to 0.56.2.2)
========

Fixes
-----

- NodeEditor : Fixed hangs when switching to "Follow Scene Selection" mode.
- SourceSet : Fixed GIL management bug in constructor binding.

0.56.2.2 (relative to 0.56.2.1)
========

Fixes
-----

- Fixed hangs caused by bad GIL management in Path bindings.
- OSLObject : Fixed bug that could cause string comparisons to fail for strings fetched using the InString shader or `inString()` function.
- Fixed potential shutdown crashes when custom Metadata or View registrations have been made via Python.
- Fixed crash when rendering unknown lights in 3Delight.

0.56.2.1 (relative to 0.56.2.0)
========

Fixes
-----

- Instancer : Fixed crashes caused by attempts to instance onto a location without a primitive (#3715).
- Viewer : Fixed crash displaying and/or manipulating objects with zero scale transform components.
- ColorSwatch : Fixed highlighted appearance (#3735).

0.56.2.0 (relative to 0.56.1.0)
========

Features
--------

- ShuffleAttributes : Added node for copying/renaming attributes (#3611).
- ShufflePrimitiveVariables : Added node for copying/renaming primitive variables (#3611).

Improvements
------------

- Viewer : Added visualisation support for Arnold shader networks connected to light gobos (#3667).
- Render nodes : Added context variables to image metadata (#3646). Currently only a subset of variable types is supported, depending on the renderer used.
- Catalogue : Added customisable columns to display image information (#3646).
- Spreadsheet : Added NodeEditor tool menu items to connect relevant nodes to existing spreadsheet `activeRowNames` plugs.

Fixes
-----

- Expression : Fixed retrieval of boolean context variables via the OSL `context()` function.
- Backdrop : Fixed bug that prevented context variables from being used by the `title` and `description` plugs. All variables from the global script context are now available.
- Box : Fixed bug that allowed locked plugs to be promoted.
- NodeEditor : Fixed bug that allowed the node name to be edited on a locked node.
- InteractiveArnoldRender : Fixed problem that could potentially stop the main RGBA AOV from receiving priority for progressive updates.
- TransformTools : Fixed rare crash triggered by selecting multiple objects.
- SceneAlgo : Fixed bug which could cause hangs when retrieving the source scene from an image via Python.
- Floating Editors : Fixed keyboard shortcuts (#3632).
- ArnoldTextureBake :  Fixed imbalanced distribution of work among tasks when some UDIMs contain many more objects than others.
- Viewer : Fixed bug when using the Crop Window Tool with anamorphic images (#3690).
- UI : Fixed bug that could cause header views to show scroll bars unnecessarily.
- Catalogue :
  - Fixed bug that prevented the loading of images with non-alphanumeric filenames.
  - Fixed bug that prevented drag and drop of certain images into the Catalogue.
- StandardOptions : Fixed bug which meant that the camera chooser dialogue started browsing in the user's home directory, not the root of the scene (#3695).
- Spreadsheet :
  - Fixed scrollbar flickering in Spreadsheets with two rows (#3628).
  - Fixed bug which changed the width of the row name column when new rows were added.
- StandardOptions : Fixed bug which meant that the camera chooser dialogue started browsing in the user's home directory, not the root of the scene (#3695).

API
---

- Gaffer : Added ShufflePlug and ShufflesPlug which facilitate renaming key/value pairs (#3611).
- Metadata : Added support for `renameable` metadata in BoxUI, LabelPlugValueWidget and NameWidget.
- NodeEditor : Deprecated `setReadOnly()` and `getReadOnly()` methods.
- NodeUI : Deprecated `setReadOnly()` and `getReadOnly()` methods.
- PlugValueWidget : Deprecated `setReadOnly()` and `getReadOnly()` methods.
- CatalogueUI : Added column configuration API (#3646).
- PathListingWidget :
	- Added `sortable` kwarg to avoid premature sorting of the path passed to the constructor (#3684).
	- Added `horizontalScrollMode` kwarg to control scroll bar behaviour (#3684).
	- Deprecated `setSortable` and `getSortable` in favour of the constructor argument.
- Menu : Added support for the `active` field on dynamic sub-menu definitions.

0.56.1.0 (relative to 0.56.0.0)
========

Features
--------

- MergeScenes : Added a new node for merging the hierarchies from multiple input scenes (#3583).

Fixes
-----

- Set expression context menus :
  - Fixed bug that prevented the plug label context menu opening when the plug accepted set expressions.
  - Fixed bug that prevented the SetFilter's set expression menu from appearing when attached to a CopyAttributes node.
- CollectScenes : Fixed bug which caused errors when `RecursiveRange` encountered a CollectScenes node.
- Range/RecursiveRange : Fixed problems caused by visiting CopyAttributes nodes.
- SceneAlgo : Fixed bug that caused unrelated processes to appear in `history()` results (#3647).

0.56.0.0
========

This major feature release brings support for deep images and Arnold 6, and contains a wealth of improvements to light and camera visualisation in the Viewer.

> Caution : Bug fixes to the ImageReader, ImageWriter and Resize nodes mean that the generated images will differ substantially in some circumstances. See the Breaking Changes section for more details.

> Note : All official release builds are for Arnold 6 only, but source-level compatibility remains for Arnold 5.4 for those who wish to make custom builds.

> Note : The following nodes have renamed plugs and/or added features, such that files saved in 0.56 are not fully compatible with 0.55 : Instancer, OpenGLAttributes, Light and Camera. See Breaking Changes and Improvements sections for more details.

Features
--------

- Deep image support (#2668, #3405) :
  - Updated ImageReader and ImageWriter to support deep images.
  - Added new nodes for processing deep images : DeepToFlat, FlatToDeep, DeepMerge, DeepRecolor, DeepHoldout, DeepState, DeepTidy, Empty, DeepSampleCounts and DeepSampler.
  - Updated existing nodes to support deep images where relevant.
- Viewer : Added the Crop Window Tool to image views to allow a scene's crop window to be adjusted directly from the rendered image (#2835).
- ImageTransform : Added support for transform concatenation. This improves speed and filtering quality for chains of adjacent ImageTransforms (#2842).
- SphereLevelSet : Added new node for creating a level set representation of a sphere.

Improvements
------------

- Viewer :
  - Added visualisation of camera frustums and spot light cones. By default these are drawn only for selected objects, but menu items allow them to be enabled or disabled globally (#3569).
  - Improved camera visualisation (#58).
  - Improved visualisation of lights :
    - Added texture previews for Arnold's quad and skydome lights. All OSL shaders are supported, along with a small subset of Arnold shaders.
    - Area lights are now drawn solid by default. This can be controlled via the Visualisation section of the Light node.
    - Added intensity distribution preview for Arnold photometric lights.
    - Extended color-correction to light textures, such that they now match rendered results (#3407).
    - Reduced size of point lights to better match other light sources.
    - Simplified the color indicator and removed the exposure wedges.
    - Removed the contribution of intensity and exposure to the color indicator.
    - Added support for mesh lights such that they draw a yellow outline around the source mesh.
    - Improved display of Arnold quad lights set to portal mode.
    - Added an approximation of Arnold area light spread.
    - Added menu items to control visualiser scale.
    - Added menu items to control the default drawing mode for lights.
    - Improved <kbd>f</kbd> framing behaviour for light visualisations (#3569).
    - Unified visualisation of light radius.
- Light : Moved light visualisation plugs to the compound data mechanism to allow lights to opt-in to setting a value at their location (#3407).
- Camera : Added Visualisation controls to the Camera node to allow frustum visualisation to be easily overridden per-camera (#3569).
- OpenGLAttributes :
  - Added new light and camera visualisation attributes.
  - Added sensible limits on attribute value plugs to prevent invalid settings.
- CropWindowTool :
  - Added new mouse interactions to edit the crop region. Dragging outside creates a new region. Dragging inside moves the existing region. <kbd>Shift</kbd>-dragging inside creates a new region.
  - Updated status presentation to match other tools (#2835).
- Tools :
  - Added generic support for precise tool adjustments by holding down <kbd>Shift</kbd> whilst adjusting tool handles (#3324).
  - Changed the behaviour of existing precise tool handle adjustments such that the current handle position is maintained when the <kbd>Shift</kbd> key is depressed (#3324).
- View navigation : Added support for precise movement adjustments by holding down <kbd>Shift</kbd> whilst using the scroll wheel or moving the camera in the Viewer and other Editors (#3324).
- AnimationEditor : Changed the modifier key used to enable single-axis zoom has changed to <kbd>Ctrl</kbd> to allow use in conjunction with precise movement mode (<kbd>Shift</kbd>) (#3324).
- Set expressions :
  - Added `in` operator. The expression `A in B` selects all locations from set A which are descendants of a location from set B.
  - Added `containing` operator. The expression `A containing B` selects all locations from set A which are ancestors of a location from set B.
  - Removed restrictions on the allowable characters at the start of a set name.
- Instancer :
  - Renamed `instances` plug to `prototypes` and `index` plug to `prototypeIndex`. This clarifies their meaning and matches the terminology used in USD.
  - Organised UI into sections.
  - Added better defaults for the `orientation` and `scale` plugs.
  - Added control over prototype root locations via a string array, which can be optionally specified using a plug, Constant primvar, or Vertex primvar.
- InteractiveArnoldRender : Enabled progressive refinement.
- ArnoldOptions : Added `subdivDicingCamera`, `subdivFrustumCulling` and `subdivFrustumPadding` options.
- OSLObject : Added non-uniform scale to standard primitive variable menu.
- OSLCode : Improved labelling of inputs and outputs. Since they represent variables used in the code, they are now labelled verbatim rather than prettified.
- Error handling : The Cortex exception type is now included in error messages where relevant.
- UI : Added the Gaffer version to the window title.
- Set : Hid unused `paths` plugs from the UI, in preparation for eventual removal of the plug itself. The `filter` plug should now always be used in preference to the `paths` plug.
- Layouts : Prevented editors pinned to a specific node from restoring with the editor pinned to an empty node set. Specific pinning is no longer saved or recalled.
- Documentation : Added examples for OSLImage and OSLObject nodes.
- Rendering : Added the name of the render node to image metadata via the `gaffer:sourceScene` header (#2835).
- Test app : Added `stopOnFailure` arguments.

Fixes
-----

- Resize : Fixed bug which caused unwanted image distortion when changing pixel aspect ratio.
- ImageReader/ImageWriter : Fixed bug which caused colour transforms to be performed on premultiplied pixel data.
- ImageTransform : Fixed inconsistent filtering of transforms containing rotation but no translation.
- Launch : Fixed bug which prevented gaffer launching when stored on case destroying file systems (#3477).
- CopyAttributes : Fixed bug loading scripts saved prior to version 0.55.0.0.
- Mix : Fixed wrong behaviour outside of mask data window.
- ImageStats : Fixed bug that would return 1.0 if the 4th channel was missing. Missing channels now always return 0.0.
- Viewer :
  - Fixed bug that caused the StandardLightVisualiser to be used instead of renderer-specific ones (#3407).
  - Fixed bug that caused duplicate drawing of inherited light filter state (#3502).
  - Fixed bug that caused unexpected results when dragging into the Viewer when the Crop Window Tool was active (#2385).
- ParallelAlgo :
  - Fixed handling of Python exceptions thrown from UIThreadCallHandler.
  - Fixed GIL management for `popUIThreadCallHandler()`.
- InteractiveRender : Fixed GIL management bug in `setContext()` Python bindings.
- OSLLight : Fixed bug which prevented visualisation attributes taking effect.
- BoolWidget : Fixed unwanted horizontal expansion.
- Style : Fixed Qt application style to use the same style on all platforms.
- Display : Fixed dirty propagation for new drivers and ensured that only the channelData plug is dirtied when new data is received (#2845).
- LabelPlugValueWidget : Fixed bug that prevented updates if the `label` metadata depended on the plug name.
- ArnoldOptions : Fixed bugs in section summary formatting.

API
---

- Handle :
  - Added an optional `processModifiers` argument to drag constructors that allows the built-in precision mode handling to be disabled (#3324).
  - Added a convenience constructor for `LinearDrag` that creates a drag in an arbitrary direction on the camera plane (#3324).
  - Added `AngularDrag` helper to manage drags that represent rotations around a single axis (#3324).
- ImagePlug :
  - Added plugs and methods to support deep data.
  - Added `tilePixels()` and `pixelIndex()` convenience functions.
- ImageAlgo :
  - Added `tiles()` method, returning all the tiles for an image.
  - Added `throwIfSampleOffsetsMismatch()` method.
- FlatImageSource : Added a new base class to help in implementing image sources which generate flat data.
- FlatImageProcessor : Added a new base class to help in implementing image processors which don't support deep data.
- GafferOSL : Added ShadingEngineAlgo to simplify the generation of shading point data for images, and rendering networks to textures.
- StandardLightVisualiser :
  - Added `surfaceTexture` virtual method to allow derived classes to provide alternate surface representations (#3407).
  - Added `sphereWireframe` protected method.
  - Added support for optional `tintParameter` metadata for `quad`, `disk`, `cylinder` and `environment` type lights. This names a Color3f parameter that will used to tint the light's final appearance.
- IECoreGLPreview :
  - Added `VisualisationType` and `VisualisationMap` to allow classification of renderables returned by visualisers.
  - IECoreGLPreview : Added support for more flexible visualisations via the `Visualisation` struct (#3569).
- SceneAlgo :
  - `history()` now returns History items for all upstream plugs in the history chain, not just those where a computation was performed.
  - Added `sourceSceneName` and `sourceScene` methods to retrieve source scene information from an ImagePlug (#3582).
- Process : Added `destinationPlug()` method.
- GafferVDB : Added Interrupter class to forward Gaffer's cancellation to OpenVDB's algorithms.

Breaking Changes
----------------

- Resize : A bug fix means that results are changed significantly when changing pixel aspect ratios.
- ImageReader/ImageWriter : A bug fix means that results will now differ when applying colour transforms to images with alpha.
- Instancer :
  - Renamed `instances` and `index` plugs. Compatibility with old `.gfr` files is maintained via a config file.
  - Attributes assigned to a prototype root are now instanced onto `<prototypeName>` rather then `<prototypeName>/<id>` (eg `/instances/robot` rather than `/instances/robot/0`)
- OSLObject : Removed support for the `GAFFEROSL_OSLOBJECT_CONTEXTCOMPATIBILITY` environment variable.
- ShaderAssignment : Removed support for the `GAFFERSCENE_SHADERASSIGNMENT_CONTEXTCOMPATIBILITY` environment variable.
- bin : Renamed the `gaffer.py` launch script (to `__gaffer.py`) to avoid a collision with the main `Gaffer` module (see #3477). This will cause the process string to change on systems that don't support process renaming.
- ViewportGadget : Added private members, ABI break only - source compatibility is maintained (#3324).
- Handle : `LinearDrag::position` and `PlanarDrag::position` are no longer `const` methods. `RotateHandle`, `ScaleHandle` and `TranslateHandle` value provider methods lose `const`-ness accordingly.
- ImagePlug :
  - Removed `image()` and `imageHash()` methods. These are now available in the ImageAlgo namespace.
  - Changed default channel names to an empty list.
- ImageNode : Added virtual methods.
- Light :
  - Changed `Light::computeLight` return type to const (#3407).
  - Added plug and accessors for `visualiserShaded` (#3407).
- StandardLightVisualiser :
  - Removed protected methods `faceCameraVertexSource()` and `environmentSphere()` (#3407).
  - Changed signature of `quadPortal()` method.
  - Changed signature of `spotlightParameters()` method.
- LightFilterVisualiser : Moved `LightFilterVisualiser` into `IECoreGLPreview`, filter visualiser registrations will need updating (#3502).
- ObjectToImage/ImagePrimitiveSource : Removed.
- ParallelAlgoTest : Removed `ExpectedUIThreadCall`. Use `UIThreadCallHandler` instead.
- OpenGLRenderer : `visualiser:scale` is now handled directly in the renderer. Visualisers should no longer apply this attribute to visualisations unless they need to invert this scale for any geometry-related components of the visualisation.
- GafferScene : Renamed attribute `visualiser:scale` > `gl:visualiser:scale`. Note : Existing scenes with OpenGLAttribute nodes setting this will need values re-entering.
- IECoreGLPreview :
  - Changed the return type of `(Light|LightFilter|Attribute)Visualiser` classes. Visualisations are now a vector of `Visualisation` structs(#3569).
  - Changed `ObjectVisualiser` return type to `Visualisations`.
- Arnold : Raised minimum required version to 5.4.
- RendererAlgo : Changed signature for `outputOutput` to include the source scene plug (#2835).
- ViewportGadget : Made the SelectionScope and RasterScope classes non-copyable.

Build
-----

- Gaffer Dependencies : Updated to version 1.0.0 (#3585).
- Cortex : Updated to version 10.0.0-a72 (#3585).
- USD : Updated to version 20.02 (#3585).
- OpenVDB : Updated to version 7.0.0 (#3585).
- Arnold : Updated to version 6.0.1.0 (#3585)

0.55.5.2 (relative to 0.55.5.1)
========

- Expression : Fixed retrieval of boolean context variables via the OSL `context()` function.
- Backdrop : Fixed bug that prevented context variables from being used by the `title` and `description` plugs. All variables from the global script context are now available.
- Box : Fixed bug that allowed locked plugs to be promoted.
- TransformTools : Fixed rare crash triggered by selecting multiple objects.
- Floating Editors : Fixed keyboard shortcuts (#3632).
- ArnoldTextureBake :  Fixed imbalanced distribution of work among tasks when some UDIMs contain many more objects than others.
- StandardOptions : Fixed bug which meant that the camera chooser dialogue started browsing in the user's home directory, not the root of the scene (#3695).
- Spreadsheet :
  - Fixed scrollbar flickering in Spreadsheets with two rows (#3628).
  - Fixed bug which changed the width of the row name column when new rows were added.

0.55.5.1 (relative to 0.55.5.0)
========

Fixes
-----

- Set expression context menus :
  - Fixed bug that prevented the plug label context menu opening when the plug accepted set expressions.
  - Fixed bug that prevented the SetFilter's set expression menu from appearing when attached to a CopyAttributes node.
- CollectScenes : Fixed bug which caused errors when `RecursiveRange` encountered a CollectScenes node.
- Range/RecursiveRange : Fixed problems caused by visiting CopyAttributes nodes.

0.55.5.0 (relative to 0.55.4.1)
========

Improvements
------------

- Viewer : Added overscan display when looking through a suitably configured render camera.
- Spreadsheet : Improved performance when constructing large Spreadsheets.

Fixes
-----

- Spreadsheet :
	- Fixed bug which caused incorrect column widths after deleting a column (#3630, #3631).
	- Fixed bug that caused a load failure if a row had been deleted prior to saving.
- Viewer/InteractiveRender : Fixed bug that caused unnecessary attribute updates when changing globals.
- GraphComponent : Fixed Range and RecursiveRange iterators so that they correctly filter classes defined in Python (#3441).
- MenuButton : Fixed bug that caused buttons to remain highlighted after their menu was closed.
- StringPlug : Added compatibility for loading files saved in a future Gaffer 0.57.0.0 release.

API
---

- Spreadsheet : Added Python binding for `RowsPlug.defaultRow()`.
- Serialisation : Added `childIdentifier()` method.

0.55.4.1 (relative to 0.55.4.0)
========

Fixes
-----

- Catalogue :
  - Fixed a rare inconsistency with re-selection after deleting re-ordered images.
  - Fixed bug which prevented the Viewer hotkeys from working with Catalogues inside Boxes (#3605).

0.55.4.0 (relative to 0.55.3.0)
========

Improvements
------------

- Spreadsheet : Added sections for the logical grouping of columns in large spreadsheets.

Fixes
-----

- ImageTransform : Fixed bug in channel data hashing.
- Spreadsheet :
  - Fixed bug that could break promoted Spreadsheet UIs.
  - Fixed bug that meant the current width was not checked in the row name width popup menu.
  - Fixed bug when undoing section resize.
  - Fixed crashes caused by removing a column.

API
---

- NodeAlgo : Added graph traversal functions (#3573) :
  - `visitUpstream()`, `visitDownstream()`, `visitConnected()`
  - `findUpstream()`, `findDownstream()`, `findConnected()`
  - `findAllUpstream()`, `findAllDownstream()`, `findAllConnected()`
  - `upstreamNodes()`, `downstreamNodes()`, `connectedNodes()`

0.55.3.0 (relative to 0.55.2.1)
========

Improvements
------------

- ArnoldLight : Improved the organisation of Arnold light parameters.
- Catalogue : Changed image duplication behaviour so the copy is now placed above the source in the image list. If <kbd>alt</kbd> is held whilst duplicating, the Catalogue will switch to the last duplicate.

Fixes
-----

- FileMenu : Fixed bug that prevented `Ctrl-N` from working when the mouse was over a `NodeSetEditor` (#3546).
- NameSwitch : Fixed bug that prevented a NameSwitch from reloading correctly if it was first connected
  to an unserialisable plug.
- Arnold : Fixed indeterminate ordering of AOVs in Arnold scene description.
- FileIndexedIOPathPreview : Fixed bug which broke the UI when using an upcoming Cortex version.
- Catalogue :
  - Fixed bug when drag-reordering images that could result in other images jumping positions (#3554).
  - Catalogue : Fixed bug when deleting an image that had been dragged to the top, that resulted in incorrect image selection after deletion (#3554).
- ErrorDialogue : Fixed bug in handling of non-standard exceptions.
- DispatchDialogue : Fixed bug in handling of non-standard exceptions.
- PresetsPlugValueWidget : Fixed bug that meant no context variables were set when generating dynamic plug presets (#3496).
- CropWindowTool : Fixed bug that meant no Context Variables were set when searching for the StandardOptions node (#3496).

API
---

- ArnoldShaderUI :
  - Added support for `gaffer.layout.divider` and `gaffer.layout.index` in Arnold metadata sidecar `.mtd` files.
  - Added support for parameter presets in Arnold metadata sidecar `.mtd` files.

0.55.2.1 (relative to 0.55.2.0)
========

Fixes
-----

- Viewer : Improved clipping plane "Fit ..." command logic to avoid clipping the scene when dollying in, or bad framing using <kbd>f</kbd>.
- Spreadsheet :
  - Fixed bug with column name text input dialog.
  - Fixed problems when adding or removing columns on promoted spreadsheets.
  - Fixed plug promotion via `BoxIO.promote()`.
- TransformTool : Fixed editing of transforms specified by promoted Spreadsheets.
- GraphGadget : Fixed bug which could cause a node to be shown under the wrong parent when its gadget type was changed.
- USD : Added workaround for custom builds which omit the `pxr.Usd` Python module. In this case USD support will be disabled.
- NumericWidget : Fixed bug that caused an exception to be raised if the up/down keys were pressed in a NumericWidget when the widget's value was empty.

0.55.2.0 (relative to 0.55.1.0)
========

Features
--------

- Spreadsheet (#3222) : Added a new node to simplify workflows where different settings are needed in different contexts. A common expected use is to collapse the "many identical branches per shot" pattern into a single branch and a Spreadsheet. Spreadsheets also integrate well with the PathFilter and CollectScenes nodes to provide values on a per-location basis.

Improvements
------------

- Stats app : Added `-postLoadScript` command line argument. This can be used to perform post-processing of the loaded script before stats are gathered.
- Appleseed : Added the ability to hide Appleseed nodes and other presets from the UI by setting the `GAFFERAPPLESEED_HIDE_UI` environment variable to `1`. Appleseed will still be available for OSL shader previews and example scenes.
- StringPlug : Added support for the `${scene:path}` variable in string substitutions.

Fixes
-----

- CollectScenes : Fixed bug in set computations. This first appeared as a failure to display lights in the viewer in certain circumstances (#3497).
- Viewer : Fixed X-Ray shading mode on MacOS (#3473).
- Caching : Changed the cache used in various sub-systems to avoid potential compute failures (#3476).
- LRUCache : Fixed handling of cases where value computation for a cache-miss was cancelled in-flight, which then prevented the value ever being successfully retrieved (#3469).
- Menu : Fixed spacing issue in menus when the first item was a labelled divider.
- ShaderTweaks : Fixed missing preset for Arnold Blockers.
- Arnold : Fixed crash when disconnecting shader networks from lights (#3484).
- VectorDataWidget : Fixed styling update bug for non-editable widgets.

API
---

- NameValuePlugValueWidget : Added `set/getNameVisible()` methods.
- PresetsPlugValueWidget : Added a `menu()` accessor method.

0.55.1.0 (relative to 0.55.0.0)
========

Improvements
------------

- Stats app : Added node compute counts to performanceMonitor script annotations.
- UIEditor :
  - Made the Plugs tab resize the editor window so the Presets section is fully visible when expanded.
  - Added options to the Node tab to turn on and off Box node plug creator decorations.

Fixes
-----

- Viewer : Fixed light filter visualisation.
- ArnoldLightFilter : Fixed bug which caused animated light blockers to lose their transform.
- NodeEditor : Fixed bug that allowed drag and drop to create unwanted input connections to output plugs.
- GraphComponent : Fixed bug that allowed construction with an invalid name (#3436).
- Layouts : Keyboard shortcuts will now work in detached panels restored with a layout.
- Rotate/TranslateTool : Fixed a potential crash if targeted mode was used with an empty selection.
- RotateTool : Fixed a bug when applying targeted mode rotations that introduced arbitrary roll around the z-axis (#3439).
- TabbedContainer : Fixed a bug that caused an exception when the last tab in a container was closed.
- ArnoldLight : Fixed a bug that prevented OSL shaders being used with Arnold lights.
- GraphEditor : Fixed several bugs and a crash that could occur when a parent of the editor's root node was changed or deleted.
- Parent : Fixed bug which prevented loading of Parent nodes with a promoted `children` plug (#3464).
- Group/Parent : Fixed processing of invalid input sets. This now omits the invalid set members rather than throwing an error.
- ImageReader : Fixed bug which meant that changes to the default format were not respected.
- UVInspector : Fixed bug which prevented alternative UV sets from being viewed.
- SceneInspector : Fixed bug comparing objects where a particular primitive variable existed on only one of the objects (#3432).

0.55.0.0
========

This release brings numerous enhancements to the Layout system, new and improved 3D nodes, performance tweaks and new tools.

> Caution : The Instancer now deletes the target point cloud from the scene (#3394). This will
> result in a behaviour change in existing scenes that rely on the target point cloud
> existing downstream of the Instancer node.

> Info : The companion patch release `0.54.2.1` includes support to allow scripts saved from
> `0.55.0.0` to be opened in environments locked to the `0.54.x.x` series. However, scripts
> saved in `0.55.0.0` that make use of multiple input connections to the Parent node are not
> compatible with any previous versions.

Features
--------

- NameSwitch : Added new node to switch between named input connections using string matching (#3349).
- CopyPrimitiveVariables : Added new node to copy primitive variables from one object to another (#3361, #3389).
- Viewer : Transform tools now feature a ‘targeted’ mode (#3403).
   - Holding <kbd>V</kbd> and clicking in the Viewer with the Translate tool active teleports the selected objects to the clicked point.
   - Holding <kbd>V</kbd> and clicking in the Viewer with the Rotate tool active aims the selection’s -z axis at the clicked point.

Improvements
------------

- Layouts (#3360, #3392, #3398, #3399) :
  - The focus state and linking of each editor is now saved with the layout.
  - All default layouts now include linked editors as standard, with all inspectors following the Viewer, and all other editors following the Graph Editor selection.
  - Viewers can now be linked to other Viewers.
  - The Pinning button has been re-designed as the Editor Focus menu, moving all interactions to a left-click menu.
  - Editor-centric keyboard shortcuts have been added and other shortcuts improved :
    - Hitting <kbd>P</kbd> will pin the editor to the current node selection
    - Hitting <kbd>N</kbd> will make the editor follow the current node selection (a.k.a ‘un-pin’).
    - All keyboard shortcuts that change an editor’s focus, when used with a slave editor will now break any links to it’s master.
  - When hovering over an entry in the Follow section of the Editor Focus menu, the target editor will be highlighted.
  - When hovering over the editor focus menu button for a master editor, all of the following (slave) editors will be highlighted when its tooltip is presented.
  - When hovering over the editor focus menu button for a slave editor, its master editor will be highlighted when its tooltip is presented.
  - Improved editor link colors.
  - Editor/Inspector tab titles now only include node names when the editor is pinned.
  - The UVInspector can now be linked to other editors.
- Parent : The Parent node now accepts multiple inputs (#1202).
- Viewer :
  - Added up/down hotkeys to navigate through Catalogue node images (#3387).
  - Fixed light visualisation bug which would draw an extra copy of a light when an object was parented under it (#3380).
  - Made paused status more obvious (#3390).
  - Changed the default near clipping plane to 0.1 to increase depth buffer precision.
- OSLObject (#3389) :
  - Optimized bounds computations for cases where "P" is not modified.
  - Added Adjust Bounds plug to optionally disable bounds computations.
- Wireframe : Optimized bounds computations (#3389).
- Instancer :
  - Added Attribute Prefix plug (#3388).
  - The target point cloud is now deleted from the scene (#3394).
- ArnoldShader : Added metadata to improve UI layout of the `toon` shader (#3391).
- ArnoldAttributes : Added `toonId` attribute to use in conjunction with Arnold's `toon`
  shader (#3416).
- ArnoldOptions : Added `profileFileName` option (#3404).
- Docs (#3337) :
   - Added an example of configuring Arnold trace sets.
   - Moved the blockers example to the Lighting section.
- Catalogue : `header:` prefixed display parameters are now available in Catalogue image metadata for IPR renders (#3410).

Fixes
-----

- TransformTool : Fixed bug which caused nodes using set filters to be ignored (#3393).
- SceneAlgo : Fixed `objectTweaks()` and `shaderTweaks()` to respect nodes using set filters (#3393).
- Switch (#3349) :
  - Fixed bug which prevented derived classes from adding their own plugs.
  - Fixed bug with deeply nested plugs.
- ArrayPlug (#3349) :
  - Added support for child-level inputs to compound plugs.
- Shader : Fixed bug affecting component-level connections through a Switch node (#3349).
- Editors : Added support for nested output plugs (#3349).
- Catalogue : Fixed image ordering bug (#3387).
- FreezeTransform : Fixed filter evaluation bug (#3397).
- BranchCreator : Fixed serialization to omit internal connections (#3401).
- Arnold : Fixed attempts to instance curves with `min_pixel_width != 0` (#3402).
- EditMenu : Fixed bug in `editor()` method that caused errors using keyboard shortcuts with custom UIs (#3395).
- Test : Fixed a test case issue when using older python versions in custom Gaffer builds (#3408).
- Viewer : Fixed an issue that required a second click in the viewer to return focus to it after selecting a tool using the mouse (#3403).
- ShaderView : Fixed a crash that could occur on shutdown (#3413).
- Ramp editor : Fixed bug that prevented editing of ramps where a subset of plugs were not editable (#3417).
- TabbedContainer : Fixed bug whereby `currentChanged()` was called with the wrong widget when a tab was removed (#3424).
- Layouts : Fixed bug triggered when removing a tab with linked editors (#3421).

API
---

- ObjectProcessor : Added new base class to simplify the creation of nodes that modify objects.
- Deformer : Added new base class to simplify the creation of nodes that modify objects such that their bounding box changes.
- ArrayPlug (#3349) :
  - Added `resizeWhenInputsChange` constructor argument.
  - Added `next()` method.
- Switch : Added `outPlug` argument to `activeInPlug()` method (#3349).
- CompoundEditor : Made constructor arguments private.
- Menu : Added support for `enter` and `leave` fields (supplied through an `IECore.MenuItemDefinition`) to provide callback functionality as the user hovers over menu items presented on screen (#3360).
- Menu : Added support for combining `label` and `divider` to create labeled sections within a menu (#3399).
- GafferUI : Added `_qtObjectIsValid()` method (#3360).
- ShadingEngine : Added `hasDeformation()` method (#3389).
- BranchCreator : Added `processesRootObject()` virtual method to enable parent object Modifications (#3406).
- Widget : Conform linux/MacOS keyRelease events such that repeated release events are no longer emit on linux (#3403).
- SelectionTool : Don't initiate drags for derived class button presses (#3403).
- SceneGadget : Added `objectAt( line, &path, &hitPoint )` method that also populates hitPoint with the (approximate) gadget-space intersection point of line and the hit object (#3403).
- Group/BranchCreator : Factored out name mapping into ChildNameMap class to facilitate reuse (#3406).
- NodeSetEditor :
  - `registerNodeSetDriverMode` gained an optional `description` kwarg to supply a custom UI description for the mode (#3399).
  - Added `nodeSetDriverModeDescription` to retrieve the UI description for a specific driver mode (#3399).
- BoolPlug : StringPlugs are now accepted as inputs, converting empty strings to `false` and all other strings to `true` (#3410).

Breaking Changes
----------------

- TweaksPlug : Changed function signature and default behaviour of `applyTweaks()` method (#3353).
- Instancer : The target point cloud is now deleted from the scene (#3394) .
- ArrayPlug : Added argument to constructor and additional private member data. ABI change only - source compatibility is maintained (#3349).
- LightVisualiser : Moved from GafferSceneUI to IECoreGLPreview (#3380).
- Changed the base class of the following nodes : MeshType, CameraTweaks, CollectPrimitiveVariables, MapOffset, MapProjection, MeshDistortion, MeshTangents, PrimitiveVariables, Orientation, Parameters, ReverseWinding, DeleteFaces, DeleteCurves, DeletePoints, MeshToPoints, PointsType, Wireframe, OSLObject (#3389).
- ShadingEngine : Added private member (ABI change only) (#3389).
- CopyAttributes : Replaced input array with separate "in" and "source" plugs, and renamed `copyFrom` plug to `sourceLocation`. A config file will automatically convert old scripts on load (#3389).
- CopyOptions : Renamed "names" plug to "options". A config file will automatically convert old scripts on load(#3389).
- BranchCreator : Added virtual method (#3406).

0.54.2.7 (relative to 0.54.2.6)
========

Fixes
-----

- GraphComponent : Fixed Range and RecursiveRange iterators so that they correctly filter classes defined in Python (#3441).
- MenuButton : Fixed bug that caused buttons to remain highlighted after their menu was closed.
- StringPlug : Added compatibility for loading files saved in a future Gaffer 0.57.0.0 release.

0.54.2.6 (relative to 0.54.2.5)
========

- ImageTransform : Fixed bug in channel data hashing.

0.54.2.5 (relative to 0.54.2.4)
========

Fixes
-----

- PresetsPlugValueWidget : Fixed bug that meant no context variables were set when generating dynamic plug presets (#3496).
- CropWindowTool : Fixed bug that meant no Context Variables were set when searching for the StandardOptions node (#3496).
- FileIndexedIOPathPreview : Fixed bug which broke the UI when using an upcoming Cortex version.
- ErrorDialogue : Fixed bug in handling of non-standard exceptions.
- DispatchDialogue : Fixed bug in handling of non-standard exceptions.

0.54.2.4 (relative to 0.54.2.3)
========

- NumericWidget : Fixed bug that caused an exception to be raised if the up/down keys were pressed in a NumericWidget when the widget's value was empty.

0.54.2.3 (relative to 0.54.2.2)
========

Fixes
-----

- CollectScenes : Fixed bug in set computations. This first appeared as a failure to display lights in the viewer in certain circumstances (#3497).
- Viewer : Fixed X-Ray shading mode on MacOS (#3473).
- Caching : Changed the cache used in various sub-systems to avoid potential compute failures (#3476).
- LRUCache : Fixed handling of cases where value computation for a cache-miss was cancelled in-flight, which then prevented the value ever being successfully retrieved (#3469).
- ShaderTweaks : Fixed missing preset for Arnold Blockers.
- Arnold : Fixed crash when disconnecting shader networks from lights (#3484).
- VectorDataWidget : Fixed styling update bug for non-editable widgets.
- ParallelAlgo : Fixed potential hang in `popUIThreadCallHandler()` Python bindings.

0.54.2.2 (relative to 0.54.2.1)
========

Fixes
-----

- ArnoldLightFilter : Fixed bug which caused animated light blockers to lose their transform.
- NodeEditor : Fixed bug that allowed drag and drop to create unwanted input connections to output plugs.
- GraphComponent : Fixed bug that allowed construction with an invalid name (#3436).
- Layouts : Keyboard shortcuts will now work in detached panels restored with a layout.
- ArnoldLight : Fixed a bug that prevented OSL shaders being used with Arnold lights.
- GraphEditor : Fixed several bugs and a crash that could occur when a parent of the editor's root node was changed or deleted.
- ImageReader : Fixed bug which meant that changes to the default format were not respected.
- UVInspector : Fixed bug which prevented alternative UV sets from being viewed.
- SceneInspector : Fixed bug comparing objects where a particular primitive variable existed on only one of the objects (#3432).

0.54.2.1 (relative to 0.54.2.0)
========

Fixes
-----

- UIEditor : Fixed bugs which prevented node colour from being edited (#3383, #3384, #3385).
- Encapsulate : Fixed concurrent access to signals that could cause crashes at render time
  (#3381).
- Layouts : Fixed bug in `editor()` method (#3395).
- TBB : Fixed an obscure context management bug involving older TBB versions in custom Gaffer builds (#3409).
- NodeSetEditor : Fixed circular references for linked editors (#3421).
- Added support for loading files saved in Gaffer 0.55 (#3415). Note that because version 0.54
  does not support multiple child inputs on the Parent node, only the first child input will
  be loaded.

0.54.2.0 (relative to 0.54.1.0)
========

Features
--------

- Shaders : Added support for attribute substitutions in all string shader parameters.
  Tokens of the form `<attr:attributeName>` will be automatically substituted with the
  value of `attributeName` at render time. We recommend using this mechanism for passing
  texture paths to shaders, while allowing the paths to be modified independently of the
  shaders themselves (via a CustomAttribute node) (#3331).

  > Note : This mechanism uses the same syntax as Arnold's native attribute substitutions,
  > meaning that substitutions now occur in Gaffer before reaching Arnold.

Improvements
------------

- ShaderTweaks : Added `ignoreMissing` plug that suppresses the error that would normally
  occur for an attempt to tweak a parameter that doesn't exist (#3353).
- ImageTransform : Added `invert` plug (#3371).
- Layouts (#3323) :
  - Added pinning menu option for following numeric bookmarks.
  - Improved legibility of pinning menu.
- Viewer : Added X-Ray shading mode to the scene Viewer (#3344).

Fixes
-----

- ArnoldLightFilter : Fixed bug whereby changing a `light_blocker` parameter during an interactive
  render caused the transform for the blocker to be reset (#3358).
- ArnoldShader : Fixed bug which could cause user defaults for shader parameters to be ignored (#3333).
- Orientation : Fixed UI for "Quaternion XYZW (Houdini)" mode. Previously the `quaternion` plug was
  disabled in this mode (#3352).
- StandardAttributes : Fixed popup menu for the `linkedLights` and `filteredLights` plugs (#3346).
- Layouts : Improved handling of errors when loading a layout which contains a missing editor (#3355).
- ScriptWindow : Fixed automatic creation of ScriptWindows so that it interacts correctly with custom
  code that calls `ScriptWindow.acquire()` on script creation (#3362).
- GafferCortex : Fixed bug which caused plug connections and values to be lost when reloading a Parameter.
  Also added support for StringParameter userData that specifies StringPlug substitutions (#3370).
- OSLExpression : Fixed bug that caused execution to request `context.getTime()` even if the expression
  didn't need it. This could cause errors when dispatching tasks (#3373).
- Layouts : Fixed menu bar shortcuts in detached panels (#3357, #3359, #3372).
- Arnold metadata : Disabled `camera_projection.camera` parameter (#3363).
- Scene Path Browser : Fixed a bug when browsing a scene for a promoted plug (#3377).

API
---

- NumericBookmarkSet : Added new set subclass that mirrors numeric bookmarks (#3323).
- TweakPlug : Added `MissingMode` enum arguments to `applyTweaks()` methods (#3353).
- ScriptWindow : Added `menuBar()` accessor (#3359).
- MenuBar : Added `addShortcutTarget()` method to allow keyboard shortcuts to be associated
  with windows other than the parent window of the menu bar (#3359).
- CompoundEditor : Added `editor()` method that can be used to find an editor that the
  user is currently interacting with (#3372).
- OpenGLShader : Added support for glsl source code parameters (#3344).
- ScenePath Binding : Prevent crashes caused by passing None to constructor (#3377).

Build
-----

- Fixed bug with builds using LOCATE_DEPENDENCY_RESOURCESPATH (#3347).
- Fixed failure to load GafferArnold during documentation builds on MacOS with SIP enabled (#3348).

0.54.1.0 (relative to 0.54.0.1)
========

Features
--------

- Orientation : Added new node for converting between different orientation representations
  (eulers, quaternions, matrices etc). This is particularly useful when preparing points for
  instancing (#3328).

Improvements
------------

- ShaderAssignment : Added support for assigning OSL shaders with an alternative prefix. This
  can be useful when mixing OSL shader assignments with renderer-specific shader assignments
  (#3334).

Fixes
-----

- HierarchyView : Fixed bug which could cause a hang when Shift+clicking to expand (#3335).
- ScriptNode (#3340) :
  - Fixed GIL management bug which could cause crashes when serialising a script.
  - Fixed bug that could cause string substitutions to be baked into serialisations.

API
---

- Improved support for iterating over nodes and plugs (#3341) :
  - Added FilteredChildRange and FilteredRecursiveChildRange classes. These can be used with
    C++11's range-for.
  - Added Iterator, RecursiveIterator, Range and RecursiveRange type aliases to all nodes and
    plugs.
  - Added InputIterator, OutputIterator, RecursiveInputIterator, RecursiveOutputIterator,
    InputRange, OutputRange, RecursiveInputRange and RecursiveOutputRange type aliases to all
    plugs.
  - Exposed Range classes to Python.

Documentation
-------------

- Fixed problems with screenshots for MacOS builds (#3321).
- Made miscellaneous improvements to the examples available from the Help menu (#3314).

0.54.0.1 (relative to 0.54.0.0)
========

Fixes
-----

- NameValuePlug : Fixed serialisation bug which could prevent promoted NameValuePlugs
  from being saved correctly (#3318).
- OSL : Fixed bug which prevented the GafferOSL module from loading on headless
  renderfarm machines (#3316).

Documentation
-------------

- Fixed missing documentation on MacOS builds (#3315).
- Made miscellaneous fixes to examples (#3309, #3313).

0.54.0.0 (relative to 0.53.x)
========

This major release brings support for Arnold's light blockers and adds a new _UV Inspector_
editor for viewing UVs and textures. It also brings a host of core UI changes, including a
new look and improvements to layout management and node pinning. Additionally we've made
advances under the hood, resulting in improved performance and lower memory usage in many
cases. Read on for further details of these and numerous other enhancements and fixes...

> **Caution** : This release brings substantial performance improvements in the generation
> of ShaderAssignments, but at the expense of removing support for using the `scene:path`
> context variable in shader networks. We recommend migrating such setups to use a
> CustomAttributes node to generate a context-varying attribute which is then referenced
> by the shader. This approach improves scene generation performance in Gaffer and
> prevents the passing of large numbers of unique shader networks to the renderer.
> Temporary backwards compatibility for old networks can be enabled by setting the
> `GAFFERSCENE_SHADERASSIGNMENT_CONTEXTCOMPATIBILITY` environment variable to `1`.
>
> The same optimization applies to the OSLObject node, with temporary backwards compatibility
> being available separately by setting the `GAFFEROSL_OSLOBJECT_CONTEXTCOMPATIBILITY` environment
> variable to `1`.

Features
--------

- Light filters : Extended support for Arnold's light filters by adding blockers (#3020) :
  - Added new ArnoldLightFilter node for creating blockers.
  - Added attribute for linking blockers to lights to StandardAttributes node.
- UVInspector : Added new editor for viewing UVs and associated textures (#3273).
- SetVisualiser : Added node to allow visualisation of set membership in the Viewer (#3117).

Improvements
------------

- Layouts :
  - Improved tab management :
    - Tabs can now be drag re-arranged, detached into new windows and closed/detached using a context menu (#3197).
    - Layouts will now store and recall detached panels, and all positions, sizes and maximized/full screen state (#3197).
    - Added tab close buttons (#3211).
  - Added advanced pinning options, available from the context menu for the pinning icon (#3270) :
    - Editors can now follow the source node for the current scene selection.
    - Editors can be linked so that an editor follows all pinning changes applied
      to another editor.
- OSLImage :
    - Added improved interface which provides image channel management directly on
      the OSLImage node (#3218).
    - Added `defaultFormat` plug. This allows OSLImage to be used without an
      input image connected (#3218).
    - Improved performance of shader input evaluation (#3074).
- OSLObject :
    - Added improved interface which provides primitive variable management directly on
      the OSLObject node (#3192).
    - Improved performance of shader input evaluation (#3074).
    - Added `useAttributes` plug, which allows OSL shaders to query attributes from the
      scene (#3226).
- Appleseed : Updated to Appleseed 2.0.5 (#3288).
- FilterResults : Improved performance. For certain FilterResults-heavy production
  graphs, we have seen 4-5x speedups in total scene generation time (#3174).
- Instancer/Parent/Seeds : Added a filter input to allow operation on multiple locations
  at once (#2917, #3176).
- TransformTools : Added precision mode enabled by holding <kbd>Shift</kbd>. Added basic
  snapping to increments by holding <kbd>Ctrl</kbd> (#3277).
- Viewer : Prioritized update of objects being manipulated, resulting in much more fluid update (#3144).
- Node Menu :
  - Added an improved "fuzzy matching" search algorithm (#2986).
  - Added an error indicator when a search matches nothing (#2986).
  - Improved naming of nodes and scene locations for newly created
    Arnold shaders and lights (#3261).
- SceneReader : Added support for USD files that reference Alembic archives.
- Text : Added support for Unicode characters (#2999).
- PythonCommand : Improved performance (#3029).
- GraphEditor :
  - Added support for arbitrary node annotations specified by metadata.
    Use `annotation:<name>:text` to specify the text to render, and `annotation:<name>:color`
    to specify an associated color (#3028).
  - Added <kbd>Ctrl</kbd> + click-drag marquee action to deselect nodes (#3090).
  - Made it show the root instead of removing the GraphEditor when the viewed Box is deleted (#3163).
- UIEditor : Added support for setting the icon for a node (#3204).
- Stats app :
  - Added `annotatedScript` argument to allow the saving of the script with
    monitor annotations added to it (#3028).
  - Added `-cacheMemoryLimit` and `-hashCacheSizeLimit` arguments for controlling
    cache limits (#3033).
  - Added support for render output profiling via `-scene` argument (#3053).
  - Added a `-contextSanitiser` argument, used to check for common context handling
    errors (#3060).
  - Added entries for SharedSceneInterface limits and usage (#3126).
- ArnoldTextureBake : Added optional median filter (#3026).
- Hash cache : Reduced memory usage and improved performance (#3033).
- GraphComponent : Reduced memory usage and improved script loading times (#3080).
- Shader : Improved performance of network generation (#3074).
- ShaderAssignment : Improved performance by removing support for varying shader networks
  by scene location (via the `scene:path` context variable) (#3074).
- AnimationEditor : Improved behaviour of the plug listing (#3106).
  - Only selected nodes are shown, not their descendants.
  - The ancestor node hierarchy is not shown redundantly.
  - Improved performance.
- Test app :
  - All tests are now run by default (#3101).
  - Added support for detecting performance regression/improvement (#3127).
- MeshTangents : Added support for additional computation modes (#3030).
- ImageWriter : Added DWA compression presets (#3153).
- Numeric Bookmarks : Added serialization to preserve numeric bookmarks across sessions (#3157).
- SetExpressions : Added support for wildcard characters in set names (#3172).
- Lights :
  - Added `visualiserScale` setting in new _Visualisation_ tab (#3180).
  - By setting `visualiserScale` to 0, all visualisation computations can now be avoided (#3178).
  - Added visualization for point light radius (#3199).
- OpenGLAttributes : Added new _Light Visualiser_ section, with control over
  visualization scale and maximum texture resolution (#3219).
- UI : Improved stylesheet (#3193, #3229, #3246, #3249).
- SystemCommand : Added `shell` plug, to determine whether or not the supplied
  command is interpreted as a shell command or executed directly (#3230).
- ArnoldShader : Added metadata for new shader parameters introduced in Arnold 5.3 (#3243).

Fixes
-----

- Dispatcher (#3024) :
  - Added support for Switch nodes. The dedicated TaskSwitch node is
    still available, but will be removed in a future release.
  - Added support for ContextProcessor nodes such as ContextVariables and
    TimeWarp. The dedicated TaskContextVariables node is still available, but
    will be removed in a future release.
- Light linking (#3265) :
  - Fixed crash when hiding a linked light during an interactive Arnold render.
  - Fixed crash when changing parameters on a linked light during an interactive
    Arnold render.
  - Fixed bug which caused light links to be output unnecessarily if non-lights
    where inadvertently added to the `defaultLights` set.
- TransformTool : Fixed crash when using the tool while a Catalogue node saves an
  image in the background (#3196).
- GraphEditor : Added bookmark annotations for Dots and other auxiliary nodes (#3028).
- ArnoldTextureBake (#3026) :
  - Connected external dispatcher settings to internal render task.
  - Connected preTasks plug to internal tasks.
  - Fixed leakage of internal context variables.
- Viewer :
  - Fixed keyboard modifier handling for object selection. Previously, holding
    down any modifier key whilst drag-selecting or clicking an object in the Viewer would
    modify the current selection. This behaviour was only intended to be triggered by the
    Shift key (#3095).
  - Fixed bug that prevented image updates after a computation error had occurred (#3273).
- Scene : Fixed context handling bugs in Transform, SceneWriter, SceneAlgo, Set,
  Isolate and Prune. This improves performance on some complex scenes (#3060).
- Offset : Fixed context handling bug (#3073).
- AnimationEditor (#3106) :
  - Fixed visibility glitch in timeline hover indicator. It wasn't being
    hidden when the mouse left the editor.
  - Fixed bug when deselecting a curve - the plug listing selection was not being updated
    to reflect the change.
- PythonCommand :
  - Prevented inadvertent modification of outer context (#3101).
  - Sequence mode now allows access to static variables without specifying the frame (#3262).
- Fixed widget signal/slot lifetime issues (#3179).
    - Using ScopedConnections is no longer needed as `Widget` now derives from `Trackable`.
    - ScopedConnections can still be used when wanting to replace connections on the fly.
- NodeMenu : Fixed Delight/Light/DistantLight menu item (#3216).
- CropWindowTool :
  - Fixed incorrect results caused by a Switch node between viewed node and target (#3207).
  - Fixed hangs caused by active CropWindowTool when viewing empty scene (#3207).
  - Fixed bug that could allow a read-only plug to be edited (#3239).
- Dispatch app : Fixed configuration bug which caused GafferUI to be loaded unnecessarily.
  This could cause a `QXcbConnection Could not connect to display` error when run on a machine
  without an X server (#3237).
- Execute app : Stopped current frame of saved script leaking into the context for
  `TaskNode::executeSequence()` (#3262).
- Stats app : Fixed VTuneMonitor scoping (#3196).
- Monitor : Fixed thread safety and scoping of monitors. Monitors now only see processes
  launched on the thread they were scoped on, and parallel tasks that are spawned by those
  processes (#3196).
- Reference : Fixed problems that meant that metadata was lost when promoting a plug from
  a reference (#3258).
- GraphComponent : Fixed crashes caused by passing `None` as a child argument from Python
  (#3276, #3279).
- Expression : Fixed bug whereby expressions could break if nodes were renamed during copy/paste
  (#3283).
- CustomAttributes : Fixed performance regression caused by addition of the `extraAttributes`
  plug (#3280).
- Warp : Fixed bug which prevented a derived class from using a single Engine for the whole
  image. It is no longer necessary to append `tileOrigin` in `engineHash()` (#3299).

Documentation
-------------

- Added "Anatomy of a Camera" which gives an overview of Gaffer's camera model, the terminology,
  the camera data in the scene, and how the data flows through the graph (#3050).
- Added a "Camera" section to "Working with Scenes" which covers usage and task information
  about the Camera node, manipulating camera objects, the CameraTweaks node, render overrides,
  and demos of a spherical and anamorphic camera setup (#3050).
- Added "Light Linking" which shows how light linking is set up and runs through an example
  scenario that would necessitate light links (#3114).
- Added mechanism for providing example node networks in the help menu. Examples can optionally be
  associated with certain node types. The Cog menu in the Node Editor lists any applicable
  Examples for the node type being edited (#3108).
- Added general improvements to readability and appearance in the stylesheet. Most notably,
  this makes the headings consistent, and the spacing between elements uniform (#3149).
- Added bootstrap scrollspy to improve signposting and to provide a mini-nav for articles (#3159).
- Moved tutorials to appropriate sections (#3210).
- Fixed broken links (#3210).

API
---

- ComputeNode : Added `hashCachePolicy()` and `computeCachePolicy()` methods which can be overridden
  to provide additional control over caching. Default behaviour is unchanged. The new
  `Standard` policy can be used to prevent multiple threads computing the same result in
  parallel, which is of particular relevance to expensive computes that load external resources.
  Computes which spawn TBB tasks _must_ use the `TaskCollaboration` or `TaskIsolation` policies
  (#3174).
- ThreadState : Added new class to consolidate tracking of current context, process and
  monitors on a per-thread basis. When spawning tasks from a compute, it is your responsibility
  to transfer thread state onto the threads executing the tasks, whereas
  before only context needed to be transferred. New constructors for the various
  `Context::EditableScope` classes make this relatively painless (#3196).
- ProcessException : Added new class used to wrap exceptions thrown during computation.
  This provides information about the plug and context where the exception was thrown (#3223).
- TextWidget/MultiLineTextWidget : Added support for Unicode characters. In this
  case the `getText()` method will return a UTF-8 encoded string (#2999).
- ContextSanitisers : Added new ContextSanitiser classes to GafferSceneTest and
  GafferImageTest. These are Monitors which warn about common context handling mistakes
  (#3060, #3073).
- TaskNode (#3024, #3025) :
  - Simplified implementation requirements for `preTasks()` and `postTasks()`
    methods. It is now sufficient to construct `Tasks` directly from the input
    plugs, with no requirement to find their source and check for a TaskNode.
  - Added missing bindings for `Task( TaskPlug )` and `Task::plug()`.
- ContextProcessor (#3024) :
  - Added `inPlugContext()` method.
  - Added support for working with `Plugs` rather than only `ValuePlugs`.
- AnnotationsGadget : Added new gadget for rendering annotations for GraphGadgets (#3028).
- MonitorAlgo : Added `annotate()` methods for turning Monitor statistics into
  GraphEditor annotations (#3028).
- ValuePlug :
	- Added `set/getHashCacheSizeLimit()` methods for controlling hash cache memory usage (#3033).
	- `isSetToDefault()` now returns false uncoditionally if a plug's value is being driven
	  by a ComputeNode. Calling `isSetToDefault()` will never trigger a compute (#3280).
- Context : Added `EditableScope::context()` method (#3060).
- SceneTestCase (#3060) :
  - Added a ContextSanitiser that is active for the duration of the tests.
  - Improved assert methods.
- GraphComponent : Added protected `parentChanged()` virtual method (#3080).
- ImagePlug : Added convenience methods for evaluating global image properties (#3073).
- GraphComponentPath : Added property for accessing the GraphComponent (#3106).
- LightFilter : Added LightFilter class used as base for renderer-specific implementations (#3020).
- NameValuePlug : Introduced new plug type for associating a name with a value (#3161).
- SceneAlgo : `history()` now returns a nullptr when called for empty scenes instead of precipitating a segfault (#3207).
- ExtensionAlgo : Added mechanism to export Boxes as Gaffer extensions via `exportExtension()` (#3158).
  Gaffer extensions each define a new node type and are automatically integrated into the node menu.
- StringPlugValueWidget : Added support for `stringPlugValueWidget:placeholderText` metadata (#3218).
- Widget : Improved interaction with stylesheet. Widgets now provide `gafferClass` and `gafferClasses`.
  Qt properties which allows stylesheets more precise control (#3229).
- MetadataWidget : Added new class and derived classes to allow editing of metadata values via
  the UI (#3143).
- UIEditor : Added support for registering custom PlugValueWidgets and associated metadata (#3143).
- TestRunner : Added new class with features for detecting performance regressions. Use the
  `PerformanceTestMethod` and `PerformanceScope` nested classes to annotate unit tests which test
  performance (#3127, (#3265).
- Plug : Deprecated `Cacheable` flag. Override `computeCachePolicy()` instead (#3174).
- Reference : Added `hasMetadataEdit()` method (#3258).
- ImageGadget : Added `set/getLabelsVisible()` accessors (#3273).
- ImageView : Added `createDisplayTransform()` static method (#3273).
- UVView : Added new View subclass for viewing UVs and textures (#3273).
- SourceSet : Added new Set subclass whose contents automatically track the source node for the
  current scene selection (#3270).
- NodeSetEditor (#3270) :
  - Added `setNodeSetDriver()`/`getNodeSetDriver()` methods to link editors.
  - Added `drivenNodeSets()` method to query linked editors.
  - Added `nodeSetDriverChangedSignal()` and `drivenNodeSetsChangedSignal()` signals
    to allow editor links to be observed.
  - Added `registerNodeSetDriverMode()` to allow custom link modes to be added.

Build
-----

- Arnold : Updated to version 5.3.1.0.
- Appleseed : Updated to version 2.0.5-beta.
- OpenEXR : Updated to version 2.3.0.
- OpenVDB : Updated to version 6.0.0.
- Blosc : Updated to version 1.15.1.
- PySide : Updated to version corresponding with Maya 2018 Update 6.
- Cortex : Updated to version 10.0.0-a59.
- TBB : Updated to version 2018 Update 5.
- Alembic : Added python bindings.
- Improved debugging support (#3070) :
  - Added support for using ASAN option with GCC.
  - Enabled TBB debugging features in DEBUG builds.
  - Added `-fno-omit-frame-pointer` compiler flag for RELWITHDEBINFO builds.
- Fixed warnings when building with XCode 10.2 (#3094).
- Fixed problem where some Arnold modules were installed when `ARNOLD_ROOT` was
  not specified (#3101).
- Made GafferCortex an optional component at build time (#3168).
- Reduced the number of errors thrown during documentation build (#3212).

Breaking Changes
----------------

- OSLObject/OSLImage :
  - The loading of networks from versions prior to Gaffer 0.45 is no longer supported (#3192, #3218).
  - Added a `useTransform` plug to OSLObject. This must now be turned on before a shader can query
    transforms (#3226).
- ShaderAssignment : Removed support for using the `scene:path` context variable in shader
  networks. Temporary backwards compatibility can be enabled by setting the `GAFFERSCENE_SHADERASSIGNMENT_CONTEXTCOMPATIBILITY` environment variable to `1` (#3074).
- OSLObject : Removed support for using the `scene:path` context variable in shader
  networks. Temporary backwards compatibility can be enabled by setting the `GAFFEROSL_OSLOBJECT_CONTEXTCOMPATIBILITY` environment variable to `1` (#3074).
- GraphComponent :
  - Added `parentChanged()` virtual method (#3080).
    > **Caution** : Experience in the Gaffer codebase suggests that `parentChanged()` was a
    > relatively common method name, which may now be inadvertently overriding the new
    > virtual method. Clang will warn for these cases if `-Wall` is used, but GCC requires
    > `-Woverloaded-virtual` to be used.
- TaskNode::Task (#3024, #3025) :
  - Removed `hash()` method and associated member data.
  - Removed deprecated `node()` method.
  - Removed less-than operator.
  - The equality operator now compares plug and context instead of
    hash.
- ArrayPlug : Inputs are now required to be ArrayPlugs too (#3116).
- BackdropNodeGadget/StandardNodeGadget : Removed private member variables (#3028).
- SceneTestCase : Changed signatures for the following functions (#3060) :
  - `assertPathsEqual()`
  - `assertScenesEqual()`
  - `assertPathHashesEqual()`
  - `assertPathHashesNotEqual()`
  - `assertSceneHashesEqual()`
  - `assertSceneHashesNotEqual()`
- Shader : Changed base class to ComputeNode (#3074).
- TweakPlug : Added compulsory ValuePlug argument to constructor used for serialisation (#3084).
- AnimationEditor : Removed `connectedCurvePlug()` method (#3106).
- ParallelAlgo : Replaced `registerUIThreadCallHandler()` with `push/popUIThreadCallHandler()` (#3101).
- Renderer API : Added `lightBlocker()` virtual method (#3020).
- CompoundDataPlug : Removed MemberPlug and `addMember()` as well as `addOptionalMember()`. Use NameValuePlug instead (#3161).
- TransformTool : Added private members (ABI change only - source compatibility is maintained) (#3144).
- RenderController : Added argument to `updateInBackground()` (ABI change only, source compatibility is maintained) (#3144).
- SceneGadget : Added new private member (ABI change only, source compatibility is maintained) (#3144).
- LightVisualiser : The signature for `visualise()` now also includes the attributes (#3180).
- StandardLightVisualiser :
  - `pointRays()` now takes an optional argument specifying the light's radius (#3199).
  - `environmentSphere()` now requires an additional `maxTextureResolution` argument (#3219).
- LightFilterVisualiser : `visualise()` now takes `attributes` as additional argument (#3260).
- BranchCreator : Added `affectsBranch*()` and `constantBranchSetNames()` virtual methods (#3176).
- EvaluateLightLinks : Removed. This was a node used internally to translate light links to renderers,
  work that is now done in RendererAlgo (#3265).
- Context : Changed base class for `Scope`/`EditableScope`, and removed private member from `Scope`. Source compatibility is preserved (#3196).
- Process : Changed base class, and removed optional `currentContext` argument from protected constructor (#3196).
- Monitor (#3196) :
  - Changed base class to `IECore::RefCounted`.
  - Removed `setActive()/getActive()` methods. Use the Scope class instead.
- ComputeNode : Added virtual methods (#3174).
- ValuePlug : Removed `getObjectValueIfCached()` method (#3174).
- TypedObjectPlug : Removed `getValueIfCached()` method (#3174).
- GafferCortex : Removed GafferCortex module from standard builds (#3253).
- Style : Changed color arguments to `renderLine()` and `renderText()` from `Color3f` to `Color4f` (#3273).

0.53.6.3 (relative to 0.53.6.2)
========

Improvements
------------

- VectorTypedParameterHandler : Added support for Color3fVectorParameter (#3228)
- CompoundVectorParameterValueWidget : Now preserves selection when editing data (#3228)

Build
-----

- ie/options: Added support for Houdini 17.5 (#3215)

0.53.6.2 (relative to 0.53.6.1)
========

Improvements
------------

- CustomAttributes : Added extraAttributes plug that can be set from CompoundData (#3191)
- StandardLightVisualiser : Setting locatorScale to 0 now avoids costly computations (#3178)
- GafferUI : Added compatibility patch to allow >0.54 layouts to load (#3206)

Fixes
-----

- MultiLineTextWidget : Fixed unicode handling in `selectedText()` (#3183)
- SplineWidget : Fixed display transform management bug (#3187)
- ArnoldLight : Nodules no longer disappear when copy/pasting Arnold quad_light and skydome_light nodes (#3188)

0.53.6.0 (relative to 0.53.5.0)
========

Improvements
------------

- FileSequenceParameterValueWidget : Added support for typeHint:includeSequences (#3164).

 Fixes
-----

- ViewportGadget::SelectionScope : Fixed bug causing GL attribute state to leak (#2991).
- GafferUI::PlugValueWidget : Fixed bug causing output plugs to be unaffected by context (#3132).
- GafferImage::BleedFill : Fixed bug regarding negative inputs (#3132).
- TransformTool :
  - Fixed issue causing unnecessary work when disabled (#3144).
  - Fixed crash in selection processing code (#3136).
- Stats app : Fixed context management bug when computing image properties (#3147).
- Docs : Fixed broken link in introduction (#3140).

0.53.5.0 (relative to 0.53.4.0)
========

Features
--------

- Reference : Added support for fileName search paths (#3049).
  - Set the new `GAFFER_REFERENCE_PATHS` environment variable in order to load relative Reference files.

Improvements
------------

- ArnoldShader/ArnoldLight :
  - Added support for "gaffer.default" and "gaffer.userDefault" metadata (#3112).
    There is an example .mtd file which provides Arnold 5.2 compatibility in contrib/arnold (#3115).
  - Exposed the geometry parameters for the `standard_surface` shader in the NodeEditor (#3104).

Fixes
-----

- Catalogue : Fixed bug when viewing a Catalogue after a ShaderView (#3113).
  - Note this is actually a change to ShaderPlug itself, not to Catalogue.
- Camera : Fixed bug in compatibility config (#3100).
- Wedge : Fixed to work without compatibility configs (#3122).
- AnimationEditor : Fixed bug affecting animated promoted plugs (#3106).
- UIEditor : Fixed bug with '/' in presets (we now replace '/' with '_') (#3103).
- Viewer : Fixed potential deadlocks when editing the camera in the Viewer (#3121).

Documentation
-------------

- Added "Anatomy of a Camera" article to "Working with Scenes" section (#3050).
- Added missing shortguts for "Controls and Shortcuts" (#3111).
- Fixed recent screengrab errors and build targets (#3066).
- Fixed shader assignment variable in Python tutorial (#3099).
- Fixed reference to 'root' in Expression Scripting Reference (#3107).

0.53.4.0 (relative to 0.53.3.0)
========

Improvements
------------

- ArnoldShaderUI (#3087) :
  - Added support for `gaffer.layout.section.<sectionName>.collapsed`
    metadata.
  - Improved NodeEditor layout for barndoor and light_decay shaders.

Fixes
-----

- Layout menu : Fixed crashes removing a panel while using Gaffer in Maya (#3091).
- ShaderTweaks : Fixed crashes when copying and pasting a ShaderTweaks node (#3084).
- OSL ShadingEngine :
  - Fixed initialisation of `dPdz` in shader globals (#3083).
  - Fixed intermittent crashes seen at shutdown (#3093).
- CompoundDataPlug : Fixed GIL management bugs for `fill*()` methods (#3079).
- Documentation : Fixed typos in ArnoldOptions documentation (#3081).

0.53.3.0 (relative to 0.53.2.0)
========

Features
--------

- ArnoldOptions : Added settings for enabling GPU rendering (#3076).

Improvements
------------

- GraphEditor : Added navigation items to the connection context menu. These allow
  quick navigation to the source or destination node (#3064).
- SceneInspector : Added fields for subdivision creases and corners (#3067).
- GafferUI : Added Markdown support in tooltips (#3065).

Fixes
-----

- Render : Fixed bug which prevented non-SceneNodes (for instance, Switches or
  ContextVariables nodes) from rendering (#3061).
- ValuePlug : Fixed GIL management bugs. These were most visible in a hang caused
  by toggling exposure in the ImageView while background processing was being performed (#3068).
- SceneInspector : Fixed drag and drop of PrimitiveVariables (#3067).
- Instancer (#3072) :
  - Fixed crashes caused by duplicate ids. Duplicates are now ignored.
  - Fixed child ordering to be ascending by id.
- GraphEditor : Fixed bug drawing auxiliary connections to sizeless parent nodules (#3069).

API
---

- DocumentationAlgo : Added `markdownToHTML()` method (#3065).

0.53.2.0 (relative to 0.53.1.1)
========

Features
--------

- ArnoldCameraShaders : Added a new node used to define shaders for cameras (#2676, #3040, #3058).
  - We currently support filtermap and uv_remap shaders.
  - Use a ShaderAssignment node to assign it to a camera.

Improvements
------------

- SubTree : Entering an invalid root location no longer generates an error. An
  empty scene is output instead (#3035).
- CollectScenes : Entering an invalid sourceRoot no longer generates an error. An
  empty scene is collected instead (#3055).
- Duplicate : Targets with an invalid name no longer generate an error. The input
  scene is passed through unchanged instead (#3055).
- ArnoldLight : Added file browser for photometric_light (#3041).

Fixes
-----

- PythonCommand : Fixed crashes caused by missing context variables (#3027, #3029).
- GraphEditor : Prevented the insertion of Dot nodes into read only connections (#3032).
- Set : Added support for '.' in set and object names (#3037).
- CameraTool : Fixed to work with animated transforms (#3034).
- Animation : Fixed precision loss when serialising keyframes (#3034).
- BoxOut : Fixed crash in `acceptsInput()` (#3042).
- ShaderAssignment : Fixed bug with Switch node plugged directly into shader input (#3052).

0.53.1.1 (relative to 0.53.1.0)
========

Fixes
-----

- PathListingWidget : Fixed GIL management bug which could cause hang when
  interacting with the HierarchyView (#3018).
- PlugValueWidget/PresetsPlugValueWidget : Fixed bugs handling leading '/'
  characters in preset names (#3016).

0.53.1.0 (relative to 0.53.0.0)
========

Improvements
------------

- Viewer : The "Edit Tweaks..." menu item now supports CameraTweaks nodes in addition
  to ShaderTweaks (#3013).
- HierarchyView : Added `Alt+E` and `Alt+Shift+E` shortcuts, matching those found in the
  Viewer (#3013).

Fixes
-----

- GLWidget : Fixed corrupted font rendering in overlay widgets (#3002).
- SceneInspector : Fixed display of empty shader networks (#2997).
- ShaderTweaks : Fixed auto-connection bugs that could cause a newly
  created node to be connected to inappropriate inputs (#3007).
- TweakPlug : Fixed `createCounterpart()` method, so TweakPlugs may now be promoted (#3007).
- NodeEditor : Fixed bug that could cause keyboard focus to be lost when switching
  between nodes (#3008).

API
---

- SceneAlgo : Added `objectTweaks()` method, for finding the last tweak node in an
  object's history (#3013).
- KeyEvent : Added equality operators (#3013).
- TweaksPlug : Added new class for holding a collection of TweakPlugs (#3007).

0.53.0.0 (relative to 0.52.x)
========

This release provides several features useful for look development, including component-level
connections for colour and vector parameters, a new ShaderTweaks node for making downstream tweaks,
and an ArnoldTextureBake node for baking UV textures. We've also added a nifty new system for quickly
accessing nodes via numeric hotkeys, and made numerous other enhancements and bug fixes.

> Caution : This release replaces nodes such as SceneLoop and ImageLoop with more general purpose
> nodes such as Loop. Backwards compatibility is provided for loading old scripts, but any scripts
> saved in Gaffer 0.53 will _not be loadable in previous versions_. Test carefully before upgrading,
> because there is no going back.

Features
--------

- ArnoldTextureBake : Added a new node for baking Arnold shading networks down into
  UV textures (#2931).
- Numeric bookmarks : Added the ability to associate a numeric hotkey to a node, providing
  quick pinning of the node into any editor. Use `Ctrl+[0-9]` in the GraphEditor to assign
  the bookmark, and then simply hit `[0-9]` to pin that node into the editor below the
  cursor (#2974).
- ShaderTweaks : Added a new node to allow shader parameters to be overridden
  downstream of the shader assignment. This replaces the old LightTweaks node, with
  the addition of new functionality to allow new connections to be made (#2954, #2983).
- GraphEditor : Added support for making connections to the individual components of colour
  and vector parameters (#2938, #2973, #755).
- Viewer (#2985, #2666, #2717, #3001) :
  - Added "History" context menu for the selected scene object.
    - Added "Edit Source..." to open a NodeEditor for the node that created the object.
    - Added "Edit Tweaks..." to open a NodeEditor for the most recent ShaderTweaks node
      applied to the object.
- BoxOut : Added a `passThrough` plug, providing a convenient way of allowing
  Boxes to be disabled (#2879).
- UDIMQuery : Added a new node to query the texture UDIMs used by a set of
  objects (#2913).
- Wireframe : Added a new node for converting MeshPrimitives into a wireframe
  representation using CurvesPrimitives (#2914).

Improvements
------------

- Loop : Added plug context menu item for connecting previous to next (#2887).
- ArnoldOptions :
  - Added adaptive sampling settings (#2919).
  - Added low light threshold (#2968).
  - Added support for JSON stats files (#2984).
- ArnoldRender (#2919) :
  - Added support for a "camera" parameter in outputs, allowing renders from
    multiple cameras to be performed in a single process.
  - Added support for Arnold's `uv_camera`.
- SceneInspector : Added curve basis to Object section (#2892).
- Dispatch app : Added `-show` argument to control which nodes are shown
  in `-gui` mode (#2900).
- Dispatcher (#2942) :
  - Added `dispatcher:scriptFileName` context variable.
  - Added support for nested dispatchers, with the inner dispatch sharing the
    job directory for the outer dispatch (#2942).
- Dot/ContextProcessor/Switch/Loop : Improved serialisation to use a call to `setup()`
  rather than manual creation of plugs. This makes the serialisation format a better
  learning tool for aspiring scripters (#2981).
- BoolPlugValueWidget : Added colour to indicate animation inputs and compute errors
 (#2990).
- OSLShader : Improved nodule labelling (#2983).
- PlugAdder : Added support for label metadata (#2345, #2983).
- Shader/Light : Improved the representation of shaders in the scene dataflow. These
  now use a dedicated `IECoreScene::ShaderNetwork` class rather than a cumbersome
  `IECore::ObjectVector`. This lays the groundwork for features such as downstream
  tweaks (#2902).
- GraphEditor : Changed hotkey for the Bookmarks menu from `Ctrl+B` to `B` (#3000).
- Error Handling : Added the plug full name, frame, and scene path (if applicable)
  to the logging output as additional `DEBUG` log messages (#2976).

Fixes
-----

- ValuePlug : Fixed bug in finding the ComputeNode for a plug. In specific
  circumstances this could cause a `Value for Plug not set as expected`
  error (#2955, #2950).
- ViewportGadget/GadgetWidget : Fixed enter/leave event handling bug (#2938).
- ShaderAssignment : OSL shaders of type "shader" are now assigned correctly
  as "osl:surface" and not "osl:shader" (#2983).
- Metadata bindings : Fix crashes caused by calling `value( None )` (#2996).

Documentation
-------------

- Improved the "Getting Started" scripting tutorial, renaming it to "Node Graph
  Editing in Python".
- Added "Working with the Node Graph" section, including documentation for
  Box nodes in particular.
- Improved the "Controls and Shortcuts" section (#2929).

API
---

- SceneAlgo (#2985, #3001) :
  - Added `history()` method for returning the tree of operations used
    to generate a a particular part of the scene.
  - Added `source()` method to return the node originally responsible for
    the creation of a particular location.
  - Added `shaderTweaks()` method to return the most recent ShaderTweaks
    node applied to an attribute.
- Metadata (#2953) :
  - Values may now be registered for plugs of a specific type.
  - Values may now be registered to specific named descendants of plugs
    of a specific type.
- CompoundNumericNodule : Added new nodule type to allow connections to be
  made to child components (#2938).
- MetadataAlgo : Added methods for numeric bookmarks (#2974).
- ContextProcessor : Added `setup()`, `inPlug()` and `outPlug()` methods (#2880).
- Loop : Added `setup()`, `inPlug()` and `outPlug()` methods (#2887).
- TweakPlug (#2954, #2983) :
  - Added default template argument to `valuePlug()` method.
  - Made `applyTweak()` const.
  - Added `mode` argument to convenience constructors.
  - Added `applyTweaks()` method for tweaking `ShaderNetworks`.
  - Added support for connecting new shaders into a `ShaderNetwork`.
- Nodule : Added `nodule()` virtual method, used to return a nodule for a child
  plug (#2938).
- GraphBookmarksUI : Removed `popupFindBookmarkMenu()`. Use `connectToEditor()`
  instead (#2974).
- ProcessMessageHandler : Added a MessageHandler for injecing `Gaffer::Process`
  information as additional `DEBUG` log messages (#2976).

Build
-----

- Replaced DEBUG option with BUILD_TYPE, with values of DEBUG, RELEASE or RELWITHDEBINFO (#2593).

Breaking Changes
----------------

- LightTweaks : Replaced with new general-purpose `ShaderTweaks` node (#2954).
- Shader : Shaders are now represented with `IECoreScene::ShaderNetworks` rather than
  `IECore::ObjectVectors` (#2902).
- Dispatcher : The base class now saves the script to dispatch automatically, so derived
  classes no longer need to do so (#2942).
- Metadata (#2953) :
  - Removed all deprecated methods.
  - `NodeValueFunction` has been replaced by a generic `GraphComponentFunction`. This allows
     metadata to be registered by Plug TypeId.
- TweakPlug :
  - Changed signatures for `applyTweak()` and constructor (#2954).
  - Changed base class (#2983).
- ContextProcessors : Removed SceneContextVariables, DeleteSceneContextVariables,
  SceneTimeWarp, ImageContextVariables, DeleteImageContextVariables and ImageTimeWarp nodes.
  Use the generic equivalents instead. Compatibility with old scripts is provided by
  converting them automatically on loading (#2880).
- Loops : Removed SceneLoop and ImageLoop nodes. Use the generic Loop node instead.
  Compatibility with old scripts is provided by converting them automatically on
  loading (#2887).
- ScriptEditor (#2876) :
  - Renamed to `PythonEditor`. Compatibility with old scripts and layouts is preserved
    by a config file.
  - Removed `script` variable. Use the new `root` variable instead.
  - Removed `parent` variable. Paste serialised scripts using the GraphEditor
    instead.
- Screengrab app : Renamed `-scriptEditor` argument to `pythonEditor` (#2876).
- Dispatch app : Renamed `-nodes` argument to `-tasks` (#2900).
- Nodule : Added virtual method (#2938).
- ScriptNode : Removed `scriptExecutedSignal()` (#2996).

0.52.3.5 (relative to 0.52.3.4)
========

Fixes
-----

- GLWidget : Fixed corrupted font rendering in overlay widgets (#3002).
- Context : Fixed fallback value for `get()` method (#2987).
- GraphLayout : Fixed GIL management bugs that could cause deadlock (#2988).
- TweakPlug : Fixed `createCounterpart()` method, so TweakPlugs may now be promoted (#3007).
- NodeEditor : Fixed bug that could cause keyboard focus to be lost when switching
  between nodes (#3008).

0.52.3.4 (relative to 0.52.3.3)
========

Fixes
-----

- Primitive Inspector : Fixed EditorWidget error (#2958).
- Graph Editor : Fixed scaling so it is centred on cursor position (#2965).
- Animation : Fixed possible deadlock when setting a key (#2970).
- ImageGadget : Fixed conflict with GLSL 'active' keyword (#2971).
- Light : Fixed light linking during IPR update (#2969).
- gui app : Fixed keypress handling of Ctrl+B (#2975).

0.52.3.3 (relative to 0.52.3.2)
========

Fixes
-----

- Arnold renderer : Fixed light linking bug (#2947).
- ViewportGadget : Fixed bug in orthographic camera projection. This prevented the
  CropWindowTool from working (#2946).

0.52.3.2 (relative to 0.52.3.1)
========

Fixes
-----

- gui : Fixed crash when starting Gaffer with unicode in the clipboard (#2933).
- TransformTool : Fixed crash caused by selection deduplication (#2940).
- ImageTransform : Fixed bug when rotating an empty data window (#2932).
- ImageView : Fixed TypeId bug (#2937).
- Arnold : Fixed crash when using shadowGroups (#2934).

0.52.3.1 (relative to 0.52.3.0)
========

Fixes
-----

- ArnoldMeshLight : Fixed light linking bug. ArnoldMeshLights are now included in the
  `defaultLights` set by default. A new `defaultLight` plug controls this behaviour,
  matching the `defaultLight` plug on other Light nodes (#2926).

0.52.3.0 (relative to 0.52.2.0)
========

Features
--------

- BleedFill : Added new image node to fill areas with zero alpha by bleeding in colours
  from adjacent image regions (#2909).
- Rectangle : Added new image node to annotate rectangular regions of an image (#2912).

Improvements
------------

- Light linking (#2875) :
  - Added a "defaultLights" set for use in light linking set expressions.
  - Added a "defaultLight" plug to all Light nodes, to control membership in
    the "defaultLights" set.
  - Significantly optimised the processing of light links in Gaffer and in
    the Arnold renderer backend.
- Viewer : "userDefault" metadata can now be used to configure the default settings
  for Views (#2893).
- PythonCommand/SystemCommand : Empty commands are now ignored (#2896).
- SceneWriter : Added support for subclassing in Python (#2901).
- Checkerboard : Improved performance (#2912).

Fixes
-----

- SceneInspector : Fixed bug which caused sections to be disabled (#2903).
- Layout Menu : Fixed clashes between custom layout names and standard menu items. For instance,
  previously you could save a layout called "Delete" and it would mean that the standard "Delete"
  submenu was no longer available (#2899).
- Grade : Fixed bug that caused clamping to be ignored if the other settings were at default
  values (#2908).
- CompoundDataPlug/ValuePlug : Fixed GIL management bugs which could cause Gaffer to hang (#2907).

0.52.2.0 (relative to 0.52.1.0)
========

Improvements
------------

- Bookmarks (#2873) :
  - Added Ctrl+B shortcut to quickly navigate to a bookmark in any editor.
  - Added bookmarks to pinning icon context menu.
- TransformTool (#2850) :
  - Added status widget with information about what is being edited (#2753).
  - Added support for transforming an ancestor location if the selected location
    is not movable. This is particularly convenient for transforming the output of
    a SceneReader node.
- Wrapper : Added GAFFER_EXTENSION_PATHS environment variable for easy configuration of 3rd
  party extensions (#2868).
- StandardOptions : Added a depthOfField enable toggle (default off) (#2890).
- Camera/CameraTweaks : Added a depthOfField render override (#2890).

Fixes
-----

- GUI Config : Fixed layout registration bug that caused the standard layouts to be
  copied into the user preferences. This caused problems running older Gaffer versions
  and broke the saving of custom layouts (#2891).
- Cameras : Fixed on-by-default depth of field rendering for cameras with an fStop
  specified. In particular this affected cameras imported to Gaffer via Alembic. The
  `depthOfField` plug on the StandardOptions node must now be used to turn depth of field
  on explicitly (#2890).
- Arnold metadata : Added missing metadata for Arnold 5.2 shader parameters (#2883).
- TransformTool (#2850) :
  - Fixed attempts to edit read-only plugs inside References.
  - Fixed `Selection::scene` so that it doesn't refer to internal plugs of
    the tool.
- Menus : Fixed search widget focus styling on Mac (#2873).
- Clipboard : Fixed bug that meant Gaffer's clipboard was not synchronised with
  the system clipboard on startup (#2878).
- Instancer : Fixed division by zero bug (#2886).
- Switch : Fixed overzealous dirty propagation. These could cause unnecessary
  viewer and/or interactive render updates (#2859).

API
---

- Tool : Made `view()` method public (#2850).
- GraphComponent : Added default value for `commonAncestor()` type (#2850).
- Menu : Fixed position of search widget when menu has title (#2873).
- Editor : Editors now grab keyboard focus on enter. This makes it easier to add
  custom shortcuts from extension code (#2873).
- CompoundEditor : Added `nodeSetMenuSignal()`, used for customising the context
  menu for the pinning icon (#2873).

Build
-----

- Added VDB_LIB_SUFFIX option (#2889).

0.52.1.0 (relative to 0.52.0.0)
========

Features
--------

- PrimitiveInspector : Added new editor panel for inspecting the values of all
  primitive variables associated with the object at the selected location (#2863).

Fixes
-----

- Fixed FilterSwitch compatibility within boxes (#2866).
- SceneWriter : Fixed unnecessary messages about unsupported features from
  the Alembic writer (#2865).
- USD : Fixed python errors due to clashing symbols (#2837).

API
---

- VectorDataWidget (#2863) :
  - Added `horizontal/verticalScrollMode` constructor arguments.
  - Added `set/getHeader()` accessors.
  - Fixed various issues with the header and tooltips.
  - Restricted column tooltips to the header.
  - Added alternating column background colours.
  - Added support for many new data types (eg vectors, matrices, boxes, quats,
    char, short).
- GafferUI : Moved ScrollMode enum from ScrolledContainer to Enums (backwards
  compatibility is provided) (#2863).

0.52.0.0
========

This release brings a major overhaul to Gaffer's camera definition, bringing more
flexibility and improved compatibility with USD and Alembic. Note that if you were
previously using a Parameters node to add a "screenWindow" parameter, you should
now manipulate the standard aperture and film fit settings instead.

Features
--------

- Camera : Adopted new camera definition (#2816)
  - Added perspectiveMode, with "Field of View" and "Aperture and Focal Length"
    modes.
  - Added aperture settings.
  - Added depth of field settings.
  - Added optional render overrides that override the StandardOptions settings on
    a per-camera basis.
  - Improved compatibility with USD and Alembic.
- CameraTweaks : Added new node to apply downstream edits to camera parameters (#2816).
- StandardOptions : Added filmFit render option (#2816).

Fixes
-----

- Restored FilterSwitch/UnionFilter compatibility for files from version 0.27.0.0 (#2854).
- SceneGadget : Fixed depth sorting for `objectAt()` when used with some legacy
  graphics drivers (#2816).
- Fixed overzealous dirty propagation in several nodes. These could cause unnecessary
  viewer and/or interactive render updates.
    - SceneElementProcessor (#2855)
    - ImageNode (#2855)
    - Switch (#2859)
- OpenGLRenderer : Fixed GL resource management threading bug. This was the cause of
  rare crashes when collapsing locations in the viewer (#2851).
- Documentation : Fixed broken link (#2857).

API
---

- PlugAlgo : Added `createPlugFromData()` and `extractDataFromPlug()` methods (#2816).
- ViewportGadget : Added `set/getPlanarMovement()` methods (#2816).
- Packaged IECorePreview and IECoreScenePreview headers. Note that these are subject to
  change without notice (#2862).

Breaking Changes
----------------

- CompoundDataPlug : Removed `createPlugFromData()` and `extractDataFromPlug()` methods (#2816).
  Use PlugAlgo instead (#2816).
- RendererAlgo : Added `scene` argument to `applyCameraGlobals()` (#2816).
- ViewportGadget : Removed `set/getOrthographic3D()` methods. Use `set/getPlanarMovement()`
  instead (#2816).
- SceneAlgo : Added `scene` argument to `shutter()` method (#2816).
- Camera : Adopted new camera definition (#2816). In particular, if you were using a "screenWindow"
  parameter, you will now need to use aperture and/or filmFit instead.

0.51.0.0
========

This release provides support for the latest versions of Arnold and 3Delight (5.2 and 1.1.7
respectively), along with the usual mix of improvements and bug fixes.

> Caution : The specialised switch nodes such as SceneSwitch and ImageSwitch have been replaced
> with a single all-purpose Switch node. Compatibility for old files is provided by converting
> nodes during loading, but files saved from Gaffer 0.51 will not be useable in prior versions.
> This can be worked around with a config file in the previous version which does
> `Gaffer.Switch = Gaffer.SwitchComputeNode`.

Features
--------

- Arnold : Added support for Arnold 5.2. Please note that Arnold 5.2 is not compatible with
  earlier Arnold versions, so if you wish to use Gaffer 0.51 with an earlier version, you
  will need to compile Gaffer yourself.
- 3Delight : Updated to support version 1.1.7. Please note that earlier versions are no
  longer supported.

Improvements
------------

- Viewer :
  - Improved interactivity when using transform tools or scrubbing animation
    (#2818).
  - Added "Escape" hotkey to pause processing (#2838, #2843).
- SceneInspector :
  - Added inspection of light and shader parameters (#2797).
  - Added annotation for indexed primitive variables (#2824).
- ScriptNode : Added "frameRange:start" and "frameRange:end" context variables (#2811).
- Documentation : Added "Anatomy of an Image" article (#2832).
- Switch (#2123, #2812) : Replaced specialised nodes with a single all-purpose Switch node.

Fixes
-----

- SceneInspector :
  - The order in which diffs are displayed now matches the order
    in which objects are selected in the Viewer (#2814).
  - Fixed formatting of Color4f values (#2797).
- GraphEditor : Fixed problems with `nodeDoubleClickSignal()` (#2821)
    - The signal didn't respect slot return values, so a slot couldn't return True
      to signify that it had handled the event, and block other slots.
    - The default slot wasn't returning True.
- Catalogue : Fixed delay when adding image with downsteam network (#2827).
- AnimationEditor : Fixed numerical imprecision when snapping keys to whole frames
  (#2820).
- RenderController :
  - Fixed bug where objects failed to render after being removed from
    the lights set (#2825).
  - Fixed GIL management bugs (#2830).
- SceneView : Fixed bugs that could lead to a hang in the viewer
  when expanding or collapsing the current selection (#2830).
- SceneGadget : Fixed GIL management bugs (#2830).
- Houdini : Fixed compilation with default build flags for Houdini 17 (#2829).
- TransformTools : Fixed bug which prevented the editing of promoted transform
  plugs (#2831).
- ImageGadget : Fixed bug which prevented non-default dataWindow maximum coordinates
  from being annotated in the Viewer (#2840).
- TaskNode : Fixed bugs preventing implementation via internal network (#2846).
- OpenGLRender (#2799) :
  - Fixed crash when trying to use `gaffer execute` with OpenGLRender nodes.
  - Fixed bug whereby the visualisation of the main render camera was visible.
- Arnold : Fixed tests for API changes in Arnold 5.2 (#2841).

API
---

- BackgroundTask : Added `waitFor()` method (#2818).
- Added MAKE_GAFFER_COMPATIBILITY_VERSION macro (#2819).
- ContextAlgo : Added GlobalScope utility class (#2812).
- Switch :
  - Added `inPlugs()` and `outPlug()` methods (#2812).
- FilterPlug : Add `sceneAffectsMatch()` method (#2812).
- TransformTool : Add `selectionChangedSignal()` (#2848).

Breaking Changes
----------------

- Removed compatibility for loading files from Gaffer 0.15.0.0 and earlier.
  Resave the file in a more recent version before loading in the current
  version. Note that this can also expose bugs in custom scripts : if a script
  incorrectly attempts to connect to an ArrayPlug instead of a child element,
  this will now fail instead of being silently corrected (#2805, #2812).
- Switch (#2812) :
  - Removed SwitchDependencyNode, SwitchComputeNode, SceneSwitch, ShaderSwitch, FilterSwitch,
    and ImageSwitch nodes. Use Switch node instead. Backwards compatibility for old files is
    provided by converting to Switches during loading.
- 3Delight : Removed compatibility for older versions. At the time of writing
  3Delight 1.1.7 is the latest tested version (#2836).
- SceneGadget : Removed private member variable. Source compatibility is retained
  (#2818).
- Filter : Made `sceneAffectsMatch()` protected. Use the new `FilterPlug::sceneAffectsMatch()`
  method instead (#2812).
- UnionFilter : Removed compatibility for nodes created prior to version 0.28.0.0 (#2812).
- TransformTool : Added private member data (#2848).

0.50.0.0
========

Improvements
------------

- TransformTools : Added support for multiple selection (#2665, #2803).

Fixes
-----

- CameraTool/TransformTool (#2807, #2808) : Mitigated against crashes during Catalogue
  image saving.

API
---

- GafferSceneUI::ContextAlgo : Added `set/getLastSelectedPath()` functions, used for
  specifying the last location to have been selected (#2803).

Breaking Changes
----------------

- TransformTool (#2803) :
  - Moved `orientedTransform()` method to `Selection` class.
  - Changed `selection()` return type.

0.49.1.0
========

Improvements
------------

- SceneReader : Added transform plug, allowing caches to be positioned without needing a
  separate Transform node (#2792).

Fixes
-----

- SubGraph : Fixed crash bug in `correspondingInput()`. This typically manifested itself
  as a crash when trying to delete or cut a box (#2796).
- FileMenu : Added confirmation dialogue for "Revert to Saved", and added proper error
  reporting for loading errors (#2735, #2794).
- SetUI/FilteredSceneProcessorUI : Fixed bugs dealing with ArrayPlug inputs. These were
  most visible as errors when working with the CopyAttributes node (#2785).
- File Browser : Fixed crash when pointed at files with strange permissions. (#2800).
- GraphEditor : Fixed hangs when framing backdrops (#2801).

Documentation
-------------

- Added "Anatomy of a Scene" article (#2787).

API
---

- ParallelAlgo : Refactored `callOnUIThread()` internals (#2786).

0.49.0.1
========

Fixes
-----

Python bindings : Fixed several bugs which could cause Gaffer to hang (#2789).

0.49.0.0
========

Improvements
------------

- ArnoldAttributes : Added `shadowGroup` attribute for performing shadow linking
  (#2754).
- ScaleTool : Added handles for scaling in the XY, XZ and YZ planes (#2760, #2664).
- RotateTool : Added support for free rotation by dragging on a virtual
  sphere (#2760, #2664).
- TranslateTool : Made XY, YX and YZ handles more visible (#2760, #2664).
- Translate/Rotate/Scale tools :
  - Added support for animation (#2721).
  - Added control over the size of the handle via the `+` and `-` keys (#2671, #2769).
- Catalogue (#2702) :
  - Multiple images may now be selected.
  - The selected images can now be deleted via the `Delete` and `Backspace`
    keys.
  - Images can now be reordered using drag and drop.
- OSLObject/OSLImage : Added support for more vector type conversions. Among other
  things, this allows Color4fData primitive variables to be read as `color` values
  in OSLObject, by discarding the alpha channel (#2759).
- GraphEditor : Added icons for Box and Reference nodes (#2762).
- Improved error message when a dependency cycle is detected. The error now
  includes the names of the plugs involved (#2745).
- AnimationEditor :
  - Keyframes are now pre-highlighted during drag-select (#2768).
  - The current frame can be set by clicking/dragging on the time axis (#2724).
  - When dragging keyframes in a single axis only, the viewport auto-scroll
    is now constrained to that axis (#2724).
- SceneReader/SceneWriter (Cortex 10.0.0-a29) :
  - Added support for scalar attributes in Alembic files.
  - Added support for quaternion primitive variables in Alembic files.
- MeshTangents : Added support for non-triangular faces (Cortex 10.0.0-a30).
- VDB : Added support for float and double metadata (Cortex 10.0.0-a31).

Fixes
-----

- TypedObjectPlug : Fixed GIL management bug that could result in the
  application hanging during operations such as choosing AOVs in the
  image viewer (#2765).
- ScriptNode : Fixed GIL management bug that could result in the
  application hanging during operations such as cut & paste (#2780).
- GraphEditor :
  - Fixed connection visibility context menu items so that they
    respect the read-only status of nodes (#2757).
  - Omitted connection visibility context menu items from the menu
    for auxiliary nodes, since such nodes do not have hideable connections
    (#2752, #2757).
  - Fixed bookmark drawing update bug (#2763).
  - Fixed plug label visibility bug (#2761).
- AnimationEditor (#2768) :
  - Fixed bugs with framerates other than 24fps.
  - Fixed selection management bug.
  - Improved numerical precision of keyframe dragging.
- Backdrop : Made resizing undoable (#2734).
- FileMenu : Closing a backup confirmation dialogue now aborts loading
  completely (#2749).
- Isolate : Fixed filter matching bug in set computation (#2748).
- Translate/Rotate/Scale tools : Fixed context management bug (#2760).
- CollectScenes : Replaced bogus ArrayPlug input with ScenePlug (#2726).
- Catalogue :
  - Fixed bug that caused CatalogueSelect nodes to be parented
    at the wrong level, if a nested Catalogue was promoted to the next level
    (#2702).
  - Fixed bug whereby image order changed if image deletion was undone (#2767).
- Offset : Fixed hangs caused by empty data windows (#2770).
- VDB : Fixed crashes caused by thread-safety bug. This manifested most
  commonly when instancing VDB objects (Cortex 10.0.0-a30).
- Seeds : Fixed cancellation bug (Cortex 10.0.0-a31).
- SceneReader : Fixed crashes caused by thread-safety bug in AlembicScene
  (Cortex 10.0.0-a32).

API
---

- Dispatcher : Fixed crashes caused by passing `None` to `frameRange()` method
  in Python (#2716).
- Added AttributeVisualiser.h to installation (#2744).
- ConfirmationDialogue : `waitForConfirmation()` now returns `None` if the user
  closes the dialogue (#2749).
- StandardStyle (#2760) :
  - Added support for XY,XZ and YZ axes in `renderScaleHandle()`.
  - Added support for XYZ rotation handle in `renderRotateHandle()`.
- Handle : Added `rasterScaleFactor()` protected method (#2760).
- MetadataAlgo : Added `bookmarkedAffectedByChange()` method (#2763).
- GraphComponent (#2767) :
  - Added python binding for `del graphComponent[childIndex]`.
  - The original child order is now restored when undoing
    calls to `removeChild()`.
- DependencyNode : Fixed crashes caused by Python derived classes returning
  `None` from `affects()` overrides (#2771).
- ViewportGadget : Added support for enabling/disabling drag tracking separately
  in each axis (#2724).

Documentation
-------------

- Added guidelines for contributing (#2713).
- Added code of conduct (#2713).
- Reworked the "Managing Complexity" section (#2623).
- Improved installation and configuration sections (#2624).
- Improved "Getting Started" tutorial (#2629).

Breaking Changes
----------------

- ScaleHandle : `scaling()` method now returns a `V3f` (#2760).
- RotateHandle (#2760) :
  - Changed signature of `rotation()` method.
  - Added private member data.
- RotateTool (#2760) :
  - Added private member data.
  - Changed signature of `rotate()` method.
- Style : Added `highlightVector` argument to `renderRotateHandle()` method (#2760).
- TransformTool : Added argument to `updateHandles()` method (#2671, #2769).
- ViewportGadget (#2724) :
  - Changed function signatures for `setDragTracking()` and `getDragTracking()` methods.
  - Changed private member variables.

0.48.1.0
========

Features
--------

- CollectTransforms : Added a node for collecting transforms from different
  contexts and storing them as attributes (#2708).
- CollectPrimitiveVariables Added a node for collecting primitive variables
  from different contexts (#2708).
- PrimitiveVariableExists : Added utility node for querying the existence
  of a primitive variable (#2708).

Improvements
------------

- ArnoldLight : Improved performance (#2718).
- SceneInspector : Added tooltips with the unabbreviated name of the item
  being inspected (#2722).

Fixes
-----

- Expression : Fixed threading bug in UI error handling (#2652, #2723).
- ColorProcessor/Shuffle : Fixed bugs caused by attempted computation of non-existent
 upstream channels (#2701, #2731).
- Light : Fixed bounds computation (#2725).
- AnimationGadget : Fixes crash caused by dragging keys on adjacent frames (#2720).

0.48.0.0
========

Features
--------

- Viewer : The 3D viewer now updates asynchronously, keeping the UI responsive while the scene
  is computed in the background (#2649).
- AnimationEditor : Added a new editor to allow the graphical editing of animation
  curves. This can be found on the tab next to the GraphEditor in the standard layouts (#2632).
- DeleteObject node (#2694).
- CopyAttributes node (#2710).

Improvements
------------

- TranslateTool : Added handles for movement in the XY,XZ,YZ and camera planes (#2709).
- Layouts menu (#51, #2698) :
  - Added "Default/..." menu items to allow the default startup layout to be chosen.
  - Added new "Save As/..." menu items to allow previously saved layouts to be replaced.
- SceneInspector (#2607) :
  - Added filter to sets sections.
  - Moved set computations to background process, so they don't block the UI.
- Shader : Improved performance (#2644).
- ArnoldLightUI : Added support for "userDefault" parameter metadata. This matches
  the format already in use for ArnoldShaderUI (#2646).
- Viewer :
  - Added selection mask, to choose which types of objects can be selected (#2696).
  - Added more Arnold diagnostic shading modes (#2645)
    - Matte
    - Opaque
    - Receive shadows
    - Self shadows
- ArnoldAttributes :
  - Added `volumeStepScale`, `shapeStepSize` and `shapeStepScale` attributes (#2634).
  - Clarified intended usage of subdividePolygons attribute (#2680).
- FormatPlug : Made "Custom" mode persistent, so it is remembered across save and reload (#2660).
- InteractiveRender : Removed unnecessary deletion and recreation of objects when `childNames`
  changes (#2690, #2649).

Fixes
-----

- GraphEditor :
  - Fixed arrowheads on axis-aligned auxiliary connections (#2647, #2648).
  - Fixed potential auto-scroll bug when dragging a node (#2705).
- LocalDispatcher/TractorDispatcher : Fixed problems using `imath` context variables (#2653, #2654).
- OSLObject : Fixed crashes caused by indexed primitive variables (#2655).
- Viewer : Fixed visibility of children of look-through camera (#2694).
- ObjectSource : Fixed transform.* -> out.bound dirty propagation (#2649).

API
---

- SceneGadget :
  - Added `setPaused()/getPaused()` and `state()` methods (#2649).
  - Replaced `baseState()` with `set/getOpenGLOptions() methods (#2649).
  - Added `waitForCompletion()` method (#2649).
  - Added `set/getBlockingPaths()` methods (#2649).
  - Added `set/getSelectionMask()` methods (#2696).
- RenderController : Added new utility class for controlling interactive renders (#2649).
- AnimationGadget : Added new Gadget for editing animation curves (#2632).
- Animation (#2632) :
  - Keys are now reference counted, so ownership can be shared between CurvePlugs and the
    AnimationEditor.
  - Keys may be edited in place with `key->setTime()` etc, and the CurvePlug automatically updates.
  - `CurvePlug::keys()` has been replaced with `CurvePlug::begin()` and `CurvePlug::end()`.
    This hides the internal choice of container while still providing iteration.
  - Added optional `threshold` argument to `closestKey()`.
- IECoreScenePreview::Renderer (#2649) :
  - Added `command()` virtual method.
  - Added `name()` virtual method.
- IECoreGLPreview::OpenGLRenderer (#2649) :
  - Made it possible to call `render()` concurrently with edits.
  - Added support for highlighting selected objects.
  - Added "gl:queryBound" command.
  - Added "gl:querySelection" command.
  - Added support for custom object and attribute visualisers.
  - Added options for controlling base attributes.
- PresetsPlugValueWidget : Added support for an optional "Custom" menu item, which allows the
  user to enter an arbitary value. This is controlled by "presetsPlugValueWidget:allowCustom"
  plug metadata (#2660).
- BusyWidget : Added `busy` constructor argument (#2607).
- LightTweaks (#2660) :
  - Moved TweakPlug to the GafferScene namespace, so it can be reused by other
    nodes.
  - Added "Remove" mode.
- Layouts (#2698) :
  - Added `persistent` argument to `add()` method, mirroring the `Bookmarks.add()` API.
    This automatically takes care of saving persistent layouts into the startup location.
  - Added `setDefault()/getDefault()` and `createDefault()` methods to allow the management
    of a default layout.
- Handle (#2709) :
  - Added `set/getVisibleOnHover()` methods.
  - Added `PlanarDrag` axis accessors.
- TranslateHandle (#2709) :
  - Added `axisMask()` method.
- FilteredSceneProcessor : Added constructor to allow array `inPlug()`.
- Style :
  - Added methods for rendering animation curves (#2632).
  - Added `width` and `userColor` arguments to `renderLine()` (#2632).
  - Added `userColor` argument to `renderText()` (#2632).
  - Added XY/XZ/YZ Axes enum values (#2709).
- ViewportGadget : Added `set/getVariableAspectZoom()` method (#2632).

Build
-----

- ViewportGadget : Fixed compilation on Windows (#2705).
- OpenImageIOReader : Fixed compilation with XCode 9.4 (#2712).
- Updated Cortex to version 10.0.0-a28
- Updated FreeType version 2.9.1
- Updated Python to version 2.7.15
- Updated Alembic to version 1.7.8

Breaking Changes
----------------

- GafferSceneUI : Moved visualiser base classes to IECoreGLPreview (#2649).
- ArnoldAttributes : Changed volume step attributes (#2634).
- GafferImage : Removed FormatPlug compatibility for files saved in Gaffer 0.16 or older.
  To migrate, resave the file in Gaffer 0.47 (#2682).
- GafferOSL::ShadingEngine : Removed `scope` parameter from `needsAttribute()` (#2655).
- Layouts (#2698) :
  - Removed `save()` method. Use the `persistent` argument to `add()` and `setDefault()` instead.
  - Added `applicationRoot` argument to constructor. You should use `acquire()` instead anyway.
- LayoutMenu : Removed `delete()` method (#2698).
- GUI config : Renamed standard layout from "Default" to "Standard" (#2698).
- TranslateHandle : translation()` method now returns a V3f rather than a float (#2709).
- TransformTool : Made `orientedTransform()` method const (#2709).
- Style : Changed method signatures, enum values, and added virtual functions (#2632).
- Animation : Refactored API. See API section for more details (#2632).
- IECoreScenePreview::Renderer : Added virtual methods (#2649).
- InteractiveRender : Added and removed private member data (ABI break) (#2649).
- SceneGadget (#2649) :
  - Added/removed private members (ABI break).
  - Remove `baseState()`.
- SceneView : Reorganised/simplified drawingMode plugs (#2649).

0.47.0.0
========

Features
---------

- ImageView : Introduced asynchronous processing, so that the UI remains responsive while
  the viewer updates progressively (#2578).
- Apps : Added a new `dispatch` application. This dispatches task nodes such as ImageWriters,
  SystemCommands and Render nodes, either from within an existing .gfr file or by
  creating nodes on the fly. This differs from the execute app in that it performs a
  full dispatch via a dispatcher, rather than executing a single task node (#2588).
- Revamped OSL shaders (#2539).
  - Added MultiplyVector, DotProduct, CrossProduct, RemapFloat, RemapColor, RemapVector,
    FloatToColor, ColorToFloat, FloatToVector, VectorToFloat, ColorToVector,
    Luminance, MixColor, MixVector, MixFloat, AddColor, AddFloat, AddVector,
    DivideColor, DivideFloat, DivideVector, MultiplyColor, MultiplyFloat, MultiplyVector,
    SubtractColor, SubtractFloat, SubtractVector, InvertMatrix, Length, Normalize,
    PowFloat, RoundFloat, SinFloat, MatrixTransform, CompareColor, CompareFloat,
    CompareVector, SwitchColor, SwitchFloat, SwitchVector, CoordinateSystemTransform,
    CoordinateSystemMatrix.
  - Removed some old shaders, keeping compatibility by converting them to new shaders
    during loading.
- Appleseed : Updated to [version 1.9](https://github.com/appleseedhq/appleseed/releases/tag/1.9.0-beta)
  (#2570).

Improvements
------------

- Instancer : Replaced original proof-of-concept Instancer with a new version intended
  to be suitable for production use (#2642) :
  - Added support for orientation and scale primitive variables.
  - Added support for index and id primitive variables.
  - Added support for creating per-instance attributes.
  - Added support for sets.
  - Improved performance by removing `${instancer:id}` context variable.
- Documentation : Improved structure and presentation (#2612, #2613, #2616, #2619, #2625, #2628, #2631).
- Appleseed (#2570) :
  - Added support for pixel_time AOV.
  - Added denoiser options to AppleseedOptions node.
- OSLImage/OSLObject (#2586) :
  - Added support for `time` global variable.
  - Added support for reading context variables.
- OSLImage : Improved performance by only reading the upstream channels needed by the
  shader (#2586).
- Arnold renderer : Improved shader conversion performance (#2594).
- ArnoldOptions : Changed default value for `parallel_node_init` to on. This matches the default
  in Arnold 5.1 (#2594).
- OSLImage/OSLObject/RankFilter/Resample : Added cancellation support. This improves
  responsiveness in the new asynchronous ImageView (#2586, #2590).
- Isolate/Prune : Improved set processing performance (#2587).
- BranchCreator : Improved set processing performance (#2594).
- Application : Moved startup file execution before argument evaluation. This makes it
  possible for a startup file to manipulate application arguments if necessary (#2588).
- Stats app : Added `-canceller` argument (#2586).
- UI : Renamed Scene Hierarchy to Hierarchy View and Node Graph to Graph Editor.
- AttributeVisualiser : Added support for visualising Color3f attributes #2641).

Fixes
-----

- Viewer :
  - Fixed display of nested lights in look-through menu (#2615).
  - Fixed selection after expanding the selected locations (#2617).
- Metadata :
  - Fixed GIL management bug (#2582).
  - Fixed crash if `None` is passed to `registerValue()` (#2582).
  - Fixed bindings for change signals (#2610).
- UI : Fixed initial size and position of Preferences, Settings and Node Editor
  windows (#2643).
- ContextAlgo : Fixed GIL management (#2618).
- SubGraph : Fixed crash in `correspondingInput()`. This manifested itself as crashes in
  the NodeGraph when dragging a Box with an unconnected BoxOut node over a connection (#2583).
- TractorDispatcher : Fixed bug handling nodes like TaskList and FrameMask nodes, that don't
  have any work of their own to do (#2584).
- ImageAlgo : Fixed GIL management bug (#2585).
- Arnold/OSL : Fixed problems caused by Arnold trying to recompile Gaffer's OSL shaders
  unnecessarily. We no longer install the shader source files (#2539).
- ScriptNode : Fixed GIL management bug (#2578).
- BackgroundTask : Fixed interactions with ScriptNode lifetime (#2578).
- Threading : Fixed bugs caused by TBB cancellation propagation (#2589).
- LocalDispatcher : Fixed exception handling during foreground dispatch. Exceptions from
  Tasks are now propagated back to the caller instead of being suppressed (#2588).
- Appleseed : Disabled SPPM for interactive renders (#2570).
- Catalogue : Fixed bug where orphaned Catalogue tried to save an image (#2621).
- ViewportGadget : Fixed `setCameraTransform()` to trigger a rerender (#2639).
- Arnold : Worked around clashes between Mesa drivers and libai.so (#2638).

API
---

- DispatchUI : Added `DispatchDialogue` class (#2588).
- Dispatcher :
  - Added `dispatchSignal()` (#2574).
  - Improved signal exception handling (#2574).
  - Added `deregisterDispatcher()` static method (#2588).
  - Removed "frame" variable from TaskBatch contexts. This means it is no longer
    available to PythonCommand code in sequence mode (#2608).
- Outputs : Added `deregisterOutput()` method (#2581).
- GafferUI : Added new BackgroundMethod decorator to assist in performing processing in
  background threads (#2578).
- ShadingEngine : Added `hash()` method (#2586).
- PlugLayout :
  - Added `embedded` constructor argument (#2599).
  - Added "<layoutName>:width" metadata support (#2604).
- Editor : Added `instanceCreatedSignal()` method. This can be used to customise the
  standard editors immediately after they've been created (#2605).
- BusyWidget : Added `setBusy()` and `getBusy()` methods (#2604).
- ImageGadget : Added `setPaused()/getPaused()` and `state()` methods (#2604).
- ScriptEditor : Added `outputWidget()` accessor (#2622).

Build
-----

- Updated Appleseed version to 1.9.
- Updated OpenImageIO version to 1.8.12.
- Updated OpenShadingLanguage version to 1.9.9.
- Updated GLEW version to 2.1.0.
- Updated Cortex version to 10.0.0-a25.
- Improved documentation build process (#2622).

Breaking Changes
----------------

- Instancer : Added and removed plugs, changed behaviour and structure of output scene (#2642).
- Metadata : Changed function signatures for `GafferBindings::metadataModuleDependencies`
  and `GafferBindings::metadataModuleDependencies`. Source compatibility is retained (#2579).
- Action (#2578) :
  - Added new arguments to constructor and `enact()`.
  - Added new data member.
  - Source compatibility is retained.
- EditorWidget : Renamed to Editor (#2605).
- BackgroundTask : Replaced `done()` method with `status()`.
- SceneHierarchy : Renamed to HierarchyView (#2640).
- NodeGraph : Renamed to GraphEditor (#2640).

0.46.1.0
========

Features
--------

- ReverseWinding : Added new node that reverses the winding order of meshes (#2568).
- MeshDistortion : Added new node that calculates the distortion of a mesh from a
  reference shape (#2568).

Improvements
------------

- Stats app : Added `-sets` command line argument, to allow scene sets to be computed (#2572).
- OSLObject : Added support for reading and writing UVs via new InUV and OutUV shaders (#2569).
- SceneViewUI : Defer camera and light set computation until required (#2567).

Fixes
-----

- Arnold : Fixed NodeEditor layout of new standard_surface shader parameters (#2573).
- Catalogue : Fixed crash caused by non-writable directory (#2571).
- Stats app : Fixed bugs in `-preCache` argument. It was using the wrong context and
  not respecting the `-frames` flag (#2572).
- WidgetAlgo : Fixed bug when `grab()` with the event loop running (#2575).
- MapOffset : Fixed bug when offsetting an indexed uv set (#2576).

0.46.0.0
========

Features
--------

- FrameMask : Added new node to mask out upstream tasks on particular frames (#2558).

Improvements
------------

- Layouts (#2522) :
  - Simplified space-bar panel expansion, and removed the annoying auto-expand
    behaviour for collapsed panels.
  - Removed tabs from the Scene layout's Timeline panel.
- DeleteFaces/DeletePoints/DeleteCurves : Added invert plug (#2546).
- Spline widgets (#2551) :
  - Added axis lines at y=0 and y=1.
  - Improved framing behaviour.
  - Made float splines display as curves by default.
- Dispatcher : Reduced overhead of job directory creation (#2557).
- OSLObject : Added support for double primitive variables (#2547).

Fixes
-----

- Layouts : Fixed circular references created by layout menus. These could cause crashes
  during shutdown (#2522).
- BoolPlugValueWidget : Fixed displayMode metadata handling. This restores the little
  switches on the Attributes nodes (#2553).

API
---

- Metadata : Improved wildcard matching (#2536) :
  - Stopped '*' matching '.' in a plug path. This mimics how '*' doesn't match '/' in a
    glob match or in the PathMatcher.
  - Added '...' wildcard that matches any number of plug path elements, in the same way a
    PathMatcher does.
- ImageAlgo (#2561) :
  - Added support for lambdas in `parallelGatherTiles()`.
  - Added a `tileOrder` parameter to `parallelProcessTiles()`.
  - Added python bindings for `parallelGatherTiles()`.
- Context : Added optional `IECore::Canceller` that can be used to cancel long
  running background processes (#2559).
- BackgroundTask : Added new class to assist in the running of processes on background
  threads (#2559).
- ParallelAlgo (#2559) :
  - Added `callOnUIThread()` method.
  - Added `callOnBackgroundThread()` method.

Breaking Changes
----------------

- SplitContainer (#2522) :
  - Removed `animationDuration` argument from `setSizes()` method.
  - Removed `targetSizes()` method.
- Metadata : `*` no longer matches `.` in a plug path (#2536).
- PlugValueWidget : Removed `registerCreator()` method. Use metadata instead (#2536).
- ImageAlgo : Changed signatures for `parallelProcessTiles()` and `parallelGatherTiles()`
  (#2561).
- StringAlgo : Removed. Use `IECore::StringAlgo` instead (#2534).
- Display : Removed `executeOnUIThread()` method. Use ParallelAlgo instead (#2559).
- Gadget : Removed `executeOnUIThread()` method. Use ParallelAlgo instead (#2559).

Build
-----

- Requires Cortex 10.0.0-a20.
- Improved experimental CMake build setup (#2560).

0.45.3.0
========

Features
--------

- GafferSceneUI : Added CameraTool to the Viewer (#2531).
  - This enables the movement of the camera in the viewport to be pushed back upstream
    into the node for the camera or light that is currently being looked through. Note
    that once activated, the CameraTool will remain active even after another tool has
    been chosen.

Improvements
------------

- ShaderUI : Added support for userDefault metadata for shader parameters (#2544).

Fixes
-----

- SceneGadget : Fixed dirty propogation (#2541).
- Metadata (#2544) :
  - Added `deregisterValue()` overload for string targets.
  - Fixed overwriting of values for string targets.
- FormatPlug::acquireDefaultFormatPlug() : Fixed crashes if None is passed via
  python bindings (#2549).

Build
-----

- Added experimental CMake build in contrib (#2543).

API
---

- ViewportGadget (#2531) :
  - Added accessors for center of interest.
  - Added `orthographic3D` camera mode.
- BoolPlugValueWidget (#2531) :
  - Added support for `BoolWidget.DisplayMode.Tool`
  - Added `boolWidget()` accessor, matching `StringPlugValueWidget.textWidget()`.
- GafferUI : Add ToolUI (#2531) :
  - This sets up the "active" plug to use a BoolPlugValueWidget in tool mode,
    with an appropriate icon.
- Viewer : Added support for "tool:exclusive" metadata (#2531) :
  - This allows certain tools to be marked as non-exclusive, allowing them to
    remain active even when another tool has been chosen.
- TransformTool : Exposed constructor for Selection class (#2531).

0.45.2.0
========

Improvements
------------

- ArnoldAttributes : Added support for "subdiv_uv_smoothing" Arnold parameter (#2538).
- OSLObject : Improved performance by removing unnecessary primitive variable resampling (#2523).
- BoxUI : Removed "Promote as Box.enabled" menu item. The regular "Promote to Box" menu
  item should be used instead (#2528).

Fixes
-----

- SceneHierarchy : Fixed bug which caused the scene selection to be cleared
  unnecessarily (#2525).
- SceneInspector (#2532) :
  - Fixed selection bug in Globals->Sets section.
  - Fixed graphical glitch in Globals->Sets section.
- Transform Tools : Fixed context management bug (#2524).
- FileMenu : Fixed premature exit when opening backup containing error (#2526, #2527).
- OpenGLShader : Fixed serialisation (#2529).
- Box : Fixed creation of Boxes around existing SceneNode graphs (#2530).
- SceneGadget : Fixed Python binding for `getScene()` (#2532).

API
---

- ShaderUI : Added `hideShaders()` function (#2533).

0.45.1.0
========

Improvements
------------

- NodeGraph (#2495) :
  - Added automatic layout for auxiliary nodes.
  - Improved aesthetics of auxiliary nodes and connections.
- Viewer :
  - PointsPrimitives now default to drawing as GL points. The Drawing dropdown menu can
    be used to display them as disks instead (#2512).
  - Enabled anti-aliasing in the 3d view (#2521).
- Application : Gaffer processes are now named `gaffer ...` rather than
  `python gaffer.py ...` (#2511).
- Expression : Added support for `"x" in context` Python syntax (#2513).
- NodeEditor : Added Lock/Unlock menu items to the tool menu (#2517).
- Shader : Added support for showing/hiding output parameters in the NodeGraph (#2515).
- Arnold : Enabled procedural instancing during interactive renders. This requires a
  minimum Arnold version of 5.0.1.4 (#2519).

Fixes
-----

- Viewer : Fixed inaccurate picking of points and curves (#2512).
- Transform tools (#2137, #2516) :
  - Fixed bug where pivot was ignored.
  - Fixed bug affecting Transform node when space was set to World.
  - Fixed drawing order so handles are always on top.
- NodeGraph :
  - Fixed kink in connection drawing (#2500).
  - Fixed inaccurate picking in the corners of rounded nodes (#2500).
- NodeEditor (#2517) :
  - Fixed update bug which allowed plugs to be edited after an
    ancestor node was made read only.
  - Fixed bugs which allowed plugs to be added to read only nodes.
- Encapsulate : Fixed double transformation bug (#2518).

API
---

- Set : Added iterators (#2495).
- MetadataAlgo (#2517) :
  - Added `ancestorAffectedByChange()` function.
  - Added `readOnlyAffectedByChange()` functions.

0.45.0.0
========

Features
--------

- Added Ramp image node (#2470).
- Added SplinefColor4fPlug type (#2470).
- Added system to backup all open scripts at frequent intervals.
  This is controlled via the Preferences dialogue (#2469, #2499, #2503).

Improvements
------------

- Viewer :
  - Improved performance significantly when selecting large numbers of
    objects (#2450, #2486).
  - Improved reporting of errors involving look-through cameras (#2490).
  - Improved camera selection UI (#2490).
  - Added default camera settings dialogue (#2490).
  - Added Ctrl+K shortcut to fit clipping planes to selection (#2490).
  - Added Ctrl+F shortcut to frame selection and fit clipping planes to
    match (#2490).
  - Added context menu (#2490).
- SceneHierarchy (#2450, #2486) :
  - Improved performance significantly when selecting or expanding large numbers
    of objects.
  - Multiple selections made in the Viewer are now highlighted properly in the
    SceneHierarchy (#76).
- Significantly reduced file sizes and load times for scripts
  containing many shader and/or light nodes (#2455).
- NodeGraph
  - Added ability to Shift+Drag a connection to duplicate it (#2480).
  - Improved representation of Expression, Animation and Random nodes (#2458, #2497).
  - Improved highlighting behaviour for connections to selected nodes (#2473).
- ScriptNode :
  - The current frame is now saved with the script and restored on
    loading (#2468).
  - Read-only files are now read-only in the UI (#2503).
- ArnoldAttributes : Added attributes to control volume motion blur (#2433).
- Arnold : Added support for OSL shaders with multiple outputs (#2494).
- Stats/Execute apps : By default the current frame stored in the script is
  executed, rather than frame 1 as before. Use the `-frames` commandline argument
  to specify a specific range of frames to execute (#2468).
- CompoundDataPlugValueWidget : Added array types to plug creation menu (#2433).
- Startup : Startup files are now executed in isolated scopes, so they cannot
  accidentally rely on other startup files (#2462).
- Expression : Python expressions can now read from CompoundDataPlugs (#2484).

Fixes
-----

- Appleseed : Fixed crashes when editing cameras during interactive renders (#2489).
- Browser : Fixed bug caused by missing import (#2449).
- OpenColorIO : Added workaround for OpenColorIO bug whereby config parsing would
  fail for non-English locales (#1654, #2460).
- Python wrappers : Fixed exception translation (#2459).
- BoxIn : Plug values are now preserved when promoting an input plug (#2461).
- Tractor Dispatcher : Fixed accumulation of tractor plugs on TaskNodes (#2463).
- GraphComponent : Fixed bug which could prevent multiple scripts from being
  loaded in parallel (#2464).
- GraphComponentPath : Fixed bug whereby children did not inherit the filter
  from their parent (#2465).
- OSLLight : Fixed metadata for child plugs of parameters (#2474).
- Shader : Fixed serialisation bugs introduced in version 0.43 (#2454, #2455).
- Spline UI : Prevented creation of multiple editing dialogues for the same
  plug (#2472).
- Added backwards compatibility for scripts referencing the old
  `GafferScene.PathMatcher`, `GafferScene.PathMatcherData` and
  `GafferScene.PathMatcherDataPlug` types (#2457).
- Layouts :
  - Fixed incorrect vertical sizing of Timelines in custom
    layouts (#2502).
  - Fixed bug serialising custom layouts containing special characters (#2492).
- ScriptNode :
  - Hid "frame" plug from the UI, and clarified in the documentation
    that is not intended for widespread use (#2504).
  - Fixed a bug loading old scripts which referenced `IECore::Data` types
    wrapping `imath` types (#2487).
- Viewer (#2490) : Fixed bug where centre of interest was lost when switching between
  the default and look-through cameras.
- PlugValueWidget : Fixed bug that allowed drags to be received for read-only
  plugs (#2503).
- GUI App : Errors are now reported correctly when loading files from the command
  line (#2499).
- Serialiser : Fixed handling of exceptions in Python serialisers (#2475).
- Expression : Fixed initial UI state so that the expression is not editable until
  a language has been chosen. This avoids problems where an expression was entered
  and then lost when the language was set (#2482).
- PlugAlgo : Fixed problems with metadata promotion when using non-Box parents (#2488).
- NodeAlgo : Fixed attempts to apply user defaults to plugs that are not settable (#2507).

API
---

- PathListingWidget : Added faster expansion and selection methods using
  `IECore.PathMatcher()` to store sets of paths (#2450).
- AuxiliaryNodeGadget : Added new class to represent nodes like Expression and
  Animation in the NodeGraph (#2458).
- Style : Added `state` argument to `renderAuxiliaryConnection()` (#2473).
- Added GafferUI.Backups class (#2469).
- ImageGadget : Added `loadTexture()` method (#2490).
- ViewportGadget : Added `fitClippingPlanes()` method (#2490).
- Viewer : Added `viewContextMenuSignal()`. This allows context menus for views to be
  customised using the same basic mechanism we use in the NodeGraph and elsewhere.
  (#2490).
- FileMenu : Added `addScript()` function (#2499).
- Serialisation : Improved support for Python serialisers (#2475).
- ConnectionCreator : Added new class to improve drag & drop functionality in
  the NodeGraph (#2480).
- ContextAlgo : Added `affects*Paths()` methods (#2486).

Breaking Changes
----------------

- Stats app : Replaced `-frame` parameter with `-frames` (#2468).
- Style : Changed signature for `renderAuxiliaryConnection()` method (#2473).
- View : Removed `framingBound()` method (#2490).
- RendererAlgo : Renamed `createDisplayDirectories()` to `createOutputDirectories()`
  (#2452).
- PlugAdder (#2480) :
  - Removed `edge` constructor argument.
  - Changed base class.
- Nodule : Changed base class (#2480).
- ConnectionGadget : Changed base class (#2480).
- NodeGadget : Renamed `noduleTangent()` to `connectionTangent()` (#2480).
- ContextAlgo : The scene selection is now stored as a PathMatcher and not
  StringVectorData (#2486).
- SceneGadget : Changed signatures for methods for accessing selection and
  expansion (#2486).
- Style : Added new `renderAuxiliaryConnection()` virtual method (#2497).

0.44.0.0
========

Features
--------

- Added Checkerboard image node (#2403).
- Added ArnoldAtmosphere and ArnoldBackground nodes (#2444).

Improvements
------------

- NodeGraph : Added rendering of auxiliary connections, for instance between Expressions
  and the nodes they are connected to (#2436).
- Build : Hid symbols that do not need to be exported (#2431).
- OSLObject : Added support for creating string primitive variables (#2425).
- ArnoldShader : Added support for shader outputs of type string and boolean (#2439).

Fixes
-----

- MessageWidget : Fixed crash when clicking on message buttons (#2438).
- BoxIO : Fix promotion of ArrayPlugs (#2446).

API
---

- Style : Added `renderAuxiliaryConnection()` method (#2436).
- Scene : Added GlobalShader base class (#2444).
- GafferVDB : Using IECoreVDB (#2440).

Breaking Changes
----------------

- Plug : Removed deprecated PerformsSubstitutions flag. Use the `substitutions`
  argument to the StringPlug constructor instead (#2432).
- Style : Added a virtual method (#2436).
- ArnoldAOVShader : Changed base class (#2444).

Build
-----

- Added WARNINGS_AS_ERRORS build argument. This defaults to being on,
  which is the same behaviour as before (#2431).
- Added ASAN build argument for use with Clang (#2434).

0.43.0.0
========

Features
--------

- GafferVDB : Added PointsGridToPoints node and visualisation
  of VDB point grids (#2386).

Improvements
------------

- Appleseed : Added support for Capsules generated by the Encapsulate
  node (#2402).
- ImageReader (#2380) :
  - Reimplemented to use Gaffer's native cache instead of
    OpenImageIO's cache, giving speedups of 20-30% in some cases. This
    also paves the way for introducing deep images to Gaffer.
  - Added initial support for multi-part OpenEXR files.

Fixes
-----

- ValuePlug : Fixed problems when serialising compound plugs (#1500, #2395).
  - BoxPlugs were being serialised with `setValue()` calls for the leaf plugs
    _and_ the top level plug itself.
  - FormatPlugs were incorrectly attempting to serialise a `getValue()` call
    at the top level even when input connections existed at the leaf level.
    This prevented a common pattern for the dispatch of image networks from
    working.
- Camera node : Fixed "Copy From Viewer" tool menu item (#2396).
- SceneInspector : Fixed transform component display (#2396).
- Expression : Fixed bug caused by non-serialisable input plugs (#2395).
- CollectImages/Merge/Offset : Fix out of bounds input tile accesses
  (#2380).
- TabbedContainer : Fixed an incompatibility with Qt5 (#2426).
- PythonCommand : Exposed imath module to the execution command (#2428).
- CompoundPlug : Added compatibility config for legacy gfr files (#2429).

API
---

- Serialisation : Added support for nested classes in `classPath()` method (#2400).
- Plug : Remove deprecated ReadOnly flag (#2401).
- Moved PathMatcher/PathMatcherData/PathMatcherDataPlug from GafferScene to Gaffer (#2404).
- Filter : Removed Result enum. Use IECore::PathMatcher::Result instead (#2404).

Breaking Changes
----------------

- GafferScene :
  - Removed AlembicSource node. Use a SceneReader instead (#2397).
  - Removed AlembicPath and AlembicPathPreview.
- GafferCortex : Removed TimeCodeParameter support. This parameter type
  has been removed from Cortex (#2427).
- GafferTest : Removed SphereNode (#2399).
- ValuePlugSerialiser : Removed `valueNeedsSerialisation()` virtual
  method (#2395).
- OpenImageIOReader : Removed cache related methods (#2380).
- Removed Plug::ReadOnly flag. Use MetadataAlgo instead (#2401).
- ValuePlugSerialiser : Removed flagsMask argument from `repr()` method (#2401).
- Filter : Removed Result enum. Use IECore::PathMatcher::Result instead (#2404).

0.42.0.0
========

This major release brings significant version upgrades to all supported
renderers : Arnold 5, 3Delight 13 (NSI), and Appleseed 1.8. It also
introduces native support for OpenVDB, and initial support for reading
and writing USD files. This is of course in addition to the usual
assortment of improvements and bug fixes.

> Note :
>
> As of this release we no longer support Arnold 4 or 3Delight 12.
> Additionally, some Cortex functionality has been moved to the
> IECoreScene python module, and we now use the imath python module
> to access types like V3f, Color3f etc. Custom scripts and/or
> expressions may need to be updated accordingly. See the Breaking
> Changes section for more details.

Features
--------

- Arnold 5 support (#2308) :
  - Added support for rendering arbitrary meshes as volumes. Previously
    they were converted to box volumes.
  - Added support for light path expressions.
  - Added support for transform_type.
  - Added ArnoldAOVShader node to support AOV shaders.
  - Added support for volume_padding (#2356).
- 3Delight 13 support via the NSI API (#2311).
  - All shading/lighting is now performed via OSL shaders.
  - Includes full support for adding/removing/moving objects during
    interactive rendering.
- Appleseed 1.8 support (#2371) :
  - Updated version to 1.8.1.
  - Added AOV presets to the Outputs node.
- USD (#2393)
  - The SceneReader node can now read USD files.
  - The SceneWriter node can now write USD files.
- VDB (#2373) :
  - Added native support for representing VDB volume data in Gaffer
    scenes.
  - The standard SceneReader node can now load .vdb files.
  - VDB objects can be rendered directly to Arnold.
  - The Viewer now provides basic visualisation of VDB grids.
  - The SceneInspector provides inspection of grid metadata etc
    in the Object section.
  - Several new nodes demonstrate the feasibility of manipulating
    VDB grids directly in Gaffer's node graph :
      - LevelSetToMesh
      - MeshToLevelSet
      - LevelSetOffset
- Catalogue : Added a new CatalogueSelect node. This can be placed
  downstream of a Catalogue to override the image to view (#2370).
- UI Editor : Added the ability to add custom buttons to a plug (#2348).
- Gadget : Introduced layer-based rendering for Gadget-based UI
  elements (#2304).

Improvements
------------

- OpenColorIO nodes : Added role presets to all colorspace plugs (#2379)
- NodeGraph : Added icons to signify that a node has been bookmarked (#2369)
- PlugLayout : Improved layout of successive accessory widgets. They
  are now all placed in the same row (#2348).
- Simplified 3delight configuration based on $DELIGHT environment
  variable (#2311).
- TaskPlug/FilterPlug/ShaderPlug : Tightened `acceptsInput()` constraints (#2321).
- OSLObject : Added support for reading and writing matrix primitive variables (#2327).
- GafferImage : Moved default format plug creation to gui config (#2333).

Fixes
-----

- Catalogue :
  - Fixed bug that prevented images with a '.' in the filename from
    being loaded (#2370).
  - Fixed crashes caused by removing several images in quick
    succession (#2337).
- File Menu : Fixed "Import..." bugs (#1077, #2339).
- Edit Menu : Fixed automatic layout of pasted nodes (#2383)
- ShaderPlug : Fixed bug when deserialising inputs from BoxIO nodes (#2374)
- Crop : Fixed bug whereby changing the format plug value did not trigger
  recomputation (#2368).
- ImageWriter (#2364) :
  - Fixed a crash when writing a data window with a single pixel .
  - Fixed writing of empty data windows to write a single pixel data
    window instead of a full image. OpenEXR does not support empty data
    windows, so we must write at least one pixel.
- NodeGraph :
  - Fixed confusing Box navigation behaviour (#2343, #2347).
  - Fixed overlay text to always be on top (#674, #2304).
  - Fixed layering so dragged connections are always drawn behind
    nodes, and highlighted plugs are drawn above all others (#2304).
- SubGraph : Accounted for BoxIO nodes in `correspondingInput() (#2360).
  This fixed a node reconnection bug when deleting a Box or Reference, and
  allows Box and Reference nodes to be drag-inserted onto existing connections.
- ScriptNode :
  - Fixed node deletion problems caused by errors in `correspondingInput()`
    implementations. This was preventing nodes representing missing Arnold
    shaders from being deleted (#2355).
  - Fixed crashes caused by syntax errors in code passed to `execute()` method.
    This could cause a crash when pasting invalid text into the NodeGraph.
    (#2319, #2320)
- Shader/ShaderPlug : Fixed GIL management bug which could cause a deadlock
  in the `attributes()` and `attributesHash()` methods (#2354).
- GraphComponent : Fixed crashes caused by passing `None` to the Python
  bindings (#2338).
- VectorWarp : Fixed handling of nan/inf (#2341).
- Expression : Fixed copy/paste bug (#2336).
- BoxIO : Fixed undo/redo of `insert()` method (#2314).
- RendererAlgo : Fixed crash when renderer returns a null ObjectInterface (#2302).
- SetUI : Fixed set name context menus to account for intermediate nodes between
  destination and filter (#2312).
- StandardLightVisualiser : Fixed for Cortex 10 UV conventions (#2311).
- PlugAlgo : Fixed promotion of non-serialisable output plugs (#2314).
- Serialiser : Fixed syntax error created by `moduleDependencies()` (#2320).
- Plug : Fixed `setInput( nullptr )` so it removes inputs from all descendant
  plugs (#2323).

API
---

- OpenColorIOTransform : Added method to query available role names (#2379)
- Added default template arguments to simplify usage of several methods (#2361)
  - `PlugGadget::getPlug()`
  - `IndividualContainer::getChild()`
  - `Dot::inPlug()` and `Dot::outPlug()`
  - `View::inPlug()`, `View::getPreprocessor()` and `View::preprocessedInPlug()`
  - `Metadata::value()`
  - `BoxIO::plug()` and `BoxIO::promotedPlug()`
- Added GafferUI.ButtonPlugValueWidget (#2348).
- ScriptNode : Added `importFile()` method (#2339).
- Added new OpenGL renderer backend (#2302).
- Gadget : Introduced layer-based rendering (#2304).
- GafferOSL :
  - Added ClosurePlug type (#2308).
  - Added OSLLight node (#2311).

Breaking Changes
----------------

- Removed GafferRenderMan, and with it support for 3Delight versions
  prior to 13 (#2311).
- Removed support for Arnold 4 (#2308).
- Gaffer and Cortex now use the official `imath` python module rather
  than custom bindings in IECore (#2378).
- Cortex scene classes have moved to a new IECoreScene module, as we
  continue to simplify and modularize Cortex (#2362).
- Removed SplineEditor/SplinePlugGadget since they have never been
  used (#2375).
- Removed ProceduralHolder node. This was not exposed via the UI,
  had never been used, and is no longer supported by any of the
  renderer backends (#2366).
- Shader : Removed deprecated state methods (#2354).
- Removed RenderableGadget. If similar functionality is required,
  use an ObjectToSceneNode and a SceneGadget (#2334).
- SceneAlgo : Removed camera/transform utilities. These relied on conventions
  and functionality that will be removed in Cortex 10 (#2332).
- RendererAlgo : Removed obsolete functions used only with the legacy
  renderer backends (#2318).
- Removed code for handling `IECore::Light`. Lights are now
  always represented as shaders assigned to a location (#2331).
- Removed SceneProcedural and ScriptProcedural. These were only useful
  in legacy renderer backends, which have now all been removed (#2318).
- Removed ExecutableRender node. This used the legacy renderer backends
  which have all been removed (#2318).
- Gadget : Modified rendering API (#2304).
- Removed IncrementingPlugValueWidget. Use RefreshPlugValueWidget
  instead (#2322).
- Removed EnumPlugValueWidget. Use PresetsPlugValueWidget and
  metadata presets instead (#2322).
- ViewportGadget : Refactored camera transform handling. The camera
  transform is now accessed via new `setCameraTransform()`/`getCameraTransform()`
  methods, rather than via the camera itself (#2351).
- ScriptNode : Modified signature of `ScriptExecutedSignal` to use raw pointers
  (#2336).

0.41.0.0
========

Breaking Changes
----------------

- Adopted Cortex 10 UV representation (#2281) :
  - UVs are now represented as V2f primitive variables,
    not separate s/t float primitive variables.
  - Primary UV set is called "uv".
  - UV origin is in the bottom left, with increasing values of
    V going _up_ (flipped vertically compared to previous orientation).
  - Indices are now stored on the same primitive variable as the
    UVs themselves.
  - This has affected the plugs and default values for a number of
    nodes.
- SplinePlug : Changed value representation from IECore::Spline to new
  SplineDefinition class (#2148).
- Algo headers : Removed compatibility namespacing (#2299).
- Removed CompoundPlug. Use Plug or ValuePlug instead (#2298, #1323).
- Removed CompoundPlugValueWidget. Use PlugLayout instead (#2298).
- FilteredSceneProcessor : Removed deprecated `filterContext` method.
  Use FilterPlug::FilterScope instead (#2260).
- Stopped installing Cortex image ops. Use GafferImage nodes instead (#2258).
- Removed OpenImageIOAlgo. Use IECoreImage::OpenImageIOAlgo instead (#2258).
- Removed GafferCortexUI::ImageReaderPathPreview. Use
  GafferImageUI::ImageReaderPathPreview instead (#2258).
- GafferBindings : Hid internal details in GafferModule (#2289).
- GafferUIBindings : Hid internal details in GafferUIModule (#2256).
- GafferCortexBindings : Hid internal details in GafferCortexModule (#2248).

Features
--------

- Added Viewer visualisation of Arnold light filters (#2275).
- Added Encapsulate node. This encapsulates portions of a scene by
  collapsing the hierarchy and replacing it with a procedural which
  will be evaluated at render time (#2283).
- Added FloatSpline OSL shader ((#2292).
- Added VTuneMonitor to annotate VTune profiles with node processes (#2247).

Improvements
------------

- LightTweaks : Added "Delete" menu item to context menu (#2285).
- OSLShader : Improved node graph labels (#2296).
- Parent : Defaulted "root" plug to value of "/" (#2242).
- ArnoldOptions : Added abortOnError and maxSubdivison settings (#2290).
- SplinePlug :
  - Added MonotoneCubic interpolation option (#2148).
  - Added option to preview splines as curves rather than a colour ramp (#2292).
- CollectScenes : Added "root" plug, to allow subtrees to be collected
  from the input scene (#2238).
- OSLObject/ShadingEngine : Added multithreaded evaluation for improved
  performance (#2251).
- CompoundDataPlug : Added menu items for adding box plugs (#2263).
- Browser/View apps : Improved image preview (#2258).
- Filter plug UI : Decluttered embedded filter UIs (#2276).
- Group/BranchCreator : Optimised context management (#2270).

Fixes
-----

- ArnoldRender : Fixed error handling for aborted renders (#2279).
- SplineWidget :
  - Fixed incorrect colours in rightmost column (#2295).
  - Fixed editing of float splines (#2292).
  - Fixed curve width (#2293).
  - Fixed drawing of curves with minimum Y values other than 0 (#2292).
- ImageWriter : Fixed bug when writing JPEG with blank scanlines (#2268).
- ImageReader : Fixed "enabled" plug, so that turning it off outputs a default
  blank image (#2254).
- Documentation :
  - Fixed formatting of supported file extensions (#2244).
  - Clarified that the SceneReader node does support Alembic (#2244).
  - Fixed URL (#2273).
- BoxIO : Fixed bug that could cause promoted plugs to initially be
  invisible in the NodeGraph (#2284).
- GraphGadget : Fixed GIL handling in `setRoot()` and `setFilter()`
  methods (#2287).
- PlugLayout : Collapsible layouts are now used if a `rootSection`
  is specified (#2276).
- PlugAlgo : Fixed bug where promoted plugs had the wrong value (#2298).
- Prune : Fixed hashing of sets (#2243).
- Text : Fixed problems with vertical alignment when there was too much
  text to fit in the text area (#2291).

API
---

- ValuePlug : The `Node::plugSetSignal()` is now emitted for all ancestors, not
  just for ValuePlugs (#2298).
- GafferCortex::ParameterHandler : Added `hash()` method (#2298).
- RendererAlgo : Added optional `root` argument to `outputObjects()` (#2283).
- SceneAlgo : Added `parallelProcessLocations()` overload taking `root` (#2283).
- Wrapper classes : Added templated variadic constructors (#2250).
- PlugAlgo : Added `promoteWithName()` function (#2284).
- Added Capsule class to represent encapsulated scene hierarchy (#2283).
- StandardLightVisualiser : Added method for querying spotlight parameters (#2275).
- WidgetAlgo : Fixed `grab()` to work around Qt bugs on OSX (#2307).

Build
-----

- Added compatibility with OIIO 1.8 (#2261).
- Requires Cortex 10.0.0-a4.
- Made SConstruct compatible with Python 3 (#2280).
- Fixed problems building the documentation (#2307).

0.40.0.0
========

This release brings improved Alembic support, support for Arnold light filters and Appleseed area lights,
and the usual medley of miscellaneous improvements and bug fixes.

The astute observer may note that the version number leaves a gap from the previous major version
of 0.34. This is because 0.40 is the first version to require the use of a C++11 compiler,
but some current users are stuck on older toolchains for a little while longer. We intend to use the
intervening versions to provide backported feature releases for the older toolchains where needed.

Breaking Changes
----------------

- Simplified GafferScene/GafferSceneUI/GafferImage/GafferImageUI bindings by hiding code which
  is only used internally (#2142, #2152).
- TaskNode : Rederived from DependencyNode (#2163)
- Removed OrphanRemover/Behaviour classes. Use StandardSet's built-in orphan removal instead (#2212).
- CompoundNodule : Removed deprecated constructor arguments. Use metadata instead (#2216).
- ContextProcessor : Changed signature of `processContext()` and added `affectsContext()` pure
  virtual method (#2220).
- SceneInspector (#2222) :
  - Renamed `SceneInspector.inspectsAttributes()` to SceneInspector.supportsInheritance()`.
  - Removed `SceneInspector.SideBySideDiff.frame()` method. Client code should use the new
    setValueWidget/getValueWidget accessors to get access to the frame contents instead.
- Replaced use of boost::function with std::function (#2224)
- Display :
  - Removed server management. Use the Catalogue or manage a display server directly instead (#2228).
  - Display : Removed `dataReceivedSignal()`
- Removed GafferBindings::ExceptionAlgo. Use IECorePython::ExceptionAlgo instead (#2241).

Features
--------

- Alembic (#2234) :
  - SceneReader and SceneWriter nodes can now read and write Alembic files directly.
    The old AlembicSource node is now deprecated.
  - Improved performance.
  - Added support for points and curves geometry.
  - Fixed mesh winding order.
- Light Filters. Added initial support for Arnold light filters. These can be loaded using the
  regular ArnoldShader node and assigned to lights using the ShaderAssignment node (#2135).
- Appleseed : Added rectangular area lights (#2237).

Improvements
------------

- SceneWriter (#2161) :
  - Added support for serialising sets to .scc files.
  - Improved performance by multithreading scene generation.
- TaskNode : Errors are now reported in the NodeGraph (#2163)
- Execute app : Improved error reporting (#2163)
- OSL expressions : Added support for M44f plugs (#2187)
- Shader node : Added attributeSuffix plug. This is primarily of
  use with light filters (#2135).
- StandardNodeGadget : Added support for "iconScale" metadata (#2211)
- OSLShader : Added support for "icon" and "iconScale" shader metadata (#2211)
- ArnoldRender : Improved render shutdown performance (#2203)
- OSL ShadingEngine : Added support for converting aggregate data to arrays in `getattribute()` (#2219).
- SceneInspector (#2222) :
  - Improved discoverability of diff, inheritance and history views
  - Removed history traceback from fields where it was irrelevant
  - Fixed click-to-select in Set history tracebacks
- NodeGraph : Node double click and Edit.. menu items now always open a floating
  NodeEditor (#2222)
- Merge (#2223) :
  - Improved labelling of node inputs (#260)
  - Changed default operation to "Over"
- Stats app : Added -preCache argument (#2236)
- Appleseed (#2237) :
  - Updated to version 1.7.1-beta
  - Added double sided material assignment attribute
  - Added per ray type bounce limits
  - Improved default texture cache size

Fixes
-----

- NodeGraph : Fixed graphical glitches when drawing connections (#2156, #2170, #2230)
- Dot :
  - Fixed bug where Dots created with Control+Click were not always immediately draggable (#2139)
  - Fixed bug where any click (not just left click) would create a Dot (#2147)
  - Fixed bug with Control+Click creation of Dots in Boxes (#2197)
- Qt :
  - Fixed crashes when reparenting child windows (#2168)
  - Fixed bug with VectorDataWidget and Qt4 (#2162)
  - Fixed bug with GLWidget host resource sharing for Qt4 hosts (#2173)
  - Suppressed GLWidget warning messages on OSX (#2195)
- Catalogue :
  - Fixed crashes when saving renders to disk (#2174)
  - Fixed shuffling of switch plugs during image delete (#2193)
- Fixed loading of old files which referred to OIIO's "catrom" filter, which is now
  named "catmull-rom" (#2177).
- OpenGLShader : Fixed problems caused by attempting to reload shaders when no GL
  implementation is available (#2176)
- OSLImage (#2198) :
  - Fixed bug which meant that tiles with origin -64 were passed through unchanged
  - Fixed UVs for images with negative display window origins
  - Fixed global `P` values to reflect pixel centres, not corners
- Menu : Fixed handling of special regex characters in search field (#2221)
- Color editors : Fixed bug that allowed the creation of multiple editors for the
  same plug (#2209, #2222)
- ScriptNode : Fixed bug where `isExecuting()` returned the wrong result when
  loading a script containing references (#2227).
- Reference : Fixed "Duplicate as Box" menu item to create the Box with the
  right parent when the Reference node is not at the root of the script (#2229).
- MonitorAlgo : Fixed use of unitialised value (#2233)
- CompoundDataPlug : Fixed bug which prevented non-alphanumeric names being used
  in `addMembers()` (#2228)

API
---

- Added default template arguments for Plug and GraphComponent methods. This simplifies
  the use of methods like `GraphComponent::getChild()` and `Plug::getInput()` (#2167).
- Added `SceneAlgo::parallelProcessLocations`. Over time this will replace `parallelTraverse()` (#2161).
- ImageAlgo : Fixed tile range for `parallelProcessTiles` (#2164)
- TaskNode : Rederived from DependencyNode (#2163)
- Arnold ParameterHandler : Allowed plug type to be overriden using a `gaffer.plugType` metadata
  entry (#2135).
- StandardSet : Added automatic orphan removal feature (#2212)
- Context : Added `EditableScope::removeMatching()` method (#2220)
- Menu : Added support for `partial( WeakMethod( ... ) )` in commands (#2222)
- NodeSetEditor : Added `floating` argument to `acquire()` method (#2222)

Build
-----

- Fixed invalid debug assertions in Shape node (#2186)
- C++11 is now required as a minimum (#2167)
- Improved speed of Travis tests (#2145)
- Requires Cortex 10.0.0-a1

0.34.0.0
========

Breaking Changes
----------------

- ImageReader/ImageWriter : Replaced hardcoded colourspace management with configurable
  system. The default colourspace for several file formats has changed. (#2121)
- ImagePlug : Changed type of `metadataPlug()` (#2087)
- ImageWriter : Changed default exr compression to "zips" (#2092)
- Shader : Added `loadShader()` and `reloadShader()` virtual methods (#2098, #2088)
- ScriptNode : Added argument to `ScriptNode::paste()`. Default behaviour is unchanged. (#2117)
- ConnectionGadget : Added virtual method (#2102)

Features
--------

- Added configurable colourspace management to ImageReader and ImageWriter nodes (#2121)
- Added ResamplePrimitiveVariables node (#2105)
- Added DeleteFaces node (#2118)
- Added DeletePoints node (#2120
- Added DeleteCurves node (#2120)
- Added CollectImages node (#2116)
- Added CollectScenes node (#2127)
- Added DeleteSceneContextVariables node (#2111)
- Added DeleteImageContextVariables node (#2111)
- Added Erode and Dilate filters (#2134)
- Added support for Qt5 (#2132)

Improvements
------------

- Image : Improved performance for complex graphs (#2111)
- OSLShader : Improved shader reloading (#2088)
- OSLObject : Added interpolation plug. This allows shading to be
  performed per-face or per-face-vertex in addition to the previous
  vertex shading. (#2113)
- DirtyPropagationScope : Added python bindings (#2104)
- NodeGraph :
  - Improved drawing of connections (#2102)
  - Added Control+Click to insert Dots into connections (#2072)
- ImageReader : Added fileFormat and dataType items to metadata (#2121)
- Catalogue : (#2106)
  - Improved performance
  - Moved saving/snapshotting to the background, so the UI remains responsive while
    they occur
- ContextVariables : Added extraVariables plug to facilitate use
  with expressions (#2131).

Fixes
-----

- Catalogue : Fixed bug where shader view images leaked into the catalogue (#2106)
- EditMenu : Fixed error handling for paste action (#2117)
- Wrapper :
  - Fixed SIP-related problems with Arnold setup on OSX (#2107)
  - Defaulted to using lldb for debugging on OSX (#2110)
- MessageWidget : Fixed widget parenting bug (#2117)
- BoxIO : Disabled removal of promoted plugs when a BoxIO is deleted from a parent
 with childNodesAreReadOnly metadata (#2122)
- ImagePlug : Fixed GIL management bugs in `imageHash()` and `channelDataHash()` bindings (#2106)
- Shape/Text : Fixed bug where disabling the node still modified the image (#2106)
- ImageProcessor : Fixed bug which prevented some nodes from using expressions based on
  channel name. The bug was introduced in version 0.30.0.0 (#2124).
- Box : Fixed bug which could prevent the boxing of nodes containing internal
  connections (#2126).
- TransformTool : Fixed interaction with Transform node (#2136).

API
---

- Added AtomicCompoundDataPlug (#2087)
- ImagePlug/ImageNode : Changed metadataPlug() to AtomicCompoundDataPlug (#2087)
- ScriptNode : Added `continueOnError` argument to `paste()` method. (#2117)
- ShadingEngine : Added `needsAttribute()` method (#2114)
- Shader : Added `reloadShader()` method (#2088)
- ConnectionGadget : Added `closestPoint() method (#2102)
- Display : Added `copy` argument to `setDriver()` method (#2106)
- Catalogue : Added `Image::copyFrom()` method (#2106)
- Context : Added `removeMatching()` method (#2111)
- DependencyNodeClass : Added constructor taking no_init, for when a
  DependencyNode has no public constructor (#2134)

Build
-----

- Fixed compilation with GCC 4.1.2 (#2103)
- Updated dependencies : (#2109)
  - OIIO 1.7.15
  - OSL 1.8.9
  - Cortex 9.21.1
  - Qt 5

0.33.3.0
========

Improvements
------------

- ImageWriter : Added plug for jpeg chroma subsampling (#2101)
- Layer selector :
  - Sorted layer names (#2089)
  - Simplified menu for standard *.RGBA layers (#2100)
- Seeds : Added densityPrimitiveVariable plug to allow point density to be varied
  across the surface of a mesh (#2095)
- Added InInt and OutInt OSL shaders, to support integer primitive variables in
  the OSLObject node (#2093)
- Stats app : Added -task argument to allow collection of stats from TaskNodes (#2090)
- Arnold :
  - Added standard AOVs to Outputs node config (#2089)
  - Cleaned up UI for alHair (#2086)
- GraphGadget : (#2078)
  - Added Ctrl+click to select a Backdrop without selecting the nodes it contains
  - Fixed keyboard modifiers for node selection
- SplineWidget (#2079) :
  - Added dropdown menu for selecting interpolation (BSpline/Linear/CatmullRom)
  - Fixed banding when drawing at large sizes

Fixes
-----

- Metadata : Fixed bug which could cause crashes at shutdown if a python slot
  was connected to a metadata signal (#2097)
- Image view : Fixed error handling bug (#2091)
- Catalogue :
  - Fixed hangs caused by GIL management bug (#2085)
  - Fixed bug whereby selection was lost when renaming an image (#2082)
- Backdrop : Fixed problems caused by driving title/description with an expression
  which contains an error (#2083)

API
---

- SceneView : Added `frame()` method for framing objects (#2084)
- GafferSceneUI : Added ContextAlgo namespace containing functions for managing
  scene expansion and selection (#2084)
- PlugWidget/PlugValueWidget : Added `acquire()` methods (#2084)
- WidgetAlgo : Added `grab()` method for taking screengrabs (#2084)

0.33.2.0
========

Features
--------

- Added Image Catalogue node (#2077)
  - Key features include:
      - Loading, exporting, removing, and renaming images on disk.
      - Receiving renders from an InteractiveRender node, automatically combining
        multiple AOVs into a single image stream.
      - Snapshot (copying) images, including in-progress renders.
      - Adding notes to images.
      - Drag 'n' drop of any other image node into the image list to snapshot it
        and add it to the catalogue.

Improvements
------------

- OSL ShadingEngine : Added 'shading:index' special attr to getattribute (#2067)
  - This can be used to fetch the index of the current shading point.

Fixes
-----

- BoxIO : Fixed `setup()` to deal with non-serialisable plugs (#2081)
- DebugDispatcher : Fixed naming bug when creating nodes inside other nodes (#2073)
- Plug : Fixed bug whereby non-serialisable children were serialised (#2077)

API
---

- Display : Added setDriver/getDriver mechanism (#2077)
- PathBinding : Added bindings for pathChangedSignalCreated and havePathChangedSignal (#2077)

0.33.1.0
========

Improvements
------------

- ArnoldOptions : Added "ai:parallel_node_init" (#2062).
  - This defaults off to match Arnold's default, but it may be beneficial to turn on
    in many cases. Note that it is not safe to use with Cryptomatte currently.
- Stats App (#2059) :
  - Added parameter to allow storing stats in a file.
  - Added parameter to optionally supress the node summary.
  - Sorted args alphabetically for consistency of output.
- CompoundDataPlug : Added support for InternedStringVectorData (#2065)
- Dispatcher : Improve batching of no-ops such as TaskList (#2064)
- GafferDispatchTest : Added DebugDispatcher (#2064)
- Documentation : Added metadata reference (#2063)

Fixes
-----

- SetExpressions : Support ':' in names of sets and objects (#2070)
- EventLoop : Specify application name as "Gaffer" (#2071)
- FilterPlugValueWidget : Remove unnecessary node placement code (#2074)

Build
-----

- Using C++03 ABI with GCC 5.1 and greater (#2069)
- Fixed gcc 4.1 compilation issues (#2057)

0.33.0.0
========

Breaking Changes
----------------

- Image :
  - ImageWriter : Defaults to writing all channels instead of just RGB (#2021).
  - DeleteChannels : Changed channels plug default to "" (#2021).
  - ImageStats : (#2018)
    - Defaulted to sampling A in addition to RGB.
    - Changed interpretation of ImageStats channels to simply be a list of 4
      channels that correspond directly to the output RGBA plugs. Behaviour is
      unchanged apart from situations where an incomplete or ambiguous channel
      mask was in use.
  - Warp : New API (#1980).
    - Engine no longer depends on channelName.
    - Derived classes no longer responsible for computing inputWindow.
- API :
  - Renamed UndoContext to UndoScope (#2049).
  - Removed `Nodule::registerNodule()` overload which took a plug name regex.
    Use "plugValueWidget:type" metadata instead (#2045).
  - Added private data member to PerformanceMonitor (#2016).
  - Added `createUStrings` argument to OpenImageIOAlgo::DataView
    constructor (#2040).
  - Removed ChannelMaskPlug.  Use a StringPlug and `StringAlgo::matchMultiple()`
    instead (#2021).
  - Renamed renderer backends to "Arnold" and "Appleseed" (#1994).
  - Added virtual method to Style class (#2051).

Features
--------

- Scene :
  - Added light linking (#1985)
    - Light links are specified as set expressions using the StandardAttributes
      node.
    - Currently only supported in the Arnold renderer backend.
  - Added "scene:renderer" context variable which  can be used to query which
    renderer a scene is being generated for (#1994).
  - SetFilter : Added support for using arbitrary set expressions instead of
    just a single set (#2052).
  - Added RotateTool for interactively rotating objects in the viewport (#2051).
  - Added MeshTangents node to compute Tangent & Binormal primitive variables on a mesh (#2028).
- Image
  - Added Median node (#2022)
  - Added Mix node (#2026)
  - Added CopyChannels node (#2006)
  - Improved support for images with multiple layers : (#2018, #2021)
    - Added layer selector to image viewer
    - Added improved layer/channel selection to many nodes
    - Added ability to use wildcards to select channels to process
  - Added colorSpace plugs to ImageReader and ImageWriter (#2004).
- Box : Added BoxIn and BoxOut nodes to improve the visualisation of promoted
  plugs within the NodeGraph (#2011).

Improvements
------------

- TaskList : Added "sequence plug" (#2044).
- Improved GafferImage performance (#2016, #2031).
- OSLShader : Added support for vector->color connections (#2042).
- Expression : Added context menu for inserting common functions and node
  bookmarks (#2039).
- Stats app : Added performance monitor summary (#2016).
- Merge : Added min and max modes (#2027).
- Grade : Added support for grading alpha channel (#2023).
- Warp : Improved filtering (#1980).
- Added more string matching features #2015 :
  - `[A-Z]` style character classes
  - `?` to match any character
  - '\' to escape a subsequent wildcard
- Added mode and units settings to the UVWarp node, and renamed it to
  VectorWarp (#2014).
- StandardNodeGadget : Added more metadata support (#2011)
  - "icon" to add an icon.
  - "nodeGadget:shape" to choose a rectangular or oval shape

Fixes
-----

- Shader : Fixed bug when assigning a disabled shader
  with pass-through defined (#2025).
- OSLCode : Fixed string length menu item (#2039).
- Expression :
  - Fixed string context variable comparison bug (#2040).
  - Protected context from modification (#2010).
- ErrorDialogue : Fixed bug in message handling code (#2030).
- StringAlgo : Fixed bug in `matchMultiple()` (#2015).
- Switch/Dot : Fixed plug colours in NodeGraph (#2008).
- Transform/Resize : Fixed sinc filter (#1980).
- Fixed export of color/vector plugs from Boxes (#2012).
- Resize : Stopped resampling when only pixel aspect
  ratio is changed (#2007).
- Fixed crash in viewport mouse handling (#2005).
- Fixed Node Reference link in help menu (#2002).
- Fixed framing of lights in the Viewer, by giving them a default bounding
  box (#2054).

API
---

- MetadataAlgo :
  - Added "childNodesAreReadOnly" metadata. This makes it possible to make the
    internal nodes of a node read-only, while still allowing the external
    plugs of the node to be edited (#2048).
  - Added functions for bookmarking nodes (#2039).
  - Added `childAffectedByChange()` overload for Node changes (#2029).
  - Added `copy()` function (#2003).
  - Added `copyColors()` function (#2008).
- NoduleLayout : Added support for custom Gadgets to be specified via metadata
  (#2043).
- ImagePlug :
- Context management (#2041, #2016) :
  - Added Context::EditableScope utility class. Use this instead of the
    now-deprecated Context::Borrowed copy contructor.
  - Added PathScope/SetScope/GlobalScope utility classes to ScenePlug
  - Added GlobalScope/ChannelDataScope utility classes to ImagePlug.
  - Added FilterPlug::SceneScope utility class.
- Added V2iVectorDataPlug (#2031).
- NodeGadget :
  - Added support for "nodeGadget:type" metadata to control the type of gadget
    created by a node (#2029).
- GraphGadget : Added support for dynamically changing "nodeGadget:type"
  metadata (#2029).
- Added ChannelPlugValueWidget (#2026).
- Added RGBAPlugValueWidget (#2018).
- ImageGadget : Added methods for selecting which channels to view (#2021).
- ImageAlgo : Added `channelNames()` and `layerNames()` functions (#2019).
- Added SetAlgo namespace with methods for evaluating set expressions (#1985).
- PathMatcher : Added `intersection()` method (#1985).
- Added FilterAlgo namespace with methods for doing filtered image sampling
  (#1980).
- SceneAlgo : Added render adaptor API. This provides a simple registry
  of SceneProcessors which will be used internally within Render nodes
  to perform just-in-time adaptations of the scene for rendering (#1994).
- PlugAlgo : Added plug promotion methods (#2003).
- Added RotateHandle class (#2051).

Build
-----

- DEBUG build option now also disables optimisations (#2009).
- Enabled coloured compiler output (#2000).
- Updated to use Cortex 9.18.0
- Added QtUiTools module to build package.

0.32.0.0
========

Breaking Changes
----------------

- GLWidget : Replaced setOverlay/getOverlay with addOverlay/removeOverlay (#1979).
- Gadget (#1979) :
  - Added member variable.
  - Made `Gadget::visible()` method const.

Improvements
------------

- ArnoldOptions : Added texture system settings (#1958).
- CustomOptions, CustomAttributes, PrimitiveVariables, OSLCode : Added option to add point and normal values in addition to vectors (#1977).
- OSLShader : Added support for specifying nodule visibility via metadata (#1975).
- Appleseed :
  - Added automatic instancing support (#1978).
  - Added support for multiple cameras (#1978).
- GUI : User defaults are now applied to new ScriptNodes (#1960).
- OpenColorIO : Added support for specifying OCIO context variables per node (#1988).
- UIEditor / UserPlugs :
  - Added menu items for adding array plugs (#1989).
  - Added control for setting the documentation:url metadata (#1995).
- Main menu (#1987) :
  - Added options for flushing Arnold render caches.
  - Added issue tracker link
  - Renamed "mailing list" to "forum"
- GLWidget (#1979) :
  - Added support for multiple overlays.
  - Fixed overlay drawing problems.
- Viewer (#1979) :
  - Added support for tool toolbars.
  - Added support for tool shortcuts.
  - Added sidebar showing all available tools.
  - Added translate and scale manipulators.
- Arnold : Added support for subdiv_smooth_derivs attribute on polymeshes (#1996).

Fixes
-----

- Isolate : Fixed bug when using keepLights or keepCameras (#1965).
- InteractiveArnoldRender : Fixed occasional hangs (#1983).
- Browser app : Fixed shutdown errors (#1981).
- Light visualisers : Fixed errors triggered by specific intensity values (#1982).
- OSLShader : Fixed ambiguities between point, vector and normal types (#1977).
- Display : Fixed to support retries after failing to launch the server (#1972).
- UIEditor : Fixed preset naming bugs (#1966).
- Wrapper : Fixed bugs when Gaffer was installed in a location with spaces in the file path (#1961, #1962).
- ErrorDialogue : Fixed parentWindow lifetime issues (#1986).
- CDL : Fixed dirty propagation (#1988).
- Crop : Fixed hang when using a crop with no input image (#1993).
- DispatcherUI : Removed emulated "PlaybackRange" option which was clashing with CustomRange (#1991).
- NodeUI : Fixed documentation:url metadata (#1995).

API
---

- GafferUI::PlugAdder : Added support for subclassing in Python ()
- CompoundNumericPlug : Added `IECore::GeometricData::Interpretation` setting (#1977).
- Added `GafferImage::OpenImageIOAlgo` namespace with various utility functions (#1977).
- Added `Gaffer::PlugAlgo` namespace with a `replacePlug()` utility function (#1977).
- Fixed binding of `Serialiser::childNeedsSerialisation` (#1973).
- Added `WidgetAlgo.joinEdges()` (#1979).
- Gadget : Added setEnabled/getEnabled/enabled methods (#1979).
- Style : Using enum to define axes for translate/scale handles (#1979).
- StandardStyle : Added `disabledState()` (#1979).

Build
-----

- Fixed build on macOS Sierra (#1978, #1992).
  - Using clang on OSX.
  - Removed troublesome XCode 8.2 build for now.
- Updated standard dependency versions :
  - Appleseed 1.6.0-beta
  - Boost 1.61
  - OSL 1.7.5
  - Alembic 1.6.1
  - FreeType 2.7.1
  - Qt 4.8.7
  - Cortex 9.16.2

0.31.0.0
========

Breaking Changes
----------------

- ScriptNode (#1935)
  - Removed evaluate() method.
  - Removed scriptEvaluatedSignal() method.
  - Reordered virtual methods.
- Options (#1929)
  - Moved "prefix" plug to CustomOptions node.
  - Added virtual method.
- Shader : Removed NetworkBuilder from the API (#1936).
- OSL ShadingEngine : Added argument to `shade()` method (#1944).
- Moved all Algo to nested namespaces (#1953).

Improvements
------------

- ShaderSwitch (#1938)
  - Added support for all parameter types.
  - Added support for expressions and other inputs to the index plug.
- Added a generic Switch node to the NodeGraph menu (#1938).
- ArnoldShader
  - Added support for pass-through of an input parameter when disabled (#1936).
  - Added simplified NodeGraph view for shaders like AlSurface and Standard. They
    are now shown with most parameters hidden by default, and additional parameters
    can be added on demand (#1951).
- OSLShader : Added support for pass-through of input parameters (#1936).
- ArnoldOptions : Added sample clamp options (#1943).
- Camera : Added "Copy From Viewer" item to NodeEditor tool menu (#1950).
- Stats app (#1949)
  - Added command line arguments to output
  - Added current version to output
  - Added -contextMonitor argument (#1952)
- OSLObject : Added support for "world" and "object" coordinate systems (#1944).
- Arnold renderer : Added automatic creation of directories for log files (#1954).
- Rewrote NodeGraph nodule layout code for improved consistency between plugs on nodes
  and nested plugs. StandardNodeGadget and CompoundNodule now support the same set of
  metadata (#1952).

Fixes
-----

- Fixed error when importing GafferScene or GafferImage before GafferDispatch.
- ScriptNode : Fixed node deletion code to automatically reconnect nested child plugs (#1936).
- Set : Fixed update bug (#1941).
- ObjectSource : Fixed update bug (#1941).
- Reference : Fix reload bug where connections to nested plugs were lost (#1940).
- Dot : Fixed bug where output plug was lost during save (#1946).
- OSLImage : Fix `affects()` so input image affects shading.
- ChannelDataProcess : Fix `affects()`.

API
---

- ScriptNode (#1935)
  - Made serialisation and execution useable from C++.
  - Added `isExecuting()` method.
- Switch
  - Added `setup()` method to simplify creation of custom switches.
  - Added `activeInPlug()` method.
- ImageGadget
  - Added `textureLoader()` method.
- Added PlugAdder gadget to simplify the process of adding dynamic
  plugs within the NodeGraph.
- OSL Shading Engine : Added support for named transform spaces (#1944).
- Added ContextMonitor class.
- Menu : Added `modal` argument to `popup()` method.
- MetadataAlgo : Added `affectedByChange()` overload for nodes.

0.30.2.0
========

Improvements
------------

- Graph Layout : Don't apply positions if the layout algorithm fails.
- StandardOptions : Added "render:sampleMotion" parameter.
  - Currently with Arnold support ( RenderMan support requires Cortex update ).
- Arnold backend : Options prefixed with "header:" are written into the header of image outputs.

Fixes
-----

- ArnoldDisplacement :
  - Accepts OSLShader inputs to map plug.
  - Fixed dirty propagation.
- ArnoldOptions : Removed errorColorBadMesh option.
- Arnold backend : Leave instancing of ASS archives to Arnold itself.
  - Fixed a crash bug when Arnold's procedural cache is in use (tested in Arnold 4.2.15.1)
- Build :
  - Fixed failing Travis tests by removing `ImageWriterTest.testMultipleWrite()`.
  - IE options supply DCC specific LINKFLAGS if specified.

0.30.1.0
========

Improvements
------------

- Arnold backend : Added support for adding arbitrary parameters to the Arnold options by using
a CustomOptions node to create options prefixed with "ai:declare:" (#1911).
- ArnoldOptions : Added AA_seed. If not specified, this defaults to the current frame (#1913).
- Expression : Added support for PathMatcherDataPlugs in python expressions. In particular this allows the FilterResults node to be used as an input to an expression (#1915).
- Documentation : Added Expression reference (#1918).

Fixes
-----

- Dispatcher
  - Fixed GIL management bug which could cause deadlock if pre/post dispatch slots launched threads that attempt to use Python (#1916).
  - Fixed UI bug in frame range field (#1917).
- Reference : Reconnect outputs from any plugs.

API
---

- Menu : Added support for `functools.partial` in "active" and "checkBox" fields (#1914).
- NodeGraph : Added support for "nodeGraph:childrenViewable" metadata. This controls whether the subgraph of a node is accessible via the "Show Contents..." menu item and the cursor down keypress (#1914).
- PathMatcher/PathMatcherData : Added Python __repr__ support (#1915).

0.30.0.0
========

Breaking Changes
----------------

- Resample : Replaced `dataWindow` plug with `matrix` plug (#1896).
- OpenImageIOReader : Changed units of cache memory limit methods to bytes (#1895).
- Serialiser : Added `serialisation` argument to all methods (#1882).
- Metadata : Removed `inherit` argument from the `plugsWithMetadata()` and `nodesWithMetadata()`
  methods (#1882).
- ExecutableRender : Removed `command()` method (#1885).
- Changed return type of `Filter::outPlug()`, `FilteredSceneProcessor::filterPlug() and
  `FilterProcessor::inPlug()`. Source code compatibility is maintained.

Features
--------

- Added Mirror node for flipping and flopping images (#1896).
- Added FilterResults node for searching an input scene for
  all locations matched by a filter (#1908).

Improvements
------------

- Reference : Added "Duplicate as Box" menu item in NodeGraph (#1898, #1899).
- Box : Added "Import Reference" menu item in NodeEditor (#1898, #1899).
- OSLObject/OSLImage : Added support for vector shader parameters (#1901).
- OSLShader : Added support for array parameters (#1892).
- Render nodes : Added cache clearing after scene generation (#1900).
- Stats app : Added OIIO memory usage reporting (#1895).
- GUI app : Increased default cache size to 1 gigabyte (#1895).
- Image view : Added solo channel plug and button (#1881).
- Node Graph :
  - The internal network of Reference nodes may now
     be viewed by pressing the cursor down key (#1882).
- ArnoldShader : Added support for "gaffer.plugType" "" metadata.
  This can be used to disable the loading of a plug (#1884).
- Documentation
  - Added release notes section (#1886).
  - Fixed broken links (#1894).
- Improved loading times for scripts with many ArnoldShaders.
- Added support for alternate shiboken install location (#1891).
- Isolate : Added `keepLights` and `keepCameras` plugs (#1893).
- Light Visualisers :
  - Added basic area light visualisations to StandardLightVisualiser.
  - Added visualisation metadata for Arnold quad, disk, cylinder, and skydome lights.

Fixes
-----

- ImageTransform : Fixed negative scaling (#1896, #1613).
- Set : Fixed filter update bug (#1878, #1908).
- Cache preferences : Stopped serialising metadata unnecessarily (#1895).
- OSX (#1879, #1566, #1880, #1885)
  - Fixed numerous build errors
  - Fixed problems caused by System Integrity Protection
- Reference (#561, #1882)
  - Fixed copy/paste of nodes from inside a Reference
  - Prevented editing of internal nodes. They may now be viewed
    but in a read-only state.
- Arnold
  - Fixed ai:shape:step_size attribute (#1883).
- Fixed crashes when using as_color_texture shader (#1905).

API
---

- OpenImageIOReader (#1895)
  - Added `cacheMemoryUsage()` static method
  - Changed units of cache memory limit methods to bytes.
- Serialiser : Added `serialisation` argument to all methods (#1882)
- Metadata (#1882)
  - Added simplified API and deprecated previous API
  - Added MetadataAlgo.h with methods for controlling read-onliness and
    querying if a metadata change affects a particular plug.
  - Removed `inherit` argument from the `plugsWithMetadata()` and `nodesWithMetadata()`
    methods.
- Plug : Deprecated ReadOnly flag - use MetadataAlgo instead (#1882).
- ExecutableRender : Removed `command()` method (#OSX).
- StandardNodule : Added support for "label" metadata (#1889).
- Added M44fVectorDataPlug (#1892).
- ValuePlug : Added `clearCache()` method (#1900).
- ErrorDialogue
  - Added ErrorHandler context manager.
  - Added `messages` constructor parameter.

0.29.0.0
========

Highlights of this release include an entirely rewritten Appleseed backend with support
for editing geometry and environment lights during interactive renders, an OSLCode node
for the writing of OSL shaders within Gaffer, and much improved OSL support in GafferArnold.

Apps
----

- Screengrab
  - Added delay command line argument (#1861).

Core
----

- StringPlug
  - Fixed substitutions when plug has an input (#1860).

Appleseed
---------

- InteractiveAppleseedRender (#1833)
  - Reimplemented completely to using new Gaffer scene description
    APIs.
  - Added support for adding/removing/deforming/transforming objects during rendering.
  - Added support for changing environment lights during rendering.
  - Improved performance and responsiveness.
- AppleseedRender (#1833)
  - Reimplemented completely to using new Gaffer scene description APIs.
- AppleseedShaderBall
  - Added threads and max samples settings (#1833).
  - Increased sphere tesselation #1869.

Arnold
------

- InteractiveArnoldRender
  - Added support for editing subdivision attributes while rendering (#1855).
- ArnoldOptions
  - Added log verbosity settings (#1866).
- OSL
  - Improved OSL shader support using Arnold's new osl_shader node (#1873).
- Improved warning messages for unsupported parameters (#1872).

OSL
---

- Added OSLCode node, to allow editing of OSL shader snippets on the fly (#1861).

UI
--

- ArnoldShader
  - Added support for specifying UI layout via Arnold metadata.
    In particular, this greatly improves the NodeEditor UI for the
    AlShaders (#757, #1864).
- ArnoldAttributes
  - Fixed formatting of Subdivision section summary (#1855).
- NodeMenu
  - Sorted Arnold shaders into submenus (#1870).
- ScriptEditor/Expression/PythonCommand
  - Made code font monospaced (#1861).
- ShaderView
  - Fixed initial framing  (#1861).
  - Fixed bug triggered by shaders changing type  (#1861).
- Expression
  - Fixed broken popup menus on non-ValuePlugs (#1861).
- OSLShader
  - Fixed support for "null" widget type (#1865).
- ImageReader/SceneReader/AlembicSource
  - Improved layout of reload button (#1867).
- ArnoldOptions
  - Moved threads setting to Rendering section.
- Added indentation to nested collapsible widgets (#1866).
- SceneInspector
  - Fixed errors when selected path doesn't exist (#1874).
- Display
  - Don't attempt to start server unless UI is connected (#222).
- Added home shortcut for image view.
- Selection/Crop Tools
  - Fixed precision issues when far from origin.

Documentation
-------------

- Consolidated reference docs into a parent section (#1860).
- Added string substitutions reference (#1860).

API
---

- Renderer
  - Added bool return value to ObjectInterface::attributes(), to signify
    success/failure #1855.
- OSLShader
  - Added support for unloading with `OSLShader::loadShader( "" )` (#1859).
  - Fixed loading of surface type after loading of shader type (#1859).
- LabelPlugValueWidget
  - Added support for "labelPlugValueWidget:renameable" metadata (#1861).
- MultiLineTextWidget
  - Added "role" property (#1861).
- MultiLineStringPlugValueWidget
  - Added support for specifying role via "multiLineStringPlugValueWidget:role"
    metadata (#1861).
- OSL
  - Added GafferOSL/Spline.h header, to simplify use of splines in shaders (#1861).
- View
  - Removed `virtual void plugDirtied()`.
- CompoundDataPlug
  - Added support for BoolVectorData (#1863).
- PlugLayout
  - Added support for "layout:accessory" metadata.
- Added RefreshPlugValueWidget and deprecated IncrementingPlugValueWidget (#1867).
- ViewportGadget
  - Don't convert raster positions to V2i.

Build
-----

- Added OSLHOME build option, only necessary when building without using GafferHQ/dependencies (#1871).

Breaking changes
----------------

- View
  - Removed `virtual void plugDirtied()`.

0.28.3.0
========

OSL
---

- Metadata
  - Support OSL "page", "connectable", and "URL" metadata
  - Support metadata on spline plugs
  - Support min/max metadata

0.28.2.1
========

API
---

- ArnoldShader
  - Fix `outPlug()` loading bug introduced in 0.28.2.0.


0.28.2.0
========

UI
--

- Fixed incorrect re-use of widgets when swapping plugs with the same name.

Scene
-----

- Fixed context scoping issue during renders.

Arnold
------

- Added curve min_pixel_width and mode attributes.
- Shaders are now re-loadable, and will automatically reload during script load.

Cortex
------

- Fixed incorrect re-use of plugs when swapping parameters with the same name.

API
---

- SceneAlgo
  - Fixed context used by `sets()` function.
- RendererAlgo (preview)
  - Fixed context used by `RenderSets` class.
- ArnoldShader
  - Added keepExistingValue argument to `loadShader()`.
  - Added `loadShader()` to serialisation.
  - Reusing existing plugs wherever possible.
- CompoundParameterHandler
  - Match by parameter object instead of name.
- CompoundPlugValueWidget
  - Match by plug object instead of name.

0.28.1.0
========

UI
--

- The 3D Viewer can now look through lights (#1846).
- Prefixed NodeMenu search text for RSL and OSL shaders with ri and osl respectively (#1850).

Arnold
------

- Added support for trace sets (#1847). Any standard gaffer set with a name beginning with "render:" will be exported to Arnold as a trace set.
- Fixed ArnoldDisplacement crash (#1849).
- Added support for a `gaffer.nodeMenu.category` metadata value to customise the shader menu (#1850).

Scene
-----

- Added LightToCamera node (#1846).

API
---

- Context (#1848)
  - Added GIL release in `set()` method bindings to
    fix potential deadlocks.
  - Fixed bug which meant that `remove()` wasn't
    emitting `changedSignal()`.
- SceneAlgo
  - Added `sets()` overload to compute a subset of all sets.
- RendererAlgo (preview)
  - Added RenderSets utility class.
  - Modified output methods to take a RenderSets argument.
- ShaderPlug
  - Fixed bug involving plugs with no input (#1849).

Build
-----

- Added INSTALL_POST_COMMAND option, to allow custom commands to be run after installation (#1845).

0.28.0.1
========

UI
--

- Viewer
  - Construct as invisible to avoid unnecessary updates
  - Improved renderer management for shader swatches
  - Support reregistration of shader swatch scenes

Scene
-----

- FilterPlug
  - Fixed compatibility with legacy SubGraphs and Dots

Arnold
------

- ArnoldShaderBall
  - Added threads plug and limited cores used by the shader swatches

Appleseed
---------

- Removed unwanted shaders from Appleseed shader menu

Build
-----

- Resources now install even when not building docs

0.28.0.0
========

UI
--

- Viewer
  - Added interactive shader swatches (#1828).
  - Added visualisation of Arnold spotlight lens radius (#1835).
  - Fixed visualisation of lights aligned to camera (#1835).
- NodeGraph
  - Added "Move To" menu items for Dot nodes.
- InteractiveRender
  - Added Play/Pause/Stop buttons.

Scene
-----

- Added LightTweaks node (#1829).
- Added ShaderBall node (#1828).
- Added CopyOptions node (#1834).
- Fixed FilterSwitch serialisation bug (#1814, #1815).

Arnold
------

- Added support for shader network inputs to light parameters (#1828).
- Added support for spline shader parameters (#1813).
- Added support for OSL shaders (#1813).
- Added bucketSize and bucketScanning options to ArnoldOptions node (#1827).
- Added ArnoldShaderBall node (#1828).
- Added performance monitor support to ArnoldRender (#1831).
- Improved parameter linking support in renderer backend.
- Fixed crashes caused by trying to use two render nodes at once in the same process (#1818).

Appleseed
---------

- Added AppleseedShaderBall node (#1828).
- Fixed problems with searchpath initialisation (#1828).

RenderMan
---------

- Added RenderManShaderBall node (#1828).

Dispatch
--------

- Fixed performance problems with complex dispatch graphs (#1820).

Image
-----

- Fixed sizing of whitespace in Text node (#1822).

OSL
---

- Fixed problems with OSL_SHADER_PATHS initialisation (#1813).

Documentation
-------------

- Added missing image to "Getting Started" tutorial (#1810).

Build
-----

- Replaced appleseed build options with single APPLESEED_ROOT option (#1812).

API
---

- Scene
  - Added FilterPlug (#1815).
  - Added ShaderPlug (#1828).
  - Deprecated public attributes methods on Shader node.
  - Allowed ObjectSource derived classes to define more than one default set (#1821).
- UI
  - Added `Gadget::visibilityChangedSignal()` (#1828).
- Arnold
  - Added gaffer.plugType metadata support for shader parameters (#1817).
- Monitor
  - Added support for NULL argument to Scope class (#1831).

Breaking Changes
----------------

- Added an argument to `GafferArnold::ParameterAlgo::setupPlug()` (#1817).
- Modified ObjectSource virtual methods (#1821).

0.27.1.0
========

Core
----

- Fixed crash caused by using an invalid expression language (#1801).

Arnold
------

- Fixed motion blurred light bug (#1805).
- Fixed overscan rendering (#1803).

OSL
---

- Added support for matrix parameters (#1798, #1800)

API
---

- Replaced cropWindow with renderRegion in new IECoreScenePreview::Renderer::camera().

0.27.0.1
========

UI
--

- ViewportGadget
  - Exposed world position to shaders

0.27.0.0
========

Apps
----

- Screengrab (#1793, #1559)
  - Added arguments for Viewer and NodeGraph framing
  - Added arguments for Viewer and SceneHiearchy expansion and selection
  - Added argument for grabbing a single plug from the NodeEditor

Scene
-----

- Fixed SubTree to error when an invalid root is entered (#1786, #1790).
- Added filter input to Set, to define additional paths to add/remove.

Arnold
------

- Added ArnoldMeshLight node (#1787)
- Added ArnoldDisplacement node (#1776)
- Added subdivision attributes to ArnoldAttributes (#1776)
- ArnoldOptions (#1788)
  - Added total depth and transparency depth/threshold plugs
- Fixed warnings about unhandled light parameters
- Fixed crashes/errors caused by multiple cameras and a threading
  bug (#1785)
- Fixed bogus warning about "ai:log:filename" option.

OSL
---

- Expression (#1791, #1789)
  - Fixed string comparison bug
  - Fixed bugs when plug names share a common prefix
  - Fixed mistaken assignments
- Added support for spline parameters in shaders (#1782)
- Fixed reload button on shader UI

Documenation
------------

- Added basic lighting and rendering tutorial (#1793).

Build
-----

- Fixed debug builds (#1781)
- Added debug builds to Travis tests (#1781)
- Fixed clang compilation error in Serialisation.cpp

API
---

- Made FilteredSceneProcessor subclassable in Python.

Breaking Changes
----------------

- Rederived Set from FilteredSceneProcessor.
- Changed LightVisualiser API
  - Added attributeName argument to visualise() virtual method.
  - Added attributeName argument to registerLightVisualiser() factory method.
- Changed StandardLightVisualiser metadata prefix convention from
  "light:renderer:shaderName" to "renderer:light:shaderName", to
  match the ordering of the data as it appears in the scene module
  (attributeName:shaderName).
- Light nodes now output IECore::Shader objects rather than IECore::Lights

0.26.0.0
========

Arnold
------

- Added automatic instancing of identical objects (#1775).
- Added support for user attributes (#1775).
- Added support for filter widths in output specifications (#1773).
- Updated subdivision attributes to match Arnold versions 4.2.8.0 and
  onwards (#1775).
- Moved path setup to wrapper. This means that `gaffer env kick` can
  be used to render a pregenerated ass file (#1774).

UI
--

- NodeGraph
  - Added automatic layout of nodes generated by scripts (#1751, #1771).
  - Fixed duplicate position plug names (#762).

API
---

- Renamed ExecutableNode to TaskNode (#1767).
- Protected TaskNode internal virtual methods. Use the TaskPlug
  methods instead (#1767).
- Replaced OSLRenderer with ShadingEngine (#1770).
- GraphGadget
  - Added unpositionedNodes() method (#1751).

Build
-----

- Updated public build to use OSL 1.7.2 and OIIO 1.6.14.

Breaking Changes
-----------------

- Renamed ExecutableNode.
- Protected internal TaskNode methods.
- Replaced OSLRenderer with ShadingEngine.
- Dropped support for OSL versions prior to 1.7.

0.25.1.0
========

Apps
-----------------------------------------------------------------------

- Screengrab
  - Support for grabbing the ScriptEditor.

UI
-----------------------------------------------------------------------

- Fixed crash on mouse move over an about-to-become-visible GLWidget.

Scene
-----------------------------------------------------------------------

- Attributes
  - Avoided unnecessary dirty propagation.
  - Deactivated filter field when in global mode.
- InteractiveRender
  - Fixed object visibility bug.
  - Fixed context management bugs.
- RenderUI
  - Exposing nodules for task plugs.

Image
-----------------------------------------------------------------------

- ImageGadget
  - Taking pixel aspect into account when drawing.
  - Fixed color inspector for non-square pixels.

Arnold
-----------------------------------------------------------------------

- ArnoldRenderer
  - Reusing shaders where possible.
  - Ensuring shader nodes are named (uniquely).
  - Fixed sharing of attributes between lights.
  - Fixed time_samples.
  - Fixed default shader override on ExternalProcedurals.
- ArnoldOptions
  - Added missing sampling and depth options.
- ArnoldAttributes
  - Supporting additional shading attributes.
    - "ai:matte", "ai:opaque", "ai:receive_shadows" and "ai:self_shadows"

Documentation
-----------------------------------------------------------------------

- Added scripting tutorials and reference.
- Added bookmarks to config file tutorial.
- Added examples for the "test" app.
- Added OpenVDB license to appendices.
- Renamed "Performance Guidelines" tutorial to "Managing Complexity".

API
-----------------------------------------------------------------------

- ScriptEditor
  - Added inputWidget() and execute() methods.
- ImageGadget
  - Added pixelAt() method.
  - Added missing bindings.

0.25.0.0
========

Apps
-----------------------------------------------------------------------

- Fixed ordering of GAFFER_STARTUP_PATHS, so that custom scripts can
  override Gaffer's built in configuration files (#1752).

Scene
-----------------------------------------------------------------------

- Set
  - Added support for modifying multiple sets with a single node,
    by entering multiple names separated by spaces (#1748).

Arnold
-----------------------------------------------------------------------

- ArnoldRender node now uses the same backend as the
  InteractiveArnoldRender node. Rendering is now performed directly
  in Gaffer rather than using a procedural (#1755).
- ArnoldShader ( #1758)
  - Added support for BYTE and UINT input parameters and VECTOR
    and POINT output types.
- Added support for crop windows, overscan and resolution multipliers
  (#1744).

Build
-----------------------------------------------------------------------

- Fixed compilation of GafferAppleseed with GCC 5 (#1757).

API
-----------------------------------------------------------------------

- Made IECorePreview module private (#1731).
- Changed default orientation of environment light visualiser (#1749).
- Fixed SceneAlgo::camera() when "option:render:camera" is "".

Incompatibilities
-----------------------------------------------------------------------

- Made IECoreScenePreview private.
- ArnoldRender node no longer has a verbosity plug.
- Changed default orientation of environment light visualiser.

0.24.1.0
========

Core
-----------------------------------------------------------------------

- Fixed performance of acceptsInput() for serial Switch networks (#1722)
- Context now uses GeometricTypedData where appropriate.
- Disallow setting user defaults on nodes in nodes.
- Fixed serialization of dynamic TransformPlug

UI
-----------------------------------------------------------------------

- Improved picking of "backwards" connections.

Apps
-----------------------------------------------------------------------

- Added basic documentation.

Scene
-----------------------------------------------------------------------

- Updated several nodes to register metadata in one shot with `registerNode()`
- SceneView
  - Fixed drawing mode.
  - Added controls for curve drawing.
    - Using uninterpolated GL lines by default.
- Restored default base state in SceneGadget.
- GafferScene
  - Added preview of new Cortex Renderer API.
  - Added preview of RendererAlgo for new Renderer API.
  - Added preview of new InteractiveRender node.
- SceneAlgo
  - Added `globalAttributes()` function.
- SceneNode
  - Reduced unnecessary dirty signalling.

Image
-----------------------------------------------------------------------

- Removed unnecessary `UVWarp::Engine::hash()` method.
- ImageWriter can now be subclassed in Python.

OSL
-----------------------------------------------------------------------

- Updated OSLShaderUI to register metadata in one shot with `registerNode()`
- OSL Expressions now support V3f data from the Context.

Arnold
-----------------------------------------------------------------------

- ArnoldOptions
  - Added licensing section.
  - Added basic support for controlling render logs.
- Added preview of IECoreArnold ShaderAlgo.
- Added preview of IECoreArnold ProceduralAlgo.
- Added preview of new IECoreArnold Renderer.
- Added InteractiveArnoldRender node.
- Added support for Arnold matrix parameters as M44fPlugs

RenderMan
-----------------------------------------------------------------------

- Remove deprecated RenderManShaderUI class
- Updated RenderMan shaders to register metadata in one shot with `registerNode()`

0.24.0.0
========

UI
-----------------------------------------------------------------------

- Added node reference documentation menu item to NodeEditor tool menus.
- GafferUI.Collapsible supports Widget.reveal().
- ScriptWindow no longer stops the EventLoop if it's already stopped.
- Fixed PathWidget WeakMethod error at shutdown.

Scene
-----------------------------------------------------------------------

- Improved error messages emitted by Group node.

Image
-----------------------------------------------------------------------

- Fixed UVWarp crash triggered by negative data window origins (#1707).

OSL
-----------------------------------------------------------------------

- Fixed crash when deleting connections to an OSL expression (#1695).
- Added support for BoolPlugs in OSL expressions (#1697).

Dispatch
-----------------------------------------------------------------------

- Stopped SystemCommand swallowing the stdout of launched processes
  (#1712).
- Disabled automatic substitutions for command (#1692). This was broken
  by #1671.
- Added LocalDispatcher environmentCommand plug.

Arnold
-----------------------------------------------------------------------

- Added ArnoldVDB node (#1711).
- Added volume step size to ArnoldAttributes node (#1694).
- Fixed metadata for ArnoldLight UIs (#1696).
- Added "ai:threads" option
  - Exposed via ArnoldOptions under the Performance section.
  - ArnoldRender uses ai:threads option to drive kick -t command line arg.

Apps
-----------------------------------------------------------------------

- Removed procedural app
- Screengrab app
  - Added `-editor` argument
  - Added `-selection` argument
  - Added `-nodeEditor.reveal` argument
  - Fix crashes at shutdown

Documentation
-----------------------------------------------------------------------

- Introduced HTML documentation which is shipped with every Gaffer
  release (#1702, #1708, #1710).
- Mentioned PerformanceMonitor.

Build
-----------------------------------------------------------------------

- Simplified packaging. Use the gafferDependencies project if the
  dependencies are needed for your build.
- Convert BUILD_DIR to an absolute path.

API
-----------------------------------------------------------------------

- View (#1713)
  - Removed View3D and ObjectView derived classes.
  - Removed update() and updateRequestSignal() methods.
- Added DocumentationAlgo namespace with functions to assist in
  auto-generating documentation.
- Removed CompoundPlug usage from Shader nodes (#1701).
- Added **kw arguments to all Widget constructors.
- Removed deprecated Widget keyword arguments(#655, #1704).
- Removed all use of deprecated IECorePython::Wrapper (#1116, #1703).
- Removed deprecated `ValuePlug::inCompute()` method. Use `Process::current()`
  instead.
- Removed deprecated `Filter::matchPlug()` method. Use `Filter::outPlug()`
  instead.
- Removed deprecated SignalBinder class. Use SignalClass instead.
- Removed deprecated iterator methods. Use `Iterator::done()` instead.

0.23.2.0
========

Apps
-----------------------------------------------------------------------

- Stats
  - Fixed bug which caused errors when there were no items to print
    in a particular category (#1667).
  - Added -performanceMonitor flag, which outputs in depth statistics
    for use in analysing and optimising performance (#1668).
  - Added -image flag for outputting image statistics (#1680).

UI
-----------------------------------------------------------------------

- Added back "Remove Input" menu option for promoted plugs. This differs
  from the "Unpromote" option in that it breaks the connection but keeps
  the promoted plug on the outside of the box (#1678).
- NodeGraph (#1679)
  - Tightened rules for inserting nodes into noodles. Nodes are now only
    inserted when disabling the inserted node would create a pass-through
    equivalent to the original connection, and deleting the node will
    restore the original connection. Previously nodes could be inserted
    in such a way that one end of the connection was broken, or two new
    connections were made which had no logical in->out connection through
    the inserted node.
  - Stopped highlighting connections when hovering in their middle, where
    they cannot be dragged anyway.
  - Made it harder to accidentally drag a long connection by grabbing it
    in the middle - the sensitive section is now limited to a shorter
    segment near the end.

Scene
-----------------------------------------------------------------------

- Improved output of objects and transforms which are static, but for
  which motion blur has been requested via StandardAttributes. Motion
  blocks are now omitted when no motion is detected (#1662).
- ScriptProcedural (#1676)
  - Fixed clearing of caches after procedural expansion in Arnold.
  - Improved error reporting to include the node which caused the
    error.
  - Added support for performance monitoring.
- StandardOptions
  - Added new performanceMonitor option, which enables/disables the
    performance monitoring now supported by the ScriptProcedural
    (#1676).
- Duplicate
  - Optimised set name computation. This knocks 35% off the time
    to compute a set in a custom downstream node with certain
    suboptimal qualities (#1682).
- Fixed hangs caused by missing GIL management in SceneAlgo
  bindings (#1686, #1687).

Dispatch
-----------------------------------------------------------------------

- ExecutableNodes now support automatic substitution of variables in
  StringPlug values, in the same way as has always been supported
  by other node types (#887, #1671).
- Fixed order of dispatch when postTasks exist (#1675).

Arnold
-----------------------------------------------------------------------

- Removed use of deprecated UI APIs. Specifically,
  `PlugValueWidget.registerCreator()` has been deprecated, and all code
  should use the equivalent "plugValueWidget:type" metadata instead
  (#1673).

RenderMan
-----------------------------------------------------------------------

- Added initial support for using OSL shaders in 3delight.

Appleseed
-----------------------------------------------------------------------

- Updated to [Appleseed 1.4.0-beta](https://github.com/appleseedhq/appleseed/releases/tag/1.4.0-beta).
- Renamed volume priority attribute to medium priority.

Cortex
-----------------------------------------------------------------------

- Fixed UI error when launching a ClassVectorParameter UI with
  preexisting child parameters (#665, #1670).

Documentation
-----------------------------------------------------------------------

- Added GafferDispatch to the API docs.

API
-----------------------------------------------------------------------

- Added Process and Monitor classes. Processes expose internal
  processes such as ComputeNode::compute() and ComputeNode::hash()
  to Monitors - classes which can observe the internal workings of
  Gaffer via the exposed Processes (#1668).
- Added PerformanceMonitor class. This uses the Monitor/Process
  API to collect statistics useful in analysing and optimising
  performance (#1668).
- RendererAlgo
  - Added outputObject() method (#1662).
  - Added outputTransform() method (#1662).
- ValuePlug
  - Deprecated inCompute() method - use Process::current() instead
    (#1668).
- FormatData
  - Added workaround for unstable hash() method when compiling with
    GCC 4.4.7 (#1669).
- ExecutableNode
  - Moved public interface to TaskPlug. The ExecutableNode virtual
    interface is now considered to be protected, and will be made
    so in a future release.
- ScenePlug
  - Fixed python binding for pathToString().
  - Added helpers for accessing globals and set names. These manage
    the context such that it is friendlier to the hash cache, by
    removing variables we know to change frequently but which cannot
    affect the result #(1683).

Build
-----------------------------------------------------------------------

- Updated Cortex to version 9.8.0.
- Updated Appleseed version to 1.4.0-beta.

0.23.1.0
========

Apps
-----------------------------------------------------------------------

- Stats App
  - Added outputs for scene traversal time and memory usage.

Core
-----------------------------------------------------------------------

- Improved performance of the computation cache, particularly when under
  heavy multithreaded load (#1638).
- Fixed GIL lock issues.
  - CompoundDataPlug releases when adding child plugs.
  - GraphComponent releases when adding/removing children.
  - Reference releases in load().
- Switch
  - Add SwitchTraits<BaseType> to control context for index evaluation.

UI
-----------------------------------------------------------------------

- SceneHierarchy
  - Added search field (#1572, #1649).
  - Added set filter (#48, #1649).
- NodeEditor
  - Improved error handling for labels and multiline text fields (#1650).
- NodeGraph
  - Fix "Find..." shortcut.
- SceneInspector
  - Fixed labelling of CoordinateSystem sets (#1648).
- ExecutableNode
  - Fixed UI for individually promoted pre/post tasks (#1647).
- UIEditor
  - Add label field to plug section.
- GLWidget
  - Supports use in Maya when using PySide.

Scene
-----------------------------------------------------------------------

- ScenePlug
  - set() and setHash() are friendlier to the hash cache.
- SceneSwitch
  - Removed scene:path from context for index.
- FilterProcessor
  - Implement pass-through when disabled.
- PathFilter
  - Fixed bugs which treated empty paths as "/" rather than ignoring them (#1642)
   - Avoid unnecessary hashing of __pathMatcher plug.
- Set
  - Fixed bugs which treated empty paths as "/" rather than ignoring them (#1642)
- SetFilter
  - Remove unnecessary context manipulation..
- DeleteSets
  - Fixed bug which could pass-through a deleted set.
- Isolate/Prune
  - Fixed bugs which caused incorrect results when used with a
    particular custom filter outside of Gaffer (#1652).
- Shader
  - Fixed crashes caused by cyclic connections in shader networks (#1646).
- Fixed GIL lock issues.
  - Outputs releases in addOutput().

Image
-----------------------------------------------------------------------

- Warp
  - Added Warp base class.
  - Added UVWarp node.
- BufferAlgo
  - Added index() function.
- ImageSwitch
  - Removed tile variables from context for index.

RenderMan
-----------------------------------------------------------------------

- Fixed GIL lock issues.
  - RenderManShader releases in loadShader().

API
-----------------------------------------------------------------------

- PathMatcher
  - Fixed bugs which treated empty paths as "/" rather than as empty (#1642).
- SceneAlgo
  - Added PathMatcher overloads for `filteredParallelTraverse()` and
    `matchingPaths()` (#1649).
- MultiLineTextWidget
  - Added `setErrored()/getErrored()` methods to (#1650).
- MultiLineStringPlugValueWidget/LabelPlugValueWidget
  - Added error handling (#1650).
- ExecutableNode
  - Disabled nodule creation by default for all but TaskPlugs. Nodules
    can be explicitly reenabled using a ( "nodule:type", "GafferUI.StandardNodule" )
    metadata registration for a particular plug.
- DownstreamIterator/RecursiveChildIterators
  - Fixed API for completion of iteration.
- FilteredChildIterator
  - Added done() method.
- TypedObjectPlug bindings : Add _copy argument to defaultValue() method.

Build
-----------------------------------------------------------------------

- GafferUI now links to QtOpenGL

0.23.0.1
========

Cortex
-----------------------------------------------------------------------

- Fixed ParameterisedHolder::parameterChanged() exception handling.

0.23.0.0
========

Core
-----------------------------------------------------------------------

- Reverted cyclic connection check on plug connection
- Reduced hash cache clearing frequency to speed up instancing.

UI
-----------------------------------------------------------------------

- Fixed labelling of renamed plugs which had a custom label. The label
  is now removed by the rename operation (#1635).

Scene
-----------------------------------------------------------------------

- Improved set performance and memory usage significantly for all node
  types (#1623).
- Added a MeshToPoints node (#1640).
- Added sets support in the Duplicate node (#1623).

Arnold
-----------------------------------------------------------------------

- Added support for motion blur, courtesy of Cortex 9.7.0.

API
-----------------------------------------------------------------------

- Fixed python bindings to accept any iterable where previously only
  lists were accepted (#1634).
- ScriptWindow
  - Added createIfNecessary argument to ScriptWindow.acquire() (#1639).
- NameLabel (#1635)
  - Exposed default formatter.
  - Deprecated setText().
- PathMatcher (#1623)
  - Reimplemented using lazy-copy-on-write sharing.
  - Added addPaths() overload with prefix path.
  - Added subTree() method.
  - Added `RawIterator find( path )` method.

Build
-----------------------------------------------------------------------

- Updated release builds to Cortex 9.7.0.
- Updated OCIO build to be compatible with Maya. It should now be
  possible to run a standard Gaffer build from within Maya.

Incompatibilities
-----------------------------------------------------------------------

- PathMatcher binary compatibility changes.

0.22.0.0
========

This release brings support for dispatching via Pixar's Tractor, in
additional to the usual medley of bug fixes and optimisations.

Core
-----------------------------------------------------------------------

- Prevented the creation of cyclic connections (#1630).

UI
-----------------------------------------------------------------------

- Fixed bugs in "Set Key" plug menu item.
- Fixed Backdrop node positioning when creating a backdrop with no
  nodes selected (#1625).
- Fixed NodeEditor layout problems caused by long summaries (#1629).

Scene
-----------------------------------------------------------------------

- SceneProcedural (#1615)
  - Fixed bug which could cause motion blurred bounding
    boxes to be computed incorrectly.
  - Removed duplicate attribute computations. This shaves
    9% off the time to first pixel for a complex benchmark scene.

RenderMan
-----------------------------------------------------------------------

- Improved time to first pixel for raytraced 3delight renders (#1614).

Arnold
-----------------------------------------------------------------------

- Fixed warnings about inaccurate bounds (#1614).

Appleseed
-----------------------------------------------------------------------

- Added support for volume priority attribute (#1631).

Tractor
-----------------------------------------------------------------------

- Added a new GafferTractor module, which enables dispatching of
  Gaffer's task graphs to renderfarms running Pixar's Tractor (#1619).

Cortex
-----------------------------------------------------------------------

- Fixed UI for promoted presets parameters (#1624).
- Fixed parameter ordering in UI (#1627).

API
-----------------------------------------------------------------------

- ValuePlug
  - Prevented the addition of children which are not themselves
    ValuePlugs.
  - Allowed subclassing in Python.
- FilteredSceneProcessor
  - Removed restrictions on `Filter::sceneAffectsMatch()` (#1620).
- SceneProcedural/ScriptProcedural
  - Added support for using Renderer::Procedural::noBound (#1614).
- Fixed GIL management in DependencyNodeWrapper.
- Added DownstreamIterator.
- Improved error handling during dirty propagation.
- Batched dirty propagation during script loading, execution and
  destruction (#1632).

Tests
-----------------------------------------------------------------------

- Unexpected messages are now treated as errors.

Build
-----------------------------------------------------------------------

- Requires Cortex 9.6.0.

0.21.0.0
========

Apps
-----------------------------------------------------------------------

- Added `gaffer stats` application. This takes a script and prints out
  information about version, settings, variables and nodes (#1437).

Core
-----------------------------------------------------------------------

- Fixed serialisation of quotes and other special characters in metadata
  keys. This was most visible when using special characters in custom
  preset names (#1599).
- Simplified metadata serialisations (#1599).

UI
-----------------------------------------------------------------------

- Fixed UV orientation for area light visualisations (#1600).
- Fixed environment light visualisations on OSX (#1609).
- Viewer (#1592)
  - Improved image viewer performance.
  - Fixed several image viewer bugs (#1427, #1426, #1356, #773).
  - Added support for custom toolbars on all edges of the viewer,
    for both views and nodes.
- Fixed hang when browsing scene locations (#1618).

Image
-----------------------------------------------------------------------

- Fixed reference counting bugs in Premultiply and Unpremultiply nodes
  (#1598).
- Fixed crashes caused by Merge requesting nonexistent upstream
  channels (#1596).

Appleseed
-----------------------------------------------------------------------

- Added support for exposure parameters on Appleseed lights (#1608).
- Simplified light menus (#1608).
- Improved environment light visualisations (#1608).

API
-----------------------------------------------------------------------

- ImageAlgo
  - Added channelExists() function (#1596).
- ExceptionAlgo
  - Fixed line number extraction for syntax errors (#1599).
- Menu
  - Fixed broken shortcuts after assigning new menu definition (#1597).
  - Fixed scoping of MenuBar shortcuts. In particular this fixes
    a bug whereby an embedded Gaffer panel could prevent Maya's
    main window shortcuts from working (#1597).
- Replaced all old-style python classes with new style ones #1607.
- GafferImageUI
  - Added ImageGadget class.
- PlugLayout improvements
  - Added support for "layout:divider" metadata - this replaces
    the old "divider" metadata.
  - Added support for multiple layouts, using a different metadata
    prefix for each layout.
  - Added support for creating partial layouts, using a new rootSection
    constructor argument.
- Toolbar improvements
  - Toolbars can now be defined for all edges, not just the top of
    frame (#1592).
  - StandardNodeToolbar has a new constructor argument to choose which
    edge to create the toolbar for. A new "toolbarLayout:section" metadata
    value chooses which toolbar plugs belong in, with values of
    "Top", "Bottom", "Left" and "Right" (#1592).
- GLWidget
  - Improved overlay mechanism. Overlays may be queried and removed as
    well as set. Container overlays are transparent to mouse events in
    areas where no child widget exists (#1592).
- NumericPlugValueWidget
  - Added support for "fixedCharacterWidth" metadata.

Build
-----------------------------------------------------------------------

- Added GCC 5 build to Travis test setup.

Incompatibilities
-----------------------------------------------------------------------

- Removed ImageView::update() virtual override.
- Replaced GLWidget.addOverlay() method with setOverlay()/getOverlay() methods.

0.20.0.0
========

Apps
-----------------------------------------------------------------------

- Added support for choosing the debugger used via a new GAFFER_DEBUGGER
  environment variable.

Core
-----------------------------------------------------------------------

- Improved ContextProcessor performance. This shaved 10% off the startup
  time for a complex render (#1573).
- Added framesPerSecond plug to ScriptNode. This provides user-level
  control over the frame rate for each script (#1576).
- Fixed hang triggered by deletion of a plug during computation
  (#1576, #1580).

Dispatch
-----------------------------------------------------------------------

- Moved all dispatch functionality from Gaffer module into a new
  GafferDispatch module. Backwards compatibility is provided by
  config files, but it is recommended that code be updated to use
  GafferDispatch directly (#1577).
- Renamed "requirements" plug to "preTasks" and "requirement" plug
  to "task". Again, backwards compatibility is provided by a config
  file, but it is recommended that code be updated to use the new
  names (#1577).
- Added "postTasks". These are nodes that are executed following another
  node, even if they are not explicitly included in the list of nodes
  to dispatch (#1577).
- Added "dispatcher.immediate" plug to all executable nodes. This
  causes the node to be executed immediately in the current process
  when dispatched (#1577).
- Removed "dispatcher.local.executeInForeground" plug - use the new
  "dispatcher.immediate" plug instead (#1577).
- Added sequence support to PythonCommand node. This causes the command
  to be called once for all frames, instead of once per frame (#1578).
- Fixed bug which could cause all frames downstream of pass-through
  nodes (like TaskList and TaskContextVariables) to depend on all
  upstream frames (#1577).
- Fixed detection of direct dependency cycles (#1577).

Image
-----------------------------------------------------------------------

- Crop
  - Added option to crop to a specific format, optionally centered (#1570).
- Fixed crashes triggered by images with empty data windows (#1575).
- Improved ImageWriter to write out images progressively as the input
  image is generated (#1517). This improved speed by 65% and memory usage
  by 60% when generating a 10K image.

Scene
-----------------------------------------------------------------------

- Lights are now represented as attributes at a location rather than as
  objects. This allows lights for multiple different renderers to exist
  at the same location, allows the creation of area lights, and provides
  the necessary support for using shader networks within lights in the
  future (#1590).
- Shader nodes now support the loading of light shaders (#1590).
- Added metadata support for specifying the orientation of lights
  in the renderer (#1590).

RenderMan
-----------------------------------------------------------------------

- Fixed crash when reloading coshader arrays.

UI
-----------------------------------------------------------------------

- Improved viewport visualisation of lights (#1590, #11).
- Added workaround for PySide bug which prevented stylesheets from
  working as expected (#1574).
- Improved error reporting for failed dispatches (#1593).
- Fixed graphical glitch in OpDialogue error icon (#1593).

API
-----------------------------------------------------------------------

- ImageAlgo
  - Added parallelProcessTiles and parallelGather tiles functions
    to facilitate easy parallel processing of images (#1517).
- BufferAlgo
  - Moved image window methods from ImageAlgo (#1517).
- Format
  - Fixed space conversions for empty boxes (#1575).
- TestCase
  - Improved output for assertTypeNamesArePrefixed() failures.
- Dispatch
  - Renamed requirements -> preTasks
  - Added LoggingExecutableNode to GafferDispatchTest. This
    facilitates easier testing of dispatchers.
- SceneUI
  - Added ObjectVisualiser and AttributeVisualiser base classes
    to support custom representations of objects and attributes
    within the viewport (#1590).
- Metadata
  - Added methods for adding and querying non-node values (#1590).

Build
-----------------------------------------------------------------------

- Added CXXSTD argument to SConstruct. Pass CXXSTD=c++11 to build
  with C++11 support (#1586).
- Added testing with GCC 4.8 and C++11 to Travis test setup (#1586).
- Updated Cortex version to 9.5.0 (minimum requirement is 9.3.0).

Incompatibilities
-----------------------------------------------------------------------

- Removed "dispatcher.local.executeInForeground" plug - use the new
  "dispatcher.immediate" plug instead.
- Moved image window methods from ImageAlgo.h into BufferAlgo.h.
- Lights are now represented as attributes rather than as objects (#1590).
- The Parameters node no longer works for lights (#1590).

0.19.0.0
========

Apps
-----------------------------------------------------------------------

- Added a preference for OIIO cache memory to the gui app.

Core
-----------------------------------------------------------------------

- Added a TaskSwitch node.
- Added support for variable substitutions within SystemCommand.
- Added a PythonCommand node.
- Expression
	- Added support for assigning floats to IntPlugs in Python expressions.
	- Added detection of circular dependencies within expressions.
- Added support for metadata edits on Reference nodes (#1536).
- Fixed bug which caused internal connections to be removed when
  unparenting a Node.

UI
-----------------------------------------------------------------------

- Fixed SceneInspector context bug.
- Fixed display bug in Wedge string mode

Image
-----------------------------------------------------------------------

- Added Blur node.
- Added Text node.
- ImageReader
	- Added modes for handling missing frames.
	- Added settings for masking image sequences.
	- Added automatic conversion to linear using OIIO colorspace
	  metadata (#250).
	- Renamed old ImageReader to OpenImageIOReader - this is now
	  just a utility class which is used internally.
- Added ImagePrimitiveProcessor base class.
- Added methods for controlling the OIIO cache memory.
- Fixed bug which prevented the ImageWriter using the requested
  compression (#1538).
- Resample
	- Added expandDataWindow plug.
	- Added support for "smoothGaussian" filter.
	- Fixed bug which prevented subpixel translations.
- Fixed dirty propagation bugs in Offset node.
- Added Difference operation to Merge.
- ImageTransform
	- Improved performance up to 50%.
	- Improved quality.
	- Changed rotation direction to counter clockwise.
	- Made "cubic" the default filter./
- Removed Reformat node. Use Resize instead.
- Fixed computation of max in ImageStats.
- Fixed performance bug when ImageNodes are used inside
  a Box subclass implemented in Python.
- Fixed Merge dataWindow computation when the first input
  is unconnected.

Arnold
-----------------------------------------------------------------------

- Added ray depth setting to ArnoldOptions node.

Documentation
-----------------------------------------------------------------------

- Updated for latest changes.

API
-----------------------------------------------------------------------

- Added python bindings for ImageWriter::Mode.
- Expression::setExpression() preserves previous state in the case
  that parsing fails.
- Stopped CompoundNumericPlug::getChild() from masking the base class
  equivalents.
- Added ImageTestCase with assertImagesEqual() method.
- Removed filter from ImageSampler.
- Added Resample::filters() method.
- ImageTestCase
	- Fixed threshold comparison bug in assertImagesEqual().
	- Added assertImageHashesEqual() method.
- Added OpenColorIOTransform::availableSpaces() method
- Context::Scope may now be constructed with a NULL argument -
  this is a no-op.
- Reintroduced default format substitutions to AtomicFormatPlug.
- Added GafferImage::Shape base class.
- Removed ChannelMaskPlug::channelIndex() method. Use ImageAlgo
  colorIndex() method instead.
- Added channel name utility methods to ImageAlgo.

Build
-----------------------------------------------------------------------

- Improved reporting in Travis config.
- Updated several dependencies to match the VFX Reference Platform.
	- Boost 1.55
	- OpenEXR 2.2.0
	- OpenColorIO 1.0.9
- Updated to Appleseed 1.3.0-beta

Incompatibilities
-----------------------------------------------------------------------

- ImageTransform now uses OIIO filters rather than GafferImage filters -
  the old filter names are no longer supported.
- ImageTransform now rotates counter clockwise.
- Removed Reformat and redirected it to Resize, which supports OIIO filters
  rather than GafferImage filters.
- Removed filter plug from ImageSampler. Bilinear interpolation is used
  instead.
- Removed FilterPlug. Use StringPlug instead.
- Removed Filter. Use OIIO filters instead.
- Removed FilterPlugValueWidget. Use presets instead.
- Removed ChannelMaskPlug::channelIndex() method. Use ImageAlgo
  colorIndex() method instead.

0.18.0.0
========

This release brings a number of updates to GafferImage, including
user-editable Formats, bug fixes to Resize and Crop, and a new Offset
node. It also fixes a few bugs todo with Expressions, Switches, and UI
crashes.

Core
-----------------------------------------------------------------------

- `Node::userPlug()` is now a Plug instead of a CompoundPlug.
- Preventing unwanted child connection tracking on userPlug().
- Changed scriptNode() to return `this` when node is a ScriptNode.
- Support indirect connections to Switch index
    - Emitting Node::plugInputChangedSignal() for all downstream connections.
- Expressions don't let `__in` plug track child inputs.
- Added top level plug argument to `Expression::Engine::apply()`.
- PythonExpressionEngine drives `apply()` by plug type not data type.
- PythonExpressionEngine supports arbitrary compound plugs types.
- Improved PythonExpressionEngine::defaultExpression().
- Fixed a bug in plugs/nodesWithMetadata.
- Fixed errors when serialising parent metadata only.
- Reference/Box no longer export user plugs (#801).

UI
-----------------------------------------------------------------------

- Skipping intermediate dots in tooltips.
- Fixed crash in the GraphGadget when a non-nodule plug was removed from a node.
- Improved UI robustness for errors on enabledPlug() expressions.
- Fixed potential connection lifetime bugs in the Viewer.

Image
-----------------------------------------------------------------------

- Added AtomicFormatPlug and replaced all non-user facing FormatPlugs with this.
    - This plug does not perform default format substitutions.
    - This plug does not serialise registered Formats.
- Changed FormatPlug to be a user-editable Format specification
    - Using FormatPlug in all user facing scenarios (e.g. Constant, Resize, etc).
- Deprecated Reformat. Use Resize instead.
- Moved default Format mechanism onto FormatPlug.
- Fixed default Format issues inside boxes (#888).
- Fixed nodes which were unusable if no default format was specified in the context (#888).
    - We now fall back to a default default format in that case.
- The default format was not getting transferred to the script context after loading (#888).
- Rationalised and simplified the Format registry.
    - Fixed registerFormat() so that a second registration overrides the first.
    - Requiring name when registering a format.
    - Names should no longer include the numeric values.
    - Renamed removeFormat() to deregisterFormat().
    - Removed unused signals and not-so-useful methods.
    - Separated registered names and ostream output.
        - The ostream output just uses numeric values, keeping it in line with
          the Imath classes.
        - Querying the registered name for a format returns an
          empty string if it hasn't been registered. Previously it returned
          a generated name, making it hard to tell if it had actually been
          registered or not.
- FormatPlugValueWidget supports manual entry of custom formats.
    - This widget only supports FormatPlugs, not AtomicFormatPlugs.
- ImageStats now uses a postCreate to set plug values via the UI only.
- Renamed CropUI.postCreateCrop to CropUI.postCreate.
- Fixed Resize disabling.
- Add Offset node.
- Fixed bug in Crop::affects().
- Added Crop "resetOrigin" plug.
    - This resets the origin of the format back to [0,0], which is intuitively what is expected.

Incompatibilities
-----------------------------------------------------------------------

- Changed type of Node::userPlug()
- Moved default Format API from Format class onto FormatPlug class.
- Changed Format registry API.
- Crop now resets the display window origin to 0,0. Turn off the "resetOrigin" plug for the old behaviour.
- Renamed CropUI.postCreateCrop to CropUI.postCreate.

0.17.0.0
========

This release brings several major features in addition to the usual
enhancements and bug fixes. Of particular interest are the addition
of a basic keyframing system, support for using OSL expressions
alongside the existing Python expressions, and several new image
processing nodes exposing OpenColorIO functionality.

Core
-----------------------------------------------------------------------

- Added Animation node, providing basic support for keyframed animation.
- Added frames-per-second support to Contexts, to map between frames
  and a time in seconds.
- Expression
  - Fixed bug when identical expressions acted on different plug types.
  - Added support for calling `context.getTime()`.
  - Added support for calling `context.getFramesPerSecond()`.
  - Fixed bugs when a plug or node is renamed.
  - Fixed bugs when manually disconnecting an output or input
    of an expression.
  - Improved error reporting in the UI.
- Fixed InputGenerator backwards compatibility bug introduced in
  0.16.0.0.
- Box
  - Promoting a plug now properly copies plug metadata (#1468).
- Plug
  - Fixed rare crash during dirty propagation.
  - Fixed bug in child connection tracking behaviour.

UI
-----------------------------------------------------------------------

- NodeEditor
  - Plug context menus
    - Added keyframing menu items for numeric and bool plugs.
    - Added Lock/Unlock meu items.
    - Added menu item for creating an OSL expression.
  - Tool menu
    - Added "Revert to Defaults" menu item.
- NodeGraph
  - Added right click menu items for reordering plugs on Boxes.
  - Fixed bugs triggered by the dynamic hiding and showing of plugs
    via the UIEditor.
- Dot
  - Added optional labels. These can be derived from the
    dot node name or the upstream node name or may be
    specified directly.
- Shader loading dialogues
  - Added bookmarks.
- Viewer
  - Fixed bug which could mean the camera would move unexpectedly
    even when look-through mode is not enabled.
  - Fixed OpenColorIO configs.
- UIEditor
  - Fixed renaming of empty user sections.
  - Prevented renaming of section to invalid names like "".
  - Added default Settings section.
  - Fixed presets UI to update values when the selected preset
    changes.
  - Ignores user plugs on box nodes.
- Box
  - Added default Settings section.
  - Disabled plug addition button in User section.
- Fixed bug which could cause the display of corrupted icons.
- ShaderSwitch
  - Fixed UI to provide access to each input rather than just the
    array input as a whole (#1461).
- Numeric fields
  - Ensured that keyboard-nudged numbers have an extra 0 added as
    necessary to ensure that the same digit is always being modified.

Image
-----------------------------------------------------------------------

- New OpenColorIO nodes
  - LUT
  - CDL
  - DisplayTransform
- ImageWriter
  - Added file format options.
  - Made sure OIIO queries for nchannel and alpha support are
    respected.
- Merge
  - Fixed artifacts when the data windows differ between layers.
  - Fixed crash.
- Resize
  - Fixed artifacts when upsizing with the sinc filter (#1457).
- Changed convention for image bounding boxes to specify that the
  maximum coordinates are exclusive (outside the box).
- Fixed Crop UI for images with the default format.
- Resample
  - Fixed incorrect input sample region.

Scene
-----------------------------------------------------------------------

- Fixed loading of UnionFilters from Gaffer 0.15.0.0 (#1474).
- Fixed loading of FilterSwitches from Gaffer 0.15.0.0 (#1474).
- Attributes are now output to the renderer before shaders at the
  same location. This works around a bug in 3delight's shader
  construction.
- Fixed crash when loading sets from an empty SceneReader.
- Added support for frames-per-second to SceneReader, AlembicSource
  and SceneWriter.

OSL
-----------------------------------------------------------------------

- Added support for using OSL as a general purpose expression language.

Cortex
-----------------------------------------------------------------------

- Fixed issue where non-ValuePlugs were not syncing during setPlugValue().
- Fixed OpHolder node summaries.

API
-----------------------------------------------------------------------

- Expression
  - Redesigned API to better support multiple languages.
- Context
  - Added "framesPerSecond" variable and time accessors.
- Metadata
  - Added nodesWithMetadata() and plugsWithMetadata() methods.
- StandardNodeGadget
  - Removed orientation constructor parameter. Use metadata instead.
  - Added dynamic nodule reordering controlled by metadata.
- ScriptNode
  - Fixed undo merging for CompoundNumericPlugs (#422).
- Plug
  - Made setFlags() undoable.
- PlugLayout
  - Ignore custom widgets with type "". This allows a widget
    inherited from a base class to be removed by a derived class
    or instance metadata.
- Removed UserPlugValueWidget.
- Added UserPlug namespace.
- Deprecated use of arbitrary Widget constructor keyword arguments
  for auto-parenting. The `parenting` argument should be used instead.
- Image
  - Renamed GafferImage::OpenColorIO to ColorSpace.
  - Changed convention for image bounding boxes to specify that the
    maximum coordinates are exclusive (outside the box).
    - Added image window utility methods to assist with this change.
  - Added OpenColorIOTransform abstract base class. This makes it
    easy to implement nodes whose processing is performed via OpenColorIO.
  - Sampler
    - Remove sample window accessors.
    - Deprecated constructor taking a filter.
- Added NumericWidget.valueToString() method.

Incompatibilities
-----------------------------------------------------------------------

- Redesigned expression API to better support multiple languages.
- Changed convention for image bounding boxes to specify that the
  maximum coordinates are exclusive (outside the box).
- NodeGadget
  - Added noduleAddedSignal() and noduleRemovedSignal().
- StandardNodeGadget
  - Removed orientation constructor parameter. Use metadata instead.
- GraphComponentWrapper
  - Improved constructors to allow any type to be passed to the single
    argument constructor.
- Removed UserPlugValueWidget.
- Deprecated use of arbitrary Widget constructor keyword arguments
  for auto-parenting. The `parenting` argument should be used instead.
- Renamed GafferImage::OpenColorIO to ColorSpace.
- Sampler
  - Remove sample window accessors.
  - Deprecated constructor taking a filter.

0.16.0.4
========

Scene
-----------------------------------------------------------------------
- Output attributes to the renderer before other state to fix some inconsistent behaviour

Build
-----------------------------------------------------------------------
- Updated IE internal build options

0.16.0.3
========

UI
-----------------------------------------------------------------------

- fixed a problem whereby presets were not being transferred when
  promoting a compound plug on a RenderManAttributes node.

Core
-----------------------------------------------------------------------

- Fixed issue where non-ValuePlugs were not syncing during
  setPlugValue().

0.16.0.2
========

UI
-----------------------------------------------------------------------

- Box : Copy all metadata when promoting plugs.
- UIEditor : Never edit user plug for Box nodes.

0.16.0.1
========

UI
-----------------------------------------------------------------------

- UIEditor : Update preset value on selection change.
- ShaderSwitchUI : Fix NodeGraph representation (#1461).

0.16.0.0
========

Apps
-----------------------------------------------------------------------

- Python
  - Sets __name__ to "__main__" to conform more closely to a standard
    python interpreter (#1405).
  - Fixed to accepts -flag arguments (#1406).
- GUI
  - Removed cortex nodes from the node menu. They can be reintroduced
    with an appropriate config file, but our intention is that Cortex
    play only a "behind the scenes" role in Gaffer in the future.

Core
-----------------------------------------------------------------------

- Added version metadata to all saved files (#1436).
- Fixed dispatching of nodes inside References.
- Python expressions can now write to AtomicBoxPlugs.
- Added support for promoting ArrayPlugs to boxes.

UI
-----------------------------------------------------------------------

- Fixed image format menu to make changes undoable.
- Added sequence browsing to the relevant file choosers.
- Hid TaskContextVariables.variables plug in the NodeGraph.
- Fixed editability of promoted CompoundDataPlugs.
- Box promotion now tranfers nodule and connection colours.

Image
-----------------------------------------------------------------------

- Added a Resize node. This will replace the Reformat node over time.
- Added a Crop node.
- Added a Shuffle node (#1380).
- Added Premultiply and Unpremultiply nodes.
- ImageWriter
    - Fixed writing to image formats which don't support separate
      display and data windows - the full display window is now written,
      padded with black as necessary.
    - Added progress message.
    - Fixed tiled writing (previously scanlines were always written).

Scene
-----------------------------------------------------------------------

- Fixed bug in Isolate which meant that a filter which matched nothing
  at all had no effect. It now removes the entire scene as expected.
- Fixed bug in Prune which meant that a filter which matched the root
  was not removing the entire scene.
- Added support for arbitrary IECore::PreWorldRenderables in global
  options.
- Improved performance of bounds propagation (around 7% improvement
  for a Transform node and a complex filter).

Cortex
-----------------------------------------------------------------------

- Fixed bug which caused errors with read-only parameter plugs.

API
-----------------------------------------------------------------------

- Replaced all InputGenerators with ArrayPlugs, and removed InputGenerator
  class. ImageProcessor and SceneProcessor may now provide an array of
  inputs for any derived class to use.
- Paths
  - Added sequence support to FileSystemPath.
  - Added FileSequencePathFilter class for filtering sequences from
    FileSystemPath.
  - FileSequencePathPlugValueWidget supports metadata for sequence
    display.
  - Deprecated SequencePath.
- Added Resample node to GafferImage, for use in node internals.
- Dispatcher
  - The current job directory is added to the context for use
    by Executable nodes.
- Sampler
  - Fixed binding of sample( int, int )
- Added AtomicBox2fPlug.
- Made SceneNode and SceneProcessor subclassable in Python.
- Made ImageNode and ImageProcessor subclassable in Python.
- Made SubGraph subclassable in Python.
- Added _copy argument to ImagePlug.channelData() method.
- CompoundPlug deprecation
  - Rederived the following plugs from ValuePlug or Plug in preparation
    for removal of CompoundPlug :
      - BoxPlug
      - CompoundNumericPlug
      - Transform2DPlug
      - TransformPlug
      - CompoundDataPlug
      - ArrayPlug
  - Replaced use of CompoundPlug in the following nodes
    - Light
    - Outputs
- Added support for extra constructor arguments in node wrappers.

Incompatibilities
-----------------------------------------------------------------------

The scene and image processing nodes have been overhauled to allow any
node to use an array of inputs. While full backwards compatibility with
old scenes is expected, please let us know if you have any problems
loading an old scene. Please also update any dependent code to the new
APIs as soon as possible.

- Removed InputGenerator. Use ArrayPlug instead.
- Removed FilterMixinBase. Use FilterProcessor instead.
- SwitchComputeNode and SwitchDependencyNode now require that the "in"
  plug is an ArrayPlug.
- Changed base classes for many plugs, breaking binary compatibility
  but in most cases not source compatibility.


Build
-----------------------------------------------------------------------

- Added checks for doxygen and inkscape prior to building.
- Fixed non-reporting of graphics build errors (#1395).
- Updated to faster container-based testing on Travis.
- Added appleseed unit tests to Travis setup.

0.15.0.0
========

UI
-----------------------------------------------------------------------

- UI Editor
  - Added dropdown menu for choosing widget type (#739).
  - Added section for specifying additional widget settings (#739).
  - Added preset editor (#739).
  - Added section for editing section summaries.
  - Added NodeGraph section.
- Added drag and drop of objects onto Set nodes in the NodeGraph.
- Fixed crash which could occur when opening recent files.
- Fixed crash which could occur when using OpenGL widgets within Maya.
- Added support for summary tooltips on node UI tabs (#332).
- Fixed bugs which could cause a blank NodeEditor if an expression
  referenced a script variable.
- Fixed bugs in channel mask menus on image processing nodes.

Core
-----------------------------------------------------------------------

- Added Wedge node. This allows tasks to be dispatched multiple times
  using a range of values (#1372).
- Added TaskContextVariables node. This allows variables to be defined
  within the tree of tasks (renders etc) executed by a dispatcher.
- Added Loop node. This takes an input and loops it N times through an
  external graph before outputting it again. This provides the user with
  the ability to do things with the graph which were previously only
  achievable with code.
- Reference
  - Fixed serialisation of empty reference.
  - Fixed serialisation of user plug metadata.
  - Fixed referencing of promoted plugs
    - ExecutableNode requirements plug
    - UnionFilter filter inputs
    - OSLImage and OSLObject shader plugs.
    - RenderManShader coshader plugs (#1358).
- Expression
  - Fixed support for setting GafferImage FormatPlugs.
- ContextVariables
  - Fixed serialisation bug where additional plugs were added on
    save/load and copy/paste.
- Improved Context and ValuePlug performance.

Image
-----------------------------------------------------------------------

- Added ImageLoop node.
- Performance
  - Improved Reformat performance.
  - Improved threading peformance for small images.
- ImageWriter
  - Improved error messages.
  - Fixed bugs with empty filenames and filenames using
    substitutions.
- ImageTransform
  - Fixed copy/paste.
  - Fixed dirty propagation bug which could prevent the viewer
    updating at the right time.
- ImageReader
  - Added error reporting for missing files.

Scene
-----------------------------------------------------------------------

- Added SceneLoop node.
- Transform
  - Fixed bugs in World mode.
  - Added Parent, Local Reset and World Reset modes.
  - Renamed Object space to Local.
  - Changed default space to Local.
  - Note that these are backwards incompatible changes, necessary to
    fix an important bug and get the Transform node on a solid footing
    for the future. To get the same results as the old World mode, use
    the new Parent mode.
- FreezeTransform
  - Fixed bug which prevented the UI updating when the input object
    was changed.
- Fixed bugs which could cause incorrect bounds to be computed.

Appleseed
-----------------------------------------------------------------------

- Removed options and attributes that are not useful in Gaffer.
- Fixed default values for some options and attributes.
- Documented all nodes.
- Added support for shading overrides.

API
-----------------------------------------------------------------------

- Pass-through connections may now be made for FormatPlug (#1250).
- Added TaskContextProcessor base class. This enables the development
  of ExecutableNodes which request their input requirements in different
  contexts.
- Added support for directly setting Color3f context values from Python.
- UI Metadata additions. Many additions were made to the metadata supported
  by the Node UIs, and the existing UIs were ported to make use of it.
  - "layout:visibilityActivator"
  - "plugValueWidget:type"
  - "compoundDataPlugValueWidget:editable"
  - "boolPlugValueWidget:displayMode"
  - "vectorDataPlugValueWidget:dragPointer"
  - "pathPlugValueWidget:leaf"
  - "pathPlugValueWidget:valid"
  - "pathPlugValueWidget:bookmarks"
  - "fileSystemPathPlugValueWidget:extensions"
  - "fileSystemPathPlugValueWidget:extensionsLabel"
- ScriptProcedural
  - Added context parameter.
- BoolWidget
  - Added setDisplayMode()/getDisplayMode() accessors.
- Added AcceptsDependencyCycles Plug flag. See the Loop node for an
  example of use.
- Added FileSystemPathPlugValueWidget.
- Metadata
  - Fixed inconsistent handling of NULL values.
  - Added methods for deregistering values.
- Removed GafferUI.SectionedCompoundPlugValueWidget.
- Activator expressions are now attached to the parent of the plug, rather than always being on the node.
- Removed StringPlugValueWidget continuousUpdate constructor argument. Use metadata instead.
- Removed MultiLineStringPlugValueWidget continuousUpdate constructor argument. Use metadata instead.
- SceneNode
  - Added childNames argument to bounds union methods.
- SceneAlgo
  - Added `bound( const IECore::Object * )` function.

Build
-----------------------------------------------------------------------

- Updated to Cortex 9.0.0.
- Updated to OIIO 1.5.17.
- Updated to OSL 1.6.8.
- Updated to 1.2.0-beta.

Incompatibilies
-----------------------------------------------------------------------

- Removed `Reference::fileNamePlug()` (#801). Use `Reference::fileName()`
  instead. Use `continueOnError = True` when loading old scripts.
- Removed arguments from CompoundDataPlugValueWidget constructor. Use
  Metadata instead.
- Removed SectionedCompoundDataPlugVlueWidget. Use LayoutPlugValueWidget
  and metadata instead.
- Changed base class for ImagePlug.
- Changed base class for ScenePlug.
- Changed base class for SplinePlug.
- Removed ImageMixinBase. Use ImageProcessor instead.
- Removed SceneMixinBase. Use SceneProcessor instead.
- Removed GafferUI.SectionedCompoundPlugValueWidget. Use LayoutPlugValueWidget instead.
- Activator expressions are now attached to the parent of the plug, rather than always being on the node.
- Changed ChannelMaskPlugValueWidget constructor arguments.
- Changed Transform behaviour to fix bug in world space mode, add new modes and change the default mode to local. If you need the old world space behaviour, use the new parent space mode.

0.14.0.0
========

UI
-----------------------------------------------------------------------

- NodeGraph
  - Improved "Select Affected Objects" menu item. This is now available
    on filters as well as on scene processors.
  - Added support for dragging objects from the Viewer and SceneHierarchy
    and dropping them onto scene processors and PathFilters, to specify
    the affected objects.
      - Dragging onto a node replaces the current paths.
      - Shift+Drag adds to the current paths.
      - Control+Drag removes from the current paths.
  - Added plug context menu for moving promoted plugs on Boxes.
- NodeEditor
  - Added "Select Affected Objects" menu item in the tool menu for
    filters and scene processors.
- UIEditor
  - Added + button for adding plugs, and - button for deleting them.
  - Added the ability to create nested sections and drag+drop plugs
    between them.
- Viewer
  - Fixed grid and gnomon menus.

Core
-----------------------------------------------------------------------

- Expression
  - Added support for setting multiple plugs from one
    expression (#1315).
  - Added support for vector, color and box outputs (#1315).
  - Added support for assigning to plugs within conditional
    branches (#1349).

Scene
-----------------------------------------------------------------------

- Improved ParentConstraint so it is acts more like the equivalent
  parenting operation, and maintains the local transforms of the
  objects being constrained. Note that this is a change of behaviour,
  but one that we feel is much for the better.
- Fixed ShaderAssignment to allow referencing of promoted shader input
  plugs.

API
-----------------------------------------------------------------------

- Added `parallelTraverse()` and `filteredParallelTraverse()` methods
  to SceneAlgo. These make it trivial to traverse all locations in a
  scene using multiple threads.
- Added inputTransform argument to `Constraint::computeConstraint()`.
- Removed TransformPlugValueWidget.
- Used Plug rather than CompoundPlug in several places. CompoundPlug
  is being phased out because the Plug base class is now perfectly
  capable of having child plugs.
    - `ExecutableNode::dispatcherPlug()`
    - LocalDispatcher dispatcher plug
    - `Shader::parametersPlug()`
- Fixed support for boost python object methods as menu commands.
- Pointer
  - Fixed `registerPointer()` method.
  - Added binding for `registerPointer()`.
- Added `scoped` argument to `Signal.connect()` python bindings.
- Added `SignalClass` for binding signals, and deprecated the old
  `SignalBinder`.
- Added support for binding signals with 4 arguments.
- Added `LazyMethod.flush()` method.
- Fixed update bug in `PathListingWidget.setSelectedPaths()`.
- Added support for "nodule:type" metadata to control the type
  of nodule created for a plug. This should be used in preference
  to `Nodule::registerNodule()`, which has been deprecated.
- Added support for modifying CompoundNodule orientation, spacing
  and direction using plug metadata.
- Improved signalling of instance metadata changes.
- Added default arguments for ValuePlug constructor arguments.

 Incompatibilities
-----------------------------------------------------------------------

- Changed Constraint::computeConstraint() function signature.
- Changed ParentConstraint behaviour to include the local transform of the constrained object.
- Removed TransformPlugValueWidget.
- Changed plug type returned by ExecutableNode::dispatcherPlug().
- Changed Dispatcher::SetupPlugsFn signature.
- Changed ExecutableNode::dispatcherPlug() signature.
- Changed Shader::parametersPlug() to Plug rather than CompoundPlug.
- Removed asUserPlug arguments from Box promotion methods. Plugs are
  now always promoted directly under a box, and never as user plugs.
- Changed signature of `Nodule::registerNodule()` when registering a subclass.
- Changed signature of CompoundNodule constructor, which now accepts a Plug
  rather than CompoundPlug.
- Replaced UIEditor setSelectedPlug()/getSelectedPlug() methods with
  setSelection()/getSelection().
- Added arguments to Metadata signals.

0.13.1.0
========

Apps
-----------------------------------------------------------------------

- Test app can now run multiple named test cases, specified via the
  "testCases" command line argument.
- Fixed errors caused by special characters in .gfr filenames.

UI
-----------------------------------------------------------------------

- Fixed unwanted viewport scrolling when dragging from one NodeGraph
  into another, or from the NodeEditor across a NodeGraph (#1321).
- Hid Viewer diagnostic modes for unavailable renderers.
- Fixed SceneInspector inheritance and history windows, which were broken
  in 0.13.0.0.
- Fixed ObjectWriter UI, which was broken in 0.13.0.0.

OSL
-----------------------------------------------------------------------

- Added utility shaders for float maths and noise.

Image
-----------------------------------------------------------------------

- Fixed bug in DeleteChannels::hashChannelNames().

Houdini
-----------------------------------------------------------------------

- Added support for Houdini 14 (requires Cortex 9.0.0-b7).

API
-----------------------------------------------------------------------

- Added GafferUI._qtObject method.
- PlugLayout
  - Added layoutSections() method.
  - Added section argument to layoutOrder() method.

Build
-----------------------------------------------------------------------

- Added support for Boost >= 1.54.
- Fixed Appleseed packaging. We were omitting the directory containing
  the Cortex display driver.

0.13.0.0
========

Apps
-----------------------------------------------------------------------

- Improved error message for execute app.

Core
-----------------------------------------------------------------------

- Improved Dispatcher
  - Stopped merging of identical tasks from different nodes.
    We decided that this auto-merging caused more confusion than it
    was worth, and it may actually have prevented useful executable
    graphs which would have been intentionally running identical
    tasks at different points in the graph.
  - Added cycle detection.

UI
-----------------------------------------------------------------------

- Avoided unnecessary rebuilds of MenuBar menus. This can improve
  performance for slow-to-build custom menus.
- Added font file browser to the Text node.
- Improved NodeGraph plug tooltips - they now contain the plug description.
- Plugs may now be promoted to Box level via the right click plug
  menu in the NodeGraph.
- Fixed search box in file open dialogues.
- Improved dialogues for picking scene paths
  - Opened in tree mode rather than list mode
  - Removed unnecessary columns
  - Added filtering to display only cameras where appropriate
- CustomAttributes/DeleteAttributes
  - Added right click menu for quickly adding attributes from the
    currently selected object.
- Viewer
  - Added shading mode menu. This allows the default shading to be overridden
    with another shader. Currently configured menu entries allow visualisation
    of shader assignments and visibility for RenderMan, Arnold and Appleseed
    (#1037).
  - Improved error handling.
- SceneInspector
  - Improved shader display in attributes section. The node colour of the
    assigned shader is used as the background colour.
  - Improved performance (#1050).
- Node UIs
  - Added tool menu to NodeEditor
  - Added support for metadata-driven activators.
  - Added support for metadata-driven section summaries.
  - Added support for metadata-driven custom widgets.

Scene
-----------------------------------------------------------------------

- InteractiveRender
  - Fixed crash when deleting a running InteractiveRender.
  - Fixed coordinate system update problem.
- Fixed bug preventing filter plugs from being promoted to Boxes.
- Improved set computation
  - Separated the computation of sets from the computation of globals.
    This should prevent delays caused when calculating large unneeded
    sets along with the globals.
  - Made sets compute individually on demand. This should reduce the
    overhead of large unneeded sets.
  - Added "sets" plug to source nodes, to allow set membership to
    be defined at creation time.
  - Optimised SetFilter hashing.
  - Prevented wildcards from being used in the Set node (#1307).
- Made Parameters node compatible with subclasses of Light/Camera/ExternalProcedural,
  such as those used internally at IE.
- Shader node now adds "gaffer:nodeColor" entry into the blind data
  for the shader in the scene - this allows UI components to display
  the colour as appropriate.
- Added AttributeVisualiser node. This applies an OpenGL shader to
  visualise the values of attributes and shader assignments.

Appleseed
-----------------------------------------------------------------------

- Fixed typo in AppleseedOptions plug names.

Documentation
-----------------------------------------------------------------------

- Improved doxyen documentation configuration.
- Documented all GafferScene nodes.
- Documented all GafferOSL nodes.
- Documented all GafferRenderMan nodes.
- Documented all GafferArnold nodes.
- Added support for Arnold "desc" metadata items.

API
-----------------------------------------------------------------------

- Refactored Node UI to provide all features via the PlugLayout and
  Metadata entries.
  - Added support for a "fixedLineHeight" metadata entry in
    MultiLineStringPlugValueWidget.
  - Added support for "layout:section" metadata - this allows the
    layout to be split into sections, and will provide the basis for
    replacing the Sectioned* widgets, adding support for sections in
    the UIEditor, and replacing the section management code in the
    StandardNodeUI.
  - Added support for Metadata activators - these allow the editability
    of a plug to be driven by the values of other plugs.
  - Added support for section summaries driven by Metadata.
  - Deprecated SectionedCompoundDataPlugValueWidget.
  - Deprecated SectionedCompoundPlugValueWidget.
  - Improved layoutOrder() API. It now returns the ordered plugs
    for a specific parent, rather than accepting a possibly unrelated
    list of plugs.
  - Added support for arbitrary custom widgets to be inserted into
    layouts.
  - Reimplemented StandardNodeUI using PlugLayout.
- Fixed ExecutableNode::requirements() binding.
- Added support for fixing the height (measured in number of lines)
  of the MultiLineTextWidget.
- Fixed support for functools.partial( classMethod ) commands in
  Menus.
- ScenePath : added setScene()/getScene() accessors.
- Added SceneFilterPathFilter class. This tongue twister uses any of
  the GafferScene::Filter nodes to implement a Gaffer::PathFilter to
  filter the children of a GafferScene::ScenePath.
- Added ScenePath::createStandardFilter() method.
- Fixed crash when a Path is deleted before its PathFilter.
- Added PathChooserDialogue.pathChooserWidget() method.
- Added ScenePathPlugValueWidget.
- Gave precedence to exact plug matches over wildcard matches in Metadata
  queries.
- Added addition controls over Context substitution methods.
- Improved StringPlug with additional control over substitutions.
- Improved PlugType to support box and bool plugs.
- Added ValuePlugSerialiser::repr() method. This is intended to allow
  derived class bindings to base their own `repr()` implementation on
  the ValuePlug one.
- Made TypedObjectPlug compatible with instantiation for new types
  outside of Gaffer. This is achieved by moving the implementation into a
  .inl file which may be included as necessary. Added TypedObjectPlugClass
  to simplify binding such instantiations.
- Implemented PathMatcherData::hash().
- Added GafferScene::PathMatcherDataPlug.
- Reimplemented SceneNode sets API.
- Added GafferUI.LazyMethod for deferring widget method calls until
  visible/idle.

 Incompatibilities
-----------------------------------------------------------------------

- StringPlug
  - Reimplemented as a standalone class
  - TypedPlug<string> is no longer instantiated (binary incompatibility).
  - Must now include "Gaffer/StringPlug.h" rather than "Gaffer/TypedPlug.h"
    (source incompatibility).
- GafferCortex
  - Removed BoxParameterHandler and CompoundNumericParameterHandler. Their
    functionality is now covered by TypedParameterHandler.
- GafferScene
  - Reimplemented sets API.
  - Removed SceneReader "sets" plug.
- GafferAppleseed
  - Fixed typo in AppleseedOptions plug names.
- PlugLayout
  - Changed layoutOrder() signature.
- StandardNodeUI
  - Removed DisplayMode enum.
  - Removed displayMode constructor argument.
  - Removed _header() method.
  - Removed _tabbedContainer() method.

Build
-----------------------------------------------------------------------

- Updated default dependency versions
  - OIIO 1.5.13
  - OSL 1.6.3dev
  - LLVM 3.4
  - Alembic 1.5.8
  - Cortex 9.0.0-b6
- Added bundled Appleseed renderer

0.12.1.0
========

Core
-----------------------------------------------------------------------

- Fixed hangs introduced in 0.12.0.0. These were seen when stopping
  Appleseed renders and when ganging plugs in Caribou.
- Fixed thread-related crashes introduced in 0.12.0.0. These have not
  been observed in the wild, but caused intermittent failures in the
  unit tests.

UI
-----------------------------------------------------------------------

- Improved error messages output by OpDialogue.
- Fixed unwanted auto-expansion in SceneHierarchy panel.

Scene
-----------------------------------------------------------------------

- Added current scene location to error messages emitted by SceneProcedural.
- Reduced memory usage for sets by 10%.
- Optimised set computations. This reduces globals computation time for
  a complex production scene by 60%.
- Fixed PathFilter wildcard matching bug.

OSL
-----------------------------------------------------------------------

- Added metadata presets support for color and point parameters.

API
-----------------------------------------------------------------------

- Added iterators to GafferScene::PathMatcher.
- Added GafferUI.EditMenu.selectionAvailable() method.

0.12.0.0
========

Core
-----------------------------------------------------------------------

- Optimised CompoundDataPlug::hash() to ignore disabled members. This
  reduces globals hashing time by 20% for a complex production scene.
- Fixes Expression serialisation bugs (#1081, #1243).
- Optimised ValuePlug hash caching. It now caches more aggressively,
  keeping cache entries alive across multiple computations. This reduces
  scene traversal time for a complex production scene by 70%.
- Improved dirty propagation mechanism.
  - Batched propagation for UndoContexts, so dirtiness is signalled
    only once for operations batched within a single undo action.
  - Fixed bugs which meant dirtiness was signalled when child/parent
    plug connections were in an inconsistent state.
  - Addition and removal of dynamic plugs now triggers dirty
    propagation.
- The values of environment variables used for string plug
  substitutions are now frozen at startup.

UI
-----------------------------------------------------------------------

- Improved indicator for non-default plug values (#1216).
- Added copy/paste entries to plug menus (#601).
- SceneInspector now shows parameters for ExternalProcedural and
  Light objects.
- Added available set names to Set node "sets" plug popup menu.

Scene
-----------------------------------------------------------------------

- Fixed PathMatcher wildcard matching bug (#1252).
- Added Parameters node. This can be used for tweaking the parameters
  of lights, cameras and external procedurals (#1259).
- Added PointsType node (#476).
- Fixes Seeds node to take into account the bounding box of the generated
  points.
- Fixed dirty propagation bugs in CoordinateSystem and ClippingPlane
  nodes.
- Improved InteractiveRenderer pausing during edits.
- Added DeleteSets node.
- Fixed CustomOptions dirty propagation (#1039).
- Fixed ContextVariables dirty propagation.
- Optimised Filter mechanism, giving a 7-20% improvement in performance
  across a range of production scenes.

Appleseed
-----------------------------------------------------------------------

- Added support for interactive renderering with shader and light
  edits.

Image
-----------------------------------------------------------------------

- Added support for image metadata
  - ImagePlug has a new metadata child plug.
  - ImageReader reads metadata from file.
  - ImageWriter writes metadata to file.
  - ImagePrimitiveSource loads metadata from `ImagePrimitive::blindData()`.
  - Merge copies metadata from the first input.
  - ImageMetadata node creates/sets metadata.
  - DeleteImageMetadata node removed metadata.
  - CopyImageMetadata transfers metadata from one image to another.
- Optimised many nodes with direct internal pass-though connections.

API
-----------------------------------------------------------------------

- StringAlgo
  - Added `hasWildcards()` function.
  - Removed flawed MatchPatternLess (#1252).
- NodeAlgo
  - Added `isSetToUserDefault( plug )` function.
- RendererAlgo
  - Added `outputAttributes()` method.
- ImageNode
  - `hash*()` and `compute*()` methods are no longer pure virtual.
    This allows subclasses to make direct internal connections to
    pass through input plugs unchanged.
- PlugValueWidget
  - Replaced `_dropValue()` method with `_convertValue()`.
- Menu
  - Added support for `functools.partial( WeakMethod )`
    in menu commands.
- Simplified and improved Merge node implementation.
- Added MetadataProcessor base class to GafferImage.
- Added Plug::dirty() virtual method. This is used to inform a Plug
  that it has been dirtied by Plug::propagateDirtiness().
- Fixed DependencyNodeWrapper to translate python exceptions to C++.

Build
-----------------------------------------------------------------------

- Fixed compilation without NDEBUG=1 with gcc 4.1.2.

 Incompatibilities
-----------------------------------------------------------------------

- Removed MatchPatternLess from StringAlgo.h.
- Replaced PlugValueWidget `_dropValue()` method with `_convertValue()`.
- Removed GafferImage::FilterProcessor.
- Added/removed virtual overrides in GafferImage.
- Added virtual function to Plug.

0.11.0.0
========

Image
-----------------------------------------------------------------------

- Image nodes are now documented
- RemoveChannels renamed to DeleteChannels

Scene
-----------------------------------------------------------------------

- Fixed a bug in the InteractiveRender that was causing a crash when the scene child names changed.

0.10.1.0
========

UI
-----------------------------------------------------------------------

- Fixed FilterPlugValueWidget filter menu

Scene
-----------------------------------------------------------------------

- Fixed dirty propagation for globals in the camera node
- IPR now blocks the UI while it's starting up, and is more selective
  about sending scene edits.

Core
-----------------------------------------------------------------------

- Fixed dirty propagation bug in expressions

0.10.0.0
========

Core
-----------------------------------------------------------------------

- Reimplemented paths framework in C++ (#1190). This gives much
  improved performance - 10x or more speed improvements in the
  SceneHierarchy panel.
- Fixed subprocess hangs seen when dispatching renders inside Maya.
- Restored compatibility with references from prior to version 0.8.0.0.

UI
-----------------------------------------------------------------------

- Added bookmarks system for NodeGraph (#849).
  - Bookmark nodes using the right-click node context menu
  - Connect plugs to bookmarked nodes using the right-click plug
    context menu.
- Added NodeGraph Ctrl+Click to select all downstream nodes (#941).
- Added additional "Edit/Select Connected" menu items
- Fixed "Edit/SelectConnected" menu items to ignore invisible nodes.
- Fixed "Edit/SelectAll" menu item to ignore invisible nodes (#1207).
- Highlighted plugs at non-default values in the NodeEditor (#1216).
- SceneInspector
  - Significant performance improvements.
  - Added name based filtering for options and attributes (#1159).
  - Added query caching.
- Fixed bug whereby Widget.setVisible( notABool ) could cause problems.
- Fixed clearing of StandardNodeGadget errors for non-DependencyNodes.

Scene
-----------------------------------------------------------------------

- Added "mode" plug to Set node. This allows paths to be added to or
  removed from existing sets, in addition to the old behaviour of
  creating a new set (or replacing an existing one of the same name).
- Added ClippingPlane node.
- Added "enabled" plug to Filter nodes (#1196).
- Added FilterSwitch node (#1197).
- Added "name" plug to Duplicate node, to provide control over the
  names given to the duplicates (#1200).

Appleseed
-----------------------------------------------------------------------

- Added photon target attribute.
- Added sampler option.
- Synced default options with new Appleseed defaults.

Cortex
-----------------------------------------------------------------------

- Added UI hint to control the visibility of the header in the
  ParameterisedHolder node UI.

API
-----------------------------------------------------------------------

- GraphGadget
  - Added degreesOfSeparation argument to upstreamNodeGadgets() method.
  - Added downstreamNodeGadgets() and connectedNodeGadgets() methods.
- EditMenu
  - Added scope() method. This should be used by custom edit menu
    commands to ensure they operate on the right portion of the
    node graph.
- CompoundVectorParameterValueWidget
  - Added support for "showIndices" parameter user data.
- PathMatcher
  - Added addPaths() and removePaths() methods, each taking a second
    PathMatcher to provide the paths.
- Serialisation
  - Made classPath() and modulePath() methods compatible with passing
    a class as well as an instance.
- PathListingWidget
  - Added setSortable() and getSortable() methods.
- Added MatchPatternPathFilter
- Added bindings for SceneAlgo camera() and shutter() functions.
- Metadata
  - Added control over persistence of instance values.
- Added preprocessor macros for gaffer version numbers.

Incompatibilities
-----------------------------------------------------------------------

- Path
  - The info API has been replaced with a property API. Emulation
    for the old API exists, but it has been deprecated.
  - Properties must derive from RunTimeTyped, whereas info could
    contain any python type.
  - Subclasses now _must_ implement the copy() method.
- PathListingWidget
  - Column python class has been replaced with several specialised
    C++ subclasses. It is no longer possible to derive from Column
    in python.
- GraphGadget
  - Added argument to upstreamNodeGadgets() method.
- GafferScene::Filter
  - Renamed "match" plug to "out". Backwards compatibility is
    provided by a __getattr__ alias in Python.

Build
-----------------------------------------------------------------------

- Updated public build to use Cortex 9.0.0-b4.
- libGafferUI now links with Qt. This must be considered when building
  Gaffer to be hosted inside other applications.
- Requires subprocess32 python module.
- Added subprocess32 to dependencies build process.

0.9.0.0
=======

This is primarily a bugfix release.

Core
-----------------------------------------------------------------------

- Documented all nodes and plugs.
- Improved Reference workflow
  - Boxes exported for referencing contain new default values for all
    promoted plugs to match their current values on the Box.
  - When reloading a reference, only values the user has changed from
    their defaults will be kept. Other values will be updated from the
    new reference.
  - Box metadata is included when exporting for referencing. This
    means that colours and descriptions set via the UIEditor will
    be transferred onto any Reference nodes which load the exported
    reference (#1171).
- Added "-threads" command line argument to Gaffer.Application
- Fixed "gaffer execute" error handling

Cortex
-----------------------------------------------------------------------

- Documented all nodes and plugs.

Scene
-----------------------------------------------------------------------

- Added hack for controlling TBB concurrency from SceneProcedural
  - Using the GAFFERSCENE_SCENEPROCEDURAL_THREADS environment variable

RenderMan
-----------------------------------------------------------------------

- Fixed hangs caused by deleting or reconnecting a paused
  InteractiveRenderManRender node.

Appleseed
-----------------------------------------------------------------------

- Fixed render threads and texture memory options.

Image
-----------------------------------------------------------------------

- Fixed bug which prevented serialisation of read only FormatPlugs.

UI
-----------------------------------------------------------------------

- Fixed creation of expressions for BoolPlugs.
- Fixed context used by scene view camera chooser.

API
-----------------------------------------------------------------------

- Added Metadata::registerNode() method. This allows all the metadata
  for a node and its plugs to be registered with a single function call
  (#1160).
- Added GafferTest.TestCase.assertNodesAreDocumented().
- Serialisation
  - Added serialisation argument to `Serialiser::constructor()`.
  - Added Serialisation::parent() accessor.
- ValuePlug
  - Simplified handling of default values.
  - Added isSetToDefault() method.
- Made CompoundDataPlug::addMember() set default value for name plug
  (#935).
- Added Python bindings for tbb::task_scheduler_init

Incompatibilities
-----------------------------------------------------------------------

- Added argument to virtual method `Serialiser::constructor()`.
- Changed layout of ValuePlug classes.
- Removed virtual overrides from some ValuePlug classes.
- Added virtual method to ValuePlug.

Build
-----------------------------------------------------------------------

- Updated public build to use Cortex 9.0.0-b3.
- Included Shiboken module in release packages.

0.8.2.0
=======

Core
-----------------------------------------------------------------------

- Prevented errors in Metadata slots from stopping other slots running.

Scene
-----------------------------------------------------------------------

- Fixed BranchCreator dirty propagation.

RenderMan
-----------------------------------------------------------------------

- Add trace bias in RenderManAttributes.

Image
-----------------------------------------------------------------------

- Stopped display transforms hardcoding OCIO "linear" colour space.
- Fixed dirty propagation for Merge node.

UI
-----------------------------------------------------------------------

- Fixed evaluation time of look-through cameras in the Viewer.
- Added camera name to resolution gate overlay.
- Removed redundant render requests from CompoundNodule.
- Simplified Gadget render requests when children are added/removed
- Prevented duplicate errors on StandardNodeGadget tooltips.
- Fixed CompoundEditor lifetime bug
- Setting DispatcherUI frameRange widget text in PlaybackRange mode.
- Made NameWidget replace " " with "_" automatically.

API
-----------------------------------------------------------------------

- Removed GafferBindings::CatchingSlotCaller.
- Added Gaffer::CatchingSignalCombiner class.
- Added Gadget::requestRender() method.

Build
-----------------------------------------------------------------------

- Fixed GafferRenderMan public build.

0.8.1.0
=======

Core
-----------------------------------------------------------------------

- Fixed ComputeNodeWrapper exception handling.

UI
-----------------------------------------------------------------------

- Fixed GafferUI crashes seen at Python shutdown.
- Added support for hiding some fields of CompoundNumericPlugValueWidgets.
- Update DispatcherUI; can dispatch box with promoted requirement.
- Fixed crashes when deleting a node immediately after it errored.

Scene
-----------------------------------------------------------------------

- Fixed light visibility bug.
- Fixed coordinate system visibility bug.
- Added visible() function to SceneAlgo.h.
- Added GL FacingRatio shader

RenderMan
-----------------------------------------------------------------------

- Added "vector2" widget annotation support for RenderMan shaders.

Build
-----------------------------------------------------------------------

- Stopped installing the python module by default
- Moved installDir to /tmp for local IE builds.
- Fixed release script to ignore GAFFER_OPTIONS_FILE environment variable.
- Updated IE publicDependenciesBuild script.
- Enabled testing of UI modules on Travis CI.
- Added debug output to installDependencies.py.

0.8.0.0
=======

Apps
-----------------------------------------------------------------------

- Python
    - Added support for executing files with arbitrary extensions.
    - Properly handled `sys.exit()` usage from within a script.
    - Updated sys.argv so `gaffer python myScript.py` behaves like
      `python myScript.py`.

Core
-----------------------------------------------------------------------

- Made small optimisations to the computation engine.

UI
-----------------------------------------------------------------------

- Added "layout:widgetType" metadata entry.
- Improved image rendering quality.
- Added error display in the node graph (#1115).
- Added menu item for applying Random node to IntPlugs.
- Fixed Box UI error when connecting external BoolPlug to internal IntPlug.

Scene
-----------------------------------------------------------------------

- Removed support for attribute caches.
- Optimised SceneReader hashes.
- Improved hash computation for many node types. This should improve
  cache memory usage and speed.
- Fixed SceneReader for invalid files and paths. Previously it would
  error on the first attempt, but either silently fail or crash on
  subsequent attempts.
- Optimised PathMatcher construction.
- Multithreaded child procedural instantiation in SceneProcedural.

RenderMan
-----------------------------------------------------------------------

- Added support for a "nodeColor" annotation.

Image
-----------------------------------------------------------------------

- Optimised ImageReader. Reduced runtime of ImageReader->ImageTransform
  benchmark by nearly 40%.
- Fixed thread-safety bug in ImageReader.

OSL
-----------------------------------------------------------------------

- Added UI support for OSL "help", "label", "divider", "widget" and
  "options" metadata entries.

Appleseed
-----------------------------------------------------------------------

- Added visibility attributes to AppleseedAttributes node.

API
-----------------------------------------------------------------------

- Added outputsToIgnore argument to GafferTest.TestCase.assertHashesValid().
- Added NodeAlgo support for plug presets specified en masse via arrays.
- Added Node::errorSignal().
- Added tokenize() function to StringAlgo.h.
- Added support for array metadata in OSLShader.
- Simplified OSLShader::*Metadata() python return types.
- Added Python bindings exposing the OSL version.
- Removed Source node.
- Removed FileSource node.
- Detemplatized ObjectSource.
- Added GafferUI.LayoutPlugValueWidget. This is entirely metadata-driven,
  and will be used to slowly replace legacy CompoundPlugValueWidget UIs.
- Deprecated CompoundPlugValueWidget.
- Fixed drawing of ImageGadget children.
- Added Gadget::executeOnUIThread() method.

Build
-----------------------------------------------------------------------

- Updated README with simplified build instructions.
- Added support for OSL 1.6.
- Requires Cortex 9.0.0-b2.
- Added Qt headers to Gaffer packages.
- Fixed TBB compilation on OS X.

Incompatibilities
-----------------------------------------------------------------------

- Simplified OSLShader::*Metadata() python return types.
- Removed support for attribute caches.
- Removed Source node.
- Removed FileSource node.
- Detemplatized ObjectSource.

0.7.0.0
========

This release brings the exciting addition of support for the open source [Appleseed](http://appleseedhq.net/) renderer. It also adds the much asked for Dot node, and a tool for editing render crop windows. Plus of course the usual small improvements, optimisations and bug fixes.

## UI

- Added resolution gate and crop windows overlays to 3d viewer (#1016).
- Added tool for manipulating crop window.
- Added "User Default" item to plug popup menus.
- Added sneaky hotkey for navigating inside any node in NodeGraph.
- Fixed Reference node UI to match equivalent Box node UI (#1108).
- Improved positioning of nodes created by the NodeMenu.
- Improved table widget (#204).
	- Remove button disabled when selection empty
	- Newly added rows are selected automatically
	- Newly added row has keyboard focus for immediate editing
- Added customisable presets to plug widgets (#1113).
- Fixed bugs where image viewer was using incorrect context (#1124).
- Fixed bug where channel mask UI was using incorrect context.
- Added a refresh button to ImageReaders.
- Added support for specifying node, nodule, and connection colours via Metadata (#89).
- Added support for setting node colour in the UIEditor or from the RMB popup in the graph.
- Fixed bug in ColorChooserDialogue.waitForColor().
- Added basic colour scheme for nodes in the GUI app (#1098, #154).

## Core

- Optimised Switch node for constant indices. A benchmark with the bunny scene followed by 50 switches shows a 6x speedup overall.
- Added Dot node (#12).
- Fixed bindings for Metadata types other than simple typed data (#1136).

## Scene

- Added min/max limits to StandardOptions crop window plug.
- Fixed bugs which prevented ObjectSource nodes from working after create/undo/redo.
- Fixed UnionFilter to accept inputs from Boxes.

## Image

- ImageWriter now creates the necessary directories before writing images.

## RenderMan

- Added shader Metadata option "shaderTypeOverride" (#pragma annotation "shaderTypeOverride" "ri:shader" will force the Gaffer shader type to "ri:shader").

## Appleseed

- Added support for the Appleseed renderer, courtesy of Esteban Tovagliari.

## API

- Optimised ScenePlug::stringToPath(). This gives an 88% reduction in runtime for a synthetic test of just that function, and a 7% reduction in total runtime for a scene benchmark using the Instancer.
- Added hasUserDefault( plug ) and applyUserDefault( plug ) to NodeAlgo.
- Added Context.__contains__ binding.
- Simplified numeric plug bindings.
- Added min/max values to BoxPlug.
- Added handy CompoundDataPlug::MemberPlug child accessors.
- Added GafferBindings::NodeClass() overload for suppressing init.
- Moved shutter() and transform() from RendererAlgo.h to SceneAlgo.h.
- Added camera() methods to SceneAlgo.h.
- Removed GLWidget minimum size.
- Fixed bug where ViewportGadget::setCamera() could forget viewport size.
- Fixed ViewportGadget::RasterScope to work during selection.
- Added ViewportGadget::preRenderSignal().
- Made View::update() non-pure virtual.
- Added View::contextChangedSignal().
- Added Tool base class.
- Fixed bugs in ExceptionAlgo formatPythonException().
- Fixed StandardStyle border widths to be independent of border radius.
- Added Menu.popupPosition() method.
- Improved support for functools.partial() callables in Menu commands.
- Added metadata to control StandardNodeGadget minimum width, padding, and nodule spacing.
- Improved StandardNodeGadget drag/drop handling. Previously it would accept drags it wasn't going to use, preventing other handlers from working.
- Added Nodule::updateDragEndPoint() virtual method.
- Fixed ScriptNode::deleteNodes() for nodes without enabled plugs.
- Added customisable edge gadgets to StandardNodeGadget.
- Added support for changing nodule position on StandardNodeGadget.
- Guaranteed order of Metadata::registered*Values().
- Added plug presets methods to Gaffer.NodeAlgo.
- Added GafferUI.PresetsPlugValueWidget.
- Added PlugValueWidget.childPlugValueWidget(), so derived classes don't need to implement it if they don't have such children (#1123).
- Added Style::renderNodeFrame() to distinguish between frames drawn for nodes and those drawn as normal frames.
- Updated Style bindings.
- Added useDisplayTransform argument to ColorSwatch constructor.
- Added useDisplayTransform argument to ColorChooser and ColorChooserDialogue.
- Added DataBinding.h header with dataToPython().

## Build

- Added scripts for automating releases.
- Updated IE public build script to use MILESTONE_VERSION, and renamed it to publicDependenciesBuild, since it is no longer used for producing the public release builds.
- Requires Cortex 9.0.0-b1 for Appleseed support.

## Incompatibilities

- Moved shutter() and transform() from RendererAlgo.h to SceneAlgo.h.
- Made View::update() non-pure virtual.
- Added virtual method to Nodule.
- Added and reordered Style virtual methods.

0.6.0.0
=======

#### UI

- Fixed bug which prevented newly created nodes from being inserted inline in the Node Graph.
- Added error display to string and numeric plug widgets - typically this is useful when a bad expression has been entered. Previously bad expressions would break the UI.
- Optimised the 3d view significantly.
- Fixed UI reordering bug in UIEditor (#847).
- Added menu item for deleting CompoundDataPlugValueWidget children.

#### Apps

- Added ignoreScriptLoadErrors parameter to execute app.

#### Core

- LocalDispatcher now has an option to ignore errors when loading the script (#1084).

#### Scene

- Fixed Grid node GL shader assignment.
- Fixed bug in Instancer dirty propagation.
- Fixed SubTree set computation when root path omits the leading slash.
- Added "isolate from" capability to GafferScene.Isolate node.

#### API

- Added support for invalid variants to GafferUI._Variant.fromVariant().
- Added TextWidget setErrored()/getErrored() methods.
- Added GafferSceneUI::SceneGadget class, for optimised display of scenes in OpenGL.
- Removed bloat from SceneProcedural - this was being used previously to implement the viewer but is no longer needed.
- Added ValuePlug::getValue() arguments for when hash is known.
- Added TypedPlugClass helper to GafferBindings.
- Improved exceptions thrown from ScriptNode::execute().
- ScriptProcedural now ignores errors when loading the script.
- Added PlugLayout.layoutOrder() static method.
- Fixed deadlocks if computes spawn their own threads.
- Added GafferScene::PathMatcher::prune() and isEmpty() methods.

#### Incompatibilities

- Added argument to ValuePlug::getObjectValue(), and associated derived class getValue() calls. Source compatibility is maintained, but binary compatibility is not.
- View::setContext() is now virtual.

#### Build

- Requires Cortex 9.0.0-a10

0.5.0.1
=======

#### Scene

- Fixed signal threading bug in SceneProcedural which was causing sporadic crashes

0.5.0.0
=======

#### Core

- Fixed LocalDispatcher to quote command line arguments and ignore "ui:" prefixed context variables.
- Avoiding shell subprocess for Local Jobs stats.
- LocalDispatcher now just constructs a Job and lets it do the heavy lifting
- Fixed bug where script context changes could leak into local background dispatches.
- added python error catching to ConnectionBinding, to prevent crashes
- Fixed serialization bug with extra plugs on references
- Dispatcher::frameRange() is now public and virtual.

#### UI

- Menu widget: Added support for icons
- Disabled Kill button when no jobs are selected.
- Job details tab is scrollable and resizable.
- Fixed context errors in teh scene inspector
- Added button to remove failed jobs.
- Preventing update error for deleted display node.
- Adding support for icons in menus

#### Image

- Preventing OIIO error overflow crash

0.4.0.0
=======

#### Core

- Plugs and ValuePlugs now accept children (#1043).
- Added child matching to connected Plugs (#1043).
- Added LocalDispatcher.Job and LocalDispatcher.JobPool to track running batches (#1064).
- Failing batches not stop a LocalDispatch job.

#### UI

- Improved Object section of SceneInspector (#897).
- Added a window for tracking currently running LocalDispatcher jobs (#872).
- Fixed reparenting bug with DispatcherWindows (#1064).

#### Scene

- Fixed poor performance of Prune/Isolate in presence of SetFilter.
- Added sets support to Parent node (#1065).
- Outputting all cameras, not just the primary camera, to the renderer.
- Added support for per-camera resolution overrides, specified with a "resolutionOverride" V2iData in the camera parameters.

#### API

- Plugs and ValuePlugs now accept children. CompoundPlug will be deprecated.
- Added BranchCreator::hashBranchGlobals() and computeBranchGlobals(), and implemented them for Parent.
- Added outputCameras() and overload for outputCamera() to RendererAlgo.h.
- Added LocalDispatcher.Job and LocalDispatcher.JobPool to track running batches.

#### Incompatible changes

- Added additional virtual methods to BranchCreator
- ValuePlug::settable() is no longer virtual
- Removed methods and member variable from CompoundPlug
- InteractiveRender "updateCamera" plug renamed to "updateCameras".

0.3.0.0
=======

#### Core

- Added SubGraph base class, which Reference and Box now derive from, allowing them both to be enabled/disabled.
- Redesigned Dispatcher registration (#922) (see API section for details).

#### UI

- Nodes created via the NodeMenu apply default values to their plugs, using the "userDefault" key in the Metadata (#1038).
- Exposed the DispatcherWindow to the public API.

#### Cortex

- Moved Cortex-specific functionality into new GafferCortex library and module.
	- The Gaffer core itself remains heavily dependent on Cortex, and always will. Here we're splitting out "end user" functionality such as OpHolders and ProceduralHolders, so that GafferCortex can be thought of as the user-visible presence of Cortex within Gaffer.
	- This remains backwards compatible for now via startup files, which allows a grace period for dependent code to update to the new module layout.

#### RenderMan

- Added basic support for RenderMan volume shaders.

#### API

- Added Gaffer.NodeAlgo python scope with applyUserDefaults( node ) (#1038).
- Redesigned Dispatcher registration (#922).
	- Dispatchers are registered with Creator functions rather than instances.
	- Added get/setDefaultDispatcherType(), which can be used to create a new instance of the default type.
	- SetupPlugsFn is now a static function that can be registered along with a Creator, rather than a virtual method of Dispatcher instances.
- Added gil release to GafferScene.matchingPaths python binding.
- Fixed StringPlug string substitution bug.
- Catching error_already_set in Dispatcher bindings.

#### Incompatible changes

- Reference and Box now derive from SubGraph rather than Node or DependencyNode.
- Redesigned Dispatcher registration (#922) (see API section for details).

0.2.1.0
=======

#### Core

* Expression node optimizations

#### Scene

* Made ShaderAssignment use the shader type as an attribute name.
* Added Group::nextInPlug() method
* InteractiveRender now updates all attributes, not just shaders

#### UI

* Dispatcher FrameRange UI displays the value that will actually be dispatched.
* Removed unwanted horizontal padding from frameless Buttons.

0.2.0.0
=======

This release brings significant optimisations, further additions to the SceneInspector, and the usual collection of miscellaneous enhancements and bug fixes.

#### Core

- Optimised Context::substitute(). This gives a 73% reduction in runtime for a substitutions benchmark.
- Added '\' as an escape character in Context::substitute() (#997).
- Boxes may now be enabled/disabled and define pass-through behaviours (#1015).
- Significant optimisations to the computation engine.
- Added TaskList node for grouping the dispatch of several input requirements.

#### Image

- Fixed Display node for bucket sizes larger than the native tile size.
- Fixed problems when running embedded in Maya.

#### Scene

- Added code to clear caches after full procedural expansion in batch renders.
- Added scene pass-through to the InteractiveRender node. This allows it to be seen in the Viewer, SceneHierarchy, SceneInspector etc.
- Significant optimisations. A benchmark scene can now be generated in 3% of its previous runtime.

#### RenderMan

- Added "command" plug to RenderManRender. This allows the user to customise the command used to render the RIB (#1017).

#### UI

- SceneInspector improvements
	- Added set membership section (#930).
	- Added sets section to globals (#895).
	- Improved responsiveness.
- MenuButton improvements
	- Menus are shown on press rather than release (#742).
	- Added menu indicator (#493).
- Fixed OpDialogue bug which caused it to return to the parameters pane when it should have been displaying an error.
- Dispatcher improvements
	- Added PlaybackRange to the frames mode menu (#1007).
	- Renamed ScriptRange to FullRange.

#### API

- Added custom Diff support to SceneInspector.
- Fixed crashes when passing None to PathMatcher python methods.
- Added accessors for the buttons on VectorDataWidget (#1003).
- Fixed broken SceneInspector.Row.getAlternate() method.
- Added SceneProcedural::allRenderedSignal().
- Added Context::remove() method.

#### Incompatible changes

- SceneInspector API changes.
- Box rederived from DependencyNode.
- Dispatcher ScriptRange renamed to FullRange.

#### Build

- Improved Travis continuous integration setup
	- Added running of unit tests
	- Added GafferRenderMan support
- Fixed installation to paths starting with "./"
- Fixed RenderManShader compilation in Clang 3.4
- GafferOSL compatibility for OSL version 1.5

0.1.1.0
=======

#### Core

- Optimised computation for long chains of nodes (#963).
	- Optimised repeat calls to Context::hash().
	- Added Context::changed() method.
	- Made Context::hash() ignore "ui:" prefixed entries.
	- Refactored ValuePlug::hash() to delegate to Computation.

#### UI

- Fixed Execute->Repeat Previous menu item.
- Fixed display of '<', '>' and '&' in SceneInspector.

#### Scene

- Added an ExternalProcedural node (#722).
- Added pass-through plugs to ExecutableRender nodes and SceneWriter.
- Added pixelAspectRatio, overscan, and resolutionMultiplier options (#979).

#### Image

- Added pass-through plugs for ImageWriter.

#### Build

- Requires Cortex 9.0.0-a6
- Fixed typedef issues when building with GCC 4.8
- Added Travis config for build verification (doesn't run the tests yet)

0.1.0.0
=======

#### Apps

- The "gui" app now tolerates errors when loading scripts from the command line. Note that currently errors are only reported to the shell.
- The "execute" app can now handle nodes inside Boxes.

#### Core

- Improved version numbering (#980)
	- Versions are now MILESTONE.MAJOR.MINOR.PATCH
		- Changes to MILESTONE version denote major development landmarks
		- Changes to MAJOR version denote backwards incompatible changes
		- Changes to MINOR version denote new backwards compatible features
		- Changes to PATCH version denote bug fixes
	- Added Gaffer.About.compatibilityVersion() method
	- Added GAFFER_COMPATIBILITY_VERSION macro for conditional compilation of C++ extensions
- Fixed bug whereby GraphComponent::setName() could allow duplicate names
- Dispatcher improvements
	- `Dispatcher::postDispatchSignal()` is now always executed, even if execution is cancelled or fails. A new boolean argument is passed to specify whether or not dispatch succeeded.
	- Dispatcher now creates job directories automatically, so derived classes don't have to

#### Incompatible changes

- `Dispatcher::postDispatchSignal()` signature change.
- Dispatcher jobDirectory() semantics change.
- Dispatcher jobDirectoryPlug() -> jobsDirectoryPlug() rename.

#### Build

- Requires Cortex 9.0.0-a5

0.101.0
=======

#### Core

- ExecutableNodes now accept Boxes as requirements inputs and outputs.
- Dispatchers accept Boxes for direct dispatching (#925).
- Added SystemCommand executable node.
- Optimised plug dirty propagation.
- Added matchMultiple() function to StringAlgo.h.

#### Scene

- Renamed Displays node to Outputs. Also changed "label" plug to "name" and the old "name" plug to "fileName" (#54).
- Fixed dirty propagation bug in Outputs node.
- Added an outputOutputs() method to RendererAlgo.h, so outputOptions() need only output actual options.
- Added DeleteGlobals node.
- Added DeleteOutputs node.
- Added DeleteOptions node (#965).
- Added wildcard matching to DeleteAttributes and DeletePrimitiveVariables.
- Prefixed options in scene globals with "option:".
- Added global mode to Attributes node, which places the attributes in the globals (with "attribute:" prefixes).
- Updated render nodes to support global attributes.
- Added global attribute support to SceneProcedural (#964).
- Fixed RendererAlgo outputScene() to include coordinate systems.

#### UI

- Added Outputs section to the SceneInspector (#921).
- Updated SceneInspector to display global attributes.
- Fixed display of single empty bounding box in SceneInspector.

#### RenderMan

- Added FrameBegin/FrameEnd in RIBs generated by RenderManRender (#358). Requires Cortex 9.0.0-a5.

#### OSL

- Fixed default arguments for OSL In* and Out* shaders.

#### Build

- Set default compiler optimisation level to -O3.
- Added missing OSL, OIIO, OCIO includes to the dependency package.
- Clang compatibility fixes.

0.100.0
=======

This release features significant improvements to Dispatcher and SceneInspector functionality, along with the usual bunch of small fixes and improvements.

#### Apps

- Changed shutdown warnings to debug messages.

#### Core

- Dispatcher improvements
	- Dispatching can be cancelled via preDispatchSignal() (#929).
	- Added batching (#870, #871).
	- Optimised foreground execution in LocalDispatcher.
	- Added per-node foreground execution overrides for LocalDispatcher (#927).
- Added support for module level config files.

#### UI

- SceneInspector improvements
	- Added history tracebacks (#834).
	- Added attribute inheritance diagramming (#206).
	- Added value drag/drop (#830).
	- Improved transform section (#896).
	- Optimised by deferring updates during playback.
	- Optimised by deferring updates when not directly visible.
	- Fixed errors where the selected path doesn't exist.

#### Scene

- Fixed SceneWriter::hash() to include file path.
- Fixed SceneWriter when caching multiple time samples.
- Added support for coordinate systems.

#### API

- Fixed Fixed python bindings crash when passing None for a scene path.
- Added removeOnClose argument to Window.addChildWindow() method.
- Fixed EventLoop bug where exection was thrown if an idle callback was removed and re-added during the same idle event.
- Added hotspots to Pointer class.
- Refactored ExecutableNode API
	- Removed "execution" prefix from method names.
	- ExecutableNodes now execute() using the current Context. Multi-context execution can be accomplished using executeSequence( frames ) assuming the client only needs to vary the frame of the current Context. requiresSequenceExecution() can be defined by nodes with special needs (SceneWriter for example), to alert clients that sequence execution is more appropriate.
	- Dispatcher::doDispatch() is now passed a DAG of TaskBatch nodes, simplifying the task of implementing more complex dispatchers.
- Fixed call sequence for GraphComponent::parentChanging(). When a child is being transferred from one parent to another, it is now called at a point where the child still has the original parent.
- Added ViewportGadget raster<->world space conversion methods.
- Added Handle::dragOffset() method.

#### Build

- Best used with 3delight version 11.0.96. This has bug fixes to support moving coordinate systems during IPR.
- Requires Cortex 9.0.0-a3.

0.99.0
======

#### Apps

- Fixed potential startup error in gui viewer.py configuration file.

#### Core

- Added background execution mode to the LocalDispatcher.

#### UI

- Added a gnomon to the 3d viewer (#41).
- Improved SceneInspector
	- Reimplemented as a hierarchy with a registration mechanism for custom sections (#36, #821).
	- Improved diff formatting (#894).
	- Improved numeric formatting and alignment.
	- Added options section (#197).
- Implemented error tolerant loading for file menu operations. Errors are reported via a dialogue, and will no longer prevent loading of a script (#746).
- Fixed ScriptEditor to execute code in the right context. Prior to this, any queries performed in the script editor were always evaluated at frame 1.
- Dispatcher UI no longer forces background execution - this is now controlled by per-dispatcher settings.

#### Scene

- Improved IPR
	- Fixed hang during shutdown with active IPR render (#855).
	- Implemented camera edits for IPR rendering (#190).
	- Prevented errors in other nodes from causing incomplete edits.
	- Fixed UI errors caused by deleting camera during IPR (#898).
	- Optimised updates by pruning invisible hierarchies.
	- Fixed bug in shader edits at non-leaf locations.
- Optimised Instancer, especially the computation of the bounding box for all the instances. This particular operation is now 18x faster on a 6 core machine, 7x faster on a 2 core machine.
- Added an automatically created set for tracking all cameras in the scene.
- Improved reporting of invalid cameras (#371).
- Fixed FilteredSceneProcessor::acceptsInput() crash when inputPlug is null.

#### API

- Registered automatic from-python conversions for ScenePlug::ScenePath. This replaces the need to manually wrap any functions taking a ScenePath, making the bindings simpler.
- Added exists() method to SceneAlgo. This can be used to query whether or not a particular location exists within a scene.
- Replaced boost_intrusive_ptr with raw pointer where appropriate, to follow the convention laid out in Cortex.
- Removed deprecated Box metadata methods. The standard Metadata API should be used instead.
- Added missing wrapper for NodeGadget::nodule() overload.
- Added OpDialogue preExecuteSignal() and postExecuteSignal().
- Added OpDialogue parameterisedHolder() method.
- Added a flags argument to ParameterHandler::setupPlug(). This allows clients to choose the default flags for their plugs, rather than being forced to have (Default | Dynamic) plugs.
- Added ViewDescription constructor for 3 argument registerView.
- Added Style::renderTranslateHandle() method.
- Added GafferUI::Handle gadget.
- Moved translatePythonException() to a new ExceptionAlgo.h header.
- Added formatPythonException() function to ExceptionAlgo.h.
- Added continueOnError argument to ScriptNode execution methods.
- Added error return value to ScriptNode execution methods.
- Improved EventLoop.executeOnUIThread() to execute immediately when used on main thread.

#### Build

- Requires Cortex-9.0.0a2
- Updated default build to use PySide 1.2.2.
- Stopped using python-config for build configuration. It was unreliable on Mac, and the hardcoded paths it returns prevented us from building with prebuilt binary dependencies.

0.98.0
======

This release makes dispatchers available via the UI for the first time. Dispatchers allow many tasks (such as rib generation, rendering and compositing) to be processed for a series of frames, with dependencies between the tasks determining the execution order. It also adds support for adding and removing lights during IPR renders, and the usual  small fixes and improvements.

#### Apps

- Added context parameter to the execute app. This takes a series of key/value pairs that allow additional context variables to be specified.
- Fixed shutdown warning when running `gaffer test GafferTest`.
- Added repeat parameter to test app.

#### UI

- Integrated Dispatchers into the UI with a Dispatcher window, which can be launched in any of the following ways :
	- The /Execute/ExecuteSelected menu item (Ctrl+E)
	- The Execute button the NodeEditor
	- The right click node menu in the NodeGraph.
- Fixed several shutdown warnings.
- Fixed bug in Reference node menu item.

#### Core

- Added jobName and jobDirectory plugs to Dispatcher. These control the creation of a location for storing temporary files needed for the dispatch.
- Added Frame Range options to Dispatcher.
- Improved LocalDispatcher to dispatch tasks in a subprocess (#866).
- Fixed ExecutableOpHolder hash computation.
- Implemented variable substitutions for ExecutableOpHolder.
- Fixed ObjectWriter hash computation (#878).

#### Scene

- Implemented light add/remove/hide/show for IPR (#874).
- Stopped ExecutableRender saving the script when it executes (#310). This is now done automatically by the dispatchers, which save a copy into the job directory.
- Fixed ExecutableRender hash computation.
- Fixed SceneWriter hash computation.

#### Image

- Fixed ImageWriter hash computation.

#### API

- Added ScenePlug::pathToString() method.
- Added outputLight() method to RendererAlgo.h.
- Fixed bug in DependencyNode dirty propagation order. This ensures that dirtiness is only signalled for a plug after it has been signalled for all the plugs it depends on and all its children.
- Derived all Gaffer unit tests from GafferTest.TestCase.
- Simplified Dispatcher implementations by providing doDispatch with the unique task list.
- Made Dispatcher::uniqueTasks() private.
- Dispatchers now require that all nodes belong to the same ScriptNode.
- Fixed ExecutableNode::Task comparison functions and member access (#865).
- Improved Plug bindings with a new PlugClass helper class.
- ExecutableNode::executionHash() must now call the base class implementation first - see documentation for details.

0.97.0
======

This release is focussed mainly on optimisation and bug fixes, with significant speedups being provided by moving to a new caching implementation provided by Cortex 9. Behind the scenes it also contains progress towards exposing Dispatcher functionality at the user level.

#### Core

- Optimised FilteredChildIterator and PlugIterator. This alone gives more than a 5% speedup in a simple Instancer benchmark.
- Fixed serialisation of non-dynamic ArrayPlugs. This bug caused the appearance of duplicate requirements plugs on executable nodes (#580).

#### UI

- Added a grid to the 3D viewer.
- Added NodeGraph menu item for selecting objects affected by a node - accessed by right clicking on a filtered scene node.
- Fixed several causes of zombie widgets which could cause errors at shutdown.
- Moved the Execute button for ExecutableNodes to a prominent position in the header of the NodeEditor.
- Added SceneWriter to the node menu. Also reorganised the Scene menu to include a File submenu, and simplified the Object menu by moving generators into the Source submenu.

#### Scene

- Optimised Shader network computation - reducing runtime by 35% for typical production networks.

#### Arnold

- Fixed ArnoldRender "Generate expanded .ass" mode. It was using a "-resaveop" command line flag removed from kick in Arnold version 4.0.10.0.

#### API

- Added ability for Gadgets to have child Gadgets. Previously only ContainerGadgets could have children.
- Rederived NodeGadget from Gadget rather than IndividualContainer. This allows more flexibility in NodeGadget implementations, and also better hides the implementation details.
- Added methods for controlling Gadget visibility.
- Rederived ViewportGadget from Gadget rather than IndividualContainer. This allows viewports to have multiple child gadgets, which paves the way for more complex views and interactive manipulators.
- Made UI registration methods accept classes in place of TypeIds.
- Added public GafferScene::Filter methods for specifying input scene via Context.
- Added SceneAlgo.h with methods for querying all objects matching a filter.
- Continued refactoring the Executable framework, in preparation for exposing it to users
	- Americanized spelling.
	- Renamed ExecuteUI to DispatcherUI.
	- Renamed ExecutableNode "dispatcherParameters" plug to simply "dispatcher".
	- Rederived SceneWriter from ExecutableNode.
	- Rederived Dispatcher from Node, to allow settings to be specified via plugs.
	- Renamed Dispatcher::addAllPlugs() to Dispatcher::setupPlugs().
	- Renamed Dispatcher::addPlugs() to Dispatcher::doSetupPlugs.
- Added shutdown checks for zombie widgets and scripts.
- Fixed "base class not created yet" GafferRenderMan import error.
- Added _copy parameter to Shader::state() python binding.

#### Documentation

- Improved formatting of Doxygen documentation - a brief description of each class is now shown above the detailed member documentation.

#### Build

- Requires Cortex 9.0.0-a1.
- Recent Cortex LRUCache improvements offer significant performance gains.
- Updated default TBB version to 4.2.

0.96.0
======

#### Core

- Added support for Box data to CompoundDataPlug.
- Optimised the Context class considerably, particularly for temporary Contexts created during computation. A synthetic test which does nothing but create temporary Contexts shows a reduction in runtime of 97%, resulting in a 30% reduction in total runtime for a more real-world test using the Instancer node (#427).
- Fixed Context copy construction doubling in Python bindings.
- Fixed circular references within the undo system, which caused memory leaks where scripts were not destroyed at the appropriate time (#397).
- Optimised ComputeNode::hash(). This yields ~14% reduction in runtime for a simple Reformat benchmark.

#### UI

- Fixed PyQt circular references within GafferUI.Menu (#397).
- Fixed crash caused by File->Quit menu item.
- Improved UI for BoxPlugs.

#### Scene

- Added crop window to StandardOptions node (#688).
- Renamed gaffer:visibility attribute to scene:visible, to support the standard attribute with that name in Cortex scene caches.
- Added a SetFilter node (#92).
- Fixed deadlock removing input from running InteractiveRender node, or undoing or redoing such an operation.
- Added pausing for interactive renders (#646).

#### API

- Renamed BoxPlug min() and max() methods to minPlug() and maxPlug().
- Made Context::Scope noncopyable.
- Added GAFFERTEST_ASSERT macro. This should be used by test cases implemented in C++, and throws an exception which can be caught and reported by the Python unit test runner.
- Added _copy argument to Context::get() bindings.
- Added optimised Context copy constructor, primarily for use in constructing temporary Contexts. See class documentation for details.
- Added checks for zombie ScriptNodes and Widgets at app shutdown. This can catch many common programming errors.
- Added BoxPlugValueWidget class.

0.95.0
======

#### UI

- Improved SceneReader UI with right click menu for toggling tags on and off in the tags and sets plugs.

#### Core

- Fixed bug with references containing non-default plug values (#844).

#### Scene

- Added preliminary support for sets (#92).
	- Added a Set node. This allows users to manage sets of named locations (with optional wildcards) as part of their graph flow.
	- Replaced "gaffer:forwardDeclarations" globals entry with a private set named "__lights".
	- Updated hierarchy modifying nodes to also modify sets to keep them in sync with the hierarchy.
	- Implemented loading of tags as sets in SceneReader.
	- An upcoming release will contain a SetFilter for actually making the sets useful.
- Added a FreezeTransform node (#822).

#### RenderMan

- Fixes IPR bug where shaders could leak onto the wrong objects.

#### API

- Typedefed PathMatcherData into GafferScene namespace.
- Optimised PathMatcher (the underlying data structure for sets).
- Replaced GafferScene::Render base class with RendererAlgo.h header.
- Simplified Executable nodes and tidied up implementation, in preparation for actually integrating Despatchers properly.

0.94.0
======

#### Apps

- Increased default size of browser app (#795).
- Added bookmarks support to Op windows in the browser app (#787).
- Fixed position of quit confirmation dialogue (#751).
- Fixed parsing of command line arguments with spaces.

#### UI

- Fixed PySide incompatibility in VectorDataWidget.
- Improved VectorDataWidget numeric editing (#637).
- Simplified OpDialogue exception reporting (#806).
- Fixed "Open Recent..." crash bug in PySide builds (#548).
- Used OpDialogue to improve progress/error reports in OpPathPreview (#792).
- Enabled background mode for OpDialogue launched from BrowserEditor.
- Fixed OpPathPreview UI glitch.
- Fixed "KeyError: 'currentTab'" error when loading custom layouts.
- Added more sensible initial widget sizes to BrowserEditor. The sizes are also saved and restored when modes are switched.
- Improved Bookmarks
    - Identifies recent items by full paths, so multiple recent items with the same basename may coexist.
    - Prevents heavy usage of one bookmarks category from removing the recent items for the general (no category) bookmarks.
    - Improves bookmarks UI in PathChooserWidget to display full paths of recent items.
	- Most recent items are now displayed at the top.
	- Added creation of bookmarks by dragging on to bookmarks icon.
- Fixed cursor bug in StringPlugValueWidget continuous update mode (#796).
- Fixed bug in non-editable MultiLineStringPlugValueWidgets.
- Fixed upside down nodule labels.
- Fixed overzealous Viewport drag tracking (#550).
- Improved SceneHierarchy to view any output ScenePlug, regardless of name. This improves compatibility with Boxes, where the user can make an output plug with any name they want.
- Added right click menu for Box plugs in NodeGraph. This allows the renaming and deletion of promoted nodules.
- Added dropdown menu for Displays node quantize parameters.
- Improved Displays node UI (#15).
- Added command-line representation of Op values in the UI (#793).
- Added workaround for squash/stretch in viewport camera look-through (#826).
-  Added custom editor to PathVectorDataWidget. This enables tab completion, nice dropdown menus and a browser for PathVectorDataParameters.
- Added indexing methods to VectorDataWidget.
- Added presetsOnly dropdown menus to CompoundVectorParameterValueWidget (#470).
- Added an auto-load preset for ops (#804).
- Added filtering by image type for ImageReader and ImageWriter file dialogues.

#### Core

- Combined setValue() serialisation for CompoundNumericPlugs (#761).
- Fixed Box plug promotion to support ImagePlugs and ScenePlugs.

#### Scene

- Renamed GLSL shaders to UpperCamelCase. This matches the naming convention we use for OSL shaders.
- Added a Grid node.
- Fixed FilteredSceneProcessor to allow Box promotion of Filter plug.

#### Image

- Fixed a bug in ImageTransform that could result in corrupted output.

#### API

- Added GraphComponentClass and GadgetClass to improve bindings.
- Added NodeGadgetClass to improve bindings of NodeGadgets.
- Added immediate execution mode to OpDialogue.
- Fixed NodeGadget::noduleTangent() binding.
- Fixed potential bug in NodeGadget::create().
- Fixed LRUCache getter cost calculations.
- Fixed Metadata test hang.
- Improved Window.resizeToFitChild() behaviour. If called on an as-yet unshown window, it would move the window to the top left corner of the screen. Now the window will still be opened in a sensible place. Added additional shrink and expand arguments to further control the resize behaviour.
- Added support for fixed size CompoundVectorParameterValueWidget. The ["UI"]["sizeEditable"] user data entry can be given a BoolData value of False, which will cause the +/- buttons to be hidden in the UI, enforcing a fixed length on the data in the vector parameters.
- Added per-column editability to CompoundVectorParameterValueWidget. This uses a ["UI"]["editable"] user data entry in each child parameter, where a BoolData value of False will make the column for that parameter read-only (#766).
- Made Bookmarks.acquire() support passing Widgets and GraphComponents.
- Added support for callable dialogue keywords in PathPlugValueWidget.
- Fixed drag/drop to allow modal dialogue creation in dropSignal().
- Added public Serialisation::acquireSerialiser() method.
- Added ValuePlugSerialiser::valueNeedsSerialisation() method. This can be reimplemented by derived classes to provide more control over the serialisation of values.
- Privatised numeric and string PlugValueWidget implementations.
- Added ViewportGadget viewportChangedSignal() and cameraChangedSignal().
- Added SpacerGadget size accessors.
- Added iterator typedefs for all GafferUI::Gadget subclasses.
- Improved Box plug promotion API.
- Made BlockedConnection and UndoContext non-copyable.
- Added useNameAsPlugName argument to CompoundDataPlug::addMembers(). Also added python bindings for CompoundDataPlug::fillCompoundData() and CompoundDataPlug::fillCompoundObject().
- Gave Displays node parameter plugs more useful names.
- Added VectorDataWidget.editSignal(). This allows custom Widgets to be provided to edit the values held in the table cells.
- Added Widget.focusChangedSignal().
- Added VectorDataWidget setColumnEditable/getColumnEditable methods.
- Added right click preset menu for CompoundVectorParameterValueWidget. This also adds the ability for any custom parameter menu to operate with CompoundVectorParameters, whereas before they couldn't.

#### Build

- Now using Coverity static analysis - this resulted in a number of bugs being found and fixed in this version.

0.93.0
======

#### Core

- Added the ability to specify Metadata overrides to specify instances of Plugs and Nodes.

#### UI

- Added UI Editor. This allows the user plug layout for any node to be edited - plugs can be reordered, dividers added and help strings specified. In particular this allows the creation of custom UIs for Boxes, which can then be exported and loaded by References.
- Fixed initial unsortedness of PathListingWidgets.

#### Scene

- Added PrimitiveVariables node. This allows arbitrary primitive variables with constant interpolation to be added to objects.
- Added Duplicate node. This allows arbitrary numbers of duplicates of subhierarchies to be created, each with their own transform.

#### OSL

- Specifying lockgeom=1 by default for all OSL shading engines. This means that primitive variables (user data in OSL parlance) are not automatically mapped to shader inputs unless those inputs have explicitly set lockgeom=0 in the source (which is rare). This almost doubles the speed of a simple image noising operation.
- Fixed OSLShader::acceptsInput( NULL ) crash.

#### API

- Added PlugLayout class, which creates node editor UIs driven by Metadata. This will replace all existing plug layouts over time.
- Added StringAlgo.h, containing various string utilities, including wildcard matching (#707).
- Added metadata accessors to OSLShader.
- Fixed module import order and namespace pollution issues.
- Replaced Metadata regexes with new string matching code.
- Added Metadata signals emitted on registration of values.
- Made NameWidget accept None for the the GraphComponent.
- Added borderWidth argument to SplitContainer constructor.
- Added PathListingWidget setHeaderVisible()/getHeaderVisible() methods.
- Added PathListingWidget.pathAt() method.
- Fixed bug in GafferUI::Pointer::setFromFile( "" )
- Added a DictPath.dict() accessor.
- Moved NodeEditor.acquire() to NodeSetEditor.acquire(). This allows it to be used to acquire an editor of any type.
- Added fallbackResult to WeakMethod.
- Fixed CompoundPlug plugSetSignal() emission when children change.

0.92.1
======

#### Scene

- Improved shader assignment reporting in SceneInspector (#335)
- Improved shader handle generation

0.92.0
======

#### Core

- Made Plug flags serialisation more future proof (#684).
- Removed redundant serialisation of default values. This reduced file sizes by 25% and load times by nearly 20% for a large production script. Note that changing the default value for a plug or shader parameter now represents a backwards compatibility break with old scripts.
- Optimised python bindings, giving speedups in many areas, including file loading and shader generation.
- Removed parameter mapping from ObjectReader
- Fixed threading bugs in ObjectReader.
- Fixed bugs preventing expressions being used with filenames in ObjectReader.

#### UI

- Improved plug "Edit Input..." menu item. It now ensures that the input plug widget is directly visible on screen, whereas before it could only show the node editor for the input node.
- Prevented nodes from being created offscreen (#640).
- Exposed "enabled" plugs in a new Node Editor "Node" tab (#759).
- Fixed MessageWidget crashes encountered in Maya.
- Fixed bug preventing positioning of new nodes within backdrops (#769).
- Added workaround for PyQt/uuid crashes (#775).
- Added filtering so that DirNameParameter file browsers will only show directories and not files (#774).
- Fixes image viewer colour swatches when the image doesn't contain an alpha channel.
- Improved scene preview support to include .abc, .cob, and .pdc files (any files for which Cortex has a Reader implementation).

#### Scene

- Options and Attributes nodes now have sensible default values for their plugs.

#### Image

- Fixed bugs associated with negative display window origins.
- Fixed crash when creating ImageWriters with another image node selected (#681 #255).

#### Arnold

- Arnold shader names are now prefixed with "ai" within the node search menu, to aid finding them amongst the other nodes.

#### API

- Added Widget.reveal() method (#503).
- Added extend argument to NodeGraph.frame(). The default value of false behaves exactly as before - the specified set of nodes are framed in the viewport. A value of true still causes the nodes to be included in the framing, but in addition to the original contents of the frame.
- Properly implemented CompoundNumericPlugValueWidget.childPlugValueWidget().
- Removed MessageWidget.textWidget() method. The internal text widget should now be considered private. The currently displayed messages may be cleared using the new MessageWidget.clear() method.
- Removed deprecated MessageWidget.appendException() method.
- Added control over the default button to the OpDialogue. This controls whether the OK or Cancel button is focussed by default when displaying the Op. The default value is as before, focussing the OK button, but the value can be controlled either by user data in the Op or by passing an alternative argument to the OpDialogue constructor.
- Adopted new Python wrapping mechanism from Cortex.
- Fixed pollution of GafferUI namespace with IECore module.
- Added DirNameParameterValueWidget.
- PathPreviewWidget now respects registration order.

#### Build

- Requires Cortex 8.2.0.

0.91.0
======

#### Apps

- Fixed gui startup error in ocio.py.

#### Core

- Fixed copy/paste problems where inappropriate values would be copied for plugs with inputs, where the input was not in the selection being copied (#740).

#### UI

- Added a first implementation of an automatic node layout algorithm. This is available via the Edit/Arrange menu item (#638).
- Fixed image viewer data window display in the presence of an offset display window.
- Fixed TextGadget vertical bound. It was slightly different depending on the text contents, causing different nodes to appear with slightly different heights.
- Moved OSLObject and OSLImage shader inputs to the left of the node.
- Added message filtering to MessageWidget.

#### Scene

- Fixed AlembicSource refresh failure (#737).
- Fixed errors when AlembicSource filename is "".

#### RenderMan

- Added support for multiple types in RSL "coshaderType" annotation (#621).

#### OSL

- Added support for arbitrary image channels to the OSLImage node. The InChannel and InLayer shaders should be used to fetch channels and layers from the input image, and the OutChannel and OutLayer shaders may be used to write values to the output channels and layers. The Out* shaders should be plugged into an OutImage shader which is then plugged into the OSLImage node.
- Added support for arbitrary primitive variables to the OSLObject node. The InFloat, InColor, InNormal, InPoint and InVector shaders provide access to vertex primitive variables on the input primitive, and the corresponding Out* shaders
can be used to write values to the output primitive variables. The Out* shaders should be pluggined into an OutObject shader which is then plugged in to the OSLObject node.
- Added V3fVectorData support to OSLRenderer user data queries.
- Fixed dirty propagation through OSLShader closure outputs.
- Improved OSL processor shader input acceptance.
	- Only accepts OSLShader nodes if they hold a surface shader, as other shader types can't be used directly.
	- Also accepts Box and ShaderSwitch connections so that shaders can be connected indirectly.
- Revised shader naming convention to UpperCamelCase. The names of existing shaders have therefore changed.

#### API

- Moved OSLImage::shadingEngine() method to OSLShader::shadingEngine().
- Removed FormatPlugSerialiser from the public interface - it was not intended to be subclassed.
- Removed FormatBindings namespace and moved formatRepr() into the GafferImageBindings namespace.
- Switched formatRepr() signature to take a reference rather than a pointer.
- Added MessageWidget setMessageLevel() and getMessageLevel() methods.

0.90.0
======

#### Scene

- Fixed off-by-one error in scene cache preview frame ranges.

#### UI

- Fixed slight jump when connections are first drawn.
- Removed PathFilter paths plug representation in the NodeGraph. There aren't really any nodes we would connect to it.
- Improved OpDialogue warning display. If an Op completes successfully, but emits error or warning messages in the process, these will now always be flagged before the user can continue.

#### API

- Refactored ConnectionGadget into an abstract base class with a factory, to allow for the creation of custom subclasses. A new StandardConnectionGadget class contains the functionality of the old ConnectionGadget. Config files may register creation function for connections to control the type of gadget created, and its style etc.
- Added MessageWidget.messageCount() method. This returns the number of messages currently being displayed.
- Added OpDialogue.messageWidget() method. This provides access to the message display for the Op being executed.
- Added MessageWidget.forwardingMessageHandler(), to allow messages received by the widget to be propagated on to other handlers. This can be useful for connecting the OpDialogue to a centralised logging system.
- Deprecated MessageWidget appendMessage() and appendException() methods. The same result can be achieved by passing messages via the message handler instead.

0.89.0
======

#### Core

- Added Support for NumericPlug->BoolPlug and BoolPlug->NumericPlug connections.

#### UI

- Added additional types to the user plug creation menu.
- Added pre-selection highlighting in the NodeGraph (#94).
- Added "Create Expression..." menu option for bool plugs.
- Fixed NodeGraph resizing to crop rather than scale (#10).
- Fixed read only CompoundPlug labels.
- Added workarounds for Qt OpenGL problem on OS X (#404 and #396).

#### Scene

- Added Parent node. This allows one hierarchy to be parented into another (#91).
- Fixed bug which could cause incorrect bound computation at the parent node in the Instancer.
- Seeds and Instancer classes now preserve existing children of the parent location, renaming the new locations to avoid name clashes if necessary.
- Added tag filtering to the SceneReader node.
- Enabled input connections to PathFilter "paths" plug. This allows it to be promoted to box level and be driven by expressions etc (#704).

#### Apps

- Updated view app to contain tabs with different views (info, header, preview etc).
- Added scene cache previews to the browser and view apps (#416).

#### API

- Removed BranchCreator name plug - derived classes are now responsible for generating the entirety of their branch.
- Modified BranchCreator hashing slightly to improve performance - derived classes hashBranch*() methods are now responsible for calling the base class implementation.
- Fixed Box::canPromotePlug( readOnlyPlug ) to return false.
- Fixed Box::canPromotePlug() to check child plugs too.
- Fixed bug in read only Plugs with input connections.
- Added Gadget setHighlighted() and getHighlighted() methods.
- Added supportedExtensions() methods to ImageReader and SceneReader.
- Added Viewer.view() and Viewer.viewGadgetWidget() methods.
- Added NodeToolbar and StandardNodeToolbar classes.

#### Build

- Updated public build to use OpenEXR 2.1.
- Updated public build to use OpenImageIO 1.3.12.
- Updated public build to use OpenShadingLanguage 1.4.1.
- Removed pkg-config from the dependency requirements.

0.88.1
======

#### Core

- Added env app which mimics /usr/bin/env
- Enabled Python threading by default in Gaffer python module

#### UI

- Renaming is available for promoted children of CompoundDataPlugs
- Moved scene node filter plugs to the right hand side of the node

#### Image

- Fixed threading issue in Display node

0.88.0
======

#### Core

- Fixed threading issue in caching code.
- Implemented per-instance metadata for Box nodes. This will provide the basis for the user to make further customisations to Boxes, like setting descriptions for plugs and so on.
- Fixed bug in Switch node which could cause crashes when promoting the index plug.
- Added pivot to TransformPlug.

#### UI

- NodeGraph node tooltips now display a helpful description for the node. Node authors can define this text using the "description" Metadata entry (which is intended to provide a static description of the node's purpose) and the "summary" Metadata which may optionally be computed dynamically to describe the current state of the node (#157).
- Fixed initial value jump in viewer gamma/exposure virtual sliders.
- NodeGraph nodes may now display plugs on all sides, rather than just top/bottom or left/right as before. Node authors may control plug placement by defining a "nodeGadget:nodulePosition" Metadata entry.
- ShaderAssignment nodes now receive their shader input from the left (#82).
- Fixed OpDialogue hangs caused by the rapid output of many messages from an Op.
- Fixed strange browser behaviour when editing a path which is no longer valid (#64).
- Improved image viewer responsiveness, especially when used as a render viewer.
- Fixed position of plugs in the NodeGraph when the node gadget was very narrow.
- Made Box nodule positions match internal nodule positions (#608).
- Simplified OpDialogue error display - long error messages are now only visible in the Details view, rather than cluttering up the main window, and potentially making it very large on screen.

#### Scene

- Added a ParentConstraint node (#26).
- Added "includeRoot" plug to GafferScene::SubTree. This means that when choosing /path/to/theNewRoot as the root, the subtree will be output under /theNewRoot rather than /. Previously this was only possible by using an Isolate node followed by a Subtree (#565).
- Added "targetOffset" plug to the Constraint node. This is of most use for offsetting the aim point in the AimConstraint node (#278).
- Fixed bug in copying a node which has an input from an unselected PathFilter.
- Fixed bug in ShaderAssignment node which could cause crashes when querying for acceptable inputs.
- Improved the transform node
	- Added a pivot plug (#156)
	- Added a space plug to specify whether the transform is applied in World or Object space.

#### Image

- Fixed ImageReader problem which caused the green and blue channels of non-float images to be offset horizontally.
- Fixed bug which could cause the OpenColorIO node to output greyscale images.
- Optimised Display node.
- Optimised ChannelDataProcessor::channelEnabled().

#### OSL

- Updated for compatibility with OSL 1.3, 1.4 and 1.5 (master branch).
- Removed unsupported closures from OSLRenderer.
- Added debug() closure support to OSLRenderer to allow the output of multiple values via ShadingEngine::shade(). The closure takes an optional "type" keyword argument to define the type of the resulting output.

#### API

- Added GafferUI.SpacerGadget class.
- Reimplemented GafferUI.Metadata in C++, so it can be used from C++ code as well as from Python.
- Fixed bug in Widget.mousePosition() with GLWidget overlays.
- Fixed GafferScene.ScenePath.isValid() to only consider a path as valid if all parents up to the root exist according to ScenePlug.childNames().
- Added space conversion methods to GafferImage::Format. These are useful for converting between the Cortex and OpenEXR Y-down space to the Gaffer y-up space.
- Fixed GafferImage::FormatData serialisation.
- Removed deprecated ImageView( name, inputPlug ) constructor.  This was being used by old View subclasses which would pass their own input plug and then use setPreprocessor() to insert some conversion network. Subclasses should now use insertConverter(), following the example in GafferImageUITest.ImageViewTest.testDeriving.
- Moved Metadata class from libGafferUI module to libGaffer.

#### Build

- Fixed compilation with GCC 4.4.

0.87.1
======

#### UI

- Constrained slider positions inside range by default (#99). Shift modifier allows slides to exceed range.
- Key modifiers are now correctly updated during drags.
- Fixed PySide incompatibility in Slider.

#### Image

- Added ImageSampler node to GafferImage
- Fixed colour space used for ImageView colour sampling (now in linear space).

0.87.0
======

#### UI

- Added visualisation of clipping colours in the image viewer (#572).

#### Core

- Boxes now export all non-hidden plugs for referencing. Prior to this they only exported "in", "out" and user plugs.
- Fixed unwanted plug promotion when nesting Boxes inside Boxes.

#### Scene

- Fixed Subtree update problem.
- Added enabling/disabling support to SceneTimeWarp and SceneContextVariables.
- Added a SceneSwitch node. This can be used to choose between different scene hierarchies.
- Added a ShaderSwitch node. This can be used to switch between different shaders being fed into a ShaderAssignment. It is also compatible with RenderMan coshaders, so can be used to switch between different coshaders in a network.

#### Image

- Added a Clamp node
- Fixed bug in Display node which caused problems when using multiple Displays at once.
- Added ImageTimeWarp, ImageContextVariables and ImageSwitch nodes - these are equivalent to their Scene module counterparts.

#### API

- Added missing IntrusivePtr typedefs to GafferImage
- Added RecursionPredicate to FilteredRecursiveChildIterator. This allows the definition of iterators which automatically prune the recursion based on some condition.
- Redefined RecursivePlugIterators so that they do not recurse into nested nodes - instead they just visit all the plugs of the parent node.
- Improved Node::plugSetSignal() behaviour. The signal is now emitted for all the outputs of the plug being set in addition to the source plug - otherwise plugSetSignal() could not be used effectively for plugs which had been promoted to Box level.
- Renamed SceneContextProcessorBase to SceneMixinBase.

#### Build

- Fixed build for Ubuntu 12.04.
- Updated public build to use Arnold 4.1.
- Removed OIIO versioning workaround - previously we had to rename the OIIO library to avoid conflicts with Arnold, but since Arnold 4.1 such conflicts no longer exist.
- Updated default boost version to 1.51.0.
- Added dependenciesPackage build target. This can be used to make a package of prebuilt dependencies to seed a build. from.
- Updated default Cortex version to 8.0.0b5.

0.86.0
======

#### UI

- Added exposure and gamma controls to the image viewer (#571).
- Added colourspace management to the image viewer (#573). By default display colourspaces are taken from the OCIO config, but any image processing node (or Box containing them) can be registered via config files to provide alternative methods of colour management.
- Added auto expand option to the scene viewer (#163).
- Added Shift+Down shortcut for full expansion in the scene viewer (#556).
- Added "look through camera" in the scene viewer (#49).
- Added global Left/Right keyboard shortcuts for frame increment/decrement (#52).
- Added background operation to op dialogues in the op and browser apps. The UI now remains responsive during execution and displays IECore messages and results (#591).
- Objects can now be dragged from the Viewer and SceneHierarchy into path fields such as the AimConstraint target or the StandardOptions camera.
- Buttons now accept Return and Enter keypresses in addition to the space bar and clicking.
- Confirmation dialogues now focus the default button so they can be dismissed using the keyboard.
- Tarted up the About dialogue with a nice new logo courtesy of Tiziana Beretta.
- Fixed MenuButton bug whereby menus could be shown partially offscreen.
- Fixed Timeline bugs
	- Wraparound during playback would remove the fractional part of the frame number
	- Entering a value in the frame field which was outside the frame range would make it impossible to subsequently enter a fractional frame number.
    - Changing the frame number via the numeric field didn't update until focus left the field.
- Fixed clipping problem in BusyWidget drawing, and removed overhead of invisible BusyWidgets.
- Fixed GadgetWidget overlay event handling problems.
- Fixed crashes when MultiSelectionMenu was used in GLWidget overlay.
- Viewer toolbar now omits labels when Metadata value is "".
- Made the NodeGraph save and restore its framing when entering and leaving Boxes (#626).
- Fixed PathWidget menu positioning when used as a GLWidget overlay.

#### Scene

- Added a UnionFilter node (#594).
- Optimised SceneReader. It now computes constant hashes where data is not animated, resulting in significant speedups and reduced memory consumption. Approximately 2x speedup and 50% memory usage reduction has been seen in animated production assets (#545).
- Optimised SceneHierarchy update for improved playback performance (#545). 4x speedups have been seen with animated production assets.
- Fixed the laggy node dragging seen after expanding the SceneHierarchy contents and moving the current frame a few times (#209).
- Disabled StandardOptions camera and resolution by default.

#### Image

- Optimised OpenColorIO node performance.
- Optimised grade node performance and memory usage (through improved hash implementation).
- Set Grade node's gamma plug minimum value to 0.
- Fixed threading related OpenColorIO crashes on OS X.
- Fixed ImagePrimitiveSource hashing bug. This would manifest itself as a corrupted image when connecting a disabled node downstream from a Display node (#420).
- Fixed miscellaneous hashing bugs.

#### Core

- Optimised StringPlug::getValue() and StringPlug::hash() for cases where the string doesn't contain substitutions.
- Fixed bug in Path inequality operator.
- Renamed python deprecation warning output - Python2.7 disabled this by default.

#### API

- Added a new Playback class. This provides a central controller for all clients who wish to initiate playback or react when playback occurs.
- Added ColorProcessor base class. This makes it easier to implement image processing nodes which mix across channels.
- DependencyNode::affects() is now called for output plugs too. This can trip up poorly implemented DependencyNode::affects() overrides - see f1e9cb3bf20430b7889795dcb5eccec863f1e2e7 for details.
- Resolved ambiguities in Widget auto-parenting keyword arguments. Parenting arguments should now be passed as "parenting = { ... }" rather than just "...".  The old style of argument passing will be deprecated (#655).
- Added ViewportGadget::set/getCameraEditable() methods.
- Added previous root node to GraphGadget::rootChangedSignal().
- Added set/getTextSelectable() method to GafferUI.Label.
- Added Dialogue set/getModal() methods.
- Added Path._emitPathChanged() protected method.  This can be used by derived classes to emit the pathChangedSignal(), avoiding emitting it if nothing is listening. All subclasses should use this in preference to self.pathChangedSignal()( self ).
- Added Context::hasSubstitutions() method. This can be used to query if a string contains any substitutions supported by Context::substitute().
- Added Slider set/getPositionIncrement() methods. These allows the cursor key position nudging behaviour to be controlled.
- Added const version of GafferUI::View::getPreprocessor.
- Added EnumPlugValueWidget.selectionMenu() method.
- Renamed ImageNode::hash*Plug() methods to hash*(), for consistency with the rest of the framework.
- Refactored ImageNode hashing for improved performance and clarity - see 78b8739f1867ecd3b660838d384cdd6083734d92 for details.
- Added many missing IntrusivePtr typedefs.
- Added support for "divider" Metadata in viewer toolbars.

0.85.1
======

#### Scene

- Compatibility with Cortex 8.0.0b1

0.85.0
======

#### API

- Added Bookmarks API for storing Path bookmarks by application, path type, and category (#55)
 - Configs can define custom bookmarks on startup (https://github.com/ImageEngine/gaffer/wiki/Custom-Bookmarks)
 - Parameters can specify the bookmarks category with a ["UI"]["bookmarksCategory"] user data entry
 - Support in the gui, browser, and op apps
 - Support in File menu, PathChooserDialogue, PathChooserWidget, PathParameter, PathVectorParameter, RenderMan shader parameter, Box, and Reference node UIs
- Added Style::changedSignal()
- Added Window set/getIcon and setting GafferLogoMini as the default window icon
- Added TextWidget set/getPreferredCharacterWidth methods
- Fixed ParameterisedHolder parameterChanged() crashes
- Fixed Widget.bound() on OS X
- Fixed some bugs with null plugs in Box's plug promotion methods

#### GL

- Fixed GLSL shaders used by the UI for OpenGL 2.1 (requires Cortex 8.0.0-a23)
- Fixed OpenGL drawing when embedded in Houdini (requires Cortex 8.0.0-a22)

#### UI

- Added ColorSwatchPlugValueWidget (#625)
- Added new Gaffer logos (though only using them for window icons currently)
- Increased preferred width of PathWidgets (#515)
- Improved PathChooserDialogue handling of invalid selections (#628)
- Fixed Dialogue positioning and focussing on Linux (#220, #642, #62)
- Fixed SectionedCompoundDataPlugValueWidget child widget bugs (#588)
- Fixed Timeline start/end field sizing bug (#111)

#### Scene

- Added DeleteAttributes node and AttributeProcessor base class (#587)
- Fixed PrimitiveVariableProcessor::affects()

#### RenderMan

- Fixed RenderManShader.acceptsInput() crash

#### OSL

- Added closure parameter support to OSLShader

0.84.0
======

#### UI

- Added shift+drag of node to panel to create duplicate editor (#575).
- Added HSV readout for pixel below mouse in image viewer (#576).
- Improved the UI for Attributes and Options, to distinguish between the boolean used to enable a setting and the boolean used to define the value (#65).
- Fixed unwanted scaling of Button images.
- Added a toolbar to the viewer, initially with only a single button for specifying the 3D display style (#114).
- Improved MenuButton menu positioning.
- Fixed bug where searchable menus kept keyboard focus after closing.
- Fixed focus stealing problems apparent in Viewer and NodeGraph. They still take focus on mouse enter, but will not steal focus from text entry widgets (#555, #439).
- Added per-column visibility for CompoundVectorParameterValueWidget. Visibility is specified using the standard ["UI"]["visible"] userData entries on the child parameters which provide the columns (#526).
- Stopped plug controls accepting drags from themselves. This was causing trouble for users who were accidentally dragging and dropping a single line from a PathVectorDataPlugValueWidget onto itself, thus removing all the other lines.
- Added drag start threshold, to make it harder to accidentally start a drag (#593).
- Disabled "Remove input" menu item for read only plugs and uis.
- Disabled Box promotion menus on read only UIs (#604).
- Disabled ganging menu items for read only UIs.
- Stopped standard graph layout reconnecting invisible nodes.

#### Scene

- Prevented rogue connections being made to Shader "parameters" Plug.
- Fixed bugs in computing hashes for transform, object and attributes at the scene root.

#### OSL

- Added support for struct parameters.
- Added shaders for doing basic vector arithmetic.
- Added support for N global variable in OSLRenderer.
- Fixed OSLShader hash bug. Because OSL shaders are the first shader type we've supported where a single shader can have multiple outputs, we weren't taking into account _which_ particular output was connected when computing the hash.
- Prevented vector->color connections for OSLShader nodes. OSL itself doesn't allow such connections so we mustn't either. Also added a vectorToColor shader to help work around the restriction.

#### Documentation

- Started versioning documentation releases - they follow the app release version.
- Changed modifier key styling in documentation content to match that used in interface.
- NodeEditor content expanded.
- NodeGraph content expanded.
- New images.
- New screen grab setups.
- Simplified example light shader.

#### API

- Renamed CheckBox to BoolWidget and added different display modes. CheckBox remains as an alias to BoolWidget for backwards compatibility.
- Added stream insertion operator for GafferScene::ScenePlug::ScenePath.
- Fixed RunTimeTyped declaration for SceneView. It was declared as deriving from View rather than View3D.
- Fixed bug in Widget.widgetAt().
- Added widget overlays to GLWidget. This allows any Widget subclass to be displayed as an overlay on top of the OpenGL contents.
- Added setColumnVisible/getColumnVisible methods to VectorDataWidget.
- Implemented VectorDataPlugValueWidget.setHighlighted().
- Fixed StandardNodeUI.setReadOnly() to properly affect plug labels.
- Implemented setPlug on a SectionedCompoundDataPlugValueWidget.
- Fixed DependencyNode::enabledPlug() python bindings.
- Added python binding for ValuePlug::setFrom().

0.83.0
======

#### UI

- Added support for framing nodes and plugs dragged to the NodeGraph.
- Fixed overzealous pinning of nodes dragged to editors. Specifically, a node dragged from within an editor would be accepted as a pinning-drag into that very same editor. Now a drag must originate from outside the editor to be considered for pinning.
- Stopped GafferUI.Frame from expanding beyond the min/max of its contents. It now behaves like the other containers in this respect. Frames can still expand, but now only when their contents want to. Updated ErrorDialogue for this fix by adding some appropriate Spacers, and updated it to use the newer "with" syntax for building UIs at the same time.
- Added highlighted rendering for frames.
- Added ConnectionPlugValueWidget. This is a fallback widget for plugs that otherwise have no value to display. It shows the input connection to the plug, and provides means of navigation to that input (#130).
- Added post-execution behaviours to OpDialogue. These allow the UI writer, the Op writer or the user to choose whether or not the dialogue should be closed after the Op has executed (#560).
- Fixed PathListingWidget errors when "/" path is invalid.  Invalid root paths occur quite frequently in the SceneHierarchy editor when an invalid filename has been entered in a SceneReader or AlembicReader. Those nodes will still display an error, but the SceneHierarchy now won't output a confusing stacktrace which distracts people from the root cause (#528).
- Added Alt click modifier for selecting upstream nodes in GraphGadget. Alt+Shift click adds all upstream nodes to the selection. Alt+Ctrl click removes all upstream nodes from the selection (#437).
- Fixed launching of external URLs on OS X.

#### Scene

-  Fixed Prune node's forward declarations of lights and cameras. Previously it would not correctly remove the forward declaration for an object whose ancestor had been pruned.
- Added Isolate node type.  This removes all paths which are not directly above or below the chosen location - particularly useful for singling out certain assets from a large scene (#564).
- Improved default values for Seeds and Instancer nodes. The new defaults mean there are less steps to perform to get something happening.
- Stopped annoying startup errors when 3delight or arnold are missing (#486).

#### OSL

- Introduced a new gaffer module which integrates Open Shading Language.
	- OSLShader node represents OSL shaders and allows them to be connected into shading networks.
	- OSLImage node executes OSL shaders in the context of an input image to perform arbitrary image processing.
	- OSLObject node executes OSL shaders in the context of an object's primitive variables to perform geometry deformation.

#### API

- Added custom formatters and name depth control to NameLabel.
- Added Widget.isAncestorOf() method.
- Added ButtonEvent.button field.
- Improved path matching to provide more complete information.
- Added GraphGadget::upstreamNodeGadgets() method.

#### Support apps

- Added ability to specify Widget to be grabbed in the screenGrab app.

####################################################################################################

0.82.0
======

#### Core

- Made Plug::acceptsInput() consider current output connections (#532).

#### UI

- Added even-more-simplified mode to StandardNodeUI (#549).
- Fixed GraphGadget for NULL return from NodeGadget::create(). This allows NodeGadget::registerNodeGadget() to be used with functions that will return NULL to signify that the node should be hidden.

#### Scene

- Fixed errors reading polygon normals from Alembic files (courtesy of Cortex 8.0.0-a18).
- Added MapOffset node for offsetting texture coordinates.

#### RenderMan

- Fixed output of multiple displays (courtesy of Cortex 8.0.0-a18) (#357).
- Added automatic instancing capabilities (courtesy of Cortex 8.0.0-a18).

0.81.0
======

Core
----

- Improved dirtiness propagation mechanism to remove duplicate signal emission.

UI
--

- Backdrop improvements
	- Backdrop contents can now be scaled, so large backdrops can still have readable text when zoomed out.
	- Fixed bug which meant that empty backdrops didn't immediately redraw as highlighted when selected.
	- Improved resizing behaviour.
	- Fixed cut and paste bug.

Scene
-----

- Added doublesided attribute to StandardAttributes node (#275).

Arnold
------

- Fixed packaging of Arnold plugins.
- Fixed problem where light shaders weren't being created as lights.

RenderMan
---------

- Fixed public build to work with older 3delight versions where RiProceduralV isn't available.
- Added support for several new attributes in RenderManAttributes node (#275).

API
---

- The plugDirtiedSignal() is now emitted when a value has been edited with ValuePlug::setValue() - this means that observers need only ever use plugDirtiedSignal() instead of also having to use plugSetSignal() as well.
- Added Style::characterBound(). This returns a bounding box guaranteed to cover the largest character in the font. It is useful for correctly positioning the text baseline among other things.


0.80.0
======

UI
--

- NodeGraph now only drag-selects nodes that are wholly contained in the drag area, not merely intersecting it.
- Added a Backdrop node (#153).

RenderMan
---------

- Added support for "help" shader annotation in RenderManShaderUI (#536). This provides help for the shader as a whole and is mapped into the MetaData as the node description, appearing in the NodeEditor as a tooltip.

API
---

- Added optional continuous update to string PlugValueWidgets, controlled by the continuousUpdate parameters to the constructor. This transfers the text from the ui to the plug on every keypress.

Core
----

- Fixed serialisation of dynamic BoxPlugs.

Documentation
-------------

- Improvements too numerous to mention.

0.79.0
======

UI
--

- Added additional plug types to the CompoundDataPlug new plug menu (#522).
- Fixed bug in searchable Menus with no entries (#527).

Scene
-----

- Added CustomAttributes and CustomOptions nodes. These will be used instead of the old Attributes and Options nodes, and exist to better distinguish their use from the Standard, RenderMan and Arnold options and attributes nodes.

RenderMan
---------

-  Enabled hosting of RenderManShaders inside custom Box classes. Previously it only worked inside Boxes and not classes derived from Box.

API
---

- Added python subclassing ability to Serialisation::Serialiser (#520).


0.78.0
======

API
---

- Added python bindings for signal::num_slots and signal::empty().
- Added Gadget::idleSignal(). This allows Gadgets to do things during the idle times of the host event loop.
- Added NodeEditor.nodeUI() method.
- Added CompoundEditor.editorAddedSignal().
- Enabled subclassing of Box from Python.
- Made RenderManShaderUI public.

Core
---

- Fixed serialisation of ExecutableOpHolder.
- Added dynamic requirement plugs to Executable.
-

UI
--

- Added middle mouse drag for dragging nodules to the script editor without dragging a connection.
- Further increased width of plug labels in NodeEditor (#98).
- Fixed read-only RenderManShader UIs.
- Fixed bug whereby read-only PlugValueWidgets were accepting drags.
- Added Help menu.
- Added NodeGraph auto-scrolling.
- Added support for "presets" parameter type hint.

OS X
----

- Fixed GafferImageUI linking.

0.77.0
======

- Added alignment support and addSpacer method to ListContainer.
- Fixed an update bug in the pixel value inspector (#401).
- Added the pinned status to saved layouts (#444).
- Added read-only mode to NodeUIs and NodeEditor (#414). Note that this currently interacts poorly with activators on RenderManShader node, and will be fixed in a future release.
- Fixed read-only MultiLineTextWidget bugs.
- Implemented tag reading in SceneReader node. Tags are represented as BoolData attributes called "user:tag:tagName" (#494).
- Increased width of plug labels in NodeEditor (#98).
- Improved the default layout to include SceneHierarchy and SceneInspector and Timeline editors.
- Fixed TabbedContainer sizing when tabs not visible.
- Fixed crashes when loading old scripts where coshader array parameters were stored as Compound plugs.
- Fixed propagation of shader hashes through Boxes.
- Allowed shaders to accept inputs from Boxes, even if the Box doesn't currently output a shader.
- Changed internal image coordinate system to have 0,0 at bottom left (formerly at top left).

0.76.0
======

- Added Application._executeStartupFiles() method (#354).
- Added RemoveChannels image node.
- Added a PointConstraint node (#482).
- Fixed framing error when entering a Box.
- Image viewer now displays channels in grey scale.
- Added Widget.widgetAt() method.
- Added ability to hide tabs in layouts.
- Fixed bug converting coshader array from fixed to variable length.
- Added Serialiser::postScript() method.

0.75.0
======

- Added a channel mask feature to GafferImageUI::ImageView. Use the r,g,b and a keys to isolate individual channels (#403).
- Updated for compatibility with Cortex 8.0.0a14.
- Updated screengrab app to allow the execution of a commands file.
- Added a node find dialogue, accessible via the Edit/Find.. menu item (#454).
- Added NodeGraph.frame( nodes ) method. This can be used to frame specific nodes within the viewport of the NodeGraph.
- Addressed thread related hangs when using an InteractiveRenderManRender and deleting or connecting nodes.

0.74.0
======

- Added a multitude of miscellaneous documentation improvements.
- Implemented parameterName.type RenderManShader annotation (#456).
- Implemented parameterName.coshaderType RenderManShader annotation (#460).
- Fixed disabled Shader pass-through bugs.
- Added variable length coshader array support to RenderManShader (#462).

0.73.0
======

- Implemented connection hiding for the NodeGraph. This is accessed by right clicking on a node in the Node Graph and using the new "Show Input Connections" and "Show Output Connections" menu items (#429).
- Fixed const correctness of GraphGadget::getNodePosition().
- Fixed connection drag bug. Dragging the endpoint of a connection around and then placing it back where it started was breaking the connection, whereas it should have been having no effect.
- Replaced Enabled/Disable node menu item with Enabled checkbox.
- Added titles to the node graph context menus.

0.72.2
======

- Fixed Box creation with nested connected plugs. This allows the creation of Boxes with shader nodes with input connections.
- Fixed removal of nodules from nodes in the graph ui when Plugs are removed.
- Fixed InputGenerator bugs and added python bindings and tests.
- Fixed Group bugs involving dynamically generated inputs and undo (#179, #210, #302).
- Tidied up node menu labels.
- Renamed WriteNode to ObjectWriter and ReadNode to ObjectReader (#17).
- Fixed minimum height of ramp editor (#445).
- Fixed empty messages from ErrorDialogue.ExceptionHandler.
- Added popup error dialogues for file save failures (#449).
- Fixed context used by interactive render nodes.

0.72.1
======

- Updated PySide build.
- Fixed bug expanding objects in viewer when a custom variable was needed by the computation (#438).
- Fixed boxing of RenderMan coshaders (#440).
- Fixed Qt 4.6 compatibility.

0.72.0
======

- Added workaround for weird focus-stealing behaviour in Maya.
- Added application variable to the scope available to the screen grab command.
- Added support for empty and relative paths in Gaffer.Path. ( #432, #324 )

    - Added root parameter to all path constructors. This is used to define the root when the path parameter is passed a list of items. Because python doesn't allow overloaded functions this is slightly awkward - see documentation of Path.__init__ for discussion of how this would break down into overloaded constructors when we move the implementation to C++.
    - Added Path.root() and Path.isEmpty() methods.
    - Added Path.setFromPath() method, which copies the elements and the root from another path. This should be used in place of code which formerly did path[:] = otherPath[:].

    Note that the new root parameter changes the parameter order for all Path (and derived class) constructors - if you were formerly passing a filter as a non-keyword argument you should now pass it as a keyword argument to avoid problems. Additionally, if you implemented a custom Path subclass, you need to add the root parameter to your constructor and update your copy() and children() implementations. The DictPath changes provide a minimal example of what needs changing.

0.71.0
======

- Variable substitution improvements
	- Added standard ${script:name} variable (#407)
	- Added custom script-wide variables accessible via the File->Settings menu (#407)
	- Added support for variable references within variables (recursive substitution)
	- Added environment variable and ~ substitution
	- Added standard ${project:name} and ${project:rootDirectory} variables.
- Fixed save and load of ReadOnly plugs.
- Removed Escape hotkey for leaving full screen mode. The same function is served by the ` hotkey.
- Defined default locations for ribs, ass files and rendered images.
- Added automatic directory creation for display, rib and ass locations (#59)
- Added GraphComponent::clearChildren() method
- Greyed out File->RevertToSaved menu item when it doesn't make sense
- Improved CompoundDataPlug data representation
- CompoundPlugValueWidget using PlugValueWidget.hasLabel() to avoid unecessary labelling
- Fixed UI for promoted plugs (#264)
- Fixed bug where deleted children of Boxes weren't removed from the selection (#430)
- Fixed bug where pinned nodes were still visible in the UI after being deleted (#308)
- Fixed hangs caused by adjusting colours while rerendering
- Tidied up some test cases

0.70.0
======

* Added Ganging for CompoundNumericPlugs (#402)
* Added menu item for loading renderman shaders from file (#125)
* Added color ramp editing support (#286)
* Added spline parameter support to RenderManShader::loadShader()
* Added shader annotations for passing default values to RenderManShader splines
* Added dividers in the NodeEditor, available to RenderMan shaders via the annotation "parameterName.divider" (#288)
* Added API for undo merging.
* Added ScriptNode::undoAddedSignal() (#103)
* Fixed hiding of Menu when using the search box
* Fixed tab focus ordering in NodeEditor (#107)
* Improved GadgetWidget focus behaviour (#119)
* Fixed redundant CompoundNumericPlug serialisation (#2)
* Fixed scrubbing of values for IntPlugs
* Fixed size issues caused by TabbedContainer size policy (Settings and About window)
* Fixed bug in Random::affects()
* Fixed multiple undo entries in virtual sliders, cursor up/down nudging, color choser, and ramps (#400)
* Fixed Ctrl+C copy shortcut in non-editable MultiLineTextWidgets
* Hid Shader enabled plug in the UI (#398)

0.69.1
======

* Fixed bug with top level actions breaking searchable menus
* Fixed node reconnection crashes in ScriptNode::deleteNodes and StandardGraphLayout::ConnectNodeInternal

0.69.0
======

* Implemented drag and drop between plugs in the NodeEditor (#285)
    Drags are initiated on the label for the plug.
    Left drag initiates a drag for connecting plugs.
    Shift-left drag and middle drag initiate a drag for transferring values between plugs.
    Colours may now also be dragged from the viewer onto a plug.
    There are custom pointer icons for each type of drag (#44)
* Added blinking indication for plugs preventing the opening of a colour picker (#185).
* Implemented enabling/disabling for shader nodes (#327).
    By default disabled shaders behave as if their output connections didn't exist.
    RenderMan shaders may act as a pass-through by defining a "primaryInput" annotation naming an input coshader parameter.
* LinkedScene files (.lscc) are now previewable in the browser
* ImageReader only reads the necessary channel from the OpenImageIO cache
* Reverted non-gui ExecutableRender::execute() to block until the render is complete (#353).
* Fixed Nuke link error
* Fixed browser op mode
* Fixed missing Recent Files bug (#378).
* Fixed some bugs with extraneous dragBegins
* Removed namespace prefixes from typenames for displaying to the user (#389).
* Removed deperecated ModelCacheSource

0.68.0
======

* Improved speed of renderman shader menu.
* Image stats node in ImageView now uses the preprocessed input plug if the raw input is not an ImagePlug
* Removed right-click layout context menu.
* Added "Unpromote from Box" item to plug popup menu.
* Fixed menu title so it doesn't interfere with menu keyboard navigation.

0.67.0
======

* Fixed potential lockup with NumericPlugs.
* Fixed RenderMan ShaderMenu match expressions (broken in 0.66.0)
* Reintroduced the node name into the NodeEditor header.
* Exposed LayoutMenu submenu callable publicly.
* Implemented in-place renaming for user plugs (#213).
* Added support for RSL "parameterName.label" annotation (#372).
* Added a MapProjection node.
* Added sample window to the ImageViewer.
* Fixed UI test cases broken by the per-application menu commits.
* Can once again build for OS X.
* Added support for packaging as .dmg on OS X.

0.66.0
======

* Fixed interactive display.
* Fixed APIs to make UI resources per-application. When applications are updated to use these new APIS, they will no longer pollute each other's interfaces (#351, #225).
* Refactored GafferImage::Filter to have a better interface whilst removing the need for the construct() method.
* Added python bindings and enhancements for the GafferImage::Filter class.
* Fixed hash() bug in RenderMan coshader, which in turn fixes an interactive rerendering bug.
* Reduced occurences of accidental connection snatching (#313, #325).
* Fixed escape-to-close menu bug.
* Added an ImageStats node.
* Fixed deadlock when writing image files to disk.
* Op. Procedural and RenderMan shader menus may now be filtered to show fewer options.
* Added "cmd" parameter to screen grab app.
* Fixed GafferImage::FormatPlug::hash()
* Fixed duplicate typename errors (#330).
* Prevented promotion of non-serialisable plugs to Box level (#347).
* Fixed a bug in ImageProcessor that was causing a segfault when the node has an output that is not an ImagePlug.

0.65.0
======

* Added divisions plug to Plane node.
* Added Cube and Sphere scene sources (#97).
* Added a Text node to GafferScene.
* Added labelling support to TabbedContainer auto-parenting mechanism.
* Added ImageViewer pixel inspection by dragging pixels to the script editor (#245).
* Added python bindings for Views (#323).
* Added screengrab app.
* Implemented Gaffer->About menu item (#6).
* Improved ImageView to allow subclassing (#323).
* Set the name attribute for lights properly in the Render node (#326).
* Fixed GLWidget for use inside Maya 2013.
* Fixed Recent Files menu bug (#333).
* Fixed a bug in ViewportGadget drag event propogation.

0.64.0
======

* Added support for displaying RenderMan shader color parameters as plain numbers. This can be achieved by setting the "parameterName.widget" annotation to a value of "number".

* Added support for RenderManShader array parameters, including arrays of coshaders.

* Fixed redraw issue in searchable menus.

0.63.1
======

* Using Boost Filesystem version 3 (for compatibility with Cortex 8)

0.63.0
======

* Fixed promotion of dynamic colour plugs to Boxes.

* Fixed crash creating Merge node (#253).

* Fixed Gaffer module dependency on GafferImage.

* Display now obeys the default format (#280).

* Fixed circular references in plug popup menus.

* Fixed NumericWidget dragBegin errors.

* Newly created nodes are now connected in-stream where possible (#257).

* Fixed editability of user plugs.

* Added error handling for bad RenderManShader activator annotations.

* Improved automatic placement of filter nodes (#86).

* Fixed empty tab creation in Node Editor.

* Added interactive search for node menu.

* Reordered image filters so that they are displayed from most soft to most sharp.

* Added the Lanczos image filter.

* Fixed a bug with the Sinc image filter.

* Fixed the "streaking" issues when using the ImageTransform.

* Added subpixel filtering to the image Sampler.

* Implemented snapping during Graph Editor drags.

* Optimised node dragging in the Graph Editor.

0.62.1
======

* Fixed gl sharing widget bug when launching gaffer in maya

* ExecutableRenderer now always launches the render asynchronously to avoid locking the maya UI

0.62.0
======

* Fixed bug with promotion of CompoundPlugs to Boxes.

* Fixed ImageNode paste error (#251).

* Fixed BoolPlugValueWidget._updateFromPlug() to avoid setting plug value (#266).

* Fixed bug in Group operation (#269).

* Implemented RenderMan shader parameter activation via annotation expressions (#226).
    An activator is defined by a global annotation of this form :
        pragma annotation "activator.name.expression" "pythonExpression"
    The python expression may reference current parameter values by name, and also use the connected( "parameterName" ) function to query whether or not a parameter is connected.
    Activators are then assigned to specific parameters using annotations of this form :
        pragma annotation "parameterName.activator" "name"

* Implemented annotation-based uis for RenderManLight node.

* Added a ComputeNode class, and refactored DependencyNode so it can be a useful base class for shaders as well.

* Fixed dirty propagation of Shaders through ShaderAssignments.

* Fixed 3delight workaround. GafferRenderMan now requires 3delight 10.0.138 or newer.

* Added rudimentary shader updates to InteractiveRender. Note that there are still problems whereby deadlocks sometimes occur so this isn't in a state where you'd want to bet the success of any public performances on it.

* Fixed an issue with the glBlendingMode that was causing the result to be pre-multiplied twice.

* Fixed an image rendering issue with data/display window mismatches.

* Fixed banding and dark edges evident in 2D viewer (#74).

* Improved speed issues when moving single nodes in the NodeGraph by refactoring GraphGadget::connectionGadgetAt (#283).

0.61.0
======

* Fixed bug in MultiSelectionMenu so that if only one selection is available, it is displayed by name rather than as "All".

* Added image Sampler and Filter API classes.

* Added an image Reformat node.

* Added an ImageWriter node.

* Added RecursiveChildIterator API class.

* Fixed noodle-snatching to work with Shader nodes.

* Node Graph label now uses "/" as a separator for Box paths, rather than ".".

* Fixed layouts to allow panels to be collapsed fully and smoothly - addresses issue #93.

* Added workaround for PyQt/PySide pyqtSignal/Signal differences.

* Fixed "CameraController not in motion" errors. These occurred when the user accidentally moved the mouse scroll wheel while performing a drag to move the camera. We now ignore wheel events when dragging the camera.

* Removed unecessary collapsible section in Group UI.

* Fixed ImageReader to work with offset data windows.

* Fixed node auto-connection to work with Shader nodes (and other nodes with nested plugs).

* Added auto-connection and auto-positioning for pasted nodes (#13).

* Added inherit argument to Metadata query functions (#232).

* Fixed negative data window origins in image module.

* Added subdivision attributes to ArnoldAttributes node.

* Renamed Assignment node to ShaderAssignment.

* Added Reference node, providing the ability to reference in external scripts to facilitate collaborative workflows (#228).

* Added popup plug labelling to the NodeGraph (#138).

* Added connection snapping to the NodeGraph - connections dragged onto a node will snap to the nearest compatible plug.

* Added ImageTransform node (#96).

0.60.0
======

* Expansion state of collapsible plug grouping is now remembered for the duration of a session (#87).

* Current tab in Node Editor is now remembered for the duration of a session (#87).

* Fixed a bug in the NodeGraph where setTitle() was having no effect.

* Slowed wheel zooming (#200).

* Fixed crash when dragging nodes (#211).

* Improved NodeEditor node labelling (#151).

0.59.0
======

* Fixed save/load of user plugs created via the UI (#174).

* Fixed UI for generic Options and Attributes nodes.

* Removed collapsibility of Transform node's transform plug as it just cluttered up the UI.

* Removed collapsibility of Attribute node's attributes plug as it just cluttered up the UI.

* Removed collapsibility of Lights node's parameters plug as it just cluttered up the UI.

* Fixed MeshType::affects() (#175).

* Fixed SceneInspector update (#176).

* Improved SceneInspector shader representation (#147).

* Improved SceneInspector numeric formatting (#88).

* Added drag and drop node connection re-wiring (#78).

* Added virtual slider for NumericWidgets, engaged using LeftClick + Control or ShiftControl (#79).

* Fixed dirty propagation for Light nodes.

* Added first implementation of interactive rerendering in the InteractiveRenderManRender node. (#141)

* Deleting nodes attempts to rebuild the network to act as if the deleted nodes had been disabled (#95).

* Viewports can be panned/tracked using middle mouse with no modifier key (#28).

0.58.0
======

* Fixed creation of nodes within Boxes - previously they were added below the root of the script rather than inside the box.

* Fixed unstable scene hierarchy expansion (issue #120).

* Fixed highlighting bugs whereby widgets inside a highlighted tab would incorrectly display an inherited highlight state. This could be seen when dragging a node into the node editor with either nested tabs or a nested VectorDataWidget.

* Fixed PathPlugValueWidget bug where it would attempt to change the value of a read only plug.

* Fixed PathWidget bug where it would still do autocompletion and popup menus even when non-editable.

* Added TabbedContainer.insert() method.

* Generalised the Metadata system to store arbitrary values rather than just descriptions.

* Fixed CompoundPlugValueWidget bug whereby it would error if a summary was provided on a non-collapsible UI.

* Added right-click context menus to enum and checkbox plug uis.

* Added Box plug-promotion feature (#142).

* Removed Gaffer.GroupNode (#164).

* Fixed ordering of parameters in RenderManShader UI (#136).

* Fixed banding and dark edges evident in 2D viewer (#74).

* Fixed awkward zooming of Viewers and NodeGraph (#46).

0.57.0
======

* Renamed ColorPlug child names to rgba rather than xyzw (issue #133).

* File->SaveAs... menu item now adds the file to the recent files list.

* Fixed unwanted vertical expansion of color plug widgets.

* Removed the unwanted visualisation of the "name" plug on shaders in the Node Graph.

* Added NodeGraph plugContextMenuSignal() and connectionContextMenuSignal() to allow customisable right click menus for plugs and connections (issue #122).

* RenderManShader annotations are now correctly reloaded when the shader itself is reloaded.

* RenderManShader UI produces more sensible errors when bad annotations are discovered.

* Fixed parameter ordering in RenderManShader UI (issue #136).

* Fixed bug which prevented numeric plug entry fields from showing the correct value when values outside the allowable range were entered.

0.56.0
======

* RenderManShader node now supports the use of annotations within the shader to define the node UI. Annotations follow the OSL specification for shader metadata.

* Added the GafferUI.Metadata class, which will be used to provide things such as node and plug descriptions for the generation of tooltips and reference documentation.

* Added a Prune node, for removing whole branches from a Scene (issue #70).

* The Menu class now supports the description field of menu items, displaying descriptions as tooltips.

* The Menu class now supports the passing of the menu to callables registered as subMenus.

* Added a "File/Open Recent" menu item (issue #118).

* Added the ability to reload RenderManShader nodes, updating them to reflect any changes to the shader on disk. This is done automatically on file load and can be performed manually at any time using the new button in the node editor.

0.55.0
======

* Fixed graphical glitches caused by icons overlapping the edge of the editors on the Gnome desktop.

* SceneProcedural now renders general VisibleRenderables too.

* Fixed SceneReader to read animation at the correct speed (issue #68).

* File->Quit and the window close icon now prompt the user to confirm before closing if there are unsaved changes (issue #19).

* Added support for shader parameters of type "shader" in the RenderManShader node - these are mapped to plugs which accept connections to other RenderManShaders, allowing the creation of networks of coshaders.

0.54.0
======

* Added base classes Executable and Despatcher and two derived Node classes: ExecutableNode and ExecutableOpHolder.

* Added an enabled/disabled plug to all SceneNodes. Nodes with no inputs output an empty scene when disabled, and SceneProcessors output the first input unchanged. The enabled/disabled state can be toggled using the node right click menu or the "d" hotkey in the Graph Editor.

* Added SceneNode::hash*() methods to match the GafferScene::compute*() methods. This was necessary for the enabled plug to be implemented, and also makes the implementation of derived classes more readable. Matching pairs of hash*() and compute*() methods should be reused as a pattern throughout Gaffer where appropriate in the future.

* Renamed SceneElementProcessor::process*() methods to SceneElementProcessor::computeProcessed*() and SceneElementProcessor::hash*() methods to SceneElementProcessor::hashProcessed*(). This was necessary to resolve conflicts with the name hash*() methods at the SceneNode level.

* Removed the ability to return distant descendants from the GraphComponent::getChild() function. Also modified GraphComponent method signatures to use InternedString where appropriate. This change alone gives a 10-15% speedup in evaluating a benchmark GafferScene network.

* Added GraphComponent::descendant() method to replace the lost functionality in GraphComponent::getChild().

* Fixed bug whereby ViewportGadget sent keyReleaseSignal() to the keyPressSignal() of child Gadgets.

* Added Style::renderLine() method.

* VectorDataWidget now supports InternedStringVectorData. This makes it possible to view InternedStringVectorData in the browser app.

* Fixed errors caused by trying to view a SceneReader with an empty filename.

* The currently active tab for each panel is now saved with each layout.

* Renamed GraphEditor to NodeGraph - the previous name was confusing to users. Renaming all the classes rather than just changing the label, because we want a fairly straightforward mapping from UI->API to help users make the transition into scripting.

* Multiple shortcuts may now be specified for each menu item by passing a comma separated list of shortcuts in the "shortCut" field of the menu item.

* EditMenu now uses both backspace and delete as shortcuts for the delete action.

* Double-clicking a node in the Node Graph now makes any Node Editor tabs editing that node visible by making them the current tab.

* The ` key (left of the 1 on the keyboard) may now be used to toggle in and out of fullscreen mode.

* Renamed SceneEditor to SceneHierarchy to be more explicit that it visualises the scene graph and doesn't really provide much in the way of editing.

* Renamed TimeEditor to a more user friendly Timeline.

* The File->SaveAs... menu item now ensures that the file saved always has a ".gfr" extension.

* Added Scene->Object->Modifiers->MeshType node for converting meshes between polygons and subdivs, and optionally adding normals when converting to polygons.

* The Scene Inspector now displays mesh interpolation.

* Fixed bugs which could prevent the UI updating appropriately when plug values were changed.

* Optimised redundant updates in the SceneHierarchy editor.

0.53.0
======

* Added the concept of a global format for disconnected nodes along with a format plug.

* Added the Constant node for GafferImage.

* Added the Select node for GafferImage.

* Fixed a bug which prevented Assignment nodes from being connected to Shaders outside the Box containing the Assignment.

* Improved formatting in NumericWidgets.

* Added NumericWidget.valueChangedSignal().

* Fixed bug where editing a numeric plug value using cursor up/down didn't immediately update.

* Added CompoundDataPlug::addMember() and CompoundDataPlug::addOptionalMember() overloads which take a ValuePlug instead of Data to provide the value for the member.

0.52.0
======

* The Gaffer clipboard now synchronizes with the global system clipboard, allowing nodes to be cut and pasted between external applications.

* Fixed a bug which meant that the Viewer didn't update if a view became dirty while it wasn't the currently active view.

0.51.0
======

* Switched Arnold import in ArnoldRender.py to a deferred import, to allow 3delight renders of scenes containing Arnold nodes

* Added a Grade node to GafferImage

* Added a Merge node to GafferImage

* Added option to disable highlight in GafferUI.Button

* Fixed exception caused by undefined subMenuDefinition in GafferUI.Menu

* Catching all exception types in ErrorDialogue

* Image nodes can now be disabled.

* Renamed ExpressionNode to simply Expression.

* Multithreaded the ImagePlug class.

* Fixed ParameterValueWidget.create() so that it always returns either None or an instance of ParameterValueWidget. Previously it was returning PlugValueWidget instances where no specific ParameterValueWidget registration had been made.

* Added PlugValueWidget setReadOnly/getReadOnly methods. These can be used to force a ui to be read only when the plug itself allows editing. Note that they can not be used to force editing when the plug itself is not editable.

* Fixed BoolPlugValueWidget so that it correctly disables the checkbox if the plug is not writable for any reason, or is setReadOnly( True ) has been called.

* PlugValueWidget.popupMenuSignal() now passes the PlugValueWidget itself to slots rather than the Plug as it did before. The plug can retrieved by calling plugValueWidget.getPlug().

* ParameterValueWidget.popupMenuSignal() now passes the ParameterValueWidget itself to slots rather than the ParameterHandler as it did before. The parameter handler can be retrieved using parameterValueWidget.parameterHandler().

* Added readOnly parameter to ParameterisedHolderNodeUI constructor.

* ParameterValueWidget now requires that the topLevelWidget passed to the constructor is always an instance of PlugValueWidget. This is made available via a new plugValueWidget() method.

* CompoundPlugValueWidget now requires that the result of _childPlugWidget either derives from PlugValueWidget or must have a plugValueWidget() method which returns a PlugValueWidget. This allows it to implement a new childPlugValueWidget() method which can be used to get access to the widget for a child plug. This is building towards a time when the NodeUI class provides a single method for retrieving the PlugValueWidget for a given plug.

* Added ValuePlug::settable() method.

* The VectorDataWidget now allows tooltips to be specified on a per-column basis using the columnToolTips argument to the constructor.

* The CompoundVectorParameterValueWidget now constructs tooltips for the columns using the descriptions for the child parameters.

* Added drag support to PathListingWidget and VectorDataWidget.

* ViewportGadget now forwards the keyPress and keyRelease signals to its child.

* GadgetWidget now allows the viewport to be changed using setViewportGadget(), and the previous viewportGadget() accessor has been renamed to getViewportGadget().

* ParameterisedHolder now calls the parameterChanged() methods of the classes held by ClassParameters and ClassVectorParameters when their parameters change, rather than calling the method on the top-level parameterised class.

* CompoundPlugs now accept input CompoundPlugs with more plugs than necessary, provided that the first N input child plugs match the N child plugs of the output. This allows Color3fPlugs to receive input directly from Color4fPlugs and arnold COLOR3 parameters to receive input from arnold COLOR4 outputs.

* ArnoldOptions node now allows the specification of texture, shader and procedural searchpaths.

* ArnoldRender node no longer specifies procedural location using a full path, allowing the procedural searchpath to be used if it has been set by an ArnoldOptions node.

* Fixed crash when evaluating a ContextProcessor containing an entry with an empty name.

* Added CompoundDataPlug::addOptionalMember(). This works as for addMember(), but adds an additional BoolPlug to allow the user to enable/disable that member. Both methods also take an additional parameter to specify the name of the plug used to represent the member.

* ArnoldOptions and ArnoldAttributes nodes now create their plugs with sensible names, and allow options and attributes to be enabled and disabled - by default they are all disabled.

* Added a File/Settings... menu option which opens a window for editing the plugs of the ScriptNode.

* Gaffer::CompoundDataPlug now handles Color4fData.

* Added a GafferScene::OpenGLAttributes node for controlling the drawing of objects in OpenGL.

* Gaffer::TypedObjectPlug::setValue() now references the value directly rather than taking a copy.

* Fixed bugs which prevented the ColorChooser working with colour types with an alpha channel.

* Added a procedural app for visualising Cortex procedurals.

* Plug::getInput() now returns a raw rather than reference counted pointer.

* Added RenderableGadget::selectionBound() method which returns the bounding box of all selected objects.

* Added View::framingBound() method which can be overridden by derived classes to control the framing behaviour when "F" is pressed.

* SceneView now frames the current selection when "F" is pressed.

* IndividualContainer::getChild() now returns raw pointers rather than smart pointers and uses a direct method of indexing.

* Gadget::getToolTip() now takes a line in gadget space, allowing the tooltip to be varied with the position of the mouse.

* RenderableGadget implements getToolTip() to display the name of the object under the mouse.

* PathMatcher is now editable after construction, with addPath() and removePath() methods. Because of this the copy constructor also now performs a full deep copy which can be expensive.

* Added PathMatcherData to make sharing PathMatchers easy, and to introduce the possibility of storing them in Plugs and Contexts. Copying is lazy-copy-on-write which can be used to avoid the expensive PathMatcher copy constructor where possible.

* Added Context::names() method.

* EditorWidget._updateFromContext() is now passed a set containing the names of items changed since the last call to _updateFromContext().

* Fixed bug which caused PathListingWidget.selectionChangedSignal() to fire far too frequently.

* Added a GraphLayout class, used in conjunction with the GraphGadget to perform automatic node connections and graph layout. This replaces ad-hoc code from NodeMenu.py. Still needs a decent fully automatic layout implementation for situations where the user doesn't build the graph manually.

* Added Plug::source() method.

* Added GraphGadget::nodeGadgetAt() method.

* GraphGadget now uses middle mouse drag for sending nodes to other widgets - left mouse drag is for moving nodes only. Shift drags can be used to add nodes to the current selection.

* TabbedContainer switches tabs automatically on drag enter, to allow drags to access targets that aren't current at the start of the drag.

* Expression node now supports calls to context.getFrame() and context.get() in addition to context["name"] dictionary style access. The get( name, defaultValue ) method is particularly useful when an expression may be executed in a context without the required entry.

* ScriptEditor no longer displays the result of execution if the result is None.

* Replaced RenderCamera node with more general StandardOptions node, which will define all the render globals type stuff that can be shared between renderers. Fixed bug in hash computation of GlobalsProcessor. Removed resolution from camera, putting it on the StandardOptions node instead.

* CompoundPlugValueWidget can now display a summary of the plug values in the collapsible header. Used this to provide useful summaries for all options and attributes nodes in GafferScene. Renamed in OpenGLAttribute plug for consistency with the others.

* Fixed SceneEditor bug which meant that items were only displayed if the first selected node contained them.

* Added TransformPlugValueWidget which provides a useful summary of the transform in the collapsible header.

* Added ScenePlug::fullAttributes() method which returns the full set of inherited attributes at a particular scene path.

0.36.0
======

* Improved bindings by removing macros and replacing them with proper wrapper classes.

* Added Window.childWindows() method.

* Added initial (and limited) support for Parameterised::parameterChanged() methods. Currently only modifying parameter values is supported in parameterChanged() - support for modifying user data and presets will be added in later revisions.

* The input and output connections for selected nodes are now drawn highlighted.

* Added BlockedConnection class in C++. This handles the blocking and unblocking of connections in an exception-safe manner.

* Added Node::plugFlagsChangedSignal().

* Added Plug::ReadOnly flag, to allow plugs to be locked against modification of the input or value.

* Added support for ["gaffer"]["readOnly"] bool parameter user data, mapping it to the Plug::ReadOnly flag. This user data may be modified in a ParameterModificationContext or in a Parameterised::parameterChanged() callback.

* StringPlugValueWidget and PathPlugValueWidget now correctly set their text entry field to read only when the plug is read only.

* PresetsOnlyParameterValueWidget now displays in a disabled state when a plug is not writable.

* Fixed C/C++ Object already deleted test messages caused by DeferredPathPreview.

* Fixed lifetime issues with ScriptWindows - they may now be constructed directly or acquire()d directly and their lifetime will be as expected (managed by the caller). ScriptWindow.connect() continues to operate as before - managing the lifetime of windows to correspond with the lifetime of scripts in the application.

* Fixed problems caused by serialising plug flags as All - they would then acquire new values when loaded in a future where there are new flags available.

* Added a SubTree node, for taking a branch of the tree and rerooting it back to /.

* Fixed bug in ConnectionGadget::bound() which meant that sometimes the graph would not be framed correctly when first displaying a GraphEditor.

* Fixed ColorChooserDialogue to actually use the colour passed to the constructor.

* Window.addChildWindow() now always causes the child window to remain on top of the parent. Previously, this was documented as the behaviour, but it only worked for child dialogues which subsequently went into a modal state. This is achieved by setting the QtCore.Qt.Tool window flag - this is much better than WindowStaysOnTopHint because it hides the child window when the application becomes inactive on the mac - otherwise the window would remain on top of the windows for the newly activated application.

* Fixed bug where colour chooser would remain after the parent swatch died, but be inoperative. It now remains but is still functional.

* Added GafferScene::PathMatcher class, which provides accelerated path matching for use in the PathFilter.

* PathFilter now supports * as a wildcard to match any portion of a name.

* PathFilter now supports ... as a path entry, to match any number of entries.

* Added a ParameterPath class for navigating Parameter hierarchies.

* Fixed bug which prevented CompoundVectorParameters from being saved in presets.

0.35.7
======

* Fixed bug which caused Windows to be hidden when being added as the child of another Window.

* Window.setVisible( True ) now ensures that the Window is unminimized and raised where necessary.

* Added NodeEditor.acquire() method, to allow other UI elements to request that a Node editor be shown in some way for a specific node.

* Double clicking a node in the graph now shows a floating Node Editor for that node.

* Added MultiLineTextWidget.dropTextSignal(), making it easy to implement drag and drop for different datatypes. This simplifies the ScriptEditor implementation somewhat.

* Added an improved ui for editing expressions. Context menu on plugs allows for creation and editing of expressions, and the expression editor accepts drag and drop of plugs.

* Random node no longer errors when context items are missing - this prevents the UI from erroring when scene:path etc is not available.

* NumericSlider now allows specification of hardMin and hardMax values to control what happens when the slider is dragged outside of the widget area.

* Slider now draws the position differently to indicate when the position is outside of the widget area.

* Fixed ColorChooser bugs caused by dragging sliders outside of sensible ranges - the ranges are now enforced.

* Added GafferUI.DisplayTransform class for managing colour transformations from linear to display space. Updated ColorSwatch and ColorChooser classes to use this, and added ocio.py config file to set up the transform using PyOpenColorIO.

* Added GafferUI.ExecuteUI module with functionality for executing nodes, repeating previous executions etc. This provides a new execute menu in the main menu, and a right click menu item in the graph editor.

* Fixed bug which meant that dynamic CompoundNumericPlugs would fail to restore their connections upon script load.

* Arnold shaders may now be connected together to form networks, and they may have non-shader inputs (such as the Random node) which can be evaluated on a per-object basis to provide additional variation.

* Fixed error caused by browser preview tab.

0.35.6
======

* Fixed problem where VectorDataWidget would grow to claim size it couldn't use.

* VectorDataWidget now scrolls to show the new rows when rows have been added.

* RenderableGadget now implements click and drag signal handlers to manage a set of selected objects.

* Fixed bug where MultiLineTextWidget would emit textChangedSignal whenever setText was called, regardless of whether or not it made any changes.

* Added insertText, setCursorPosition, getCursorPosition, cursorPositionAt, setFocussed and getFocussed methods to MultiLineTextWidget.

* ScriptEditor now accepts drops for scene objects, plugs, and nodes, which can be dragged from the Viewer and the GraphEditor.

* Added Widget.parentChangedSignal(), which does what you'd expect from the name.

* Improved default sizing for OpDialogue.

* Fixed CompoundParameter UIs to respect the ["UI"]["collapsed"] user data entry.

* CompoundPlugValueWidget now has a collapsed constructor argument to replace the previous collapsible argument. This takes None, True or False as values, allowing the ui to be created as non-collapsible, collapsed or expanded.

* Disallowing null values in plugs. This fixes bugs in the computation of hashes (all null values hashed the same, regardless of type, or what the actual default value was), and also simplifies coding (no more need for tests against null before using an Object).

* Fixed bug where setting SplinePlug to a value with less points than before raised an Exception.

* Fixed bug where SplinePlug::setToDefault did not work as expected.

* Added ValuePlug::setCacheMemoryLimit() and ValuePlug::getCacheMemoryLimit(), to allow management of cache memory usage. Added startup/gui/cache.py to expose this to the user via the preferences.

* Fixed bug which prevented user preferences from loading.

* Improved drawing of very thin/small selection boxes - they had a tendency to disappear before.

* Added Widget setHighlighted() and getHighlighted() methods, implementing highlight-on-hover for buttons and sliders.

* Implemented drop of items into VectorDataWidget. This allows objects from the viewer to be dragged and dropped into a filter to perform assignments.

* PlugValueWidget.popupMenuSignal now passes the PlugValueWidget to slots instead of the Plug.

* Fixed bug where ColorPlugValueWidget would attempt to show colour pickers for non-editable plugs, resulting in errors.

* NodeUI now also shows output plugs. They can be removed as necessary by registering None with PlugValueWidget.registerCreator().

* ModelCacheSource now uses the new ModelCache class provided by Cortex.

* Added a Random node, for producing random floats and colours based on a seed and a context item.

* Fixed bug where plug popup menus tried to edit plugs which were not editable.

* Fixed bug where the effects of TextWidget.setEditable() did not update the appearance of the widget.

* Fixed bug which caused ExpressionNode to crash when the expression was changed while the output plug was being viewed by the UI.

* Fixed bug which caused errors when connecting compatible children of CompoundPlugs together, if the CompoundPlugs were not themselves compatible enough for a complete connection between all child plugs to be made.

* Fixed bug which prevents ExpressionNode from accepting a Plug with direction()==In as an input to the expression.

* Fixed bug whereby GadgetWidget was passing buttonDoubleClick signals to buttonPress signals on the held gadget.

* Added GraphEditor.nodeDoubleClickSignal().

0.35.5
======

* Fixed graphical glitches caused by incorrectly applying visibility to children of TabbedContainer - this affected the preview section of the browser app particularly badly.

* Added a reportErrors parameter to the OpMatcher constructor - this defaults to True (same behaviour as before) but can be set to False to silence error reporting while loading ops. Note that the OpMatcher used by the BrowserEditor may be customised by implementing the Mode._createOpMatcher() method - this would be the place to pass reportErrors=True.

0.35.4
======

* Added a GafferBindings::NodeClass class, which simplifies the binding of Node derived classes. It is now a one liner to bind a typical extension node.

* The op app now has an arguments parameter which can be used to specify the parameter values for the op.

* The op app now has a gui parameter. When this is true a gui is presented, when it is false the op is executed directly on the command line.

* Added the GafferScene and GafferSceneUI modules. These will allow the generation and editing of scene graphs.

* Fixed RunTimeTyped registration of Gaffer::CompoundPlug.

* Fixed behaviour when a Widget doesn't have a tooltip - it now correctly looks for tooltips on parent Widgets until one is found.

* Added a GafferUI.NumericSlider widget.

* The Viewer now correctly updates when the context has changed. The EditorWidget no longer calls _updateFromContext() at awkward times.

* Added a simple TimeEditor for manipulating the current frame.

* Fixed GIL problems caused by passing multithreaded python procedurals to RenderableGadget.

* Fixed GIL problems when emitting signals with python slots from a thread which does not currently hold the GIL.

* Added an ExpressionNode class.

* PlugValueWidgets now have setContext and getContext methods, and update correctly when the context changes if a plug has input connections.

* Added a Gaffer.TransformPlug class, for specifying transformations.

* Removed NodeUI.createPlugValueWidget() registeredWidgets only parameter.

* Added PathListingWidget setPathExpanded, getPathExpanded, setExpandedPaths, getExpandedPaths and expansionChangedSignal methods.

* Added the GafferImage and GafferImageUI modules, for tile based image processing.

* Removed deprecated StandardNodeGadget::acceptsNodule() method, and associated StandardNodeGadget( node, deferNoduleCreation ) constructor. Nodule creation should now be controlled entirely by the Nodule factory mechanism.

* The Application base class now automatically creates an ApplicationRoot and makes it available via the root() method. Derived classes should use this rather than create their own. The Application base class now also makes sure that all startup files have been executed before the application is run, so derived classes may not now call _executeStartupFiles themselves (it is now protected). Additionally the doRun() method has
been renamed to _run, to be more in keeping with general python philosophy.

* The WeakMethod class now throws a more useful exception when called on expired instances.

* Fixed bug whereby menus were never destroyed due to a circular reference. This masked other bugs whereby some uis weren't maintaining a reference to their menus to keep them alive - it's now essential that this is done.

* Fixed bug which prevented dynamic output CompoundNumericPlugs serialising correctly.

* Fixed problems caused by PlugValueWidget.__init__ calling _updateFromPlug() at a point when the derived class is not fully constructed. PlugValueWidget.__init__ no longer calls _updateFromPlug(), so derived classes should now call it at the end of their __init__ method.

* ColorPlugValueWidget now has numeric fields for editing the colour, in addition to the
swatch.

* ContainerGadget can now add padding around the children, accessed using the new setPadding() and getPadding() methods.

* StandardNodeGadget can now be used in a vertical orientation as well as a horizontal one. This will be useful for making graphs which better suit a horizontal flow (shaders for example).

* Fixed IECore::RunTimeTyped registration for CompoundNumericPlug types.

* Added GafferArnold module.

* Added Label.linkActivatedSignal(), for reacting to HTML links in label text.

* Fixed flickering caused by MenuBars appearing briefly on screen before being parented.

* Added MultiLineTextWidget setWrapMode, getWrapMode, appendHTML, linkAt and linkActivatedSignal methods.

* Added a PopupWindow class.

* Fixed the Slider button press handler to swallow the events it uses.

* Added Window setPosition() and getPosition() methods.

* Moved NodeUI.registerPlugValueWidget() functionality into PlugValueWidget.registerCreator().

* Removed NodeUI._build() method. Derived classes should instead pass a topLevelWidget to the constructor if they wish to be in control of the ui construction.

* GafferUI.EventLoop now disables any idle callbacks which error during execution.

* Added Node::acceptsInput virtual method, to allow nodes to reject connections.

* Added a Widget.bound() method.

* Added GadgetWidget.positionToGadgetSpace() method, for converting Widget-relative positions into Gadget-relative lines.

* Added a GraphEditor.graphGadgetWidget() method.

* Nodes created via the NodeMenu are now automatically connected to the selected nodes, and positioned based on those connections.

* Parameter help for CompoundParameters (and derived classes) is now available as a tooltip on the label of the Collapsible ui.

* The op application now has an arguments parameter, which can be used to specify the initial values for the parameters of the op (backported from trunk).

* The python application now has an arguments parameter, which can be used to specify an arbitrary list of strings to be provided to the python script in a variable called argv.

* VectorDataWidget now allows a minimum number of visible rows to be passed in the constructor. Previously a similar behaviour was implemented internally with the minimum hardcoded to 1 - the new default is now 8. This improves the layout of CompoundVectorDataParameters.

* Added workaround for Qt problems which caused VectorDataWidget to sometimes be clipped on the right hand edge.

0.35.3
======

* Fixed LayoutMenu delete function

0.35.2
======

* Added a minimum size of the OpDialogue

0.35.1
======

* Removed ParameterValueWidget._addPopupMenu and _popupMenuDefinition, replacing them with PlugValueWidget._addPopupMenu and _popupMenuDefinition. This makes the parameter preset menus automatically available on all parameter uis, and provides for easy extension in the future (menus for manipulating plug inputs, expressions, locking etc). Note that if you previously had a custom ParameterValueWidget class with a _popupMenuDefinition() override, then it will no longer work - use ParameterValueWidget.popupMenuSignal() instead.

* Removed ToolParameterValueWidget, replacing it with ToolPlugValueWidget which has identical functionality (but applicable to Plugs too).

* Fixed bug which caused the filename column to become too wide when switching to Op browsing mode in the browser and then back to files.

0.35.0
======

* Sequence Path displays file sequences with a single frame

* Reverted changes made in Widget class about "apply visiblity"

* OpDialogue now supports op.userData()["UI"]["buttonLabel"], for specifying a custom label for the OK button.

* Removed requirement of the boost build having a patched python library capable of participating in garbage collection.

* Fixed bug in Collapsible when calling setChild() with a widget currently parented elsewhere.

* Fixed various GafferUI.Container bugs which prevented successful transfer of Widgets between containers.

* Added workarounds for unwanted Qt behaviours - parentless Widgets becoming top-level windows, and widgets being hidden when reparented.

* Added setClassLoader and getClassLoader methods to the op application. These may be used by configuration files to customise the loading of ops (the application is available as an "application" variable to the startup scripts).

* Calling BrowserEditor.registerMode() with the label of an existing mode now overrides the previous registration, rather than adding a second with an identical name.

* The standard BrowserEditor modes are now accessible publicly as BrowserEditor.FileSystemMode, BrowserEditor.FileSequenceMode and BrowserEditor.OpMode.

* The browser OpMode now takes an additional classLoader argument to the constructor, allowing the use of custom class loaders.

* The ParameterValueWidget.registerType() method now accepts an optional uiTypeHint argument, which allows the registration of custom uis, which parameters can request using the standard ["UI"]["typeHint"] userData entry.

* Added ValueType class members to TypedObjectPlug bindings, so that appropriate values
can be constructed easily.

* GraphComponent.children() python method now accepts a typeId to filter the result.

* Fixed bug which meant that colour swatches for plugs had the wrong colour when first shown.

* Simplified EditorWidget implementations by removing setScriptNode() method - now the scriptNode is always provided at construction and cannot be subsequently changed. Renamed ScriptWindow.getScript() to ScriptWindow.scriptNode() and EditorWidget.getScriptNode() to EditorWidget.scriptNode() for consistency.

* Menus now support a "shortCut" entry in the MenuItemDefinition to provide keyboard shortcuts. The standard application, file and edit menus now provide the expected shortcuts, and are greyed out appropriately when they cannot be used for whatever reason.

* Added ScriptNode undoAvailable() and redoAvailable() methods.

* CompoundNodule now supports a vertical orientation, specified using a new argument to the constructor.

* GafferUI.LinearContainer now supports decreasing as well as increasing child ordering, controlled with the setDirection() and getDirection() methods.

* Fixed ordering of nodules in vertically oriented NodeGadgets.

* PathPlugValueWidget doesn't update the plug value as you type any more - this was causing constant computation with invalid values. The value is now only set when editing finishes.

* Fixed problems with PathChooserWidget which meant the wrong file/directory was displayed on opening (truncated by one).

* ParameterValueWidget popup menus may now be customised by external code, using the ParameterValueWidget.popupMenuSignal().

* The Path class now implements a much more readable __repr__.

* The DictPath class now accepts an additional "dictTypes" argument to the constructor, which can be used to define what types it considers to be branches in the path (all other types are considered leaves).

* The OpMatcher.defaultInstance() function now takes an optional classLoader argument, which is used to create the shareable OpMatcher.

* The BrowserEditor.Mode class now has a _createOpMatcher() method which may be overridden by derived classes. Typically this would be overridden to use a custom ClassLoader for the ops.

* Moved Label.VerticalAlignment and Label.HorizontalAlignment enums to GafferUI namespace - to allow their use in other parts of the API. They are temporarily available under their old names for backwards compatibility.

* GridContainer.addChild() now accepts an alignment parameter to control alignment of the child within its cells.

* Path setFromString, append and truncateUntilValid methods now return self, to allow easy chaining and use in list comprehensions.

* Fixed problem which could cause MultiLineTextWidget to raise an Exception when losing focus as part of a ui being destroyed.

* Fixed SelectionMenu so that standard python strings (and not QStrings) are returned from the getCurrentItem() and getItem() methods.

* Added support for loading and saving presets for ops and other Parameterised classes.

* The OpPathPreview is now more flexible in what it considers to be a ClassLoader for ops, to provide better support for custom ClassLoaders.

* The PathListing widget now allows multiple levels of hierarchy to be expanded, by holding either Shift (all levels) or Control (one level) while expanding a level. In addition, expansionChangedSignal() is not emitted only once for batched changes, such as those caused by setExpandedPaths() and the new recursive expansion/collapsing.

* Layouts now remember their correct splitting ratios when they're saved. Added a useful layout for use with scenes.

* The ExpressionNode now supports string as well as numeric output types.

* The execute app now operates over frame ranges defined using the -frames command line argument.

* When not in gui mode, the Render node waits for the render subprocess to complete before returning from execute().

* StringPlug inputs now automatically substitute $name, ${name} and ### tokens using values from the current context when their value is accessed during a computation. This behaviour can be controlled using the new PerformsSubstitutions plug flag.

* Node computations are now cached in memory and reused when possible. Hashes representing computations are available using the ValuePlug::hash() method, and Node implementations must now implement the new Node::hash() method to assist in computing hashes.

* Added GraphComponent::getChild( childIndex ) method, providing constant-time access to children by index. This improved the implementation of SplinePlug, ChildSet and the GraphComponent __getitem__ method in Python.

* The op application now supports the loading of presets at launch, using the new "-preset presetName" command line option.

* Added a simple ConfirmationDialogue class.

* Presets are now stored in subdirectories based on class name, to avoid clashes between presets for different classes.

* Added a small UI for deleting presets.

* Resolved browser errors caused by broken symlinks. FileSystemPath now returns True for isValid() if a path is a broken symlink (it seems unreasonable for children() to return invalid paths) and falls back to os.lstat() to generate path info if os.stat() fails due to a broken link.

* Fixed problem where SequencePath would error in info() when given an invalid base path. Now it returns None as expected.

0.34.0
======

* Added support for ClassVectorParameters.

* Added a -help flag to the gaffer command line.

* Fixed parameter menu bug introduced in version 0.33.2.

* Added support for TimeCodeParameters.

* Menu.popup() method now takes an optional grabFocus parameter - if this is False and a key is pressed then the menu will close and pass the key to the previous focus widget.

* PathWidget's helpful popup menus are now more helpful because they don't steal keypresses from the PathWidget itself.

* TextWidget now supports having a fixed width defined in characters using the setCharacterWidth() and getCharacterWidth() methods.

* NumericPlugValueWidget now sets maximum field width for integer plugs where max values has been set - this slightly improves the ui for the TimeCodeParameterValueWidget.

0.33.2
======

* Fixed the delete order of ListContainer that was causing popup windows

* Fixed circular reference in menu that was causing popup windows

0.33.1
======

* Fixed bug in Menu

0.33.0
======

* Added a MenuButton class to GafferUI.

* The GafferUI.Spacer class now specifies a maximumSize in addition to the previous minimumSize.

* Added support for ClassParameters.

* Improved formatting of Parameter tooltips, and worked around Qt crash caused by having "\n\n" in the tooltip text.

* Fixed bug which meant that Labels were always aligned to the right and centre. Note that this changes the behaviour of default constructed Labels, which have always specified left alignment, but have been ignored till now.

* ListContainer now supports slices when setting children. For instance container[2:4] = [ list, of, children ]. ListContainer also now implements the index() method in the same way a list would, and allows access to the expand attribute of children using the new setExpand() and getExpand() methods.

* Improved WeakMethod behaviour when called after the instance has expired. Now a descriptive ReferenceError exception is thrown rather than the previous cryptic exception. Also added instance() and method() member functions to return the underlying member data.

* GafferUI.Menu now allows WeakMethods to be used for the command field of a menu item.

* Improved file selector for PathVectorParameters, and added custom file selector for FileSequenceVectorParameters.

* Fixed problem where the automatic Widget parenting mechanism was attempting to parent Menus unnecessarily.

0.32.1
======

* Added workaround for problems where string values were not always committed into parameters before the Execute button of the OpDialogue was clicked.

0.32.0
======

* Added GafferUI.NotificationMessageHandler, for displaying IECore messages in a little window.

* Added a ParameterHandler and ParameterValueWidget for DateTimeParameters.

* VectorDataWidget size behaviour now works much better for large amounts of data. It is now possible to use the browser's FileIndexedIO preview tab to view large amounts of data
from .cob and .fio files.

* Fixed bug in VectorDataWidget, whereby the vertical header would disappear when rows were deleted.

* Multiple fields may now be edited simultaneously in the VectorDataWidget, by selecting several fields before editing one of the selected fields. Changes are automatically copied to the rest of the selection. Columns may be selected by clicking on the horizontal header
and rows by clicking on the vertical header.

* The enter and return keys can now be used to edit the checkbox fields of a VectorDataWidget.

* The MultiLineTextWidget now has setEditable, getEditable, textChangedSignal, editingFinishedSignal and activatedSignal methods equivalent to the existing methods on TextWidget.

* Added a MultiLineStringPlugValueWidget class.

* StringParameterValueWidget now supports the ["UI"]["multiLine"] user data item.

* The browser app now has an "initialPath" parameter to allows the browsing location to be set from the command line.

* Added Gaffer.AttributeCachePath and GafferUI.AttributeCachePathPreview classes, to allow browsing of attribute caches.

* Browsing for paths from a PathPlugValueWidget where the path is presumed empty now starts from the current working directory.

0.31.0
======

* Fixed getText method of Label widget.

* TextInputDialogue now has all text in the textfield selected by default.

* Fixed "RuntimeError: underlying C/C++ object has been deleted" error triggered by removing a panel from a ScriptWindow.

* Fixed bug which meant that removing a panel would only keep a single subpanel of the panel that remained.

* Fixed bug which meant that sometimes the remaining layout buttons would cease to work after removing a panel from the CompoundEditor.

* PathListingWidget now has a displayModeChangedSignal() method.

* Added PathChooserWidget setPath() and getPath() methods.

* Added customisable modes to the BrowserEditor. Current modes allow the browsing of either files or ops.

* Added Gaffer.SequencePath class and used it to implement a file sequence browsing mode for the BrowserEditor and a FileSequenceParameterValueWidget.

* Added PathListingWidget setColumns() and getColumns() methods.

* Added a Gaffer.OpMatcher class, to provide lists of ops which are suitable for application to particular objects.

* Added a contextMenuSignal() to the Widget class.

* Added a right click menu to the BrowserEditor, allowing suitable ops to be applied to
files and file sequences.

0.30.0
======

* Fixed problem trying to call QLineEdit.setPlaceholderText within Nuke.

* Gaffer.BlockedConnection now supports reentrancy, with the connection only becoming unblocked when the outermost block has been exited.

* Fixed bug which prevented selection using the up/down cursor keys from working in the PathChooserWidget.

* ImageGadgets now have a linear to srgb conversion applied when they are drawn. This means they now match the Image widget behaviour.

* PathChooserWidget and PathChooserDialogue now accept a new allowMultipleSelection argument to the constructor. Use the new PathChooserDialogue.waitForPaths() method to wait for paths selected in this way.

* VectorDataWidget has a new protected _createRows() method which may be overridden by derived classes to customise the addition of new rows. The PathVectorDataWidget implements this by displaying a dialogue where the user may select multiple paths to be added. This improves the parameter ui for PathVectorParameters.

0.29.0
======

* The Gaffer.BlockedConnection constructor now accepts a list of connections to block, as an alternative to just a single connection.

* Added a Gaffer.LeafPathFilter class, which filters out leaf Paths.

* Fixed problem with Dialogue.waitForButton() which meant that the keyboard focus would be in the wrong place if a parent window was provided.

* PathListingWidget now supports user resizing of the columns. The existing automatic resizing behaviour remains, but any changes made by the user are remembered and applied as offsets to future automatic resize events.

* PathListingWidget.Column.lessThanFunction has been replaced with PathListingWidget.Column.sortFunction. The former was a function to compare two items, whereas the latter now simply returns the data in a form that should be passed to a standard less than comparison.

* Added PathListingWidget.selectionChangedSignal().

* Added PathListingWidget.scrollToPath() method.

* PathListingWidget now supports a tree view mode in addition to the existing list mode. This is exposed in the PathChooserWidget and PathChooserDialogue via a button to toggle between the modes.

* Deprecated PathListingWidget.selectedPaths() and introduced a pair of getSelectedPaths()/setSelectedPaths() methods.

* Added the ability to remove children from the TabbedContainer using del[start:end] notation.

* Added GafferUI.EventLoop.executeOnUIThread().

* Added Gaffer.DictPath, to allow browsing of dictionaries, IECore.CompoundData and IECore.CompoundObjects using the GafferUI Path components.

* Added GafferUI.BusyWidget, for saying "i might be some time but i don't really know how long so just twiddle your thumbs please".

* Fixed bug in GafferUI.Frame.removeChild.

* PathListingWidget now copes if a field in the Path.info() is missing.

* Added a Gaffer.IndexedIOPath class, to allow browsing inside Cortex files using the GafferUI Path components.

* GafferUI.EventLoop in Houdini mode now pumps 5 times rather than once per hou.ui.eventLoop idle. This makes typing in text fields interactive.

* GafferUI.TabbedContainer now has setTabsVisible() and getTabsVisible() methods.

* Added a frame() method to GafferUI.GadgetWidget, to frame a particular bounding box in the viewport, and fixed a bug whereby setGadget() didn't request a redraw.

* Added setPath and getPath methods to PathListingWidget, and PathWidget.

* Added setPathCollapsed and getPathCollapsed to PathListingWidget to allow programmatic control of the tree view.

* Added Gaffer.ClassLoaderPath class to allow browsing of ops and suchlike.

* GafferUI.SplitContainer.setSizes() can now be called before the SplitContainer has become visible.

* Added GafferUI.ErrorDialogue.ExceptionHandler class to simplify error handling.

* Added classes for previewing paths. General file information, headers, images, meshes, ops, and indexed io files and contents may all be previewed.

* Added a BrowserEditor class for embedding a file browser into a Gaffer layout.

* Added a browser app to browse the filesystem and display previews.

* Renamed ScriptNode::application() method to ScriptNode::applicationRoot() and changed return type to a raw pointer in keeping with the rest of Gaffer. Added python binding.

* Added ApplicationRoot::preferencesLocation() method to return an appropriate directory into which settings can be saved.

* Added Widget.visibilityChangedSignal().

* Fixed crash in python bindings for TypedObjectPlug::defaultValue, for the case of the default value being null.

* TypedObjectPlug bindings now support the serialisation of the value and default value, provided that the bindings for the types they hold implement __repr__ appropriately.

* Fixed bug in GafferBindings::Serialiser which meant that serialisers were called twice unecessarily.

0.28.1
======

* Changed the default resize mode of OpDialogue/ErrorDialogue to be manual

* Removed assert warning

* Fixed juddering resize events when opening the OpDialogue, by optimising out unecessary calls in Widget.setVisible().

0.28.0
======

* Added an InfoPathFilter, which allows filtering with an arbitrary match function applied to an arbitrary field of Path.info(). Used this to implement a filter text box for path choosers.

* PathParameterWidget now applies path filters, and has an _filter() method which can be overridden in derived classes to define the filter.

* GridContainer now supports the automatic parenting mechanism

* Window now support the addition of child windows using the automatic parenting mechanism.

* Keyword arguments can now be passed to the ContainerWidget.addChild() call generated by the automatic parenting mechanism. To properly support this, all Widget subclasses must take a **kw constructor argument, and pass it to their parent class constructor. An example use follows :

	with GafferUI.GridContainer() :
		# index is automatically passed to GridContainer.addChild() to specify the position of the button
		GafferUI.Button( "myButton", index = ( 0, 2 ) )

	with GafferUI.ListContainer() :
		# expand is automatically passed to ListContainer.addChild()
		GafferUI.Spacer( IECore.V2i( 10 ), expand=True )

* Added the ability to easily profile any gaffer application using the cPython profiling module, by specifying the -profileFileName command line flag. Use the pstats module to examine the resulting file.

* Optimised the Widget event filter.

* Fixed circular reference in GafferUI.CompoundParameterValueWidget which could cause "Underlying C/C++ object has been deleted" errors.

* The displayFunction in GafferUI.PathListingWidget.Columns may now return a GafferUI.Image or (as an optimisation) a QtGui.QIcon.

* Added GafferUI.PathListingWidget.defaultFileSystemIconColumn, which can be added to the list of columns passed to GafferUI.PathListingWidget to obtain an icon view.

* Optimised Widget implementation so that the event filter is only applied when it is absolutely needed - either when a connection to one of the signals has been made or when getToolTip has been overridden. Investigations with the standard gaffer ui revealed that only about one third of widgets meet these criteria.

* Optimised Widget implementation by lazily constructing signals when they are first accessed. This improves construction times but also reduces the memory footprint of a freshly constructed Widget by 40%.

* Added Gaffer.lazyImport function, which imports modules in such a way that they aren't actually loaded until first accessed.

* Optimised startup of gaffer applications which don't use any GL functionality, by using the new Gaffer.lazyImport functionality for PyOpenGL, IECoreGL and QtOpenGL.

* Added buttonDoubleClickSignal() to GafferUI.Widget and GafferUI.Gadget.

* Added setSelection() and getSelection() methods to GafferUI.TextWidget, along with a selectionChangedSignal() method. An additional selectingFinishedSignal() uses heuristics to determine when the user has finished making a selection. This is useful in Widgets which wish to provide easy methods of acting on the selection.

* The Menu.popup() method now takes optional position and forcePosition arguments.

* Improved PathWidget popup listing behaviour.

* GafferUI.ScrolledContainer now always asks for enough size to completely show its contents, regardless of the scroll mode in use.

* Deprecated GafferUI.Window setResizeable() and getResizeable() methods in favour of new setSizeMode() and getSizeMode() methods. These provide three modes - Manual (the same as the previous resizeable), Fixed (the same as the previous non-resizeable) and Automatic, whereby the window always tries to fit its child. Added a resizeToFitChild() method for cases where sizeMode is not Automatic and you know the child has been resized.

* The OpDialogue now resizes automatically to fit the parameters initially, and adjust as parameter sections are shown and hidden.

* The Widget class now has a keyReleaseSignal, and the GadgetWidget propagates events on this signal to the existing Gadget::keyReleaseSignal.

* Added support for "label" attributes in menu definitions to GafferUI.Menu. This is really just a workaround for the fact that IECore.MenuDefinition uses / characters to delineate between menu entries, and sometimes we want a / in the entry name itself.

* The VectorDataWidget now sizes itself to fit its contents.

0.27.0
======

* Keeping the same font dpi no matter where gaffer is running.

* Fixed bug which caused NameError to be thrown when loading a script containing an OpHolder.

* NodeUI widgets can now be customised on a per-plug basis using the NodeUI.registerPlugValueWidget call.

* Fixed bug which could cause crashes if a plug managed by VectorTypedParameterHandler had a null value.

* Fixed bug which caused additional parameters1, parameters2 etc plugs to be created on the ReadNode. Added an additional test to check that the ReadNode works following serialisation.

* Implemented keys(), values(), items() and __getitem__( long ) for GraphComponent bindings.

* Added a simple Write node.

* Added an execute application which can be used to execute Write nodes, or any other node with an execute() method.

* The Gaffer headers are now installed in the include directory in the Gaffer distribution.

* The Cortex procedural stubs are now installed as part of the Gaffer distribution.

* GafferUI.TabbedContainer now has an index() method for retrieving the index of a given child, and a currentChangedSignal() method for signalling when the current tab has been changed.

* GafferUI.NodeSetEditor now has a nodeSetChangedSignal() method, to notify listeners when the node set the editor is using has changed.

* GafferUI.CompoundEditor now houses a couple of useful buttons alongside the tabs in the layout. One brings up the menu to edit the layout, and the other locks the currently viewed nodes for the current editor.

* Added Serialisable flag to Gaffer.Plug, to control whether or not plugs and their values are serialised.

* The gui app now has a fullScreen command line flag.

* NodeEditor now displays the node type.

* The Plug base class may now be serialised.

* Fixed bug which meant that plug flags were not correctly serialised.

* Fixed bug in the automatic Widget parenting mechanism, which meant Widgets could be parented inappropriately when being created from the constructor of another Widget.

* The Path.addFilter() and Path.removeFilter() methods have been deprecated and replaced with Path.setFilter() and Path.getFilter() methods. Use the new CompoundFilter class if you wish to use more than one filter.

* The Path and FileSystemPath constructors now accept an optional filter argument.

* The PathFilter class now has setEnabled() and getEnabled() methods to turn the filter on and off. Derived classes should now implement the _filter() method rather than the filter() method.

* The PathFilter class now has a changedSignal(), which issues notifications when the filter is changed in some way. The Path class uses this to correctly trigger its own pathChangedSignal()

* The PathFilter classes now accept a dictionary userData argument to the constructor, which can be used for storing arbitrary data with the filter.

* The CheckBox class now has setText() and getText() accessors.

* Added PathFilterWidget class to allow uis to be built for the filters on paths. Added filter ui to PathChooserWidget, along with a button to refresh the listing.

* The Path class now adds "name" and "fullName" entries to the info() dictionary.

* The Menu class now accepts booleans as well as callables for the checkBox MenuItemDefinition entry.

0.26.0
======

* Gaffer.Application._executeStartupFiles() now takes an optional contextDict to allow variables to be passed to the startup scripts.

* GafferBindings.Serialiser now has a public constructor and can be used directly. It still needs some refactoring.

* Gaffer.ApplicationRoot now has a preferences() method which returns a node used to represent preferences. It also has a savePreferences() method to save the user preferences into a startup script. The GafferUI.ApplicationMenu
provides access to this via a menu item.

* Default stylesheet now does a better job of aligning the corner widget for the TabbedContainer.

0.25.0
======

* Changed in NumericPlugValueWidget the methods __keypress and __textChanged to be protected

* Added alternate color as new entry in widget style sheet

* The GafferUI.Image class now uses a more sensible cache size to eliminate thrashing when loading images from disk. The cache size defaults to 100 MB but can be specified directly using the GAFFERUI_IMAGECACHE_MEMORY environment variable, which is also interpreted as being a number in MB.

0.24.0
======

* ParameterisedHolder now correctly loads an instance of the held class
following serialisation.

* ParameterisedHolder::setParameterised() and OpHolder::setOp() now accept
an optional keepExistingValues parameter which defaults to false. Passing
true preserves existing plug values in preference to the values in the
incoming Parameterised object.

* TabbedContainer now allows the addition of a custom Widget to the top
right corner using the setCornerWidget() and getCornerWidget() methods.

* Fixed a bug which meant that the ButtonEvent::line field was incorrectly
transformed when delivering events to Gadgets.

* Fixed tab sizing issue on OS X.

* Fixed crashes in ObjectParameterHandler triggered by plugs with null values.

* Added enterSignal(), leaveSignal(), dragEnterSignal() and dragLeaveSignal() methods to Gadget. Nodules now highlight themselves when entered using this
new functionality.

* Fixed GafferUI to work with qt 4.6 as well as 4.7.

* Gaffer can now be run embedded in Nuke.

0.23.0
======

* Fixed a bug which prevented keypresses in GadgetWidget from being propagated to the parent widget if they were not processed by the GadgetWidget.

* Can now exit full screen mode by hitting Escape.

* OpDialogue.waitForResult() now never returns Exceptions if execution fails. Instead it gives the user the chance to try again or cancel.

* CompoundParameterValueWidget and CompoundVectorParameterValueWidget now support the ["UI"]["collapsible"] and ["UI"]["collapsed"] parameter userData. The collapsible argument to the constructor now defaults to None, it can be specified explicitly as True or False to override the userData request.

* Fixed a bug which prevented the GafferUI.Widget owner for empty QTabWidgets from being found with PyQt4. This caused errors during event handling.

* The Widget.setVisible() and Widget.getVisible() methods have been modified to match the behaviour of Widget.setEnabled() and Widget.getEnabled(), and an addition Widget.visible() method has been introduced to query visibility relative to an ancestor. See documentation for further details.

* Added SplitContainer getSizes(), setSizes() and handle() methods. See documentation for details.

* ListContainer.__init__() orientation parameter now defaults to vertical.

* CompoundEditor now provides dynamic behaviour for expanding and collapsing child editors. Hit space to expand the current editor one level, double space for two levels and so on. Space then collapses back one level, double space two levels and so on. When an editor is fully collapsed, hovering over the splitter handle will dynamically show it.

0.22.1
======

* Changed events keyPress and textChanged to be protected

0.22.0
======

* Collapsible Widget now supports corner widget expanded

* Changed Error Window to be resizable as default

* Added selectedSignal in SelectionMenu

* Added CurrentIndexChangedSignal test in SelectionMenuTest

* Fixed StringParameterValueWidget to create a PlugValueWidget using the registered Type

* Added enterSignal and leaveSignal in Widget


0.21.0
======

* Added a selectionMenu widget.

* Stylesheet restructured, enabling style overrides in widgets.

* Improved stylesheet performance applying styles only in Window and Menu widgets.

* Buttons can optionally have the frame removed using the setHasFrame() method or the hasFrame argument to the constructor. Additionally they no longer have minimum sizes defined by the stylesheet.

* Minor style changes.

* Disabled Qt's automatic merging of menubars with the OS X system menu. This was causing crashes and wasn't compatible with fullscreen mode either.

* Added a simple ProgressBar widget.

* Removing a node from a parent using removeChild() now automatically disconnects the node from the graph. Fixes issue #38.

* Fixed a number of test failures which occurred only in the Image Engine build, due to the fact that we install the cortex ops with different version numbers than a standard install.

* CompoundParameterValueWidget now updates the ui appropriately when plugs are added and removed. This can be seen in the Read node when switching between different file types.

* File menu items now open file browsers in a more sensible location.

* File browser now has a button to go up one directory level.

* Containers may now be used in the python with statement to make the creation of nested layouts more straightforward. For example :

	with GafferUI.Collapsible() :
		with GafferUI.ScrolledContainer() :
			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical ) :
				GafferUI.TextWidget( "Making uis is easier now" )
				GafferUI.Button()

* Nodule::registerNodule now accepts regular expressions for plug names.

* StandardNodeGadget::acceptsNodule is deprecated. Use Nodule::registerNodule in preference. Default implementation of StandardNodeGadget::acceptsNodule now always returns true.

* Graph editor ui for ParameterisedHolders now only shows connections for ObjectPlugs, this prevents the interface being cluttered with connections for all the other parameter types.

* Viewer is no longer hardcoded to display the result of the "output" plug - it now displays the result of the first output ObjectPlug. This allows it to view the results of procedurals and ops.

* The node creation menus for Ops and Procedurals now create OpHolder and ProceduralHolder nodes rather than generic ParameterisedHolder nodes. Ops and procedurals may now be run in Gaffer.

0.20.0
======

* GafferUI.EventLoop supports Houdini using hou.ui.addEventLoopCallback

* Support for boost 1.37.0

* Using future to import with_statement for python 2.5 compatibility

0.19.0
======

* Added a BoolVectorDataPlug and a BoolVectorDataParameterHandler.

* GafferUI._Variant.fromVariant() now supports booleans.

* VectorDataWidget now accepts a list of VectorData objects to the constructor and in setData(). This allows larger tables to be constructed consisting of columns from several VectorData objects. As a result VectorData.getData() always returns a list of objects, even when operating on only a single object. VectorDataWidget now accepts custom header labels specified by passing a list of strings to the header parameter in the constructor.

* Using an officially allocated TypeId range, and not one that might conflict with internal projects.

* CompoundValueParameterWidget can now be usefully subclassed, and the _buildChildParameterUIs method reimplemented to change behaviour.

* Added a CompoundVectorParameterValueWidget.

* Fixed a bug in GafferUI.Menu which prevented dynamically generated submenus from displaying correctly.

* Plugs representing parameters are now correctly identified as being dynamic, and can therefore be saved and loaded to scripts. Custom ParameterHandler classes should now call setupPlugFlags() in their setupPlug() implementation to support this behaviour.

* Added OpHolder and ProceduralHolder node types. The ui still needs work to make these useable.

* Fixed problem which caused artifacts in GafferUI.Images when using PySide.

* Reduced default font size to fit more on screen.

* Fixed problem with GafferUI.Button positioning on OS X.

0.18.0
======

* Renamed ArrayNodule to CompoundNodule.

* Bug fix for PathListingWidget with allowMultipleSelection==True. When selecting more than one item, the path being edited is now always set the current directory. This avoids problems where setting the path to the last selected leaf could cause the current selection to be destroyed.

0.17.0
======

* Fixed a bug in NumericPlug::setValue() which meant it was possible to set value outside the Plug's min/max range.

* Changed ParameterHandler interface to allow the same ParameterHandler instance to be used repeatedly even when Parameters are being added and remove or are changing type. This should be more efficient but more importantly will be necessary to allow the CompoundParameterValueWidget to adjust the ui when Parameters are edited in this way. The following changes need to be made to a ParameterHandler implementation :

	* Remove the plugParent argument to the constructor, and move the plug creation code to an implementation of the new setupPlug() pure virtual function.
	* Stop passing the parameter to the base class constructor, but instead store it as a member variable, and implement the pure virtual parameter() method to return it.

See python/GafferTest/ParameterHandlerTest.py for an example.

* The path argument to the PathPlugValueWidget is now optional, with a FileSystemPath being used if no path is specified.

* ValuePlug now emits plugSetSignal() before calling Node::dirty(), rather than vice versa.

* The ReadNode now exposes the parameters of the IECore::Readers it uses as plugs on the node.

* The PathListingWidget contents can now be customised by passing a column specification to the constructor. See PathListingWidget.defaultFileSystemColumns for an example. Also added support for sorting the listing by clicking on the headers, and allowed the column specification to provide a sorting function to be used in this case.

* The PathListingWidget now allows multiple selection of files using the allowMultipleSelection argument to the constructor, and provides a list of the currently selected paths using the selectedPaths() method.

* Implemented the ParameterisedHolder::setParameterised( className, classVersion, searchPathEnvVar ) overload. Still needs some work so nodes can be serialised to a script and reloaded properly.

* Fixed a bug in the Node bindings which meant that the C++ base class implementations weren't called when a python class didn't provide overrides.

* ParameterHandler::setupPlug now takes an argument specifying the plug direction required.

* Added an ObjectParameterHandler.

* Added Widget setEnabled(), getEnabled() and enabled( relativeTo ) methods - see documentation for details. Signals are not emitted for Widgets which have been disabled.

* Fixed a bug in the RunTimeTyped registration for TypedPlug.

0.16.0
======

* Added a StandardNodeGadget::acceptsNodule() method which may be reimplemented by derived classes to control exactly which plugs are represented by the gadget. See GafferUITest.StandardNodeGadgetTest.testSubclassing() for an example.

* GafferUI.StringPlugValueWidget now exposes the internal TextWidget with a textWidget() method.

* GafferUI.TextWidget now supports password style text display, settable with the displayMode constructor parameter, or the setDisplayMode() method.

* New StringParameterValueWidget supports ["UI"]["password"] parameter userData.

* The appearance of disabled buttons is now less confusing.

0.15.1
======

* Fixed layout problems caused by adding larger items into existing rows of a GridLayout.

0.15.0
======

* Added a GridContainer class.

* Fixed bug which meant that connections were temporarily offset from their endpoint if a nodule was added to a node immediately after them being made (as the Group node does).

* Fixed bugs in the GroupNode which meant that compute() was called each time the node was moved in the GraphEditor, and that compute() could error if an input plug contained None.

* Gaffer can now be run embedded in maya versions which use Qt natively.

0.14.0
======

* The parameter userData ["UI"]["visible"] is now supported.

* Fixed failing test GafferTest.ParameterisedHolderTest.testAddAndRemoveParameters. Parameters may now be added or removed within a ParameterisedHolder::ParameterModificationContext.

* Fixed a few stylesheet issues that appeared when running under Gnome.

* Added a GraphComponent::setChild() method - this operates in the same way as the __setitem__ python method. See documentation for the distinction between addChild() and setChild().

* Fixed a bug whereby GraphComponent::getChild( "" ) would return the GraphComponent itself rather than nothing.

* Fixed a bug dealing with parameters changing type within a ParameterisedHolder::ParameterModificationContext.

* GraphComponent::parentChangedSignal() now also provides the previous parent to connected slots in addition to the child argument.

* Fixed a bug where transferring a child from one parent to another would emit parentChangedSignal() twice, once with the child unparented from the old parent, and once with the child reparented to the new parent. Now the signal is only emitted once, omitting the bogus temporary unparenting signal.

* Plugs now automatically disconnect their inputs and outputs when they are removed from their parent.

* Plugs may no longer implement acceptsInput( 0 ) to return false - this was illogical as it prevents the undoing of a connection made by the user.

0.13.0
======

* Fixed a bug whereby a node would be offset from the mouse position when dragging if starting the drag was delayed while other uis (particularly the NodeEditor) were updating.

* Fixed a bug which meant that connections were not correctly represented in the GraphEditor for children of the ArrayNodule.

* The ParameterHandler classes now correctly define the Ptr and ConstPtr member typedefs required for all IECore::RefCounted subclasses.

* The ParameterHandler classes now have a plug() method which returns the plug which was created to represent the parameter().

* The ParameterisedHolder class now exposes the internal ParameterHandler with a parameterHandler() method.

* The CompoundParameterHandler class now provides access to the handlers it uses for child parameters using the childParameterHandler() method.

* The CompoundParameterHandler now has python bindings.

* The Image widget no longer expands to fill space if it is available.

* The Label widget now has setText() and getText() methods.

* The PathWidget class now has a path() method returning the path being displayed.

* The Window.addChildWindow( window ) call now results in the parent window holding a reference to the python object representing the child. This avoids situations whereby the child python object would die but the QWidget representing the child on the C++ side would continue to live. Use Window.removeChild() to remove a child window when you wish to destroy it, or use setVisible( False ) to hide the child until you need it again.

* Fixed bug in PathWidget which meant that the path display would be incorrect until the path changed for the first time.

* PathListingWidget fixes :

	* Error when double clicking an item.
	* Selection was not being cleared when the current path wasn't valid.
	* Path wasn't being set when a leaf item was selected, which meant that hitting Enter in the PathChooserDialogue chose the wrong path.
	* Double clicking a directory when the current path wasn't valid created another invalid path, rather than replacing the invalid section.

* Added a "python" application which simply executes a python file in the Gaffer environment.

* Added a GafferUI._Variant class which has helper function for dealing with differences in PySide and PyQt4 with respect to QVariant handling.

* Fixed VectorDataWidget to work with PySide.

* Added a BoxParameterHandler covering Box2i, Box2f, Box3i and Box3f parameter types.

* GraphComponent now supports the len() function in python, returning the number of children for the instance. The __nonzero__ method is also implemented so that queries of the type "if graphComponent : " will return True as before, even if there are no children.

* The sizing behaviour of the PathListingWidget is no longer quite as annoying.

* GafferUI.Menu now optionally passes a "menu" argument to the checkBox callback of a menu item, in the same way as it does for the command callback.

* Fixed bug in GafferUI.ColorSwatch.getColor().

* Added Window.[gs]etFullScreen() methods, and added a menu item to the Layout menu to use them. Added a parentWindow argument to the Dialogue*.waitFor*() methods, and used it appropriately to keep dialogues on top even when in full screen mode.

* The Image class now uses the Cortex PNGImageReader for loading png files, and correctly converts linear data to sRGB for display.

* Added a basic framework for parameter-specific uis. Initially there are only specific uis for compound parameters, presets only parameters and path parameters - all others fall back to using the default plug widgets. A UI may be easily instantiated for all the parameters of a ParameterisedHolderNode using the GafferUI.CompoundParameterValueWidget - see GafferUI.ParameterisedHolderNodeUI for an example.

* The MultiLineTextWidget now has much more sensible tab spacing.

* The Collapsible container can now display an optional widget in the top right corner of the header. Use the setCornerWidget() and getCornerWidget() methods to manipulate this widget.

* Removed font parameter from GafferUI.Label - it wasn't doing anything anyway. Font control will likely return in the form of some support for text markup.

* Fixed variable scope issues which meant that the following code would fail if executed in a script editor :

		class A() :

			def __init__( self ) :

				print A

		a = A()

0.12.0
======

* Added a VectorDataWidget and a VectorDataPlugValueWidget, handling plugs of type StringVectorPlug, IntVectorPlug, FloatVectorPlug and V3fVectorPlug. Still needs file selector support.

* Added a V3fVectorDataPlug and a V3fVectorDataParameter handler.

* All gaffer applications now include a call to IECore.registerRunTimeTyped.

* Fixed bug which would cause the base class doRender() method to be called in addition to the overridden one when subclassing from Gadget in python.

* Plug::setInput() now calls acceptsInput() even when the new input is null. This allows plugs to reject the removal of existing connections. The connection gadget has been updated to respect the new rejection possibility, preventing the dragging of the destination end of a connection to a plug whose acceptsInput( 0 ) returns false, and not attempting to set the input if the source end of source a connection is dragged off into space. Currently no Gaffer plug type returns false from acceptsInput( 0 ), but custom plugs are free to do so and Gaffer plugs may return false in the future based on the content of a ReadOnly or Locked flag on the plug.

* Window constructor now accepts an additional "child" keyword argument which is passed to a call to setChild().

* Fixed problem whereby the hover colour for the SplitContainer handles wouldn't work on all platforms.

* The GraphEditor now provides access to its internal GraphGadget with the graphGadget() method.

* Refactored the Set class into an abstract base class and a StandardSet class containing the previous functionality. The members() and sequencedMembers() methods have been removed as they didn't generalise well to other potential Set subclasses (such as a NameFilteredSet). Instead a new member( i ) method provides ordered access and the contains( member ) method provides membership queries.

* Added a ChildSet class whose membership tracks the children of a given GraphComponent.

* Added python bindings for Nodule::plug and Connection::srcNodule() and Connection::dstNodule().

* Added CompoundEditor.editors() method, which returns all the child editors, optionally filtered by type.

* GraphGadget can now show arbitrary Sets of nodes, specified using the GraphGadget::setGraphSet() method.

* GafferBindings::SignalBinder now supports signals of arity 0.

* GafferBindings::SignalBinder now returns the class that was bound, so that additional method bindings may be added by calling code.

* A generic set of python signals are now bound as Signal0, Signal1, Signal2 and Signal3, where the number denotes the number of arguments the Signal takes. Python callables may be used to provide custom result combiners - see GafferTest.SignalsTest for examples.

* The GraphEditor now allows custom right click menus to be displayed for nodes in the graph. See GraphEditor.nodeContextMenuSignal() for brief documentation.

0.11.0
======

* GafferUI.Image() constructor now accepts unicode strings.

* Gadget, NodeGadget and StandardNodeGadget may now be derived from in Python.

* NodeGadget.registerNodeGadget() may now be called from Python, passing a callable for the creation function.

* New GafferUI.ImageGadget class allows images to be displayed in zoomable gadget uis.

* GafferUI.StandardNodeGadget can now be customised using a new setContents() method. This allows the central region of the node to be replaced with custom gadgets on a per-node basis. See startup/gui/graphs.py for example code for customising with an icon (note that this is waiting for a PNGImageReader to be available in cortex).

0.10.0
======

* Fixed flickering in the Viewer - enabled double buffering in same way as GraphEditor.

* The view application has been ported from gtk to Qt.

* The Collapsible widget no longer changes width when its collapse state is changed.

* Window.addChildWindow() has been ported from gtk to Qt. This means that dialogues can be made to stay on top of the windows that launch them.

* GafferUI.Dialogue.__init__ now accepts borderWidth and resizeable arguments.

* Collapsible constructor now accepts borderWidth argument.

* MultiLineTextWidget now accepts text argument to constructor.

* OpDialogue now reliably closes itself following execution or cancel. A future version may stay open if userData on the Op requests it.

* All signal connections are now made to Gaffer.WeakMethod objects where appropriate. Updated the Widget documentation to encourage the use of WeakMethod.

* GafferUI.Frame class now accepts a child argument to the constructor, actually uses the borderWidth argument, and Frame.setChild( None ) no longer errors.

* Rationalised Window close behaviour. Added Window.close() method which may be called to request that a window be closed - this is also called when the user clicks the close icon. Window subclasses may override Window._acceptsClose to reject or defer closing. Window.closeSignal() has been renamed to Window.closedSignal() and now is now used purely for notification when a window has closed (the return value from attached slots is irrelevant).

* GafferUI.Frame has a borderStyle argument, defaulting to drawing a rather plain border.

* OpDialogue now reports errors using a new ErrorDialogue class.

* GafferUI.CamelCase has been removed as it was ported into IECore some time ago.

* Fixed bug which prevented GraphComponent::commonAncestor<T>() from compiling.

* Gadgets and Widgets may now have tooltips. Client code can set the tooltip using setToolTip(), and classes may provide default dynamic values by implementing getToolTip() appropriately. Currently the NodeGadget, Nodule and ConnectionGadget implement getToolTip to return information about the Nodes, Plugs and Connections they represent.

* Widgets now have a wheelSignal() for responding to mouse wheel events. The Viewer and GraphEditor use this to implement zooming.

* Fixed bug which prevented Collapsible containers from toggling state correctly when multiple instances shared a parent.

* Node UIs now use a ScrolledContainer for their top level container.

* Label widget now allows the alignment to be specified.

* Fixed alignment issues in NodeUIs.

* OpDialogue has a better default size.

* Added handlers for the following parameter types :

	IECore.V2iParameter
	IECore.V3iParameter
	IECore.V2fParameter
	IECore.V3fParameter
	IECore.Color3fParameter
	IECore.Color4fParameter

* Fixed TypeError: invalid argument to sipBadCatcherResult() messages coming from ColorSwatch widget.

0.9.0
=====

* Can now access the internal QPixmap for a GafferUI.Image widget using the _qtPixmap() method. This is to assist in implementing other widget types and should be considered off limits for user code (along with all the other protected _qt* function).

* GafferUI.Button can now display an optional GafferUI.Image in addition to text, and has setText(), getText(), setImage() and getImage() accessors. Note that the label keyword parameter has been renamed to text. The GafferUI.Dialogue._addButton() method now accepts a Button directly (as well as still accepting a string for backwards compatibility) to allow buttons with images to be used in Dialogues.

* GraphEditor flicker should now be fixed (enabled double buffering for GL display).

* Fixed bug which would cause Ops to be executed twice in OpDialogue.waitForResult().

0.8.0
=====

* GafferUI.Image now falls back to using Qt image loading code if no IECore.Reader is available. This provides support for PNG images among others. Also fixed some bugs whereby images would fail to load if a full path wasn't provided - now the GAFFERUI_IMAGE_PATHS are used appropriately.

* OpDialogue can now be used non-modally without waitForResult(). The new OpDialogue.opExecutedSignal() can be used to tell when the op has been executed, and to get the result.

* GafferUI.EventLoop addIdleCallback() and removeIdleCallback() have been ported from the old gtk code to the new Qt code.

* Reworked GafferUI.EventLoop to support embedding of Gaffer in Maya. See documentation in GafferUI/EventLoop.py and apps/gui/gui-1.py for details.

0.7.0
=====

* Can now derive from ScriptNode in python and override acceptsChild etc as expected.

* ScrolledContainer and viewer classes have now been ported to the Qt based GafferUI.

* Added a GafferUI.Image class for displaying images in a widget.

* GafferUI.Menu class now supports checkBox menu items again.

* GafferUI.CheckBox widget now displayed with a tick rather than a blank yellow box.

* CompoundNumericPlugValueWidget has now been ported to the Qt based GafferUI, providing uis for V2f, V3f, V2i and V3i plug types.

* GafferUI.Widget derived classes may now pass a GafferUI.Widget instead of a QtGui.QWidget instance to the base class constructor. This makes it possible to develop a wider variety of custom widgets without resorting to Qt APIs.

0.6.0
=====

* Can now specify whether to use PySide or PyQt for Qt python bindings, using the GAFFERUI_QT_BINDINGS environment variable.

0.5.0
=====

* Added a new OpDialogue class to make it easy to run ops.

* Added a new op application, to allow users to run ops in a gui.

* NodeEditor.registerNodeUI has been moved to NodeUI.registerNodeUI, and a NodeUI.create factory functiona added. This allows NodeUIs to be used in places other than the NodeEditor.

0.4.0
=====

* Can now derive from GraphComponent in python and override acceptsParent and acceptsChild methods. These methods can also be overridden in other python-derivable classes such as Plug and Node.

* Can now derive from CompoundPlug in python.

0.3.0
=====

* ParameterisedHolders now allow some Parameters to opt out of representation as a Plug by adding a "noHostMapping" user data item with a value of BoolData( True ).

* Can now implement and use ParameterHandlers in python.

* Ctrl-C now correctly kills Gaffer

* Fixed type registration for TypedObjectPlugs.

* Fixed NodeEditor lag when selecting several nodes in the GraphEditor.

* Added a factory mechanism for Nodules, allowing different nodules to be used for different plugs. Used this to implement an ArrayNodule type which allows connections to the children of a CompoundPlug to be managed. The code below can be used to demonstrate this :

	import GafferUI
	GafferUI.Nodule.registerNodule( Gaffer.Node.staticTypeId(), "c", GafferUI.ArrayNodule )

	n = Gaffer.Node()

	n.addChild( Gaffer.CompoundPlug( "c" ) )
	n["c"].addChild( Gaffer.IntPlug( "a" ) )
	n["c"].addChild( Gaffer.IntPlug( "b" ) )
	n["c"].addChild( Gaffer.IntPlug( "c" ) )

	addChild( n )

	n2 = Gaffer.Node()
	n2.addChild( Gaffer.IntPlug( "o", Gaffer.Plug.Direction.Out ) )

	addChild( n2 )

* Fixed bug which caused "RuntimeError: Internal C++ object (PySide.QtGui.QLineEdit) already deleted." messages to be displayed.
