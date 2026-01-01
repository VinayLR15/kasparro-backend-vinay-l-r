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
        Returns serialized dicts suitable for JSON response.
        """
        try:
            with SessionLocal() as session:
                # Query canonical coins
                stmt = select(Coin)
                if q:
                    q_pattern = f"%{q}%"
                    stmt = stmt.where(
                        or_(
                            Coin.symbol.ilike(q_pattern),
                            Coin.name.ilike(q_pattern)
                        )
                    )
                
                # Get total count
                total_stmt = select(sql_func.count(Coin.id))
                if q:
                    q_pattern = f"%{q}%"
                    total_stmt = total_stmt.where(
                        or_(
                            Coin.symbol.ilike(q_pattern),
                            Coin.name.ilike(q_pattern)
                        )
                    )
                total = session.execute(total_stmt).scalar() or 0
                
                # Apply pagination
                stmt = stmt.order_by(Coin.symbol).limit(limit).offset(offset)
                coins = session.execute(stmt).scalars().all()
                
                # Serialize to JSON-friendly dicts
                serialized_data = []
                for coin in coins:
                    # Get sources
                    sources_stmt = select(CoinSource).where(CoinSource.coin_id == coin.id)
                    sources = session.execute(sources_stmt).scalars().all()
                    
                    coin_dict = {
                        "id": coin.id,
                        "symbol": coin.symbol,
                        "name": coin.name,
                        "created_at": coin.created_at.isoformat() if coin.created_at else None,
                        "updated_at": coin.updated_at.isoformat() if coin.updated_at else None,
                        "sources": [
                            {
                                "source": s.source,
                                "external_id": s.external_id,
                                "metadata": s.source_metadata,
                                "created_at": s.created_at.isoformat() if s.created_at else None
                            }
                            for s in sources
                        ]
                    }
                    serialized_data.append(coin_dict)
                
                return serialized_data, total
        except Exception as e:
            logger.exception("Error in list_assets: %s", e)
            return [], 0
