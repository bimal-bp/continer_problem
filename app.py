import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os

# Initialize session state for data persistence
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=[
        'customer_name', 
        'container_id', 
        'arrival_date', 
        'delivery_date',
        'days_to_deliver'
    ])

# Function to calculate days between dates
def calculate_days(arrival, delivery):
    if pd.isna(delivery):
        return None
    return (delivery - arrival).days

# Function to save data to CSV
def save_data():
    st.session_state.data.to_csv('container_data.csv', index=False)

# Function to load data from CSV
def load_data():
    if os.path.exists('container_data.csv'):
        st.session_state.data = pd.read_csv('container_data.csv', parse_dates=['arrival_date', 'delivery_date'])

# Load existing data
load_data()

# App title and description
st.title("📦 Container Yard Management System")
st.markdown("""
This app helps optimize container placement based on customer delivery patterns.
Store containers with shorter delivery times in easily accessible locations.
""")

# Sidebar for navigation
menu = st.sidebar.selectbox("Menu", ["Add New Record", "View Customer Stats", "Container Placement Suggestions", "Data Management"])

if menu == "Add New Record":
    st.header("Add New Container Record")
    
    col1, col2 = st.columns(2)
    with col1:
        customer_name = st.text_input("Customer Name")
        container_id = st.text_input("Container ID")
    with col2:
        arrival_date = st.date_input("Arrival Date", datetime.today())
        delivery_date = st.date_input("Delivery Date", datetime.today() + timedelta(days=3))
    
    if st.button("Add Record"):
        if not customer_name or not container_id:
            st.error("Please fill in all fields")
        else:
            days_to_deliver = (delivery_date - arrival_date).days
            new_record = pd.DataFrame([{
                'customer_name': customer_name,
                'container_id': container_id,
                'arrival_date': arrival_date,
                'delivery_date': delivery_date,
                'days_to_deliver': days_to_deliver
            }])
            
            st.session_state.data = pd.concat([st.session_state.data, new_record], ignore_index=True)
            save_data()
            st.success("Record added successfully!")
            
            # Show the updated dataframe
            st.dataframe(st.session_state.data.tail())

elif menu == "View Customer Stats":
    st.header("Customer Delivery Statistics")
    
    if st.session_state.data.empty:
        st.warning("No data available. Please add records first.")
    else:
        # Calculate average delivery days per customer
        customer_stats = st.session_state.data.groupby('customer_name')['days_to_deliver'].agg(
            avg_delivery_days='mean',
            record_count='count'
        ).reset_index().sort_values('avg_delivery_days')
        
        # Display stats
        st.subheader("Average Delivery Days by Customer")
        st.dataframe(customer_stats.style.background_gradient(cmap='YlOrRd', subset=['avg_delivery_days']))
        
        # Plot the data
        fig = px.bar(customer_stats, 
                     x='customer_name', 
                     y='avg_delivery_days',
                     color='avg_delivery_days',
                     title="Average Delivery Days by Customer",
                     labels={'avg_delivery_days': 'Avg. Delivery Days', 'customer_name': 'Customer'},
                     color_continuous_scale='YlOrRd')
        st.plotly_chart(fig)
        
        # Customer selection for detailed view
        selected_customer = st.selectbox("Select Customer for Detailed View", customer_stats['customer_name'])
        
        customer_data = st.session_state.data[st.session_state.data['customer_name'] == selected_customer]
        st.subheader(f"Delivery History for {selected_customer}")
        st.dataframe(customer_data)
        
        # Plot customer's delivery trend
        if len(customer_data) > 1:
            fig2 = px.line(customer_data, 
                          x='arrival_date', 
                          y='days_to_deliver',
                          title=f"Delivery Trend for {selected_customer}",
                          markers=True)
            st.plotly_chart(fig2)

elif menu == "Container Placement Suggestions":
    st.header("Container Placement Recommendations")
    
    if st.session_state.data.empty:
        st.warning("No data available. Please add records first.")
    else:
        # Get current containers (those not yet delivered)
        current_containers = st.session_state.data[st.session_state.data['delivery_date'].isna() | 
                            (st.session_state.data['delivery_date'] > pd.to_datetime(datetime.today()))]
        
        if current_containers.empty:
            st.info("No active containers in the yard currently.")
        else:
            # Merge with customer stats
            customer_stats = st.session_state.data.groupby('customer_name')['days_to_deliver'].mean().reset_index()
            current_containers = current_containers.merge(customer_stats, on='customer_name', how='left')
            current_containers.rename(columns={'days_to_deliver_y': 'customer_avg_delivery'}, inplace=True)
            
            # Categorize containers
            current_containers['placement'] = current_containers['customer_avg_delivery'].apply(
                lambda x: "Lower Level (Easy Access)" if x <= 3 else "Upper Level (Long-term Storage)"
            )
            
            st.subheader("Suggested Placement for Current Containers")
            st.dataframe(current_containers[['container_id', 'customer_name', 'customer_avg_delivery', 'placement']])
            
            # Summary stats
            placement_counts = current_containers['placement'].value_counts()
            st.subheader("Placement Summary")
            col1, col2 = st.columns(2)
            col1.metric("Containers for Lower Level", placement_counts.get("Lower Level (Easy Access)", 0))
            col2.metric("Containers for Upper Level", placement_counts.get("Upper Level (Long-term Storage)", 0))
            
            # Plot placement distribution
            fig = px.pie(placement_counts, 
                         names=placement_counts.index, 
                         values=placement_counts.values,
                         title="Container Placement Distribution")
            st.plotly_chart(fig)

elif menu == "Data Management":
    st.header("Data Management")
    
    if not st.session_state.data.empty:
        st.subheader("Current Data")
        st.dataframe(st.session_state.data)
        
        # Export data
        st.download_button(
            label="Download Data as CSV",
            data=st.session_state.data.to_csv(index=False).encode('utf-8'),
            file_name='container_yard_data.csv',
            mime='text/csv'
        )
        
        # Clear data (with confirmation)
        if st.button("Clear All Data"):
            st.warning("This will permanently delete all data. Are you sure?")
            if st.button("Confirm Delete"):
                st.session_state.data = pd.DataFrame(columns=st.session_state.data.columns)
                save_data()
                st.success("All data has been cleared.")
    else:
        st.info("No data available to manage.")

# Footer
st.sidebar.markdown("---")
st.sidebar.info(
    "Container Yard Management System v1.0\n\n"
    "Optimize your container placement based on customer delivery patterns."
)
