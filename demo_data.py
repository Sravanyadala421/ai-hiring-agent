#!/usr/bin/env python3
"""
Demo data for the hiring agent when API limits are reached.
"""
from models import EvaluationData, Scores, CategoryScore, BonusPoints, Deductions

def get_demo_evaluation():
    """Return a demo evaluation result for testing."""
    
    # Create sample evaluation data
    demo_evaluation = EvaluationData(
        scores=Scores(
            open_source=CategoryScore(
                score=12.0,
                max=35,
                evidence="Candidate has a GitHub profile with several public repositories. However, most projects appear to be personal learning projects rather than contributions to external open source projects. No evidence of participation in major open source programs or significant community contributions."
            ),
            self_projects=CategoryScore(
                score=25.0,
                max=30,
                evidence="Strong portfolio of self-initiated projects demonstrating full-stack capabilities. Projects include a task management system with React frontend and Node.js backend, a weather application with API integration, and a personal portfolio website. Code quality appears good with proper documentation and modern development practices."
            ),
            production=CategoryScore(
                score=15.0,
                max=25,
                evidence="Limited professional experience with one internship at a software company where the candidate worked on bug fixes and feature enhancements. Contributed to a team project for 3 months, gaining experience with production codebases and collaborative development practices."
            ),
            technical_skills=CategoryScore(
                score=8.5,
                max=10,
                evidence="Comprehensive technical skill set including JavaScript, React, Node.js, Python, SQL databases, Git version control, and cloud deployment. Skills are well-demonstrated through projects and backed by relevant coursework and certifications."
            )
        ),
        bonus_points=BonusPoints(
            total=5.0,
            breakdown="+2 points for live project deployments, +2 points for comprehensive documentation, +1 point for active LinkedIn profile with technical content"
        ),
        deductions=Deductions(
            total=2.0,
            reasons="-2 points for limited contribution to open source community beyond personal projects"
        ),
        key_strengths=[
            "Strong full-stack development skills with modern web technologies",
            "Well-documented projects with live deployments showing real-world application",
            "Good understanding of software development best practices and version control",
            "Diverse project portfolio demonstrating problem-solving abilities",
            "Active learning mindset with relevant certifications and continuous skill development"
        ],
        areas_for_improvement=[
            "Increase contributions to open source projects to build community presence",
            "Gain more substantial professional work experience beyond internships",
            "Develop specialization in specific technology domains for deeper expertise"
        ]
    )
    
    return demo_evaluation