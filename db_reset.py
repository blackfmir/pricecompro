from app.db.session import engine
from app.models.base import Base
import app.models  # noqa: F401


if __name__ == "__main__":
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("DB reset done.")
