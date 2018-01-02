#! /bin/bash

set -e

gafferBotReaderCommand='import GafferScene; script.addChild( GafferScene.SceneReader() ); script["SceneReader"]["fileName"].setValue( "${GAFFER_ROOT}/resources/gafferBot/caches/gafferBot.scc" )'
renderCommand='import time; script["InteractiveAppleseedRender"]["state"].setValue( script["InteractiveAppleseedRender"].State.Running ); time.sleep( 15 )'

gaffer screengrab -image images/defaultLayout.png
gaffer screengrab -command "import GafferScene; script.addChild( GafferScene.SceneReader() )" -selection SceneReader -image images/emptySceneReader.png

gaffer screengrab \
	-command "$gafferBotReaderCommand" \
	-selection SceneReader \
	-image images/sceneReaderBound.png

gaffer screengrab \
	-command "$gafferBotReaderCommand" \
	-selection SceneReader \
	-scene.expandedPaths /GAFFERBOT /GAFFERBOT/C_torso_GRP \
	-editor GafferSceneUI.SceneHierarchy \
	-image images/sceneHierarchyExpandedTwoLevels.png

gaffer screengrab \
	-command "$gafferBotReaderCommand" \
	-selection SceneReader \
	-scene.fullyExpandedPaths /GAFFERBOT/C_torso_GRP/C_head_GRP /GAFFERBOT/C_torso_GRP/L_legUpper_GRP \
	-image images/headAndLegExpanded.png

gaffer screengrab \
	-command "$gafferBotReaderCommand" \
	-selection SceneReader \
	-editor Viewer \
	-scene.fullyExpandedPaths /GAFFERBOT/C_torso_GRP/C_head_GRP /GAFFERBOT/C_torso_GRP/L_legUpper_GRP /GAFFERBOT/C_torso_GRP/R_legUpper_GRP \
	-scene.selectedPaths /GAFFERBOT/C_torso_GRP/R_legUpper_GRP \
	-image images/headAndLegsExpanded.png

gaffer screengrab \
	-command "$gafferBotReaderCommand" \
	-selection SceneReader \
	-scene.fullyExpandedPaths / \
	-image images/fullyExpanded.png

gaffer screengrab \
	-command "$gafferBotReaderCommand; import GafferScene; script.addChild( GafferScene.Camera() )" \
	-selection Camera \
	-image images/camera.png

gaffer screengrab \
	-script scripts/group.gfr \
	-selection Group \
	-viewer.minimumExpansionDepth 999 \
	-scene.expandedPaths /group \
	-image images/group.png

gaffer screengrab \
	-script scripts/group.gfr \
	-command "import imath; script['Camera']['transform']['translate'].setValue( imath.V3f( 19, 13, 31 ) ); script['Camera']['transform']['rotate'].setValue( imath.V3f( 0, 30, 0 ) );" \
	-selection Camera \
	-editor NodeEditor \
	-nodeEditor.reveal Camera.transform \
	-image images/cameraTransform.png

gaffer screengrab \
	-script scripts/renderSettings.gfr \
	-selection Catalogue \
	-editor NodeGraph \
	-image images/renderSettings.png

gaffer screengrab \
	-script scripts/renderSettings.gfr \
	-command "$renderCommand" \
	-selection Catalogue \
	-image images/firstRender.png

gaffer screengrab \
	-script scripts/renderSettingsWithGap.gfr \
	-selection StandardOptions AppleseedOptions Outputs InteractiveAppleseedRender Catalogue \
	-editor NodeGraph \
	-image images/renderSettingsWithGap.png

gaffer screengrab \
	-script scripts/firstShaderAssignment.gfr \
	-selection ShaderAssignment \
	-editor NodeGraph \
	-image images/firstShaderAssignment.png

gaffer screengrab \
	-script scripts/firstLight.gfr \
	-selection Parent \
	-editor NodeGraph \
	-nodeGraph.frame Group Parent hosek_environment_edf \
	-image images/parentingNodeGraph.png

gaffer screengrab \
	-script scripts/firstLight.gfr \
	-selection Parent \
	-editor GafferSceneUI.SceneHierarchy \
	-scene.expandedPaths / /group \
	-image images/parentingSceneHierarchy.png

gaffer screengrab \
	-script scripts/firstLight.gfr \
	-command "$renderCommand" \
	-selection Catalogue \
	-editor Viewer \
	-image images/firstLighting.png

gaffer screengrab \
	-script scripts/textures.gfr \
	-command "$renderCommand" \
	-selection Catalogue \
	-editor Viewer \
	-image images/textures.png

gaffer screengrab \
	-script scripts/secondShaderAssignment.gfr \
	-selection ShaderAssignment1 \
	-editor NodeGraph \
	-nodeGraph.frame as_disney_material as_disney_material1 ShaderAssignment ShaderAssignment1 \
	-image images/secondShaderAssignment.png

gaffer screengrab \
	-script scripts/secondShaderAssignment.gfr \
	-command "$renderCommand" \
	-selection Catalogue \
	-image images/secondShaderAssignmentRender.png

gaffer screengrab \
	-script scripts/secondShaderAssignmentFiltered.gfr \
	-editor NodeGraph \
	-nodeGraph.frame PathFilter ShaderAssignment1 \
	-selection PathFilter \
	-image images/filterConnection.png

gaffer screengrab \
	-script scripts/secondShaderAssignmentFiltered.gfr \
	-editor Viewer \
	-selection ShaderAssignment1 \
	-scene.selectedPaths \
		/group/GAFFERBOT/C_torso_GRP/C_head_GRP/C_head_CPT/C_browNose001_REN \
		/group/GAFFERBOT/C_torso_GRP/C_head_GRP/C_head_CPT/C_mouthGrill001_REN \
	-viewer.minimumExpansionDepth 999 \
	-viewer.framedObjects /group/GAFFERBOT/C_torso_GRP/C_head_GRP/C_head_CPT \
	-viewer.viewDirection -0.2 -0.2 -1 \
	-image images/faceSelection.png

gaffer screengrab \
	-script scripts/secondShaderAssignmentFiltered.gfr \
	-command "$renderCommand" \
	-selection Catalogue \
	-editor Viewer \
	-image images/finalRender.png

cp $GAFFER_ROOT/graphics/expansion.png images
cp $GAFFER_ROOT/graphics/plus.png images
cp $GAFFER_ROOT/graphics/targetNodesUnlocked.png images
cp $GAFFER_ROOT/graphics/targetNodesLocked.png images
cp $GAFFER_ROOT/graphics/layoutButton.png images
cp $GAFFER_ROOT/graphics/objects.png images
cp $GAFFER_ROOT/graphics/addObjects.png images
cp $GAFFER_ROOT/graphics/replaceObjects.png images
