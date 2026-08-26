# 🏦 APS Frontend - Streamlit Web Interface

## 🚀 Quick Start

### Option 1: Automatic Launch (Recommended)
```bash
python launch_frontend.py
```

### Option 2: Manual Launch
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

### Option 3: Windows Batch File
```batch
launch_frontend.bat
```

## 📱 Features

### 🎯 Dashboard
- **Real-time Metrics**: View automation rates, confidence scores, pattern detection
- **Data Visualization**: Interactive charts showing repair patterns and timelines
- **Quick Stats**: Total repairs, clearing types, message types overview

### 📋 Data Management
- **Sample Data**: Pre-loaded realistic banking audit logs
- **File Upload**: Import JSON audit logs from your system
- **Manual Entry**: Add individual repair logs with guided forms

### 🤖 AI Analysis
- **Dual AI Models**: Choose between Phi-3 (local) or Groq (cloud)
- **Model Comparison**: Run both models side-by-side
- **Pattern Recognition**: Automatic detection of repeated manual repair patterns
- **Rule Generation**: AI-suggested automation rules with confidence scores

### 📈 Export & Reporting
- **Multiple Formats**: JSON, Excel, PDF, CSV exports
- **Detailed Reports**: Comprehensive analysis summaries
- **Download Options**: One-click report generation

## 🔧 Configuration

### AI Models
- **Phi-3 (Local)**: Microsoft's Phi-3-mini-4k-instruct for privacy-focused analysis
- **Groq (Cloud)**: Llama-3-8B-8192 for ultra-fast cloud inference

### Data Formats
The system accepts audit logs in this format:
```json
{
  "log_type": "DR_ACCOUNT_MANUAL_REPAIR",
  "clearing_type": "SEPA",
  "message_type": "103",
  "old_account_id": "ACC001",
  "old_iban": "DE89 3704 0044 0532 0130 00",
  "new_account_id": "ACC001", 
  "new_iban": "DE89370400440532013000",
  "timestamp": "2026-03-31T10:15:30"
}
```

## 🎨 Interface Overview

### Tab 1: 📊 Dashboard
- Overview metrics and charts
- Recent repairs timeline
- Quick data preview

### Tab 2: 📋 Data Input
- Upload audit logs (JSON)
- Manual log entry forms
- Data validation and preview

### Tab 3: 🤖 AI Analysis  
- Model selection (Phi-3/Groq/Both)
- Pattern analysis results
- Generated automation rules
- Automation opportunities

### Tab 4: 📈 Results Export
- Report generation
- Multiple export formats
- Download management

## 🌐 Access

Once launched, open your browser to:
**http://localhost:8501**

## 🛠️ Troubleshooting

### Common Issues
1. **Port already in use**: Stop other Streamlit apps or use `--server.port 8502`
2. **Missing dependencies**: Run `pip install -r requirements.txt`
3. **AI model connection**: Check internet for Groq API or use Phi-3 local mode

### Support
- Check terminal output for detailed error messages
- Verify all dependencies are installed
- Ensure proper JSON format for uploaded files

## 🎯 Perfect for

✅ **Banking Teams**: Analyze payment repair patterns  
✅ **Operations**: Monitor automation opportunities  
✅ **Compliance**: Audit trail analysis  
✅ **IT Teams**: Rule deployment planning  
✅ **Management**: ROI analysis for automation  

---

**🚀 Ready to modernize your payment operations with AI-powered insights!**