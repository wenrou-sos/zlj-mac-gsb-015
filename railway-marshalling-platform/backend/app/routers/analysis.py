"""冲突分析接口。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..detector import analyze

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("", response_model=schemas.AnalysisResponse)
def run_analysis(db: Session = Depends(get_db)):
    """基于当前全部配置执行一次冲突检测。"""
    return analyze(db)
