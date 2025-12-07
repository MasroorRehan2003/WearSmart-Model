# WearSmart - AI Outfit Recommender API

A FastAPI-based outfit recommendation system that suggests clothing based on weather conditions, using machine learning models and cloud storage integration.

## 🚀 Features

- **Weather-based Recommendations**: Get outfit suggestions based on temperature, humidity, wind speed, and weather conditions
- **Gender-specific Models**: Separate ML models for men's and women's clothing
- **Cloudinary Integration**: Images stored in Cloudinary with URLs in MongoDB
- **RESTful API**: Clean REST endpoints for mobile app integration
- **MongoDB Atlas**: Cloud database for storing image metadata

## 📋 Prerequisites

- Python 3.8 or higher
- MongoDB Atlas account (for cloud images)
- Cloudinary account (optional, for cloud image storage)
- Model files: `weather_clothing_recommender.pkl` and `weather_clothing_recommender_women.pkl`
- Image folders: `clothing_images_men/` and `clothing_images/`

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd weather_module
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables (Optional)

Create a `.env` file in the project root:

```env
# MongoDB Atlas Connection String
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/wearsmart?retryWrites=true&w=majority

# Cloudinary Credentials (if using cloud images)
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

**Note:** The MongoDB connection string is already configured in `wearsmart_api.py` with default values. You can override it using the environment variable.

## 🏃 Running the API

### Start the FastAPI Server

```bash
uvicorn wearsmart_api:app --reload --port 8000
```

The API will be available at:
- **Local**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc

### For Network Access (Mobile Testing)

```bash
uvicorn wearsmart_api:app --host 0.0.0.0 --port 8000
```

Then use your computer's IP address instead of `localhost`.

## 📡 API Endpoints

### Health Check
```
GET /health
```
Returns API status and model loading information.

### Get Outfit Recommendation (Men)
```
POST /recommend/men
```
Body: JSON with weather data (temperature, humidity, wind_speed, weather_condition, time_of_day, season, occasion, mood)

### Get Outfit Recommendation (Women)
```
POST /recommend/women
```
Body: JSON with weather data (temperature, humidity, wind_speed, weather_condition, time_of_day, season, occasion)

### Get Local Images
```
GET /images?gender=men&label=shirt&limit=10
```
Returns local image URLs from static folders.

### Get Cloudinary Images (MongoDB)
```
GET /cloud-images?gender=men&label=hoodie&limit=5
```
Returns Cloudinary URLs from MongoDB database.

## 🧪 Testing

### Test the API

```bash
python test_cloud_images.py
```

This will test:
- `/health` endpoint
- `/cloud-images` endpoint with sample queries

## 📁 Project Structure

```
weather_module/
├── wearsmart_api.py              # Main FastAPI application
├── requirements.txt              # Python dependencies
├── test_cloud_images.py          # API test script
├── upload_to_cloudinary_mongodb.py  # Upload images to Cloudinary + MongoDB
├── weather_clothing_recommender.pkl          # Men's ML model
├── weather_clothing_recommender_women.pkl    # Women's ML model
├── clothing_images_men/          # Men's clothing images
└── clothing_images/             # Women's clothing images
```

## 🔐 Security Notes

- **Never commit sensitive data** (passwords, API keys) to Git
- Use environment variables for production
- Add `.env` to `.gitignore`
- Keep MongoDB connection strings secure

## 📚 Documentation

- **API Documentation**: See `API_DOCUMENTATION.md`
- **MongoDB Setup**: See `MONGODB_UPLOAD_GUIDE.md`
- **Cloudinary Setup**: See `CLOUDINARY_UPLOAD_GUIDE.md`
- **Quick Start**: See `QUICK_START.md`

## 🐛 Troubleshooting

### Models Not Loading
- Ensure `.pkl` files exist in the project directory
- Check file paths in `wearsmart_api.py`

### MongoDB Connection Failed
- Verify connection string is correct
- Check IP whitelist in MongoDB Atlas
- Ensure internet connection is active

### Images Not Found
- Verify image folders exist: `clothing_images_men/` and `clothing_images/`
- Check subfolders contain image files (.jpg, .jpeg, .png, .webp)

### Port Already in Use
```bash
# Use a different port
uvicorn wearsmart_api:app --reload --port 8001
```

## 📝 License

[Your License Here]

## 👥 Contributors

[Your Name/Team]

---

**Need Help?** Check the documentation files or open an issue on GitHub.

