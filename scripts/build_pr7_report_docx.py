#!/usr/bin/env python3
"""Build a GOST-formatted DOCX report for Practical work #7."""

from __future__ import annotations

import datetime as dt
import html
import re
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "out"
DOCX_PATH = OUT_DIR / "Отчет_ПЗ7_ГОСТ.docx"

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def clean_spaces(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def rpr(bold: bool = False) -> str:
    bold_xml = "<w:b/><w:bCs/>" if bold else ""
    return (
        "<w:rPr>"
        "<w:rFonts w:ascii=\"Times New Roman\" w:hAnsi=\"Times New Roman\" w:cs=\"Times New Roman\"/>"
        "<w:color w:val=\"000000\"/>"
        "<w:sz w:val=\"28\"/><w:szCs w:val=\"28\"/>"
        f"{bold_xml}"
        "</w:rPr>"
    )


def paragraph(
    text: str,
    *,
    align: str = "both",
    first_line: int = 710,
    bold: bool = False,
    page_break_before: bool = False,
) -> str:
    text = clean_spaces(text)
    ppr = (
        "<w:pPr>"
        f"<w:jc w:val=\"{align}\"/>"
        "<w:spacing w:before=\"0\" w:after=\"0\" w:line=\"360\" w:lineRule=\"auto\"/>"
        f"<w:ind w:firstLine=\"{first_line}\"/>"
        "</w:pPr>"
    )
    br = "<w:r><w:br w:type=\"page\"/></w:r>" if page_break_before else ""
    if not text:
        return f"<w:p>{ppr}{br}</w:p>"
    return (
        f"<w:p>{ppr}{br}"
        f"<w:r>{rpr(bold=bold)}<w:t xml:space=\"preserve\">{esc(text)}</w:t></w:r>"
        "</w:p>"
    )


def table_cell_paragraph(text: str, *, align: str = "left", bold: bool = False) -> str:
    text = clean_spaces(text)
    return (
        "<w:p>"
        "<w:pPr>"
        f"<w:jc w:val=\"{align}\"/>"
        "<w:spacing w:before=\"0\" w:after=\"0\" w:line=\"360\" w:lineRule=\"auto\"/>"
        "<w:ind w:firstLine=\"0\"/>"
        "</w:pPr>"
        f"<w:r>{rpr(bold=bold)}<w:t xml:space=\"preserve\">{esc(text)}</w:t></w:r>"
        "</w:p>"
    )


def build_table(rows: list[tuple[str, str]]) -> str:
    body_rows: list[str] = []
    header = (
        "<w:tr>"
        "<w:tc><w:tcPr><w:tcW w:w=\"5300\" w:type=\"dxa\"/></w:tcPr>"
        + table_cell_paragraph("Сценарий use case", align="center", bold=True)
        + "</w:tc>"
        "<w:tc><w:tcPr><w:tcW w:w=\"4200\" w:type=\"dxa\"/></w:tcPr>"
        + table_cell_paragraph("Действия и endpoint в Swagger", align="center", bold=True)
        + "</w:tc>"
        "</w:tr>"
    )
    body_rows.append(header)

    for left, right in rows:
        body_rows.append(
            "<w:tr>"
            "<w:tc><w:tcPr><w:tcW w:w=\"5300\" w:type=\"dxa\"/></w:tcPr>"
            + table_cell_paragraph(left)
            + "</w:tc>"
            "<w:tc><w:tcPr><w:tcW w:w=\"4200\" w:type=\"dxa\"/></w:tcPr>"
            + table_cell_paragraph(right)
            + "</w:tc>"
            "</w:tr>"
        )

    return (
        "<w:tbl>"
        "<w:tblPr>"
        "<w:tblW w:w=\"0\" w:type=\"auto\"/>"
        "<w:tblBorders>"
        "<w:top w:val=\"single\" w:sz=\"8\" w:space=\"0\" w:color=\"000000\"/>"
        "<w:left w:val=\"single\" w:sz=\"8\" w:space=\"0\" w:color=\"000000\"/>"
        "<w:bottom w:val=\"single\" w:sz=\"8\" w:space=\"0\" w:color=\"000000\"/>"
        "<w:right w:val=\"single\" w:sz=\"8\" w:space=\"0\" w:color=\"000000\"/>"
        "<w:insideH w:val=\"single\" w:sz=\"8\" w:space=\"0\" w:color=\"000000\"/>"
        "<w:insideV w:val=\"single\" w:sz=\"8\" w:space=\"0\" w:color=\"000000\"/>"
        "</w:tblBorders>"
        "</w:tblPr>"
        "<w:tblGrid><w:gridCol w:w=\"5300\"/><w:gridCol w:w=\"4200\"/></w:tblGrid>"
        + "".join(body_rows)
        + "</w:tbl>"
    )


def build_document_xml(parts: list[str]) -> str:
    body = "".join(parts)
    sectpr = (
        "<w:sectPr>"
        "<w:footerReference w:type=\"default\" r:id=\"rId1\"/>"
        "<w:pgSz w:w=\"11906\" w:h=\"16838\"/>"
        "<w:pgMar w:top=\"1134\" w:right=\"567\" w:bottom=\"1134\" w:left=\"1701\" w:header=\"708\" w:footer=\"708\" w:gutter=\"0\"/>"
        "<w:pgNumType w:start=\"1\"/>"
        "<w:titlePg/>"
        "</w:sectPr>"
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W_NS}" xmlns:r="{R_NS}">'
        f"<w:body>{body}{sectpr}</w:body>"
        "</w:document>"
    )


def build_footer_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:ftr xmlns:w="{W_NS}">'
        "<w:p>"
        "<w:pPr><w:jc w:val=\"center\"/></w:pPr>"
        f"<w:r>{rpr()}<w:fldChar w:fldCharType=\"begin\"/></w:r>"
        f"<w:r>{rpr()}<w:instrText xml:space=\"preserve\"> PAGE </w:instrText></w:r>"
        f"<w:r>{rpr()}<w:fldChar w:fldCharType=\"separate\"/></w:r>"
        f"<w:r>{rpr()}<w:t>1</w:t></w:r>"
        f"<w:r>{rpr()}<w:fldChar w:fldCharType=\"end\"/></w:r>"
        "</w:p>"
        "</w:ftr>"
    )


def build_styles_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:styles xmlns:w="{W_NS}">'
        "<w:docDefaults>"
        "<w:rPrDefault><w:rPr>"
        "<w:rFonts w:ascii=\"Times New Roman\" w:hAnsi=\"Times New Roman\" w:cs=\"Times New Roman\"/>"
        "<w:color w:val=\"000000\"/>"
        "<w:sz w:val=\"28\"/><w:szCs w:val=\"28\"/>"
        "</w:rPr></w:rPrDefault>"
        "<w:pPrDefault><w:pPr>"
        "<w:jc w:val=\"both\"/>"
        "<w:spacing w:before=\"0\" w:after=\"0\" w:line=\"360\" w:lineRule=\"auto\"/>"
        "<w:ind w:firstLine=\"710\"/>"
        "</w:pPr></w:pPrDefault>"
        "</w:docDefaults>"
        "<w:style w:type=\"paragraph\" w:default=\"1\" w:styleId=\"Normal\">"
        "<w:name w:val=\"Normal\"/>"
        "</w:style>"
        "</w:styles>"
    )


def build_settings_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:settings xmlns:w="{W_NS}">'
        "<w:zoom w:percent=\"100\"/>"
        "</w:settings>"
    )


def build_document_rels_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>'
        "</Relationships>"
    )


def build_content_types_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
        '<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>'
        '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>'
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
        "</Types>"
    )


def build_package_rels_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
        "</Relationships>"
    )


def build_core_xml() -> str:
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<cp:coreProperties '
        'xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:dcmitype="http://purl.org/dc/dcmitype/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        "<dc:title>Отчет по практической работе №7</dc:title>"
        "<dc:creator>Студент</dc:creator>"
        "<cp:lastModifiedBy>Codex</cp:lastModifiedBy>"
        f'<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>'
        "</cp:coreProperties>"
    )


def build_app_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
        'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
        "<Application>Codex</Application>"
        "</Properties>"
    )


def compose_report_content() -> list[str]:
    year = dt.datetime.now().year
    today = dt.datetime.now().strftime("%d.%m.%Y")

    mapping_rows = [
        (
            "UC-AI1. Получить персональные рекомендации товаров",
            "Swagger AI: GET /recommendations (user_id, context). Swagger Catalog: GET /products?user_id=...",
        ),
        (
            "UC-AI2. Дать фидбек по рекомендациям",
            "Swagger AI: POST /recommendations/feedback (request_id, user_id, item_id, action).",
        ),
        (
            "UC-AI3. Проверить карточку товара",
            "Swagger AI: POST /moderation/check. В Catalog вызывается при POST /products и PUT /products/{id}.",
        ),
        (
            "UC-AI4. Оспорить решение модерации",
            "Swagger AI: POST /moderation/appeals и POST /moderation/appeals/{appeal_id}/result.",
        ),
        (
            "UC-AI5. Просмотреть статистику модели",
            "Swagger AI: GET /models/active, GET /models, GET /training/jobs.",
        ),
        (
            "UC-AI6. Запустить переобучение модели",
            "Swagger AI: POST /training/recommendation/run (lookback_days, epochs, learning_rate и др.).",
        ),
        (
            "UC-AI7. Переобучиться на новых данных",
            "Swagger AI: /training/recommendation/run + данные из /recommendations, /recommendations/feedback, /events.",
        ),
    ]

    p: list[str] = []

    # Title page
    p.append(paragraph("ФГБОУ ВО «Уфимский университет науки и технологий»", align="center", first_line=0))
    p.append(paragraph("Кафедра технической кибернетики", align="center", first_line=0))
    p.append(paragraph("", align="center", first_line=0))
    p.append(paragraph("ОТЧЁТ ПО ПРАКТИЧЕСКОЙ РАБОТЕ №7", align="center", first_line=0, bold=True))
    p.append(paragraph("по дисциплине «Интеллектуальные информационные системы»", align="center", first_line=0))
    p.append(paragraph("Тема: Сопоставление use case сценариев и действий в Swagger", align="center", first_line=0, bold=True))
    p.append(paragraph("", align="center", first_line=0))
    p.append(paragraph("Выполнил: ст. гр. ИВТ-432Б", align="right", first_line=0))
    p.append(paragraph("Зиязетдинов Д.С.", align="right", first_line=0))
    p.append(paragraph("Проверил: доцент кафедры", align="right", first_line=0))
    p.append(paragraph("", align="center", first_line=0))
    p.append(paragraph(f"Уфа {year} г.", align="center", first_line=0))

    p.append(paragraph("", page_break_before=True, first_line=0))

    # 1
    p.append(paragraph("1 Введение", bold=True, first_line=0, align="left"))
    p.append(
        paragraph(
            "Согласно заданию практической работы №7 необходимо на основе разработанных use case диаграмм и сценариев вариантов "
            "выполнить сопоставление действий в интерфейсе Swagger соответствующим сценариям использования системы."
        )
    )
    p.append(
        paragraph(
            "В качестве исходных материалов использованы диаграммы и сценарии из ранее подготовленного отчёта, "
            "где описаны сценарии UC-AI1 ... UC-AI7 для интеллектуальной компоненты системы mini-ozon."
        )
    )

    # 2
    p.append(paragraph("2 Цель работы", bold=True, first_line=0, align="left"))
    p.append(
        paragraph(
            "Проверить трассируемость сценариев use case к конкретным API-методам, доступным в Swagger, "
            "и подтвердить практическую реализуемость бизнес-сценариев интеллектуальной подсистемы."
        )
    )

    # 3
    p.append(paragraph("3 Ход работы", bold=True, first_line=0, align="left"))
    p.append(paragraph("1) Проанализированы формулировки сценариев UC-AI1 ... UC-AI7 из отчёта ПР3."))
    p.append(paragraph("2) Определены сервисы и эндпоинты, реализующие каждый сценарий."))
    p.append(paragraph("3) Выполнена проверка доступности методов через Swagger интерфейс сервисов."))
    p.append(paragraph("4) Сформирована таблица соответствия «Use Case -> Действия в Swagger»."))
    p.append(paragraph("5) Подготовлены контрольные точки для демонстрации выполнения сценариев."))

    # 4
    p.append(paragraph("4 Результаты", bold=True, first_line=0, align="left"))
    p.append(paragraph("Таблица 1 – Сопоставление сценариев use case с действиями в Swagger", first_line=0, align="left"))
    p.append(build_table(mapping_rows))
    p.append(paragraph("", first_line=0))
    p.append(
        paragraph(
            "Проведённое сопоставление показывает, что все ключевые сценарии интеллектуальной подсистемы "
            "поддержаны API-методами и доступны для демонстрации в Swagger."
        )
    )
    p.append(
        paragraph(
            "Сценарии персонализации, сбора обратной связи и обучения модели образуют замкнутый цикл: "
            "выдача рекомендаций -> пользовательский фидбек -> формирование обучающих данных -> запуск переобучения."
        )
    )

    p.append(paragraph("[МЕСТО ДЛЯ СКРИНШОТА]", align="center", first_line=0, bold=True))
    p.append(paragraph("Рисунок 1 – Swagger AI Service: endpoint /recommendations", first_line=0, align="left"))
    p.append(paragraph("[МЕСТО ДЛЯ СКРИНШОТА]", align="center", first_line=0, bold=True))
    p.append(paragraph("Рисунок 2 – Swagger AI Service: endpoint /recommendations/feedback", first_line=0, align="left"))
    p.append(paragraph("[МЕСТО ДЛЯ СКРИНШОТА]", align="center", first_line=0, bold=True))
    p.append(paragraph("Рисунок 3 – Swagger AI Service: endpoint /moderation/check", first_line=0, align="left"))
    p.append(paragraph("[МЕСТО ДЛЯ СКРИНШОТА]", align="center", first_line=0, bold=True))
    p.append(paragraph("Рисунок 4 – Swagger AI Service: endpoint /training/recommendation/run", first_line=0, align="left"))

    # 5
    p.append(paragraph("5 Вывод", bold=True, first_line=0, align="left"))
    p.append(
        paragraph(
            "В ходе ПЗ7 выполнено сопоставление use case сценариев и действий в Swagger для интеллектуальной компоненты системы. "
            "Получена единая карта соответствия, подтверждающая, что описанные сценарии реализованы на уровне API и могут быть воспроизведены при демонстрации."
        )
    )
    p.append(paragraph(f"Дата формирования отчёта: {today}."))

    return p


def create_docx(document_xml: str, output_path: Path) -> None:
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", build_content_types_xml())
        zf.writestr("_rels/.rels", build_package_rels_xml())
        zf.writestr("word/document.xml", document_xml)
        zf.writestr("word/styles.xml", build_styles_xml())
        zf.writestr("word/settings.xml", build_settings_xml())
        zf.writestr("word/footer1.xml", build_footer_xml())
        zf.writestr("word/_rels/document.xml.rels", build_document_rels_xml())
        zf.writestr("docProps/core.xml", build_core_xml())
        zf.writestr("docProps/app.xml", build_app_xml())


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    content_parts = compose_report_content()
    document_xml = build_document_xml(content_parts)
    create_docx(document_xml, DOCX_PATH)
    print(f"DOCX created: {DOCX_PATH}")


if __name__ == "__main__":
    main()
