from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.component import queryMultiAdapter
from zope.container.interfaces import INameChooser
from Products.ATContentTypes.interfaces import IATFile
from Products.ATContentTypes.interfaces import IATImage
from Products.CMFPlone.utils import safe_unicode
from plone.namedfile.file import NamedBlobFile
from plone.namedfile.file import NamedBlobImage
from plone.api.env import adopt_roles

from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent

from collective.upload.config import IMAGE_MIMETYPES
from iol.gisweb.document.config import ATTACHMENT_FOLDER
from iol.gisweb.document.utils.utils import getAttachmentFiles as filesInfo
from plomino.pgcatalog.pgReplication import dbUpload, getFile, isfloat
import json
import base64

class addAttachment(BrowserView):

    def publishTraverse(self, request, element):
        self.element = element
        self.multi = '/dbmultiupload/' in request.get("PATH_INFO")
        return self

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.doc = context


    def getAttachmentUrl(self):
        """
        url dell'allegato
        """
        docfolderId = self.doc.getId()
        dbfolderId = self.doc.getParentDatabase().id
        target = self.context.portal_url.getPortalObject()[ATTACHMENT_FOLDER][dbfolderId][docfolderId]
        return target.absolute_url_path()

    def getFileAttachment(self):
        """
            carica un file dal database
        """

        if not self.doc.isReader():
            return None

        if not (self.element and isfloat(self.element)):
            return None
        fileid = int(self.element)

        dbfile = getFile(self.doc,fileid)
        if not dbfile:
            return None
            
        self.request.RESPONSE.setHeader(
                'content-type', dbfile.file_type)
        self.request.RESPONSE.setHeader(
                "Content-Disposition", "inline; filename=" + dbfile.file_name)
        return base64.b64decode(dbfile.file_content)

    def removeFileAttachment(self):
        """
            rimuove un file dal database
        """



        if not self.doc.isReader():
            return None

        if not (self.element and isfloat(self.element)):
            return None
        fileid = int(self.element)

        removeFile(self.doc,fileid)


    #def getFile(self,filename)

    def __call__(self):
        import pdb;pdb.set_trace()
        if hasattr(self.request, 'REQUEST_METHOD'):
            # TODO: we should check errors in the creation process, and
            # broadcast those to the error template in JS
            if self.request['REQUEST_METHOD'] == 'POST':
                if getattr(self.request, 'files[]', None) is not None:
                    files = self.request['files[]']
                    title = self.request['title[]']
                    description = self.request['description[]']
                    uploaded = dbUpload(self.doc, self.element, self.multi, [files], [title], [description])
                    import pdb;pdb.set_trace();
                    if uploaded:
                        return json.dumps({'files': uploaded})
                    #     upped = []
                    #     #setto il plomino item
                    #     current_files = self.doc.getItem(self.element,{})
                    #     #import pdb;pdb.set_trace()
                    #     for item in uploaded:
                    #         current_files[item.id] = item.getContentType()
                    #         el = getFileInfo(item)
                    #         upped.append(el)
                    #         self.doc.setItem(self.element,current_files)
                    #     return json.dumps({'files': upped})
                return ""
        return self.index()

    def upload(self, files, title='', description=''):

        #import pdb;pdb.set_trace()

        if not self.doc.isDocument():
            return

        docfolderId = self.doc.getId()
        dbfolderId = self.doc.getParentDatabase().id

        #TODO come configurare diverse cartelle per applicazione o plomino db (da fare sulle singole app)?
        target = self.context.portal_url.getPortalObject()[ATTACHMENT_FOLDER]

        with adopt_roles('Manager'):
            if not dbfolderId in target.keys():
                target.invokeFactory("Folder", id=dbfolderId, title=dbfolderId)
            target = target[dbfolderId]
            if not docfolderId in target.keys():
                target.invokeFactory("Folder", id=docfolderId, title=docfolderId)
            docFolder = target[docfolderId]
            for username, roles in self.doc.get_local_roles():
                docFolder.manage_setLocalRoles(username, roles)

        if not isinstance(files, list):
            files = [files]

        #se non  campo multiplo vuoto la cartella
        #TODO tenere allineati i files nella cartella con i nomi sul campo di plomino 
        current_files = self.doc.getItem(self.element)
        cleaned_files = {}
        if self.multiple:
            for fName in current_files:
                if fName in docFolder.keys():
                    cleaned_files[fName] = current_files[fName]
            self.doc.setItem(self.element, cleaned_files)

        #se upload singolo cancello tutti i file presenti collegati al campo
        else:
            try:
                docFolder.manage_delObjects(current_files.keys())
            except Exception as error:
                pass
            self.doc.removeItem(self.element)     

        namechooser = INameChooser(docFolder)
        loaded = []
        for item in files:
            if item.filename:
                content_type = item.headers.get('Content-Type')
                filename = safe_unicode(item.filename)
                data = item.read()
                id_name = ''
                title = title and title[0] or filename
                # Get a unique id here
                id_name = namechooser.chooseName(title, docFolder)

                # Portal types allowed : File and Image
                # Since Plone 4.x both types use Blob
                if content_type in IMAGE_MIMETYPES:
                    portal_type = 'Image'
                    wrapped_data = NamedBlobImage(data=data, filename=filename)
                else:
                    portal_type = 'File'
                    wrapped_data = NamedBlobFile(data=data, filename=filename)

                # Create content
                docFolder.invokeFactory(portal_type,
                                           id=id_name,
                                           title=title,
                                           description=description[0])
                newfile = docFolder[id_name]
                # Set data
                if portal_type == 'File':
                    if IATFile.providedBy(newfile):
                        newfile.setFile(data, filename=filename)
                    else:
                        newfile.file = wrapped_data
                elif portal_type == 'Image':
                    if IATImage.providedBy(newfile):
                        newfile.setImage(data, filename=filename)
                    else:
                        newfile.image = wrapped_data

                # Finalize content creation, reindex it
                newfile.reindexObject()
                notify(ObjectModifiedEvent(newfile))
                loaded.append(newfile)
            if loaded:
                return loaded
            return False


    def getFileInfo(self, item):
        context_type = 'File'
        info = {'name': 'adasd',
                'title': 'asdasdasd',
                'description': 'asdasdasd',
                'url': 'sdasda',
                'delete_url': 'adsdasda',
                'delete_type': 'DELETE',
                'field_name' : 'sadasd',
                }

        if hasattr(item, 'size'):
            info['size'] = context.size()
        else:
            if context_type == 'File':
                info['size'] = context.file.getSize()
            elif context_type == 'Image':
                info['size'] = context.image.getSize()
        if context_type == 'Image':
            scales = context.restrictedTraverse('@@images')
            thumb = scales.scale(element='image', scale='thumb')
            info['thumbnail_url'] = thumb.url
        return info
