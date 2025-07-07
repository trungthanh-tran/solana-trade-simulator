from sqlalchemy import Column, Integer, String, Float, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Trade(Base):
    """SQLAlchemy model for trades table."""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True)
    type = Column(String, nullable=False)  # "buy" or "sell"
    ca_mint = Column(String, nullable=False, index=1)  # CA token mint address
    input_token = Column(String, nullable=False)  # Input token (SOL or CA)
    input_amount = Column(Float, nullable=False)  # Input amount in token units
    output_token = Column(String, nullable=False)  # Output token (CA or SOL)
    output_amount = Column(Float, nullable=False)  # Output amount in token units
    timestamp = Column(DateTime, nullable=False)  # Timestamp of trade
    slippage_bps = Column(Integer, nullable=False)  # Slippage in basis points
    __table_args__ = (
        Index('ix_ca_mint', ca_mint),
        Index('ix_type', type),
    )