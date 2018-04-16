#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.lang import XServiceInfo, XInitialization
from com.sun.star.beans import XPropertySet, XPropertySetInfo
from com.sun.star.task import XInteractionHandler

import binascii


def getResourceLocation(ctx, path="OAuth2OOo"):
    identifier = "com.gmail.prrvchr.extensions.OAuth2OOo"
    service = "/singletons/com.sun.star.deployment.PackageInformationProvider"
    provider = ctx.getValueByName(service)
    return "%s/%s" % (provider.getPackageLocation(identifier), path)

def getConfiguration(ctx, nodepath, update=False):
    service = "com.sun.star.configuration.ConfigurationProvider"
    provider = ctx.ServiceManager.createInstance(service)
    service = "com.sun.star.configuration.ConfigurationUpdateAccess" if update else \
              "com.sun.star.configuration.ConfigurationAccess"
    arguments = (uno.createUnoStruct("com.sun.star.beans.NamedValue", "nodepath", nodepath), )
    return provider.createInstanceWithArguments(service, arguments)

def getCurrentLocale(ctx):
    service = "/org.openoffice.Setup/L10N"
    parts = getConfiguration(ctx, service).getByName("ooLocale").split("-")
    locale = uno.createUnoStruct("com.sun.star.lang.Locale", parts[0], "", "")
    if len(parts) > 1:
        locale.Country = parts[1]
    else:
        service = ctx.ServiceManager.createInstance("com.sun.star.i18n.LocaleData")
        locale.Country = service.getLanguageCountryInfo(locale).Country
    return locale

def getStringResource(ctx, locale=None, filename="DialogStrings"):
    service = "com.sun.star.resource.StringResourceWithLocation"
    location = getResourceLocation(ctx)
    if locale is None:
        locale = getCurrentLocale(ctx)
    arguments = (location, True, locale, filename, "", PyInteractionHandler())
    return ctx.ServiceManager.createInstanceWithArgumentsAndContext(service, arguments, ctx)

def generateUuid():
    return binascii.hexlify(uno.generateUuid().value).decode("utf-8")

def createMessageBox(ctx, peer, message, title, mtype="messbox", buttons=2):
    mtypes = {"messbox": "MESSAGEBOX", "infobox": "INFOBOX", "warningbox": "WARNINGBOX",
              "errorbox": "ERRORBOX", "querybox": "QUERYBOX"}
    mtype = uno.Enum("com.sun.star.awt.MessageBoxType", mtypes[mtype] if mtype in mtypes else "MESSAGEBOX")
    return peer.getToolkit().createMessageBox(peer, mtype, buttons, title, message)

def createService(ctx, name, **args):
    if args:
        arguments = []
        for key, value in args.items():
            arguments.append(uno.createUnoStruct("com.sun.star.beans.NamedValue", key, value))
    if args:
        service = ctx.ServiceManager.createInstanceWithArgumentsAndContext(name, tuple(arguments), ctx)
    else:
        service = ctx.ServiceManager.createInstanceWithContext(name, ctx)
    return service


class PyInteractionHandler(unohelper.Base, XInteractionHandler):
    # XInteractionHandler
    def handle(self, requester):
        pass


class PyPropertySetInfo(unohelper.Base, XPropertySetInfo):
    def __init__(self, properties={}):
        self.properties = properties

    # XPropertySetInfo
    def getProperties(self):
        return tuple(self.properties.values())
    def getPropertyByName(self, name):
        return self.properties[name] if name in self.properties else None
    def hasPropertyByName(self, name):
        return name in self.properties


class PyServiceInfo(XServiceInfo):
    # XServiceInfo
    def supportsService(self, service):
        return unohelper.ImplementationHelper().supportsService(g_ImplementationName, service)
    def getImplementationName(self):
        return g_ImplementationName
    def getSupportedServiceNames(self):
        return unohelper.ImplementationHelper().getSupportedServiceNames(g_ImplementationName)


class PyInitialization(XInitialization):
    # XInitialization
    def initialize(self, namedvalues=()):
        for namedvalue in namedvalues:
            if hasattr(namedvalue, "Name") and hasattr(namedvalue, "Value"):
                self.setPropertyValue(namedvalue.Name, namedvalue.Value)


class PyPropertySet(XPropertySet):
    def __init__(self, properties={}):
        self.properties = properties

    # XPropertySet
    def getPropertySetInfo(self):
        return PyPropertySetInfo(self.properties)
    def setPropertyValue(self, name, value):
        if name in self.properties and hasattr(self, name):
            setattr(self, name, value)
    def getPropertyValue(self, name):
        value = None
        if name in self.properties and hasattr(self, name):
            value = getattr(self, name)
        return value
    def addPropertyChangeListener(self, name, listener):
        pass
    def removePropertyChangeListener(self, name, listener):
        pass
    def addVetoableChangeListener(self, name, listener):
        pass
    def removeVetoableChangeListener(self, name, listener):
        pass
