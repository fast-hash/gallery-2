"""Gallery grid view with lazy-friendly loading and file picker support."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

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
            runs_count=0,
            max_extent=280,
            child_aspect_ratio=0.78,
            spacing=12,
            run_spacing=12,
        )
        self.folder_list = ft.Column(spacing=16, expand=True)
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
        self.sort_dropdown = ft.Dropdown(
            width=190,
            dense=True,
            value="desc",
            filled=True,
            border_radius=14,
            options=[
                ft.dropdown.Option("desc", "Newest first"),
                ft.dropdown.Option("asc", "Oldest first"),
            ],
            on_change=self._handle_sort_change,
        )
        self.view_tabs = ft.Tabs(
            selected_index=0,
            animation_duration=150,
            expand=True,
            tabs=[
                ft.Tab(text="All photos", icon=ft.icons.GRID_VIEW, content=self.grid),
                ft.Tab(
                    text="By folder",
                    icon=ft.icons.FOLDER_OPEN,
                    content=ft.Container(content=self.folder_list, padding=ft.padding.only(top=8), expand=True),
                ),
            ],
            on_change=self._handle_tab_change,
        )

    def build(self) -> ft.Column:
        search_bar = ft.Container(
            bgcolor=ft.colors.with_opacity(0.06, ft.colors.ON_SURFACE),
            border_radius=14,
            padding=8,
            expand=True,
            content=self.search_field,
            col={"xs": 12, "sm": 12, "md": 8},
        )

        self.sort_dropdown.col = {"xs": 12, "sm": 12, "md": 4}

        controls = ft.ResponsiveRow(
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[search_bar, self.sort_dropdown],
        )

        return ft.Column(
            [controls, self.view_tabs],
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
        images = self._fetch_images()
        if self.view_tabs.selected_index == 0:
            self._render_all_images(images)
        else:
            self._render_folder_groups(images)
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

    def _handle_sort_change(self, event: ft.ControlEvent) -> None:
        self.refresh_gallery()

    def _handle_tab_change(self, event: ft.ControlEvent) -> None:
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

    def _current_sort_order(self) -> str:
        return "asc" if (self.sort_dropdown.value or "").startswith("asc") else "desc"

    def _fetch_images(self) -> List[dict]:
        query = (self.search_field.value or "").strip()
        sort_order = self._current_sort_order()
        return (
            self.database.search_images(query=query, limit=200, order=sort_order)
            if query
            else self.database.get_images(limit=200, order=sort_order)
        )

    def _render_all_images(self, images: List[dict]) -> None:
        if not images:
            self.grid.controls = [
                empty_state("No images match your search" if (self.search_field.value or "").strip() else "No images yet")
            ]
            return

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

    def _render_folder_groups(self, images: List[dict]) -> None:
        if not images:
            self.folder_list.controls = [
                empty_state("No images match your search" if (self.search_field.value or "").strip() else "No images yet")
            ]
            return

        grouped: Dict[str, list[dict]] = {}
        for image in images:
            folder_name = Path(image["path"]).parent.name or "Uncategorized"
            grouped.setdefault(folder_name, []).append(image)

        sections: list[ft.Control] = []
        for folder_name in sorted(grouped.keys()):
            folder_images = grouped[folder_name]
            grid = ft.Wrap(
                spacing=12,
                run_spacing=12,
                controls=[
                    image_card(
                        image_src=str(img["path"]),
                        description=img.get("description", ""),
                        tags=self.database.get_tags_for_image(image_id=int(img["id"])),
                        on_open=lambda _, image_id=img["id"]: self._open_details(image_id),
                        on_edit=lambda _, image_id=img["id"]: self._open_details(image_id),
                    )
                    for img in folder_images
                ],
            )
            sections.append(
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.icons.FOLDER_OUTLINED, color=ft.colors.ON_SURFACE_VARIANT),
                                ft.Text(folder_name, size=15, weight=ft.FontWeight.BOLD),
                                ft.Text(f"{len(folder_images)}", color=ft.colors.ON_SURFACE_VARIANT),
                            ],
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        grid,
                        ft.Divider(height=1),
                    ],
                )
            )

        self.folder_list.controls = sections
