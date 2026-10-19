"""Offline best-effort API simulation when Streamlit cannot be installed.
For developer QA only; not a replacement for running a browser Streamlit test.
"""
import sys
from pathlib import Path
from types import ModuleType

class State(dict):
    def __getattr__(self,k):
        if k in self:return self[k]
        raise AttributeError(k)
    def __setattr__(self,k,v):self[k]=v

class Fake(ModuleType):
    def __init__(self):
        super().__init__('streamlit')
        self.session_state=State()
        self.sidebar=self
        self.topic_index={'r_topic':0,'u_topic':0,'g_topic':0}
        self.calls=[]
    def __enter__(self):return self
    def __exit__(self,*args):return None
    def set_page_config(self,**kwargs):pass
    def markdown(self,*a,**kw):pass
    def caption(self,*a,**kw):pass
    def subheader(self,*a,**kw):pass
    def header(self,*a,**kw):pass
    def info(self,*a,**kw):pass
    def success(self,*a,**kw):pass
    def error(self,*a,**kw):raise Exception('UI ERROR: '+str(a))
    def warning(self,*a,**kw):pass
    def write(self,*a,**kw):pass
    def metric(self,*a,**kw):pass
    def dataframe(self,*a,**kw):pass
    def plotly_chart(self,*a,**kw):pass
    def code(self,*a,**kw):pass
    def divider(self,*a,**kw):pass
    def json(self,*a,**kw):pass
    def tabs(self,labels,*args,**kwargs):return [self for _ in labels]
    def columns(self,n,*args,**kwargs):return [self for _ in range(n if isinstance(n,int) else len(n))]
    def expander(self,*a,**kw):return self
    def selectbox(self,label,options,index=0,key=None,**kw):
        if key in self.topic_index:index=self.topic_index[key]
        return list(options)[index]
    def slider(self,label,*args,**kw):
        return kw.get('value',args[2] if len(args)>=3 else args[0] if len(args)>=1 else 0)
    def radio(self,label,options,*a,**kw):return list(options)[kw.get('index',0)]
    def multiselect(self,label,options,*a,**kw):return kw.get('default',[])
    def checkbox(self,label,*a,**kw):return kw.get('value',False)
    def toggle(self,label,*a,**kw):return kw.get('value',False)
    def number_input(self,label,*a,**kw):return kw.get('value',0)
    def button(self,*a,**kw):return False
    def download_button(self,*a,**kw):return False
    def file_uploader(self,*a,**kw):return None

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
fake=Fake();sys.modules['streamlit']=fake
import app
from backend.demo_data import energy_demo,survey_demo,sensor_demo
app.init();app.load(energy_demo(),'synthetic energy','energy')
for area,limit in [('r_topic',6),('u_topic',12),('g_topic',4)]:
    for i in range(limit):
        fake.topic_index[area]=i
        try:app.main()
        except Exception as e:
            print('FAIL',area,i,repr(e));raise
        print('PASS',area,i)
print('Simulated all 22 lesson routes OK')
