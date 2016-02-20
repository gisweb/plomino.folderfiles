# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plomino.folderfiles.testing import PLOMINO_folderfiles_INTEGRATION_TESTING  # noqa
from plone import api

import unittest2 as unittest


class TestSetup(unittest.TestCase):
    """Test that plomino.folderfiles is properly installed."""

    layer = PLOMINO_folderfiles_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        """Test if plomino.folderfiles is installed with portal_quickinstaller."""
        self.assertTrue(self.installer.isProductInstalled('plomino.folderfiles'))

    def test_browserlayer(self):
        """Test that IPlominofolderfilesLayer is registered."""
        from plomino.folderfiles.interfaces import IPlominofolderfilesLayer
        from plone.browserlayer import utils
        self.assertIn(IPlominofolderfilesLayer, utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = PLOMINO_folderfiles_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')
        self.installer.uninstallProducts(['plomino.folderfiles'])

    def test_product_uninstalled(self):
        """Test if plomino.folderfiles is cleanly uninstalled."""
        self.assertFalse(self.installer.isProductInstalled('plomino.folderfiles'))
