# 🧠 AutoWave Memory Setup Guide

## Overview
AutoWave now includes intelligent memory capabilities for all agents using Qdrant Cloud. This allows agents to remember user preferences, past interactions, and provide personalized experiences.

## 🚀 Quick Setup (5 minutes)

### Step 1: Create Free Qdrant Cloud Account
1. Go to [https://cloud.qdrant.io/signup](https://cloud.qdrant.io/signup)
2. Sign up for a **free account** (no credit card required)
3. Create a new cluster:
   - Choose **Free Tier** (1GB storage)
   - Select your preferred region
   - Wait for cluster creation (1-2 minutes)

### Step 2: Get Your Credentials
1. In Qdrant Cloud dashboard, click on your cluster
2. Go to **"Access"** tab
3. Copy your:
   - **Cluster URL** (e.g., `https://xyz-abc-123.qdrant.io`)
   - **API Key** (click "Create API Key" if needed)

### Step 3: Configure AutoWave
1. Open `agen911/.env` file
2. Replace the placeholder values:
   ```env
   # Qdrant Cloud Configuration for Memory Service
   QDRANT_URL=https://your-actual-cluster-url.qdrant.io
   QDRANT_API_KEY=your-actual-api-key-here
   
   # Memory Service Configuration
   ENABLE_MEMORY=true
   MEMORY_RETENTION_DAYS=365
   ```

### Step 4: Install Dependencies
```bash
cd agen911
pip install qdrant-client==1.7.0 sentence-transformers==2.2.2
```

### Step 5: Test Memory (Optional)
Visit: `http://localhost:5009/api/memory/test` to verify memory is working.

## 🎯 What Memory Does

### For Prime Agent Tools:
- ✅ Remembers your booking preferences (airlines, hotels, etc.)
- ✅ Learns from past searches and recommendations
- ✅ Provides personalized suggestions based on history
- ✅ Recalls successful task patterns

### For Agentic Code:
- ✅ Remembers your coding style and preferences
- ✅ Learns from past code generation requests
- ✅ Suggests improvements based on previous projects
- ✅ Maintains consistency across coding sessions

### For Agent Wave:
- ✅ Remembers design preferences and styles
- ✅ Learns from past campaign successes
- ✅ Provides personalized design recommendations
- ✅ Maintains brand consistency

## 🔧 Memory Collections

AutoWave creates these memory collections automatically:
- `prime_agent_memory` - Task execution and user preferences
- `agentic_code_memory` - Code generation patterns and style
- `agent_wave_memory` - Design preferences and campaign history
- `context7_memory` - Tool usage patterns and preferences
- `global_user_memory` - Cross-agent user profile

## 💡 Memory Features

### Intelligent Context
- Agents automatically retrieve relevant past interactions
- Context is provided to improve current responses
- No manual memory management required

### User Preferences Learning
- Automatically learns from successful interactions
- Adapts to user patterns and preferences
- Improves recommendations over time

### Cross-Agent Memory
- Preferences learned in one agent benefit others
- Consistent user experience across all tools
- Unified user profile and preferences

## 🛡️ Privacy & Security

- **User Isolation**: Each user's memory is completely separate
- **Secure Storage**: All data encrypted in transit and at rest
- **GDPR Compliant**: Qdrant Cloud is GDPR compliant
- **Data Control**: You control your Qdrant instance and data

## 📊 Free Tier Limits

Qdrant Cloud Free Tier includes:
- ✅ **1GB storage** (approximately 1M vectors)
- ✅ **Unlimited queries** per month
- ✅ **No time limits** - free forever
- ✅ **Full feature access** including backups

This is sufficient for:
- 🎯 **Individual users**: Years of memory storage
- 🎯 **Small teams**: Months of active usage
- 🎯 **Development/Testing**: Complete feature testing

## 🚀 Scaling Options

When you need more storage:
- **Starter Plan**: $25/month for 8GB storage
- **Pro Plan**: $100/month for 32GB storage
- **Enterprise**: Custom pricing for larger needs

## 🔍 Troubleshooting

### Memory Not Working?
1. Check `.env` file has correct Qdrant credentials
2. Verify Qdrant cluster is running in dashboard
3. Check server logs for memory service errors
4. Test connection: `http://localhost:5009/api/memory/test`

### Dependencies Issues?
```bash
pip install --upgrade qdrant-client sentence-transformers
```

### Connection Errors?
- Verify your Qdrant URL includes `https://`
- Check API key is correct (no extra spaces)
- Ensure cluster is in "Running" state

## 🎉 Success!

Once configured, memory works automatically:
- No additional setup required
- Agents become smarter over time
- Personalized experience for each user
- Cross-agent learning and preferences

Your AutoWave platform now has enterprise-grade memory capabilities! 🧠✨
