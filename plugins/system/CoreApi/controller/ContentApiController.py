import json
import os
import time

from flask import Flask, request, jsonify, abort
from werkzeug.utils import secure_filename
from src.service.ModelStore import ModelStore
from src.model.entity.Content import Content
from src.manager.FolderManager import FolderManager
from src.model.enum.ContentType import ContentType
from src.model.enum.FolderEntity import FolderEntity, FOLDER_ROOT_PATH
from src.interface.ObController import ObController
from src.service.ExternalStorageServer import ExternalStorageServer
from src.util.utils import str_to_enum, get_optional_string
from src.util.UtilFile import randomize_filename
from plugins.system.CoreApi.exception.ContentPathMissingException import ContentPathMissingException
from plugins.system.CoreApi.exception.ContentNotFoundException import ContentNotFoundException
from plugins.system.CoreApi.exception.FolderNotFoundException import FolderNotFoundException
from plugins.system.CoreApi.exception.FolderNotEmptyException import FolderNotEmptyException


class ContentApiController(ObController):

    def register(self):
        self._app.add_url_rule('/api/content', 'api_content_list', self.list_content, methods=['GET'])
        self._app.add_url_rule('/api/content', 'api_content_add', self.add_content, methods=['POST'])
        self._app.add_url_rule('/api/content/<int:content_id>', 'api_content_get', self.get_content, methods=['GET'])
        self._app.add_url_rule('/api/content/<int:content_id>', 'api_content_update', self.update_content, methods=['PUT'])
        self._app.add_url_rule('/api/content/<int:content_id>', 'api_content_delete', self.delete_content, methods=['DELETE'])
        self._app.add_url_rule('/api/content/rename', 'api_content_rename', self.rename_content, methods=['PUT'])
        self._app.add_url_rule('/api/content/location/<int:content_id>', 'api_content_location', self.location_content, methods=['GET'])
        self._app.add_url_rule('/api/content/move-bulk', 'api_content_bulk_move', self.move_bulk_content, methods=['POST'])
        self._app.add_url_rule('/api/content/upload-bulk', 'api_content_upload_bulk', self.upload_bulk_content, methods=['POST'])
        self._app.add_url_rule('/api/content/folder', 'api_folder_add', self.add_folder, methods=['POST'])
        self._app.add_url_rule('/api/content/folder', 'api_folder_delete', self.delete_folder, methods=['DELETE'])
        self._app.add_url_rule('/api/content/folder/rename', 'api_folder_rename', self.rename_folder, methods=['PUT'])

    def get_json(self):
        data = {}

        try:
            data = request.get_json()
        except:
            pass

        return data

    def get_folder_context(self):
        data = self.get_json()
        path = data.get('path')
        path = "{}/{}".format(FOLDER_ROOT_PATH, path.strip('/')) if not path.startswith(FOLDER_ROOT_PATH) else path

        if 'folder_id' in data:
            folder = self._model_store.folder().get(id=data.get('folder_id'))
            return path, folder

        if 'path' not in data:
            raise ContentPathMissingException()

        folder = self._model_store.folder().get_one_by_path(path=path, entity=FolderEntity.CONTENT)
        is_root_drive = FolderManager.is_root_drive(path)

        if not folder and not is_root_drive:
            raise FolderNotFoundException()

        return FOLDER_ROOT_PATH if is_root_drive else path, folder

    def list_content(self):
        data = self.get_json()
        working_folder_path = None
        working_folder = None
        folder_id = None

        try:
            working_folder_path, working_folder = self.get_folder_context()
            folder_id = data.get('folder_id', 0 if not working_folder else working_folder.id)
        except ContentPathMissingException:
            pass

        contents = self._model_store.content().get_contents(
            folder_id=folder_id,
            slide_id=data.get('slide_id', None),
        )
        result = [content.to_dict() for content in contents]

        return jsonify({
            'contents': result,
            'working_folder_path': working_folder_path,
            'working_folder': working_folder.to_dict() if working_folder else None
        })

    def get_content(self, content_id: int):
        content = self._model_store.content().get(content_id)
        if not content:
            raise ContentNotFoundException()

        return jsonify(content.to_dict())

    def add_content(self):
        data = self.get_json()
        working_folder_path, working_folder = self.get_folder_context()

        if 'name' not in data or 'type' not in data:
            abort(400, description="Name and type are required")

        content_type = str_to_enum(data.get('type'), ContentType)
        location = data.get('location', None)

        content = self._model_store.content().add_form_raw(
            name=data.get('name'),
            type=content_type,
            request_files=request.files,
            upload_dir=self._app.config['UPLOAD_FOLDER'],
            location=location,
            folder_id=working_folder.id if working_folder else None
        )

        if not content:
            abort(400, description="Failed to add content")

        return jsonify(content.to_dict()), 201

    def upload_bulk_content(self):
        working_folder_path, working_folder = self.get_folder_context()

        for key in request.files:
            files = request.files.getlist(key)
            for file in files:
                content_type = ContentType.guess_content_type_file(file.filename)
                name = file.filename.rsplit('.', 1)[0]

                if content_type:
                    self._model_store.content().add_form_raw(
                        name=name,
                        type=content_type,
                        request_files=file,
                        upload_dir=self._app.config['UPLOAD_FOLDER'],
                        folder_id=working_folder.id if working_folder else None
                    )

        return jsonify({'status': 'ok'}), 201

    def update_content(self, content_id: int):
        data = self.get_json()
        content = self._model_store.content().get(content_id)

        if not content:
            raise ContentNotFoundException()

        if 'name' not in data:
            abort(400, description="Name is required")

        self._model_store.content().update_form(
            id=content.id,
            name=data.get('name'),
        )
        self._post_update()

        return jsonify(content.to_dict())

    def delete_content(self, content_id: int):
        content = self._model_store.content().get(content_id)

        if not content:
            raise ContentNotFoundException()

        if self._model_store.slide().count_slides_for_content(content.id) > 0:
            abort(400, description="Content is referenced in slides")

        self._model_store.content().delete(content.id)
        self._post_update()

        return jsonify({'status': 'ok'}), 204

    def rename_content(self):
        data = self.get_json()

        if 'id' not in data or 'name' not in data:
            abort(400, description="ID and name are required")

        if not self._model_store.content().get(data.get('id')):
            raise ContentNotFoundException()

        self._model_store.content().update_form(
            id=data.get('id'),
            name=data.get('name')
        )

        return jsonify({'status': 'ok'})

    def move_bulk_content(self):
        data = self.get_json()

        if 'entity_ids' not in data or 'new_folder_id' not in data:
            abort(400, description="Entity IDs and new folder ID are required")

        entity_ids = data.get('entity_ids')

        for entity_id in entity_ids:
            self._model_store.folder().move_to_folder(
                entity_id=entity_id,
                folder_id=data.get('new_folder_id'),
                entity_is_folder=False,
                entity=FolderEntity.CONTENT
            )

        return jsonify({'status': 'ok'})

    def location_content(self, content_id: int):
        content = self._model_store.content().get(content_id)

        if not content:
            raise ContentNotFoundException()

        content_location = self._model_store.content().resolve_content_location(content)

        return jsonify({'location': content_location})

    def add_folder(self):
        data = self.get_json()
        working_folder_path, working_folder = self.get_folder_context()

        folder = self._model_store.folder().add_folder(
            entity=FolderEntity.CONTENT,
            name=data.get('name'),
            working_folder_path=working_folder_path
        )

        return jsonify(folder.to_dict()), 201

    def delete_folder(self):
        working_folder_path, working_folder = self.get_folder_context()

        content_counter = self._model_store.content().count_contents_for_folder(working_folder.id)
        folder_counter = self._model_store.folder().count_subfolders_for_folder(working_folder.id)

        if content_counter > 0 or folder_counter:
            raise FolderNotEmptyException()

        self._model_store.folder().delete(id=working_folder.id)
        self._post_update()

        return jsonify({'status': 'ok'}), 204

    def rename_folder(self):
        data = self.get_json()
        working_folder_path, working_folder = self.get_folder_context()

        self._model_store.folder().rename_folder(
            folder_id=working_folder.id,
            name=data.get('name')
        )

        return jsonify({'status': 'ok'})

    def _post_update(self):
        self._model_store.variable().update_by_name("last_content_update", time.time())
