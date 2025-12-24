from sqlalchemy import Column, Integer, String, JSON, DateTime, func, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from .db import Base

class RawAsset(Base):
    __tablename__ = "raw_assets"
    id = Column(Integer, primary_key=True)
    source = Column(String, nullable=False)
    record_id = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint('source','record_id',name='uq_raw_source_record'),)

class Asset(Base):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True)
    symbol = Column(String, nullable=False)
    name = Column(String, nullable=True)
    external_id = Column(String, nullable=False)
    source = Column(String, nullable=False)
    run_metadata = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint('external_id','source',name='uq_asset_external_source'),)

class Checkpoint(Base):
    __tablename__ = "etl_checkpoints"
    id = Column(Integer, primary_key=True)
    source = Column(String, nullable=False, unique=True)
    last_record_id = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ETLRun(Base):
    __tablename__ = "etl_runs"
    id = Column(Integer, primary_key=True)
    source = Column(String, nullable=False)
    run_started_at = Column(DateTime(timezone=True), server_default=func.now())
    run_finished_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, nullable=False)
    records_processed = Column(Integer, default=0)
    error = Column(String, nullable=True)
    injected_failure = Column(Boolean, default=False)
