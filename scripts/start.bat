@echo off
REM AgentForge Start Script for Windows

echo Starting AgentForge services...

REM Check if docker-compose is available
where docker-compose >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo docker-compose is not installed. Please install Docker and docker-compose first.
    exit /b 1
)

REM Start all services
docker-compose up -d

echo.
echo AgentForge services started successfully!
echo.
echo Services:
echo   - API:    http://localhost:8000
echo   - Web:    http://localhost:3000
echo   - DB:     localhost:5432
echo   - Redis:  localhost:6379
echo   - Chroma: localhost:8100
echo.
echo To view logs: docker-compose logs -f
echo To stop:      docker-compose down
