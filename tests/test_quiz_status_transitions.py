import pytest

from datalayer import (
    QUIZ_HIDDEN,
    QUIZ_STEP1,
    QUIZ_STEP2,
    QUIZ_STEP3,
    QUIZ_SOLUTIONS,
    is_valid_quiz_status_transition,
)


@pytest.mark.parametrize(
    "current_status, new_status",
    [
        (QUIZ_HIDDEN, QUIZ_STEP1),
        (QUIZ_STEP1, QUIZ_STEP2),
        (QUIZ_STEP2, QUIZ_STEP3),
        (QUIZ_STEP2, QUIZ_SOLUTIONS),
        (QUIZ_STEP3, QUIZ_SOLUTIONS),
        (QUIZ_SOLUTIONS, QUIZ_HIDDEN),
    ],
)
def test_forward_and_hide_transitions_are_allowed(current_status, new_status):
    assert is_valid_quiz_status_transition(current_status, new_status)


@pytest.mark.parametrize(
    "current_status, new_status",
    [
        (QUIZ_STEP2, QUIZ_STEP1),
        (QUIZ_STEP3, QUIZ_STEP2),
        (QUIZ_STEP3, QUIZ_STEP1),
        (QUIZ_SOLUTIONS, QUIZ_STEP3),
        (QUIZ_SOLUTIONS, QUIZ_STEP2),
        (QUIZ_SOLUTIONS, QUIZ_STEP1),
    ],
)
def test_backward_phase_transitions_are_rejected(current_status, new_status):
    assert not is_valid_quiz_status_transition(current_status, new_status)


def test_hiding_a_quiz_with_attempts_does_not_allow_restarting_it():
    assert not is_valid_quiz_status_transition(
        QUIZ_HIDDEN, QUIZ_STEP1, has_attempts=True
    )


def test_hidden_quiz_without_attempts_can_start():
    assert is_valid_quiz_status_transition(
        QUIZ_HIDDEN, QUIZ_STEP1, has_attempts=False
    )


def test_repeating_the_current_status_is_allowed():
    assert is_valid_quiz_status_transition(QUIZ_STEP2, QUIZ_STEP2)


def test_unknown_statuses_are_rejected():
    assert not is_valid_quiz_status_transition("UNKNOWN", QUIZ_STEP1)
    assert not is_valid_quiz_status_transition(QUIZ_STEP1, "UNKNOWN")
