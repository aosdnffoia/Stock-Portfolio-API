#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.auth.models import User
from app.core.security import get_password_hash
from app.config import settings
from sqlalchemy import select
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_demo_user():
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(User).where(User.email == settings.demo_user_email))
            existing_user = result.scalar_one_or_none()
            if existing_user:
                logger.info(f"Demo user already exists: {settings.demo_user_email}")
                return existing_user
            demo_user = User(
                email=settings.demo_user_email,
                hashed_password=get_password_hash(settings.demo_user_password),
                full_name="Demo User",
                is_active=True,
                is_superuser=False,
            )
            db.add(demo_user)
            await db.commit()
            await db.refresh(demo_user)
            logger.info(f"✓ Demo user created: {settings.demo_user_email}")
            logger.info(f"  Password: {settings.demo_user_password}")
            return demo_user
        except Exception as e:
            logger.error(f"Error seeding demo user: {e}")
            await db.rollback()
            raise

async def main():
    logger.info("Seeding demo user...")
    try:
        await seed_demo_user()
        logger.info("✓ Seeding complete!")
    except Exception as e:
        logger.error(f"✗ Seeding failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
