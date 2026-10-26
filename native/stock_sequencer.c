/* MicroFreak 5.0.0.2084 only. Stock remains the sole sequence engine.
 * Addresses and ABI evidence: docs/native-integration.md.
 * No libc, heap, flash writer, independent transport, or modulation bank. */
#include <stdint.h>

#define U8(a) (*(volatile uint8_t *)(uintptr_t)(a))
#define U16(a) (*(volatile uint16_t *)(uintptr_t)(a))
#define U32(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define KEEP __attribute__((noinline, used))
#define TRAMP __attribute__((naked, noinline, used))
#define SEQ 0x20000eecu
#define MOD 0x20000e30u
#define PARAMS 0x2001c898u
#define REQUEST 0x20000a14u
#define WIDGET 0x2001dff4u
#define EDIT 1u
#define CAPTURE 2u
#define CONSUMED 4u
#define PANEL_ACTIVE 8u
#define RAW_VALID 128u
#define TAG 0xd3u
#define COPY 0x8000u
#ifndef FREAKER_PASSTHROUGH
#define FREAKER_PASSTHROUGH 0
#endif

/* Undefined .abs symbols keep calls relocatable until placement. The pinned
 * linker resolves them through these absolute symbols, without address pools. */
#define STOCK_SYMBOL(name, address) __asm__(".global " #name "\n.equ " #name ", " #address)
#define STOCK(name, address, ...) \
    extern uint32_t name(__VA_ARGS__) __asm__(#name ".abs"); \
    STOCK_SYMBOL(name, address)
STOCK(stock_init, 0x0800e730, uint32_t, uint32_t, uint32_t, uint32_t);
STOCK(stock_advance, 0x080281f8, uint32_t);
STOCK(stock_close, 0x08055e40, uint32_t);
STOCK(stock_post, 0x080558c0, uint32_t, uint32_t);
STOCK(stock_scale, 0x0800e644, uint32_t, uint32_t);
STOCK(stock_target, 0x08027fcc, uint32_t, uint32_t, uint32_t);
STOCK(stock_send, 0x0802682c, uint32_t, uint32_t, uint32_t);
STOCK(stock_button, 0x08043224, uint32_t, uint32_t, uint32_t, uint32_t);
STOCK(stock_encoder, 0x08042bc8, uint32_t, uint32_t, uint32_t, uint32_t);
STOCK(stock_pot, 0x08040220, uint32_t, uint32_t, uint32_t, uint32_t);
STOCK(stock_poll, 0x08039da4, uint32_t);
STOCK(stock_text, 0x080557e8, uint32_t, uint32_t, uint32_t);
STOCK(stock_widget, 0x0805579c, uint32_t, uint32_t, uint32_t);
STOCK_SYMBOL(encoder_resume, 0x0802c484);
STOCK_SYMBOL(popup_resume, 0x08052c2e);
typedef struct {
    volatile uint32_t random;
    uint8_t flags; /* Low four bits: UI scope. Bits 4..6: track (7 = none). */
    /* Scope: Shift during panel dispatch; pending Oct/copy gesture otherwise. */
    uint8_t step : 6, pattern : 1, scope : 1;
    volatile uint8_t allowed, close_pending; /* Separate interrupt-owned bytes. */
    uint16_t parameter, value;
} State;
_Static_assert(sizeof(State) == 12, "unused stock CC pointer slots only");
#define S ((State *)0x2001c9d8u)
#define TRACK ((S->flags >> 4) & 7u)
static inline void select_track(uint32_t track) {
    S->flags = (uint8_t)((S->flags & 0x8fu) | (track << 4));
}

/* The builder fills these eight-byte slots from validated, PC-independent
 * stock prologues and a branch back. No proprietary instructions in source. */
TRAMP uint32_t original_set(uint32_t a, uint32_t b, uint32_t c, uint32_t d) { __asm__(".space 8"); }
TRAMP uint32_t original_note(uint32_t a, uint32_t b, uint32_t c, uint32_t d, uint32_t e, uint32_t f) { __asm__(".space 8"); }
#define original_send(a, b, c) stock_send(a, b, c)
TRAMP uint32_t original_load(uint32_t a, uint32_t b, uint32_t c, uint32_t d) { __asm__(".space 8"); }
TRAMP uint32_t original_clear(uint32_t a, uint32_t b) { __asm__(".space 8"); }
TRAMP uint32_t original_transport(uint32_t a, uint32_t b) { __asm__(".space 8"); }
TRAMP uint32_t original_builtin(uint32_t a) { __asm__(".space 8"); }

static inline uint32_t pattern_address(uint32_t sequence, uint32_t pattern) {
    return sequence + 4u + pattern * 0x412u;
}

KEEP uint32_t valid_pattern(uint32_t base) {
    if (U8(base + 0x410u) == 0xffu) return 0;
    for (uint32_t i = 0; i < 64; ++i)
        if (U8(base + i * 16u + 15u) != TAG || U8(base + i * 16u + 14u) > 100u) return 0;
    return 1;
}

KEEP uint32_t probability(uint32_t sequence, uint32_t pattern, uint32_t step) {
    uint32_t base = pattern_address(sequence, pattern);
    return valid_pattern(base) ? U8(base + step * 16u + 14u) : 100u;
}

KEEP void set_probability(uint32_t value) {
    uint32_t base = pattern_address(SEQ, S->pattern);
    if (!valid_pattern(base)) for (uint32_t i = 0; i < 64; ++i) {
        U8(base + i * 16u + 14u) = 100;
        U8(base + i * 16u + 15u) = TAG;
    }
    U8(base + S->step * 16u + 14u) = (uint8_t)value;
    U8(base + 0x410u) = 0xaau;
}

KEEP uint32_t boot(uint32_t a, uint32_t b, uint32_t c, uint32_t d) {
    uint32_t result = stock_init(a, b, c, d);
    S->random = 42;
    S->flags = 0x70;
    S->allowed = 1;
    S->close_pending = 0;
    return result;
}

KEEP uint32_t boundary(uint32_t sequence) {
    uint32_t step = stock_advance(sequence);
    if (FREAKER_PASSTHROUGH) return step;
    uint32_t mode = U8(0x20003ac4u);
    if (mode < 2u || mode > 3u) return step;
    uint32_t random = S->random * 1664525u + 1013904223u;
    S->random = random;
    uint32_t p = probability(sequence, U8(sequence + 2u), step);
    uint32_t allowed = p == 100u || (p != 0u && (random >> 16) * 100u < p * 65536u);
    S->allowed = (uint8_t)allowed;
    return step;
}

KEEP uint32_t note(uint32_t object, uint32_t message, uint32_t source,
                   uint32_t mode, uint32_t e, uint32_t f) {
    uint32_t engine = U8(0x20003ac4u);
    if (!FREAKER_PASSTHROUGH && source == 5u && (message & 0xf0u) == 0x90u && (message & 0x7f0000u) &&
        engine >= 2u && engine <= 3u && U8(0x20003a80u) && !S->allowed) return 1;
    return original_note(object, message, source, mode, e, f);
}

KEEP void close_editor(void) {
    if (S->flags & EDIT) {
        S->flags &= (uint8_t)~(EDIT | RAW_VALID);
        S->scope = 0;
        stock_close(REQUEST);
    }
}

KEEP uint32_t transport(uint32_t object, uint32_t event) {
    if (FREAKER_PASSTHROUGH) return original_transport(object, event);
    if (event == 1u || event == 4u) { S->random = 42; S->allowed = 1; }
    /* Transport can run in an interrupt. UI closes on the next main-loop poll. */
    if (event == 0u || event == 2u) { S->allowed = 0; S->close_pending = 1; }
    return original_transport(object, event);
}

KEEP uint32_t clear_pattern(uint32_t object, uint32_t pattern) {
    if (FREAKER_PASSTHROUGH) return original_clear(object, pattern);
    U8(pattern_address(object, pattern) + 15u) = 0;
    return original_clear(object, pattern);
}

KEEP uint32_t builtin_pattern(uint32_t object) {
    if (FREAKER_PASSTHROUGH) return original_builtin(object);
    if (U8(object + 1u) < 10u) U8(pattern_address(object, U8(object + 2u)) + 15u) = 0;
    return original_builtin(object);
}

KEEP uint32_t load_sequence(uint32_t object, uint32_t source, uint32_t offset, uint32_t pattern) {
    if (FREAKER_PASSTHROUGH) return original_load(object, source, offset, pattern);
    close_editor();
    return original_load(object, source, offset, pattern);
}

KEEP uint32_t editor_available(void) {
    uint32_t mode = U8(0x20003ac4u);
    /* UI transport 2 = playback, 3/4 = real-time/step recording. */
    return !S->close_pending && U8(0x20003a80u) && mode >= 2u && mode <= 3u && U8(0x20003705u) == 2u;
}

KEEP void post_editor(void) {
    stock_post(REQUEST, 0x700);
}

KEEP uint32_t raw_parameter(uint32_t object, uint32_t parameter) {
    return U16(U32(object + 0x2cu + ((parameter & 0xffffu) >> 8) * 4u) + (parameter & 255u) * 2u);
}

KEEP uint32_t panel_value(uint32_t object, uint32_t parameter) {
    /* Relative panel controls must start at the selected snapshot. The scope
     * and UI caller range exclude recorder base reads, MIDI and audio queries. */
    if (!FREAKER_PASSTHROUGH && object == PARAMS &&
        (S->flags & (EDIT | PANEL_ACTIVE | CAPTURE)) == (EDIT | PANEL_ACTIVE) &&
        editor_available() && U8(SEQ + 2u) == S->pattern) {
        uint32_t base = pattern_address(SEQ, S->pattern);
        uint32_t record = base + S->step * 16u;
        for (uint32_t track = 0; track < 4; ++track) {
            if (U16(base + 0x400u + track * 2u) == parameter) {
                if ((S->flags & RAW_VALID) && S->parameter == parameter && TRACK == track) return S->value;
                if (U8(record + 13u) & (1u << track))
                    return (uint16_t)(U8(record + 8u + track) << ((uint16_t)(parameter - 0xa00u) <= 0x605u ? 8 : 7));
            }
        }
    }
    return raw_parameter(object, parameter);
}

KEEP uint32_t get_parameter(uint32_t object, uint32_t parameter) {
    uint32_t caller = (uint32_t)(uintptr_t)__builtin_return_address(0);
    if (caller >= 0x0803a000u && caller < 0x0804347cu) return panel_value(object, parameter);
    return raw_parameter(object, parameter);
}

KEEP uint32_t scaled_parameter(uint32_t object, uint32_t parameter) {
    if (FREAKER_PASSTHROUGH) return stock_scale(object, parameter);
    uint32_t value = panel_value(object, parameter);
    uint32_t index = parameter & 255u;
    uint32_t group = (parameter & 0xffffu) >> 8;
    if (value == raw_parameter(object, parameter))
        return stock_scale(object, parameter);
    /* This pure stock scaler reads only the value/metadata table pointers.
     * Supply one local value without changing any global value or pointer. */
    uint32_t view[36];
    view[11] = (uint32_t)(uintptr_t)&value - index * 2u;
    view[35] = U32(object + 0x8cu + group * 4u);
    return stock_scale((uint32_t)(uintptr_t)view, index);
}

/* Stock's generic incrementer inlines its signed value read. Preserve its
 * live metadata in LR, every other register and the preceding comparison. */
__attribute__((naked, used)) void encoder_value(void) {
    __asm__("push {r0-r3,r12,lr}\n mrs r2, apsr\n push {r2,r3}\n"
            "mov r0,r8\n sub.w r1,r10,r8\n lsl.w r1,r1,#6\n orr.w r1,r1,r9\n"
            "bl panel_value\n sxth r6,r0\n pop {r2,r3}\n msr apsr_nzcvqg,r2\n"
            "pop {r0-r3,r12,lr}\n .reloc ., R_ARM_THM_JUMP24, encoder_resume.abs\n .inst.w 0xf7ffbffe");
}

/* Keep this loop out of capture: fewer spills in its caller, same stack bound. */
static __attribute__((noinline)) uint32_t scale_track(uint32_t track, uint32_t baseline, uint32_t encoded) {
    uint32_t base = pattern_address(SEQ, S->pattern);
    uint32_t record = base + S->step * 16u;
    int32_t a = (U8(record + 13u) & (1u << track)) ? U8(record + 8u + track) : baseline;
    int32_t b = (int32_t)encoded, offset = 0;
    uint32_t bipolar = (uint16_t)(S->parameter - 0xa00u) <= 0x605u;
    if (bipolar) { a = (int8_t)a; b = (int8_t)b; }
    if (!a || (a ^ b) < 0) { offset = b - a; a = b = 1; }
    for (uint32_t step = 0; step < 64; ++step) {
        uint32_t cell = base + step * 16u;
        if (!(U8(cell + 13u) & (1u << track))) continue;
        uint32_t address = cell + 8u + track;
        int32_t v = bipolar ? (int8_t)U8(address) : U8(address);
        v = v * b / a + offset;
        int32_t low = bipolar ? -128 : 0, high = bipolar ? 127 : 255;
        if (v < low) v = low;
        if (v > high) v = high;
        U8(address) = (uint8_t)v;
    }
    record = base + U8(SEQ + 0x828u) * 16u;
    return U8(record + 13u) & (1u << track) ? U8(record + 8u + track) : U8(MOD + 0x1au + track * 4u);
}

static void capture_parameter(uint32_t parameter, uint32_t value) {
    uint32_t local = S->scope, selected = S->step;
    uint32_t base = pattern_address(SEQ, S->pattern);
    uint32_t track, free_track = 4;
    for (track = 0; track < 4; ++track) {
        uint32_t target = U16(base + 0x400u + track * 2u);
        if (target == parameter) break;
        if (target == 0xffffu && free_track == 4u) free_track = track;
    }
    uint32_t added = track == 4u;
    if (added) track = free_track;
    S->parameter = (uint16_t)parameter;
    S->value = (uint16_t)value;
    select_track(track);
    S->flags |= RAW_VALID;
    if (track == 4u) return;
    uint32_t current = MOD + track * 4u;
    uint32_t shift = (uint16_t)(parameter - 0xa00u) <= 0x605u ? 8 : 7;
    uint32_t raw_base = raw_parameter(PARAMS, parameter);
    uint32_t baseline = raw_base >> shift;
    uint32_t encoded = (uint8_t)((int16_t)value >> shift);
    if (added) {
        stock_target(SEQ, track, parameter);
        for (uint32_t step = 0; step < 64; ++step) {
            uint32_t cell = base + step * 16u;
            U8(cell + 8u + track) = (uint8_t)(local ? baseline : encoded);
            U8(cell + 13u) |= (uint8_t)(1u << track);
        }
    }
    if (local) {
        /* Reuse stock targets and record fields. Recorder parity tests cover
         * every eligible ID, conversion, baseline and LED state. */
        uint32_t cell = base + selected * 16u;
        U8(cell + 8u + track) = (uint8_t)encoded;
        U8(cell + 13u) |= (uint8_t)(1u << track);
    } else value = (added ? encoded : scale_track(track, baseline, encoded)) << shift;
    if (U16(current + 0x18u) != parameter) {
        U16(current + 0x18u) = (uint16_t)parameter;
        U16(current + 0x28u) = (uint16_t)parameter;
        U16(current + 0x2au) = (uint8_t)(raw_base >> 7);
        U16(current + 0x1au) = (uint16_t)baseline;
        U8(MOD + 0x3cu + track) = (uint8_t)baseline;
        U8(MOD + 0x40u + track) = (uint8_t)baseline;
        U8(MOD + 0x44u + track) = 0;
    }
    U8(base + 0x410u) = 0xaa;
    U8(MOD + 0x78u) = (uint8_t)track;
    U16(MOD + 0x48u + track * 12u + 8u) = 0x0701;
    if (!local || U8(SEQ + 0x828u) == selected) {
        uint32_t output = (uint16_t)((int16_t)value >> shift);
        U16(current + 0x1au) = (uint16_t)output;
        U8(MOD + 0x38u + track) = 1;
        U8(MOD + 0x3cu + track) = (uint8_t)output;
        U8(MOD + 0x40u + track) = (uint8_t)output;
        original_send(MOD, parameter, value);
    }
}

KEEP uint32_t set_parameter(uint32_t object, uint32_t parameter, uint32_t value, uint32_t force) {
    if (FREAKER_PASSTHROUGH) return original_set(object, parameter, value, force);
    uint32_t group = parameter >> 8, index = parameter & 255u;
    /* Scope the actual panel dispatch, including stock tail calls and helpers.
     * Main-loop MIDI dispatch is outside this scope. */
    if ((S->flags & (EDIT | PANEL_ACTIVE | CAPTURE)) == (EDIT | PANEL_ACTIVE) &&
        editor_available() && U8(SEQ + 2u) == S->pattern &&
        group < U32(PARAMS + 0x24cu) && index < U8(0x20000408u + group)) {
        uint32_t flags = U32(PARAMS + 0x8cu + 4u * group);
        if (U8(flags + index * 2u + 1u) & 0x40u) {
            capture_parameter(parameter, value);
            post_editor();
            return 3;
        }
    }
    return original_set(object, parameter, value, force);
}

KEEP uint32_t step_address(uint32_t step) {
    return pattern_address(SEQ, S->pattern) + step * 16u;
}

KEEP void edit_locks(uint32_t mask, uint32_t source) {
    uint32_t target = step_address(S->step);
    if (source < 64u) {
        source = step_address(source);
        U16(target + 8u) = U16(source + 8u);
        U16(target + 10u) = U16(source + 10u);
        U8(target + 13u) = (uint8_t)((U8(target + 13u) & 0xf0u) | (U8(source + 13u) & 15u));
    } else U8(target + 13u) &= (uint8_t)~mask;
    U8(pattern_address(SEQ, S->pattern) + 0x410u) = 0xaa;
    S->flags &= (uint8_t)~RAW_VALID;
    S->scope = 0;
    post_editor();
}

static void select_next_track(void) {
    uint32_t track = TRACK;
    for (uint32_t i = 0; i < 4; ++i) {
        track = (track + 1u) & 3u;
        uint32_t parameter = U16(pattern_address(SEQ, S->pattern) + 0x400u + track * 2u);
        if (parameter != 0xffffu) {
            select_track(track); S->parameter = (uint16_t)parameter;
            U8(MOD + 0x78u) = (uint8_t)track;
            break;
        }
    }
    S->flags &= (uint8_t)~RAW_VALID;
    S->scope = 0;
    post_editor();
}

KEEP void edit_pitch(int32_t delta) {
    uint32_t record = step_address(S->step);
    uint32_t raw = U8(record);
    if (raw != 0xffu) {
        int32_t note = (int32_t)(raw & 127u) + delta;
        int32_t high = (raw & 128u) ? 126 : 127;
        if (note < 0) note = 0;
        if (note > high) note = high;
        U8(record) = (uint8_t)((raw & 128u) | (uint32_t)note);
        U8(pattern_address(SEQ, S->pattern) + 0x410u) = 0xaa;
    }
    S->scope = 0;
    S->flags &= (uint8_t)~RAW_VALID;
    post_editor();
}

KEEP uint32_t button(uint32_t panel, uint32_t control, uint32_t flags, uint32_t down) {
    if (FREAKER_PASSTHROUGH) return stock_button(panel, down, control, flags);
    if (!down && control == 0x1103u && (S->flags & CONSUMED)) {
        S->flags &= (uint8_t)~CONSUMED;
        if ((S->flags & EDIT) && S->scope && (S->value & COPY) && editor_available()) edit_locks(15, S->value & 63u);
        return 0;
    }
    if (down && control == 0x1103u && U8(panel + 0x28u) &&
        editor_available()) {
        if (S->flags & EDIT) close_editor();
        else {
            S->step = U8(SEQ + 0x828u);
            S->pattern = U8(SEQ + 2u);
            select_track(7);
            S->flags &= (uint8_t)~RAW_VALID;
            S->scope = 0;
            S->flags |= EDIT;
            post_editor();
        }
        S->flags |= CONSUMED;
        return 0;
    }
    if ((S->flags & EDIT) && editor_available()) {
        if (control == 0x401u) {
            if (down) {
                S->scope = 1;
                S->value = (uint16_t)(U32(0x2001e1d8u) & 0x7fffu);
            } else if (S->scope && !(S->value & COPY)) select_next_track();
            S->flags &= (uint8_t)~RAW_VALID;
            return 0;
        }
        if (down && control == 0x1103u) {
            S->scope = 1; S->value = (uint16_t)(COPY | S->step);
            S->flags = (uint8_t)((S->flags | CONSUMED) & ~RAW_VALID);
            post_editor(); return 0;
        }
        if (control == 0x1105u && (!down || U8(panel + 0x28u))) {
            if (down) { edit_locks(15, 64); set_probability(100); }
            return 0;
        }
    }
    /* Matrix selection belongs to live lock editing; other workflow buttons
     * retain their stock actions after leaving the editor. */
    if (down && control != 0x804u && control != 0x901u) close_editor();
    return stock_button(panel, down, control, flags);
}

KEEP uint32_t press(uint32_t panel, uint32_t control, uint32_t flags) {
    return button(panel, control, flags, 1);
}
KEEP uint32_t release(uint32_t panel, uint32_t control, uint32_t flags) {
    return button(panel, control, flags, 0);
}

KEEP uint32_t encoder(uint32_t panel, uint32_t control, uint32_t delta, uint32_t flags) {
    if (FREAKER_PASSTHROUGH) return stock_encoder(panel, control, delta, flags);
    /* Physical panel config uses 0x403; 0x402 is the stock unsynced alternate. */
    if ((S->flags & EDIT) && (control == 0x402u || control == 0x403u) && editor_available()) {
        int32_t change = (int16_t)delta;
        if (U8(panel + 0x28u) && !(S->scope && (S->value & COPY))) {
            int32_t value = (int32_t)probability(SEQ, S->pattern, S->step) + change;
            if (value < 0) value = 0;
            if (value > 100) value = 100;
            set_probability((uint32_t)value);
        } else {
            int32_t length = U8(pattern_address(SEQ, S->pattern) + 0x409u);
            if (length < 4 || length > 64) { close_editor(); return 0; }
            int32_t step = ((int32_t)S->step + change) % length;
            if (step < 0) step += length;
            S->step = (uint8_t)step;
            S->flags &= (uint8_t)~RAW_VALID;
        }
        post_editor();
        return 0;
    }
    if ((S->flags & EDIT) && editor_available() && control == 0x800u) {
        edit_pitch((int16_t)delta);
        return 0;
    }
    if (control == 0x800u) close_editor();
    S->scope = U8(panel + 0x28u) != 0;
    S->flags |= PANEL_ACTIVE;
    uint32_t result = stock_encoder(panel, control, delta, flags);
    S->flags &= (uint8_t)~PANEL_ACTIVE;
    S->scope = 0;
    return result;
}

KEEP uint32_t pot(uint32_t panel, uint32_t control, uint32_t value, uint32_t flags) {
    if (FREAKER_PASSTHROUGH) return stock_pot(panel, control, value, flags);
    uint32_t shift = U8(panel + 0x28u);
    S->scope = shift != 0;
    S->flags |= PANEL_ACTIVE;
    /* Shift is the step-edit modifier here, not the pot's stock alternate
     * destination (for example Rise Shape instead of Rise Time). */
    U8(panel + 0x28u) = (S->flags & EDIT) ? 0 : (uint8_t)shift;
    uint32_t result = stock_pot(panel, control, value, flags);
    S->flags &= (uint8_t)~PANEL_ACTIVE;
    U8(panel + 0x28u) = (uint8_t)shift;
    S->scope = 0;
    return result;
}

KEEP uint32_t poll(uint32_t object) {
    uint32_t result = stock_poll(object);
    if (FREAKER_PASSTHROUGH) return result;
    if (S->close_pending) { S->close_pending = 0; close_editor(); }
    if (S->flags & EDIT) {
        uint32_t length = U8(pattern_address(SEQ, S->pattern) + 0x409u);
        if (!editor_available() || U8(SEQ + 2u) != S->pattern || S->step >= length) close_editor();
        else {
            if (S->scope && !(S->value & COPY) &&
                ((U32(0x2001e1d8u) - S->value) & 0x7fffu) >= 600u)
                edit_locks(TRACK < 4u ? 1u << TRACK : 0, 64);
            if (U16(REQUEST + 2u) != 0x700u) post_editor();
        }
    }
    return result;
}

KEEP char *number(char *out, uint32_t value) {
    /* At most three frames: every editor field is bounded to 255. */
    if (value >= 10u) out = number(out, value / 10u);
    *out++ = (char)('0' + value % 10u);
    return out;
}

KEEP void draw_editor(void) {
    char text[64], *out = text;
    uint32_t pattern = S->pattern, selected = S->step, track = TRACK, parameter = S->parameter;
    *out++ = (char)('A' + pattern); *out++ = ' '; *out++ = 'E';
    out = number(out, selected + 1u); *out++ = '/';
    out = number(out, U8(pattern_address(SEQ, pattern) + 0x409u));
    *out++ = ' '; *out++ = 'N';
    uint32_t record = step_address(selected);
    if (U8(record) == 0xffu) *out++ = '-';
    else out = number(out, U8(record) & 127u);
    *out++ = '\n'; *out++ = '%'; out = number(out, probability(SEQ, pattern, selected));
    *out++ = ' '; *out++ = 'T';
    if (track < 4u) out = number(out, track + 1u);
    else if (track == 4u) {
        *out++ = 'F'; *out++ = 'U'; *out++ = 'L'; *out++ = 'L';
    } else *out++ = '-';
    if (track < 4u) {
        *out++ = '\n';
        uint32_t pid = parameter;
        uint32_t names = U32(0x20000420u + (pid >> 8) * 4u);
        uint32_t name = names + (pid & 255u) * 12u;
        while (U8(name)) *out++ = (char)U8(name++);
        *out++ = ' ';
        if (!(U8(record + 13u) & (1u << track))) *out++ = '-';
        else {
            uint32_t value = U8(record + 8u + track);
            if ((uint16_t)(pid - 0xa00u) <= 0x605u && value >= 128u) {
                *out++ = '-'; value = 256u - value;
            }
            out = number(out, value);
        }
    }
    *out++ = 0;
    U32(REQUEST + 0x7cu) = 0x7fffffffu;
    stock_text(WIDGET, 0, 0x7f);
    char *part = text;
    while (part < out) {
        uint32_t size = (uint32_t)(out - part);
        if (size > 4u) size = 4;
        stock_text(WIDGET, (uint32_t)(uintptr_t)part, size);
        part += size;
    }
    stock_widget(WIDGET, 0x12, 0x02001a00);
}

/* Entered inside stock's request-0x700 display case; stock owns return/timeout. */
__attribute__((naked, used)) void popup(void) {
    __asm__("push {r4-r7}\n bl draw_editor\n pop {r4-r7}\n .reloc ., R_ARM_THM_JUMP24, popup_resume.abs\n .inst.w 0xf7ffbffe");
}
