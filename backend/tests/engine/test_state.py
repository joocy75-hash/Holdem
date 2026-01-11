"""Tests for engine state models."""

import pytest
from datetime import datetime

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
    SidePot,
    GamePhase,
    ActionType,
    ActionRequest,
    ValidAction,
)


class TestCard:
    """Tests for Card model."""

    def test_card_creation(self):
        """Test creating a card."""
        card = Card(rank=Rank.ACE, suit=Suit.HEARTS)
        assert card.rank == Rank.ACE
        assert card.suit == Suit.HEARTS

    def test_card_string(self):
        """Test card string representation."""
        card = Card(rank=Rank.ACE, suit=Suit.HEARTS)
        assert str(card) == "Ah"

        card2 = Card(rank=Rank.TEN, suit=Suit.CLUBS)
        assert str(card2) == "Tc"

    def test_card_from_string(self):
        """Test parsing card from string."""
        card = Card.from_string("Ah")
        assert card.rank == Rank.ACE
        assert card.suit == Suit.HEARTS

        card2 = Card.from_string("2c")
        assert card2.rank == Rank.TWO
        assert card2.suit == Suit.CLUBS

        card3 = Card.from_string("Td")
        assert card3.rank == Rank.TEN
        assert card3.suit == Suit.DIAMONDS

    def test_card_from_string_case_insensitive(self):
        """Test card parsing is case-insensitive for suit."""
        card = Card.from_string("AH")
        assert card.suit == Suit.HEARTS

    def test_card_from_string_invalid(self):
        """Test invalid card string raises error."""
        with pytest.raises(ValueError):
            Card.from_string("XY")

        with pytest.raises(ValueError):
            Card.from_string("A")

        with pytest.raises(ValueError):
            Card.from_string("Ahh")

    def test_card_immutable(self):
        """Test card is immutable."""
        card = Card(rank=Rank.ACE, suit=Suit.HEARTS)
        with pytest.raises(AttributeError):
            card.rank = Rank.KING


class TestRank:
    """Tests for Rank enum."""

    def test_rank_values(self):
        """Test rank numeric values."""
        assert Rank.TWO.value == 2
        assert Rank.ACE.value == 14

    def test_rank_symbols(self):
        """Test rank symbols."""
        assert Rank.TEN.symbol == "T"
        assert Rank.JACK.symbol == "J"
        assert Rank.ACE.symbol == "A"

    def test_rank_from_symbol(self):
        """Test rank from symbol."""
        assert Rank.from_symbol("A") == Rank.ACE
        assert Rank.from_symbol("t") == Rank.TEN  # Case insensitive
        assert Rank.from_symbol("2") == Rank.TWO


class TestSuit:
    """Tests for Suit enum."""

    def test_suit_symbols(self):
        """Test suit symbols."""
        assert Suit.HEARTS.symbol == "h"
        assert Suit.SPADES.symbol == "s"

    def test_suit_unicode(self):
        """Test suit unicode symbols."""
        assert Suit.HEARTS.unicode == "♥"
        assert Suit.SPADES.unicode == "♠"

    def test_suit_from_symbol(self):
        """Test suit from symbol."""
        assert Suit.from_symbol("h") == Suit.HEARTS
        assert Suit.from_symbol("S") == Suit.SPADES  # Case insensitive


class TestTableConfig:
    """Tests for TableConfig."""

    def test_valid_config(self):
        """Test valid table configuration."""
        config = TableConfig(
            max_seats=6,
            small_blind=10,
            big_blind=20,
            min_buy_in=400,
            max_buy_in=2000,
        )
        assert config.max_seats == 6
        assert config.small_blind == 10
        assert config.big_blind == 20
        assert config.turn_timeout_seconds == 30  # Default
        assert config.ante == 0  # Default

    def test_config_validation_max_seats(self):
        """Test max_seats validation."""
        with pytest.raises(ValueError, match="max_seats must be 2-9"):
            TableConfig(
                max_seats=1,
                small_blind=10,
                big_blind=20,
                min_buy_in=400,
                max_buy_in=2000,
            )

        with pytest.raises(ValueError, match="max_seats must be 2-9"):
            TableConfig(
                max_seats=10,
                small_blind=10,
                big_blind=20,
                min_buy_in=400,
                max_buy_in=2000,
            )

    def test_config_validation_blinds(self):
        """Test blind validation."""
        with pytest.raises(ValueError, match="small_blind must be positive"):
            TableConfig(
                max_seats=6,
                small_blind=0,
                big_blind=20,
                min_buy_in=400,
                max_buy_in=2000,
            )

        with pytest.raises(ValueError, match="small_blind must be less than big_blind"):
            TableConfig(
                max_seats=6,
                small_blind=20,
                big_blind=10,
                min_buy_in=400,
                max_buy_in=2000,
            )


class TestPotState:
    """Tests for PotState."""

    def test_pot_total(self):
        """Test pot total calculation."""
        pot = PotState(main_pot=100)
        assert pot.total == 100

        pot_with_sides = PotState(
            main_pot=100,
            side_pots=(
                SidePot(amount=50, eligible_positions=(0, 1)),
                SidePot(amount=30, eligible_positions=(0,)),
            ),
        )
        assert pot_with_sides.total == 180


class TestTableState:
    """Tests for TableState."""

    def test_table_state_creation(self):
        """Test creating table state."""
        config = TableConfig(
            max_seats=6,
            small_blind=10,
            big_blind=20,
            min_buy_in=400,
            max_buy_in=2000,
        )

        player1 = Player(user_id="user1", nickname="Player1")
        player2 = Player(user_id="user2", nickname="Player2")

        seats = (
            SeatState(position=0, player=player1, stack=1000, status=SeatStatus.ACTIVE),
            SeatState(position=1, player=player2, stack=1000, status=SeatStatus.ACTIVE),
            SeatState(position=2, player=None, stack=0, status=SeatStatus.EMPTY),
            SeatState(position=3, player=None, stack=0, status=SeatStatus.EMPTY),
            SeatState(position=4, player=None, stack=0, status=SeatStatus.EMPTY),
            SeatState(position=5, player=None, stack=0, status=SeatStatus.EMPTY),
        )

        state = TableState(
            table_id="table-1",
            config=config,
            seats=seats,
            hand=None,
            dealer_position=0,
            state_version=0,
            updated_at=datetime.utcnow(),
        )

        assert state.table_id == "table-1"
        assert len(state.seats) == 6
        assert state.hand is None

    def test_get_active_seats(self):
        """Test getting active seats."""
        config = TableConfig(
            max_seats=6,
            small_blind=10,
            big_blind=20,
            min_buy_in=400,
            max_buy_in=2000,
        )

        player1 = Player(user_id="user1", nickname="Player1")
        player2 = Player(user_id="user2", nickname="Player2")

        seats = (
            SeatState(position=0, player=player1, stack=1000, status=SeatStatus.ACTIVE),
            SeatState(position=1, player=player2, stack=1000, status=SeatStatus.ACTIVE),
            SeatState(position=2, player=None, stack=0, status=SeatStatus.EMPTY),
        )

        state = TableState(
            table_id="table-1",
            config=config,
            seats=seats,
            hand=None,
            dealer_position=0,
            state_version=0,
            updated_at=datetime.utcnow(),
        )

        active = state.get_active_seats()
        assert len(active) == 2
        assert active[0].position == 0
        assert active[1].position == 1

    def test_state_immutable(self):
        """Test state is immutable."""
        config = TableConfig(
            max_seats=6,
            small_blind=10,
            big_blind=20,
            min_buy_in=400,
            max_buy_in=2000,
        )

        state = TableState(
            table_id="table-1",
            config=config,
            seats=(),
            hand=None,
            dealer_position=0,
            state_version=0,
            updated_at=datetime.utcnow(),
        )

        with pytest.raises(AttributeError):
            state.state_version = 1

    def test_increment_version(self):
        """Test version increment creates new state."""
        config = TableConfig(
            max_seats=6,
            small_blind=10,
            big_blind=20,
            min_buy_in=400,
            max_buy_in=2000,
        )

        state = TableState(
            table_id="table-1",
            config=config,
            seats=(),
            hand=None,
            dealer_position=0,
            state_version=0,
            updated_at=datetime.utcnow(),
        )

        new_state = state.increment_version()
        assert new_state.state_version == 1
        assert state.state_version == 0  # Original unchanged


class TestActionRequest:
    """Tests for ActionRequest."""

    def test_action_request_creation(self):
        """Test creating action request."""
        action = ActionRequest(
            request_id="req-1",
            action_type=ActionType.CALL,
        )
        assert action.request_id == "req-1"
        assert action.action_type == ActionType.CALL
        assert action.amount is None

    def test_action_request_with_amount(self):
        """Test action request with amount."""
        action = ActionRequest(
            request_id="req-1",
            action_type=ActionType.RAISE,
            amount=100,
        )
        assert action.amount == 100


class TestValidAction:
    """Tests for ValidAction."""

    def test_valid_action_fold(self):
        """Test fold action."""
        action = ValidAction(action_type=ActionType.FOLD)
        assert action.action_type == ActionType.FOLD
        assert action.min_amount is None
        assert action.max_amount is None

    def test_valid_action_raise(self):
        """Test raise action with amount range."""
        action = ValidAction(
            action_type=ActionType.RAISE,
            min_amount=40,
            max_amount=1000,
        )
        assert action.min_amount == 40
        assert action.max_amount == 1000
