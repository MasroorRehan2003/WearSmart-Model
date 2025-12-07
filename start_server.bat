@echo off
echo Starting WearSmart FastAPI Server...
echo.
echo Server will be available at:
echo   - Local: http://localhost:8000
echo   - Network: http://YOUR_IP:8000
echo   - Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

uvicorn unified_wearsmart:app --reload --host 0.0.0.0 --port 8000

pause

