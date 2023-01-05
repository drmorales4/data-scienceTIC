# streamlit

import streamlit as st
import pandas as pd

st.title('My Cool Bar Chart')


df = pd.read_csv('data.csv')

st.dataframe(df)

st.bar_chart(df)