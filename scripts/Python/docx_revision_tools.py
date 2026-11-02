# -*- coding: utf-8 -*-
"""
docx_revision_tools.py  (New for Review, 2026)  Author of the revision tooling: RNV
Low-level helpers to revise a Word manuscript while preserving its package:
  * replace the text of an existing paragraph (new text in red #FF0000, paragraph
    properties kept; the first character becomes its own run so a comment can be
    anchored on it);
  * insert new paragraphs (red) after an existing one, copying its properties;
  * delete paragraphs;
  * add native Word comments (author RNV, initials RNV) anchored on exactly the
    first character of a paragraph;
  * set document metadata (Author / Last Modified By) to RNV;
  * produce a 'Clean' copy (red turned to automatic colour, comments removed).
Equations (m:oMath), drawings, tables and fields are never touched unless the
paragraph that contains them is explicitly replaced.
"""
import copy
import datetime
import re
import shutil
import zipfile
from lxml import etree

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W}
RED = 'FF0000'
CT_COMMENTS = ('<Override PartName="/word/comments.xml" ContentType="application/vnd.openxmlformats-'
               'officedocument.wordprocessingml.comments+xml"/>')
REL_COMMENTS = ('<Relationship Id="rIdCmts" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
                'relationships/comments" Target="comments.xml"/>')


def q(tag):
    return '{%s}%s' % (W, tag)


class Docx:
    def __init__(self, path):
        self.path = path
        self.z = zipfile.ZipFile(path)
        self.parts = {n: self.z.read(n) for n in self.z.namelist()}
        self.doc = etree.fromstring(self.parts['word/document.xml'])
        self.body = self.doc.find(q('body'))
        self.comments = []  # (id, text)
        self.next_cid = 0
        self.log = []

    # ---------- navigation ----------
    def paragraphs(self):
        return list(self.body.iter(q('p')))

    @staticmethod
    def ptext(p):
        return ''.join(t.text or '' for t in p.iter(q('t')))

    def find(self, prefix, nth=0):
        """Paragraph whose text starts with prefix (whitespace-normalised)."""
        norm = lambda s: re.sub(r'\s+', ' ', s).strip()
        hits = [p for p in self.paragraphs() if norm(self.ptext(p)).startswith(norm(prefix))]
        if len(hits) <= nth:
            raise KeyError('paragraph not found: %r' % prefix[:60])
        return hits[nth]

    # ---------- run construction ----------
    @staticmethod
    def _base_rpr(p):
        """Run properties template: first text run's rPr, else paragraph mark rPr."""
        for r in p.iter(q('r')):
            if r.find(q('t')) is not None:
                rpr = r.find(q('rPr'))
                return copy.deepcopy(rpr) if rpr is not None else None
        ppr = p.find(q('pPr'))
        if ppr is not None and ppr.find(q('rPr')) is not None:
            return copy.deepcopy(ppr.find(q('rPr')))
        return None

    @staticmethod
    def _make_run(text, rpr_template, red=True, italic=None, bold=None):
        r = etree.Element(q('r'))
        rpr = copy.deepcopy(rpr_template) if rpr_template is not None else etree.Element(q('rPr'))
        for tag in ('color', 'highlight'):
            for e in rpr.findall(q(tag)):
                rpr.remove(e)
        if red:
            c = etree.SubElement(rpr, q('color'))
            c.set(q('val'), RED)
        if italic is not None:
            for e in rpr.findall(q('i')) + rpr.findall(q('iCs')):
                rpr.remove(e)
            if italic:
                etree.SubElement(rpr, q('i'))
        if bold is not None:
            for e in rpr.findall(q('b')) + rpr.findall(q('bCs')):
                rpr.remove(e)
            if bold:
                etree.SubElement(rpr, q('b'))
        # keep schema order roughly: rFonts, b, i, color, sz ... (Word is tolerant)
        r.append(rpr)
        t = etree.SubElement(r, q('t'))
        t.text = text
        t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        return r

    def _fill(self, p, text, rpr, red=True, segments=None):
        """Put text in p as runs: first char alone (comment anchor), then the rest.
        segments: optional list of (text, {'italic':bool,'bold':bool}) for mixed formatting."""
        for child in list(p):
            if child.tag != q('pPr'):
                p.remove(child)
        if segments is None:
            segments = [(text, {})]
        first = True
        for seg, fmt in segments:
            if not seg:
                continue
            if first:
                p.append(self._make_run(seg[0], rpr, red, fmt.get('italic'), fmt.get('bold')))
                if len(seg) > 1:
                    p.append(self._make_run(seg[1:], rpr, red, fmt.get('italic'), fmt.get('bold')))
                first = False
            else:
                p.append(self._make_run(seg, rpr, red, fmt.get('italic'), fmt.get('bold')))

    # ---------- editing primitives ----------
    def replace(self, prefix, new_text, nth=0, segments=None, note=None, drop_math=False):
        p = self.find(prefix, nth)
        old = self.ptext(p)
        has_math = p.find('.//{http://schemas.openxmlformats.org/officeDocument/2006/math}oMath') is not None
        if p.find(q('drawing')) is not None or (has_math and not drop_math):
            raise ValueError('refusing to replace a paragraph with drawing/equation: %r' % prefix[:50])
        self._fill(p, new_text, self._base_rpr(p), True, segments)
        self.log.append(('replace', old, new_text, note))
        return p

    def insert_after(self, anchor, new_text, style_from=None, segments=None, note=None):
        """anchor: lxml paragraph or prefix string. Returns the new paragraph."""
        ap = anchor if not isinstance(anchor, str) else self.find(anchor)
        src = style_from if style_from is not None else ap
        if isinstance(src, str):
            src = self.find(src)
        np_ = etree.Element(q('p'))
        ppr = src.find(q('pPr'))
        if ppr is not None:
            np_.append(copy.deepcopy(ppr))
        self._fill(np_, new_text, self._base_rpr(src), True, segments)
        ap.addnext(np_)
        self.log.append(('insert', None, new_text, note))
        return np_

    def delete(self, prefix, nth=0, note=None):
        p = self.find(prefix, nth)
        old = self.ptext(p)
        p.getparent().remove(p)
        self.log.append(('delete', old, None, note))

    def recolor_paragraph(self, p):
        """Force all text runs of an existing paragraph to red (used when a paragraph is moved)."""
        for r in p.iter(q('r')):
            rpr = r.find(q('rPr'))
            if rpr is None:
                rpr = etree.SubElement(r, q('rPr'))
                r.insert(0, rpr)
            for e in rpr.findall(q('color')):
                rpr.remove(e)
            c = etree.SubElement(rpr, q('color'))
            c.set(q('val'), RED)

    # ---------- comments ----------
    def comment(self, p, text):
        """Anchor a comment on exactly the first character of paragraph p.
        The first run is split if it has more than one character."""
        runs = [r for r in p.iter(q('r')) if r.find(q('t')) is not None and (r.find(q('t')).text or '')]
        if not runs:
            raise ValueError('no text run to anchor comment')
        r0 = runs[0]
        t0 = r0.find(q('t'))
        if len(t0.text) > 1:
            rest = copy.deepcopy(r0)
            rest.find(q('t')).text = t0.text[1:]
            rest.find(q('t')).set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
            t0.text = t0.text[0]
            t0.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
            r0.addnext(rest)
        cid = str(self.next_cid)
        self.next_cid += 1
        start = etree.Element(q('commentRangeStart'))
        start.set(q('id'), cid)
        end = etree.Element(q('commentRangeEnd'))
        end.set(q('id'), cid)
        r0.addprevious(start)
        r0.addnext(end)
        ref = etree.Element(q('r'))
        rr = etree.SubElement(ref, q('rPr'))
        rs = etree.SubElement(rr, q('rStyle'))
        rs.set(q('val'), 'CommentReference')
        cr = etree.SubElement(ref, q('commentReference'))
        cr.set(q('id'), cid)
        end.addnext(ref)
        self.comments.append((cid, text))
        return cid

    def _comments_xml(self):
        root = etree.Element(q('comments'), nsmap={'w': W})
        now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        for cid, text in self.comments:
            c = etree.SubElement(root, q('comment'))
            c.set(q('id'), cid)
            c.set(q('author'), 'RNV')
            c.set(q('date'), now)
            c.set(q('initials'), 'RNV')
            p = etree.SubElement(c, q('p'))
            r = etree.SubElement(p, q('r'))
            t = etree.SubElement(r, q('t'))
            t.text = text
        return etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)

    # ---------- metadata ----------
    def set_metadata(self, author='RNV'):
        core = self.parts['docProps/core.xml'].decode('utf8')
        core = re.sub(r'<dc:creator>.*?</dc:creator>', '<dc:creator>%s</dc:creator>' % author, core, flags=re.S)
        core = re.sub(r'<cp:lastModifiedBy>.*?</cp:lastModifiedBy>', '<cp:lastModifiedBy>%s</cp:lastModifiedBy>' % author, core, flags=re.S)
        if '<dc:creator>' not in core:
            core = core.replace('</cp:coreProperties>', '<dc:creator>%s</dc:creator></cp:coreProperties>' % author)
        if '<cp:lastModifiedBy>' not in core:
            core = core.replace('</cp:coreProperties>', '<cp:lastModifiedBy>%s</cp:lastModifiedBy></cp:coreProperties>' % author)
        self.parts['docProps/core.xml'] = core.encode('utf8')
        app = self.parts.get('docProps/app.xml')
        if app:
            app = re.sub(r'<Company>.*?</Company>', '<Company></Company>', app.decode('utf8'), flags=re.S)
            app = re.sub(r'<Manager>.*?</Manager>', '<Manager></Manager>', app, flags=re.S)
            self.parts['docProps/app.xml'] = app.encode('utf8')

    # ---------- save ----------
    def save(self, out_path, clean=False):
        doc = copy.deepcopy(self.doc)
        parts = dict(self.parts)
        if clean:
            for tag in ('commentRangeStart', 'commentRangeEnd', 'commentReference'):
                for e in list(doc.iter(q(tag))):
                    par = e.getparent()
                    if tag == 'commentReference':
                        par.getparent().remove(par)
                    else:
                        par.remove(e)
            for c in list(doc.iter(q('color'))):
                if c.get(q('val'), '').upper() == RED:
                    c.getparent().remove(c)
        parts['word/document.xml'] = etree.tostring(doc, xml_declaration=True, encoding='UTF-8', standalone=True)
        if self.comments and not clean:
            parts['word/comments.xml'] = self._comments_xml()
            ct = parts['[Content_Types].xml'].decode('utf8')
            if 'comments+xml' not in ct:
                ct = ct.replace('</Types>', CT_COMMENTS + '</Types>')
            parts['[Content_Types].xml'] = ct.encode('utf8')
            rels = parts['word/_rels/document.xml.rels'].decode('utf8')
            if 'relationships/comments"' not in rels:
                rels = rels.replace('</Relationships>', REL_COMMENTS + '</Relationships>')
            parts['word/_rels/document.xml.rels'] = rels.encode('utf8')
        with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as zo:
            for n in self.z.namelist():
                zo.writestr(n, parts[n])
            for n in parts:
                if n not in self.z.namelist():
                    zo.writestr(n, parts[n])
