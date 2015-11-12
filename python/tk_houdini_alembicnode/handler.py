# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import sys

import hou

import sgtk

class TkAlembicNodeHandler(object):
    """Handle Tk Alembic node operations and callbacks."""

    ############################################################################
    # Class data

    HOU_ROP_ALEMBIC_TYPE = "rop_alembic"
    """Houdini type for regular alembic rops."""

    HOU_SOP_ALEMBIC_TYPE = "alembic"
    """Houdini type for regular alembic sops."""

    NODE_OUTPUT_PATH_PARM = "filename"
    """The name of the output path parameter on the node."""

    TK_ALEMBIC_NODE_TYPE = "sgtk_alembic"
    """The class of node as defined in Houdini for the Alembic nodes."""

    TK_CONFIG_PARM = "alembic_config"
    """The name of the parameter that stores the toolkit node configuration."""

    TK_CONFIG_NAME_KEY = "tk_config_name"
    """The name of the key in the user data that stores the config name."""

    ############################################################################
    # Class methods

    @classmethod
    def convert_back_to_toolkit_alembic_nodes(cls, app):
        """Convert Alembic nodes back to Toolkit Alembic nodes.

        :param app: The calling Toolkit Application

        Note: only converts nodes that had previously been Toolkit Alembic
        nodes.

        """

        # get all rop/sop alembic nodes in the session
        alembic_nodes = []
        alembic_nodes.extend(hou.nodeType(hou.sopNodeTypeCategory(),
            cls.HOU_SOP_ALEMBIC_TYPE).instances())
        alembic_nodes.extend(hou.nodeType(hou.ropNodeTypeCategory(),
            cls.HOU_ROP_ALEMBIC_TYPE).instances())

        # the tk node type we'll be converting to
        node_type = TkAlembicNodeHandler.TK_ALEMBIC_NODE_TYPE

        # iterate over all the alembic nodes and attempt to convert them
        for alembic_node in alembic_nodes:

            # get the user data dictionary stored on the node
            user_dict = alembic_node.userDataDict()

            # get the config data from the dictionary
            tk_config_name = user_dict.get(cls.TK_CONFIG_NAME_KEY)

            if not tk_config_name:
                app.log_warning(
                    "Almbic node '%s' does not have tk config name. "
                    "Can't convert to Tk Alembic node. Continuing." %
                    (alembic_node.name(),)
                )
                continue

            # create a new, Toolkit Alembic node:
            tk_alembic_node = alembic_node.parent().createNode(node_type)

            # find the index of the stored name on the new tk alembic node
            # and set that item in the menu.
            try:
                config_parm = tk_alembic_node.parm(
                    TkAlembicNodeHandler.TK_CONFIG_PARM)
                index = config_parm.menuLabels().index(tk_config_name)
                parm.set(index)
            except ValueError:
                pass

            # copy over all parameter values except the output path 
            _copy_parm_values(alembic_node, tk_alembic_node,
                excludes=[cls.NODE_OUTPUT_PATH_PARM])

            # copy the inputs and move the outputs
            _copy_inputs(alembic_node, tk_alembic_node)
            _move_outputs(alembic_node, tk_alembic_node)

            # make the new node the same color
            tk_alembic_node.setColor(alembic_node.color())

            # remember the name and position of the original alembic node
            alembic_node_name = n.name()
            alembic_node_pos = n.position()

            # destroy the original alembic node
            alembic_node.destroy()

            # name and reposition the new, regular alembic node to match the
            # original
            tk_alembic_node.setName(alembic_node_name)
            tk_alembic_node.setPosition(alembic_node_pos)

            app.log_debug("Converted: Alembic node '%s' to TK Alembic node."
                % (alembic_node_name,))

    @classmethod
    def convert_to_regular_alembic_nodes(cls, app):
        """Convert Toolkit Alembic nodes to regular Alembic nodes.

        :param app: The calling Toolkit Application

        """

        # retrieve all of the tk alembic nodes in the session
        tk_alembic_nodes = cls.get_tk_alembic_nodes()

        if not tk_alembic_nodes:
            app.log_debug("No Toolkit Alembic Nodes found for conversion.")
            return

        node_type = TkAlembicNodeHandler.TK_ALEMBIC_NODE_TYPE

        # determine the surface operator type for this class of node
        sop_types = hou.sopNodeTypeCategory().nodeTypes()
        sop_type = sop_types[node_type]

        # determine the render operator type for this class of node
        rop_types = hou.ropNodeTypeCategory().nodeTypes()
        rop_type = rop_types[node_type]

        # get all instances of tk alembic rop/sop nodes
        tk_alembic_nodes = []
        tk_alembic_nodes.extend(
            hou.nodeType(hou.sopNodeTypeCategory(), node_type).instances())
        tk_alembic_nodes.extend(
            hou.nodeType(hou.ropNodeTypeCategory(), node_type).instances())

        # iterate over all the tk alembic nodes and attempt to convert them
        for tk_alembic_node in tk_alembic_nodes:

            # determine the corresponding, built-in operator type
            if tk_alembic_node.type() == sop_type:
                alembic_operator = cls.HOU_SOP_ALEMBIC_TYPE
            elif tk_alembic_node.type() == rop_type:
                alembic_operator = cls.HOU_ROP_ALEMBIC_TYPE
            else:
                app.log_warning("Unknown type for node '%s': %s'" %
                    (tk_alembic_node.name(), tk_alembic_node.type()))
                continue

            # create a new, regular Alembic node
            alembic_node = tk_alembic_node.parent().createNode(alembic_operator)

            # copy the file parms value to the new node
            filename = _get_output_menu_label(
                tk_alembic_node.parm(cls.NODE_OUTPUT_PATH_PARM))
            alembic_node.parm(cls.NODE_OUTPUT_PATH_PARM).set(filename)

            # copy across knob values
            _copy_parm_values(tk_alembic_node, alembic_node,
                excludes=[cls.NODE_OUTPUT_PATH_PARM])

            # store the alembic config name in the user data so that we can
            # retrieve it later.
            config_parm = tk_alembic_node.parm(cls.TK_CONFIG_PARM)
            tk_config_name = config_parm.menuLabels()[config_parm.eval()]
            alembic_node.setUserData(cls.TK_CONFIG_NAME_KEY, tk_config_name)

            # copy the inputs and move the outputs
            _copy_inputs(tk_alembic_node, alembic_node)
            if alembic_operator == cls.HOU_SOP_ALEMBIC_TYPE:
                _move_outputs(tk_alembic_node, alembic_node)

            # make the new node the same color
            alembic_node.setColor(tk_alembic_node.color())

            # remember the name and position of the original tk alembic node
            tk_alembic_node_name = tk_alembic_node.name()
            tk_alembic_node_pos = tk_alembic_node.position()

            # destroy the original tk alembic node
            tk_alembic_node.destroy()

            # name and reposition the new, regular alembic node to match the
            # original
            alembic_node.setName(tk_alembic_node_name)
            alembic_node.setPosition(tk_alembic_node_pos)

            app.log_debug("Converted: Tk Alembic node '%s' to Alembic node."
                % (tk_alembic_node_name,))


    ############################################################################
    # Instance methods


    def __init__(self, app):
        """Initialize the handler.
        
        :params app: The application instance. 
        
        """

        # keep a reference to the app for easy access to templates, settings,
        # logging methods, tank, context, etc.
        self._app = app
    

    ############################################################################
    # methods and callbacks executed via the OTLs


    # create an Alembic node,  set the path to the output path of current node
    def _create_alembic_node(self):
        current_node = hou.pwd()

        cls = self.__class__

        output_path_parm = current_node.parm(cls.NODE_OUTPUT_PATH_PARM)
        alembic_node_name = 'alembic_' + current_node.name()

        # create the alembic node and set the filename parm
        alembic_node = node.parent().createNode(cls.HOU_SOP_ALEMBIC_TYPE)
        alembic_node.parm(cls.NODE_OUTPUT_PATH_PARM).set(
            output_path_parm.menuLabels()[output_path_parm.eval()])
        alembic_node.setName(alembic_node_name, unique_name=True)

        # move it away from the origin
        alembic_node.moveToGoodPosition()


    # returns a list of menu items for the current node
    def _get_output_path_menu_items(self):
        menu = ["sgtk"]
        current_node = hou.pwd()

        # attempt to compute the output path and add it as an item in the menu
        try:
            menu.append(self._compute_output_path(current_node))
        except sgtk.TankError as e:
            error_msg = ("Unable to construct the output path menu items: " 
                         "%s - %s" % (current_node.name(), e))
            self._app.log_error(error_msg)
            menu.append("ERROR: %s" % (error_msg,))

        return menu


    # copy the render path for the current node to the clipboard
    def _copy_path_to_clipboard(self):

        render_path = self._get_render_path(hou.pwd())

        # use Qt to copy the path to the clipboard:
        from sgtk.platform.qt import QtGui
        QtGui.QApplication.clipboard().setText(render_path)

        self._app.log_debug(
            "Copied render path to clipboard: %s" % (render_path,))


    # open a file browser showing the render path of the current node
    def _show_in_fs(self):

        # retrieve the calling node
        current_node = hou.pwd()
        if not current_node:
            return

        render_dir = None

        # first, try to just use the current cached path:
        render_path = self._get_render_path(current_node)

        if render_path:
            # the above method returns houdini style slashes, so ensure these
            # are pointing correctly
            render_path = render_path.replace("/", os.path.sep)

            dir_name = os.path.dirname(render_path)
            if os.path.exists(dir_name):
                render_dir = dir_name

        if not render_dir:
            # render directory doesn't exist so try using location
            # of rendered frames instead:
            rendered_files = self._get_rendered_files(current_node)

            if not rendered_files:
                msg = ("Unable to find rendered files for node '%s'." 
                       % (current_node,))
                self.log_error(msg)
                hou.ui.displayMessage(msg)
                return
            else:
                render_dir = os.path.dirname(rendered_files[0])

        # if we have a valid render path then show it:
        if render_dir:
            # XXX call utility method on core
            system = sys.platform

            # run the app
            if system == "linux2":
                cmd = "xdg-open \"%s\"" % render_dir
            elif system == "darwin":
                cmd = "open '%s'" % render_dir
            elif system == "win32":
                cmd = "cmd.exe /C start \"Folder\" \"%s\"" % render_dir
            else:
                msg = "Platform '%s' is not supported." % (system,)
                self.log_error(msg)
                hou.ui.displayMessage(msg)

            self._app.log_debug("Executing command:\n '%s'" % (cmd,))
            exit_code = os.system(cmd)
            if exit_code != 0:
                msg = "Failed to launch '%s'!" % (cmd,)
                hou.ui.displayMessage(msg)

    # lookup the default node name from the settings and apply it to the
    # supplied node
    def _set_default_node_name(self, node):
        default_name = self._app.get_setting('default_node_name')
        return node.setName(name, unique_name=True)


    ############################################################################
    # Private methods


    # compute the output path based on the current work file and cache template
    def _compute_output_path(self, node):

        # get relevant fields from the current file path
        work_file_fields = self._get_hipfile_fields()

        if not work_file_fields:
            msg = "This Houdini file is not a Shotgun Toolkit work file!"
            raise sgtk.TankError(msg)

        # Get the cache templates from the app
        work_cache_template = self._app.get_template("work_cache_template")

        # create fields dict with all the metadata
        fields = {
            "name": work_file_fields.get("name", None),
            "version": work_file_fields.get("version", None),
            "renderpass": node.name(),
            "SEQ": "FORMAT: $F",
        }

        # get the camera width and height if necessary
        if ("width" in work_cache_template.keys or 
            "height" in work_cache_template.keys):
            cam_path = node.parm("geometry1_camera").eval()
            cam_node = hou.node(cam_path)
            if not cam_node:
                raise sgtk.TankError("Camera %s not found." % cam_path)

            fields["width"] = cam_node.parm("resx").eval()
            fields["height"] = cam_node.parm("resy").eval()

        fields.update(self._app.context.as_template_fields(work_cache_template))

        path = template.apply_fields(fields)
        path = path.replace(os.path.sep, "/")

        return path


    # extract fields from current Houdini file using the workfile template
    def _get_hipfile_fields(self):
        current_file_path = hou.hipFile.path()

        work_fields = {}
        work_file_template = self._app.get_template("work_file_template")
        if (work_file_template and 
            work_file_template.validate(current_file_path)):
            work_fields = work_file_template.get_fields(current_file_path)

        return work_fields


    # get the render path from current item in the output path parm menu
    def _get_render_path(self, node):
        output_parm = node.parm(self.__class__.NODE_OUTPUT_PATH_PARM)
        path = output_parm.menuLabels()[output_parm.eval()]
        return path


    # returns the files on disk associated with this node
    def _get_rendered_files(self, node):

        file_name = self._get_render_path(node)
        template = self._app.get_template("work_cache_template")

        if not template.validate(file_name):
            msg = ("Unable to validate files on disk for node %s."
                   "The path '%s' is not recognized by Shotgun."
                   % (node.name(), file_name))
            self.log_error(msg)
            return []
            
        fields = template.get_fields(file_name)

        # get the actual file paths based on the template. Ignore any sequence
        # or eye fields
        return self._app.tank.paths_from_template(
            template, fields, ["SEQ", "eye"])


################################################################################
# Utility methods


# Copy all the input connections from this node to the target node.
def _copy_inputs(source_node, target_node):

    input_connections = source_node.inputConnections()
    num_target_inputs = len(target_node.inputConnectors())

    if len(input_connections) != num_target_inputs:
        raise hou.InvalidInput(
            "Node input count does not match. Cannot copy inputs from "
            "'%s' to '%s'" % (source_node, target_node)
        )
        
    for connection in input_connections:
        target.setInput(connection.inputIndex(), connection.inputNode())


# Copy parameter values of the source node to those of the target node if a
# parameter with the same name exists.
def _copy_parm_values(source_node, target_node, excludes=None):

    if not excludes:
        excludes = []

    # build a parameter list from the source node, ignoring the excludes
    source_parms = [
        parm for parm in source_node.parms() if parm.name() not in excludes]

    for source_parm in source_parms:

        source_parm_template = source_parm.parmTemplate()

        # skip folder parms
        if isinstance(source_parm_template, hou.FolderSetParmTemplate):
            continue

        target_parm = target_node.parm(source_parm.name())

        # if the parm on the target node doesn't exist, skip it
        if target_parm is None:
            continue

        # if we have keys/expressions we need to copy them all.
        if source_parm.keyframes():
            for key in source_parm.keyframes():
                target_parm.setKeyframe(key)
        else:
            # if the parameter is a string, copy the raw string.
            if isinstance(source_parm_template, hou.StringParmTemplate):
                target_parm.set(source_parm.unexpandedString())
            # copy the evaluated value
            else:
                target_parm.set(source_parm.eval())


# return the menu label for the supplied parameter
def _get_output_menu_label(parm):
    if parm.menuItems()[parm.eval()] == "sgtk":
        # evaluated sgtk path from item
        return parm.menuLabels()[parm.eval()] 
    else:
        # output path from menu label
        return parm.menuItems()[parm.eval()] 


# move all the output connections from the source node to the target node
def _move_outputs(source_node, target_node):

    for connection in source_node.outputConnections():
        output_node = connection.outputNode()
        output_node.setInput(connection.inputIndex(), target_node)


