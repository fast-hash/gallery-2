"""Reusable UI components for Smart Gallery."""

from __future__ import annotations

import flet as ft


def tag_chip(label: str) -> ft.Chip:
    return ft.Chip(label=ft.Text(label), bgcolor=ft.colors.PRIMARY_CONTAINER)


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


def image_card(image_src: str, description: str, tags: list[str]) -> ft.Container:
    return ft.Container(
        border_radius=12,
        bgcolor=ft.colors.SURFACE_VARIANT,
        padding=8,
        content=ft.Column(
            [
                ft.Image(src=image_src, width=220, height=220, fit=ft.ImageFit.COVER),
                ft.Text(description, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Row([
                    tag_chip(tag) for tag in tags[:4]
                ], wrap=True, spacing=4, run_spacing=4),
            ],
            spacing=8,
        ),
    )
