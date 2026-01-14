"""Unit tests for HandEvaluator module.

Tests all hand rankings, preflop strength evaluation, and draw detection.
Validates Requirements 10.2 from code-quality-security-upgrade spec.
"""

import pytest
from app.game.hand_evaluator import (
    HandRank,
    HandStrength,
    parse_card,
    get_rank_value,
    evaluate_preflop_strength,
    evaluate_postflop_strength,
    evaluate_hand_for_bot,
    _find_straight,
    _check_straight_draw,
)


# =============================================================================
# Card Parsing Tests
# =============================================================================


class TestCardParsing:
    """Tests for card parsing utilities."""

    def test_parse_card_standard(self):
        """Test parsing standard card format."""
        rank, suit = parse_card("As")
        assert rank == "A"
        assert suit == "s"

    def test_parse_card_ten(self):
        """Test parsing 10 card format."""
        rank, suit = parse_card("10h")
        assert rank == "T"
        assert suit == "h"

    def test_parse_card_lowercase(self):
        """Test parsing lowercase rank."""
        rank, suit = parse_card("kd")
        assert rank == "K"
        assert suit == "d"

    def test_get_rank_value(self):
        """Test rank value mapping."""
        assert get_rank_value("2") == 2
        assert get_rank_value("T") == 10
        assert get_rank_value("J") == 11
        assert get_rank_value("Q") == 12
        assert get_rank_value("K") == 13
        assert get_rank_value("A") == 14


# =============================================================================
# Preflop Strength Tests
# =============================================================================


class TestPreflopStrength:
    """Tests for preflop hand strength evaluation."""

    def test_pocket_aces(self):
        """Test pocket aces is strongest."""
        strength = evaluate_preflop_strength(["As", "Ah"])
        assert strength >= 0.95

    def test_pocket_kings(self):
        """Test pocket kings is very strong."""
        strength = evaluate_preflop_strength(["Ks", "Kh"])
        assert strength >= 0.90

    def test_pocket_twos(self):
        """Test pocket twos is moderate."""
        strength = evaluate_preflop_strength(["2s", "2h"])
        assert 0.45 <= strength <= 0.60

    def test_suited_ace_king(self):
        """Test suited AK is premium."""
        strength = evaluate_preflop_strength(["As", "Ks"])
        assert strength >= 0.85

    def test_offsuit_ace_king(self):
        """Test offsuit AK is strong."""
        strength = evaluate_preflop_strength(["As", "Kh"])
        assert strength >= 0.75

    def test_suited_connectors(self):
        """Test suited connectors have decent strength."""
        strength = evaluate_preflop_strength(["9s", "8s"])
        assert strength >= 0.40

    def test_trash_hand(self):
        """Test trash hand is weak."""
        strength = evaluate_preflop_strength(["7h", "2c"])
        assert strength <= 0.35

    def test_suited_ace_rag(self):
        """Test suited Ax is playable."""
        strength = evaluate_preflop_strength(["As", "5s"])
        assert strength >= 0.45

    def test_empty_cards(self):
        """Test empty cards returns default."""
        strength = evaluate_preflop_strength([])
        assert strength == 0.3

    def test_invalid_cards(self):
        """Test single card returns default."""
        strength = evaluate_preflop_strength(["As"])
        assert strength == 0.3


# =============================================================================
# Postflop Hand Ranking Tests
# =============================================================================


class TestPostflopHandRanking:
    """Tests for postflop hand ranking evaluation."""

    def test_royal_flush(self):
        """Test royal flush detection."""
        result = evaluate_postflop_strength(
            ["As", "Ks"],
            ["Qs", "Js", "Ts"]
        )
        assert result.rank == HandRank.ROYAL_FLUSH
        assert result.strength == 1.0

    def test_straight_flush(self):
        """Test straight flush detection."""
        result = evaluate_postflop_strength(
            ["9s", "8s"],
            ["7s", "6s", "5s"]
        )
        assert result.rank == HandRank.STRAIGHT_FLUSH
        assert result.strength >= 0.95

    def test_four_of_a_kind(self):
        """Test four of a kind detection."""
        result = evaluate_postflop_strength(
            ["As", "Ah"],
            ["Ad", "Ac", "Ks"]
        )
        assert result.rank == HandRank.FOUR_OF_A_KIND
        assert result.strength >= 0.90

    def test_full_house(self):
        """Test full house detection."""
        result = evaluate_postflop_strength(
            ["As", "Ah"],
            ["Ad", "Ks", "Kh"]
        )
        assert result.rank == HandRank.FULL_HOUSE
        assert result.strength >= 0.85

    def test_flush(self):
        """Test flush detection."""
        result = evaluate_postflop_strength(
            ["As", "7s"],
            ["Ks", "9s", "2s"]
        )
        assert result.rank == HandRank.FLUSH
        assert result.strength >= 0.80

    def test_straight(self):
        """Test straight detection."""
        result = evaluate_postflop_strength(
            ["9h", "8c"],
            ["7d", "6s", "5h"]
        )
        assert result.rank == HandRank.STRAIGHT
        assert result.strength >= 0.70

    def test_wheel_straight(self):
        """Test A-2-3-4-5 (wheel) straight."""
        result = evaluate_postflop_strength(
            ["As", "2h"],
            ["3d", "4c", "5s"]
        )
        assert result.rank == HandRank.STRAIGHT

    def test_three_of_a_kind(self):
        """Test three of a kind detection."""
        result = evaluate_postflop_strength(
            ["As", "Ah"],
            ["Ad", "Ks", "Qh"]
        )
        assert result.rank == HandRank.THREE_OF_A_KIND
        assert result.strength >= 0.60

    def test_two_pair(self):
        """Test two pair detection."""
        result = evaluate_postflop_strength(
            ["As", "Kh"],
            ["Ad", "Ks", "Qh"]
        )
        assert result.rank == HandRank.TWO_PAIR
        assert result.strength >= 0.50

    def test_one_pair(self):
        """Test one pair detection."""
        result = evaluate_postflop_strength(
            ["As", "Kh"],
            ["Ad", "Qs", "Jh"]
        )
        assert result.rank == HandRank.ONE_PAIR
        assert result.strength >= 0.35

    def test_top_pair(self):
        """Test top pair has higher strength."""
        top_pair = evaluate_postflop_strength(
            ["As", "Kh"],
            ["Ad", "Qs", "Jh"]
        )
        bottom_pair = evaluate_postflop_strength(
            ["Jh", "2c"],
            ["Ad", "Qs", "Jd"]
        )
        assert top_pair.strength > bottom_pair.strength

    def test_high_card(self):
        """Test high card detection."""
        result = evaluate_postflop_strength(
            ["As", "Kh"],
            ["Qd", "Js", "9h"]
        )
        assert result.rank == HandRank.HIGH_CARD
        assert result.strength <= 0.30


# =============================================================================
# Draw Detection Tests
# =============================================================================


class TestDrawDetection:
    """Tests for draw detection."""

    def test_flush_draw(self):
        """Test flush draw detection."""
        result = evaluate_postflop_strength(
            ["As", "Ks"],
            ["Qs", "Jh", "2s"]
        )
        assert result.has_flush_draw is True

    def test_no_flush_draw(self):
        """Test no flush draw when not applicable."""
        result = evaluate_postflop_strength(
            ["As", "Kh"],
            ["Qd", "Jc", "2s"]
        )
        assert result.has_flush_draw is False

    def test_open_ended_straight_draw(self):
        """Test open-ended straight draw detection."""
        values = [9, 8, 7, 6, 2]
        assert _check_straight_draw(values) is True

    def test_gutshot_straight_draw(self):
        """Test gutshot straight draw detection."""
        values = [9, 8, 6, 5, 2]
        assert _check_straight_draw(values) is True

    def test_no_straight_draw(self):
        """Test no straight draw."""
        # Values that are too spread out for any draw
        values = [14, 10, 6, 3, 2]
        assert _check_straight_draw(values) is False


# =============================================================================
# Straight Finding Tests
# =============================================================================


class TestStraightFinding:
    """Tests for straight finding utility."""

    def test_find_straight_broadway(self):
        """Test finding broadway straight."""
        values = [14, 13, 12, 11, 10]
        assert _find_straight(values) == 14

    def test_find_straight_wheel(self):
        """Test finding wheel straight."""
        values = [14, 5, 4, 3, 2]
        assert _find_straight(values) == 5

    def test_find_straight_middle(self):
        """Test finding middle straight."""
        values = [9, 8, 7, 6, 5]
        assert _find_straight(values) == 9

    def test_no_straight(self):
        """Test no straight found."""
        values = [14, 10, 7, 4, 2]
        assert _find_straight(values) is None


# =============================================================================
# Bot Evaluation Tests
# =============================================================================


class TestBotEvaluation:
    """Tests for bot hand evaluation."""

    def test_evaluate_hand_for_bot_preflop(self):
        """Test bot evaluation at preflop."""
        result = evaluate_hand_for_bot(
            hole_cards=["As", "Ah"],
            community_cards=[],
            pot=30,
            to_call=20,
        )
        
        assert result["phase"] == "preflop"
        assert result["strength"] >= 0.90
        assert "recommendation" in result

    def test_evaluate_hand_for_bot_postflop(self):
        """Test bot evaluation at postflop."""
        result = evaluate_hand_for_bot(
            hole_cards=["As", "Kh"],
            community_cards=["Ad", "Qs", "Jh"],
            pot=100,
            to_call=50,
        )
        
        assert result["phase"] == "postflop"
        assert result["rank"] == HandRank.ONE_PAIR
        assert "recommendation" in result

    def test_bot_recommendation_strong_hand(self):
        """Test bot recommends raise with strong hand."""
        result = evaluate_hand_for_bot(
            hole_cards=["As", "Ah"],
            community_cards=["Ad", "Ks", "Qh"],
            pot=100,
            to_call=20,
        )
        
        assert result["recommendation"] in ["raise", "bet"]

    def test_bot_recommendation_weak_hand(self):
        """Test bot recommends fold with weak hand."""
        result = evaluate_hand_for_bot(
            hole_cards=["7h", "2c"],
            community_cards=["Ad", "Ks", "Qh"],
            pot=100,
            to_call=50,
        )
        
        assert result["recommendation"] in ["fold", "check"]

    def test_bot_recommendation_check_available(self):
        """Test bot recommends check when no bet."""
        result = evaluate_hand_for_bot(
            hole_cards=["7h", "2c"],
            community_cards=["Ad", "Ks", "Qh"],
            pot=100,
            to_call=0,
        )
        
        assert result["recommendation"] == "check"

    def test_pot_odds_calculation(self):
        """Test pot odds are calculated correctly."""
        result = evaluate_hand_for_bot(
            hole_cards=["As", "Kh"],
            community_cards=["Qd", "Js", "9h"],
            pot=100,
            to_call=25,
        )
        
        # pot_odds = 25 / (100 + 25) = 0.2
        assert abs(result["pot_odds"] - 0.2) < 0.01


# =============================================================================
# Hand Strength Dataclass Tests
# =============================================================================


class TestHandStrengthDataclass:
    """Tests for HandStrength dataclass."""

    def test_hand_strength_creation(self):
        """Test creating HandStrength object."""
        hs = HandStrength(
            rank=HandRank.FLUSH,
            strength=0.85,
            has_flush_draw=False,
            has_straight_draw=False,
            description="플러시 A 하이"
        )
        
        assert hs.rank == HandRank.FLUSH
        assert hs.strength == 0.85
        assert hs.description == "플러시 A 하이"

    def test_hand_strength_defaults(self):
        """Test HandStrength default values."""
        hs = HandStrength(
            rank=HandRank.HIGH_CARD,
            strength=0.2,
        )
        
        assert hs.has_flush_draw is False
        assert hs.has_straight_draw is False
        assert hs.description == ""


# =============================================================================
# Hand Rank Enum Tests
# =============================================================================


class TestHandRankEnum:
    """Tests for HandRank enum."""

    def test_hand_rank_ordering(self):
        """Test hand ranks are ordered correctly."""
        assert HandRank.HIGH_CARD < HandRank.ONE_PAIR
        assert HandRank.ONE_PAIR < HandRank.TWO_PAIR
        assert HandRank.TWO_PAIR < HandRank.THREE_OF_A_KIND
        assert HandRank.THREE_OF_A_KIND < HandRank.STRAIGHT
        assert HandRank.STRAIGHT < HandRank.FLUSH
        assert HandRank.FLUSH < HandRank.FULL_HOUSE
        assert HandRank.FULL_HOUSE < HandRank.FOUR_OF_A_KIND
        assert HandRank.FOUR_OF_A_KIND < HandRank.STRAIGHT_FLUSH
        assert HandRank.STRAIGHT_FLUSH < HandRank.ROYAL_FLUSH

    def test_hand_rank_values(self):
        """Test hand rank integer values."""
        assert HandRank.HIGH_CARD == 1
        assert HandRank.ROYAL_FLUSH == 10


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_community_cards(self):
        """Test evaluation with empty community cards."""
        result = evaluate_postflop_strength(
            ["As", "Kh"],
            []
        )
        assert result.rank == HandRank.HIGH_CARD

    def test_empty_hole_cards(self):
        """Test evaluation with empty hole cards."""
        result = evaluate_postflop_strength(
            [],
            ["Ad", "Ks", "Qh"]
        )
        assert result.rank == HandRank.HIGH_CARD

    def test_seven_card_evaluation(self):
        """Test evaluation with 7 cards (2 hole + 5 community)."""
        result = evaluate_postflop_strength(
            ["As", "Kh"],
            ["Ad", "Ks", "Qh", "Jd", "Tc"]
        )
        # Should find best 5-card hand
        assert result.rank >= HandRank.TWO_PAIR

    def test_multiple_possible_straights(self):
        """Test finding highest straight when multiple possible."""
        result = evaluate_postflop_strength(
            ["9h", "8c"],
            ["7d", "6s", "5h", "4c", "3d"]
        )
        # Should find 9-high straight, not 7-high
        assert result.rank == HandRank.STRAIGHT
        assert "9" in result.description or result.strength > 0.75
