from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from AccessControl import getSecurityManager
from AccessControl import Unauthorized
from zope.interface import Interface, implements, Attribute
from zope.publisher.interfaces import IPublishTraverse
from iol.gisweb.document.plomino_utils import getSelectionListSettings
from iol.gisweb.document.utils.workflow_utils import wfInfo
from Products.CMFPlomino.exceptions import PlominoScriptException
from Products.CMFPlomino.config import SCRIPT_ID_DELIMITER
from ..config import WIZARD_FIELD_NAME
from json import dumps, load
from plone import api
from plone.memoize.view import memoize
from urlparse import urlparse, parse_qs
from zope.security import checkPermission

import json
import logging
_logger = logging.getLogger('IolDocument')


class newDocument(BrowserView):

    wizardTemplate = ViewPageTemplateFile("templates/newdocument.pt")
    plominoTemplate = ViewPageTemplateFile("templates/openform.pt")


    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.form = self.context
        self.target = self.context
        _logger.info('nuovo documento')
        self.wizardList = getSelectionListSettings(self.form,WIZARD_FIELD_NAME)
        self.isWizardForm = len(self.wizardList["names"])>0


    def getPendingDocuments(self):
        """
            verifica l'esitenza di un documento in compilazione 
        """  
        #import pdb;pdb.set_trace()
        #todo:
        #Ricerca dei documenti che sono in stato di avvio e che hanno come owner l'utente
        #Se trovati aggiungo nel template un javascript che attiva il dialog con l'avviso e il link alla scrivania


    @property
    def wizMenu(self):

        names = self.wizardList["names"]
        titles = self.wizardList["titles"]
        menus=[]        
        for i in range(len(names)):
            item={"name":names[i],"title":titles[i]}
            if i == 0:
                item["enabled"] = True
                item["active"] = True
            menus.append(item)
        return json.dumps(menus)

    @property
    def docUrl(self):
        """
        Url del documento corrente
        """
        #import pdb; pdb.set_trace()
        return self.form.absolute_url()


    def __call__(self):

        self.getPendingDocuments()

        if self.isWizardForm:
            _logger.info('template wizard')
            return self.wizardTemplate()
        else:
            _logger.info('template plomino')
            return self.plominoTemplate()


class manageDocument(BrowserView):
    implements(IPublishTraverse)

    editTemplate = ViewPageTemplateFile("templates/editdocument.pt")
    viewTemplate = ViewPageTemplateFile("templates/opendocument.pt")
    errorTemplate = ViewPageTemplateFile("templates/error.pt")

    def __init__(self, context, request):

        self.context = context
        self.request = request
        self.doc = context
        self.openwithform = ''
        self.isWizForm = False
        self.baseFormName = False

        #sul doc l'item contiene l'elenco dei visitati
        self.wizardInfo = self.doc.getItem(WIZARD_FIELD_NAME,[])

        if len(self.wizardInfo) > 0:
            #form di base
            self.baseFormName =self.wizardInfo[0]
            #campo con lista completa dei menu
            self.db = self.doc.getParentDatabase()
            frm = self.db.getForm(self.baseFormName) or self.doc.getForm()
            self.wizardList = getSelectionListSettings(frm,WIZARD_FIELD_NAME)



    def publishTraverse(self, request, name):
        self.openwithform = name 
        return self

    def setForm(self):
        """
        prende la form di apertura e la passa con il parametro openwithform
        """

        #import pdb;pdb.set_trace()

        if self.openwithform:
            openwithform = self.openwithform
        elif len(self.wizardInfo) > 0:
            openwithform = self.wizardInfo[len(self.wizardInfo)-1]
        elif self.baseFormName:
            openwithform = self.baseFormName
        else:
            return

        self.isWizForm = openwithform in self.wizardList["names"]

        #prendo il form passato in request
        frmName = openwithform
        frmObj = self.db.getForm(frmName)
        if not frmObj:
            #se non esiste provo ad usare il form memorizzato nel doc
            frmName =  self.doc.getItem('Form')
            frmObj = self.db.getForm(frmName)
            if not frmObj:
                _logger.info("IL FORM %s NON ESISTE" %frmName)
                raise Unauthorized 

        self.request.set("openwithform",frmName)
        self.doc.setItem('Form',frmName)  

    @property
    def wizMenu(self):

        names = self.wizardList["names"]
        titles = self.wizardList["titles"]
        menus=[]

        activeform = self.openwithform
        for i in range(len(names)):
            item={"name":names[i],"title":titles[i]}
            if names[i] in self.wizardInfo:
                item["enabled"] = True
            if names[i] == activeform:
                item["enabled"] = True
                item["active"] = True
            menus.append(item)

        #se  completa abitilito l'ultima form di invio
        if self.completa:
            menus[len(menus)-1]["enabled"] = True

        return json.dumps(menus)



    @property
    def completa(self):
        """
        Elenco dei menu uguale alla lista dei visitati + l'ultima form
        """
        # info = wfInfo(self.doc)
        # varInfo = info["variables"] or False
        # return varInfo and varInfo["review_state"] != "avvio"
        if self.baseFormName:
            return len(self.wizardList["names"]) == (len(self.wizardInfo)+1)

    @property
    def isLastForm(self):
        """
        Ultima form per l'invio
        """
        lastFormName = self.wizardList["names"][len(self.wizardList["names"])-1]
        return lastFormName == self.openwithform

    @property
    def lastForm(self):
        """
        Ultima form per l'invio
        """
        return self.wizardList["names"][len(self.wizardList["names"])-1]

    @property
    def presentata(self):
        """
        Form inviato .. disattiva il wizard
        """
        info = wfInfo(self.doc)
        if not info:
            _logger.info("NO WORKFLOW %s ASSOCIATO" %self.doc.getItem("iol_workflow_id",''))
            return False

        varInfo = info["variables"] or False
        return varInfo and "wf_presentata" in varInfo.keys() and varInfo["wf_presentata"]

    @property
    def wizForm(self):
        """
        Usa una form della lista wizard
        """
        return self.isWizForm

    @property
    def docUrl(self):
        """
        Url del documento corrente
        """
        #import pdb; pdb.set_trace()
        return self.doc.doc_url()

    def checkPermission(self):
        """You might want to do other stuff"""
        pass
        #import pdb;pdb.set_trace()
        #raise Unauthorized 
        #return


    def closeDocument(self):
        #Elimino dalla sessione il nome della form
        session_manager = self.context.session_data_manager
        session = session_manager.getSessionData()
        formName = self.doc.getItem(IOL_BASE_FORM)  
        if session.has_key(formName):
            del session[formName]
        url = self.doc.getParentDatabase().absolute_url() + '/'
        return self.request.response.redirect(url)


    def editDocument(self):
        self.template = self.editTemplate
        return self.renderDocument()

    def openDocument(self):        
        self.template = self.viewTemplate
        return self.renderDocument()
       

    def renderDocument(self):
        self.checkPermission()    
        self.setForm()
        
        #if not self.isWizForm:
        #    self.template = self.errorTemplate

        return self.template()




class createIolDocument(BrowserView):

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.form = self.context

    def __call__(self):

        #verificare se ho un documento del tipo uguale a quello che devo salvare in sessione.
        #se esiste non faccio nulla ????????????????????
        #oppure metto in sessione l'id del documento per tipologia e lo riapro con il form 
        #import pdb;pdb.set_trace()

        #TODO da sistemare un po

        # session_manager = self.context.session_data_manager
        # session = session_manager.getSessionData()
        # frm = self.form
        # if session.has_key(frm.getFormName()):
        #     _logger.info('esiste una richiesta uguale in compilazione, usa il link di navigazione....')
        #     db = frm.getParentDatabase()
        #     docId = session[frm.getFormName()]

        #     document = db.getDocument(docId)
        #     if document:
        #         document.plone_utils.addPortalMessage(u'Attenzione esiste un documento in compilazione %s ( % s )' %(frm.title,frm.getFormName()))
        #         firstForm = document.getItem(WIZARD_FIELD_NAME)[0]
        #         redirect = '%s/docview/%s' % (document.absolute_url(),firstForm)
        #         self.request.RESPONSE.redirect(redirect)
        #     else:
        #         del session[frm.getFormName()]   
        #     return


        # Add a document to the database
        #db = self.form.getParentDatabase()
        #doc = db.createDocument()
        #doc.setItem('Form', self.form.getFormName())

        # execute the onCreateDocument code of the form
        # valid = ''
        # try:
        #     valid = self.form.runFormulaScript(
        #             SCRIPT_ID_DELIMITER.join(['form', self.form.id, 'oncreate']),
        #             doc,
        #             self.form.onCreateDocument)
        # except PlominoScriptException, e:
        #     e.reportError('Document is created, but onCreate formula failed')

        # if valid is None or valid == '':
        #     doc.saveDocument(self.request, creation=True)

        # else:
        #     db.documents._delOb(doc.id)
        #     db.writeMessageOnPage(valid, self.request, False)
        #     self.request.response.redirect(db.absolute_url())


        self.form.createDocument(self.request)
        _logger.info('documento creato')


class wizardMenu(BrowserView):
    """ Viewlet per il menu """

    def __call__(self):        

        pdb.set_trace()
        document = self.context

#        wizardInfo = document.getItem(WIZARD_FIELD_NAME,[])
        wizardInfo = []

        if document.isNewDocument():
            frm = document.getForm()
        else:
            wizardInfo = document.getItem(WIZARD_FIELD_NAME,[])
            db = document.getParentDatabase()
            frm = db.getForm(wizardInfo[0])

        wizardList = getSelectionListAsDict(frm,WIZARD_FIELD_NAME)
        wKeys = wizardList.keys()

    	menu = []
        visited = []

        if not document.isNewDocument():
            visited = self.context.getItem(WIZARD_FIELD_NAME,[])
    	for v in wKeys:
    		item={"name":v,"title":wizardList[v]}
    		if v in visited:
    			item["enabled"] = True
    		menu.append(item)

        return json.dumps(menu)

