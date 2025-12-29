import logging
from core.db import SessionLocal
from core.models import Coin, CoinSource
from sqlalchemy import select, func as sql_func, or_

logger = logging.getLogger("services.api")

class APIService:
    @staticmethod
    def list_assets(limit: int = 50, offset: int = 0, q: str | None = None):
        """
        List canonical coins with their source mappings.
        Returns unified coins (normalized by symbol) with all their sources.
        """
        with SessionLocal() as session:
            # Query canonical coins
            stmt = select(Coin)
            if q:
                # Case-insensitive search on symbol and name
                q_pattern = f"%{q}%"
                stmt = stmt.where(
                    or_(
                        Coin.symbol.ilike(q_pattern),
                        Coin.name.ilike(q_pattern)
                    )
                )
            
            # Get total count before pagination
            total_stmt = select(sql_func.count(Coin.id))
            if q:
                q_pattern = f"%{q}%"
                total_stmt = total_stmt.where(
                    or_(
                        Coin.symbol.ilike(q_pattern),
                        Coin.name.ilike(q_pattern)
                    )
                )
            total = session.execute(total_stmt).scalar()
            
            # Apply pagination
            stmt = stmt.order_by(Coin.symbol).limit(limit).offset(offset)
            coins = session.execute(stmt).scalars().all()
            
            # Eagerly load sources for each coin
            result = []
            for coin in coins:
                # Get all sources for this coin
                sources = session.execute(
                    select(CoinSource).where(CoinSource.coin_id == coin.id)
                ).scalars().all()
                
                result.append({
                    "coin": coin,
                    "sources": sources
                })
            
            return result, total
