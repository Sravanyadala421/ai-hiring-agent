#!/usr/bin/env python3
"""
Streamlit web application for the Hiring Agent - Fixed Version.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import sys
import tempfile
from pathlib import Path
import json
from score import main as score_resume
from models import EvaluationData
from demo_data import get_demo_evaluation
import io
import contextlib
import time

# Page configuration
st.set_page_config(
    page_title="AI Hiring Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .score-excellent { color: #28a745; font-weight: bold; }
    .score-good { color: #17a2b8; font-weight: bold; }
    .score-fair { color: #ffc107; font-weight: bold; }
    .score-poor { color: #dc3545; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

def get_score_class(score, max_score):
    """Get CSS class based on score percentage."""
    percentage = (score / max_score) * 100
    if percentage >= 80:
        return "score-excellent"
    elif percentage >= 60:
        return "score-good"
    elif percentage >= 40:
        return "score-fair"
    else:
        return "score-poor"

def create_score_chart(evaluation_data):
    """Create a radar chart for scores."""
    if not evaluation_data or not evaluation_data.scores:
        return None
    
    scores = evaluation_data.scores
    categories = []
    actual_scores = []
    max_scores = []
    
    # Extract scores
    if hasattr(scores, 'open_source') and scores.open_source:
        categories.append('Open Source')
        actual_scores.append(min(scores.open_source.score, 35))
        max_scores.append(35)
    
    if hasattr(scores, 'self_projects') and scores.self_projects:
        categories.append('Self Projects')
        actual_scores.append(min(scores.self_projects.score, 30))
        max_scores.append(30)
    
    if hasattr(scores, 'production') and scores.production:
        categories.append('Production')
        actual_scores.append(min(scores.production.score, 25))
        max_scores.append(25)
    
    if hasattr(scores, 'technical_skills') and scores.technical_skills:
        categories.append('Technical Skills')
        actual_scores.append(min(scores.technical_skills.score, 10))
        max_scores.append(10)
    
    if not categories:
        return None
    
    # Create radar chart
    fig = go.Figure()
    
    # Add actual scores
    fig.add_trace(go.Scatterpolar(
        r=actual_scores,
        theta=categories,
        fill='toself',
        name='Actual Score',
        line_color='rgba(31, 119, 180, 0.8)',
        fillcolor='rgba(31, 119, 180, 0.3)'
    ))
    
    # Add maximum scores
    fig.add_trace(go.Scatterpolar(
        r=max_scores,
        theta=categories,
        fill='toself',
        name='Maximum Possible',
        line_color='rgba(255, 127, 14, 0.8)',
        fillcolor='rgba(255, 127, 14, 0.1)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max(max_scores) if max_scores else 35]
            )),
        showlegend=True,
        title="Resume Score Breakdown"
    )
    
    return fig

def create_comparison_chart(csv_file_path):
    """Create comparison chart from CSV data."""
    if not os.path.exists(csv_file_path):
        return None
    
    try:
        df = pd.read_csv(csv_file_path)
        if df.empty:
            return None
        
        # Check if required columns exist
        if 'name' not in df.columns or 'total_score' not in df.columns:
            # Try alternative column names
            name_col = None
            score_col = None
            
            # Look for name column alternatives
            for col in ['name', 'candidate_name', 'file_name']:
                if col in df.columns:
                    name_col = col
                    break
            
            # Look for score column alternatives  
            for col in ['total_score', 'score', 'overall_score']:
                if col in df.columns:
                    score_col = col
                    break
            
            if not name_col or not score_col:
                return None
        else:
            name_col = 'name'
            score_col = 'total_score'
        
        # Create bar chart comparing candidates
        recent_data = df.tail(10)  # Show last 10 evaluations
        
        fig = px.bar(
            recent_data,
            x=name_col,
            y=score_col,
            title='Recent Candidate Comparisons',
            labels={score_col: 'Total Score', name_col: 'Candidate'},
            color=score_col,
            color_continuous_scale='viridis'
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            height=400
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creating comparison chart: {e}")
        return None

def display_evaluation_results(evaluation_result, console_output="", is_demo=False):
    """Display evaluation results."""
    
    # Calculate total score
    total_score = 0
    max_total = 100
    
    if hasattr(evaluation_result, 'scores') and evaluation_result.scores:
        if hasattr(evaluation_result.scores, 'open_source') and evaluation_result.scores.open_source:
            total_score += min(evaluation_result.scores.open_source.score, 35)
        if hasattr(evaluation_result.scores, 'self_projects') and evaluation_result.scores.self_projects:
            total_score += min(evaluation_result.scores.self_projects.score, 30)
        if hasattr(evaluation_result.scores, 'production') and evaluation_result.scores.production:
            total_score += min(evaluation_result.scores.production.score, 25)
        if hasattr(evaluation_result.scores, 'technical_skills') and evaluation_result.scores.technical_skills:
            total_score += min(evaluation_result.scores.technical_skills.score, 10)
    
    if hasattr(evaluation_result, 'bonus_points') and evaluation_result.bonus_points:
        total_score += evaluation_result.bonus_points.total
    
    if hasattr(evaluation_result, 'deductions') and evaluation_result.deductions:
        total_score -= evaluation_result.deductions.total
    
    # Display results
    st.header("📊 Analysis Results")
    
    # Overall score
    score_class = get_score_class(total_score, max_total)
    st.markdown(f'<div class="metric-card"><h2>Overall Score: <span class="{score_class}">{total_score:.1f}/{max_total}</span></h2></div>', unsafe_allow_html=True)
    
    # Score breakdown
    st.subheader("📈 Detailed Scores")
    
    score_cols = st.columns(4)
    
    if hasattr(evaluation_result, 'scores') and evaluation_result.scores:
        with score_cols[0]:
            if hasattr(evaluation_result.scores, 'open_source') and evaluation_result.scores.open_source:
                os_score = evaluation_result.scores.open_source
                capped_score = min(os_score.score, 35)
                st.metric("🌐 Open Source", f"{capped_score}/35")
        
        with score_cols[1]:
            if hasattr(evaluation_result.scores, 'self_projects') and evaluation_result.scores.self_projects:
                sp_score = evaluation_result.scores.self_projects
                capped_score = min(sp_score.score, 30)
                st.metric("🚀 Self Projects", f"{capped_score}/30")
        
        with score_cols[2]:
            if hasattr(evaluation_result.scores, 'production') and evaluation_result.scores.production:
                prod_score = evaluation_result.scores.production
                capped_score = min(prod_score.score, 25)
                st.metric("🏢 Production", f"{capped_score}/25")
        
        with score_cols[3]:
            if hasattr(evaluation_result.scores, 'technical_skills') and evaluation_result.scores.technical_skills:
                tech_score = evaluation_result.scores.technical_skills
                capped_score = min(tech_score.score, 10)
                st.metric("💻 Tech Skills", f"{capped_score}/10")
    
    # Bonus and deductions
    bonus_deduct_cols = st.columns(2)
    with bonus_deduct_cols[0]:
        if hasattr(evaluation_result, 'bonus_points') and evaluation_result.bonus_points:
            st.success(f"⭐ Bonus Points: +{evaluation_result.bonus_points.total}")
    
    with bonus_deduct_cols[1]:
        if hasattr(evaluation_result, 'deductions') and evaluation_result.deductions and evaluation_result.deductions.total > 0:
            st.warning(f"⚠️ Deductions: -{evaluation_result.deductions.total}")
    
    # Radar chart
    chart = create_score_chart(evaluation_result)
    if chart:
        st.plotly_chart(chart, use_container_width=True)
    
    # Detailed feedback
    feedback_cols = st.columns(2)
    
    with feedback_cols[0]:
        st.subheader("✅ Key Strengths")
        if hasattr(evaluation_result, 'key_strengths') and evaluation_result.key_strengths:
            for i, strength in enumerate(evaluation_result.key_strengths, 1):
                st.write(f"{i}. {strength}")
    
    with feedback_cols[1]:
        st.subheader("🔧 Areas for Improvement")
        if hasattr(evaluation_result, 'areas_for_improvement') and evaluation_result.areas_for_improvement:
            for i, area in enumerate(evaluation_result.areas_for_improvement, 1):
                st.write(f"{i}. {area}")
    
    # Evidence details
    with st.expander("📋 Detailed Evidence"):
        if hasattr(evaluation_result, 'scores') and evaluation_result.scores:
            if hasattr(evaluation_result.scores, 'open_source') and evaluation_result.scores.open_source:
                st.write("**Open Source:**", evaluation_result.scores.open_source.evidence)
            if hasattr(evaluation_result.scores, 'self_projects') and evaluation_result.scores.self_projects:
                st.write("**Self Projects:**", evaluation_result.scores.self_projects.evidence)
            if hasattr(evaluation_result.scores, 'production') and evaluation_result.scores.production:
                st.write("**Production:**", evaluation_result.scores.production.evidence)
            if hasattr(evaluation_result.scores, 'technical_skills') and evaluation_result.scores.technical_skills:
                st.write("**Technical Skills:**", evaluation_result.scores.technical_skills.evidence)
    
    # Show console output in expander (only if not demo)
    if not is_demo and console_output:
        with st.expander("🖥️ Console Output"):
            st.text(console_output)

def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown('<div class="main-header">🤖 AI Hiring Agent</div>', unsafe_allow_html=True)
    st.markdown("### Upload a resume PDF to get an AI-powered evaluation with detailed scoring and feedback")
    
    # Sidebar configuration
    st.sidebar.header("⚙️ Configuration")
    
    # Check environment configuration
    # Try to read from Streamlit secrets first, then environment variables
    try:
        llm_provider = st.secrets.get('LLM_PROVIDER', os.getenv('LLM_PROVIDER', 'ollama'))
        default_model = st.secrets.get('DEFAULT_MODEL', os.getenv('DEFAULT_MODEL', 'gemma3:4b'))
        api_key = st.secrets.get('GEMINI_API_KEY', os.getenv('GEMINI_API_KEY', ''))
    except (FileNotFoundError, AttributeError):
        llm_provider = os.getenv('LLM_PROVIDER', 'ollama')
        default_model = os.getenv('DEFAULT_MODEL', 'gemma3:4b')
        api_key = os.getenv('GEMINI_API_KEY', '')
    
    st.sidebar.info(f"**LLM Provider:** {llm_provider}\n**Model:** {default_model}")
    
    if llm_provider == 'gemini':
        api_key = os.getenv('GEMINI_API_KEY', '')
        if not api_key or api_key == 'your_gemini_api_key_here':
            st.sidebar.error("⚠️ Gemini API key not configured!")
        else:
            st.sidebar.success("✅ Gemini API configured")
    else:
        st.sidebar.warning("⚠️ Using Ollama - ensure it's running locally")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📄 Upload Resume")
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type="pdf",
            help="Upload a resume in PDF format for AI analysis"
        )
        
        if uploaded_file is not None:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            st.success(f"✅ Uploaded: {uploaded_file.name}")
            
            # Add analyze buttons
            analyze_col, demo_col = st.columns([3, 1])
            
            with analyze_col:
                analyze_clicked = st.button("🚀 Analyze Resume", type="primary")
            
            with demo_col:
                demo_clicked = st.button("🎭 Demo Mode", help="See sample results when API limits are reached")
            
            if analyze_clicked or demo_clicked:
                # Add progress bar and status
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                evaluation_result = None
                console_output = ""
                
                if demo_clicked:
                    status_text.text("🎭 Loading demo results...")
                    progress_bar.progress(50)
                    time.sleep(1)  # Simulate processing
                    evaluation_result = get_demo_evaluation()
                    console_output = "Demo mode: Using sample evaluation data"
                    progress_bar.progress(100)
                    status_text.text("✅ Demo results loaded!")
                    st.info("🎭 **Demo Mode**: This is sample evaluation data. Upload your resume and use 'Analyze Resume' for real results.")
                    
                    # Display demo results
                    display_evaluation_results(evaluation_result, console_output, is_demo=True)
                    
                else:
                    # Real analysis
                    with st.spinner("🔄 Starting analysis..."):
                        progress_bar.progress(10)
                        time.sleep(0.5)
                    
                    try:
                        with st.spinner("📄 Extracting text from PDF..."):
                            progress_bar.progress(30)
                            time.sleep(0.5)
                        
                        # Capture the output from score_resume
                        old_stdout = sys.stdout
                        captured_output = io.StringIO()
                        sys.stdout = captured_output
                        
                        with st.spinner("🤖 AI is analyzing the resume... This usually takes 30-60 seconds"):
                            status_text.text("🤖 Analyzing with Gemini AI...")
                            progress_bar.progress(50)
                            
                            try:
                                evaluation_result = score_resume(tmp_file_path)
                                progress_bar.progress(90)
                            except Exception as analysis_error:
                                progress_bar.progress(100)
                                status_text.text("❌ Analysis failed")
                                st.error(f"❌ Analysis failed: {str(analysis_error)}")
                                if "timeout" in str(analysis_error).lower():
                                    st.error("⏱️ API request timed out. The Gemini API took too long to respond (>60s).")
                                    st.info("💡 Try again - sometimes the API is slow. Or use 'Demo Mode' to see sample results.")
                                elif "quota" in str(analysis_error).lower() or "rate limit" in str(analysis_error).lower():
                                    st.error("🚫 API quota exceeded. Please try again later or check your API limits.")
                                    st.info("💡 Tip: Try 'Demo Mode' to see how the analysis results look, or wait for API limits to reset.")
                                evaluation_result = None
                        
                        # Restore stdout
                        sys.stdout = old_stdout
                        console_output = captured_output.getvalue()
                        
                        progress_bar.progress(100)
                        status_text.text("✅ Analysis completed!")
                        
                        if evaluation_result:
                            display_evaluation_results(evaluation_result, console_output, is_demo=False)
                        else:
                            st.error("❌ Analysis failed. Please check the console output or try Demo Mode.")
                    
                    except Exception as e:
                        progress_bar.progress(100)
                        status_text.text("❌ Error occurred")
                        st.error(f"❌ Error during analysis: {str(e)}")
                        st.exception(e)
                    
                    finally:
                        # Clean up temporary file
                        try:
                            os.unlink(tmp_file_path)
                        except:
                            pass
    
    with col2:
        st.header("📊 Statistics")
        
        # Check if CSV exists and show stats
        csv_path = "resume_evaluations.csv"
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                if not df.empty:
                    st.metric("Total Evaluations", len(df))
                    
                    # Find the score column
                    score_column = None
                    for col in ['total_score', 'score', 'overall_score']:
                        if col in df.columns:
                            score_column = col
                            break
                    
                    if score_column:
                        avg_score = df[score_column].mean()
                        st.metric("Average Score", f"{avg_score:.1f}")
                        
                        # Show recent evaluations - handle missing columns gracefully
                        display_columns = []
                        name_column = None
                        
                        # Find name column
                        for col in ['name', 'candidate_name', 'file_name']:
                            if col in df.columns:
                                name_column = col
                                break
                        
                        if name_column:
                            display_columns = [name_column, score_column]
                            
                            st.subheader("Recent Evaluations")
                            recent = df.tail(5)[display_columns].copy()
                            # Rename columns for display
                            column_mapping = {
                                name_column: 'Candidate',
                                score_column: 'Score'
                            }
                            recent.columns = [column_mapping.get(col, col) for col in recent.columns]
                            st.dataframe(recent, use_container_width=True)
                    else:
                        st.info("Score data not available in expected format")
                else:
                    st.info("No evaluations yet")
            except Exception as e:
                st.warning(f"Could not load statistics: {str(e)[:100]}...")
                st.info("Upload and analyze a resume to start building statistics")
        else:
            st.info("No evaluation history found")
        
        # Show comparison chart if data exists
        comparison_chart = create_comparison_chart(csv_path)
        if comparison_chart:
            st.plotly_chart(comparison_chart, use_container_width=True)

if __name__ == "__main__":
    main()