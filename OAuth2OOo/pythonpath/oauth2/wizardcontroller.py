#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.ui.dialogs import XWizardController

from .unolib import PropertySet

from .configurationwriter import ConfigurationWriter
from .httpcodehandler import HttpCodeHandler
from .wizardpage import WizardPage
from .wizardhandler import WizardHandler

from .unotools import createService
from .unotools import generateUuid
from .unotools import getCurrentLocale
from .unotools import getProperty
from .unotools import getStringResource

from .logger import getLogger

from .oauth2tools import g_identifier

import traceback


class WizardController(unohelper.Base,
                       PropertySet,
                       XWizardController):
    def __init__(self, ctx, url, username):
        level = uno.getConstantByName('com.sun.star.logging.LogLevel.INFO')
        self.ctx = ctx
        self.Configuration = ConfigurationWriter(self.ctx)
        self.ResourceUrl = url
        self.UserName = username
        self.AuthorizationCode = uno.createUnoStruct('com.sun.star.beans.Optional<string>')
        self.Handler = HttpCodeHandler(self.ctx)
        self.CodeVerifier = generateUuid() + generateUuid()
        self.State = generateUuid()
        self.advanceTo = True
        self.Pages = {}
        self.WizardHandler = WizardHandler(self.ctx, self.Configuration, self)
        self.Logger = getLogger(self.ctx)
        self.stringResource = getStringResource(self.ctx, g_identifier, 'OAuth2OOo')
        self.Provider = createService(self.ctx, 'com.sun.star.awt.ContainerWindowProvider')

    @property
    def ResourceUrl(self):
        return self.Configuration.Url.Id
    @ResourceUrl.setter
    def ResourceUrl(self, url):
        self.Configuration.Url.Id = url
    @property
    def UserName(self):
        return self.Configuration.Url.Provider.Scope.User.Id
    @UserName.setter
    def UserName(self, name):
        self.Configuration.Url.Provider.Scope.User.Id = name
    @property
    def ActivePath(self):
        return 0 if self.Configuration.Url.Provider.HttpHandler else 1

    # XWizardController
    def createPage(self, parent, id):
        if id not in self.Pages:
            level = uno.getConstantByName('com.sun.star.logging.LogLevel.INFO')
            self.Logger.logp(level, "WizardController", "createPage()", "PageId: %s..." % id)
            page = WizardPage(self.ctx,
                              self.Configuration,
                              id,
                              parent,
                              self.WizardHandler,
                              self.CodeVerifier,
                              self.State,
                              self.AuthorizationCode)
            self.Pages[id] = page
        return self.Pages[id]
    def getPageTitle(self, id):
        title = self.stringResource.resolveString('PageWizard%s.Step' % (id, ))
        return title
    def canAdvance(self):
        return True
    def onActivatePage(self, id):
        try:
            print("WizardController.onActivatePage()")
            level = uno.getConstantByName('com.sun.star.logging.LogLevel.INFO')
            self.Logger.logp(level, "WizardController", "onActivatePage()", "PageId: %s..." % id)
            title = self.stringResource.resolveString('PageWizard%s.Title' % (id, ))
            self.WizardHandler.Wizard.setTitle(title)
            finish = uno.getConstantByName('com.sun.star.ui.dialogs.WizardButton.FINISH')
            self.WizardHandler.Wizard.enableButton(finish, False)
            if id == 1:
                self.WizardHandler.Wizard.activatePath(self.ActivePath, True)
                self.WizardHandler.Wizard.updateTravelUI()
            elif id == 3:
                print("WizardController.onActivatePage.addCallback() 1 %s" % id)
                page = self.Pages[id]
                print("WizardController.onActivatePage.addCallback() 2 %s" % page)
                if page:
                    self.Handler.addCallback(page, self)
                    print("WizardController.onActivatePage.addCallback() 3")
    #       if self.advanceTo:
    #           self.advanceTo = False
    #           self.WizardHandler.Wizard.advanceTo(2)
            self.Logger.logp(level, "WizardController", "onActivatePage()", "PageId: %s... Done" % id)
        except Exception as e:
            print("WizardController.onActivatePage().Error: %s - %s" % (e, traceback.print_exc()))
    def onDeactivatePage(self, id):
        pass
    def confirmFinish(self):
        print("WizardController.confirmFinish()")
        return True

    def _getPropertySetInfo(self):
        properties = {}
        bound = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.BOUND')
        readonly = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.READONLY')
        transient = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.TRANSIENT')
        maybevoid = uno.getConstantByName('com.sun.star.beans.PropertyAttribute.MAYBEVOID')
        properties['ResourceUrl'] = getProperty('ResourceUrl', 'string', transient)
        properties['UserName'] = getProperty('UserName', 'string', transient)
        properties['ActivePath'] = getProperty('ActivePath', 'short', readonly)
        properties['AuthorizationCode'] = getProperty('AuthorizationCode', 'com.sun.star.beans.Optional<string>', bound)
        properties['AuthorizationStr'] = getProperty('AuthorizationStr', 'string', readonly)
        properties['CheckUrl'] = getProperty('CheckUrl', 'boolean', readonly)
        properties['CodeVerifier'] = getProperty('CodeVerifier', 'string', readonly)
        properties['Configuration'] = getProperty('Configuration', 'com.sun.star.uno.XInterface', readonly)
        properties['Handler'] = getProperty('Handler', 'com.sun.star.uno.XInterface', bound | readonly)
        properties['Paths'] = getProperty('Paths', '[][]short', readonly)
        properties['State'] = getProperty('State', 'string', readonly)
        properties['WizardHandler'] = getProperty('WizardHandler', 'com.sun.star.uno.XInterface', readonly)
        return properties