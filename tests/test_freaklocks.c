#include "freaklocks.h"

#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>

static void test_stock_positions_and_default_probability(void) {
    fl_state state;
    fl_init(&state, 42);
    assert(!fl_on_step(&state, 0, 0, 64));
    assert(!fl_note_allowed(&state, true));
    assert(fl_transport(&state, FL_START));
    for (unsigned length = FL_MIN_LENGTH; length <= FL_STEPS; ++length) {
        for (unsigned pattern = 0; pattern < FL_PATTERNS; ++pattern) {
            for (unsigned step = 0; step < length; ++step) {
                assert(fl_on_step(&state, pattern, step, length));
                assert(fl_note_allowed(&state, true));
                assert(!fl_note_allowed(&state, false));
                assert(state.active_step == step && state.active_pattern == pattern);
            }
        }
    }
    /* A stock cursor jump is authoritative; the extension must not increment it. */
    assert(fl_on_step(&state, 0, 42, 64));
    assert(state.active_step == 42);
    assert(fl_on_step(&state, 0, 2, 64));
    assert(state.active_step == 2);
}

static void test_probability_cache_and_step_64(void) {
    fl_state state;
    fl_init(&state, 42);
    assert(fl_transport(&state, FL_START));
    assert(fl_set_probability(&state, 0, 63, 0));
    assert(fl_on_step(&state, 0, 63, 64));
    const uint32_t draw = state.random_state;
    for (unsigned i = 0; i < 100; ++i) assert(!fl_note_allowed(&state, true));
    assert(state.random_state == draw);
    assert(fl_set_probability(&state, 0, 63, 100));
    assert(!fl_note_allowed(&state, true));
    assert(fl_on_step(&state, 0, 63, 64));
    assert(fl_note_allowed(&state, true));
    assert(state.random_state != draw);
    assert(fl_on_step(&state, 1, 63, 64));
    assert(fl_note_allowed(&state, true));
    assert(state.probability[1][63] == 100);
    assert(!fl_note_allowed(&state, false));
}

static void test_seeded_probability_and_transport(void) {
    fl_state first, second;
    fl_init(&first, 42);
    fl_init(&second, 42);
    for (unsigned step = 0; step < FL_STEPS; ++step) {
        assert(fl_set_probability(&first, 0, step, 50));
        assert(fl_set_probability(&second, 0, step, 50));
    }
    assert(fl_transport(&first, FL_START) && fl_transport(&second, FL_START));
    unsigned hits = 0;
    unsigned golden = 0;
    for (unsigned i = 0; i < 100000; ++i) {
        assert(fl_on_step(&first, 0, i % FL_STEPS, FL_STEPS));
        assert(fl_on_step(&second, 0, i % FL_STEPS, FL_STEPS));
        const bool allowed = fl_note_allowed(&first, true);
        assert(allowed == fl_note_allowed(&second, true));
        if (allowed) ++hits;
        if (i < 16 && allowed) golden |= 1u << i;
    }
    assert(golden == 0x88fb && hits > 49000 && hits < 51000);
    const uint32_t before_stop = first.random_state;
    assert(fl_open_editor(&first, 0, 0, 64, false));
    assert(fl_transport(&first, FL_STOP));
    assert(!first.editor_open && !fl_note_allowed(&first, true));
    assert(!fl_on_step(&first, 0, 0, 64));
    assert(first.random_state == before_stop);
    assert(fl_transport(&first, FL_CONTINUE));
    assert(first.random_state == before_stop && !first.has_decision);
    assert(fl_transport(&first, FL_START));
    assert(first.random_state == 42 && first.probability[0][0] == 50);
}

static void test_live_editor_selection_and_probability(void) {
    fl_state state;
    fl_init(&state, 42);
    assert(!fl_open_editor(&state, 0, 0, 64, false));
    assert(fl_transport(&state, FL_START));
    assert(fl_on_step(&state, 0, 7, 64));
    assert(!fl_open_editor(&state, 0, 7, 64, true));
    assert(fl_open_editor(&state, 0, 7, 64, false));
    const uint32_t before = state.random_state;
    assert(fl_turn_rate(&state, -8, false, 64));
    assert(state.edit_step == 63 && state.active_step == 7);
    assert(fl_turn_rate(&state, -75, true, 64));
    assert(state.probability[0][63] == 25);
    assert(fl_turn_rate(&state, INT_MIN, true, 64));
    assert(state.probability[0][63] == 0);
    assert(fl_turn_rate(&state, INT_MAX, true, 64));
    assert(state.probability[0][63] == 100);
    assert(fl_turn_rate(&state, INT_MIN, false, 64));
    assert(state.edit_step < 64 && state.active_step == 7 && state.random_state == before);
    assert(fl_on_step(&state, 0, 3, 4));
    assert(state.edit_step < 4);
    assert(fl_on_step(&state, 1, 0, 4));
    assert(!state.editor_open);
    assert(!fl_turn_rate(&state, 1, false, 64));
}

/* This fixture stands in for stock-owned tracks; it is not a second sequencer. */
typedef struct {
    uint16_t parameter[4];
    uint16_t values[4][FL_STEPS];
    unsigned tracks;
    unsigned writes;
    uint16_t applied_value;
} stock_tracks;

static bool stock_write(stock_tracks *stock, const fl_lock_edit *edit) {
    unsigned track = 0;
    while (track < stock->tracks && stock->parameter[track] != edit->parameter) ++track;
    if (track == stock->tracks) {
        if (stock->tracks == 4) return false;
        stock->parameter[track] = edit->parameter;
        ++stock->tracks;
    }
    stock->values[track][edit->step] = edit->raw_value;
    ++stock->writes;
    if (edit->apply_now) stock->applied_value = edit->raw_value;
    return true;
}

static void test_lock_requests_use_stock_targets_and_storage(void) {
    fl_state state;
    fl_lock_edit edit;
    stock_tracks stock = {0};
    fl_init(&state, 42);
    assert(fl_transport(&state, FL_START));
    assert(fl_set_probability(&state, 0, 10, 0));
    assert(fl_on_step(&state, 0, 10, 64));
    assert(!fl_note_allowed(&state, true));
    assert(fl_open_editor(&state, 0, 63, 64, false));
    const uint32_t before = state.random_state;
    const uint16_t targets[4] = {0x0000, 0x0101, 0x0601, 0x0d01};
    for (unsigned i = 0; i < 4; ++i) {
        assert(fl_capture_lock(&state, targets[i], 0xc000, true, 64, &edit));
        assert(edit.step == 63 && edit.pattern == 0 && !edit.apply_now);
        assert(edit.raw_value == 0xc000 && stock_write(&stock, &edit));
        assert(stock.values[i][63] == 0xc000 && stock.values[i][10] == 0);
    }
    /* Raw bits for a negative signed matrix amount must survive unchanged. */
    assert(edit.parameter == 0x0d01 && (int16_t)edit.raw_value == -16384);
    assert(stock.applied_value == 0 && stock.tracks == 4);
    assert(fl_capture_lock(&state, 0x0500, 123, true, 64, &edit));
    assert(!stock_write(&stock, &edit) && stock.writes == 4);
    assert(fl_open_editor(&state, 0, 10, 64, false));
    assert(fl_capture_lock(&state, 0x0d01, 0x8000, true, 64, &edit));
    assert(edit.apply_now && stock_write(&stock, &edit));
    assert(stock.applied_value == 0x8000 && stock.tracks == 4);
    assert(state.active_step == 10 && state.random_state == before);
    assert(!fl_capture_lock(&state, 0xffff, 1, false, 64, &edit));
    assert(fl_open_editor(&state, 0, 63, 64, false));
    assert(!fl_capture_lock(&state, 0x0d01, 1, true, 4, &edit));
    fl_close_editor(&state);
    assert(!fl_capture_lock(&state, 0x0d01, 1, true, 64, &edit));
}

static void test_invalid_inputs_leave_state_unchanged(void) {
    fl_state state;
    memset(&state, 0, sizeof(state));
    fl_init(&state, 42);
    assert(fl_transport(&state, FL_START));
    fl_state before = state;
    assert(!fl_set_probability(&state, 2, 0, 100));
    assert(!fl_set_probability(&state, 0, 64, 100));
    assert(!fl_set_probability(&state, 0, 0, 101));
    assert(!fl_on_step(&state, 2, 0, 64));
    assert(!fl_on_step(&state, 0, 64, 64));
    assert(!fl_on_step(&state, 0, 0, 3));
    assert(!fl_on_step(&state, 0, 0, 65));
    assert(!fl_open_editor(&state, 0, 64, 64, false));
    assert(!fl_transport(&state, (fl_transport_event)-1));
    assert(memcmp(&state, &before, sizeof(state)) == 0);
}

int main(void) {
    test_stock_positions_and_default_probability();
    test_probability_cache_and_step_64();
    test_seeded_probability_and_transport();
    test_live_editor_selection_and_probability();
    test_lock_requests_use_stock_targets_and_storage();
    test_invalid_inputs_leave_state_unchanged();
    printf("Stock extension: 6 behavioral groups passed; 100000 steps; state %zu bytes.\n", sizeof(fl_state));
    return 0;
}
