# importar librerias
import streamlit as st
import pandas as pd
import sys
from SPARQLWrapper import SPARQLWrapper, JSON, RDF, XML
import re
from pandas import json_normalize
from pymongo import MongoClient
from py2neo import Graph
import rdflib
from pyvis.network import Network
import tempfile	
import networkx as nx
import matplotlib.pyplot as plt

# titulo y logo streamlit
st.set_page_config(page_title="Streamlit", page_icon=":guardsman:")


# Conectarse a la base de datos MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["itinerario"]

# Seleccionar una colección
coleccion = db["dataScience_TIC"]

# endpoint
sparql = SPARQLWrapper("http://localhost:7200/repositories/dsResources")

# consulta al grafo de conocimiento
def consultaGraphDB(query_term):
	query = f"""
		PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
		PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
		PREFIX dct: <http://purl.org/dc/terms/>
		PREFIX owl: <http://www.w3.org/2002/07/owl#>

		SELECT ?broader ?subject ?sameAs
			WHERE {{
				?concept rdfs:label ?label .
				OPTIONAL {{ ?concept skos:broader ?broader }}
  				OPTIONAL {{ ?concept dct:subject ?subject }}
  				OPTIONAL {{ ?concept owl:sameAs ?sameAs }}
				FILTER (LCASE(str(?label)) = LCASE("{query_term}")) .
			}}
	"""
	sparql.setQuery(query)
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()
	return results


# encabezado de nuestra aplicacion

st.title("Data Science TIC")
st.header("Exploración y Búsqueda de recursos para aprender Ciencia de Datos")


# Solicitamos al usuario que ingrese una consulta
consulta = st.text_input("Ingresa el tema a Consultar")

# Obtén las categorías únicas de la colección
categories = coleccion.distinct("type")

# utiliazmos el widget de selección de Streamlit para crear un elemento de selección HTML
selected_category = st.selectbox('Elige una categoría', categories)

valores_seleccionados = st.multiselect('Selecciona opciones', categories)

if valores_seleccionados:
    valores_seleccionados_str = ', '.join(valores_seleccionados)
    st.write(f'Has seleccionado: {valores_seleccionados_str}')


# seleccionamos la cantidad de votos que tiene el contenido
votos = st.number_input("Votos de popularidad:", min_value=0, max_value=1000, step=1)

if 'datasets' in valores_seleccionados and len(valores_seleccionados) == 1:
    st.write('Has seleccionado solo la opción datasets')
if 'kernels' in valores_seleccionados and len(valores_seleccionados) == 1:
    st.write('Has seleccionado solo la opción kernels')
if 'youtube video' in valores_seleccionados and len(valores_seleccionados) == 1:
    st.write('Has seleccionado solo la opción youtube video')
elif 'datasets' in valores_seleccionados and 'kernels' in valores_seleccionados and len(valores_seleccionados) == 2:
    st.write('Has seleccionado las opciones datasets y kernels')
elif 'datasets' in valores_seleccionados and 'youtube video' in valores_seleccionados and len(valores_seleccionados) == 2:
    st.write('Has seleccionado las opciones datasets y youtube video')
elif 'kernels' in valores_seleccionados and 'youtube video' in valores_seleccionados and len(valores_seleccionados) == 2:
    st.write('Has seleccionado las opciones kernels y youtube video')
elif 'datasets' in valores_seleccionados and 'kernels' in valores_seleccionados and 'youtube video' in valores_seleccionados and len(valores_seleccionados) == 3:
    st.write('Has seleccionado las opciones 1, 2 y 3')





if selected_category == "youtube video":
	# consulta a contenido multimedia
	c2 = coleccion.find({"$and": [{"videoTitle": {"$regex": consulta}}, {"type": selected_category}]})
else:
	# consulta a datasets y kernels
	c1 = coleccion.find({"$and": [{"topic": {"$regex": "^" + consulta + "$", "$options": "i"}}, 
                         {"type": selected_category}, 
                         {"voteCount": {"$gt": votos}}]})

# mostrar temas relacionados a la consulta del autor
st.write("Temas relacionados", level=2)

# ejecutar funcion de consulta GraphDB
results = consultaGraphDB(consulta)

# mostrar resultados
for result in results["results"]["bindings"]:
    if "broader" in result:
        broader = result["broader"]["value"]
        broader_name = broader.split("/")[-1].replace("_", " ")
        st.write("skos:broader:", f'[{broader_name}]({broader})')
    if "subject" in result:
        subject = result["subject"]["value"]
        subject_name = subject.split(":")[-1].replace("_", " ")
        st.write("dct:subject:", f'[{subject_name}]({subject})')
    if "sameAs" in result:
        sameAs = result["sameAs"]["value"]
        sameAs_name = sameAs.split("/")[-1].replace("_", " ")
        st.write("owl:sameAs:", f'[{sameAs_name}]({sameAs})')

# Convierte los resultados de la consulta a MongoDB, convertir en un DataFrame de Pandas
df = pd.DataFrame(list(c1))

df = df.rename(columns={"topic": "Tópico", 
                        "type": "Tipo",
                        "urlKaggle": "URL Kaggle",
                        "autor": "Autor",
                        "title": "Titulo", 
                        "voteCount": "Votos"})

# converir a int los votos
if "Votos" in df.columns:
    df["Votos"] = df["Votos"].apply(lambda x: round(x))

# convertir en enlace el link de Kaggle
if "URL Kaggle" in df.columns:
    df["URL Kaggle"] = df["URL Kaggle"].apply(lambda x: f"<a href='{x}'>Kaggle</a>")

# Selecciona las columnas que deseas mostrar
selected_columns = ["Tipo", "Titulo", "Autor", "URL Kaggle", "Votos"]

# Verifica que las columnas existan en el DataFrame
columns_exist = all([col in df.columns for col in selected_columns])

if columns_exist:
    # Presenta la tabla en Streamlit con solo las columnas seleccionadas
    st.write(df[selected_columns])


G = nx.DiGraph()

for result in results["results"]["bindings"]:
    broader = result.get("broader", {}).get("value")
    subject = result.get("subject", {}).get("value")
    sameAs = result.get("sameAs", {}).get("value")

    if broader:
        G.add_edge(broader, subject)
    if sameAs:
        G.add_edge(sameAs, subject)

st.write("Exploración de los tópicos relacionados", level=2)

fig, ax = plt.subplots(figsize=(12, 8))
nx.draw(G, with_labels=True, ax=ax)

st.pyplot(fig)



