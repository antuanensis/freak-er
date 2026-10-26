#include "freaklocks.h"

_Static_assert(sizeof(fl_state) <= FL_STATE_BUDGET, "extension exceeds reference RAM budget");

static bool valid_position(unsigned pattern, unsigned step, unsigned length) {
    return pattern < FL_PATTERNS && length >= FL_MIN_LENGTH &&
           length <= FL_STEPS && step < length;
}

void fl_init(fl_state *state, uint32_t seed) {
    state->seed = seed;
    state->random_state = seed;
    for (unsigned pattern = 0; pattern < FL_PATTERNS; ++pattern) {
        for (unsigned step = 0; step < FL_STEPS; ++step) {
            state->probability[pattern][step] = 100;
        }
    }
    state->active_pattern = 0;
    state->active_step = 0;
    state->edit_pattern = 0;
    state->edit_step = 0;
    state->running = false;
    state->has_decision = false;
    state->allow_trigger = false;
    state->editor_open = false;
}

bool fl_transport(fl_state *state, fl_transport_event event) {
    if ((unsigned)event > FL_STOP) {
        return false;
    }
    if (event == FL_START) {
        state->random_state = state->seed;
    }
    state->running = event != FL_STOP;
    state->has_decision = false;
    state->allow_trigger = false;
    state->editor_open = false;
    return true;
}

bool fl_set_probability(fl_state *state, unsigned pattern, unsigned step, unsigned percent) {
    if (pattern >= FL_PATTERNS || step >= FL_STEPS || percent > 100) {
        return false;
    }
    state->probability[pattern][step] = (uint8_t)percent;
    return true;
}

bool fl_on_step(fl_state *state, unsigned pattern, unsigned step, unsigned stock_length) {
    if (!state->running || !valid_position(pattern, step, stock_length)) {
        return false;
    }
    state->random_state = state->random_state * UINT32_C(1664525) + UINT32_C(1013904223);
    const uint32_t draw = ((state->random_state >> 16) * 100u) >> 16;
    state->allow_trigger = draw < state->probability[pattern][step];
    state->active_pattern = (uint8_t)pattern;
    state->active_step = (uint8_t)step;
    state->has_decision = true;
    if (state->editor_open) {
        if (state->edit_pattern != pattern) {
            fl_close_editor(state);
        } else if (state->edit_step >= stock_length) {
            state->edit_step = (uint8_t)(stock_length - 1);
        }
    }
    return true;
}

bool fl_note_allowed(const fl_state *state, bool stock_would_trigger) {
    return stock_would_trigger && state->running && state->has_decision && state->allow_trigger;
}

bool fl_open_editor(fl_state *state, unsigned pattern, unsigned step,
                    unsigned stock_length, bool stock_recording) {
    if (!state->running || stock_recording || !valid_position(pattern, step, stock_length)) {
        return false;
    }
    state->edit_pattern = (uint8_t)pattern;
    state->edit_step = (uint8_t)step;
    state->editor_open = true;
    return true;
}

void fl_close_editor(fl_state *state) {
    state->editor_open = false;
}

bool fl_turn_rate(fl_state *state, int delta, bool shift, unsigned stock_length) {
    if (!state->editor_open || stock_length < FL_MIN_LENGTH || stock_length > FL_STEPS) {
        return false;
    }
    if (state->edit_step >= stock_length) {
        state->edit_step = (uint8_t)(stock_length - 1);
    }
    if (shift) {
        if (delta > 100) delta = 100;
        if (delta < -100) delta = -100;
        int percent = state->probability[state->edit_pattern][state->edit_step] + delta;
        if (percent > 100) percent = 100;
        if (percent < 0) percent = 0;
        state->probability[state->edit_pattern][state->edit_step] = (uint8_t)percent;
    } else {
        const int length = (int)stock_length;
        state->edit_step = (uint8_t)((state->edit_step + delta % length + length) % length);
    }
    return true;
}

bool fl_capture_lock(const fl_state *state, uint16_t parameter, uint16_t raw_value,
                     bool stock_recordable, unsigned stock_length, fl_lock_edit *edit) {
    if (!state->editor_open || !stock_recordable ||
        !valid_position(state->edit_pattern, state->edit_step, stock_length)) {
        return false;
    }
    edit->parameter = parameter;
    edit->raw_value = raw_value;
    edit->pattern = state->edit_pattern;
    edit->step = state->edit_step;
    edit->apply_now = state->running && state->has_decision &&
                      state->active_pattern == state->edit_pattern &&
                      state->active_step == state->edit_step;
    return true;
}
