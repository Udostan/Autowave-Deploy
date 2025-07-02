#!/usr/bin/env python3
"""
Quick setup script for subscription tables without requiring Supabase
Creates local SQLite tables for testing paywall functionality
"""

import sqlite3
import os
import sys
from datetime import datetime, timedelta

def setup_local_subscription_db():
    """Setup local SQLite database for subscription testing"""
    
    print("🚀 Setting up local subscription database for testing...")
    
    # Create database directory if it doesn't exist
    db_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(db_dir, exist_ok=True)
    
    db_path = os.path.join(db_dir, 'subscriptions.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create subscription plans table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscription_plans (
                id TEXT PRIMARY KEY,
                plan_name TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                monthly_price_usd REAL NOT NULL DEFAULT 0,
                annual_price_usd REAL NOT NULL DEFAULT 0,
                monthly_credits INTEGER NOT NULL DEFAULT 0,
                features TEXT NOT NULL DEFAULT '{}',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create user subscriptions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_subscriptions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                plan_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                payment_gateway TEXT NOT NULL DEFAULT 'test',
                gateway_subscription_id TEXT,
                gateway_customer_id TEXT,
                current_period_start TIMESTAMP,
                current_period_end TIMESTAMP,
                cancel_at_period_end BOOLEAN DEFAULT 0,
                trial_start TIMESTAMP,
                trial_end TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (plan_id) REFERENCES subscription_plans(id)
            )
        ''')
        
        # Create user credits table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_credits (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                total_credits INTEGER NOT NULL DEFAULT 0,
                used_credits INTEGER NOT NULL DEFAULT 0,
                billing_period_start TIMESTAMP,
                billing_period_end TIMESTAMP,
                rollover_credits INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert default subscription plans (optimized pricing)
        plans = [
            ('free-plan-id', 'free', 'Free Plan', 0, 0, 50, '{"ai_agents": ["prime_agent", "autowave_chat", "code_wave"], "daily_credits": 50, "credit_type": "daily", "file_upload_limit": 5, "support_level": "community"}'),
            ('plus-plan-id', 'plus', 'Plus Plan', 15, 171, 8000, '{"ai_agents": ["prime_agent", "autowave_chat", "code_wave", "agent_wave", "research_lab"], "monthly_credits": 8000, "credit_type": "monthly", "prime_agent_tools": 12, "file_upload_limit": 100, "credit_rollover": true, "rollover_limit": 0.5, "support_level": "email"}'),
            ('pro-plan-id', 'pro', 'Pro Plan', 99, 1188, 200000, '{"ai_agents": ["prime_agent", "autowave_chat", "code_wave", "agent_wave", "research_lab"], "monthly_credits": 200000, "credit_type": "monthly", "prime_agent_tools": -1, "file_upload_limit": -1, "credit_rollover": true, "rollover_limit": 0.3, "real_time_browsing": true, "support_level": "priority"}'),
            ('enterprise-plan-id', 'enterprise', 'Enterprise', 0, 0, -1, '{"ai_agents": ["prime_agent", "autowave_chat", "code_wave", "agent_wave", "research_lab"], "prime_agent_tools": -1, "file_upload_limit": -1, "real_time_browsing": true, "custom_integrations": true, "white_label": true, "support_level": "dedicated"}')
        ]
        
        cursor.executemany('''
            INSERT OR REPLACE INTO subscription_plans 
            (id, plan_name, display_name, monthly_price_usd, annual_price_usd, monthly_credits, features)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', plans)
        
        # Create test admin users
        admin_emails = ['reffynestan@gmail.com', 'autowave101@gmail.com']
        for email in admin_emails:
            user_id = f"admin-{email.split('@')[0]}"
            
            # Create admin subscription (Pro plan)
            cursor.execute('''
                INSERT OR REPLACE INTO user_subscriptions 
                (id, user_id, plan_id, status, current_period_start, current_period_end)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                f"sub-{user_id}",
                user_id,
                'pro-plan-id',
                'active',
                datetime.now().isoformat(),
                (datetime.now() + timedelta(days=30)).isoformat()
            ))
            
            # Create admin credits
            cursor.execute('''
                INSERT OR REPLACE INTO user_credits 
                (id, user_id, total_credits, used_credits, billing_period_start, billing_period_end)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                f"credits-{user_id}",
                user_id,
                -1,  # Unlimited credits for Pro plan
                0,
                datetime.now().isoformat(),
                (datetime.now() + timedelta(days=30)).isoformat()
            ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Local subscription database created: {db_path}")
        print("✅ Default subscription plans inserted")
        print("✅ Admin users configured")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        return False

def test_subscription_db():
    """Test the subscription database"""
    
    print("\n🧪 Testing subscription database...")
    
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'subscriptions.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test plans
        cursor.execute("SELECT COUNT(*) FROM subscription_plans")
        plan_count = cursor.fetchone()[0]
        print(f"   Plans in database: {plan_count}")
        
        # Test subscriptions
        cursor.execute("SELECT COUNT(*) FROM user_subscriptions")
        sub_count = cursor.fetchone()[0]
        print(f"   Subscriptions in database: {sub_count}")
        
        # Test credits
        cursor.execute("SELECT COUNT(*) FROM user_credits")
        credit_count = cursor.fetchone()[0]
        print(f"   Credit records in database: {credit_count}")
        
        conn.close()
        
        if plan_count >= 4 and sub_count >= 2 and credit_count >= 2:
            print("✅ Database test successful!")
            return True
        else:
            print("❌ Database test failed - missing data")
            return False
            
    except Exception as e:
        print(f"❌ Database test error: {e}")
        return False

if __name__ == "__main__":
    print("AutoWave Local Subscription Database Setup")
    print("This creates a local SQLite database for testing paywall functionality.")
    
    success = setup_local_subscription_db()
    
    if success:
        test_success = test_subscription_db()
        
        if test_success:
            print("\n🎉 Setup completed successfully!")
            print("You can now test the paywall functionality.")
        else:
            print("\n⚠️  Setup completed but test failed.")
    else:
        print("\n❌ Setup failed.")
        sys.exit(1)
