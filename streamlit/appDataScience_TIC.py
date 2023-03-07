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
import re

# titulo y logo streamlit
st.set_page_config(page_title="Streamlit", page_icon=":guardsman:")


# Conectarse a la base de datos MongoDB 1
client = MongoClient("mongodb://localhost:27017/")
db = client["itinerario"]

# Seleccionar una colección 1
coleccion = db["dataScience_TIC"]

# Seleccionar una colección 2 
coleccion2 = db["dataScienceYouTube_TIC"]

# Seleccionar una colección 3
coleccion3 = db["dataScienceDBpedia_TIC"]


# endpoint
sparql = SPARQLWrapper("http://localhost:7200/repositories/dsResources")


net = Network(height="500px", width="100%", directed=False)


# encabezado de nuestra aplicacion
st.image('images/datascience-image.png')
st.title("Data Science TIC")
st.header("Exploración y Búsqueda de recursos para aprender Ciencia de Datos")


# Solicitamos al usuario que ingrese una consulta
consulta = st.text_input("Ingresa el tema a Consultar")

# Obtén las categorías únicas de la colección
# categories = coleccion.distinct("type")
categories = ['datasets', 'kernels', 'youtube video']


# utiliazmos el widget de selección de Streamlit para crear un elemento de selección HTML
valores_seleccionados = st.multiselect('Tipos de Recursos Educativos', categories)

if valores_seleccionados:
    valores_seleccionados_str = ', '.join(valores_seleccionados)
    st.write(f'Has seleccionado: {valores_seleccionados_str}')

# seleccionamos la cantidad de votos que tiene el contenido
votos = st.number_input("Votos de popularidad:", min_value=0, max_value=1000, step=1)

# cuando seleccionamos datasets
if 'datasets' in valores_seleccionados and len(valores_seleccionados) == 1:

	# consultar metadatos dbpedia
	dbpedia = coleccion3.find({"topic": {"$regex": "^" + consulta + "$", "$options": "i"}})

	# transformar a dataframe la consulta
	df_dbpedia = pd.DataFrame(list(dbpedia))

	# obtener el titulo del topico
	st.header(df_dbpedia['topic'].iloc[0])

	# imprimir imagen con condicional en caso de no existir imagen
	if not df_dbpedia['images'].isnull().all():
		image_url = df_dbpedia['images'].iloc[0]
		st.image(image_url)
	else:
		st.write("No se encontró ninguna imagen.")

	# imprimir descripcion
	descriptions = df_dbpedia['descriptions'].tolist()
	text = "\n".join(descriptions)
	st.write(text)


	# consulta a GraphDB
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

    # llamar a la funcion
	results = consultaGraphDB(consulta)

	st.write("**Temas Relacionados:**")

	# imprimir consulta a graphDB
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


	# esto es para el grafo de conocimiento
	for result in results["results"]["bindings"]:
	    if "broader" in result and "subject" in result:
	        broader = result["broader"]["value"]
	        broader_name = broader.split("/")[-1].replace("_", " ")
	        subject = result["subject"]["value"]
	        subject_name = subject.split(":")[-1].replace("_", " ")
	        #net.add_node(consulta)
	        net.add_node(broader_name, title=broader, url=broader)
	        net.add_node(subject_name, title=subject, url=subject)
	        #net.add_edge(consulta, broader_name)
	        net.add_edge(broader_name, subject_name)
	    if "broader" in result and "sameAs" in result:
	        broader = result["broader"]["value"]
	        broader_name = broader.split("/")[-1].replace("_", " ")
	        sameAs = result["sameAs"]["value"]
	        sameAs_name = sameAs.split("/")[-1].replace("_", " ")
	        #net.add_node(consulta)
	        net.add_node(broader_name, title=broader, url=broader)
	        net.add_node(sameAs_name, title=sameAs, url=sameAs)
	        #net.add_edge(consulta, broader_name)
	        net.add_edge(broader_name, sameAs_name)
	    if "subject" in result and "sameAs" in result:
	        subject = result["subject"]["value"]
	        subject_name = subject.split(":")[-1].replace("_", " ")
	        sameAs = result["sameAs"]["value"]
	        sameAs_name = sameAs.split("/")[-1].replace("_", " ")
	        #net.add_node(consulta)
	        net.add_node(subject_name, title=subject, url=subject)
	        net.add_node(sameAs_name, title=sameAs, url=sameAs)
	        #net.add_edge(consulta, subject_name)
	        net.add_edge(subject_name, sameAs_name)
	    if "broader" in result and "subject" in result and "sameAs" in result:
	        broader = result["broader"]["value"]
	        broader_name = broader.split("/")[-1].replace("_", " ")
	        subject = result["subject"]["value"]
	        subject_name = subject.split(":")[-1].replace("_", " ")
	        sameAs = result["sameAs"]["value"]
	        sameAs_name = sameAs.split("/")[-1].replace("_", " ")
	        #net.add_node(consulta)
	        net.add_node(broader_name, title=broader, url=broader)
	        net.add_node(subject_name, title=subject, url=subject)
	        net.add_node(sameAs_name, title=sameAs, url=sameAs)
	        #net.add_edge(consulta, broader_name)
	        net.add_edge(broader_name, subject_name)
	        net.add_edge(subject_name, sameAs_name)

	st.write("**Explorar Grafo de Conocimiento:**")

	# mostrar objeto Network en Streamlit
	net.show("mygraph.html")
	html_file = open('mygraph.html')
	html_content = html_file.read()
	st.components.v1.html(html_content, width=700, height=500)

    # consulta a datasets y kernels
	c1 = coleccion.find({"$and": [{"topic": {"$regex": "^" + consulta + "$", "$options": "i"}}, 
                         {"type": 'datasets'}, 
                         {"voteCount": {"$gt": votos}}]})

	# Convierte los resultados de la consulta a MongoDB, convertir en un DataFrame de Pandas
	df = pd.DataFrame(list(c1))

	# cambiar nombre a las columnas
	df = df.rename(columns={"topic": "Tópico", 
                        "type": "Tipo",
                        "urlKaggle": "URL Kaggle",
                        "autor": "Autor",
                        "title": "Título", 
                        "voteCount": "Votos"})

	# converir a int los votos
	if "Votos" in df.columns:
		df["Votos"] = df["Votos"].apply(lambda x: round(x))

	# Modificar la columna "URL Kaggle" en el DataFrame original para mostrarla como un hipervínculo
	if "URL Kaggle" in df.columns:
		df["URL Kaggle"] = df["URL Kaggle"].apply(lambda x: f"[Kaggle]({x if x.startswith('http') else 'https://www.' + x})")

	# ordenar por votos los resultados
	# df = df.sort_values(['Tópico', 'Votos'], ascending=[False, False])

	# Selecciona las columnas que deseas mostrar
	selected_columns = ["Tipo", "Título", "Autor", "URL Kaggle", "Votos"]

	# Verifica que las columnas existan en el DataFrame
	columns_exist = all([col in df.columns for col in selected_columns])

	st.write("**Recursos Educativos:**")

	# imprimir tabla de los recursos educativos recopilados con la consulta MongoDB
	if columns_exist:
		markdown_text = df[selected_columns].to_markdown(index=False)
		st.markdown(markdown_text)

# cuando seleccionamos kernels
elif 'kernels' in valores_seleccionados and len(valores_seleccionados) == 1:

	# consultar metadatos dbpedia
	dbpedia = coleccion3.find({"topic": {"$regex": "^" + consulta + "$", "$options": "i"}})

	# transformar a dataframe la consulta
	df_dbpedia = pd.DataFrame(list(dbpedia))

	# obtener el titulo del topico
	st.header(df_dbpedia['topic'].iloc[0])

	# imprimir imagen con condicional en caso de no existir imagen
	if not df_dbpedia['images'].isnull().all():
		image_url = df_dbpedia['images'].iloc[0]
		st.image(image_url)
	else:
		st.write("No se encontró ninguna imagen.")

	# imprimir descripcion
	descriptions = df_dbpedia['descriptions'].tolist()
	text = "\n".join(descriptions)
	st.write(text)


	# consulta a GraphDB
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

    # llamar a la funcion
	results = consultaGraphDB(consulta)

	st.write("**Temas Relacionados:**")

	# imprimir consulta a graphDB
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


	# esto es para el grafo de conocimiento
	for result in results["results"]["bindings"]:
	    if "broader" in result and "subject" in result:
	        broader = result["broader"]["value"]
	        broader_name = broader.split("/")[-1].replace("_", " ")
	        subject = result["subject"]["value"]
	        subject_name = subject.split(":")[-1].replace("_", " ")
	        #net.add_node(consulta)
	        net.add_node(broader_name, title=broader, url=broader)
	        net.add_node(subject_name, title=subject, url=subject)
	        #net.add_edge(consulta, broader_name)
	        net.add_edge(broader_name, subject_name)
	    if "broader" in result and "sameAs" in result:
	        broader = result["broader"]["value"]
	        broader_name = broader.split("/")[-1].replace("_", " ")
	        sameAs = result["sameAs"]["value"]
	        sameAs_name = sameAs.split("/")[-1].replace("_", " ")
	        #net.add_node(consulta)
	        net.add_node(broader_name, title=broader, url=broader)
	        net.add_node(sameAs_name, title=sameAs, url=sameAs)
	        #net.add_edge(consulta, broader_name)
	        net.add_edge(broader_name, sameAs_name)
	    if "subject" in result and "sameAs" in result:
	        subject = result["subject"]["value"]
	        subject_name = subject.split(":")[-1].replace("_", " ")
	        sameAs = result["sameAs"]["value"]
	        sameAs_name = sameAs.split("/")[-1].replace("_", " ")
	        #net.add_node(consulta)
	        net.add_node(subject_name, title=subject, url=subject)
	        net.add_node(sameAs_name, title=sameAs, url=sameAs)
	        #net.add_edge(consulta, subject_name)
	        net.add_edge(subject_name, sameAs_name)
	    if "broader" in result and "subject" in result and "sameAs" in result:
	        broader = result["broader"]["value"]
	        broader_name = broader.split("/")[-1].replace("_", " ")
	        subject = result["subject"]["value"]
	        subject_name = subject.split(":")[-1].replace("_", " ")
	        sameAs = result["sameAs"]["value"]
	        sameAs_name = sameAs.split("/")[-1].replace("_", " ")
	        #net.add_node(consulta)
	        net.add_node(broader_name, title=broader, url=broader)
	        net.add_node(subject_name, title=subject, url=subject)
	        net.add_node(sameAs_name, title=sameAs, url=sameAs)
	        #net.add_edge(consulta, broader_name)
	        net.add_edge(broader_name, subject_name)
	        net.add_edge(subject_name, sameAs_name)

	st.write("**Explorar Grafo de Conocimiento:**")

	# mostrar objeto Network en Streamlit
	net.show("mygraph.html")
	html_file = open('mygraph.html')
	html_content = html_file.read()
	st.components.v1.html(html_content, width=700, height=500)

    # consulta a datasets y kernels
	c1 = coleccion.find({"$and": [{"topic": {"$regex": "^" + consulta + "$", "$options": "i"}}, 
                         {"type": 'datasets'}, 
                         {"voteCount": {"$gt": votos}}]})

	# Convierte los resultados de la consulta a MongoDB, convertir en un DataFrame de Pandas
	df = pd.DataFrame(list(c1))

	# cambiar nombre a las columnas
	df = df.rename(columns={"topic": "Tópico", 
                        "type": "Tipo",
                        "urlKaggle": "URL Kaggle",
                        "autor": "Autor",
                        "title": "Título", 
                        "voteCount": "Votos"})

	# converir a int los votos
	if "Votos" in df.columns:
		df["Votos"] = df["Votos"].apply(lambda x: round(x))

	# Modificar la columna "URL Kaggle" en el DataFrame original para mostrarla como un hipervínculo
	if "URL Kaggle" in df.columns:
		df["URL Kaggle"] = df["URL Kaggle"].apply(lambda x: f"[Kaggle]({x if x.startswith('http') else 'https://www.' + x})")

	# ordenar por votos los resultados
	# df = df.sort_values(['Tópico', 'Votos'], ascending=[False, False])

	# Selecciona las columnas que deseas mostrar
	selected_columns = ["Tipo", "Título", "Autor", "URL Kaggle", "Votos"]

	# Verifica que las columnas existan en el DataFrame
	columns_exist = all([col in df.columns for col in selected_columns])

	st.write("**Recursos Educativos:**")

	# imprimir tabla de los recursos educativos recopilados con la consulta MongoDB
	if columns_exist:
		markdown_text = df[selected_columns].to_markdown(index=False)
		st.markdown(markdown_text)

# cuando se selecciona youtube video
elif 'youtube video' in valores_seleccionados and len(valores_seleccionados) == 1:

	# consultar metadatos dbpedia
	dbpedia = coleccion3.find({"topic": {"$regex": "^" + consulta + "$", "$options": "i"}})

	# transformar a dataframe la consulta
	df_dbpedia = pd.DataFrame(list(dbpedia))

	# obtener el titulo del topico
	st.header(df_dbpedia['topic'].iloc[0])

	# imprimir imagen con condicional en caso de no existir imagen
	if not df_dbpedia['images'].isnull().all():
		image_url = df_dbpedia['images'].iloc[0]
		st.image(image_url)
	else:
		st.write("No se encontró ninguna imagen.")

	# imprimir descripcion
	descriptions = df_dbpedia['descriptions'].tolist()
	text = "\n".join(descriptions)
	st.write(text)


	# consulta a GraphDB
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

    # llamar a la funcion
	results = consultaGraphDB(consulta)

	st.write("**Temas Relacionados:**")

	# imprimir consulta a graphDB
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


	# esto es para el grafo de conocimiento
	for result in results["results"]["bindings"]:
	    if "broader" in result and "subject" in result:
	        broader = result["broader"]["value"]
	        broader_name = broader.split("/")[-1].replace("_", " ")
	        subject = result["subject"]["value"]
	        subject_name = subject.split(":")[-1].replace("_", " ")
	        #net.add_node(consulta)
	        net.add_node(broader_name, title=broader, url=broader)
	        net.add_node(subject_name, title=subject, url=subject)
	        #net.add_edge(consulta, broader_name)
	        net.add_edge(broader_name, subject_name)
	    if "broader" in result and "sameAs" in result:
	        broader = result["broader"]["value"]
	        broader_name = broader.split("/")[-1].replace("_", " ")
	        sameAs = result["sameAs"]["value"]
	        sameAs_name = sameAs.split("/")[-1].replace("_", " ")
	        #net.add_node(consulta)
	        net.add_node(broader_name, title=broader, url=broader)
	        net.add_node(sameAs_name, title=sameAs, url=sameAs)
	        #net.add_edge(consulta, broader_name)
	        net.add_edge(broader_name, sameAs_name)
	    if "subject" in result and "sameAs" in result:
	        subject = result["subject"]["value"]
	        subject_name = subject.split(":")[-1].replace("_", " ")
	        sameAs = result["sameAs"]["value"]
	        sameAs_name = sameAs.split("/")[-1].replace("_", " ")
	        #net.add_node(consulta)
	        net.add_node(subject_name, title=subject, url=subject)
	        net.add_node(sameAs_name, title=sameAs, url=sameAs)
	        #net.add_edge(consulta, subject_name)
	        net.add_edge(subject_name, sameAs_name)
	    if "broader" in result and "subject" in result and "sameAs" in result:
	        broader = result["broader"]["value"]
	        broader_name = broader.split("/")[-1].replace("_", " ")
	        subject = result["subject"]["value"]
	        subject_name = subject.split(":")[-1].replace("_", " ")
	        sameAs = result["sameAs"]["value"]
	        sameAs_name = sameAs.split("/")[-1].replace("_", " ")
	        #net.add_node(consulta)
	        net.add_node(broader_name, title=broader, url=broader)
	        net.add_node(subject_name, title=subject, url=subject)
	        net.add_node(sameAs_name, title=sameAs, url=sameAs)
	        #net.add_edge(consulta, broader_name)
	        net.add_edge(broader_name, subject_name)
	        net.add_edge(subject_name, sameAs_name)

	st.write("**Explorar Grafo de Conocimiento:**")

	# mostrar objeto Network en Streamlit
	net.show("mygraph.html")
	html_file = open('mygraph.html')
	html_content = html_file.read()
	st.components.v1.html(html_content, width=700, height=500)

    # definir la variable "c2" con un valor predeterminado
	c2 = []

	# consulta a datasets y kernels
	if consulta:
		patron = f".*{re.escape(consulta)}.*"
		c2 = coleccion2.find({"$and": [{"videoTitle": {"$regex": patron, "$options": "i"}}, {"type": 'youtube video'}]})

	# Convierte los resultados de la consulta a MongoDB, convertir en un DataFrame de Pandas
	df2 = pd.DataFrame(list(c2))

	df2 = df2.rename(columns={"type": "Tipo", 
                        "videoURL": "URL YouTube",
                        "publishedAt": "Publicado",
                        "videoTitle": "Titulo",
                        "descriptionVideo": "Descripción", 
                        "channelTitle": "Autor"})

	# Modificar la columna "URL YouTube" en el DataFrame original para mostrarla como un hipervínculo
	if "URL YouTube" in df2.columns:
		df2["URL YouTube"] = df2["URL YouTube"].apply(lambda x: f"[YouTube]({x if x.startswith('http') else 'https://www.' + x})")

	# Selecciona las columnas que deseas mostrar
	selected_columns2 = ["Tipo", "Titulo", "Autor", "URL YouTube", "Publicado"]

	# Verifica que las columnas existan en el DataFrame
	columns_exist2 = all([col in df2.columns for col in selected_columns2])

	if columns_exist2:
		markdown_text2 = df2[selected_columns2].to_markdown(index=False)
		st.markdown(markdown_text2)


# cuando se selecciona datasets y kernels
elif 'datasets' in valores_seleccionados and 'kernels' in valores_seleccionados and len(valores_seleccionados) == 2:

	# consultar metadatos dbpedia
	dbpedia = coleccion3.find({"topic": {"$regex": "^" + consulta + "$", "$options": "i"}})

	# transformar a dataframe la consulta
	df_dbpedia = pd.DataFrame(list(dbpedia))

	# obtener el titulo del topico
	st.header(df_dbpedia['topic'].iloc[0])

	# imprimir imagen con condicional en caso de no existir imagen
	if not df_dbpedia['images'].isnull().all():
		image_url = df_dbpedia['images'].iloc[0]
		st.image(image_url)
	else:
		st.write("No se encontró ninguna imagen.")

	# imprimir descripcion
	descriptions = df_dbpedia['descriptions'].tolist()
	text = "\n".join(descriptions)
	st.write(text)


	# consulta a GraphDB
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

    # llamar a la funcion
	results = consultaGraphDB(consulta)

	st.write("**Temas Relacionados:**")

	# imprimir consulta a graphDB
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


	# esto es para el grafo de conocimiento
	for result in results["results"]["bindings"]:
	    if "broader" in result and "subject" in result:
	        broader = result["broader"]["value"]
	        broader_name = broader.split("/")[-1].replace("_", " ")
	        subject = result["subject"]["value"]
	        subject_name = subject.split(":")[-1].replace("_", " ")
	        #net.add_node(consulta)
	        net.add_node(broader_name, title=broader, url=broader)
	        net.add_node(subject_name, title=subject, url=subject)
	        #net.add_edge(consulta, broader_name)
	        net.add_edge(broader_name, subject_name)
	    if "broader" in result and "sameAs" in result:
	        broader = result["broader"]["value"]
	        broader_name = broader.split("/")[-1].replace("_", " ")
	        sameAs = result["sameAs"]["value"]
	        sameAs_name = sameAs.split("/")[-1].replace("_", " ")
	        #net.add_node(consulta)
	        net.add_node(broader_name, title=broader, url=broader)
	        net.add_node(sameAs_name, title=sameAs, url=sameAs)
	        #net.add_edge(consulta, broader_name)
	        net.add_edge(broader_name, sameAs_name)
	    if "subject" in result and "sameAs" in result:
	        subject = result["subject"]["value"]
	        subject_name = subject.split(":")[-1].replace("_", " ")
	        sameAs = result["sameAs"]["value"]
	        sameAs_name = sameAs.split("/")[-1].replace("_", " ")
	        #net.add_node(consulta)
	        net.add_node(subject_name, title=subject, url=subject)
	        net.add_node(sameAs_name, title=sameAs, url=sameAs)
	        #net.add_edge(consulta, subject_name)
	        net.add_edge(subject_name, sameAs_name)
	    if "broader" in result and "subject" in result and "sameAs" in result:
	        broader = result["broader"]["value"]
	        broader_name = broader.split("/")[-1].replace("_", " ")
	        subject = result["subject"]["value"]
	        subject_name = subject.split(":")[-1].replace("_", " ")
	        sameAs = result["sameAs"]["value"]
	        sameAs_name = sameAs.split("/")[-1].replace("_", " ")
	        #net.add_node(consulta)
	        net.add_node(broader_name, title=broader, url=broader)
	        net.add_node(subject_name, title=subject, url=subject)
	        net.add_node(sameAs_name, title=sameAs, url=sameAs)
	        #net.add_edge(consulta, broader_name)
	        net.add_edge(broader_name, subject_name)
	        net.add_edge(subject_name, sameAs_name)

	st.write("**Explorar Grafo de Conocimiento:**")

	# mostrar objeto Network en Streamlit
	net.show("mygraph.html")
	html_file = open('mygraph.html')
	html_content = html_file.read()
	st.components.v1.html(html_content, width=700, height=500)

    # consulta a datasets y kernels
	c1 = coleccion.find({"$and": [{"topic": {"$regex": "^" + consulta + "$", "$options": "i"}}, 
                         {"type": {"$in": ["datasets", "kernels"]}}, 
                         {"voteCount": {"$gt": votos}}]})

	# Convierte los resultados de la consulta a MongoDB, convertir en un DataFrame de Pandas
	df = pd.DataFrame(list(c1))

	# cambiar nombre a las columnas
	df = df.rename(columns={"topic": "Tópico", 
                        "type": "Tipo",
                        "urlKaggle": "URL Kaggle",
                        "autor": "Autor",
                        "title": "Título", 
                        "voteCount": "Votos"})

	# converir a int los votos
	if "Votos" in df.columns:
		df["Votos"] = df["Votos"].apply(lambda x: round(x))

	# Modificar la columna "URL Kaggle" en el DataFrame original para mostrarla como un hipervínculo
	if "URL Kaggle" in df.columns:
		df["URL Kaggle"] = df["URL Kaggle"].apply(lambda x: f"[Kaggle]({x if x.startswith('http') else 'https://www.' + x})")

	# ordenar por votos los resultados
	# df = df.sort_values(['Tópico', 'Votos'], ascending=[False, False])

	# Selecciona las columnas que deseas mostrar
	selected_columns = ["Tipo", "Título", "Autor", "URL Kaggle", "Votos"]

	# Verifica que las columnas existan en el DataFrame
	columns_exist = all([col in df.columns for col in selected_columns])

	st.write("**Recursos Educativos:**")

	# imprimir tabla de los recursos educativos recopilados con la consulta MongoDB
	if columns_exist:
		markdown_text = df[selected_columns].to_markdown(index=False)
		st.markdown(markdown_text)


elif 'datasets' in valores_seleccionados and 'youtube video' in valores_seleccionados and len(valores_seleccionados) == 2:

	# consultar metadatos dbpedia
	dbpedia = coleccion3.find({"topic": {"$regex": "^" + consulta + "$", "$options": "i"}})

	# transformar a dataframe la consulta
	df_dbpedia = pd.DataFrame(list(dbpedia))

	# obtener el titulo del topico
	st.header(df_dbpedia['topic'].iloc[0])

	# imprimir imagen con condicional en caso de no existir imagen
	if not df_dbpedia['images'].isnull().all():
		image_url = df_dbpedia['images'].iloc[0]
		st.image(image_url)
	else:
		st.write("No se encontró ninguna imagen.")

	# imprimir descripcion
	descriptions = df_dbpedia['descriptions'].tolist()
	text = "\n".join(descriptions)
	st.write(text)


	# consulta a GraphDB
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

    # llamar a la funcion
	results = consultaGraphDB(consulta)

	st.write("**Temas Relacionados:**")

	# imprimir consulta a graphDB
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


	# esto es para el grafo de conocimiento
	for result in results["results"]["bindings"]:
	    if "broader" in result and "subject" in result:
	        broader = result["broader"]["value"]
	        broader_name = broader.split("/")[-1].replace("_", " ")
	        subject = result["subject"]["value"]
	        subject_name = subject.split(":")[-1].replace("_", " ")
	        #net.add_node(consulta)
	        net.add_node(broader_name, title=broader, url=broader)
	        net.add_node(subject_name, title=subject, url=subject)
	        #net.add_edge(consulta, broader_name)
	        net.add_edge(broader_name, subject_name)
	    if "broader" in result and "sameAs" in result:
	        broader = result["broader"]["value"]
	        broader_name = broader.split("/")[-1].replace("_", " ")
	        sameAs = result["sameAs"]["value"]
	        sameAs_name = sameAs.split("/")[-1].replace("_", " ")
	        #net.add_node(consulta)
	        net.add_node(broader_name, title=broader, url=broader)
	        net.add_node(sameAs_name, title=sameAs, url=sameAs)
	        #net.add_edge(consulta, broader_name)
	        net.add_edge(broader_name, sameAs_name)
	    if "subject" in result and "sameAs" in result:
	        subject = result["subject"]["value"]
	        subject_name = subject.split(":")[-1].replace("_", " ")
	        sameAs = result["sameAs"]["value"]
	        sameAs_name = sameAs.split("/")[-1].replace("_", " ")
	        #net.add_node(consulta)
	        net.add_node(subject_name, title=subject, url=subject)
	        net.add_node(sameAs_name, title=sameAs, url=sameAs)
	        #net.add_edge(consulta, subject_name)
	        net.add_edge(subject_name, sameAs_name)
	    if "broader" in result and "subject" in result and "sameAs" in result:
	        broader = result["broader"]["value"]
	        broader_name = broader.split("/")[-1].replace("_", " ")
	        subject = result["subject"]["value"]
	        subject_name = subject.split(":")[-1].replace("_", " ")
	        sameAs = result["sameAs"]["value"]
	        sameAs_name = sameAs.split("/")[-1].replace("_", " ")
	        #net.add_node(consulta)
	        net.add_node(broader_name, title=broader, url=broader)
	        net.add_node(subject_name, title=subject, url=subject)
	        net.add_node(sameAs_name, title=sameAs, url=sameAs)
	        #net.add_edge(consulta, broader_name)
	        net.add_edge(broader_name, subject_name)
	        net.add_edge(subject_name, sameAs_name)

	st.write("**Explorar Grafo de Conocimiento:**")

	# mostrar objeto Network en Streamlit
	net.show("mygraph.html")
	html_file = open('mygraph.html')
	html_content = html_file.read()
	st.components.v1.html(html_content, width=700, height=500)

    # consulta a datasets y kernels
	c1 = coleccion.find({"$and": [{"topic": {"$regex": "^" + consulta + "$", "$options": "i"}}, 
                         {"type": 'datasets'}, 
                         {"voteCount": {"$gt": votos}}]})

	# Convierte los resultados de la consulta a MongoDB, convertir en un DataFrame de Pandas
	df = pd.DataFrame(list(c1))

	# cambiar nombre a las columnas
	df = df.rename(columns={"topic": "Tópico", 
                        "type": "Tipo",
                        "urlKaggle": "URL Kaggle",
                        "autor": "Autor",
                        "title": "Título", 
                        "voteCount": "Votos"})

	# converir a int los votos
	if "Votos" in df.columns:
		df["Votos"] = df["Votos"].apply(lambda x: round(x))

	# Modificar la columna "URL Kaggle" en el DataFrame original para mostrarla como un hipervínculo
	if "URL Kaggle" in df.columns:
		df["URL Kaggle"] = df["URL Kaggle"].apply(lambda x: f"[Kaggle]({x if x.startswith('http') else 'https://www.' + x})")

	# ordenar por votos los resultados
	# df = df.sort_values(['Tópico', 'Votos'], ascending=[False, False])

	# Selecciona las columnas que deseas mostrar
	selected_columns = ["Tipo", "Título", "Autor", "URL Kaggle", "Votos"]

	# Verifica que las columnas existan en el DataFrame
	columns_exist = all([col in df.columns for col in selected_columns])

	st.write("**Recursos Educativos:**")

	# imprimir tabla de los recursos educativos recopilados con la consulta MongoDB
	if columns_exist:
		markdown_text = df[selected_columns].to_markdown(index=False)
		st.markdown(markdown_text)

	c2 = []

	# consulta a datasets y kernels
	if consulta:
		patron = f".*{re.escape(consulta)}.*"
		c2 = coleccion2.find({"$and": [{"videoTitle": {"$regex": patron, "$options": "i"}}, {"type": 'youtube video'}]})

	# Convierte los resultados de la consulta a MongoDB, convertir en un DataFrame de Pandas
	df2 = pd.DataFrame(list(c2))

	df2 = df2.rename(columns={"type": "Tipo", 
                        "videoURL": "URL YouTube",
                        "publishedAt": "Publicado",
                        "videoTitle": "Titulo",
                        "descriptionVideo": "Descripción", 
                        "channelTitle": "Autor"})

	# Modificar la columna "URL YouTube" en el DataFrame original para mostrarla como un hipervínculo
	if "URL YouTube" in df2.columns:
		df2["URL YouTube"] = df2["URL YouTube"].apply(lambda x: f"[YouTube]({x if x.startswith('http') else 'https://www.' + x})")

	# Selecciona las columnas que deseas mostrar
	selected_columns2 = ["Tipo", "Titulo", "Autor", "URL YouTube", "Publicado"]

	# Verifica que las columnas existan en el DataFrame
	columns_exist2 = all([col in df2.columns for col in selected_columns2])

	if columns_exist2:
		markdown_text2 = df2[selected_columns2].to_markdown(index=False)
		st.markdown(markdown_text2)

elif 'kernels' in valores_seleccionados and 'youtube video' in valores_seleccionados and len(valores_seleccionados) == 2:

	# consultar metadatos dbpedia
	dbpedia = coleccion3.find({"topic": {"$regex": "^" + consulta + "$", "$options": "i"}})

	# transformar a dataframe la consulta
	df_dbpedia = pd.DataFrame(list(dbpedia))

	# obtener el titulo del topico
	st.header(df_dbpedia['topic'].iloc[0])

	# imprimir imagen con condicional en caso de no existir imagen
	if not df_dbpedia['images'].isnull().all():
		image_url = df_dbpedia['images'].iloc[0]
		st.image(image_url)
	else:
		st.write("No se encontró ninguna imagen.")

	# imprimir descripcion
	descriptions = df_dbpedia['descriptions'].tolist()
	text = "\n".join(descriptions)
	st.write(text)


	# consulta a GraphDB
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

    # llamar a la funcion
	results = consultaGraphDB(consulta)

	st.write("**Temas Relacionados:**")

	# imprimir consulta a graphDB
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


	# esto es para el grafo de conocimiento
	for result in results["results"]["bindings"]:
	    if "broader" in result and "subject" in result:
	        broader = result["broader"]["value"]
	        broader_name = broader.split("/")[-1].replace("_", " ")
	        subject = result["subject"]["value"]
	        subject_name = subject.split(":")[-1].replace("_", " ")
	        #net.add_node(consulta)
	        net.add_node(broader_name, title=broader, url=broader)
	        net.add_node(subject_name, title=subject, url=subject)
	        #net.add_edge(consulta, broader_name)
	        net.add_edge(broader_name, subject_name)
	    if "broader" in result and "sameAs" in result:
	        broader = result["broader"]["value"]
	        broader_name = broader.split("/")[-1].replace("_", " ")
	        sameAs = result["sameAs"]["value"]
	        sameAs_name = sameAs.split("/")[-1].replace("_", " ")
	        #net.add_node(consulta)
	        net.add_node(broader_name, title=broader, url=broader)
	        net.add_node(sameAs_name, title=sameAs, url=sameAs)
	        #net.add_edge(consulta, broader_name)
	        net.add_edge(broader_name, sameAs_name)
	    if "subject" in result and "sameAs" in result:
	        subject = result["subject"]["value"]
	        subject_name = subject.split(":")[-1].replace("_", " ")
	        sameAs = result["sameAs"]["value"]
	        sameAs_name = sameAs.split("/")[-1].replace("_", " ")
	        #net.add_node(consulta)
	        net.add_node(subject_name, title=subject, url=subject)
	        net.add_node(sameAs_name, title=sameAs, url=sameAs)
	        #net.add_edge(consulta, subject_name)
	        net.add_edge(subject_name, sameAs_name)
	    if "broader" in result and "subject" in result and "sameAs" in result:
	        broader = result["broader"]["value"]
	        broader_name = broader.split("/")[-1].replace("_", " ")
	        subject = result["subject"]["value"]
	        subject_name = subject.split(":")[-1].replace("_", " ")
	        sameAs = result["sameAs"]["value"]
	        sameAs_name = sameAs.split("/")[-1].replace("_", " ")
	        #net.add_node(consulta)
	        net.add_node(broader_name, title=broader, url=broader)
	        net.add_node(subject_name, title=subject, url=subject)
	        net.add_node(sameAs_name, title=sameAs, url=sameAs)
	        #net.add_edge(consulta, broader_name)
	        net.add_edge(broader_name, subject_name)
	        net.add_edge(subject_name, sameAs_name)

	st.write("**Explorar Grafo de Conocimiento:**")

	# mostrar objeto Network en Streamlit
	net.show("mygraph.html")
	html_file = open('mygraph.html')
	html_content = html_file.read()
	st.components.v1.html(html_content, width=700, height=500)

    # consulta a datasets y kernels
	c1 = coleccion.find({"$and": [{"topic": {"$regex": "^" + consulta + "$", "$options": "i"}}, 
                         {"type": 'kernels'}, 
                         {"voteCount": {"$gt": votos}}]})

	# Convierte los resultados de la consulta a MongoDB, convertir en un DataFrame de Pandas
	df = pd.DataFrame(list(c1))

	# cambiar nombre a las columnas
	df = df.rename(columns={"topic": "Tópico", 
                        "type": "Tipo",
                        "urlKaggle": "URL Kaggle",
                        "autor": "Autor",
                        "title": "Título", 
                        "voteCount": "Votos"})

	# converir a int los votos
	if "Votos" in df.columns:
		df["Votos"] = df["Votos"].apply(lambda x: round(x))

	# Modificar la columna "URL Kaggle" en el DataFrame original para mostrarla como un hipervínculo
	if "URL Kaggle" in df.columns:
		df["URL Kaggle"] = df["URL Kaggle"].apply(lambda x: f"[Kaggle]({x if x.startswith('http') else 'https://www.' + x})")

	# ordenar por votos los resultados
	# df = df.sort_values(['Tópico', 'Votos'], ascending=[False, False])

	# Selecciona las columnas que deseas mostrar
	selected_columns = ["Tipo", "Título", "Autor", "URL Kaggle", "Votos"]

	# Verifica que las columnas existan en el DataFrame
	columns_exist = all([col in df.columns for col in selected_columns])

	st.write("**Recursos Educativos:**")

	# imprimir tabla de los recursos educativos recopilados con la consulta MongoDB
	if columns_exist:
		markdown_text = df[selected_columns].to_markdown(index=False)
		st.markdown(markdown_text)

	# definir la variable "c2" con un valor predeterminado
	c2 = []

	# consulta a datasets y kernels
	if consulta:
		patron = f".*{re.escape(consulta)}.*"
		c2 = coleccion2.find({"$and": [{"videoTitle": {"$regex": patron, "$options": "i"}}, {"type": 'youtube video'}]})

	# Convierte los resultados de la consulta a MongoDB, convertir en un DataFrame de Pandas
	df2 = pd.DataFrame(list(c2))

	df2 = df2.rename(columns={"type": "Tipo", 
                        "videoURL": "URL YouTube",
                        "publishedAt": "Publicado",
                        "videoTitle": "Titulo",
                        "descriptionVideo": "Descripción", 
                        "channelTitle": "Autor"})

	# Modificar la columna "URL YouTube" en el DataFrame original para mostrarla como un hipervínculo
	if "URL YouTube" in df2.columns:
		df2["URL YouTube"] = df2["URL YouTube"].apply(lambda x: f"[YouTube]({x if x.startswith('http') else 'https://www.' + x})")

	# Selecciona las columnas que deseas mostrar
	selected_columns2 = ["Tipo", "Titulo", "Autor", "URL YouTube", "Publicado"]

	# Verifica que las columnas existan en el DataFrame
	columns_exist2 = all([col in df2.columns for col in selected_columns2])

	if columns_exist2:
		markdown_text2 = df2[selected_columns2].to_markdown(index=False)
		st.markdown(markdown_text2)

elif 'datasets' in valores_seleccionados and 'kernels' in valores_seleccionados and 'youtube video' in valores_seleccionados and len(valores_seleccionados) == 3:

	# consultar metadatos dbpedia
	dbpedia = coleccion3.find({"topic": {"$regex": "^" + consulta + "$", "$options": "i"}})

	# transformar a dataframe la consulta
	df_dbpedia = pd.DataFrame(list(dbpedia))

	# obtener el titulo del topico
	st.header(df_dbpedia['topic'].iloc[0])

	# imprimir imagen con condicional en caso de no existir imagen
	if not df_dbpedia['images'].isnull().all():
		image_url = df_dbpedia['images'].iloc[0]
		st.image(image_url)
	else:
		st.write("No se encontró ninguna imagen.")

	# imprimir descripcion
	descriptions = df_dbpedia['descriptions'].tolist()
	text = "\n".join(descriptions)
	st.write(text)


	# consulta a GraphDB
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

    # llamar a la funcion
	results = consultaGraphDB(consulta)

	st.write("**Temas Relacionados:**")

	# imprimir consulta a graphDB
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


	# esto es para el grafo de conocimiento
	for result in results["results"]["bindings"]:
	    if "broader" in result and "subject" in result:
	        broader = result["broader"]["value"]
	        broader_name = broader.split("/")[-1].replace("_", " ")
	        subject = result["subject"]["value"]
	        subject_name = subject.split(":")[-1].replace("_", " ")
	        #net.add_node(consulta)
	        net.add_node(broader_name, title=broader, url=broader)
	        net.add_node(subject_name, title=subject, url=subject)
	        #net.add_edge(consulta, broader_name)
	        net.add_edge(broader_name, subject_name)
	    if "broader" in result and "sameAs" in result:
	        broader = result["broader"]["value"]
	        broader_name = broader.split("/")[-1].replace("_", " ")
	        sameAs = result["sameAs"]["value"]
	        sameAs_name = sameAs.split("/")[-1].replace("_", " ")
	        #net.add_node(consulta)
	        net.add_node(broader_name, title=broader, url=broader)
	        net.add_node(sameAs_name, title=sameAs, url=sameAs)
	        #net.add_edge(consulta, broader_name)
	        net.add_edge(broader_name, sameAs_name)
	    if "subject" in result and "sameAs" in result:
	        subject = result["subject"]["value"]
	        subject_name = subject.split(":")[-1].replace("_", " ")
	        sameAs = result["sameAs"]["value"]
	        sameAs_name = sameAs.split("/")[-1].replace("_", " ")
	        #net.add_node(consulta)
	        net.add_node(subject_name, title=subject, url=subject)
	        net.add_node(sameAs_name, title=sameAs, url=sameAs)
	        #net.add_edge(consulta, subject_name)
	        net.add_edge(subject_name, sameAs_name)
	    if "broader" in result and "subject" in result and "sameAs" in result:
	        broader = result["broader"]["value"]
	        broader_name = broader.split("/")[-1].replace("_", " ")
	        subject = result["subject"]["value"]
	        subject_name = subject.split(":")[-1].replace("_", " ")
	        sameAs = result["sameAs"]["value"]
	        sameAs_name = sameAs.split("/")[-1].replace("_", " ")
	        #net.add_node(consulta)
	        net.add_node(broader_name, title=broader, url=broader)
	        net.add_node(subject_name, title=subject, url=subject)
	        net.add_node(sameAs_name, title=sameAs, url=sameAs)
	        #net.add_edge(consulta, broader_name)
	        net.add_edge(broader_name, subject_name)
	        net.add_edge(subject_name, sameAs_name)

	st.write("**Explorar Grafo de Conocimiento:**")

	# mostrar objeto Network en Streamlit
	net.show("mygraph.html")
	html_file = open('mygraph.html')
	html_content = html_file.read()
	st.components.v1.html(html_content, width=700, height=500)

    # consulta a datasets y kernels
	c1 = coleccion.find({"$and": [{"topic": {"$regex": "^" + consulta + "$", "$options": "i"}}, 
                         {"type": {"$in": ["datasets", "kernels"]}}, 
                         {"voteCount": {"$gt": votos}}]})

	# Convierte los resultados de la consulta a MongoDB, convertir en un DataFrame de Pandas
	df = pd.DataFrame(list(c1))

	# cambiar nombre a las columnas
	df = df.rename(columns={"topic": "Tópico", 
                        "type": "Tipo",
                        "urlKaggle": "URL Kaggle",
                        "autor": "Autor",
                        "title": "Título", 
                        "voteCount": "Votos"})

	# converir a int los votos
	if "Votos" in df.columns:
		df["Votos"] = df["Votos"].apply(lambda x: round(x))

	# Modificar la columna "URL Kaggle" en el DataFrame original para mostrarla como un hipervínculo
	if "URL Kaggle" in df.columns:
		df["URL Kaggle"] = df["URL Kaggle"].apply(lambda x: f"[Kaggle]({x if x.startswith('http') else 'https://www.' + x})")

	# ordenar por votos los resultados
	# df = df.sort_values(['Tópico', 'Votos'], ascending=[False, False])

	# Selecciona las columnas que deseas mostrar
	selected_columns = ["Tipo", "Título", "Autor", "URL Kaggle", "Votos"]

	# Verifica que las columnas existan en el DataFrame
	columns_exist = all([col in df.columns for col in selected_columns])

	st.write("**Recursos Educativos:**")

	# imprimir tabla de los recursos educativos recopilados con la consulta MongoDB
	if columns_exist:
		markdown_text = df[selected_columns].to_markdown(index=False)
		st.markdown(markdown_text)
	# definir la variable "c2" con un valor predeterminado
	c2 = []

	# consulta a datasets y kernels
	if consulta:
		patron = f".*{re.escape(consulta)}.*"
		c2 = coleccion2.find({"$and": [{"videoTitle": {"$regex": patron, "$options": "i"}}, {"type": 'youtube video'}]})

	# Convierte los resultados de la consulta a MongoDB, convertir en un DataFrame de Pandas
	df2 = pd.DataFrame(list(c2))

	df2 = df2.rename(columns={"type": "Tipo", 
                        "videoURL": "URL YouTube",
                        "publishedAt": "Publicado",
                        "videoTitle": "Titulo",
                        "descriptionVideo": "Descripción", 
                        "channelTitle": "Autor"})

	# Modificar la columna "URL YouTube" en el DataFrame original para mostrarla como un hipervínculo
	if "URL YouTube" in df2.columns:
		df2["URL YouTube"] = df2["URL YouTube"].apply(lambda x: f"[YouTube]({x if x.startswith('http') else 'https://www.' + x})")

	# Selecciona las columnas que deseas mostrar
	selected_columns2 = ["Tipo", "Titulo", "Autor", "URL YouTube", "Publicado"]

	# Verifica que las columnas existan en el DataFrame
	columns_exist2 = all([col in df2.columns for col in selected_columns2])

	if columns_exist2:
		markdown_text2 = df2[selected_columns2].to_markdown(index=False)
		st.markdown(markdown_text2)
	