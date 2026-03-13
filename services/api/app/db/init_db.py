from pathlib import Path

from app.db.session import engine
from app.models import Base


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def reset_db() -> None:
    if engine.url.get_backend_name() == 'sqlite' and engine.url.database and engine.url.database != ':memory:':
        engine.dispose()
        Path(engine.url.database).unlink(missing_ok=True)
        Base.metadata.create_all(bind=engine)
        return
    Base.metadata.create_all(bind=engine)
