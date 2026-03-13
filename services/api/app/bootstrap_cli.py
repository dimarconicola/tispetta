from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.services.corpus import ensure_bootstrap_corpus


def main() -> None:
    init_db()
    with SessionLocal() as db:
        result = ensure_bootstrap_corpus(db)
    print(f'Bootstrap complete: {result}')


if __name__ == '__main__':
    main()
