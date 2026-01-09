from sqlalchemy import Column, Integer, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()

class OPDDocument(Base):
    __tablename__ = "opd_documents"

    id = Column(Integer, primary_key=True, index=True)
    doctor_text = Column(Text, nullable=False)
    soap = Column(Text, nullable=False)
    icd_codes = Column(JSONB, nullable=False)
    claim_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
