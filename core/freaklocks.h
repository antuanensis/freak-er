#ifndef FREAKLOCKS_H
#define FREAKLOCKS_H

#include <stdbool.h>
#include <stdint.h>

enum { FL_PATTERNS = 2, FL_STEPS = 64, FL_MIN_LENGTH = 4, FL_STATE_BUDGET = 160 };

typedef enum {
    FL_START,
    FL_CONTINUE,
    FL_STOP
} fl_transport_event;

/* Extension state only: stock owns notes, clock, cursor, gates and modulation. */
typedef struct {
    uint32_t seed;
    uint32_t random_state;
    uint8_t probability[FL_PATTERNS][FL_STEPS];
    uint8_t active_pattern;
    uint8_t active_step;
    uint8_t edit_pattern;
    uint8_t edit_step;
    bool running;
    bool has_decision;
    bool allow_trigger;
    bool editor_open;
} fl_state;

typedef struct {
    uint16_t parameter;
    uint16_t raw_value;
    uint8_t pattern;
    uint8_t step;
    bool apply_now;
} fl_lock_edit;

/* All pointers must be valid. Serialize stock callbacks and panel edits. */
void fl_init(fl_state *state, uint32_t seed);
bool fl_transport(fl_state *state, fl_transport_event event);
bool fl_set_probability(fl_state *state, unsigned pattern, unsigned step, unsigned percent);

/* Call exactly once at an actual stock boundary, never to advance stock. */
bool fl_on_step(fl_state *state, unsigned pattern, unsigned step, unsigned stock_length);
/* Gate new sequencer note-ons only; never gate note-offs, ties, MIDI or arp. */
bool fl_note_allowed(const fl_state *state, bool stock_would_trigger);

/* A stock A/B switch, preset change, or edit-context loss closes the editor. */
bool fl_open_editor(fl_state *state, unsigned pattern, unsigned step,
                    unsigned stock_length, bool stock_recording);
void fl_close_editor(fl_state *state);
bool fl_turn_rate(fl_state *state, int delta, bool shift, unsigned stock_length);

/* Stock validates eligibility/range and owns the four-track write/full result. */
bool fl_capture_lock(const fl_state *state, uint16_t parameter, uint16_t raw_value,
                     bool stock_recordable, unsigned stock_length, fl_lock_edit *edit);

#endif
