"""Reusable UI components for Smart Gallery."""

from __future__ import annotations

from typing import Callable

import flet as ft
from flet import colors


def tag_chip(label: str) -> ft.Chip:
    return ft.Chip(
        label=ft.Text(label, color=colors.ON_PRIMARY_CONTAINER, size=11),
        bgcolor=colors.SURFACE_VARIANT,
        padding=6,
        shape=ft.StadiumBorder(),
    )


def info_snackbar(message: str) -> ft.SnackBar:
    return ft.SnackBar(ft.Text(message), open=True)


def error_snackbar(message: str) -> ft.SnackBar:
    return ft.SnackBar(ft.Text(message), open=True, bgcolor=ft.colors.ERROR_CONTAINER)


def empty_state(message: str = "No images yet") -> ft.Container:
    return ft.Container(
        content=ft.Column(
            [
                ft.Icon(name=ft.icons.COLLECTIONS, size=64, color=ft.colors.OUTLINE),
                ft.Text(message, text_align=ft.TextAlign.CENTER),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        alignment=ft.alignment.center,
        expand=True,
    )


def image_card(
    image_src: str,
    description: str,
    tags: list[str],
    on_open: Callable[[ft.ControlEvent], None] | None = None,
    on_edit: Callable[[ft.ControlEvent], None] | None = None,
) -> ft.Container:
    """Card layout used in the gallery grid."""

    edit_button = ft.Container(
        content=ft.IconButton(
            icon=ft.icons.EDIT_OUTLINED,
            icon_color=colors.ON_SURFACE_VARIANT,
            tooltip="Edit",
            on_click=on_edit,
        ),
        alignment=ft.alignment.top_right,
        padding=6,
    )

    image = ft.Container(
        content=ft.Image(
            src=image_src,
            width=280,
            height=220,
            fit=ft.ImageFit.COVER,
            cache_width=300,
            border_radius=12,
        ),
        border_radius=12,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        bgcolor=colors.with_opacity(0.08, colors.ON_SURFACE),
    )

    return ft.Container(
        on_click=on_open,
        ink=True,
        border_radius=16,
        padding=12,
        bgcolor=colors.with_opacity(0.04, colors.ON_SURFACE),
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=10,
            color=colors.with_opacity(0.2, colors.BLACK),
        ),
        content=ft.Column(
            spacing=10,
            controls=[
                ft.Stack(controls=[image, edit_button]),
                ft.Text(
                    description or "No description",
                    size=13,
                    weight=ft.FontWeight.W_600,
                    max_lines=2,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    color=colors.ON_SURFACE,
                ),
                ft.Wrap(
                    spacing=6,
                    run_spacing=6,
                    controls=[tag_chip(tag) for tag in tags[:6]] or [tag_chip("Untagged")],
                ),
            ],
        ),
    )
