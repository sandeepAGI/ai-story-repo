# AI Customer Stories Dashboard

A comprehensive Streamlit-based web dashboard for exploring and analyzing AI customer stories from 191 companies across 5 major AI providers (Anthropic, OpenAI, AWS, Google Cloud, Microsoft Azure).

## 🚀 Quick Start

```bash
# Start the dashboard
python run_dashboard.py

# Or directly with streamlit
streamlit run dashboard.py
```

The dashboard will be available at: http://localhost:8501

## 📊 Features

### Core Functionality
- **📈 Overview Dashboard**: Key metrics, source distribution, and recent activity
- **🔍 Story Explorer**: Advanced search and filtering across all 191 stories
- **📊 Analytics**: Industry distribution, technology usage, and timeline analysis
- **🎯 Aileron Insights**: GenAI SuperPowers framework analytics
- **💾 Data Export**: CSV, Excel, and JSON downloads with filtering

### Aileron GenAI Framework Analysis (Enhanced with Official Framework)
- **🔗 SuperPowers (Drive)**: 7 AI capabilities with icons (Code, Create Content, Automate with Agents, Find Data Insights, Research, Brainstorm, Use Natural Language)
- **🚀 Business Impacts (Constrain)**: 6 outcomes with icons (Innovation, Efficiency, Speed, Quality, Client Satisfaction, Risk Reduction)
- **🛡️ Adoption Enablers**: 5 organizational factors (Data & Digital, Innovation Culture, Ecosystem Partners, Policy & Governance, Risk Management)
- **🏢 Business Value Chain**: 6 functions (Marketing → Sales → Production → Distribution → Service → Finance & Accounting)
- **🔄 Cross-Analysis Matrix**: Interactive heatmap showing how AI capabilities drive business outcomes
- **📋 Key Insights**: Top SuperPower → Impact combinations with story counts

### Visualization Features
- Interactive Plotly charts with download capability (PNG, SVG, PDF)
- Responsive design for all screen sizes
- Real-time filtering and search
- Exportable visualizations for presentations

## 🏗️ Architecture

### Technology Stack
- **Frontend**: Streamlit (Python-based web framework)
- **Visualizations**: Plotly for interactive charts
- **Data Processing**: Pandas for data manipulation
- **Database**: PostgreSQL with existing schema
- **Export**: CSV, Excel (openpyxl), JSON formats

### Dashboard Structure
```
dashboard.py
├── Main Navigation (5 pages)
├── Data Loading (cached for performance)
├── Visualization Components
└── Export Functionality

Pages:
📊 Overview - Key metrics and source distribution
🔍 Story Explorer - Search and filtering interface  
📈 Analytics - Industry, technology, and timeline analysis
🎯 Aileron Insights - GenAI framework analytics
💾 Data Export - Filtered export capabilities
```

## 📋 System Requirements

### Dependencies
```
streamlit>=1.28.0
plotly>=5.17.0
pandas>=2.0.0
openpyxl>=3.1.0
```

### Database
- PostgreSQL with existing ai_stories database
- 191 customer stories with Aileron framework classifications
- Full-text search capabilities

## 🔧 Configuration

### Environment Setup
1. Ensure PostgreSQL database is running
2. Install dependencies: `pip install -r requirements.txt`
3. Verify database connectivity with existing stories

### Performance Optimization
- **Caching**: Database queries cached for 5 minutes
- **Lazy Loading**: Charts rendered on-demand
- **Efficient Queries**: Optimized PostgreSQL queries with indexes

## 📊 Data Overview

### Current Dataset (191 Stories)
- **Anthropic**: 129 stories (67.5%)
- **OpenAI**: 33 stories (17.3%)
- **AWS AI/ML**: 10 stories (5.2%)
- **Google Cloud AI**: 10 stories (5.2%)
- **Microsoft Azure**: 9 stories (4.7%)

### Data Quality
- **100% completeness** on core fields (customer_name, url, source)
- **Rich extracted data** with Claude AI processing
- **Aileron framework** classifications on all processed stories
- **Full-text search** integration

## 🎯 Use Cases

### Business Intelligence
- **Competitive Analysis**: Compare AI adoption across providers
- **Market Research**: Industry trends and technology usage patterns
- **Strategic Planning**: Identify successful AI implementation patterns

### Research & Analysis
- **Academic Research**: Comprehensive dataset for AI adoption studies
- **Technology Assessment**: Real-world AI use cases and outcomes
- **Best Practices**: Learn from successful implementations

### Data Export & Integration
- **Filtered Exports**: Custom datasets based on criteria
- **Business Reports**: Ready-to-use data for presentations
- **API Integration**: JSON exports for further processing

## 🧪 Testing

### Test Suite
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_dashboard.py -v          # Unit tests
python -m pytest tests/test_dashboard_integration.py -v  # Integration tests

# Run with coverage
python -m pytest --cov=dashboard --cov-report=html
```

### Test Coverage
- **Unit Tests**: Core functionality, data processing, exports
- **Integration Tests**: Database connectivity, real data validation
- **Performance Tests**: Large dataset handling, query optimization
- **Data Quality Tests**: Validation of extracted data structure

## 🚀 Advanced Usage

### Custom Filtering
```python
# Example: Filter stories by multiple criteria
filtered_data = df[
    (df['source_name'] == 'Anthropic') & 
    (df['industry'] == 'technology') &
    (df['company_size'] == 'startup')
]
```

### API Integration
```python
# Export data programmatically
import pandas as pd
from dashboard import create_download_data

df = load_all_stories()
csv_data = create_download_data(df, 'csv')
json_data = create_download_data(df, 'json')
```

### Custom Visualizations
```python
# Add custom charts using existing data loading
import plotly.express as px

aileron_data = get_aileron_analytics()
fig = px.sunburst(
    data,
    path=['superpowers', 'business_impact'],
    values='count'
)
```

## 🔍 Troubleshooting

### Common Issues

**Database Connection Error**
```
❌ Database connection failed: connection refused
```
- Ensure PostgreSQL is running
- Check connection parameters in src/config.py
- Verify database contains customer_stories table

**Missing Dependencies**
```
❌ Missing dependency: No module named 'streamlit'
```
- Run: `pip install -r requirements.txt`
- Use virtual environment if needed

**Port Already in Use**
```
❌ Port 8501 is already in use
```
- Kill existing Streamlit process
- Use different port: `streamlit run dashboard.py --server.port 8502`

### Performance Tips
- Use filters to reduce dataset size for better performance
- Cache is automatically cleared every 5 minutes
- Large exports (>1000 stories) may take a few seconds

## 📈 Future Enhancements

### Planned Features
- **Real-time Updates**: Auto-refresh when new stories are added
- **User Authentication**: Multi-user access with saved preferences
- **Advanced Analytics**: Machine learning insights and predictions
- **API Endpoints**: RESTful API for programmatic access
- **Mobile Optimization**: Enhanced mobile responsiveness

### Integration Opportunities
- **Business Intelligence Tools**: Tableau, Power BI connectors
- **Slack/Teams Integration**: Automated insights delivery
- **Email Reports**: Scheduled analytics summaries
- **Cloud Deployment**: AWS/GCP hosted version

## 📝 Support

### Documentation
- See `ai-big5-stories.md` for project requirements
- Check `TRACKER-LOG.md` for development history
- Review test files for usage examples

### Getting Help
- Check database connectivity first
- Review error messages in terminal
- Ensure all dependencies are installed
- Verify data exists in database

---

**Built with ❤️ using Streamlit, Plotly, and the power of 191 real AI customer stories**