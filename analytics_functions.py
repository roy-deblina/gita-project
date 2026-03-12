#!/usr/bin/env python3
"""
Analytics Module for Gita RAG Streamlit App
PRODUCTION-READY: Uses Supabase (cloud PostgreSQL) for persistent data storage
FALLBACK: Uses SQLite locally if Supabase is not configured
"""

import os
import sqlite3
from pathlib import Path
from datetime import datetime
import streamlit as st

# Try to import Supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


def init_analytics_db(db_path):
    """
    Initialize analytics database.
    In production: Uses Supabase (no init needed, tables auto-created)
    Locally: Falls back to SQLite
    """
    if SUPABASE_AVAILABLE and _get_supabase_client():
        # Supabase handles schema automatically
        return
    
    # Fallback to SQLite
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            rating INTEGER CHECK(rating >= 1 AND rating <= 5),
            comment TEXT,
            email TEXT,
            sentiment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS page_visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_agent TEXT,
            session_id TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS query_clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            click_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            verses_returned INTEGER,
            confidence REAL,
            latency_ms REAL,
            session_id TEXT
        )
    ''')
    
    conn.commit()
    conn.close()


def _get_supabase_client() -> Client | None:
    """Get Supabase client from secrets or env vars."""
    try:
        supabase_url = None
        supabase_key = None
        
        # Try Streamlit secrets first
        try:
            supabase_url = st.secrets.get("SUPABASE_URL")
            supabase_key = st.secrets.get("SUPABASE_KEY")
        except:
            pass
        
        # Fall back to environment variables
        if not supabase_url:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
        
        if supabase_url and supabase_key:
            return create_client(supabase_url, supabase_key)
    except Exception as e:
        st.warning(f"⚠️ Supabase not configured. Using local SQLite instead. Error: {str(e)[:100]}")
    
    return None


class AnalyticsManager:
    """
    Production-grade analytics manager.
    Automatically uses Supabase if available, falls back to SQLite.
    """
    
    def __init__(self, db_path="data/analytics.db"):
        self.db_path = db_path
        self.supabase = _get_supabase_client()
        self.use_supabase = self.supabase is not None
        
        if not self.use_supabase:
            init_analytics_db(self.db_path)
    
    def record_visit(self, session_id, user_agent=None):
        """Record a page visit."""
        try:
            if self.use_supabase:
                self.supabase.table("page_visits").insert({
                    "session_id": session_id,
                    "user_agent": user_agent,
                    "visit_time": datetime.now().isoformat()
                }).execute()
            else:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO page_visits (user_agent, session_id) VALUES (?, ?)',
                    (user_agent, session_id)
                )
                conn.commit()
                conn.close()
        except Exception as e:
            print(f"Analytics error recording visit: {e}")
    
    def record_query_click(self, query, session_id, verses_returned=0, 
                          confidence=0.0, latency_ms=0.0):
        """Record a query submission (click tracking)."""
        try:
            if self.use_supabase:
                self.supabase.table("query_clicks").insert({
                    "query": query,
                    "session_id": session_id,
                    "verses_returned": verses_returned,
                    "confidence": confidence,
                    "latency_ms": latency_ms,
                    "click_time": datetime.now().isoformat()
                }).execute()
            else:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO query_clicks 
                    (query, session_id, verses_returned, confidence, latency_ms)
                    VALUES (?, ?, ?, ?, ?)
                ''', (query, session_id, verses_returned, confidence, latency_ms))
                conn.commit()
                conn.close()
        except Exception as e:
            print(f"Analytics error recording query: {e}")
    
    def save_review(self, query, rating, comment, email, sentiment):
        """Save a user review."""
        try:
            if self.use_supabase:
                self.supabase.table("reviews").insert({
                    "query": query,
                    "rating": rating,
                    "comment": comment,
                    "email": email,
                    "sentiment": sentiment,
                    "created_at": datetime.now().isoformat()
                }).execute()
            else:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO reviews (query, rating, comment, email, sentiment)
                    VALUES (?, ?, ?, ?, ?)
                ''', (query, rating, comment, email, sentiment))
                conn.commit()
                conn.close()
        except Exception as e:
            print(f"Analytics error saving review: {e}")
    
    def get_reviews(self, limit=10):
        """Get recent reviews."""
        try:
            if self.use_supabase:
                response = self.supabase.table("reviews").select("query, rating, comment, email, created_at").order("created_at", desc=True).limit(limit).execute()
                reviews = [(r['query'], r['rating'], r['comment'], r['email'], r['created_at']) for r in response.data]
                return reviews
        except Exception as e:
            print(f"Supabase read error: {e}")
        
        # Fallback to SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT query, rating, comment, email, created_at FROM reviews
            ORDER BY created_at DESC LIMIT ?
        ''', (limit,))
        reviews = cursor.fetchall()
        conn.close()
        return reviews
    
    def get_analytics_summary(self):
        """Get analytics metrics for today."""
        try:
            if self.use_supabase:
                today = datetime.now().strftime("%Y-%m-%d")
                
                # Get visits today
                visits = self.supabase.table("page_visits").select("COUNT").eq("visit_time::date", today).execute()
                visits_today = len(visits.data) if visits.data else 0
                
                # Get queries today
                queries = self.supabase.table("query_clicks").select("COUNT").eq("click_time::date", today).execute()
                queries_today = len(queries.data) if queries.data else 0
                
                # Get average rating
                all_reviews = self.supabase.table("reviews").select("rating").execute()
                ratings = [r['rating'] for r in all_reviews.data if r['rating']]
                avg_rating = sum(ratings) / len(ratings) if ratings else 0
                
                # Get most popular query
                all_clicks = self.supabase.table("query_clicks").select("query").execute()
                query_counts = {}
                for click in all_clicks.data:
                    q = click['query']
                    query_counts[q] = query_counts.get(q, 0) + 1
                most_popular = max(query_counts, key=query_counts.get) if query_counts else "N/A"
                
                # Get average query length
                queries_data = all_clicks.data
                avg_complexity = sum(len(q['query']) for q in queries_data) / len(queries_data) if queries_data else 0
                
                return {
                    'visits_today': visits_today,
                    'queries_today': queries_today,
                    'avg_rating': round(avg_rating, 2),
                    'most_popular_query': most_popular,
                    'avg_complexity': round(avg_complexity, 1)
                }
        except Exception as e:
            print(f"Supabase analytics error: {e}")
        
        # Fallback to SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM page_visits 
            WHERE DATE(visit_time) = DATE('now')
        ''')
        visits_today = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM query_clicks
            WHERE DATE(click_time) = DATE('now')
        ''')
        queries_today = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(rating) FROM reviews')
        avg_rating = cursor.fetchone()[0] or 0
        
        cursor.execute('''
            SELECT query, COUNT(*) as count FROM query_clicks
            GROUP BY query ORDER BY count DESC LIMIT 1
        ''')
        popular = cursor.fetchone()
        most_popular = popular[0] if popular else 'N/A'
        
        cursor.execute('SELECT AVG(LENGTH(query)) FROM query_clicks')
        avg_complexity = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'visits_today': visits_today,
            'queries_today': queries_today,
            'avg_rating': round(avg_rating, 2),
            'most_popular_query': most_popular,
            'avg_complexity': round(avg_complexity, 1)
        }
    
    def get_top_queries(self, limit=5):
        """Get most searched queries."""
        try:
            if self.use_supabase:
                all_clicks = self.supabase.table("query_clicks").select("query").execute()
                query_counts = {}
                for click in all_clicks.data:
                    q = click['query']
                    query_counts[q] = query_counts.get(q, 0) + 1
                sorted_queries = sorted(query_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
                return sorted_queries
        except Exception as e:
            print(f"Supabase query error: {e}")
        
        # Fallback to SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT query, COUNT(*) as count FROM query_clicks
            GROUP BY query ORDER BY count DESC LIMIT ?
        ''', (limit,))
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_rating_distribution(self):
        """Get distribution of star ratings."""
        try:
            if self.use_supabase:
                all_reviews = self.supabase.table("reviews").select("rating").execute()
                rating_counts = {}
                for review in all_reviews.data:
                    rating = review['rating']
                    if rating:
                        rating_counts[rating] = rating_counts.get(rating, 0) + 1
                sorted_ratings = sorted(rating_counts.items(), key=lambda x: x[0], reverse=True)
                return sorted_ratings
        except Exception as e:
            print(f"Supabase rating error: {e}")
        
        # Fallback to SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT rating, COUNT(*) as count FROM reviews
            GROUP BY rating ORDER BY rating DESC
        ''')
        results = cursor.fetchall()
        conn.close()
        return results
