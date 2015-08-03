# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Alembic Output App for Houdini
"""

import sgtk


class AlembicOutputNode(sgtk.platform.Application):
    def init_app(self):
        module = self.import_module("tk_houdini_alembicnode")
        self.handler = module.ToolkitAlembicNodeHandler(self)

    def convert_to_alembic_nodes(self):
        """
        Convert all Shotgun Alembic nodes found in the current Script to regular
        Alembic nodes. Additional toolkit information will be stored in
        user data named 'tk_*'
        """
        self.handler.convert_sg_to_alembic_nodes()

    def convert_from_alembic_nodes(self):
        """
        Convert all regular Alembic nodes that have previously been converted
        from Shotgun Alembic nodes, back into Shotgun Alembic nodes.
        """
        self.handler.convert_alembic_to_sg_nodes()
