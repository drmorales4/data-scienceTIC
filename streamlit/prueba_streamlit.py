# importar librerias
import streamlit as st
import pandas as pd
from pymongo import MongoClient
from py2neo import Graph
import rdflib

# Conectarse a la base de datos MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["itinerario"]

# Seleccionar una colección
coleccion = db["dataScience_TIC"]


# Consultar algunos documentos de MongoDB
# documentos = coleccion.find()

# Solicitamos al usuario que ingrese una consulta
consulta = st.text_input("Ingresa el tema a Consultar")

# Obtén las categorías únicas de la colección
categories = coleccion.distinct("type")

# utiliazmos el widget de selección de Streamlit para crear un elemento de selección HTML
selected_category = st.selectbox('Elige una categoría', categories)

# prueba consulta 1
c1 = coleccion.find({"$and": [{"topic": "Data-scientist"}, {"voteCount": {"$lt": 1}}]})


# Mostrar los resultados de MongoDB en la aplicación web
#st.title("Documentos en mi base de datos MongoDB")
#for doc in c1:
#   st.write(doc)

# Crea una lista con los documentos que se van a mostrar en la tabla
data = []
for document in c1:
    data.append([document["topic"], document["type"], document["autor"], document["title"]])

st.table(data)



# GraphDB
'''
# Conecta a GraphDB
g = rdflib.Graph()
g.bind('ns', 'http://example.org/ns#')
g.parse("http://localhost:7200/repositories/dsResources")

# Utiliza el widget de consulta de SPARQL de Streamlit para permitir al usuario escribir y enviar consultas
query = st.text_area()

if query:
    results = g.query(query)
    # Muestra los resultados de la consulta
    st.write(results)

'''
