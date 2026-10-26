#include "freaklocks.h"

#include <assert.h>
#include <stdio.h>

int main(void) {
    fl_state state;
    fl_lock_edit edit;
    fl_init(&state, 42);
    assert(fl_transport(&state, FL_START));
    assert(fl_set_probability(&state, 0, 63, 0));
    puts("Reference stock adapter only: positions supplied by caller; no native hooks installed.");
    for (unsigned stock_step = 0; stock_step < FL_STEPS; ++stock_step) {
        assert(fl_on_step(&state, 0, stock_step, FL_STEPS));
        if (stock_step == 8) {
            assert(fl_open_editor(&state, 0, stock_step, FL_STEPS, false));
            assert(fl_turn_rate(&state, 55, false, FL_STEPS));
            assert(fl_turn_rate(&state, 25, true, FL_STEPS));
            assert(fl_capture_lock(&state, 0x0d01, 0xc000, true, FL_STEPS, &edit));
            printf("Live edit request: A/%u, matrix parameter %#x, signed value %d, apply now=%d\n",
                   edit.step + 1u, edit.parameter, (int16_t)edit.raw_value, edit.apply_now);
            puts("The native stock track writer is still required to apply this request.");
        }
        if (stock_step == 0 || stock_step == 63) {
            printf("Stock position A/%u, probability=%u%%, new note allowed=%d\n",
                   stock_step + 1u, state.probability[0][stock_step], fl_note_allowed(&state, true));
        }
    }
    assert(fl_transport(&state, FL_STOP));
    return 0;
}
