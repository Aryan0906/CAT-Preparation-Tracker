import streamlit as st
from datetime import datetime, timedelta
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import save_study_session, save_timer_session

# Define a consistent color palette
COLOR_PALETTE = {
    "VARC": "#4F46E5",      # Indigo
    "DILR": "#06B6D4",      # Cyan
    "Quant": "#10B981",     # Emerald
    "General Preparation": "#F97316",  # Orange
    "Mock Test": "#8B5CF6",  # Purple
    "Other": "#64748B"      # Slate
}

# Define a consistent color sequence for charts
COLOR_SEQUENCE = ["#4F46E5", "#06B6D4", "#10B981", "#F97316", "#8B5CF6", "#64748B"]

def init_db():
    """Initialize database connection"""
    conn = sqlite3.connect('cat_prep.db')
    c = conn.cursor()

    # Ensure study_log table exists
    c.execute('''CREATE TABLE IF NOT EXISTS study_log
                 (date TEXT, topic TEXT, subtopic TEXT, time_spent INTEGER, notes TEXT)''')

    conn.commit()
    return conn

def show_focus_timer():
    """Display a minimal focus timer with analysis section"""
    st.title("Focus Timer")

    # Add custom CSS for better styling
    st.markdown("""
    <style>
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #f0f9ff;
        border-bottom-color: #4F46E5;
    }

    /* Card styling */
    .stat-card {
        background-color: white;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }

    /* Header styling */
    .section-header {
        color: #4F46E5;
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #E2E8F0;
    }
    </style>
    """, unsafe_allow_html=True)

    # Initialize database connection
    conn = init_db()
    c = conn.cursor()

    # Create tabs for Timer and Analysis
    tab1, tab2 = st.tabs(["⏱️ Timer", "📊 Analysis"])

    with tab1:
        # Topic selector for focus sessions
        topic = st.selectbox(
            "What are you working on?",
            ["VARC", "DILR", "Quant", "General Preparation", "Mock Test", "Other"]
        )

        # Embed only the timer part of Pomofocus.io in an iframe with custom CSS
        st.markdown("""
        <style>
        iframe {
            border: none;
            width: 100%;
            height: 500px;
            overflow: hidden;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        </style>

        <div style="margin-bottom: 20px;">
            <iframe src="https://pomofocus.io/" scrolling="no"></iframe>
        </div>
        """, unsafe_allow_html=True)

        # Simple form to record completed sessions
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">Record Completed Session</div>', unsafe_allow_html=True)

        with st.form("record_session"):
            col1, col2 = st.columns([3, 1])

            with col1:
                minutes_spent = st.number_input("Minutes completed", min_value=1, max_value=180, value=25)

            with col2:
                record_button = st.form_submit_button("Save Session")

            if record_button:
                try:
                    # Save to database
                    save_study_session(topic, "", minutes_spent)
                    st.success(f"Saved {minutes_spent} minutes of study on {topic}")
                except Exception as e:
                    st.error(f"Error saving session: {str(e)}")

        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">Study Analysis</div>', unsafe_allow_html=True)

        # Date range selector
        col1, col2 = st.columns(2)
        with col1:
            days = st.slider("Time period (days)", 1, 30, 7)
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days-1)

        # Get study data from database
        c.execute("""
            SELECT date, topic, SUM(time_spent) as total_time
            FROM study_log
            WHERE date BETWEEN ? AND ?
            GROUP BY date, topic
            ORDER BY date
        """, (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))

        data = c.fetchall()

        if data:
            # Convert to DataFrame
            df = pd.DataFrame(data, columns=['date', 'topic', 'minutes'])

            # Total study time
            total_time = df['minutes'].sum()
            total_hours = round(total_time / 60, 1)

            # Create metrics row
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Study Time", f"{total_hours} hours")
            with col2:
                avg_daily = round(total_time / days, 1)
                st.metric("Daily Average", f"{avg_daily} min")
            with col3:
                # Calculate consistency (days with study sessions)
                unique_days = df['date'].nunique()
                consistency = round((unique_days / days) * 100)
                st.metric("Consistency", f"{consistency}%")

            # Topic distribution
            topic_data = df.groupby('topic')['minutes'].sum().reset_index()

            # Create pie chart with custom colors
            fig1 = px.pie(
                topic_data,
                values='minutes',
                names='topic',
                title='Study Time by Topic',
                color='topic',
                color_discrete_map=COLOR_PALETTE
            )
            fig1.update_traces(textposition='inside', textinfo='percent+label')
            fig1.update_layout(
                legend_title_text='Topic',
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                margin=dict(t=50, b=100, l=20, r=20),
                title_font=dict(size=20, color="#333333"),
                title_x=0.5
            )
            st.plotly_chart(fig1, use_container_width=True)

            # Daily progress
            daily_data = df.groupby('date')['minutes'].sum().reset_index()
            daily_data['date'] = pd.to_datetime(daily_data['date'])

            # Create bar chart with gradient color
            fig2 = px.bar(
                daily_data,
                x='date',
                y='minutes',
                title='Daily Study Minutes',
                labels={'minutes': 'Minutes', 'date': 'Date'},
                color_discrete_sequence=[COLOR_SEQUENCE[0]]
            )
            fig2.update_layout(
                xaxis_title="Date",
                yaxis_title="Minutes",
                title_font=dict(size=20, color="#333333"),
                title_x=0.5,
                xaxis=dict(tickangle=-45),
                margin=dict(t=50, b=50, l=20, r=20)
            )
            st.plotly_chart(fig2, use_container_width=True)

            # Topic breakdown table
            st.subheader("Topic Breakdown")
            topic_breakdown = df.groupby('topic')['minutes'].agg(['sum', 'count']).reset_index()
            topic_breakdown.columns = ['Topic', 'Total Minutes', 'Sessions']
            topic_breakdown['Average Minutes/Session'] = round(topic_breakdown['Total Minutes'] / topic_breakdown['Sessions'], 1)
            topic_breakdown['Hours'] = round(topic_breakdown['Total Minutes'] / 60, 1)

            # Display styled dataframe
            st.dataframe(
                topic_breakdown[['Topic', 'Hours', 'Sessions', 'Average Minutes/Session']],
                column_config={
                    "Topic": st.column_config.TextColumn("Topic"),
                    "Hours": st.column_config.NumberColumn("Hours", format="%.1f"),
                    "Sessions": st.column_config.NumberColumn("Sessions"),
                    "Average Minutes/Session": st.column_config.NumberColumn("Avg Min/Session", format="%.1f")
                },
                hide_index=True,
                use_container_width=True
            )

            # Study pattern heatmap
            st.subheader("Study Pattern")

            # Prepare data for heatmap
            pattern_data = df.copy()
            pattern_data['date'] = pd.to_datetime(pattern_data['date'])
            pattern_data['day_of_week'] = pattern_data['date'].dt.day_name()

            # Aggregate by day of week
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            dow_data = pattern_data.groupby('day_of_week')['minutes'].sum().reindex(day_order).reset_index()

            # Create bar chart for day of week pattern
            fig3 = px.bar(
                dow_data,
                x='day_of_week',
                y='minutes',
                title='Study Minutes by Day of Week',
                labels={'minutes': 'Minutes', 'day_of_week': 'Day'},
                color_discrete_sequence=[COLOR_SEQUENCE[2]]
            )
            fig3.update_layout(
                xaxis_title="Day of Week",
                yaxis_title="Total Minutes",
                title_font=dict(size=20, color="#333333"),
                title_x=0.5,
                margin=dict(t=50, b=50, l=20, r=20)
            )
            st.plotly_chart(fig3, use_container_width=True)

        else:
            st.info(f"No study data available for the selected period ({start_date} to {end_date})")

        st.markdown('</div>', unsafe_allow_html=True)

    # Close database connection
    conn.close()
