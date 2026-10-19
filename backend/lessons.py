"""Teaching metadata grounded in ResearchMethodComp(2).pdf slides."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Lesson:
    title:str
    slides:str
    summary:str
    key_points:tuple[str,...]
    limitation:str
    python:str

REPRESENTATION=[
 Lesson('Why Data Representation Matters','13–16','Architecture is translated into observations and variables so that buildings, spaces, and human experience can be compared and analyzed.',('An observation is a building, room, person, or measurement.','Variables describe attributes such as floor area, material, temperature, or cost.'),'A table only represents the attributes you actually measured.','df.shape  # rows, columns'),
 Lesson('Tabular Data (Spreadsheet Thinking)','17–20','Rows are observations; columns are variables. A well-structured table has one measurable attribute per column.',('Buildings or rooms can be rows.','Area, energy and orientation can be columns.'),'Identifiers label observations but are usually not continuous measurements.','df.head(); df.dtypes'),
 Lesson('Categorical Data','21–24','Categorical data labels meaningful types such as orientation, material or room type.',('Categories can be counted and compared.','One-hot encoding creates indicator columns for regression.'),'Integer-coding categories can introduce false numerical ordering.','pd.get_dummies(df[["building_type"]], dtype=int)'),
 Lesson('Numerical Data','25–27','Numerical data expresses measurable or countable quantities.',('Continuous: temperature, floor area.','Discrete: occupancy count, storey count.'),'A numeric-looking code may be an identifier, not a numerical measurement.','df.select_dtypes(include="number").describe()'),
 Lesson('Organizing Tabular Data Properly','28–29','Consistent units, clearly named columns, and missing-value handling are essential to valid analysis.',('Keep one meaning and unit per variable.','Inspect missing records and duplicated rows.','Approve transformations and keep the original data.'),'Automatic type guesses and imputation can silently distort meaning.','df.isna().sum(); df.duplicated().sum()'),
 Lesson('Why Focus on Tabular Data?','45–46','Tabular data is accessible in Excel and directly compatible with statistics, visualization and regression.',('Representation enables calculation.','Analysis asks what is typical, variable and associated.'),'Analysis cannot recover data that were not originally collected.','df.describe(include="all")'),
]
UNDERSTANDING=[
 Lesson('Why Statistics Matter','48–51','Statistics summarize otherwise overwhelming individual observations.',('Descriptive statistics compress information.','Summary values should be paired with distribution plots.'),'Two datasets can share a mean but have very different distributions.','df.describe()'),
 Lesson('Mean (Average Value)','52','The mean represents the arithmetic average of valid numerical observations.',('Mean = sum of observations / number of observations.','Compare the mean and median for skewed data.'),'The mean is sensitive to extreme observations.','df["x"].mean()'),
 Lesson('Standard Deviation (Variability)','53','Standard deviation describes how widely observations vary around their mean.',('A small SD means values are relatively close to the mean.','A large SD indicates more spread; sample SD uses n−1.'),'Compare SD only for compatible variables and units.','df["x"].std(ddof=1)'),
 Lesson('What Is Correlation?','54–57','Correlation measures the direction and strength of numerical association.',('Positive, negative or approximately zero association.','Compare Pearson and Spearman, inspect sample size and scatterplots.'),'Correlation does not establish causation; outliers and nonlinearity matter.','df[["x","y"]].corr(method="pearson")'),
 Lesson('Why Visualization Matters','58–61','Visualizations reveal patterns, trends, clusters and unusual observations.',('Charts complement numerical statistics.','Label axes, denominators and units accurately.'),'A chart can mislead when scales or aggregations are inappropriate.','import plotly.express as px'),
 Lesson('Scatter Plot (Relationships)','62–65','A scatter plot compares two numerical variables; each point represents an observation.',('Upward or downward trends can suggest association.','Use a fitted line cautiously.'),'Patterns do not imply one variable caused another.','px.scatter(df,x="x",y="y",trendline="ols")'),
 Lesson('Bar Chart (Categorical Comparison)','66','Bar charts compare categories using counts or clearly identified aggregated measurements.',('Frequency is distinct from mean or sum.','Percentages need a clear denominator.'),'Averaging an encoded category is usually meaningless.','df["category"].value_counts().plot.bar()'),
 Lesson('Choosing the Right Chart','67','Match visualization to the type of data and research question.',('One numerical variable → histogram.','Two numerical variables → scatter.','Category frequencies → bar chart.'),'Good choices depend on meaning as well as data type.','px.histogram(df,x="x")'),
 Lesson('Running Statistics and Visualizations','68–70','The lecture used Google Colab; here the same computations are run interactively in Streamlit.',('pandas calculates descriptive statistics.','Plotly constructs interactive figures.'),'A graphical interface should still expose the mathematical method and reproducible code.','df.describe(); px.histogram(df,x="x")'),
 Lesson('Linear Interpolation','71','Interpolate missing numerical values between known measurements at ordered positions.',('Estimate internal gaps using neighboring known values.','Useful for sequential sensor or performance measurements.'),'Do not extrapolate, and do not interpolate unordered survey categories.','series.interpolate(method="index",limit_area="inside")'),
 Lesson('From Data to Real Research Data','72','Architectural data are often messy, mixed-type and incomplete.',('Inspect before transforming.','Preserve originals and document processing decisions.'),'Cleaning decisions must reflect the scientific meaning of each variable.','df.isna().sum()'),
 Lesson('Survey Data','73','Survey responses often represent categories, preferences and human behavior.',('Count valid and missing responses.','Report percentages and denominators.'),'Likert categories are ordinal; treat mean-based interpretations with care.','df["response"].value_counts(dropna=False,normalize=True)'),
]
REGRESSION=[
 Lesson('What Is Prediction?','75','Prediction estimates a numerical outcome using one or more input variables.',('Inputs are X; a numerical outcome is y.','Select the research target before fitting a model.'),'Predictive accuracy does not demonstrate causal mechanisms.','X=df[["floor_area"]]; y=df["energy"]'),
 Lesson('Regression Definition','76','Linear regression fits a numerical relationship between explanatory variables and a target.',('Simple linear regression uses one explanatory variable.','Inspect the fitted line, residuals and prediction error.'),'The fitted line summarizes observations and may extrapolate poorly.','from sklearn.linear_model import LinearRegression'),
 Lesson('Learning Relationships','77','Separate model fitting from evaluation on observations not used for fitting.',('Training fits preprocessing and model parameters.','Cross-validation supports model selection.','Final test data remain untouched until final evaluation.'),'High test performance does not guarantee generalization under different operating conditions.','from sklearn.model_selection import train_test_split'),
 Lesson('Architectural Applications','78','Regression can model energy consumption, cost or environmental performance using measured building attributes.',('Example: floor area → construction cost.','Example: outdoor temperature → electricity demand.'),'Ensure dataset coverage, variable meaning and units match the intended use.','model.predict(new_building_features)'),
]
