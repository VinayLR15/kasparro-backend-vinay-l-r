from sqlalchemy import Column, Integer, String, JSON, DateTime, func, Boolean, UniqueConstraint, ForeignKey, Index
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

class Coin(Base):
    """Canonical coin entity - unified identity across all sources."""
    __tablename__ = "coins"
    id = Column(Integer, primary_key=True)
    symbol = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship to source mappings
    sources = relationship("CoinSource", back_populates="coin", cascade="all, delete-orphan")

class CoinSource(Base):
    """Links source-specific data to canonical coins."""
    __tablename__ = "coin_sources"
    id = Column(Integer, primary_key=True)
    coin_id = Column(Integer, ForeignKey("coins.id", ondelete="CASCADE"), nullable=False, index=True)
    source = Column(String, nullable=False)
    external_id = Column(String, nullable=False)
    source_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint('coin_id', 'source', name='uq_coin_source'),
        UniqueConstraint('source', 'external_id', name='uq_source_external_id'),
        Index('idx_source_external_id', 'source', 'external_id'),
    )
    
    # Relationship to canonical coin
    coin = relationship("Coin", back_populates="sources")

# Keep Asset for backward compatibility during migration, but it's deprecated
class Asset(Base):
    """Deprecated: Use Coin and CoinSource instead."""
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
