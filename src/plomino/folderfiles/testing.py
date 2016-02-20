# -*- coding: utf-8 -*-
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2

import plomino.folderfiles


class PlominofolderfilesLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        self.loadZCML(package=plomino.folderfiles)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'plomino.folderfiles:default')


PLOMINO_folderfiles_FIXTURE = PlominofolderfilesLayer()


PLOMINO_folderfiles_INTEGRATION_TESTING = IntegrationTesting(
    bases=(PLOMINO_folderfiles_FIXTURE,),
    name='PlominofolderfilesLayer:IntegrationTesting'
)


PLOMINO_folderfiles_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(PLOMINO_folderfiles_FIXTURE,),
    name='PlominofolderfilesLayer:FunctionalTesting'
)


PLOMINO_folderfiles_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        PLOMINO_folderfiles_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE
    ),
    name='PlominofolderfilesLayer:AcceptanceTesting'
)
