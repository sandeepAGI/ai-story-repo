# Dashboard Launcher Guide

This document explains the two ways to launch the AI Customer Stories Dashboard and when to use each approach.

## 🚀 **Two Launch Methods Available**

### **Method 1: Direct Streamlit Command (Recommended for Most Users)**
```bash
streamlit run dashboard.py
```

**✅ Benefits:**
- **Fastest startup** - No overhead, direct execution
- **Simplest command** - Standard Streamlit approach
- **Maximum flexibility** - Full access to all Streamlit CLI options
- **Clean output** - Direct Streamlit logs without wrapper noise
- **Industry standard** - What most Streamlit developers expect
- **Easy debugging** - Direct error messages from Streamlit
- **Customizable** - Add any Streamlit flags you need

**🎯 Use When:**
- Daily development work
- You want the fastest startup
- You need specific Streamlit options
- You're familiar with Streamlit CLI
- You want clean, minimal output

**📝 Examples:**
```bash
# Basic launch
streamlit run dashboard.py

# Custom port
streamlit run dashboard.py --server.port 8502

# Development mode with file watching
streamlit run dashboard.py --server.runOnSave true

# External access
streamlit run dashboard.py --server.address 0.0.0.0
```

---

### **Method 2: Production Launcher Script (Enhanced Mode)**
```bash
python scripts/production/run_dashboard.py
```

**✅ Benefits:**
- **Pre-flight validation** - Checks dependencies and database before starting
- **Automatic browser opening** - Opens http://localhost:8501 after 3 seconds
- **Environment validation** - Confirms system is ready to run
- **Story count display** - Shows how many stories are in your database
- **Error prevention** - Catches common setup issues early
- **Production-ready settings** - Optimized server configuration
- **User-friendly output** - Clear status messages and instructions

**🎯 Use When:**
- First-time setup or after system changes
- You want validation that everything is working
- You prefer automatic browser opening
- Running in production/deployment scenarios
- You want to see database story count
- Troubleshooting connection issues

**🔍 What It Validates:**
- ✅ Required packages installed (streamlit, plotly, pandas, psycopg2)
- ✅ Database connectivity and accessibility
- ✅ Story count in database
- ✅ Automatic browser launch

---

## 🤝 **Why Two Methods?**

These methods serve **different user needs** and **different scenarios**:

### **Philosophy:**
- **Method 1** follows the **"simple tools do one thing well"** principle
- **Method 2** follows the **"provide helpful automation"** principle

### **User Personas:**
- **Developers/Power Users** → Method 1 (direct control, speed)
- **End Users/New Users** → Method 2 (validation, guidance)

### **Scenarios:**
- **Daily development workflow** → Method 1
- **First run or troubleshooting** → Method 2
- **Production deployment** → Method 2
- **Custom configuration needed** → Method 1

---

## 📊 **Comparison Table**

| Feature | Method 1: Direct | Method 2: Enhanced |
|---------|------------------|-------------------|
| **Startup Speed** | ⚡ Instant (~1-2s) | 🕐 5-8 seconds |
| **Flexibility** | ✅ All Streamlit options | ❌ Fixed settings |
| **Validation** | ❌ None | ✅ Dependencies + DB |
| **Browser** | 👤 Manual | 🤖 Auto-opens |
| **Output** | 📄 Clean Streamlit logs | 📋 Enhanced status info |
| **Troubleshooting** | 🔧 Direct error messages | 🔍 Pre-flight diagnostics |
| **Customization** | ✅ Any CLI flags | ❌ Preset configuration |
| **Learning Curve** | 📚 Standard Streamlit | 🎯 Custom wrapper |

---

## 🏆 **Our Recommendation**

### **For Most Users: Start with Method 1**
```bash
streamlit run dashboard.py
```
- It's faster, simpler, and gives you full control
- Use this for 90% of your dashboard launches

### **Use Method 2 When You Need:**
```bash
python scripts/production/run_dashboard.py
```
- System validation before important demos/presentations
- First-time setup verification  
- Troubleshooting connectivity issues
- Automatic browser opening convenience

---

## 🛠️ **Troubleshooting**

### **If Method 1 Fails:**
1. Check if you're in the right directory (should see `dashboard.py`)
2. Verify Streamlit is installed: `pip install streamlit`
3. Try Method 2 for detailed diagnostics

### **If Method 2 Fails:**
1. Read the specific error messages - they're designed to be helpful
2. Common issues it catches:
   - Missing dependencies → Run `pip install -r requirements.txt`
   - Database not running → Start your PostgreSQL service
   - Port conflicts → Method 1 with different port

### **Both Methods Fail:**
1. Check Python environment: `python --version`
2. Verify project structure: `ls -la` (should see dashboard.py)
3. Check requirements: `pip install -r requirements.txt`
4. Test database independently: `python -c "from src.database.models import DatabaseOperations; print('DB OK')"`

---

## 📁 **File Locations**

```
ai-stories/
├── dashboard.py                           # Main dashboard file
├── scripts/production/run_dashboard.py    # Enhanced launcher
└── DASHBOARD-LAUNCHER-GUIDE.md           # This guide
```

Both methods launch the same `dashboard.py` file - they just provide different ways to start it based on your needs and preferences.