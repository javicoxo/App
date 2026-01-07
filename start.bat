@echo off
setlocal

set "ROOT=%~dp0"

pushd "%ROOT%"
start "BeFitLab API" cmd /k "uvicorn backend.app.main:app --reload --port 8000"
start "BeFitLab Frontend" cmd /k "streamlit run frontend/app.py --server.port 8501"
popd
