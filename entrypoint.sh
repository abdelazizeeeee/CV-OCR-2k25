#!/bin/bash
# Check if the model directory is empty and populate it if needed
if [ ! -d "/app/src/ResumeModel/output/model-best" ] || [ -z "$(ls -A /app/src/ResumeModel/output/model-best)" ]; then
  echo "Copying model files..."
  mkdir -p /app/src/ResumeModel/output/model-best
  cp -r /app/model_backup/* /app/src/ResumeModel/output/model-best/
fi

# Start the application
exec uvicorn src.main:app --host 0.0.0.0 --port 5000 --reload