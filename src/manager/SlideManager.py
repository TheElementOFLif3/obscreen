import os

from typing import Dict, Optional, List, Tuple, Union

from src.model.entity.Slide import Slide
from src.model.entity.Playlist import Playlist
from src.util.utils import get_optional_string
from src.manager.DatabaseManager import DatabaseManager
from src.manager.LangManager import LangManager
from src.manager.UserManager import UserManager
from src.manager.VariableManager import VariableManager
from src.service.ModelManager import ModelManager


class SlideManager(ModelManager):

    TABLE_NAME = "slides"
    TABLE_MODEL = [
        "uuid CHAR(255)",
        "enabled INTEGER DEFAULT 0",
        "delegate_duration INTEGER DEFAULT 0",
        "is_notification INTEGER DEFAULT 0",
        "playlist_id INTEGER",
        "content_id INTEGER",
        "duration INTEGER",
        "position INTEGER",
        "cron_schedule CHAR(255)",
        "cron_schedule_end CHAR(255)",
        "created_by CHAR(255)",
        "updated_by CHAR(255)",
        "created_at INTEGER",
        "updated_at INTEGER"
    ]

    def __init__(self, lang_manager: LangManager, database_manager: DatabaseManager, user_manager: UserManager, variable_manager: VariableManager):
        super().__init__(lang_manager, database_manager, user_manager, variable_manager)
        self._db = database_manager.open(self.TABLE_NAME, self.TABLE_MODEL)

    def hydrate_object(self, raw_slide: dict, id: int = None) -> Slide:
        if id:
            raw_slide['id'] = id

        [raw_slide, user_tracker_edits] = self.user_manager.initialize_user_trackers(raw_slide)

        if len(user_tracker_edits) > 0:
            self._db.update_by_id(self.TABLE_NAME, raw_slide['id'], user_tracker_edits)

        return Slide(**raw_slide)

    def hydrate_list(self, raw_slides: list) -> List[Slide]:
        return [self.hydrate_object(raw_slide) for raw_slide in raw_slides]

    def get(self, id: int) -> Optional[Slide]:
        object = self._db.get_by_id(self.TABLE_NAME, id)
        return self.hydrate_object(object, id) if object else None

    def get_by(self, query, sort: Optional[str] = None) -> List[Slide]:
        return self.hydrate_list(self._db.get_by_query(self.TABLE_NAME, query=query, sort=sort))

    def get_one_by(self, query) -> Optional[Slide]:
        object = self._db.get_one_by_query(self.TABLE_NAME, query=query)

        if not object:
            return None

        return self.hydrate_object(object)

    def get_all(self, sort: bool = False) -> List[Slide]:
        return self.hydrate_list(self._db.get_all(self.TABLE_NAME, sort="position" if sort else None))

    def get_all_indexed(self, attribute: str = 'id', multiple=False) -> Dict[str, Slide]:
        index = {}

        for item in self.get_slides():
            id = getattr(item, attribute)
            if multiple:
                if id not in index:
                    index[id] = []
                index[id].append(item)
            else:
                index[id] = item

        return index

    def forget_for_user(self, user_id: int):
        slides = self.get_by("created_by = '{}' or updated_by = '{}'".format(user_id, user_id))
        edits_slides = self.user_manager.forget_user_for_entity(slides, user_id)

        for slide_id, edits in edits_slides.items():
            self._db.update_by_id(self.TABLE_NAME, slide_id, edits)

    def get_slides(self, playlist_id: Optional[int] = None, content_id: Optional[int] = None, enabled: Optional[bool] = None, is_notification: Optional[bool] = None) -> List[Slide]:
        query = " 1=1 "

        if enabled is not None:
            query = "{} AND enabled = {} ".format(query, "1" if enabled else "0")

        if is_notification is not None:
            query = "{} AND is_notification = {} ".format(query, "1" if is_notification else "0")

        if playlist_id:
            query = "{} {}".format(query, "AND playlist_id = {}".format(playlist_id))

        if content_id:
            if isinstance(content_id, bool):
                query = "{} {}".format(query, "AND content_id IS NOT NULL")
            else:
                query = "{} {}".format(query, "AND content_id = {}".format(content_id))

        return self.get_by(query=query, sort="position")

    def pre_add(self, slide: Dict) -> Dict:
        self.user_manager.track_user_on_create(slide)
        self.user_manager.track_user_on_update(slide)
        return slide

    def pre_update(self, slide: Dict) -> Dict:
        self.user_manager.track_user_on_update(slide)
        return slide

    def pre_delete(self, slide_id: str) -> str:
        return slide_id

    def post_add(self, slide_id: str) -> str:
        return slide_id

    def post_update(self, slide_id: str) -> str:
        return slide_id

    def post_updates(self):
        pass

    def post_delete(self, slide_id: str) -> str:
        return slide_id
        
    def update_positions(self, positions: list) -> None:
        for slide_id, slide_position in positions.items():
            self._db.update_by_id(self.TABLE_NAME, slide_id, {"position": slide_position})

    def update_form(self, id: int, duration: Optional[int] = None, content_id: Optional[int] = None, delegate_duration: Optional[bool] = None, is_notification: Optional[bool] = None, cron_schedule: Optional[str] = '', cron_schedule_end: Optional[str] = '', enabled: Optional[bool] = None, position: Optional[int] = None) -> Optional[Slide]:
        slide = self.get(id)

        if not slide:
            return

        form = {
            "duration": duration if duration else slide.duration,
            "content_id": content_id if content_id else slide.content_id,
            "position": position if isinstance(position, int) else slide.position,
            "enabled": enabled if isinstance(enabled, bool) else slide.enabled,
            "delegate_duration": delegate_duration if isinstance(delegate_duration, bool) else slide.delegate_duration,
            "is_notification": is_notification if isinstance(is_notification, bool) else slide.is_notification,
            "cron_schedule": get_optional_string(cron_schedule),
            "cron_schedule_end": get_optional_string(cron_schedule_end)
        }

        self._db.update_by_id(self.TABLE_NAME, id, self.pre_update(form))
        self.post_update(id)
        return self.get(id)

    def add_form(self, slide: Union[Slide, Dict]) -> Slide:
        form = slide

        if not isinstance(slide, dict):
            form = slide.to_dict()
            del form['id']

        self._db.add(self.TABLE_NAME, self.pre_add(form))
        self.post_add(slide.id)
        return self.get_one_by(query="uuid = '{}'".format(slide.uuid))

    def delete(self, id: int) -> None:
        slide = self.get(id)

        if slide:
            self.pre_delete(id)
            self._db.delete_by_id(self.TABLE_NAME, id)
            self.post_delete(id)

    def to_dict(self, slides: List[Slide]) -> List[Dict]:
        return [slide.to_dict() for slide in slides]

    def count_slides_for_playlist(self, id: int) -> int:
        return len(self.get_slides(playlist_id=id))

    def count_slides_for_content(self, id: int) -> int:
        return len(self.get_slides(content_id=id))
