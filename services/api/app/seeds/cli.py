from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.seeds.catalog import seed_all


def main() -> None:
    init_db()
    with SessionLocal() as db:
        seed_all(db)
    print('Seed complete')


if __name__ == '__main__':
    main()
