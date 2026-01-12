"""Query optimization utilities for 300-500 concurrent users.

Phase 3.2: N+1 쿼리 제거 및 배치 조회 최적화

Best Practices:
1. 관계 로딩: selectinload() 또는 joinedload() 사용
   - selectinload: 1:N 관계에서 효율적 (IN 절 사용)
   - joinedload: 1:1 관계에서 효율적 (JOIN 사용)

2. 배치 조회: 여러 ID로 조회할 때 IN 절 사용
   - 잘못된 예: for id in ids: await db.get(Model, id)
   - 올바른 예: select(Model).where(Model.id.in_(ids))

3. 페이지네이션: OFFSET + LIMIT 대신 Cursor 기반 고려
   - 대용량 테이블에서 OFFSET이 느려짐
   - Cursor 기반이 더 효율적

4. 쿼리 모니터링: echo=True로 실제 쿼리 확인
"""

from typing import TypeVar, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

T = TypeVar("T")


async def batch_get_by_ids(
    db: AsyncSession,
    model: type[T],
    ids: Sequence[str],
    load_relationships: list | None = None,
) -> dict[str, T]:
    """Batch get entities by IDs with optional relationship loading.

    N개 ID 조회 시 N개 쿼리 대신 1개 쿼리(IN 절)로 처리.

    Args:
        db: Database session
        model: SQLAlchemy model class
        ids: List of entity IDs
        load_relationships: Optional list of relationship attributes to eager load

    Returns:
        Dict mapping ID to entity

    Example:
        # Before (N+1 problem):
        for user_id in user_ids:
            user = await db.get(User, user_id)

        # After (single query):
        users = await batch_get_by_ids(db, User, user_ids)
    """
    if not ids:
        return {}

    # Build query with optional relationship loading
    query = select(model).where(model.id.in_(ids))

    if load_relationships:
        for rel in load_relationships:
            query = query.options(selectinload(rel))

    result = await db.execute(query)
    entities = result.scalars().all()

    return {entity.id: entity for entity in entities}


async def batch_get_with_related(
    db: AsyncSession,
    model: type[T],
    ids: Sequence[str],
    relationships: list,
) -> dict[str, T]:
    """Batch get entities with eager-loaded relationships.

    Args:
        db: Database session
        model: SQLAlchemy model class
        ids: List of entity IDs
        relationships: List of relationship attributes to eager load

    Returns:
        Dict mapping ID to entity with loaded relationships

    Example:
        rooms = await batch_get_with_related(
            db, Room, room_ids,
            relationships=[Room.owner, Room.tables]
        )
    """
    if not ids:
        return {}

    query = select(model).where(model.id.in_(ids))

    for rel in relationships:
        query = query.options(selectinload(rel))

    result = await db.execute(query)
    entities = result.scalars().all()

    return {entity.id: entity for entity in entities}


async def paginate_with_cursor(
    db: AsyncSession,
    query,
    cursor_column,
    cursor_value=None,
    limit: int = 20,
    descending: bool = True,
) -> tuple[list, str | None]:
    """Cursor-based pagination (more efficient than OFFSET).

    For large tables, cursor-based pagination is more efficient
    than OFFSET because it doesn't scan skipped rows.

    Args:
        db: Database session
        query: Base query
        cursor_column: Column to use as cursor
        cursor_value: Last seen cursor value (None for first page)
        limit: Page size
        descending: Sort direction

    Returns:
        Tuple of (entities, next_cursor)

    Example:
        # First page
        hands, cursor = await paginate_with_cursor(
            db, select(Hand), Hand.started_at, limit=20
        )

        # Next page
        more_hands, next_cursor = await paginate_with_cursor(
            db, select(Hand), Hand.started_at, cursor_value=cursor
        )
    """
    if descending:
        query = query.order_by(cursor_column.desc())
        if cursor_value is not None:
            query = query.where(cursor_column < cursor_value)
    else:
        query = query.order_by(cursor_column.asc())
        if cursor_value is not None:
            query = query.where(cursor_column > cursor_value)

    query = query.limit(limit + 1)  # Fetch one extra to determine if there's more

    result = await db.execute(query)
    entities = list(result.scalars().all())

    next_cursor = None
    if len(entities) > limit:
        entities = entities[:limit]
        last_entity = entities[-1]
        next_cursor = str(getattr(last_entity, cursor_column.key))

    return entities, next_cursor


def apply_eager_loading(query, *relationships):
    """Apply selectinload to multiple relationships.

    Args:
        query: SQLAlchemy query
        relationships: Relationship attributes to load

    Returns:
        Query with eager loading applied

    Example:
        query = apply_eager_loading(
            select(Room),
            Room.owner,
            Room.tables
        )
    """
    for rel in relationships:
        query = query.options(selectinload(rel))
    return query


def apply_joined_loading(query, *relationships):
    """Apply joinedload to multiple relationships.

    Use for 1:1 relationships where JOIN is more efficient.

    Args:
        query: SQLAlchemy query
        relationships: Relationship attributes to load

    Returns:
        Query with joined loading applied
    """
    for rel in relationships:
        query = query.options(joinedload(rel))
    return query
