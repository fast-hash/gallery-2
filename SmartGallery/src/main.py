"""Entry point for the Smart Gallery Flet application."""

from __future__ import annotations

import flet as ft

from .ai_engine import AIEngine
from .database import Database
from .ui.gallery_view import GalleryView


def main(page: ft.Page) -> None:
    page.title = "Smart Gallery"
    page.padding = 12
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(
        color_scheme_seed="#82b1ff",
        scaffold_background_color="#1a1c1e",
        card_color=ft.colors.with_opacity(0.08, ft.colors.ON_SURFACE),
        use_material3=True,
    )
    page.bgcolor = "#1a1c1e"
    page.vertical_alignment = ft.MainAxisAlignment.START

    database = Database()
    ai_engine = AIEngine()

    gallery_view = GalleryView(database=database, ai_engine=ai_engine)

    def handle_navigation_change(event: ft.ControlEvent) -> None:
        index = int(event.control.selected_index)
        if index != 0 and page.snack_bar is None:
            page.snack_bar = ft.SnackBar(ft.Text("Only Gallery is available in this preview."))
            page.snack_bar.open = True
            page.update()

    page.navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationDestination(icon=ft.icons.COLLECTIONS, label="Gallery"),
            ft.NavigationDestination(icon=ft.icons.SETTINGS, label="Settings"),
        ],
        on_change=handle_navigation_change,
    )

    page.overlay.append(gallery_view.file_picker)
    page.add(gallery_view)


if __name__ == "__main__":
    ft.app(target=main)
