import traceback

from app.core.config import get_settings
from app.db.migrations import current_revision, head_revision
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.seeds.catalog import seed_all


def main() -> None:
    try:
        settings = get_settings()
        print(f'predeploy: current revision before upgrade = {current_revision() or "none"}')
        print('predeploy: running alembic upgrade')
        init_db()
        print(f'predeploy: current revision after upgrade = {current_revision() or "none"} (head = {head_revision()})')
        if settings.auto_seed_on_startup:
            print('predeploy: seeding catalog')
            with SessionLocal() as db:
                seed_all(db)
        print('predeploy: completed successfully')
    except Exception:
        print('predeploy: failed with exception')
        traceback.print_exc()
        raise


if __name__ == '__main__':
    main()
