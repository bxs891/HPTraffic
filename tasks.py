import os
from datetime import datetime, timedelta

from celery import Celery
from sqlalchemy import and_, create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from models import Base, Lead, Message
from notify_telegram import TelegramNotifier

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///hptrafic.db")

celery_app = Celery("hptraffic", broker=CELERY_BROKER_URL)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _ensure_tables() -> None:
    Base.metadata.create_all(bind=engine)


@celery_app.task(name="notify_high_priority_leads")
def notify_high_priority_leads() -> dict[str, int]:
    """
    拉取过去 1 小时 P0/P1 且未通知过的 leads，并通过 Telegram 发送。
    通过 messages(lead_id, channel) 唯一约束保证幂等。
    """
    _ensure_tables()
    notifier = TelegramNotifier()
    window_start = datetime.utcnow() - timedelta(hours=1)

    sent_count = 0
    skipped_count = 0

    with SessionLocal() as db:  # type: Session
        stmt = (
            select(Lead)
            .outerjoin(
                Message,
                and_(Message.lead_id == Lead.id, Message.channel == "telegram"),
            )
            .where(
                Lead.created_at >= window_start,
                Lead.priority.in_(["P0", "P1"]),
                Message.id.is_(None),
            )
            .order_by(Lead.created_at.asc())
        )

        candidates = db.scalars(stmt).all()

        for lead in candidates:
            try:
                telegram_resp = notifier.send_lead(
                    {
                        "source": lead.source,
                        "title": lead.title,
                        "summary": lead.summary,
                        "score": lead.score,
                        "priority": lead.priority,
                        "url": lead.url,
                        "reply_points": lead.reply_points,
                    }
                )

                msg = Message(
                    lead_id=lead.id,
                    channel="telegram",
                    external_message_id=str(telegram_resp.get("result", {}).get("message_id", "")),
                )
                db.add(msg)
                db.commit()
                sent_count += 1
            except IntegrityError:
                db.rollback()
                skipped_count += 1

    return {"sent": sent_count, "skipped": skipped_count}
