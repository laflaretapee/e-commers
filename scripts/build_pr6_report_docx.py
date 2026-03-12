#!/usr/bin/env python3
"""Build a GOST-formatted DOCX report for Practical work #6."""

from __future__ import annotations

import datetime as dt
import html
import re
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "out"
DOCX_PATH = OUT_DIR / "Отчет_ПЗ6_ГОСТ.docx"

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
    b = "<w:b/><w:bCs/>" if bold else ""
    return (
        "<w:rPr>"
        "<w:rFonts w:ascii=\"Times New Roman\" w:hAnsi=\"Times New Roman\" w:cs=\"Times New Roman\"/>"
        "<w:color w:val=\"000000\"/>"
        "<w:sz w:val=\"28\"/><w:szCs w:val=\"28\"/>"
        f"{b}"
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


def table_cell_paragraph(text: str, align: str = "left", bold: bool = False) -> str:
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


def build_table(rows: list[tuple[str, str]], col1: str, col2: str) -> str:
    body_rows: list[str] = []
    header = (
        "<w:tr>"
        "<w:tc><w:tcPr><w:tcW w:w=\"6400\" w:type=\"dxa\"/></w:tcPr>"
        + table_cell_paragraph(col1, align="center", bold=True)
        + "</w:tc>"
        "<w:tc><w:tcPr><w:tcW w:w=\"3100\" w:type=\"dxa\"/></w:tcPr>"
        + table_cell_paragraph(col2, align="center", bold=True)
        + "</w:tc>"
        "</w:tr>"
    )
    body_rows.append(header)

    for left, right in rows:
        body_rows.append(
            "<w:tr>"
            "<w:tc><w:tcPr><w:tcW w:w=\"6400\" w:type=\"dxa\"/></w:tcPr>"
            + table_cell_paragraph(left)
            + "</w:tc>"
            "<w:tc><w:tcPr><w:tcW w:w=\"3100\" w:type=\"dxa\"/></w:tcPr>"
            + table_cell_paragraph(right, align="left")
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
        "<w:tblGrid><w:gridCol w:w=\"6400\"/><w:gridCol w:w=\"3100\"/></w:tblGrid>"
        + "".join(body_rows)
        + "</w:tbl>"
    )


def build_document_xml(content_parts: list[str]) -> str:
    body = "".join(content_parts)
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
        '<dc:title>Отчет по практическому занятию №6</dc:title>'
        '<dc:creator>Студент</dc:creator>'
        '<cp:lastModifiedBy>Codex</cp:lastModifiedBy>'
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


def screenshot_placeholder(title: str) -> list[str]:
    return [
        paragraph("[МЕСТО ДЛЯ СКРИНШОТА]", align="center", first_line=0, bold=True),
        paragraph(title, align="left", first_line=0),
        paragraph("", first_line=0),
    ]


def compose_report_content() -> list[str]:
    year = dt.datetime.now().year
    today = dt.datetime.now().strftime("%d.%m.%Y")

    services_rows = [
        ("Auth Service", "Регистрация и вход пользователей, порт 8001"),
        ("Catalog Service", "Каталог товаров и интеграция с AI, порт 8002"),
        ("Cart Service", "Корзина пользователя и выдача рекомендаций, порт 8003"),
        ("Order Service", "Оформление заказов и отправка событий, порт 8004"),
        ("Notification Service", "Обработка событий заказов (Kafka), порт 8005"),
        ("AI Service", "Модерация, рекомендации, обучение, порт 8006"),
    ]

    p: list[str] = []

    # Title page
    p.append(paragraph("ФГБОУ ВО «Уфимский университет науки и технологий»", align="center", first_line=0))
    p.append(paragraph("Кафедра технической кибернетики", align="center", first_line=0))
    p.append(paragraph("", align="center", first_line=0))
    p.append(paragraph("ОТЧЁТ ПО ПРАКТИЧЕСКОМУ ЗАНЯТИЮ №6", align="center", first_line=0, bold=True))
    p.append(paragraph("по дисциплине «Интеллектуальные информационные системы»", align="center", first_line=0))
    p.append(paragraph("Тема: Реализация интеллектуализированной системы e-commerce", align="center", first_line=0, bold=True))
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
            "В практическом занятии №6 выполнена реализация учебной e-commerce системы с интеллектуальными функциями. "
            "Система построена как набор микросервисов с отдельным AI-сервисом для модерации контента, генерации рекомендаций и запуска обучения рекомендательной модели."
        )
    )
    p.append(
        paragraph(
            "Дополнительно реализован пользовательский интерфейс, интегрированный с backend API, что позволяет демонстрировать полный пользовательский сценарий: "
            "регистрация, просмотр каталога, добавление в корзину, оформление заказа и сбор событий для интеллектуальной обработки."
        )
    )

    # 2
    p.append(paragraph("2 Цель работы", bold=True, first_line=0, align="left"))
    p.append(
        paragraph(
            "Реализовать работоспособную архитектуру системы с AI-компонентами, обеспечить хранение и обработку событий, "
            "интегрировать рекомендации и модерацию в бизнес-процессы, а также подготовить интерфейс и материалы для демонстрации."
        )
    )

    # 3
    p.append(paragraph("3 Реализация системы", bold=True, first_line=0, align="left"))
    p.append(
        paragraph(
            "Реализация выполнена на FastAPI и PostgreSQL с использованием Redis и Kafka в сервисном контуре. "
            "Каждый микросервис отвечает за свою предметную область и взаимодействует через HTTP API."
        )
    )
    p.append(paragraph("Таблица 1 – Состав реализованных микросервисов", first_line=0, align="left"))
    p.append(build_table(services_rows, "Сервис", "Назначение"))
    p.append(paragraph("", first_line=0))
    p.append(
        paragraph(
            "AI-сервис принимает события от каталогов, корзины и заказов, обновляет feature store и формирует персонализированную выдачу. "
            "Для рекомендаций реализован контур обучения: данные показов и обратной связи используются для расчёта параметров модели, "
            "после чего новая версия регистрируется в model_registry и может быть активирована."
        )
    )
    p.extend(screenshot_placeholder("Рисунок 1 – Общая архитектура системы (docker compose / схема сервисов)"))
    p.extend(screenshot_placeholder("Рисунок 2 – Swagger Catalog Service: методы /products и ответы"))
    p.extend(screenshot_placeholder("Рисунок 3 – Swagger AI Service: endpoints /recommendations и /recommendations/feedback"))
    p.extend(screenshot_placeholder("Рисунок 4 – Swagger AI Service: endpoint /training/recommendation/run"))

    # 4
    p.append(paragraph("4 Результаты", bold=True, first_line=0, align="left"))
    p.append(
        paragraph(
            "Система успешно запускается в контейнерном окружении, backend API возвращают корректные ответы, а каталог заполнен тестовыми товарами. "
            "Фронтенд отображает витрину, корзину и заказы, а AI-компонент обеспечивает модерацию и рекомендации."
        )
    )
    p.append(
        paragraph(
            "Проведена проверка сценария от пользовательского действия до AI-событий: показ рекомендаций, запись feedback, "
            "создание обучающего задания и получение новой версии рекомендательной модели."
        )
    )
    p.extend(screenshot_placeholder("Рисунок 5 – Интерфейс фронтенда: страница каталога с карточками товаров"))
    p.extend(screenshot_placeholder("Рисунок 6 – Интерфейс фронтенда: корзина и блок AI-рекомендаций"))
    p.extend(screenshot_placeholder("Рисунок 7 – Swagger AI Service: активная модель /models/active"))
    p.extend(screenshot_placeholder("Рисунок 8 – Результат выполнения /training/recommendation/run (job completed)"))

    # 5
    p.append(paragraph("5 Вывод", bold=True, first_line=0, align="left"))
    p.append(
        paragraph(
            "В рамках ПЗ6 реализована полноценная интеллектуализированная система e-commerce: "
            "микросервисный backend, AI-модуль рекомендаций и модерации, контур обучения модели и пользовательский фронтенд. "
            "Подготовленные точки для скриншотов позволяют оформить итоговую демонстрацию в соответствии с требованиями ГОСТ."
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
    content = compose_report_content()
    document_xml = build_document_xml(content)
    create_docx(document_xml, DOCX_PATH)
    print(f"DOCX created: {DOCX_PATH}")


if __name__ == "__main__":
    main()
