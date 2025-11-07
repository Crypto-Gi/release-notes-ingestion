"""FastAPI wrapper for n8n orchestration"""

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Optional
import uuid
import logging
from datetime import datetime
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pipeline import IngestionPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Release Notes Ingestion API",
    description="REST API for n8n orchestration of the ingestion pipeline",
    version="1.0.0"
)

# Global state for tracking tasks
tasks = {}
pipeline_instance = None


class TaskStatus(BaseModel):
    """Task status model"""
    task_id: str
    status: str  # "pending", "running", "completed", "failed"
    progress: Optional[str] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


def get_pipeline() -> IngestionPipeline:
    """Get or create pipeline instance"""
    global pipeline_instance
    if pipeline_instance is None:
        pipeline_instance = IngestionPipeline()
    return pipeline_instance


def run_pipeline_task(task_id: str):
    """Background task to run the pipeline"""
    try:
        logger.info(f"Starting pipeline task: {task_id}")
        tasks[task_id]["status"] = "running"
        tasks[task_id]["started_at"] = datetime.utcnow().isoformat() + "Z"
        
        # Run pipeline
        pipeline = get_pipeline()
        result = pipeline.run()
        
        # Update task status
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["result"] = result
        tasks[task_id]["completed_at"] = datetime.utcnow().isoformat() + "Z"
        
        logger.info(f"Pipeline task completed: {task_id}")
        
    except Exception as e:
        logger.error(f"Pipeline task failed: {task_id} - {e}")
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)
        tasks[task_id]["completed_at"] = datetime.utcnow().isoformat() + "Z"


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Release Notes Ingestion API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        pipeline = get_pipeline()
        health = pipeline.health_check()
        
        all_healthy = all(health.values())
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "services": health,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )


@app.post("/api/pipeline/start")
async def start_pipeline(background_tasks: BackgroundTasks):
    """Start the ingestion pipeline"""
    task_id = str(uuid.uuid4())
    
    # Initialize task
    tasks[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "progress": "Initializing...",
        "result": None,
        "error": None,
        "started_at": None,
        "completed_at": None
    }
    
    # Add background task
    background_tasks.add_task(run_pipeline_task, task_id)
    
    logger.info(f"Pipeline task created: {task_id}")
    
    return {
        "task_id": task_id,
        "status": "pending",
        "message": "Pipeline task started"
    }


@app.get("/api/pipeline/status/{task_id}")
async def get_task_status(task_id: str):
    """Get pipeline task status"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskStatus(**tasks[task_id])


@app.get("/api/pipeline/summary")
async def get_summary():
    """Get processing summary from logs"""
    try:
        pipeline = get_pipeline()
        stats = pipeline.log_manager.get_stats()
        
        return {
            "files_converted": stats["converted"],
            "files_uploaded": stats["uploaded"],
            "files_failed": stats["failed"],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/logs/conversion")
async def get_conversion_log():
    """Get conversion log"""
    try:
        pipeline = get_pipeline()
        return pipeline.log_manager.get_conversion_log()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/logs/upload")
async def get_upload_log():
    """Get upload log"""
    try:
        pipeline = get_pipeline()
        return pipeline.log_manager.get_upload_log()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/logs/failed")
async def get_failed_log():
    """Get failed files log"""
    try:
        pipeline = get_pipeline()
        return pipeline.log_manager.get_failed_files()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/collections/info")
async def get_collections_info():
    """Get Qdrant collections information"""
    try:
        pipeline = get_pipeline()
        
        filename_info = pipeline.qdrant_uploader.get_collection_info(
            pipeline.config.qdrant.filename_collection
        )
        content_info = pipeline.qdrant_uploader.get_collection_info(
            pipeline.config.qdrant.content_collection
        )
        
        return {
            "filename_collection": filename_info,
            "content_collection": content_info,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8060,
        reload=True,
        log_level="info"
    )
