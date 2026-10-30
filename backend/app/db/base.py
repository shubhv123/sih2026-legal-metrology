try:
    from sqlalchemy.orm import DeclarativeBase
except ImportError:
    class DeclarativeBase:
        pass


class Base(DeclarativeBase):
    pass
