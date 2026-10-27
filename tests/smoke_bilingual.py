"""Offline route checks in English and Thai; run from project folder with Python."""
from __future__ import annotations
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import smoke_simulated_ui as base
from ui.i18n import LESSON_TH, READING, TERMS, t, localized_lesson
from backend.lessons import REPRESENTATION, UNDERSTANDING, REGRESSION
from backend.demo_data import cost_demo
from backend.reporting import make_docx
from io import BytesIO
from docx import Document

fake=base.fake
assert len(LESSON_TH)==22
assert len(READING)==22
assert all('https://' in TERMS[code][-1] for links in READING.values() for code in links)
for locale in ('en','th'):
    fake.session_state.ui_language=locale
    captured=[];links=[]
    previous_sub=fake.subheader;previous_mark=fake.markdown
    fake.subheader=lambda s,*args,**kwargs: captured.append(s)
    fake.markdown=lambda s,*args,**kwargs: links.append(s)
    try:
        for key,lessonset in [('r_topic',REPRESENTATION),('u_topic',UNDERSTANDING),('g_topic',REGRESSION)]:
            for i,lesson in enumerate(lessonset):
                fake.topic_index[key]=i
                base.app.main()
                expected=localized_lesson(lesson)[0]
                assert expected in captured,(locale, key, i, expected)
    finally:
        fake.subheader=previous_sub;fake.markdown=previous_mark
    assert any('wikipedia.org' in entry for entry in links)
    assert any('geeksforgeeks.org' in entry for entry in links)
    print('PASS language',locale,'22 lesson routes, contextual term links')

sample=cost_demo()
blob=make_docx(sample,'synthetic_demo',sample.shape,[],lang='th')
doc=Document(BytesIO(blob))
words='\n'.join(p.text for p in doc.paragraphs)
assert 'Interactive Data Lab' in words and 'การแทนข้อมูล' in words
print('PASS Thai DOCX')
