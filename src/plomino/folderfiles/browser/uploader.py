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


class addAttachment(BrowserView):

    def publishTraverse(self, request, fieldName):
        self.fieldName = fieldName
        return self

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.doc = context
    
    #usata per le prove
    def getAttachmentFiles(self):
        self.request.RESPONSE.setHeader('content-type', 'application/json; charset=utf-8')
        return filesInfo(self.doc, self.fieldName)


    def getAttachmentUrl(self):
        """
        url dell'allegato
        """
        docfolderId = self.doc.getId()
        dbfolderId = self.doc.getParentDatabase().id
        target = self.context.portal_url.getPortalObject()[ATTACHMENT_FOLDER][dbfolderId][docfolderId]
        return target.absolute_url_path()

    def getAttachment(self):
        """
        carica un file dalla cartella giusta TODO....
        """
        filename = self.request.get('filename')
        if not filename:
            return None

        docfolderId = self.doc.getId()
        dbfolderId = self.doc.getParentDatabase().id
        target = self.context.portal_url.getPortalObject()[ATTACHMENT_FOLDER][dbfolderId][docfolderId]

        if not filename in target.keys():
            return None

        file_obj = target[filename]
        self.request.RESPONSE.setHeader(
                'content-type', file_obj.getContentType())
        self.request.RESPONSE.setHeader(
                "Content-Disposition", "inline; filename="+filename)
        return file_obj.data


    @property
    def multiple(self):
        return "multi" in self.request.keys() 

    #def getFile(self,filename)

    def __call__(self):

        template = ViewPageTemplateFile("templates/file_upload.pt")

        if hasattr(self.request, 'REQUEST_METHOD'):
            json_view = queryMultiAdapter(
                (self.context, self.request), name=u'api')

            # TODO: we should check errors in the creation process, and
            # broadcast those to the error template in JS
            if self.request['REQUEST_METHOD'] == 'POST':
                if getattr(self.request, 'files[]', None) is not None:
                    files = self.request['files[]']
                    title = self.request['title[]']
                    description = self.request['description[]']
                    uploaded = self.upload([files], [title], [description])
                    if uploaded and json_view:
                        upped = []
                        #setto il plomino item
                        current_files = self.doc.getItem(self.fieldName,{})
                        #import pdb;pdb.set_trace()
                        for item in uploaded:
                            current_files[item.id] = item.getContentType()
                            el = json_view.getContextInfo(item)
                            el["fieldName"] = self.fieldName
                            upped.append(el)
                            self.doc.setItem(self.fieldName,current_files)
                        return json_view.dumps(upped)
                return json_view()
        return template(self)

    def upload(self, files, title='', description=''):

        #TODO!!!!!!!!!!!!!!!
        #OGNI PACCHETTO CREA LA PROPRIA CARTELLA PER GLI ALLEGATI 
        #E IL GRUPPO DI ISTRUTTORI/RUP 
        #CHE HANNO RUOLI DI CONTRIBUTORI/EDITOR SULLA CARTELLA
        #QUESTO PACCHETTO DEVE CREARE LA CARTELLA DI PARTENZA CHE PER ORA CABLO IN documenti_allegati

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
        current_files = self.doc.getItem(self.fieldName)
        cleaned_files = {}
        if self.multiple:
            for fName in current_files:
                if fName in docFolder.keys():
                    cleaned_files[fName] = current_files[fName]
            self.doc.setItem(self.fieldName, cleaned_files)

        #se upload singolo cancello tutti i file presenti collegati al campo
        else:
            try:
                docFolder.manage_delObjects(current_files.keys())
            except Exception as error:
                pass
            self.doc.removeItem(self.fieldName)     

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



    def upload_prove_plomino(self, files, title='', description=''):
        loaded = []
        namechooser = INameChooser(self.context)
        import pdb;pdb.set_trace()

#        if isinstance(submittedValue, FileUpload):
#                submittedValue = asList(submittedValue)
        
        if not isinstance(files, list):
            files = [files]
        
        for item in files:
            if item.filename:
                content_type = item.headers.get('Content-Type')
                filename = safe_unicode(item.filename)
                data = item.read()
                id_name = ''
                title = title and title[0] or filename
                # Get a unique id here
                id_name = namechooser.chooseName(title, self.context)



                

                # Portal types allowed : File and Image
                # Since Plone 4.x both types use Blob
                # if content_type in IMAGE_MIMETYPES:
                #     portal_type = 'Image'
                #     wrapped_data = NamedBlobImage(data=data, filename=filename)
                # else:
                #     portal_type = 'File'
                #     wrapped_data = NamedBlobFile(data=data, filename=filename)


                # # Create content
                # self.context.invokeFactory(portal_type,
                #                            id=id_name,
                #                            title=title,
                #                            description=description[0])




                # newfile = self.context[id_name]
                

                # # Set data
                # if portal_type == 'File':
                #     if IATFile.providedBy(newfile):
                #         newfile.setFile(data, filename=filename)
                #     else:
                #         newfile.file = wrapped_data
                # elif portal_type == 'Image':
                #     if IATImage.providedBy(newfile):
                #         newfile.setImage(data, filename=filename)
                #     else:
                #         newfile.image = wrapped_data
                # # Finalize content creation, reindex it
                # newfile.reindexObject()
                # notify(ObjectModifiedEvent(newfile))
                # loaded.append(newfile)


            if loaded:
                return loaded
            return False




            # if isinstance(submittedValue, FileUpload):
            #     submittedValue = asList(submittedValue)

            # current_files=doc.getItem(fieldname)
            # if not current_files:
            #     current_files = {}

            # if submittedValue is not None:
            #     for fl in submittedValue:
            #         (new_file, contenttype) = doc.setfile(fl)
            #         if new_file is not None:
            #             if adapt.type == "SINGLE":
            #                 for filename in current_files.keys():
            #                     if filename != new_file:
            #                         doc.deletefile(filename)
            #                 current_files={}
            #             current_files[new_file]=contenttype

            # v = current_files




class addAllegatiDatagrid(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        doc = self.aq_parent
        data = dict()
        fieldAttach = doc.REQUEST.get('allegato_field')        
        fileDoc = doc.REQUEST.get('allegato_file')
        fileName = doc.REQUEST.get('allegato_filename')
        dgContents =  json.loads(doc.REQUEST.get('dg_contents'))
        files = doc.getItem(fieldAttach,{})

        listFile = files.keys()
        tempFilePresent = []
        if len(dgContents)>0:
            for row in dgContents:
                if row[-1] in listFile:
                    tempFilePresent.append(row[-1])

        for fileKey in listFile:
            if fileKey not in tempFilePresent:
                del files[fileKey]
                doc.deletefile(fileKey)
        doc.setItem(fieldAttach, files) 

        (f,c) = doc.setfile(fileDoc,filename = fileName)
        files[f]=c
        lastFile = f
        doc.setItem(fieldAttach, files)


        data['success']=1
        data['results']={'files':files.keys(),'lastFile':lastFile}

        return json.dumps(data)



class removeAllegatiDatagrid(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        doc = self.aq_parent
        data = dict()
        fieldAttach = doc.REQUEST.get('allegato_field')
        fileName = doc.REQUEST.get('allegato_filename')
        files = doc.getItem(fieldAttach,{})
        if fileName in files.keys():
            del files[fileName]
            doc.deletefile(fileName)
        doc.setItem(fieldAttach,files)    
        data['success']=1
        data['results']={'files':files.keys()}

        return json.dumps(data)



