"""Full-screen editor dialog for viewing and updating image metadata."""

from __future__ import annotations

from typing import Callable, List

import flet as ft
from flet import colors

from ..database import Database


class ImageDetailsDialog(ft.AlertDialog):
    """Interactive editor for image description and tags."""

    def __init__(
        self,
        database: Database,
        image_id: int,
        on_saved: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(modal=True)
        self.database = database
        self.image_id = image_id
        self.on_saved = on_saved
        self.tags: List[str] = []

        self.image = ft.Image(
            fit=ft.ImageFit.CONTAIN,
            height=320,
            border_radius=12,
            bgcolor=colors.with_opacity(0.1, colors.ON_SURFACE),
            cache_width=640,
        )
        self.description_field = ft.TextField(
            label="Description",
            multiline=True,
            min_lines=3,
            max_lines=4,
            border_radius=12,
            filled=True,
            bgcolor=colors.with_opacity(0.06, colors.ON_SURFACE),
        )
        self.new_tag_field = ft.TextField(
            label="Add tag",
            hint_text="Press Enter or tap + to add",
            border_radius=30,
            filled=True,
            bgcolor=colors.with_opacity(0.06, colors.ON_SURFACE),
            on_submit=self._handle_add_tag,
        )
        self.tags_wrap = ft.Wrap(spacing=8, run_spacing=8)

        self._build_layout()
        self._load_details()

    def _build_layout(self) -> None:
        header = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Column(
                    spacing=2,
                    controls=[
                        ft.Text("Image details", size=20, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            "Review, edit description, and manage tags.",
                            size=12,
                            color=colors.ON_SURFACE_VARIANT,
                        ),
                    ],
                ),
                ft.IconButton(
                    icon=ft.icons.CLOSE,
                    icon_size=20,
                    tooltip="Close",
                    on_click=self._dismiss,
                ),
            ],
        )

        add_tag_row = ft.Row(
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self.new_tag_field,
                ft.IconButton(
                    icon=ft.icons.ADD_ROUNDED,
                    tooltip="Add tag",
                    bgcolor=colors.PRIMARY_CONTAINER,
                    icon_color=colors.ON_PRIMARY_CONTAINER,
                    on_click=self._handle_add_tag,
                ),
            ],
        )

        actions = ft.Row(
            alignment=ft.MainAxisAlignment.END,
            controls=[
                ft.TextButton("Cancel", on_click=self._dismiss),
                ft.FilledButton(
                    "Save",
                    icon=ft.icons.SAVE_ROUNDED,
                    on_click=self._handle_save,
                ),
            ],
        )

        self.content = ft.Container(
            expand=True,
            padding=20,
            bgcolor=colors.with_opacity(0.9, colors.BLACK),
            content=ft.Container(
                expand=True,
                padding=16,
                border_radius=16,
                bgcolor=colors.with_opacity(0.08, colors.ON_SURFACE),
                content=ft.Column(
                    spacing=16,
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        header,
                        ft.Container(
                            border_radius=12,
                            bgcolor=colors.with_opacity(0.04, colors.ON_SURFACE),
                            padding=10,
                            content=self.image,
                        ),
                        self.description_field,
                        ft.Column(
                            spacing=8,
                            controls=[
                                ft.Text("Tags", weight=ft.FontWeight.W_600),
                                self.tags_wrap,
                                add_tag_row,
                            ],
                        ),
                        actions,
                    ],
                ),
            ),
        )

    def _load_details(self) -> None:
        details = self.database.get_image_details(self.image_id)
        if not details:
            self._dismiss(None)
            return

        self.image.src = details.get("path", "")
        self.description_field.value = details.get("description", "")
        self.tags = list(details.get("tags", []))
        self._refresh_tags()

    def _refresh_tags(self) -> None:
        chips: list[ft.Control] = []
        for tag in self.tags:
            chips.append(
                ft.Chip(
                    label=ft.Text(tag, color=colors.ON_PRIMARY_CONTAINER, size=11),
                    bgcolor=colors.PRIMARY_CONTAINER,
                    delete_icon=ft.icons.CLOSE,
                    delete_icon_color=colors.ON_PRIMARY_CONTAINER,
                    on_delete=lambda _, t=tag: self._remove_tag(t),
                    padding=6,
                    shape=ft.StadiumBorder(),
                )
            )

        if not chips:
            chips.append(
                ft.Chip(
                    label=ft.Text("No tags yet", color=colors.ON_SURFACE_VARIANT),
                    bgcolor=colors.SURFACE_VARIANT,
                )
            )
        self.tags_wrap.controls = chips
        if self.page:
            self.update()

    def _handle_add_tag(self, event: ft.ControlEvent | None) -> None:
        new_tag = (self.new_tag_field.value or "").strip()
        if new_tag and new_tag not in self.tags:
            self.tags.append(new_tag)
        self.new_tag_field.value = ""
        self._refresh_tags()

    def _remove_tag(self, tag: str) -> None:
        self.tags = [t for t in self.tags if t != tag]
        self._refresh_tags()

    def _handle_save(self, event: ft.ControlEvent | None) -> None:
        description = (self.description_field.value or "").strip()
        self.database.update_image_metadata(
            image_id=self.image_id, description=description, processed_flag=True
        )
        self.database.clear_tags(self.image_id)
        tag_ids = self.database.upsert_tags(self.tags)
        self.database.link_tags_to_image(self.image_id, tag_ids)

        if self.on_saved:
            self.on_saved()

        self._dismiss(event)

    def _dismiss(self, event: ft.ControlEvent | None) -> None:
        self.open = False
        if self.page:
            self.page.update()


def show_image_editor(
    page: ft.Page, database: Database, image_id: int, on_saved: Callable[[], None] | None = None
) -> ImageDetailsDialog:
    """Create and display the full-screen dialog."""

    dialog = ImageDetailsDialog(database=database, image_id=image_id, on_saved=on_saved)
    dialog.open = True
    page.dialog = dialog
    page.update()
    return dialog
