#!/usr/bin/env python3
"""
Streamlit app with GitHub fetching disabled for faster response.
"""
import streamlit as st
import tempfile
import os

# Temporarily disable GitHub fetching
os.environ['SKIP_GITHUB'] = 'true'

from score import main as score_resume
from demo_data import get_demo_evaluation

st.set_page_config(page_title="AI Hiring Agent - Fast Mode", page_icon="🚀")

st.title("🚀 AI Hiring Agent (Fast Mode)")
st.info("⚡ GitHub data fetching disabled for faster analysis")

uploaded_file = st.file_uploader("Upload Resume PDF", type="pdf")

if uploaded_file:
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 Analyze (No GitHub)", type="primary"):
            with st.spinner("Analyzing resume..."):
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(uploaded_file.getvalue())
                        tmp_path = tmp.name
                    
                    result = score_resume(tmp_path)
                    os.unlink(tmp_path)
                    
                    if result:
                        st.success("✅ Analysis complete!")
                        
                        total = 0
                        if hasattr(result, 'scores'):
                            if hasattr(result.scores, 'open_source'):
                                score = min(result.scores.open_source.score, 35)
                                st.metric("Open Source", f"{score}/35")
                                total += score
                            if hasattr(result.scores, 'self_projects'):
                                score = min(result.scores.self_projects.score, 30)
                                st.metric("Self Projects", f"{score}/30")
                                total += score
                            if hasattr(result.scores, 'production'):
                                score = min(result.scores.production.score, 25)
                                st.metric("Production", f"{score}/25")
                                total += score
                            if hasattr(result.scores, 'technical_skills'):
                                score = min(result.scores.technical_skills.score, 10)
                                st.metric("Technical Skills", f"{score}/10")
                                total += score
                        
                        st.metric("Total Score", f"{total}/100")
                    else:
                        st.error("Analysis failed")
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    st.exception(e)
    
    with col2:
        if st.button("🎭 Demo Mode"):
            result = get_demo_evaluation()
            st.success("✅ Demo data loaded!")
            st.json({"demo": "mode"})
