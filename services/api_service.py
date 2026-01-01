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
        session = SessionLocal()
        try:
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
                # Find the primary source record for this coin to get its ID/Symbol/Name mapping
                # In this unified model, a "Coin" is the canonical entity.
                # The user expects id, symbol, name, source, and external_id.
                # Since a coin can have multiple sources, we take the first available one for this flat view.
                primary_source = session.execute(
                    select(CoinSource).where(CoinSource.coin_id == coin.id).limit(1)
                ).scalar_one_or_none()
                
                source_val = "unknown"
                if primary_source:
                    source_val = str(primary_source.source.value if hasattr(primary_source.source, "value") else primary_source.source)

                serialized_data.append({
                    "id": coin.id,
                    "symbol": coin.symbol,
                    "name": coin.name,
                    "source": source_val,
                    "external_id": primary_source.external_id if primary_source else "unknown"
                })
            
            return serialized_data, total
        except Exception as e:
            logger.error("Database error in list_assets: %s", str(e), exc_info=True)
            return [], 0
        finally:
            session.close()
