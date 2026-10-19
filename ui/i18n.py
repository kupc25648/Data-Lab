"""Local UI translations; scientific column names and underlying computation stay unchanged.

External reading links are voluntary and never fetched by this application.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
import streamlit as st

HERE = Path(__file__).parent
UI_TH = json.loads((HERE / 'ui_th.json').read_text(encoding='utf-8'))
LESSON_TH = json.loads((HERE / 'lesson_th.json').read_text(encoding='utf-8'))


def language() -> str:
    return st.session_state.get('ui_language', 'en')


def t(text: str) -> str:
    if not isinstance(text, str) or language() != 'th':
        return text
    if text in UI_TH:
        return UI_TH[text]
    if text in LESSON_TH:
        return LESSON_TH[text]['title']
    # Messages with runtime values are translated after interpolation.
    patterns = [
        (r'^(.*?) observations · (\d+) variables$', lambda m: f'{m.group(1)} หน่วยสังเกต · {m.group(2)} ตัวแปร'),
        (r'^Observation (\d+): (.*)\. Selected variable: (.*)\.$', lambda m: f'หน่วยสังเกต {m.group(1)}: {m.group(2)} · ตัวแปรที่เลือก: {m.group(3)}'),
        (r'^User interpretation: (.*)\. The Python dtype alone cannot establish this scientific meaning\.$', lambda m: f'การตีความโดยผู้ใช้: {t(m.group(1))} · ชนิดข้อมูลใน Python เพียงอย่างเดียวไม่สามารถยืนยันความหมายทางวิชาการได้'),
        (r'^Lower SD = (.*); adjusted SD = (.*) \(same mean ≈ (.*)\)\.$',lambda m:f'SD ของกลุ่มกระจายน้อย = {m.group(1)}; SD ที่ปรับแล้ว = {m.group(2)} (ค่าเฉลี่ยใกล้เคียง {m.group(3)})'),
        (r'^Screened (\d+) pairs\. Unadjusted p-values are not confirmatory evidence after searching many relationships\.$',lambda m:f'ตรวจสอบ {m.group(1)} คู่ค่า p ที่ยังไม่ปรับไม่ใช่หลักฐานยืนยันเมื่อค้นหาความสัมพันธ์หลายคู่'),
        (r'^(.+) r=(.*), paired N=(\d+)\. Descriptive association, not causation\.$',lambda m:f'{m.group(1)} r={m.group(2)}, จำนวนคู่ข้อมูล={m.group(3)} · เป็นความสัมพันธ์เชิงพรรณนา ไม่ใช่เหตุและผล'),
        (r'^Denominator: all (\d+) observations, including missing categories\.$',lambda m:f'ตัวหารคือหน่วยสังเกตทั้งหมด {m.group(1)} รายการ รวมหมวดหมู่ที่ข้อมูลหาย'),
        (r'^Selected using training folds: (.*) · Final holdout: (\d+) observations$',lambda m:f'เลือกแบบจำลองจากการตรวจสอบไขว้ของข้อมูลฝึก: {m.group(1)} · ข้อมูลทดสอบสุดท้าย: {m.group(2)} รายการ'),
        (r'^Fitted equation: (.*)$',lambda m:f'สมการที่ปรับได้: {m.group(1)}'),
        (r'^Split=(.*); seed=(.*); train n=(.*); test n=(.*)\. Residual = observed − predicted\.$', lambda m: f'วิธีแบ่ง={t(m.group(1))}; seed={m.group(2)}; ฝึก n={m.group(3)}; ทดสอบ n={m.group(4)} · ค่าคลาดเคลื่อน = ค่าจริง − ค่าพยากรณ์'),
        (r'^Upload failed: (.*)$',lambda m:f'อัปโหลดไม่สำเร็จ: {m.group(1)}'),
        (r'^Cannot run regression: (.*)$',lambda m:f'ไม่สามารถรันการถดถอยได้: {m.group(1)}'),
        (r'^LECTURE SLIDES (.*)  ·  TABULAR DATA SCIENCE$',lambda m:f'สไลด์บทเรียน {m.group(1)} · วิทยาการข้อมูลตาราง'),
    ]
    for pat,fn in patterns:
        match = re.match(pat,text,re.DOTALL)
        if match:
            return fn(match)
    return text


def localize_tabs(labels: list[str]) -> list[str]:
    return [t(label) for label in labels]


def localized_lesson(lesson):
    thai = LESSON_TH.get(lesson.title) if language() == 'th' else None
    if thai:
        return thai['title'], thai['summary'], thai['points'], thai['limitation']
    return lesson.title, lesson.summary, lesson.key_points, lesson.limitation

# Term ID: English name, Thai name, English definition, Thai definition, verified reading links.
TERMS = {
    'observation': ('Observation', 'หน่วยสังเกต', 'A row describing one unit or measurement.', 'หนึ่งแถวแทนหน่วยที่ศึกษา หรือการวัดหนึ่งครั้ง', 'https://en.wikipedia.org/wiki/Statistical_unit'),
    'variable': ('Variable', 'ตัวแปร', 'A recorded attribute that can vary between observations.', 'คุณลักษณะที่วัดได้และมีค่าต่างกันระหว่างหน่วยสังเกต', 'https://en.wikipedia.org/wiki/Variable_(statistics)'),
    'tabular': ('Tabular data', 'ข้อมูลตาราง', 'Data organized in rows and columns.', 'ข้อมูลที่จัดรูปเป็นแถวและคอลัมน์', 'https://en.wikipedia.org/wiki/Table_(information)'),
    'categorical': ('Categorical variable', 'ตัวแปรหมวดหมู่', 'A variable whose values represent groups or labels.', 'ตัวแปรที่ใช้แบ่งประเภทหรือกำหนดป้ายชื่อ', 'https://en.wikipedia.org/wiki/Categorical_variable'),
    'one_hot': ('One-hot encoding', 'การเข้ารหัส One-hot', 'Convert each nominal category into an indicator column.', 'แปลงแต่ละหมวดหมู่เป็นคอลัมน์ค่าศูนย์หรือหนึ่ง', 'https://www.geeksforgeeks.org/machine-learning/ml-one-hot-encoding/'),
    'continuous': ('Continuous and discrete variables', 'ตัวแปรต่อเนื่องและไม่ต่อเนื่อง', 'Continuous values can vary on a scale; discrete values are distinct counts.', 'ตัวแปรต่อเนื่องวัดค่าบนช่วงได้ ส่วนไม่ต่อเนื่องมักเป็นค่าที่นับได้', 'https://en.wikipedia.org/wiki/Continuous_or_discrete_variable'),
    'cleaning': ('Data cleaning', 'การทำความสะอาดข้อมูล', 'Detect and address inaccurate, incomplete or inconsistent values.', 'ตรวจหาและจัดการข้อมูลผิดพลาด ขาดหาย หรือไม่สอดคล้อง', 'https://en.wikipedia.org/wiki/Data_cleansing'),
    'mean': ('Arithmetic mean', 'ค่าเฉลี่ยเลขคณิต', 'Sum of values divided by their count.', 'ผลรวมค่าหารด้วยจำนวนข้อมูล', 'https://en.wikipedia.org/wiki/Arithmetic_mean'),
    'median': ('Median', 'มัธยฐาน', 'Middle value after sorting observations.', 'ค่ากึ่งกลางเมื่อเรียงข้อมูลจากน้อยไปมาก', 'https://en.wikipedia.org/wiki/Median'),
    'sd': ('Standard deviation', 'ส่วนเบี่ยงเบนมาตรฐาน', 'A measure of spread around the mean.', 'ตัวชี้วัดระดับการกระจายของข้อมูลรอบค่าเฉลี่ย', 'https://en.wikipedia.org/wiki/Standard_deviation'),
    'outlier': ('Outlier', 'ค่าผิดปกติ', 'An observation unusually far from other values.', 'ค่าที่อยู่ห่างจากข้อมูลส่วนใหญ่มากผิดปกติ', 'https://en.wikipedia.org/wiki/Outlier'),
    'correlation': ('Correlation', 'สหสัมพันธ์', 'A statistical association; it does not imply causation.', 'ความสัมพันธ์ทางสถิติซึ่งไม่จำเป็นต้องเป็นเหตุและผล', 'https://en.wikipedia.org/wiki/Correlation'),
    'spearman': ('Spearman correlation', 'สหสัมพันธ์สเปียร์แมน', 'Rank-based measure of monotonic association.', 'ตัววัดความสัมพันธ์จากอันดับของข้อมูล', 'https://www.geeksforgeeks.org/data-science/spearmans-rank-correlation/'),
    'scatter': ('Scatter plot', 'แผนภาพการกระจาย', 'Points representing paired numeric observations.', 'จุดที่แสดงคู่ข้อมูลเชิงตัวเลข', 'https://en.wikipedia.org/wiki/Scatter_plot'),
    'histogram': ('Histogram', 'ฮิสโตแกรม', 'A chart of numerical value frequencies in bins.', 'แผนภูมิแจกแจงความถี่ของข้อมูลตัวเลขตามช่วงค่า', 'https://en.wikipedia.org/wiki/Histogram'),
    'bar': ('Bar chart', 'แผนภูมิแท่ง', 'A chart comparing category counts or summaries.', 'แผนภูมิเปรียบเทียบค่าหรือจำนวนในแต่ละหมวดหมู่', 'https://en.wikipedia.org/wiki/Bar_chart'),
    'interpolation': ('Linear interpolation', 'การประมาณค่าเชิงเส้น', 'Estimate an intermediate value using known neighboring points.', 'ประมาณค่าระหว่างจุดข้อมูลข้างเคียงที่ทราบค่า', 'https://en.wikipedia.org/wiki/Linear_interpolation'),
    'survey': ('Likert scale', 'มาตราส่วนลิเคิร์ต', 'An ordered scale frequently used for survey responses.', 'มาตราส่วนเรียงลำดับที่ใช้ในแบบสอบถาม', 'https://en.wikipedia.org/wiki/Likert_scale'),
    'regression': ('Linear regression', 'การถดถอยเชิงเส้น', 'Fit a linear relationship to predict numerical outcomes.', 'ปรับสมการเชิงเส้นเพื่อทำนายผลลัพธ์เชิงตัวเลข', 'https://www.geeksforgeeks.org/machine-learning/ml-linear-regression/'),
    'residual': ('Residual', 'ค่าคลาดเคลื่อน', 'Observed outcome minus predicted outcome.', 'ค่าจริงลบค่าที่แบบจำลองพยากรณ์', 'https://en.wikipedia.org/wiki/Errors_and_residuals'),
    'cv': ('Cross-validation', 'การตรวจสอบไขว้', 'Repeated training/validation splits to estimate generalization.', 'แบ่งข้อมูลฝึกและตรวจสอบหลายรอบเพื่อประเมินแบบจำลอง', 'https://en.wikipedia.org/wiki/Cross-validation_(statistics)'),
    'data_leakage': ('Data leakage', 'การรั่วไหลของข้อมูล', 'Information from the evaluation data inadvertently enters model training.', 'ข้อมูลจากส่วนทดสอบเล็ดลอดเข้าสู่ขั้นตอนฝึกแบบจำลอง', 'https://en.wikipedia.org/wiki/Leakage_(machine_learning)'),
}
READING = {
    'Why Data Representation Matters': ['observation','variable'],
    'Tabular Data (Spreadsheet Thinking)': ['tabular','observation','variable'],
    'Categorical Data': ['categorical','one_hot'],
    'Numerical Data': ['continuous'],
    'Organizing Tabular Data Properly': ['cleaning'],
    'Why Focus on Tabular Data?':['tabular'],
    'Why Statistics Matter':['mean','sd'],
    'Mean (Average Value)':['mean','median','outlier'],
    'Standard Deviation (Variability)':['sd','mean'],
    'What Is Correlation?':['correlation','spearman'],
    'Why Visualization Matters':['outlier','histogram'],
    'Scatter Plot (Relationships)':['scatter','correlation'],
    'Bar Chart (Categorical Comparison)':['bar'],
    'Choosing the Right Chart':['histogram','scatter','bar'],
    'Running Statistics and Visualizations':['histogram'],
    'Linear Interpolation':['interpolation'],
    'From Data to Real Research Data':['cleaning'],
    'Survey Data':['survey','categorical'],
    'What Is Prediction?':['regression'],
    'Regression Definition':['regression','residual'],
    'Learning Relationships':['cv','data_leakage'],
    'Architectural Applications':['regression','residual'],
}

def localize_plot(fig):
    """Translate fixed educational plot text, keeping user-supplied variable names intact."""
    if language() != 'th' or fig is None:
        return fig
    try:
        if fig.layout.title and fig.layout.title.text:
            fig.update_layout(title=t(fig.layout.title.text))
        for axis in ('xaxis','yaxis'):
            item=getattr(fig.layout,axis,None)
            if item and item.title and item.title.text:
                fig.update_layout(**{axis:{'title':{'text':t(item.title.text)}}})
        for trace in fig.data:
            if isinstance(trace.name,str):
                trace.name=t(trace.name)
    except (AttributeError,TypeError,ValueError):
        pass
    return fig

def render_reading(lesson_title: str):
    refs = READING.get(lesson_title, [])
    if not refs:
        return
    heading = 'คำศัพท์และอ่านเพิ่มเติม (Wikipedia / GeeksforGeeks)' if language()=='th' else 'Key terms & further reading (Wikipedia / GeeksforGeeks)'
    with st.expander(heading):
        for code in refs:
            en,th,en_ex,th_ex,url=TERMS[code]
            name,desc=(th,th_ex) if language()=='th' else (en,en_ex)
            src='GeeksforGeeks' if 'geeksforgeeks.org' in url else 'Wikipedia'
            st.markdown(f'**{name} ({en})** — {desc} · [{src}]({url})' if language()=='th' else f'**{name}** — {desc} · [{src}]({url})')
        st.caption('ลิงก์เปิดเว็บไซต์ภายนอกเมื่อผู้ใช้คลิกเท่านั้น' if language()=='th' else 'External pages open only when you click their links.')
