import json
import os
import time
from datetime import datetime

from flask import Flask, request, jsonify, abort, make_response
from werkzeug.utils import secure_filename
from src.service.ModelStore import ModelStore
from src.model.entity.Slide import Slide
from src.model.enum.ContentType import ContentType
from src.interface.ObController import ObController
from src.util.utils import str_to_enum, get_optional_string, str_datetime_to_cron, str_weekdaytime_to_cron
from src.util.UtilFile import randomize_filename


class SlideApiController(ObController):

    def register(self):
        self._app.add_url_rule('/api/slide', 'api_slide_add', self.add_slide, methods=['POST'])
        self._app.add_url_rule('/api/slide/notification', 'api_slide_notification_add', self.add_notification, methods=['POST'])
        self._app.add_url_rule('/api/slide/<int:slide_id>', 'api_slide_get', self.get_slide, methods=['GET'])
        self._app.add_url_rule('/api/slide/<int:slide_id>', 'api_slide_edit', self.edit_slide, methods=['PUT'])
        self._app.add_url_rule('/api/slide/<int:slide_id>', 'api_slide_delete', self.delete_slide, methods=['DELETE'])
        self._app.add_url_rule('/api/slide/positions', 'api_slide_positions', self.update_slide_positions, methods=['POST'])

    def get_slide(self, slide_id: int):
        slide = self._model_store.slide().get(slide_id)
        if not slide:
            abort(404, description="Slide not found")
        return jsonify(slide.to_dict())

    def add_slide(self):
        return self.add_slide_or_notification(is_notification=False)

    def add_notification(self):
        return self.add_slide_or_notification(is_notification=True)

    def add_slide_or_notification(self, is_notification=False):
        data = request.get_json()

        if not data or 'content_id' not in data:
            abort(400, description="Valid Content ID is required")

        if not self._model_store.content().get(data.get('content_id')):
            abort(404, description="Content not found")

        if not data or 'playlist_id' not in data:
            abort(400, description="Valid Playlist ID is required")

        if not self._model_store.playlist().get(data.get('playlist_id')):
            abort(404, description="Playlist not found")

        cron_schedule_start, cron_schedule_end = self._resolve_scheduling(data, is_notification=is_notification)

        slide = Slide(
            content_id=data.get('content_id'),
            enabled=data.get('enabled', True),
            delegate_duration=data.get('delegate_duration', False),
            duration=data.get('duration', 3),
            position=data.get('position', 999),
            is_notification=is_notification,
            playlist_id=data.get('playlist_id', None),
            cron_schedule=cron_schedule_start,
            cron_schedule_end=cron_schedule_end
        )

        slide = self._model_store.slide().add_form(slide)
        self._post_update()

        return jsonify(slide.to_dict()), 201

    def edit_slide(self, slide_id: int):
        data = request.get_json()
        if not data or 'content_id' not in data:
            abort(400, description="Content ID is required")

        slide = self._model_store.slide().get(slide_id)
        if not slide:
            abort(404, description="Slide not found")

        cron_schedule_start, cron_schedule_end = self._resolve_scheduling(data, is_notification=slide.is_notification)

        self._model_store.slide().update_form(
            id=slide_id,
            content_id=data.get('content_id', slide.content_id),
            enabled=data.get('enabled', slide.enabled),
            position=data.get('position', slide.position),
            delegate_duration=data.get('delegate_duration', slide.delegate_duration),
            duration=data.get('duration', slide.duration),
            cron_schedule=cron_schedule_start if 'scheduling' in data else slide.cron_schedule,
            cron_schedule_end=cron_schedule_end if 'scheduling' in data else slide.cron_schedule_end,
        )
        self._post_update()

        updated_slide = self._model_store.slide().get(slide_id)
        return jsonify(updated_slide.to_dict())

    def delete_slide(self, slide_id: int):
        slide = self._model_store.slide().get(slide_id)

        if not slide:
            abort(404, description="Slide not found")

        self._model_store.slide().delete(slide_id)
        self._post_update()

        return '', 204

    def update_slide_positions(self):
        data = request.get_json()
        if not data:
            abort(400, description="Positions data are required")

        self._model_store.slide().update_positions(data)
        self._post_update()
        return jsonify({'status': 'ok'})

    def _post_update(self):
        self._model_store.variable().update_by_name("last_slide_update", time.time())

    def _resolve_scheduling(self, data, is_notification=False):
        try:
            return self._resolve_scheduling_for_notification(data) if is_notification else self._resolve_scheduling_for_slide(data)
        except ValueError as ve:
            abort(400, description=str(ve))

    def _resolve_scheduling_for_slide(self, data):
        scheduling = data.get('scheduling', 'loop')
        cron_schedule_start = None
        cron_schedule_end = None

        if scheduling == 'loop':
            pass
        elif scheduling == 'datetime':
            datetime_start = data.get('datetime_start')
            datetime_end = data.get('datetime_end')

            if not datetime_start:
                abort(400, description="Field datetime_start is required for scheduling='datetime'")

            cron_schedule_start = str_datetime_to_cron(datetime_str=datetime_start)

            if datetime_end:
                cron_schedule_end = str_datetime_to_cron(datetime_str=datetime_end)
        elif scheduling == 'inweek':
            day_start = data.get('day_start')
            time_start = data.get('time_start')
            day_end = data.get('day_end')
            time_end = data.get('time_end')

            if not (day_start and time_start and day_end and time_end):
                abort(400, description="day_start, time_start, day_end, and time_end are required for scheduling='inweek'")
            cron_schedule_start = str_weekdaytime_to_cron(weekday=int(day_start), time_str=time_start)
            cron_schedule_end = str_weekdaytime_to_cron(weekday=int(day_end), time_str=time_end)
        else:
            abort(400, description="Invalid value for slide scheduling. Expected 'loop', 'datetime', or 'inweek'.")

        return cron_schedule_start, cron_schedule_end

    def _resolve_scheduling_for_notification(self, data):
        scheduling = data.get('scheduling', 'datetime')
        cron_schedule_start = None
        cron_schedule_end = None

        if scheduling == 'datetime':
            datetime_start = data.get('datetime_start')
            datetime_end = data.get('datetime_end')

            if not datetime_start:
                abort(400, description="Field datetime_start is required for scheduling='datetime'")

            cron_schedule_start = str_datetime_to_cron(datetime_str=datetime_start)

            if datetime_end:
                cron_schedule_end = str_datetime_to_cron(datetime_str=datetime_end)
        elif scheduling == 'cron':
            cron_schedule_start = data.get('cron_start')

            if not cron_schedule_start:
                abort(400, description="Field cron_start is required for scheduling='cron'")
        else:
            abort(400, description="Invalid value for notification scheduling. Expected 'datetime' or 'cron'.")

        return cron_schedule_start, cron_schedule_end
