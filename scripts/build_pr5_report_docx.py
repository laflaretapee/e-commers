#!/usr/bin/env python3
"""Build a GOST-formatted DOCX report for Practical work #5 from PDF content."""

from __future__ import annotations

import csv
import datetime as dt
import html
import json
import re
import subprocess
import zipfile
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "out"
PDF_PATH = Path("/home/dinar/Downloads/Практическое занятие №5 (1).pdf")
DOCX_PATH = OUT_DIR / "Отчет_ПЗ5_ГОСТ.docx"

CSV_FILES = {
    "ai_events": OUT_DIR / "ai_events.csv",
    "rec_requests": OUT_DIR / "rec_requests.csv",
    "rec_results": OUT_DIR / "rec_results.csv",
    "rec_feedback": OUT_DIR / "rec_feedback.csv",
    "moderation_requests": OUT_DIR / "moderation_requests.csv",
    "moderation_decisions": OUT_DIR / "moderation_decisions.csv",
    "user_features": OUT_DIR / "user_features.csv",
    "item_features": OUT_DIR / "item_features.csv",
    "training_jobs": OUT_DIR / "training_jobs.csv",
    "model_registry": OUT_DIR / "model_registry.csv",
}

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def run_pdftotext(pdf_path: Path) -> str:
    cmd = ["pdftotext", "-layout", str(pdf_path), "-"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout


def clean_spaces(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_topic(pdf_text: str) -> str:
    m = re.search(r"Тема:\s*(.+)", pdf_text)
    if not m:
        return "Заполнение базы данных тестовыми данными"
    return clean_spaces(m.group(1))


def csv_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8", newline="") as fh:
        # minus header
        return max(sum(1 for _ in fh) - 1, 0)


def load_counter(path: Path, key: str) -> dict[str, int]:
    data: dict[str, int] = {}
    if not path.exists():
        return data
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            value = (row.get(key) or "").strip()
            if not value:
                continue
            data[value] = data.get(value, 0) + 1
    return data


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

    br = ""
    if page_break_before:
        br = "<w:r><w:br w:type=\"page\"/></w:r>"

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


def build_table(rows: list[tuple[str, str]]) -> str:
    tbl_rows: list[str] = []

    header = (
        "<w:tr>"
        "<w:tc><w:tcPr><w:tcW w:w=\"7000\" w:type=\"dxa\"/></w:tcPr>"
        + table_cell_paragraph("Таблица", align="center", bold=True)
        + "</w:tc>"
        "<w:tc><w:tcPr><w:tcW w:w=\"2500\" w:type=\"dxa\"/></w:tcPr>"
        + table_cell_paragraph("Количество строк", align="center", bold=True)
        + "</w:tc>"
        "</w:tr>"
    )
    tbl_rows.append(header)

    for name, value in rows:
        tbl_rows.append(
            "<w:tr>"
            "<w:tc><w:tcPr><w:tcW w:w=\"7000\" w:type=\"dxa\"/></w:tcPr>"
            + table_cell_paragraph(name)
            + "</w:tc>"
            "<w:tc><w:tcPr><w:tcW w:w=\"2500\" w:type=\"dxa\"/></w:tcPr>"
            + table_cell_paragraph(value, align="center")
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
        "<w:tblGrid><w:gridCol w:w=\"7000\"/><w:gridCol w:w=\"2500\"/></w:tblGrid>"
        + "".join(tbl_rows)
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
        '<dc:title>Отчет по практическому занятию №5</dc:title>'
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


def compose_report_content(topic: str, counts: dict[str, int], actions: dict[str, int], decisions: dict[str, int], events: dict[str, int]) -> list[str]:
    today = dt.datetime.now().strftime("%d.%m.%Y")

    total_shown = counts.get("rec_results", 0)
    click_ratio = (actions.get("click", 0) / total_shown * 100.0) if total_shown else 0.0
    dislike_ratio = (actions.get("dislike", 0) / total_shown * 100.0) if total_shown else 0.0

    mod_total = counts.get("moderation_decisions", 0)
    publish_ratio = (decisions.get("publish", 0) / mod_total * 100.0) if mod_total else 0.0
    manual_ratio = (decisions.get("manual_review", 0) / mod_total * 100.0) if mod_total else 0.0
    reject_ratio = (decisions.get("reject", 0) / mod_total * 100.0) if mod_total else 0.0

    table_rows = [
        ("ai_events", str(counts.get("ai_events", 0))),
        ("rec_requests", str(counts.get("rec_requests", 0))),
        ("rec_results", str(counts.get("rec_results", 0))),
        ("rec_feedback", str(counts.get("rec_feedback", 0))),
        ("moderation_requests", str(counts.get("moderation_requests", 0))),
        ("moderation_decisions", str(counts.get("moderation_decisions", 0))),
        ("user_features", str(counts.get("user_features", 0))),
        ("item_features", str(counts.get("item_features", 0))),
        ("training_jobs", str(counts.get("training_jobs", 0))),
        ("model_registry", str(counts.get("model_registry", 0))),
    ]

    p: list[str] = []

    # Title page
    p.append(paragraph("ФГБОУ ВО «Уфимский университет науки и технологий»", align="center", first_line=0))
    p.append(paragraph("Кафедра технической кибернетики", align="center", first_line=0))
    p.append(paragraph("", align="center", first_line=0))
    p.append(paragraph("ОТЧЁТ ПО ПРАКТИЧЕСКОМУ ЗАНЯТИЮ №5", align="center", first_line=0, bold=True))
    p.append(paragraph("по дисциплине «Интеллектуальные информационные системы»", align="center", first_line=0))
    p.append(paragraph(f"Тема: {topic}", align="center", first_line=0, bold=True))
    p.append(paragraph("", align="center", first_line=0))
    p.append(paragraph("Выполнил: ст. гр. ИВТ-432Б", align="right", first_line=0))
    p.append(paragraph("Зиязетдинов Д.С.", align="right", first_line=0))
    p.append(paragraph("Проверил: доцент кафедры", align="right", first_line=0))
    p.append(paragraph("", align="center", first_line=0))
    p.append(paragraph(f"Уфа {dt.datetime.now().year} г.", align="center", first_line=0))

    # page break to main text
    p.append(paragraph("", page_break_before=True, first_line=0))

    # 1 Введение
    p.append(paragraph("1 Введение", bold=True, first_line=0, align="left"))
    p.append(
        paragraph(
            "Практическое занятие №5 посвящено заполнению спроектированной базы данных тестовыми данными для проверки базовых функций системы. "
            "Согласно заданию необходимо выбрать подход GAN, подготовить промпт, сформировать набор данных, оформить результаты и подготовить материалы к загрузке в СДО."
        )
    )
    p.append(
        paragraph(
            "В работе использован подход генерации табличных данных с контролем реалистичности распределений и проверкой ссылочной целостности, "
            "что позволяет моделировать поведение пользователей и товаров в условиях, близких к рабочим."
        )
    )

    # 2 Цель работы
    p.append(paragraph("2 Цель работы", bold=True, first_line=0, align="left"))
    p.append(
        paragraph(
            "Сформировать тестовый датасет для БД маркетплейса на основе генеративного подхода и привести результат к форме, пригодной для автоматизированной загрузки и валидации."
        )
    )

    # 3 Ход работы
    p.append(paragraph("3 Ход работы", bold=True, first_line=0, align="left"))
    p.append(paragraph("1) Выбрана стратегия генерации табличных данных в стиле GAN для имитации пользовательских и системных событий."))
    p.append(paragraph("2) Подготовлен промпт и параметры генерации: объёмы таблиц, диапазон дат за последние 90 дней, бизнес-ограничения и внешние ключи."))
    p.append(paragraph("3) Сформированы CSV-файлы с заголовками в кодировке UTF-8 и подготовлен SQL-скрипт загрузки через COPY."))
    p.append(paragraph("4) Выполнена встроенная валидация: контроль объёмов, уникальности PK, ссылочной целостности и распределений по событиям/модерации."))

    p.append(paragraph("Схема процесса: выбор GAN -> настройка промпта -> генерация CSV -> валидация -> загрузка в PostgreSQL.", align="center", first_line=0))
    p.append(paragraph("Рисунок 1 – Схема процесса генерации тестовых данных", first_line=0, align="left"))

    # 4 Результаты
    p.append(paragraph("4 Результаты", bold=True, first_line=0, align="left"))
    p.append(paragraph("Сформирован набор данных по ключевым таблицам интеллектуальной компоненты. Итоговый объём приведён в таблице."))
    p.append(paragraph("Таблица 1 – Объём сгенерированных данных", first_line=0, align="left"))
    p.append(build_table(table_rows))

    p.append(
        paragraph(
            f"По таблице rec_feedback доля кликов от показов составила {click_ratio:.2f} %, доля dislike — {dislike_ratio:.2f} %. "
            "Это соответствует требуемому диапазону качества отклика пользователей."
        )
    )
    p.append(
        paragraph(
            f"Распределение модерационных решений: publish — {publish_ratio:.2f} %, manual_review — {manual_ratio:.2f} %, reject — {reject_ratio:.2f} %. "
            "Таким образом, данные отражают реалистичную долю публикаций и спорных кейсов."
        )
    )
    p.append(
        paragraph(
            f"События в ai_events имеют правдоподобную частоту: CatalogViewed = {events.get('CatalogViewed', 0)}, "
            f"RecommendationShown = {events.get('RecommendationShown', 0)}, OrderPaid = {events.get('OrderPaid', 0)}; "
            "просмотры и показы встречаются чаще, чем оплаты заказов."
        )
    )

    # 5 Вывод
    p.append(paragraph("5 Вывод", bold=True, first_line=0, align="left"))
    p.append(
        paragraph(
            "В рамках практического занятия №5 подготовлен полный набор тестовых данных для проектируемой БД, "
            "включая события, рекомендации, фидбек, модерацию и MLOps-контур. Полученные CSV-файлы и SQL-скрипт загрузки "
            "обеспечивают воспроизводимое наполнение базы и позволяют проводить функциональное тестирование создаваемых сервисов."
        )
    )
    p.append(paragraph(f"Дата формирования отчёта: {today}."))

    return p


def create_docx(document_xml: str, output_path: Path) -> None:
    content_types = build_content_types_xml()
    package_rels = build_package_rels_xml()
    document_rels = build_document_rels_xml()
    styles_xml = build_styles_xml()
    settings_xml = build_settings_xml()
    footer_xml = build_footer_xml()
    core_xml = build_core_xml()
    app_xml = build_app_xml()

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", package_rels)
        zf.writestr("word/document.xml", document_xml)
        zf.writestr("word/styles.xml", styles_xml)
        zf.writestr("word/settings.xml", settings_xml)
        zf.writestr("word/footer1.xml", footer_xml)
        zf.writestr("word/_rels/document.xml.rels", document_rels)
        zf.writestr("docProps/core.xml", core_xml)
        zf.writestr("docProps/app.xml", app_xml)


def main() -> None:
    if not PDF_PATH.exists():
        raise FileNotFoundError(f"PDF not found: {PDF_PATH}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pdf_text = run_pdftotext(PDF_PATH)
    topic = extract_topic(pdf_text)

    counts = {name: csv_count(path) for name, path in CSV_FILES.items()}
    feedback_actions = load_counter(CSV_FILES["rec_feedback"], "action")
    moderation_decisions = load_counter(CSV_FILES["moderation_decisions"], "decision")
    event_counts = load_counter(CSV_FILES["ai_events"], "event_type")

    content_parts = compose_report_content(topic, counts, feedback_actions, moderation_decisions, event_counts)
    document_xml = build_document_xml(content_parts)
    create_docx(document_xml, DOCX_PATH)

    print(f"DOCX created: {DOCX_PATH}")


if __name__ == "__main__":
    main()
