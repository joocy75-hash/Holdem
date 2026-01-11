"""Tests for snapshot serialization."""

import pytest
from datetime import datetime

from app.engine.snapshot import (
    SnapshotSerializer,
    ViewType,
    serialize_state,
    deserialize_state,
    create_player_view,
    create_spectator_view,
)
from app.engine.state import (
    Card,
    Rank,
    Suit,
    Player,
    SeatState,
    SeatStatus,
    TableConfig,
    TableState,
    HandState,
    PlayerHandState,
    PlayerHandStatus,
    PotState,
    GamePhase,
    ValidAction,
    ActionType,
)


@pytest.fixture
def sample_config() -> TableConfig:
    """Create sample table config."""
    return TableConfig(
        max_seats=6,
        small_blind=10,
        big_blind=20,
        min_buy_in=400,
        max_buy_in=2000,
    )


@pytest.fixture
def sample_state(sample_config: TableConfig) -> TableState:
    """Create sample table state with hand."""
    player1 = Player(user_id="user1", nickname="Player1")
    player2 = Player(user_id="user2", nickname="Player2")

    seats = (
        SeatState(position=0, player=player1, stack=950, status=SeatStatus.ACTIVE),
        SeatState(position=1, player=player2, stack=970, status=SeatStatus.ACTIVE),
        SeatState(position=2, player=None, stack=0, status=SeatStatus.EMPTY),
    )

    hand = HandState(
        hand_id="hand-1",
        hand_number=1,
        phase=GamePhase.FLOP,
        community_cards=(
            Card(Rank.ACE, Suit.HEARTS),
            Card(Rank.KING, Suit.DIAMONDS),
            Card(Rank.QUEEN, Suit.CLUBS),
        ),
        pot=PotState(main_pot=80),
        player_states=(
            PlayerHandState(
                position=0,
                hole_cards=(Card(Rank.ACE, Suit.SPADES), Card(Rank.ACE, Suit.DIAMONDS)),
                bet_amount=0,
                total_bet=30,
                status=PlayerHandStatus.ACTIVE,
                last_action=None,
            ),
            PlayerHandState(
                position=1,
                hole_cards=(Card(Rank.KING, Suit.HEARTS), Card(Rank.KING, Suit.CLUBS)),
                bet_amount=0,
                total_bet=50,
                status=PlayerHandStatus.ACTIVE,
                last_action=None,
            ),
        ),
        current_turn=0,
        last_aggressor=1,
        min_raise=40,
        started_at=datetime.utcnow(),
    )

    return TableState(
        table_id="table-1",
        config=sample_config,
        seats=seats,
        hand=hand,
        dealer_position=0,
        state_version=5,
        updated_at=datetime.utcnow(),
    )


class TestSnapshotSerializer:
    """Tests for SnapshotSerializer."""

    def test_serialize_basic(self, sample_state: TableState):
        """Test basic serialization."""
        serializer = SnapshotSerializer()
        data = serializer.serialize(sample_state)

        assert data["tableId"] == "table-1"
        assert data["stateVersion"] == 5
        assert data["dealerPosition"] == 0
        assert data["config"]["smallBlind"] == 10
        assert data["config"]["bigBlind"] == 20
        assert len(data["seats"]) == 3

    def test_serialize_hand(self, sample_state: TableState):
        """Test hand serialization."""
        serializer = SnapshotSerializer()
        data = serializer.serialize(sample_state)

        hand = data["hand"]
        assert hand["handId"] == "hand-1"
        assert hand["phase"] == "flop"
        assert len(hand["communityCards"]) == 3
        assert hand["communityCards"][0] == "Ah"
        assert hand["pot"]["mainPot"] == 80

    def test_deserialize_roundtrip(self, sample_state: TableState):
        """Test serialize then deserialize produces equivalent state."""
        serializer = SnapshotSerializer()
        data = serializer.serialize(sample_state)
        restored = serializer.deserialize(data)

        assert restored.table_id == sample_state.table_id
        assert restored.state_version == sample_state.state_version
        assert restored.config.small_blind == sample_state.config.small_blind
        assert len(restored.seats) == len(sample_state.seats)

        # Hand should be restored
        assert restored.hand is not None
        assert restored.hand.hand_id == sample_state.hand.hand_id
        assert restored.hand.phase == sample_state.hand.phase

        # Community cards should match
        assert len(restored.hand.community_cards) == len(
            sample_state.hand.community_cards
        )
        for i, card in enumerate(restored.hand.community_cards):
            original = sample_state.hand.community_cards[i]
            assert card.rank == original.rank
            assert card.suit == original.suit

    def test_create_player_snapshot(self, sample_state: TableState):
        """Test player snapshot shows only their cards."""
        serializer = SnapshotSerializer()

        # Player 1 view
        snapshot = serializer.create_player_snapshot(sample_state, "user1")

        assert snapshot["myPosition"] == 0
        assert snapshot["myHoleCards"] is not None
        assert len(snapshot["myHoleCards"]) == 2
        assert snapshot["viewType"] == "player"

        # Other player's cards should be masked
        for ps in snapshot["hand"]["playerStates"]:
            if ps["position"] == 0:
                # Own cards visible in playerStates too
                assert ps["holeCards"] is not None
            else:
                # Other player's cards masked
                assert ps["holeCards"] is None

    def test_create_spectator_snapshot(self, sample_state: TableState):
        """Test spectator snapshot hides all hole cards."""
        serializer = SnapshotSerializer()
        snapshot = serializer.create_spectator_snapshot(sample_state)

        assert snapshot["myPosition"] is None
        assert snapshot["myHoleCards"] is None
        assert snapshot["viewType"] == "spectator"

        # All hole cards should be masked
        for ps in snapshot["hand"]["playerStates"]:
            assert ps["holeCards"] is None

    def test_spectator_view_for_unseated_player(self, sample_state: TableState):
        """Test that unseated player gets spectator view."""
        serializer = SnapshotSerializer()

        # Unknown user gets spectator view
        snapshot = serializer.create_player_snapshot(sample_state, "unknown-user")

        assert snapshot["myPosition"] is None
        assert snapshot["viewType"] == "spectator"

    def test_create_admin_snapshot(self, sample_state: TableState):
        """Test admin snapshot shows all cards."""
        serializer = SnapshotSerializer()
        snapshot = serializer.create_admin_snapshot(sample_state)

        assert snapshot["viewType"] == "admin"

        # All hole cards should be visible
        for ps in snapshot["hand"]["playerStates"]:
            assert ps["holeCards"] is not None


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_serialize_state(self, sample_state: TableState):
        """Test serialize_state convenience function."""
        data = serialize_state(sample_state)
        assert data["tableId"] == "table-1"

    def test_deserialize_state(self, sample_state: TableState):
        """Test deserialize_state convenience function."""
        data = serialize_state(sample_state)
        restored = deserialize_state(data)
        assert restored.table_id == "table-1"

    def test_create_player_view(self, sample_state: TableState):
        """Test create_player_view convenience function."""
        view = create_player_view(sample_state, "user1")
        assert view["myPosition"] == 0

    def test_create_spectator_view(self, sample_state: TableState):
        """Test create_spectator_view convenience function."""
        view = create_spectator_view(sample_state)
        assert view["viewType"] == "spectator"


class TestSerializationEdgeCases:
    """Tests for edge cases in serialization."""

    def test_serialize_no_hand(self, sample_config: TableConfig):
        """Test serializing state without active hand."""
        seats = (
            SeatState(
                position=0,
                player=Player(user_id="user1", nickname="P1"),
                stack=1000,
                status=SeatStatus.WAITING,
            ),
        )

        state = TableState(
            table_id="table-1",
            config=sample_config,
            seats=seats,
            hand=None,
            dealer_position=0,
            state_version=0,
            updated_at=datetime.utcnow(),
        )

        serializer = SnapshotSerializer()
        data = serializer.serialize(state)

        assert data["hand"] is None

        # Roundtrip
        restored = serializer.deserialize(data)
        assert restored.hand is None

    def test_serialize_empty_community_cards(self, sample_config: TableConfig):
        """Test serializing preflop state with no community cards."""
        player1 = Player(user_id="user1", nickname="Player1")

        hand = HandState(
            hand_id="hand-1",
            hand_number=1,
            phase=GamePhase.PREFLOP,
            community_cards=(),  # Empty
            pot=PotState(main_pot=30),
            player_states=(
                PlayerHandState(
                    position=0,
                    hole_cards=(
                        Card(Rank.ACE, Suit.SPADES),
                        Card(Rank.ACE, Suit.DIAMONDS),
                    ),
                    bet_amount=20,
                    total_bet=20,
                    status=PlayerHandStatus.ACTIVE,
                    last_action=None,
                ),
            ),
            current_turn=0,
            last_aggressor=None,
            min_raise=40,
            started_at=datetime.utcnow(),
        )

        state = TableState(
            table_id="table-1",
            config=sample_config,
            seats=(
                SeatState(
                    position=0, player=player1, stack=980, status=SeatStatus.ACTIVE
                ),
            ),
            hand=hand,
            dealer_position=0,
            state_version=1,
            updated_at=datetime.utcnow(),
        )

        serializer = SnapshotSerializer()
        data = serializer.serialize(state)

        assert data["hand"]["communityCards"] == []

        # Roundtrip
        restored = serializer.deserialize(data)
        assert len(restored.hand.community_cards) == 0

    def test_serialize_with_side_pots(self, sample_config: TableConfig):
        """Test serializing state with side pots."""
        from app.engine.state import SidePot

        player1 = Player(user_id="user1", nickname="Player1")

        hand = HandState(
            hand_id="hand-1",
            hand_number=1,
            phase=GamePhase.RIVER,
            community_cards=(
                Card(Rank.ACE, Suit.HEARTS),
                Card(Rank.KING, Suit.DIAMONDS),
                Card(Rank.QUEEN, Suit.CLUBS),
                Card(Rank.JACK, Suit.SPADES),
                Card(Rank.TEN, Suit.HEARTS),
            ),
            pot=PotState(
                main_pot=300,
                side_pots=(
                    SidePot(amount=200, eligible_positions=(0, 1)),
                    SidePot(amount=100, eligible_positions=(0,)),
                ),
            ),
            player_states=(
                PlayerHandState(
                    position=0,
                    hole_cards=(
                        Card(Rank.ACE, Suit.SPADES),
                        Card(Rank.ACE, Suit.DIAMONDS),
                    ),
                    bet_amount=0,
                    total_bet=300,
                    status=PlayerHandStatus.ALL_IN,
                    last_action=None,
                ),
            ),
            current_turn=None,
            last_aggressor=0,
            min_raise=0,
            started_at=datetime.utcnow(),
        )

        state = TableState(
            table_id="table-1",
            config=sample_config,
            seats=(
                SeatState(
                    position=0, player=player1, stack=0, status=SeatStatus.ACTIVE
                ),
            ),
            hand=hand,
            dealer_position=0,
            state_version=10,
            updated_at=datetime.utcnow(),
        )

        serializer = SnapshotSerializer()
        data = serializer.serialize(state)

        assert data["hand"]["pot"]["mainPot"] == 300
        assert len(data["hand"]["pot"]["sidePots"]) == 2
        assert data["hand"]["pot"]["total"] == 600

        # Roundtrip
        restored = serializer.deserialize(data)
        assert restored.hand.pot.main_pot == 300
        assert len(restored.hand.pot.side_pots) == 2
