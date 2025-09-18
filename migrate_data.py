# migrate_data.py
import os
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from app import create_app, db
from app.models import ServiceStandard, ServiceArrangement, ServiceContract  # import your models
from dotenv import load_dotenv


load_dotenv()


def engine(url): 
    return create_engine(url, pool_pre_ping=True, future=True)


def copy_table(Model, s_src, s_dst, chunk=1000):
    # Build a streaming select; avoids loading all rows into memory
    stmt = (
        select(Model)
        .execution_options(stream_results=True, yield_per=chunk)
    )
    result = s_src.execute(stmt).scalars()
    buf = []
    cols = Model.__table__.columns
    for row in result:
        data = {
            c.name: getattr(row, c.name)
            for c in cols
            if not (c.primary_key and c.autoincrement) and not c.server_default
        }
        buf.append(Model(**data))
        if len(buf) >= chunk:
            s_dst.add_all(buf)
            s_dst.commit()
            buf.clear()
    if buf:
        s_dst.add_all(buf)
        s_dst.commit()



if __name__ == "__main__":

    SQLITE_URL = "sqlite:///service_standards.db"
    AZURE_URL  = os.environ["DATABASE_URL"]

    app = create_app()

    with app.app_context():
        src_engine = engine(SQLITE_URL)
        dst_engine = engine(AZURE_URL)
        SrcSession = sessionmaker(bind=src_engine, future=True)
        DstSession = sessionmaker(bind=dst_engine, future=True)

        copy_table(ServiceStandard,  SrcSession, DstSession)
        copy_table(ServiceArrangement, SrcSession, DstSession)
        copy_table(ServiceContract, SrcSession, DstSession)
        print("Data copy complete.")

