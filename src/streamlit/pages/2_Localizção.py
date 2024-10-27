from dataclasses import dataclass
import folium.map
import streamlit as st
import pandas as pd
import seaborn as sns
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
from unidecode import unidecode
from streamlit_folium import st_folium
import folium

regiao_nordeste = ['BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE', 'AL']
regiao_sudeste = ['SP', 'RJ', 'MG', 'ES']
regiao_norte = ['AM', 'PA', 'AP', 'RR', 'RO', 'AC', 'TO']
regiao_centro_oeste = ['MT', 'MS', 'GO', 'DF']
regiao_sul = ['PR', 'SC', 'RS']

@dataclass
class IOlistDataframes:
    df_customers: pd.DataFrame
    df_geolocation: pd.DataFrame
    df_order_items: pd.DataFrame
    df_order_payments: pd.DataFrame
    df_orders: pd.DataFrame
    df_products: pd.DataFrame
    df_sellers: pd.DataFrame
    df_product_category_translation: pd.DataFrame

st.set_page_config(layout="wide")
st.write("# Localização ")
st.write("### O carregamento dos mapas pode levar alguns minutos. Por favor, aguarde. ")
st.write("### Alguns filtros estão ativos para agilizar o carregamento. ")

@st.cache_data
def init_get_datasets()->IOlistDataframes:
    df_customers: pd.DataFrame = pd.read_csv('./src/streamlit/data/olist_customers_dataset.csv')

    df_geolocation: pd.DataFrame = pd.read_csv('./src/streamlit/data/olist_geolocation_dataset.csv')
    df_geolocation['geolocation_city']=df_geolocation['geolocation_city'].apply(lambda x: unidecode(x).lower())
    df_geolocation['geolocation_state']=df_geolocation['geolocation_state'].apply(lambda x: unidecode(x).upper())

    df_order_items: pd.DataFrame = pd.read_csv('./src/streamlit/data/olist_order_items_dataset.csv')
    df_order_items['shipping_limit_date'] = pd.to_datetime(df_order_items['shipping_limit_date'])
    df_order_items['year'] = df_order_items['shipping_limit_date'].dt.year
    
    df_order_payments: pd.DataFrame = pd.read_csv('./src/streamlit/data/olist_order_payments_dataset.csv')
    
    df_orders: pd.DataFrame = pd.read_csv('./src/streamlit/data/olist_orders_dataset.csv')
    
    date_columns = ['order_purchase_timestamp', 'order_delivered_carrier_date', 'order_delivered_customer_date', 'order_estimated_delivery_date']
    for column in date_columns:
        df_orders[column] = pd.to_datetime(df_orders[column])
        
    df_orders['year'] = df_orders['order_purchase_timestamp'].dt.year

    df_products: pd.DataFrame = pd.read_csv('./src/streamlit/data/olist_products_dataset.csv')

    df_products['product_category_name']= df_products['product_category_name'].fillna('outros')

    df_products.loc[:,'product_macro_category'] = df_products['product_category_name'].apply(lambda x: x.split('_')[0])

    df_sellers: pd.DataFrame = pd.read_csv('./src/streamlit/data/olist_sellers_dataset.csv')

    df_product_category_translation: pd.DataFrame = pd.read_csv('./src/streamlit/data/product_category_name_translation.csv')
    
    obj = IOlistDataframes(
        df_customers=df_customers,
        df_geolocation=df_geolocation,
        df_order_items=df_order_items,
        df_order_payments=df_order_payments,
        df_orders=df_orders,
        df_products=df_products,
        df_sellers=df_sellers,
        df_product_category_translation=df_product_category_translation
    )
    
    return obj

df_obj = init_get_datasets()

# ----------------------------------------------------------------------------

def rename_category(category:str)->str:
    alimentos=['alimentos','bebidas']
    casa=['cama','casa','eletrodomesticos','moveis']
    construcao=['construcao','ferramentas','climatizacao','sinalizacao']
    informatica=['consoles','eletroportateis','informatica','pc','pcs','portateis','tablets','telefonia']
    eletronicos=['audio','automotivo','eletronicos',]
    moda=['artigos','bebes','cool','fashion','la','relogios']
    saude=['beleza','fraldas','perfumaria','esporte']
    hobbies=['cds','dvds','cine','utilidades','livros','musica','papelaria','flores','instrumentos','brinquedos','pet']
    
    if category in alimentos:
        return 'alimentos'
    elif category in construcao:
        return 'construcao'
    elif category in eletronicos:
        return 'eletronicos'
    elif category in casa:
        return 'casa'
    elif category in informatica:
        return 'informatica'
    elif category in moda:
        return 'moda'
    elif category in saude:
        return 'saude'
    elif category in hobbies:
        return 'hobbies'
    else:
        return 'outros'

def category_color_sequence(category:str)->str:
    if category ==  'alimentos':
        return '#c4392f'
    elif category ==  'construcao':
        return '#c4a22f'
    elif category ==  'eletronicos':
        return '#1a1918'
    elif category ==  'casa':
        return '#0b4002'
    elif category ==  'informatica':
        return '#7d040e'
    elif category ==  'moda':
        return '#02dbf7'
    elif category ==  'saude':
        return '#0233f7'
    elif category ==  'hobbies':
        return '#926bc2'
    else:
        return '#d909d5'
 
def get_region(customer_state: str) -> str:
    if customer_state in regiao_nordeste:
        return 'Nordeste'
    elif customer_state in regiao_sudeste:
        return "Sudeste"
    elif customer_state in regiao_norte:
        return "Norte"
    elif customer_state in regiao_centro_oeste:
        return "Centro-Oeste"
    elif customer_state in regiao_sul:
        return "Sul"
    else:
        return "Brasil"

def create_category_dataframe(df_obj: IOlistDataframes)-> pd.DataFrame:
    order_items_columns = ['product_id', 'price', 'freight_value', 'year']
    products_columns = ['product_id', 'product_category_name', 'product_macro_category']
    
    df_category: pd.DataFrame = df_obj.df_order_items[order_items_columns].merge(df_obj.df_products[products_columns], on='product_id')
    
    mask_2017_2018 = df_category['year'].between(2017,2018)
    df_category = df_category[mask_2017_2018]
    df_category['product_macro_category_rename'] = df_category['product_macro_category'].apply(lambda x: rename_category(x))
    agg_dict = {
        'price':'sum',
        'product_macro_category_rename': 'first'
    }
    group_by_columns = ['product_macro_category','year']
    df_category_per_year = df_category.groupby(group_by_columns).agg(agg_dict).reset_index()
    return df_category_per_year.sort_values(by=['price','year'], ascending=True)

def create_macro_category_dataframe(df_obj: IOlistDataframes)-> pd.DataFrame:
    order_items_columns = ['product_id', 'price', 'freight_value', 'year']
    products_columns = ['product_id', 'product_category_name', 'product_macro_category']
    
    df_category: pd.DataFrame = df_obj.df_order_items[order_items_columns].merge(df_obj.df_products[products_columns], on='product_id')
    
    mask_2017_2018 = df_category['year'].between(2017,2018)
    df_category = df_category[mask_2017_2018]
    df_category['product_macro_category_rename'] = df_category['product_macro_category'].apply(lambda x: rename_category(x))
    agg_dict = {'price':'sum'}
    group_by_columns = ['product_macro_category_rename','year']
    df_macro_category_per_year = df_category.groupby(group_by_columns).agg(agg_dict).reset_index()
    return df_macro_category_per_year

def create_geolocation_orders_dataframe(df_obj: IOlistDataframes)-> pd.DataFrame:
    mask_2017_2018 = df_obj.df_orders['year'].between(2017,2018)
    orders_columns = ['order_id', 'customer_id', 'year']
    customers_columns = ['customer_id', 'customer_zip_code_prefix']
    geolocation_columns = ['geolocation_zip_code_prefix','geolocation_lat', 'geolocation_lng']
    geolocation_group_by_columns = ['geolocation_zip_code_prefix']
    agg_dict = {
        'geolocation_lat':'mean',
        'geolocation_lng':'mean'
    }
    df_unique_geolocation = df_obj.df_geolocation.groupby(geolocation_group_by_columns).agg(agg_dict).reset_index()
    agg_dict = {
        'price': 'sum',
        'freight_value': 'sum'
    }
    df_order_prices = df_obj.df_order_items.groupby('order_id').agg(agg_dict).reset_index()
    
    df_geolocation_orders = df_obj.df_orders.loc[mask_2017_2018, orders_columns].merge(
        df_obj.df_customers[customers_columns], 
        on='customer_id', 
        how='left'
        ).merge(
                df_unique_geolocation[geolocation_columns], 
                left_on='customer_zip_code_prefix', 
                right_on='geolocation_zip_code_prefix', 
                how='left'
            ).merge(
                    df_order_prices, 
                    on='order_id', 
                    how='left'
                )

    return df_geolocation_orders

def create_geo_categories_dataframe(df_obj: IOlistDataframes)-> pd.DataFrame:
    mask_2017_2018 = df_obj.df_orders['year'].between(2017,2018)
    order_items_columns = ['order_id', 'product_id', 'price', 'freight_value',]
    orders_columns = ['order_id', 'customer_id', 'year']
    customers_columns = ['customer_id', 'customer_zip_code_prefix']
    products_columns = ['product_id', 'product_macro_category']
    geolocation_group_by_columns = ['geolocation_zip_code_prefix']
    agg_dict = {
        'geolocation_lat':'mean',
        'geolocation_lng':'mean'
    }
    df_unique_geolocation = df_obj.df_geolocation.groupby(geolocation_group_by_columns).agg(agg_dict).reset_index()
    
    df_geolocation_categories: pd.DataFrame = df_obj.df_order_items[order_items_columns].merge(
            df_obj.df_products[products_columns], 
            on='product_id', 
            how='left'
        ).merge(
                df_obj.df_orders[orders_columns], 
                on='order_id', 
                how='left'
            ).merge(
                    df_obj.df_customers[customers_columns], 
                    on='customer_id', 
                    how='left'
                ).merge(
                        df_unique_geolocation, 
                        left_on='customer_zip_code_prefix', 
                        right_on='geolocation_zip_code_prefix', 
                        how='left'
                    )
    df_geolocation_categories['product_macro_category_rename'] = df_geolocation_categories['product_macro_category'].apply(lambda x: rename_category(x))
    df_geolocation_categories['color'] = df_geolocation_categories['product_macro_category_rename'].apply(lambda x: category_color_sequence(x))
    return df_geolocation_categories

# ----------------------------------------------------------------------------

df_geolocation_orders = create_geo_categories_dataframe(df_obj)
df_geolocation_orders = df_geolocation_orders.dropna()
# print(df_geolocation_orders['product_macro_category_rename'].value_counts() )
df_geolocation_orders = df_geolocation_orders.merge(df_obj.df_customers, how='left', on='customer_id') 
df_geolocation_orders['region'] = df_geolocation_orders['customer_state'].apply(lambda x: get_region(x))
df_geolocation_orders['color'] = df_geolocation_orders['product_macro_category_rename'].apply(lambda x: category_color_sequence(x))
st.write("# Localização dos pedidos")
st.write('Defina filtros para melhorar a visualização')
col1, col2, col3 = st.columns(3)
with col1:
    with st.expander("Filtro por ano"):
        year = st.radio(label='Ano', options=[2017, 2018], index=1, key='ano_mapa')
        mask_year = df_geolocation_orders['year'] == year
with col2:
    with st.expander("Filtro por região"):
        region = st.multiselect(
            'Região',
            df_geolocation_orders['region'].unique(),
            df_geolocation_orders['region'].unique()
        )
        mask_region = df_geolocation_orders['region'].isin(region)
with col3:
    with st.expander("Filtro por categoria"):
        macro_category = st.multiselect(
            'Categoria',
            default=['casa','informatica'],
            options=df_geolocation_orders['product_macro_category_rename'].unique()
        )
        mask_category = df_geolocation_orders['product_macro_category_rename'].isin(macro_category)
df_geolocation_orders = df_geolocation_orders[mask_year & mask_region & mask_category]

colm1,cvazio,colm2 = st.columns((3,3,3))
with colm1:
    with st.expander('Quantidade de pontos no mapa'):
        st.write('Defina a quantidade de pedidos no mapa. Quanto maior o valor, mais demora para carregar.')
        max_value = len(df_geolocation_orders)-1
        curr_value_initial = 0
        curr_value_max = 1
        if max_value > 1000:
            curr_value_max = 1000
        else:
            curr_value_max = max_value/2
        min_views, max_views = st.select_slider(label='Quantidade de pedidos', options=range(0, int(max_value)), value=(curr_value_initial, int(curr_value_max)), key='quantidade_mapa')

with cvazio:
    with st.expander('Ordenar por Preco ou Frete'):
        order_selected = st.radio(label='Ordem:', options=['Nenhum', 'Preco', 'Frete'], index=1, key='ordem_mapa')
        df_geolocation_orders = df_geolocation_orders.sort_values('year', ascending=False)
        if order_selected == 'Preco':
            df_geolocation_orders = df_geolocation_orders.sort_values('price', ascending=False)
        elif order_selected == 'Frete':
            df_geolocation_orders = df_geolocation_orders.sort_values('freight_value', ascending=False)
with colm2:
    with st.expander('Tamanho relativo'):
        radius_selected = st.radio(label='Tamanho do ponto baseado em:', options=['Nenhum', 'Preco', 'Frete'], index=1, key='tamanho_mapa')
        df_geolocation_orders['radius'] = 2
        if radius_selected == 'Preco':
            df_geolocation_orders['radius'] = (df_geolocation_orders['price']/ df_geolocation_orders['price'].max())
            df_geolocation_orders['radius'] = round(df_geolocation_orders['radius']* 10, 4) + 3.3
        elif radius_selected == 'Frete':
            df_geolocation_orders['radius'] = ((df_geolocation_orders['freight_value'] + 1.0)/ df_geolocation_orders['freight_value'].max())
            df_geolocation_orders['radius'] = round(df_geolocation_orders['radius']* 10, 4) + 3.3

        radius_values = df_geolocation_orders['radius']
    
df_geolocation_orders = df_geolocation_orders.iloc[min_views:max_views]
latitude = df_geolocation_orders['geolocation_lat']
longitude = df_geolocation_orders['geolocation_lng']
prices = df_geolocation_orders['price']
fretes = df_geolocation_orders['freight_value']
categorias = df_geolocation_orders['product_macro_category_rename']
sub_categorias = df_geolocation_orders['product_macro_category']
colors = df_geolocation_orders['color']
regions = df_geolocation_orders['region']
    
zip_values = zip(latitude, longitude, prices, fretes, categorias,sub_categorias, colors, regions, radius_values)

mapa = folium.Map(
    location=[-20.0801, -45.9292], 
    control_scale=True,
    prefer_canvas=True,
    min_zoom=4,
    zoom_start=4)
for lat, long, price, frete, categoria,sub_categoria, color, region, radius in zip_values:
    folium.CircleMarker(
        location=[float(lat), float(long)],
        radius=radius,
        tooltip=categoria,
        popup=f'Categoria: {categoria} <br/><br/> Subcategoria: {sub_categoria} <br/><br/> Valor total: {price} <br/><br/> Frete total: {frete}',
        fill=True,
        fillColor=color,
        weight=0,
        color=color,
        fillOpacity=radius*0.1
    ).add_to(mapa)

st_folium(
    mapa,
    key='localidade1_mapa',
    height=650,
    width=850,
    zoom=4
)
