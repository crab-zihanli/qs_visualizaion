import plotly.express as px
import geopandas as gpd
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# 必须将 st.set_page_config() 放在其他 Streamlit 命令之前
st.set_page_config(layout="wide")

@st.cache_data
def get_data(url):
    return pd.read_excel(url)

@st.cache_data
def get_map_data(persist="disk"):
    url = 'world/tdtGlobal.shp'
    return gpd.read_file(url)

@st.cache_data
def get_qs_data(persist="disk"):
    url = 'qs_ranking_iso.xlsx'
    return get_data(url)
st.markdown("""
# 全球大学QS排名可视化展示

欢迎来到本网站！这里展示了全球 **QS排名前1000的大学** 的可视化图表，包括全球各大洲与国家的大学分布情况、各地区排名前20的大学的柱状图、以及不同大学在各项指标上的得分对比。

- **全球QS排名前1000的大学数量分布**：通过世界地图展示各大洲与国家的大学数量。
- **大洲与国家的大学数量分布**：通过 sunburst 图展现各大洲与国家的大学数量。
- **各地区排名前20的大学柱状图**：可以选择不同的国家，查看该国家排名前20的大学。
- **大学指标得分对比**：通过雷达图展示选定学校在各项指标上的得分。

请使用下方的交互功能选择您感兴趣的数据进行探索。
""")
col1, space, col2 = st.columns((15, 1, 10))

df_qs = get_qs_data()
gdf = get_map_data()


df_country_num = df_qs['iso'].value_counts().reset_index()
df_country_num.columns = ['iso', 'num']
df_country_num = df_country_num.merge(df_qs[['iso', 'Country']].drop_duplicates(), on='iso', how='left')

gdf = gdf.rename(columns={'SOC': 'iso'})
gdf = gdf.merge(df_country_num, on='iso', how='left')

# 将 GeoDataFrame 转换为 GeoJSON 格式
geojson_data = gdf.to_json()
with col1:
    fig = px.choropleth(geojson=gdf.__geo_interface__,  # 使用GeoJSON地图数据
                        locations=gdf.iso,  # 使用GeoDataFrame的索引作为位置
                        featureidkey="properties.iso",  # GeoJSON中的属性名称
                        color=gdf.num,  # 使用索引作为颜色编码
                        hover_name=gdf['Country'],  # 悬停时显示的国家名称
                        color_continuous_scale=px.colors.sequential.Reds
                        )
    # 更新地图样式
    fig.update_geos(
        visible=True,
        showcountries=True,  # 显示国家边界线
        countrycolor="grey"  # 国家边界线颜色
    )

    # 设置标题
    fig.update_layout(
        title="全球QS排名前1000的大学数量分布",
        coloraxis_colorbar=dict(title="大学数量")  # 设置图例标题
    )

    # 用streamlit显示图表，设置宽度为容器宽度
    st.plotly_chart(fig, use_container_width=True)

with col2:
    df_count = df_qs.groupby(['Region', 'Country']).size().reset_index(name='大学数量')
    # 使用 sunburst 绘制图形
    color_map = {
        'Asia': 'rgb(204, 153, 102)',  # 土黄色系
        'Europe': 'rgb(0, 0, 255)',    # 蓝色系
        'NorthAmerica': 'rgb(255, 182, 193)',  # 粉红色系
        'SouthAmerica': 'rgb(255, 105, 180)',  # 粉红色系
        'Africa': 'rgb(128, 128, 128)',  # 灰色
        'Oceania': 'rgb(102, 205, 170)'   # 绿松石色
    }

    # 计算颜色值列，基于 Region
    df_count['color'] = df_count['Region'].map(color_map).fillna('rgb(169, 169, 169)')  # 默认颜色为灰色
    fig = px.sunburst(df_count, 
                    path=['Region', 'Country'],  # 定义层级结构：内环是Region，外环是Country
                    values='大学数量',  # 每个区域的大小为大学数量
                    title="大洲与国家的大学数量分布",
                    color='Region',  # 设置颜色依据Region列
                    color_discrete_map=color_map)

    # 显示图形
    st.plotly_chart(fig, use_container_width=True)

col3, space2, col4 = st.columns((10, 1, 10))
with col3:
    st.markdown("""**不同国家大学QS排名前20的柱状图**""")
    # 选择不同的国家，可以看到该国家排名前20的大学的柱状图
    # 默认展示的是全世界排名前20的大学
    country = st.selectbox('选择国家', ['World']+df_qs['Country'].unique().tolist(), index=0)
    if country == 'World':
        df_country = df_qs.head(20)
    else:
        df_country = df_qs[df_qs['Country'] == country].head(20)
    df_country = df_country.iloc[::-1]
    fig_container = st.empty() # 创建一个空的占位符，后续更新图表
    # 创建条形图
    fig = px.bar(df_country, 
                x='排名', 
                y='大学名称', 
                orientation='h', 
                color='排名', 
                color_continuous_scale=px.colors.sequential.Oryel[::-1],  # 设置渐变色
                text='排名'  # 在每个柱子上显示学校排名
                )

    # 更新布局以显示标签
    fig.update_traces(texttemplate='%{text}', textposition='outside')
    # 去掉轴标签

    fig.update_yaxes(title=None)
    fig.update_xaxes(title='世界排名')
    fig.update(layout_coloraxis_showscale=False)

    # 用streamlit显示图表，设置宽度为容器宽度
    fig_container.plotly_chart(fig, use_container_width=True)  

with col4:
    st.markdown("""**不同大学的各项指标得分对比**""")
    # 雷达图
    # 选择要展示的学校
    school = df_qs['大学名称'].unique()
    default_schools = ['麻省理工学院','北京大学','清华大学']

    selected_schools = st.multiselect('选择学校', school, default_schools)
    df_school = df_qs.query('大学名称 in @selected_schools')

    # 先把列挑出来，学术声誉，雇主声誉，师生比，每位教员引用率，国际教师占比，国际学生占比，国际研究网络，就业结果，可持续性
    df_school = df_school[['大学名称','学术声誉','雇主声誉','师生比','每位教员引用率','国际教师占比','国际学生占比','国际研究网络','就业结果','可持续性']]
    df_school = df_school.set_index('大学名称')
    radar_chart_container = st.empty()  # 创建一个空的占位符，后续更新图表
    # 以选中的学校为索引，绘制雷达图
    # 雷达图
    def create_radar_chart(df_school):
        categories = df_school.columns.tolist()

        # 为了绘制雷达图，需要将数据转换为合适的格式
        fig = go.Figure()
        school_colors = {
            '北京大学': '#8b0012',  # 北京大学设为红色
            '清华大学': '#660874'  # 清华大学设为紫色
        }
        for school in df_school.index:
            values = df_school.loc[school].tolist()
            values += values[:1]
            # 获取颜色，如果学校有指定颜色则使用指定颜色，否则使用默认颜色
            color = school_colors.get(school, 'blue')  # 默认颜色为蓝色
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories + [categories[0]],
                name=school,
                line=dict(color=color)
            ))

        # 设置图表布局
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]  # 假设得分范围为0到100，调整为你的数据范围
                )
            ),
            showlegend=True,
            title="不同大学的各项指标得分对比"
        )
        
        radar_chart_container.plotly_chart(fig, use_container_width=True)
    create_radar_chart(df_school)

st.markdown('__Data Source:__ _QS Top Universities_')
st.markdown('__Author:__ 李子涵 __Advisor__: 李梅 __Time__:2024.12.27')