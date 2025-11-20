# 🏁 VelocityInsight - GR Cup Racing Analytics

**Hack the Track 2025 Submission** | AI-Powered Race Strategy & Telemetry Analysis

> A comprehensive racing telemetry and strategy platform for Toyota GR Cup with AI-powered insights, real-time data streaming, and predictive analytics.

## 🏆 Hackathon Categories

This project competes in **FOUR categories**, providing end-to-end race weekend coverage:

- ✅ **Driver Training & Insights** - AI-powered performance analysis, racing line optimization, and personalized improvement recommendations
- ✅ **Pre-Event Prediction** - Weather-integrated qualifying forecasts, race pace predictions, and strategic recommendations
- ✅ **Post-Event Analysis** - Comprehensive race storytelling with key moments, strategic decisions, and performance highlights
- ✅ **Real-Time Analytics** - Live telemetry monitoring, position tracking, and lap-by-lap data visualization

---

## ✨ Features

### 🤖 AI-Powered Insights (Google Gemini 2.5 Flash)
- **Driver Training & Insights** - Identify areas for improvement, optimize racing line, performance patterns
- **Pre-Event Prediction** - Forecast qualifying results, race pace, tire degradation
- **Post-Event Analysis** - Comprehensive race story with key moments and strategic decisions
- **Natural Language Generation** - Human-readable insights and recommendations

### 🎨 Modern UI/UX
- **Dark/Light Theme Toggle** - Seamless theme switching with adaptive backgrounds
- **Glassmorphism Design** - Premium liquid glass aesthetic with backdrop blur effects
- **Animated Backgrounds** - WebGL-powered mesh gradients with smooth transitions
- **Gooey Text Morphing** - Dynamic hero section with morphing text animation
- **Responsive Design** - Optimized for desktop, tablet, and mobile devices
- **Bento Grid Layout** - Modern asymmetric feature showcase on homepage
- **Interactive Charts** - Real-time data visualizations with Recharts
- **Lucide Icons** - Professional icon system instead of emojis

### 🎯 Core Analytics
- **Real-Time Telemetry Streaming** - Live WebSocket data at 20Hz
- **Lap Time Analysis** - Historical lap progression with tire age tracking
- **Tire Degradation Modeling** - ML-powered performance decline prediction
- **Pit Stop Strategy Optimization** - Data-driven pit window calculations
- **Driving Style Analysis** - Aggression scoring and tire wear correlation
- **Multi-Vehicle Comparison** - Compare performance across drivers
- **Weather Integration** - Real-time weather data for strategic recommendations
- **Lap Time Predictor** - XGBoost regression (6 tracks, R² 0.72-0.98)
- **Tire Degradation Model** - Polynomial regression (R² 0.617)
- **Pit Strategy Optimizer** - Multi-factor optimization engine
- **Driving Style Analyzer** - Behavioral scoring algorithm

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- 24GB dataset (7 racing circuits)

### Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Start server
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Backend will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at `http://localhost:5173`

### Train ML Models (Optional)

```bash
cd backend
python3 train_models.py
```

This trains lap time prediction models for all 6 supported tracks.

## 📁 Project Structure

```
gr2025/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # REST endpoints
│   │   │   ├── telemetry.py
│   │   │   ├── analytics.py
│   │   │   ├── strategy.py
│   │   │   ├── predictions.py
│   │   │   ├── insights.py  # AI-powered insights
│   │   │   └── consistency.py
│   │   ├── ml/             # Machine learning models
│   │   ├── data/           # Data loading & processing
│   │   └── websocket/       # Real-time streaming
│   ├── models/             # Trained ML models (.pkl)
│   └── requirements.txt
│
├── frontend/                # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   │   ├── TelemetryChart.tsx
│   │   │   ├── LapTimeline.tsx
│   │   │   ├── DriverTraining.tsx
│   │   │   ├── PreEventPrediction.tsx
│   │   │   └── PostEventAnalysis.tsx
│   │   ├── api/            # API clients
│   │   └── App.tsx
│   └── package.json
│
└── dataset/                # Race data (7 circuits)
    ├── barber/
    ├── indianapolis/
    ├── COTA/
    ├── Road America/
    ├── Sonoma/
    ├── VIR/
    └── Sebring/
```

## 🔌 API Endpoints

### Core Endpoints
- `GET /` - Health check
- `GET /tracks` - List available tracks
- `GET /telemetry` - Raw telemetry data
- `GET /laps` - Lap time analysis

### Analytics Endpoints
- `GET /analytics/degradation/{track}/{race}` - Tire degradation analysis
- `GET /analytics/degradation/{track}/{race}/{vehicle_id}/predictions` - Degradation predictions
- `GET /analytics/driving-style/{track}/{race}/{vehicle_id}` - Driving style analysis

### Strategy Endpoints
- `GET /strategy/pit/{track}/{race}/{vehicle_id}` - Pit stop strategy
- `GET /strategy/pit/{track}/{race}/{vehicle_id}/undercut` - Undercut analysis
- `GET /strategy/compare/{track}/{race}` - Strategy comparison
- `POST /strategy/pit/{track}/{race}/{vehicle_id}/simulate` - Race simulation

### Predictions Endpoints
- `GET /predictions/laptime/{track}/{race}/{vehicle_id}` - Predict lap time
- `GET /predictions/laptime/next/{track}/{race}/{vehicle_id}` - Predict next lap

### Insights Endpoints (AI-Powered)
- `GET /insights/driver-training/{track}/{race}/{vehicle_id}` - Driver training insights
- `GET /insights/pre-event-prediction/{track}` - Pre-event predictions
- `POST /insights/post-event-analysis` - Upload CSV for analysis
- `GET /insights/post-event-analysis/{track}/{race}` - Analyze existing race data

### Real-Time Streaming
- `WebSocket: ws://localhost:8000/ws/live/{track}/{race}` - Live telemetry stream

## 🎨 Features in Detail

### Driver Training & Insights
Analyzes driver performance and provides:
- Areas for improvement (specific sectors or techniques)
- Racing line optimization suggestions
- Performance patterns and insights
- Actionable training recommendations

### Pre-Event Prediction
Forecasts race outcomes before the event:
- Qualifying positions and times
- Race pace predictions
- Tire degradation forecast
- Strategic recommendations

### Post-Event Analysis
Tells the story of the race:
- Race narrative (beginning, middle, end)
- Key strategic decisions
- Critical moments that defined the outcome
- Performance highlights
- Lessons learned

**Upload CSV**: Upload post-race data via `POST /insights/post-event-analysis` with a CSV file.

## 📊 Supported Tracks

1. **Barber Motorsports Park** - R1, R2
2. **Indianapolis Motor Speedway** - R1, R2
3. **Circuit of the Americas (COTA)** - R1, R2
4. **Road America** - R1, R2
5. **Sonoma Raceway** - R1, R2
6. **Virginia International Raceway (VIR)** - R1, R2
7. **Sebring International Raceway** - R1, R2

## 🧪 Testing

### Test All Endpoints
```bash
cd backend
python3 test_all_endpoints.py
```

### Test Individual Components
```bash
python3 test_complete_backend.py
python3 test_lap_predictor.py
python3 test_race_simulator.py
```

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **XGBoost** - Machine learning for lap time prediction
- **scikit-learn** - ML utilities
- **pandas** - Data processing
- **Google Generative AI** - Gemini 2.5 Flash for AI insights

### Frontend
- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Recharts** - Data visualization
- **Socket.IO** - WebSocket client
- **Axios** - HTTP client

## 📈 Performance Metrics

- **API Response Time**: <100ms (analytics endpoints)
- **Model Inference**: <50ms per prediction
- **WebSocket Latency**: <50ms
- **Model Accuracy**: R² 0.72-0.98 (lap time prediction)
- **Dataset Size**: 24GB across 7 circuits

## 🔧 Configuration

### Backend Environment Variables
```bash
# Dataset root path (default: ../dataset)
DATASET_ROOT=/path/to/dataset
```

### Frontend Environment Variables
```bash
# .env file
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

### Gemini API Key
The Gemini API key is configured in:
- `backend/app/api/insights.py` (backend)
- `frontend/src/api/gemini.ts` (frontend)

## 📝 Usage Examples

### Get Driver Training Insights
```bash
curl "http://localhost:8000/insights/driver-training/barber/R1/GR86-002-000"
```

### Get Pre-Event Predictions
```bash
curl "http://localhost:8000/insights/pre-event-prediction/barber?weather=Sunny&track_temp=25"
```

### Upload Post-Event Data
```bash
curl -X POST "http://localhost:8000/insights/post-event-analysis?track=barber&race=R1" \
  -F "file=@race_data.csv"
```

### Get Post-Event Analysis
```bash
curl "http://localhost:8000/insights/post-event-analysis/barber/R1"
```

## 🎯 Use Cases

### For Race Engineers
- Monitor tire degradation in real-time
- Receive pit stop recommendations
- Analyze driver behavior patterns
- Compare different race strategies

### For Team Strategists
- Evaluate undercut opportunities
- Simulate race scenarios
- Optimize pit windows
- Pre-event race predictions

### For Drivers
- Identify areas for improvement
- Optimize racing line
- Understand tire management needs
- Get actionable training recommendations

## 🚦 Development Status

**Overall Completion: 95%+**

- ✅ Backend: 100% Complete
- ✅ Frontend: 95% Complete
- ✅ ML Models: 100% Trained
- ✅ API Endpoints: 13+ endpoints
- ✅ Real-Time Streaming: Working
- ✅ AI Insights: Integrated with Gemini 2.5 Flash

## 📚 Documentation

- **API Documentation**: `http://localhost:8000/docs` (Swagger UI)
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

## 🐛 Troubleshooting

### Backend Issues
- **Port 8000 already in use**: `lsof -ti:8000 | xargs kill -9`
- **Module not found**: Run `pip install -r requirements.txt`
- **Gemini API errors**: Check API key in `backend/app/api/insights.py`

### Frontend Issues
- **Cannot connect to backend**: Ensure backend is running on port 8000
- **WebSocket not connecting**: Check CORS configuration in backend
- **No data loading**: Verify track/race/vehicle combination exists

## 📄 License

© 2025 GR-Insight. All rights reserved.

## 🤝 Contributing

This is a project for the GR Cup 2025 racing series. For contributions, please ensure:
- Code follows existing patterns
- Tests pass before submitting
- Documentation updated for new features

## 🙏 Acknowledgments

- Powered by **XGBoost** for lap time predictions
- **Gemini 2.5 Flash** for AI-powered insights
- Built with **React** + **FastAPI** for modern web development
- Data visualization by **Recharts**

---

**GR-Insight** - Empowering Toyota GR Cup teams with AI-driven race strategy 🏁
