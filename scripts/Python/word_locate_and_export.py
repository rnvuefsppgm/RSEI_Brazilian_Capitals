# -*- coding: utf-8 -*-
"""
word_locate_and_export.py  (RNV, 2026)
Opens the revised manuscript in Microsoft Word (COM automation), repaginates,
exports a review PDF, and records for every RNV comment the page and line number
of its anchor (Word's own pagination with continuous line numbering enabled),
together with the first words of the anchored paragraph. Also reports the word
count of the main text. Output: <docx>.locations.json
Usage: python word_locate_and_export.py <revised.docx> <out.pdf> <locations.json> [clean.docx clean.pdf]
"""
import sys
import os
import json
import win32com.client as win32

src, pdf, out_json = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])
word = win32.gencache.EnsureDispatch('Word.Application')
word.Visible = False
word.DisplayAlerts = 0
try:
    doc = word.Documents.Open(src, ReadOnly=False)
    doc.Repaginate()
    locs = []
    for c in doc.Comments:
        rng = c.Scope
        page = rng.Information(3)   # wdActiveEndAdjustedPageNumber
        line = rng.Information(10)  # wdFirstCharacterLineNumber
        para = rng.Paragraphs(1).Range.Text.strip()
        locs.append({'comment': c.Range.Text.strip(), 'author': c.Author, 'page': page, 'line': line,
                     'anchor_char': rng.Text, 'paragraph_start': para[:90]})
    # main text word count (title to 'Declarations')
    full = doc.Content.Text
    i = full.find('\rDeclarations')
    main_words = len((full[:i] if i > 0 else full).split())
    stats = {'pages': doc.ComputeStatistics(2), 'words_total': doc.ComputeStatistics(0), 'lines': doc.ComputeStatistics(1),
             'words_main_text': main_words, 'comments': doc.Comments.Count}
    doc.ExportAsFixedFormat(pdf, 17)  # wdExportFormatPDF
    doc.Save()
    doc.Close()
    if len(sys.argv) > 5:
        cdoc = word.Documents.Open(os.path.abspath(sys.argv[4]))
        cdoc.Repaginate()
        cdoc.ExportAsFixedFormat(os.path.abspath(sys.argv[5]), 17)
        stats['clean_pages'] = cdoc.ComputeStatistics(2)
        cdoc.Close()
    json.dump({'stats': stats, 'locations': locs}, open(out_json, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps(stats))
finally:
    word.Quit()
