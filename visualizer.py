import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from config import NORMAL_RANGES, REPORT_TYPES

class Visualizer:
    def __init__(self):
        pass
    
    def create_trend_chart(self, df, param, patient_name=None):
        """Create trend chart for a single parameter"""
        if df.empty or param not in df.columns:
            return None
        
        # Filter data for the specific parameter
        trend_data = df[['Date', 'Patient Name', param]].copy()
        trend_data['Date'] = pd.to_datetime(trend_data['Date'], errors='coerce')
        trend_data = trend_data.dropna(subset=['Date', param])
        
        if trend_data.empty:
            return None
        
        # Filter by patient if specified
        if patient_name:
            trend_data = trend_data[trend_data['Patient Name'] == patient_name]
        
        if trend_data.empty:
            return None
        
        # Sort by date
        trend_data = trend_data.sort_values('Date')
        
        # Create figure
        fig = go.Figure()
        
        # Add trace for the parameter
        fig.add_trace(go.Scatter(
            x=trend_data['Date'],
            y=trend_data[param],
            mode='lines+markers',
            name=param,
            line=dict(color='blue', width=2),
            marker=dict(size=8)
        ))
        
        # Add normal range if available
        if param in NORMAL_RANGES:
            normal_range = NORMAL_RANGES[param]
            min_val = normal_range.get('min')
            max_val = normal_range.get('max')
            
            if min_val is not None and max_val is not None:
                # Add shaded area for normal range
                fig.add_trace(go.Scatter(
                    x=[trend_data['Date'].min(), trend_data['Date'].max()],
                    y=[min_val, min_val],
                    mode='lines',
                    line=dict(color='green', width=0),
                    showlegend=False,
                    hoverinfo='skip'
                ))
                
                fig.add_trace(go.Scatter(
                    x=[trend_data['Date'].min(), trend_data['Date'].max()],
                    y=[max_val, max_val],
                    mode='lines',
                    fill='tonexty',
                    fillcolor='rgba(0, 255, 0, 0.2)',
                    line=dict(color='green', width=0),
                    name='Normal Range',
                    hoverinfo='skip'
                ))
        
        # Update layout
        unit = NORMAL_RANGES.get(param, {}).get('unit', '')
        fig.update_layout(
            title=f"{param} Trend Over Time",
            xaxis_title="Date",
            yaxis_title=f"{param} ({unit})" if unit else param,
            hovermode='x unified',
            template='plotly_white',
            showlegend=True
        )
        
        return fig
    
    def create_multi_test_trend_chart(self, df, param, report_type_val=None):
        """Create trend chart for a parameter across multiple patients/tests"""
        if df.empty or param not in df.columns:
            return None
        
        # Extract unique patients
        patients = df['Patient Name'].dropna().unique().tolist()
        
        # Filter and prepare data
        chart_data = df[['Date', 'Patient Name', 'Report Type', param]].copy()
        chart_data['Date'] = pd.to_datetime(chart_data['Date'], errors='coerce')
        chart_data = chart_data.dropna(subset=['Date', param])
        
        if chart_data.empty:
            return None
        
        # Filter by report type if specified
        if report_type_val:
            chart_data = chart_data[chart_data['Report Type'] == report_type_val]
        
        if chart_data.empty:
            return None
        
        # Sort by date
        chart_data = chart_data.sort_values('Date')
        
        # Create figure
        fig = go.Figure()
        
        # Get unique patients in the filtered data
        filtered_patients = chart_data['Patient Name'].unique()
        
        # Color palette
        colors = px.colors.qualitative.Set3
        
        # Add trace for each patient
        for idx, patient in enumerate(filtered_patients):
            patient_data = chart_data[chart_data['Patient Name'] == patient]
            
            if len(patient_data) > 0:
                color_idx = idx % len(colors)
                
                fig.add_trace(go.Scatter(
                    x=patient_data['Date'],
                    y=patient_data[param],
                    mode='lines+markers',
                    name=patient,
                    line=dict(color=colors[color_idx], width=2),
                    marker=dict(size=8),
                    hovertemplate=(
                        f"<b>{patient}</b><br>" +
                        "Date: %{x|%Y-%m-%d}<br>" +
                        f"{param}: %{{y}}<br>" +
                        "<extra></extra>"
                    )
                ))
        
        # Add normal range if available
        if param in NORMAL_RANGES:
            normal_range = NORMAL_RANGES[param]
            min_val = normal_range.get('min')
            max_val = normal_range.get('max')
            
            if min_val is not None and max_val is not None:
                # Add shaded area for normal range
                fig.add_trace(go.Scatter(
                    x=[chart_data['Date'].min(), chart_data['Date'].max()],
                    y=[min_val, min_val],
                    mode='lines',
                    line=dict(color='green', width=0),
                    showlegend=False,
                    hoverinfo='skip'
                ))
                
                fig.add_trace(go.Scatter(
                    x=[chart_data['Date'].min(), chart_data['Date'].max()],
                    y=[max_val, max_val],
                    mode='lines',
                    fill='tonexty',
                    fillcolor='rgba(0, 255, 0, 0.2)',
                    line=dict(color='green', width=0),
                    name='Normal Range',
                    hoverinfo='skip'
                ))
        
        # Update layout
        unit = NORMAL_RANGES.get(param, {}).get('unit', '')
        title = f"{param} Trend"
        if report_type_val:
            title += f" - {report_type_val}"
        
        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title=f"{param} ({unit})" if unit else param,
            hovermode='x unified',
            template='plotly_white',
            showlegend=True if len(filtered_patients) > 1 else False,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
        
        return fig
    
    def create_comparison_chart(self, df, patient_name):
        """Create comparison chart for a patient's latest report"""
        if df.empty:
            return None
        
        # Get latest report for the patient
        patient_data = df[df['Patient Name'] == patient_name].copy()
        if patient_data.empty:
            return None
        
        latest_report = patient_data.iloc[-1]
        
        # Get numeric parameters from the report
        numeric_params = []
        param_values = []
        normal_mins = []
        normal_maxs = []
        
        for param, value in latest_report.items():
            if param in NORMAL_RANGES and pd.notna(value):
                try:
                    # Try to convert to float
                    num_value = float(value)
                    numeric_params.append(param)
                    param_values.append(num_value)
                    
                    # Get normal range
                    normal_range = NORMAL_RANGES[param]
                    normal_mins.append(normal_range.get('min', np.nan))
                    normal_maxs.append(normal_range.get('max', np.nan))
                except (ValueError, TypeError):
                    continue
        
        if not numeric_params:
            return None
        
        # Create figure
        fig = go.Figure()
        
        # Add bars for parameter values
        fig.add_trace(go.Bar(
            x=numeric_params,
            y=param_values,
            name='Current Value',
            marker_color='lightblue',
            text=param_values,
            textposition='auto',
            texttemplate='%{text:.2f}'
        ))
        
        # Add normal range markers
        for i, (param, min_val, max_val) in enumerate(zip(numeric_params, normal_mins, normal_maxs)):
            if pd.notna(min_val) and pd.notna(max_val):
                # Add a line for normal range
                fig.add_shape(
                    type="rect",
                    xref="x",
                    yref="y",
                    x0=i-0.4,
                    x1=i+0.4,
                    y0=min_val,
                    y1=max_val,
                    fillcolor="green",
                    opacity=0.2,
                    line_width=0,
                    layer="below"
                )
        
        # Update layout
        fig.update_layout(
            title=f"Parameter Comparison - {patient_name}",
            xaxis_title="Parameters",
            yaxis_title="Value",
            template='plotly_white',
            showlegend=True,
            xaxis_tickangle=-45
        )
        
        return fig
    
    def create_report_type_distribution(self, df):
        """Create distribution chart of report types"""
        if df.empty or 'Report Type' not in df.columns:
            return None
        
        report_counts = df['Report Type'].value_counts()
        
        fig = go.Figure(data=[
            go.Pie(
                labels=report_counts.index,
                values=report_counts.values,
                hole=0.3,
                textinfo='label+percent',
                hoverinfo='label+value+percent'
            )
        ])
        
        fig.update_layout(
            title="Report Type Distribution",
            showlegend=True
        )
        
        return fig
    
    def create_patient_summary_chart(self, df):
        """Create summary chart showing reports per patient"""
        if df.empty or 'Patient Name' not in df.columns:
            return None
        
        patient_counts = df['Patient Name'].value_counts().reset_index()
        patient_counts.columns = ['Patient Name', 'Report Count']
        
        fig = go.Figure(data=[
            go.Bar(
                x=patient_counts['Patient Name'],
                y=patient_counts['Report Count'],
                marker_color='skyblue',
                text=patient_counts['Report Count'],
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title="Reports per Patient",
            xaxis_title="Patient Name",
            yaxis_title="Number of Reports",
            xaxis_tickangle=-45,
            template='plotly_white'
        )
        
        return fig