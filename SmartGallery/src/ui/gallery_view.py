"""Gallery grid view with lazy-friendly loading and file picker support."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import flet as ft

from ..ai_engine import AIEngine
from ..database import Database
from .components import empty_state, error_snackbar, image_card, info_snackbar
from .image_details import show_image_editor


class GalleryView(ft.UserControl):
    """Main gallery view with a bottom-friendly layout for mobile."""

    def __init__(self, database: Database, ai_engine: AIEngine) -> None:
        super().__init__()
        self.database = database
        self.ai_engine = ai_engine
        self.grid = ft.GridView(
            expand=True,
            runs_count=2,
            max_extent=260,
            child_aspect_ratio=0.78,
            spacing=12,
            run_spacing=12,
        )
        self.file_picker = ft.FilePicker(on_result=self._handle_file_picker_result)
        self.page: Optional[ft.Page] = None
        self.search_field = ft.TextField(
            hint_text="Search by description or tag...",
            prefix_icon=ft.icons.SEARCH,
            border_radius=14,
            dense=True,
            filled=True,
            autofocus=False,
            on_change=self._handle_search_change,
        )

    def build(self) -> ft.Column:
        search_bar = ft.Container(
            bgcolor=ft.colors.with_opacity(0.06, ft.colors.ON_SURFACE),
            border_radius=14,
            padding=8,
            content=self.search_field,
        )

        return ft.Column(
            [search_bar, self.grid],
            expand=True,
            spacing=12,
        )

    def did_mount(self) -> None:
        self.page = self.page or self._control.page
        if self.page:
            self.page.floating_action_button = ft.FloatingActionButton(
                icon=ft.icons.ADD_ROUNDED,
                text="Add photos",
                bgcolor=ft.colors.PRIMARY_CONTAINER,
                foreground_color=ft.colors.ON_PRIMARY_CONTAINER,
                on_click=lambda _: self.file_picker.pick_files(allow_multiple=True),
            )
            self.page.update()
        self.refresh_gallery()

    def refresh_gallery(self) -> None:
        query = (self.search_field.value or "").strip()
        images = (
            self.database.search_images(query=query, limit=200) if query else self.database.get_images(limit=200)
        )
        if not images:
            self.grid.controls = [
                empty_state("No images match your search" if query else "No images yet")
            ]
        else:
            cards = []
            for image in images:
                tags = self.database.get_tags_for_image(image_id=int(image["id"]))
                cards.append(
                    image_card(
                        image_src=str(image["path"]),
                        description=image.get("description", ""),
                        tags=tags,
                        on_open=lambda _, image_id=image["id"]: self._open_details(image_id),
                        on_edit=lambda _, image_id=image["id"]: self._open_details(image_id),
                    )
                )
            self.grid.controls = cards
        self.update()

    def _handle_file_picker_result(self, event: ft.FilePickerResultEvent) -> None:
        if not event.files:
            return

        for picked_file in event.files:
            path = Path(picked_file.path)
            image_id = self.database.add_image(path)
            analysis = self.ai_engine.analyze_image(path)
            self.database.update_image_metadata(
                image_id=image_id,
                description=analysis.get("description", ""),
                processed_flag=True,
            )
            tag_ids = self.database.upsert_tags(analysis.get("tags", []))
            self.database.link_tags_to_image(image_id, tag_ids)

        if self.page:
            self.page.snack_bar = info_snackbar("Images added to gallery")
            self.page.snack_bar.open = True
            self.page.update()
        self.refresh_gallery()

    def show_error(self, message: str) -> None:
        if self.page:
            self.page.snack_bar = error_snackbar(message)
            self.page.snack_bar.open = True
            self.page.update()

    def _handle_search_change(self, event: ft.ControlEvent) -> None:
        self.refresh_gallery()

    def _open_details(self, image_id: int) -> None:
        if not self.page:
            return
        show_image_editor(
            page=self.page,
            database=self.database,
            image_id=image_id,
            on_saved=self.refresh_gallery,
        )
