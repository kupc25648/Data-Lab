"""Synthetic teaching examples (not measured building data)."""
from __future__ import annotations
import numpy as np
import pandas as pd


def energy_demo(seed:int=42,n:int=180)->pd.DataFrame:
    rng=np.random.default_rng(seed)
    area=np.round(rng.uniform(40,220,n),1)
    temp=np.round(rng.normal(30,3,n),1)
    typ=rng.choice(['Residential','Office','School'],n,p=[.5,.3,.2])
    occupancy=rng.integers(1,18,n)
    electricity=(1.8*area+10*temp+14*occupancy+np.select([typ=='Office',typ=='School'],[120,80],default=0)+rng.normal(0,65,n)).round(1)
    df=pd.DataFrame({'building_id':[f'B-{i:03}' for i in range(1,n+1)],'floor_area_m2':area,
        'outdoor_temp_c':temp,'building_type':typ,'occupancy_count':occupancy,
        'monthly_electricity_kwh':electricity})
    return df


def cost_demo(seed:int=17,n:int=145)->pd.DataFrame:
    rng=np.random.default_rng(seed)
    area=rng.uniform(75,880,n).round(1)
    stories=rng.integers(1,9,n)
    material=rng.choice(['Concrete','Timber','Steel'],n)
    total=(18500*area+200000*stories+np.where(material=='Steel',1_800_000,0)+rng.normal(0,450000,n)).round()
    df=pd.DataFrame({'project_id':[f'PRJ-{j:03}' for j in range(n)],'area_m2':area,'storeys':stories,
                     'primary_material':material,'construction_cost_thb':total})
    for i in [3,7,14,28]:df.loc[i,'construction_cost_thb']=np.nan
    df.loc[7,'primary_material']=None
    return df


def survey_demo(seed:int=8,n:int=130)->pd.DataFrame:
    rng=np.random.default_rng(seed)
    building=rng.choice(['Tower A','Tower B','Tower C'],n)
    comfort=rng.choice(['Very dissatisfied','Dissatisfied','Neutral','Satisfied','Very satisfied'],n,p=[.07,.11,.23,.4,.19]).astype(object)
    comfort[::19]=None
    temp=np.round(rng.normal(26,1.8,n),1)
    return pd.DataFrame({'response_id':[f'R{i:03}' for i in range(n)],'building':building,
        'comfort_rating':comfort,'indoor_temperature_c':temp,'hours_in_space':rng.integers(1,13,n)})


def sensor_demo(seed:int=5,n:int=90)->pd.DataFrame:
    rng=np.random.default_rng(seed)
    t=pd.date_range('2026-01-01',periods=n,freq='h')
    values=25+2*np.sin(np.arange(n)*2*np.pi/24)+rng.normal(0,.2,n)
    df=pd.DataFrame({'timestamp':t,'indoor_temperature_c':values.round(2),'occupancy_count':rng.integers(0,12,n)})
    df.loc[[8,9,10,24,44,76],'indoor_temperature_c']=np.nan
    return df

DEMOS={'Energy performance (synthetic)':energy_demo,'Construction cost (synthetic)':cost_demo,
       'Comfort survey (synthetic)':survey_demo,'Hourly sensors with gaps (synthetic)':sensor_demo}
