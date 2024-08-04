from flask import Flask, render_template, jsonify, request, abort, make_response

from src.model.entity.Playlist import Playlist
from src.interface.ObController import ObController


class PlaylistApiController(ObController):

    def register(self):
        self._app.add_url_rule('/api/playlist', 'api_playlist_list', self.get_playlists, methods=['GET'])
        self._app.add_url_rule('/api/playlist', 'api_playlist_add', self.add_playlist, methods=['POST'])
        self._app.add_url_rule('/api/playlist/<int:playlist_id>', 'api_playlist_get', self.get_playlist, methods=['GET'])
        self._app.add_url_rule('/api/playlist/<int:playlist_id>', 'api_playlist_update', self.update_playlist, methods=['PUT'])
        self._app.add_url_rule('/api/playlist/<int:playlist_id>', 'api_playlist_delete', self.delete_playlist, methods=['DELETE'])
        self._app.add_url_rule('/api/playlist/<int:playlist_id>/slides', 'api_playlist_list_slides', self.get_playlists_slides, methods=['GET'])
        self._app.add_url_rule('/api/playlist/<int:playlist_id>/notifications', 'api_playlist_list_notifications', self.get_playlists_notifications, methods=['GET'])

    def get_playlists(self):
        playlists = self._model_store.playlist().get_all(sort="created_at", ascending=True)
        result = [playlist.to_dict() for playlist in playlists]
        return jsonify(result)

    def get_playlist(self, playlist_id: int):
        playlist = self._model_store.playlist().get(playlist_id)
        if not playlist:
            abort(404, description="Playlist not found")
        return jsonify(playlist.to_dict())

    def add_playlist(self):
        data = request.get_json()
        if not data or 'name' not in data:
            abort(400, description="Invalid input")

        playlist = Playlist(
            name=data.get('name'),
            enabled=data.get('enabled', True),
            time_sync=data.get('time_sync', False)
        )

        try:
            playlist = self._model_store.playlist().add_form(playlist)
        except Exception as e:
            abort(409, description=str(e))

        return jsonify(playlist.to_dict()), 201

    def update_playlist(self, playlist_id: int):
        data = request.get_json()
        if not data or 'name' not in data:
            abort(400, description="Invalid input")

        playlist = self._model_store.playlist().get(playlist_id)
        if not playlist:
            abort(404, description="Playlist not found")

        self._model_store.playlist().update_form(
            id=playlist_id,
            name=data.get('name', playlist.name),
            time_sync=data.get('time_sync', playlist.time_sync),
            enabled=data.get('enabled', playlist.enabled)
        )
        updated_playlist = self._model_store.playlist().get(playlist_id)
        return jsonify(updated_playlist.to_dict())

    def delete_playlist(self, playlist_id: int):
        playlist = self._model_store.playlist().get(playlist_id)
        if not playlist:
            abort(404, description="Playlist not found")

        if self._model_store.slide().count_slides_for_playlist(playlist_id) > 0:
            abort(400, description="Playlist cannot be deleted because it has slides")

        if self._model_store.node_player_group().count_node_player_groups_for_playlist(playlist_id) > 0:
            abort(400, description="Playlist cannot be deleted because it is associated with node player groups")

        self._model_store.playlist().delete(playlist_id)
        return '', 204

    def get_playlists_slides(self, playlist_id: int):
        playlist = self._model_store.playlist().get(playlist_id)

        if not playlist:
            abort(404, description="Playlist not found")

        slides = self._model_store.slide().get_slides(is_notification=False, playlist_id=playlist_id)

        result = [slide.to_dict() for slide in slides]
        return jsonify(result)

    def get_playlists_notifications(self, playlist_id: int):
        playlist = self._model_store.playlist().get(playlist_id)

        if not playlist:
            abort(404, description="Playlist not found")

        slides = self._model_store.slide().get_slides(is_notification=True, playlist_id=playlist_id)

        result = [slide.to_dict() for slide in slides]
        return jsonify(result)
