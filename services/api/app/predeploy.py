from app.core.config import get_settings
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.seeds.catalog import seed_all


def main() -> None:
    settings = get_settings()
    init_db()
    if settings.auto_seed_on_startup:
        with SessionLocal() as db:
            seed_all(db)


if __name__ == '__main__':
    main()
