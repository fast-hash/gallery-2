"""Gallery grid view with lazy-friendly loading and file picker support."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import flet as ft

from ..ai_engine import AIEngine
from ..database import Database
from .components import empty_state, error_snackbar, image_card, info_snackbar


class GalleryView(ft.UserControl):
    """Main gallery view with a bottom-friendly layout for mobile."""

    def __init__(self, database: Database, ai_engine: AIEngine) -> None:
        super().__init__()
        self.database = database
        self.ai_engine = ai_engine
        self.grid = ft.GridView(
            expand=True,
            runs_count=2,
            max_extent=240,
            child_aspect_ratio=0.75,
            spacing=8,
            run_spacing=8,
        )
        self.file_picker = ft.FilePicker(on_result=self._handle_file_picker_result)
        self.page: Optional[ft.Page] = None

    def build(self) -> ft.Column:
        add_button = ft.FilledButton(
            "Add images", on_click=lambda _: self.file_picker.pick_files(allow_multiple=True)
        )
        header = ft.Row(
            [add_button],
            alignment=ft.MainAxisAlignment.END,
        )

        return ft.Column(
            [self.file_picker, header, self.grid],
            expand=True,
            spacing=12,
        )

    def did_mount(self) -> None:
        self.page = self.page or self._control.page
        self.refresh_gallery()

    def refresh_gallery(self) -> None:
        images = self.database.get_images(limit=200)
        if not images:
            self.grid.controls = [empty_state()]
        else:
            cards = []
            for image in images:
                tags = self.database.get_tags_for_image(image_id=int(image["id"]))
                cards.append(
                    image_card(
                        image_src=str(image["path"]),
                        description=image.get("description", ""),
                        tags=tags,
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
