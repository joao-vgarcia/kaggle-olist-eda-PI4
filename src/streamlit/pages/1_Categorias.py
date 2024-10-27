from dataclasses import dataclass
import streamlit as st
import pandas as pd
import seaborn as sns
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
from unidecode import unidecode

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
st.write("# Categorias")

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
        return '#EAEAEA'
    elif category ==  'construcao':
        return '#DBD8EA'
    elif category ==  'eletronicos':
        return '#D3CFEA'
    elif category ==  'casa':
        return '#CBC5EA'
    elif category ==  'informatica':
        return '#9F94BA'
    elif category ==  'moda':
        return '#73628A'
    elif category ==  'saude':
        return '#313D5A'
    elif category ==  'hobbies':
        return '#183642'
    else:
        return '#2D4853'

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


tab_categoria, tab_crescimento = st.tabs(['Categorias', 'Crescimento'])
with tab_categoria:
    st.write("# Categorias")
    col1, col2 = st.columns(2)
    with col1:
        st.write("## Veja quanto foi gasto por categoria")
    with col2:
        st.write("")
        show_macro_category = st.toggle("Categoria/Macro categoria", value=False, key='data_frame_toggle')
    
    df_category_ = create_category_dataframe(df_obj)
    df_macro_category_ = create_macro_category_dataframe(df_obj)
    if show_macro_category:
        df_plot = df_macro_category_.copy()
        rename_dict = {
            "product_macro_category_rename": "Macro_categoria",
            "product_macro_category": "Categoria",
            "year": "Ano",
            "price": "Preco"
        }
        df_plot = df_plot.rename(columns=rename_dict)
        df_plot = df_plot.sort_values(by=['Preco', 'Ano'], ascending=False)
        texto_analise = """
        As top 3 macro categorias são: Moda, Saúde e Casa.
        
        Os consumidores compraram mais produtos para saúde e casa. O segmento de moda perdeu relevância.
        """
        fig_height = 600
        plot_options = df_plot['Macro_categoria'].unique()
        y_name='Macro_categoria'
    else:
        df_plot = df_category_.copy()
        rename_dict = {
            "product_macro_category_rename": "Macro_categoria",
            "product_macro_category": "Categoria",
            "year": "Ano",
            "price": "Preco"
        }
        df_plot = df_plot.rename(columns=rename_dict)
        texto_analise = """
        As top 3 categorias em 2017 são: Móveis, Cama e Relógios.
        
        As top 3 categorias em 2018 são: Beleza, Relógios e Móveis.
        
        Houve um aumento na busca por itens de beleza.
        Os itens de cama perderam relevância mas houve um aumento de mais de 10% de receita
        """
        
        plot_options = df_plot['Categoria'].unique()
        fig_height = 1200
        y_name='Categoria'
    
    col1, col2 = st.columns(2)
    
    with col1:
        group_by_macro_category = st.toggle(label='Agrupar por categoria', value=False, key='group_by_macro_category')
    with col2:
        with st.expander("Filtros"):
            display_categories = st.multiselect(
                label="Selecione as categorias",
                options=plot_options,
                default=plot_options,
            )
    
    df_plot['category_color'] = df_plot['Macro_categoria'].apply(lambda x: category_color_sequence(x))
    max_x = df_plot['Preco'].max()
    
    if show_macro_category:
        mask_categories = df_plot['Macro_categoria'].isin(display_categories)
        color='Macro_categoria'
        df_plot = df_plot[mask_categories]
        fig = px.bar(
            df_plot.sort_values(by=['Ano', 'Preco'], ascending=True),
            y=y_name, 
            x="Preco",
            animation_frame="Ano",
            range_x=[0,max_x*1.05],
            height=fig_height,
            color=color
        )
        fig.update_layout(
            yaxis={
                'categoryorder': 'total ascending'
            }
        )

    else:
        if group_by_macro_category:
            color='Macro_categoria'
            mask_categories = df_plot['Categoria'].isin(display_categories)
            df_plot = df_plot[mask_categories]
            df_plot = df_plot.sort_values(by=['Ano','Preco',], ascending=True)
            fig = px.bar(
                df_plot, 
                y=y_name, 
                x="Preco",
                animation_frame="Ano",
                range_x=[0,max_x*1.05],
                height=fig_height,
                color=color,
                hover_data=['Categoria', 'Macro_categoria','Preco'],
            )

        else:
            mask_categories = df_plot['Categoria'].isin(display_categories)
            df_plot = df_plot[mask_categories]
            df_plot = df_plot.sort_values(by=['Ano', 'Preco'], ascending=True)
            fig = px.bar(
                df_plot,
                y=y_name,
                x="Preco",
                animation_frame="Ano",
                range_x=[0,max_x*1.05],
                height=fig_height,
                hover_data=['Categoria', 'Macro_categoria', 'Preco'],
                color='Macro_categoria',
            )
            fig.update_layout(
                yaxis={
                    'categoryorder': 'total ascending'
                }
            )
            
        
        
    fig.update_layout(hovermode='y unified')
    st.write('Análise')
    st.write(texto_analise)
    st.plotly_chart(
        figure_or_data=fig,
        use_container_width=False,
        theme=None
    )
with tab_crescimento:
    st.write("# Crescimento")
    st.write('## Comparação entre os anos')
    show_macro_category = st.toggle("Macro categoria/Categoria", value=False, key='data_frame_toggle_tendency')
    if show_macro_category:
        df_category_ = create_category_dataframe(df_obj)
        df_pivot_category = pd.pivot_table(
            data=df_category_,
            index='product_macro_category',
            columns = 'year',
            values='price'
        ).reset_index()
        df_pivot_category['tendency'] = df_pivot_category[2018] - df_pivot_category[2017]
        df_pivot_category['product_macro_category_rename'] = df_pivot_category['product_macro_category'].apply(lambda x: rename_category(x))
        fig = px.bar(
            data_frame=df_pivot_category,
            y='product_macro_category',
            x='tendency',
            orientation='h',
            height=1200,
            color='product_macro_category_rename'
        )
        fig.update_layout(
            yaxis={
                'categoryorder': 'total ascending'
            }
        )
        texto_analise = """
        As categorias que mais cresceram foram: Beleza, Relógios e Construção. 
        
        O segmento de utilidades também é um grande destaque.
        """
    
    else:
        df_macro_category_ = create_macro_category_dataframe(df_obj)
        df_pivot_macro_category = pd.pivot_table(
            data=df_macro_category_,
            index='product_macro_category_rename',
            columns = 'year',
            values='price'
        ).reset_index()
        df_pivot_macro_category['tendency'] = df_pivot_macro_category[2018] - df_pivot_macro_category[2017]
        fig = px.bar(
            data_frame=df_pivot_macro_category,
            y='product_macro_category_rename',
            x='tendency',
            orientation='h',
            height=800,
            color='product_macro_category_rename'
        )
        fig.update_layout(
            yaxis={
                'categoryorder': 'total ascending'
            }
        )
        texto_analise = """
        As macro categorias que mais cresceram foram: Saúde, Casa e Hobbies. 
        
        O segmento de saúde teve mais de 40% de crescimento em relação ao segmento casa.
        """
    
    st.write('Análise') 
    st.write(texto_analise) 
    st.plotly_chart(
        figure_or_data=fig,
        use_container_width=False,
        theme=None
    )
