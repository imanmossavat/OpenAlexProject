from __future__ import annotations

import io
from typing import Dict, Sequence

import polars as pl
import xlsxwriter
from xlsxwriter.utility import xl_col_to_name

from app.repositories import PaperAnnotationRepository, PaperCatalogRepository


class PaperCatalogExporter:
    """Create downloadable catalog exports."""

    def __init__(
        self,
        catalog_repository: PaperCatalogRepository,
        annotation_repository: PaperAnnotationRepository,
        *,
        mark_column: str,
    ) -> None:
        self._catalog_repo = catalog_repository
        self._annotation_repo = annotation_repository
        self._mark_column = mark_column

    def export(self, job_id: str) -> bytes:
        lf = self._catalog_repo.scan_catalog(job_id)
        mark_lookup = self._annotation_repo.load_marks(job_id) or {}
        if mark_lookup:
            lf = lf.with_columns(
                pl.col("paperId")
                .cast(pl.Utf8, strict=False)
                .replace(mark_lookup, default="standard")
                .fill_null("standard")
                .alias(self._mark_column)
            )
        else:
            lf = lf.with_columns(pl.lit("standard").alias(self._mark_column))

        export_frame = (
            lf.with_columns(pl.col(self._mark_column).alias("annotation_mark"))
            .drop(self._mark_column)
        )
        df = export_frame.collect()
        if df.is_empty():
            df = df.select(pl.all())
        if "annotation_mark" not in df.columns:
            df = df.with_columns(pl.lit("standard").alias("annotation_mark"))

        buffer = io.BytesIO()
        workbook = xlsxwriter.Workbook(buffer, {"in_memory": True})
        worksheet = workbook.add_worksheet("Catalog")

        header_fmt = workbook.add_format({"bold": True, "bg_color": "#f3f4f6"})
        default_width = 18
        column_widths: Dict[str, int] = {
            "title": 42,
            "authors_display": 36,
            "doi": 30,
            "venue": 26,
            "nmf_topic": 18,
            "lda_topic": 18,
        }

        columns = df.columns
        for col_idx, name in enumerate(columns):
            worksheet.write(0, col_idx, name, header_fmt)
            worksheet.set_column(col_idx, col_idx, column_widths.get(name, default_width))

        for row_idx, row in enumerate(df.iter_rows(named=True), start=1):
            for col_idx, name in enumerate(columns):
                worksheet.write(row_idx, col_idx, self._format_value(row.get(name)))

        row_count = df.height
        if row_count > 0:
            mark_index = columns.index("annotation_mark")
            mark_letter = xl_col_to_name(mark_index)
            last_col_letter = xl_col_to_name(len(columns) - 1)
            start_row = 2
            last_row = row_count + 1
            data_range = f"A{start_row}:{last_col_letter}{last_row}"
            formats = self._mark_formats(workbook)
            for mark_value, cell_format in formats.items():
                worksheet.conditional_format(
                    data_range,
                    {
                        "type": "formula",
                        "criteria": f'=${mark_letter}{start_row}="{mark_value}"',
                        "format": cell_format,
                    },
                )

        workbook.close()
        buffer.seek(0)
        return buffer.getvalue()

    def _format_value(self, value):
        if isinstance(value, list):
            return ", ".join(str(item) for item in value if item not in (None, ""))
        return value

    def _mark_formats(self, workbook) -> Dict[str, "xlsxwriter.format.Format"]:
        return {
            "good": workbook.add_format({"bg_color": "#dcfce7", "font_color": "#166534"}),
            "neutral": workbook.add_format({"bg_color": "#fef9c3", "font_color": "#854d0e"}),
            "bad": workbook.add_format({"bg_color": "#fee2e2", "font_color": "#991b1b"}),
        }
