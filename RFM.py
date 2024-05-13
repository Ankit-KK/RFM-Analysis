apt-get requirements.txt

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import plotly.io as pio

# Set default plotly template
pio.templates.default = "plotly_white"

# Load data
# Replace this with your data loading code
data = pd.read_csv("rfm_data.csv")

# Convert 'PurchaseDate' to datetime
data['PurchaseDate'] = pd.to_datetime(data['PurchaseDate'])

# Calculate Recency
data['Recency'] = (pd.to_datetime('now') - data['PurchaseDate']).dt.days

# Calculate Frequency
frequency_data = data.groupby('CustomerID')['OrderID'].count().reset_index()
frequency_data.rename(columns={'OrderID': 'Frequency'}, inplace=True)
data = data.merge(frequency_data, on='CustomerID', how='left')

# Calculate Monetary Value
monetary_data = data.groupby('CustomerID')['TransactionAmount'].sum().reset_index()
monetary_data.rename(columns={'TransactionAmount': 'MonetaryValue'}, inplace=True)
data = data.merge(monetary_data, on='CustomerID', how='left')

# Define scoring criteria for each RFM value
recency_scores = [5, 4, 3, 2, 1]  # Higher score for lower recency (more recent)
frequency_scores = [1, 2, 3, 4, 5]  # Higher score for higher frequency
monetary_scores = [1, 2, 3, 4, 5]  # Higher score for higher monetary value

# Calculate RFM Scores
data['RecencyScore'] = pd.cut(data['Recency'], bins=5, labels=recency_scores)
data['FrequencyScore'] = pd.cut(data['Frequency'], bins=5, labels=frequency_scores)
data['MonetaryScore'] = pd.cut(data['MonetaryValue'], bins=5, labels=monetary_scores)

# Convert RFM scores to numeric type
data['RecencyScore'] = data['RecencyScore'].astype(int)
data['FrequencyScore'] = data['FrequencyScore'].astype(int)
data['MonetaryScore'] = data['MonetaryScore'].astype(int)

# Calculate RFM score by combining the individual scores
data['RFM_Score'] = data['RecencyScore'] + data['FrequencyScore'] + data['MonetaryScore']

# Create RFM segments based on the RFM score
segment_labels = ['Low-Value', 'Mid-Value', 'High-Value']
data['Value Segment'] = pd.qcut(data["RFM_Score"], q=3, labels=segment_labels)

# RFM Segment Distribution
segment_counts = data['Value Segment'].value_counts().reset_index()
segment_counts.columns = ['Value Segment', 'Count']

# Choose a color palette
pastel_colors = px.colors.qualitative.Pastel

# Create the bar chart
fig_segment_dist = px.bar(segment_counts, x='Value Segment', y='Count',
                          color='Value Segment', color_discrete_sequence=pastel_colors,
                          title='RFM Value Segment Distribution')

# Update the layout
fig_segment_dist.update_layout(
    xaxis_title='RFM Value Segment',
    yaxis_title='Count',
    showlegend=False
)

# Create a new column for RFM Customer Segments
data['RFM Customer Segments'] = ''

# Assign RFM segments based on the RFM score
data.loc[data['RFM_Score'] >= 9, 'RFM Customer Segments'] = 'Champions'
data.loc[(data['RFM_Score'] >= 6) & (data['RFM_Score'] < 9), 'RFM Customer Segments'] = 'Potential Loyalists'
data.loc[(data['RFM_Score'] >= 5) & (data['RFM_Score'] < 6), 'RFM Customer Segments'] = 'At Risk Customers'
data.loc[(data['RFM_Score'] >= 4) & (data['RFM_Score'] < 5), 'RFM Customer Segments'] = "Can't Lose"
data.loc[(data['RFM_Score'] >= 3) & (data['RFM_Score'] < 4), 'RFM Customer Segments'] = "Lost"

# Group by 'Value Segment' and 'RFM Customer Segments' and count the occurrences
segment_product_counts = data.groupby(['Value Segment', 'RFM Customer Segments']).size().reset_index(name='Count')

# Sort the data by 'Count' in descending order
segment_product_counts = segment_product_counts.sort_values('Count', ascending=False)

# Create the treemap visualization
fig_treemap_segment_product = px.treemap(segment_product_counts,
                                         path=['Value Segment', 'RFM Customer Segments'],
                                         values='Count',
                                         color='Value Segment', color_discrete_sequence=px.colors.qualitative.Pastel,
                                         title='RFM Customer Segments by Value')

# Update the layout
fig_treemap_segment_product.update_layout(
    margin=dict(t=50, l=10, r=10, b=10),
    uniformtext=dict(minsize=10, mode='hide'),
)

# Filter the data to include only the customers in the Champions segment
champions_segment = data[data['RFM Customer Segments'] == 'Champions']

# Create a box plot for each RFM value
fig_champions_boxplot = go.Figure()
fig_champions_boxplot.add_trace(go.Box(y=champions_segment['RecencyScore'], name='Recency'))
fig_champions_boxplot.add_trace(go.Box(y=champions_segment['FrequencyScore'], name='Frequency'))
fig_champions_boxplot.add_trace(go.Box(y=champions_segment['MonetaryScore'], name='Monetary'))

# Update layout and add title
fig_champions_boxplot.update_layout(
    title='Distribution of RFM Values within Champions Segment',
    yaxis_title='RFM Value',
    showlegend=True
)

# Calculate the correlation matrix
correlation_matrix = champions_segment[['RecencyScore', 'FrequencyScore', 'MonetaryScore']].corr()

# Create a heatmap to visualize the correlation matrix
fig_champions_heatmap = go.Figure(data=go.Heatmap(
    z=correlation_matrix.values,
    x=correlation_matrix.columns,
    y=correlation_matrix.columns,
    colorscale='RdBu',
    colorbar=dict(title='Correlation')
))

# Update layout and add title
fig_champions_heatmap.update_layout(
    title='Correlation Matrix of RFM Values within Champions Segment'
)

# Calculate the count of customers in each RFM segment
segment_counts_comparison = data['RFM Customer Segments'].value_counts()

# Create a bar chart to compare segment counts
fig_comparison_bar = go.Figure(data=[go.Bar(x=segment_counts_comparison.index, y=segment_counts_comparison.values,
                                            marker=dict(color=pastel_colors))])

# Set the color of the Champions segment as a different color
champions_color = 'rgb(158, 202, 225)'
fig_comparison_bar.update_traces(marker_color=[champions_color if segment == 'Champions' else pastel_colors[i]
                                               for i, segment in enumerate(segment_counts_comparison.index)],
                                 marker_line_color='rgb(8, 48, 107)',
                                 marker_line_width=1.5, opacity=0.6)

# Update the layout
fig_comparison_bar.update_layout(title='Comparison of RFM Segments',
                                 xaxis_title='RFM Segments',
                                 yaxis_title='Number of Customers',
                                 showlegend=False)

# Calculate the average Recency, Frequency, and Monetary scores for each segment
segment_scores = data.groupby('RFM Customer Segments')[['RecencyScore', 'FrequencyScore', 'MonetaryScore']].mean().reset_index()

# Create a grouped bar chart to compare segment scores
fig_scores_bar = go.Figure()

# Add bars for Recency score
fig_scores_bar.add_trace(go.Bar(
    x=segment_scores['RFM Customer Segments'],
    y=segment_scores['RecencyScore'],
    name='Recency Score',
    marker_color='rgb(158,202,225)'
))

# Add bars for Frequency score
fig_scores_bar.add_trace(go.Bar(
    x=segment_scores['RFM Customer Segments'],
    y=segment_scores['FrequencyScore'],
    name='Frequency Score',
    marker_color='rgb(94,158,217)'
))

# Add bars for Monetary score
fig_scores_bar.add_trace(go.Bar(
    x=segment_scores['RFM Customer Segments'],
    y=segment_scores['MonetaryScore'],
    name='Monetary Score',
    marker_color='rgb(32,102,148)'
))

# Update the layout
fig_scores_bar.update_layout(
    title='Comparison of RFM Segments based on Recency, Frequency, and Monetary Scores',
    xaxis_title='RFM Segments',
    yaxis_title='Score',
    barmode='group',
    showlegend=True
)

# Streamlit App
# Set page title and favicon
st.set_page_config(page_title="RFM Analysis Dashboard", page_icon="📊")

# Sidebar
st.sidebar.title("RFM Analysis Dashboard")
selected_chart_type = st.sidebar.selectbox(
    "Select Chart:",
    ['RFM Value Segment Distribution', 'Distribution of RFM Values within Customer Segment',
     'Correlation Matrix of RFM Values within Champions Segment', 'Comparison of RFM Segments',
     'Comparison of RFM Segments based on Scores']
)

# Main content
st.title("RFM Analysis Dashboard")
st.write("Analyze customer segments based on RFM scores.")

# Render selected chart
if selected_chart_type == 'RFM Value Segment Distribution':
    st.plotly_chart(fig_segment_dist)
elif selected_chart_type == 'Distribution of RFM Values within Customer Segment':
    st.plotly_chart(fig_treemap_segment_product)
elif selected_chart_type == 'Correlation Matrix of RFM Values within Champions Segment':
    st.plotly_chart(fig_champions_heatmap)
elif selected_chart_type == 'Comparison of RFM Segments':
    st.plotly_chart(fig_comparison_bar)
elif selected_chart_type == 'Comparison of RFM Segments based on Scores':
    st.plotly_chart(fig_scores_bar)
