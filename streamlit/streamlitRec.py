import streamlit as st
import sys
from SPARQLWrapper import SPARQLWrapper, JSON, RDF, XML
import pandas as pd
from pandas import json_normalize

endPoint = "http://172.17.26.6:7200/repositories/CoursesRecVal"
sparql = SPARQLWrapper(endPoint)

#To get the degree curriculum:
def getMalla():
    query = """
PREFIX schema: <http://schema.org/>
PREFIX onto: <http://www.utpl.edu.ec/academiconto/>
select * where { 
    ?s a schema:Course; schema:name ?name;
    schema:educationalLevel/schema:name ?level; schema:numberOfCredits ?credits;
    schema:educationalAlignment/schema:name ?category.
    FILTER(LANG(?name)="en")
} ORDER BY ?level ?category
    """
    sparql.setQuery(query%())
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    malla = json_normalize(results["results"]["bindings"])
    malla = malla[['s.value', 'name.value', 'level.value', 'credits.value', 'category.value']]
    malla.columns = ['URI', 'Course', 'Level', 'Credits', 'Category']
    return malla

def write_level(l):
    rows = ''
    for i in range(len(l)):
        rows = rows + '<td>' +l.iloc[i].Course + '</td>'
    return rows
    

malla = getMalla()
#html = '<table><tr>' + write_level(malla[malla.Level == '1']) + '</tr>'
#html = html + '<tr>' + write_level(malla[malla.Level == '2']) + '</tr>'
#html = html + '<tr>' + write_level(malla[malla.Level == '3']) + '</tr>'
#html = html + '<tr>' + write_level(malla[malla.Level == '4']) + '</tr>'
#html = html + '<tr>' + write_level(malla[malla.Level == '5']) + '</tr>'
#html = html + '<tr>' + write_level(malla[malla.Level == '6']) + '</tr>'
html = '<table><tr>' + write_level(malla[malla.Level == '4']) + '</tr>'
html = html + '<tr>' + write_level(malla[malla.Level == '5']) + '</tr>'
html = html + '<tr>' + write_level(malla[malla.Level == '6']) + '</tr></table>'
st.markdown(html, unsafe_allow_html=True)

# To query data:
def getRec(student):
    query = """
PREFIX schema: <http://schema.org/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX onto: <http://www.utpl.edu.ec/academiconto/>
prefix : <http://www.utpl.edu.ec/academicdata/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
select ?r ?s ?course ?code ?c ?credits ?el ?sl ?weight 
where { 
    VALUES ?s {%s}
    ?r onto:student ?s; onto:course ?c.
    ?s onto:level ?sl.
    ?c schema:name ?course; schema:courseCode ?code; schema:numberOfCredits ?credits ; schema:educationalLevel/schema:name ?el.
    BIND(xsd:integer(?sl) / xsd:integer(?el) AS ?weight)
    FILTER(LANG(?course)="en")
}ORDER BY DESC(?weight)
    """
    sparql.setQuery(query%(student))
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return results

results = getRec(':S1900856038') # student 1900856038

resultsRec1 = json_normalize(results["results"]["bindings"])
resultsRec1 = resultsRec1[['r.value', 's.value', 'course.value', 'code.value', 'c.value', 'credits.value', 'el.value', 'sl.value', 'weight.value']]


import numpy as np
resultsRec1['weight.value'] = resultsRec1['weight.value'].astype(float)

resultsRec1['weight.value'] = np.round(resultsRec1['weight.value'], decimals = 2)

maxValue = resultsRec1['weight.value'].max()

resultsReco = resultsRec1[['course.value', 'code.value', 'credits.value', 'el.value', 'weight.value']]


resultsReco["relevance"] = np.where(resultsReco['weight.value'] == maxValue, 'HIGH',
                                np.where((resultsReco['weight.value'] < maxValue) & (resultsReco['weight.value'] >= 1), 'MEDIUM', 'LOW'))


st.write("""# Course Recommender
	According to your grade report, you could take the next courses:""")



def highlight_survived(s):
    return ['background-color: #339999']*len(s) if s.relevance == 'HIGH' else ['background-color: #FFCC33']*len(s)

def color_survived(val):
    if val=='HIGH':
    	color = '#339999'
    else:
    	if val=='MEDIUM':
    		color = '#FFCC33'
    	else: color = '#FF9966'
    return f'background-color: {color}'

def color_cell(val):
    if val=='HIGH':
    	color = '#339999'
    else:
    	if val=='MEDIUM':
    		color = '#FFCC33'
    	else: color = '#FF9966'
    return f'<font color="{color}">'

#A function that returns the html code as it should
def show_url(code):
    return '<a href="http://www.utpl.edu.ec/academicdata/' + code + '">' + code + ' </a>'


@st.cache
def convert_df(input_df):
     # IMPORTANT: Cache the conversion to prevent computation on every rerun
     return input_df.to_html(escape=False, formatters=dict(code=show_url))



resultsF = resultsReco[['code.value', 'course.value', 'credits.value', 'el.value', 'relevance']]
resultsF.columns = ['Code', 'Course', 'Credits', 'Level', 'Relevance']

resultsF.Code = resultsF.Code.apply(lambda x:show_url(x))
#resultsF['Relevance2'] = resultsF.Relevance
resultsF.Relevance = resultsF.Relevance.apply(lambda x:color_cell(x)+x)

#html = convert_df(resultsF)

#st.dataframe(resultsReco.style.apply(highlight_survived, axis=1))
#st.dataframe(resultsF.style.applymap(color_survived, subset=['Relevance']))

#st.write(resultsF.to_html(escape=False, index=False), unsafe_allow_html=True)

#resultsF.columns = ['Code', 'Course', 'Credits', 'Level', 'Relevance', 'Relevance2', 'Relevance3']
st.markdown(resultsF.to_html(escape=False, index=False), unsafe_allow_html=True)

st.write("""## Explanation""")
tH = '- <font color="#339999"><b>Hight</b> </font> relevant courses have the highest score because they are at the lower level of your studies or they are pre-requisites for others.'
#tM = '- <font color="#FFCC33"><b>Medium</b> </font> relevant courses have the intermediate score because they are at the same level as other courses that you approved or they are pre-requisites for others.'
tL = '- <font color="#FF9966"><b>Low</b> </font> relevant courses have the lowest score because they are located at the top level of your curriculum, if you have the time you could enroll in them.'
st.markdown(tH, unsafe_allow_html=True)
#st.markdown(tM, unsafe_allow_html=True)
st.markdown(tL, unsafe_allow_html=True)


