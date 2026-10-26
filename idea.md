# Project FREAKOS
## Experimental Firmware for the Arturia MicroFreak

**Project type:** Open-source embedded firmware research and development  
**Target hardware:** Arturia MicroFreak  
**Initial firmware baseline:** 5.0.0.2084  
**Primary applications:** Dark ambient, drone, industrial, experimental electronic music, generative sequencing and live performance  
**Status:** Concept and technical feasibility assessment

---

## 1. Project Vision

FREAKOS aims to transform the Arturia MicroFreak into a self-contained experimental synthesis and generative performance instrument.

Inspired by Elektron parameter locking, Mutable Instruments' experimental synthesis concepts, modular control systems and contemporary alternative firmware projects, FREAKOS will extend the MicroFreak beyond conventional preset-based synthesis.

The instrument should become capable of producing evolving musical structures, independently modulated voices, complex rhythmic textures, controlled unpredictability and long-form autonomous soundscapes.

The goal is not to replicate a DAW, groovebox or modular synthesizer. It is to develop a coherent new instrument that exploits the MicroFreak's unique combination of digital oscillators, analog filtering, pressure-sensitive keyboard, modulation matrix, sequencer, OLED display and external control outputs.

### Core design principles

1. **Generative by design:** Modulation and sequencing can evolve autonomously while retaining musical coherence.
2. **Performance-oriented:** Parameters can be changed, recorded and manipulated without stopping playback.
3. **Deep but immediate:** Advanced synthesis capabilities must remain usable through the original hardware interface.
4. **Non-destructive experimentation:** Randomization, mutation and morphing should support locking, undo, reproducibility and controlled variation.
5. **Hardware-aware:** Every feature must respect CPU, memory, storage, timing and physical output constraints.
6. **Modular development:** Features should be individually testable, with minimal coupling and a documented compatibility strategy.

## 2. Functional Scope

### 2.1 FreakLocks — Advanced Step Sequencing

**Priority: P0 — Core feature**

Introduce Elektron-inspired per-step parameter locks, transforming each sequencer step into a programmable synthesis event.

Each step may contain note information, timing, triggering conditions and a sparse collection of parameter overrides.

**Required functionality**

- Per-step locks for oscillator Wave, Timbre, Shape, filter cutoff, resonance, modulation amounts and compatible envelope parameters.
- Conditional triggering, including probability, every-N-cycle events, first-cycle events and previous-step conditions.
- Ratchets, microtiming, variable gate lengths and step repeats.
- Multiple playback directions, including forward, reverse, pendulum and random.
- Parameter transitions supporting immediate changes, interpolation and slew.
- Per-step assignment of oscillator types, subject to feasibility of real-time engine switching.
- Pattern mutation and performance-oriented conditional overrides.

**Live parameter-lock editing**

Users must be able to modify an existing lock while the sequence continues playing.

Editing workflows should support:

- Selecting or holding a step and turning a parameter knob.
- Recording locks during playback.
- Editing a lock without restarting the sequence.
- Removing one lock without clearing others.
- Locking, copying, pasting and clearing individual steps.
- Optional parameter takeover to prevent sudden jumps.
- Undoing recent edits.

**Sequencer interface**

Explore replacing or extending the stock sequencer interface with OLED-driven navigation.

The proposed interface should include a step overview, per-step parameter pages, a lock editor, pattern navigation and clear indicators for playback position, conditional events and active locks.

The first implementation should use a compact 16-step page with support for longer patterns. The existing 64-step sequencer should be reused where practical rather than replaced prematurely.

**Critical technical investigation:** Determine whether oscillator algorithms can be switched safely between steps, especially when multiple notes are sustained. Rapid engine replacement may require retriggering, deferred switching or substantial architectural changes.

### 2.2 FreakVoice — Independent Per-Note Modulation

**Priority: P0/P1 — Core research objective**

Extend the existing polyphonic modulation capabilities to provide greater independence between the MicroFreak's four paraphonic voices.

**Proposed functionality**

- Independent modulation phase and random state per active voice.
- Per-note modulation offsets and evolving timbral parameters.
- Note-specific LFO retriggering and free-running behavior.
- Independent slew, drift, random walks and modulation cycles.
- Per-voice parameter locks where oscillator architecture permits.
- Alternative voice-allocation policies for generative and drone applications.

A single held chord could therefore evolve as four partially independent synthesis processes.

**Hardware limitation:** The MicroFreak has one shared analog filter. Independent filter-cutoff values for simultaneous voices cannot be implemented through firmware alone. Per-voice digital oscillator modulation should be prioritized, while global parameters require explicit conflict-resolution rules.

### 2.3 FreakMod — Generative Modulation Laboratory

**Priority: P0 — Core feature**

Develop a programmable, clock-aware modulation framework that operates alongside or extends the stock modulation matrix.

**Modulation generators**

- Traditional LFOs with additional waveforms and phase control.
- Brownian motion and bounded random walks.
- Slew-limited random signals.
- Logistic maps and chaotic oscillators.
- Lorenz and other low-dimensional attractors.
- Euclidean triggers and modulation gates.
- Clocked modulation sequences.
- Sample-and-hold and track-and-hold.
- Slowly evolving drift generators.

**Modulation processing**

Introduce operators capable of transforming and combining signals:

- Addition, multiplication and bipolar scaling.
- Comparisons and threshold gates.
- Rectification, inversion and quantization.
- Slew limiting and sample-and-hold.
- Event-controlled resets and clock divisions.

Example modulation relationships:

- `LFO × Envelope`
- `Random + Keyboard Pressure`
- `LFO > Threshold`
- `Euclidean Gate × Chaotic Modulation`
- `Clock → Sample & Hold → Oscillator Timbre`

Provide a compact way to assign modulation generators, processors and destinations.

The implementation should distinguish control-rate modulation from audio-rate synthesis. Computationally expensive algorithms must not compromise audio rendering or MIDI timing.

### 2.4 FreakDrone — Autonomous Drone Engine

**Priority: P1 — Defining artistic feature**

Create a dedicated performance mode for slowly evolving, sustained and autonomous soundscapes.

**Proposed functionality**

- Hold and sustain independent pitches.
- Individual modulation cycles for each active voice.
- Independent note duration and rearticulation behavior.
- Slowly evolving pitch offsets and controlled detuning.
- Per-voice random evolution.
- Timed changes to modulation intensity.
- Generative events operating over minutes or hundreds of bars.
- Configurable voice allocation and note replacement.

The drone engine should be capable of generating evolving textures without continued keyboard interaction.

Possible modes include sustained chords, shifting clusters, rhythmic drones, inharmonic swarms and slowly changing harmonic structures.

An explicit priority is the ability to maintain stable long-duration playback without hanging notes, voice-allocation failures or unwanted modulation discontinuities.

### 2.5 FreakMorph — Continuous Sound Morphing

**Priority: P1**

Introduce two-state morphing between snapshots of a synthesis configuration.

Snapshots A and B should capture compatible synthesis, envelope and modulation parameters.

**Proposed functionality**

- Continuous interpolation of compatible numeric parameters.
- Morphing of modulation-matrix depths.
- Touch-strip, pressure and MIDI CC control.
- Configurable smoothing curves.
- Tempo-synchronized morphing.
- Automatic long-duration morphing.
- Morph-position locking and automation.

Different parameter types require different transition strategies.

Continuous values can be interpolated. Discrete states require threshold or quantized switching. Oscillator-type transitions are a separate research problem and must not be described as continuous crossfades unless simultaneous engine rendering is demonstrated.

Morphing should be deterministic, reversible and playable in real time.

### 2.6 FreakMutate — Evolutionary Sound Design

**Priority: P1**

Introduce an intelligent parameter mutation system for generating sound variations while retaining selected musical properties.

**Proposed functionality**

- Global and per-parameter mutation strength.
- Parameter locks protecting selected characteristics.
- Oscillator-aware mutation distributions.
- Controlled harmonic, rhythmic and modulation variation.
- A/B comparison and mutation history.
- Deterministic mutation from stored random seeds.
- Audition and rollback.
- Progressive mutation over configurable musical intervals.

Suggested mutation modes:

**Subtle:** Slow timbral drift with preserved harmonic structure.

**Texture:** Stronger changes to modulation, oscillator parameters and noise characteristics.

**Rhythmic:** Variations in triggering, timing, probability and modulation sequences.

**Unstable:** Aggressive transformations intended for industrial and experimental sound design.

Mutation must remain non-destructive until explicitly committed. The system should avoid invalid states and prevent uncontrolled randomization of parameters marked as protected.

### 2.7 FreakArp — Algorithmic Arpeggiator

**Priority: P2**

Extend the stock arpeggiator with generative melodic behavior.

Candidate algorithms include Euclidean rhythms, Brownian pitch movement, Markov-chain transitions, bounded stochastic melodies, scale-constrained random walks and rule-based note generation.

The arpeggiator should integrate with FreakLocks and FreakMod rather than establish an independent sequencing system.

Potential capabilities include variable sequence lengths, melodic memory, controlled mutation, pattern continuation and generative harmonization.

### 2.8 FreakScenes — Performance Macros and Keyboard Zones

**Priority: P1/P2**

Provide a performance layer for controlling complex modulation and sequencing behaviors.

**Macro scenes**

- Store combinations of modulation settings, locks and macro values.
- Recall scenes without necessarily loading a new preset.
- Change multiple parameters through a single performance action.
- Support immediate, quantized and smoothed transitions.

**Keyboard performance zones**

- Trigger or transpose sequences.
- Start and stop generative processes.
- Switch modulation scenes.
- Control probability, mutation and variation.
- Maintain drone notes while other zones remain playable.

The available 25-key interface limits the number of practical zones. The UI should favor configurable, minimal layouts over excessive subdivision.

### 2.9 FreakEngines — Experimental Oscillator Development

**Priority: P3 — Advanced research**

Investigate replacing or extending the existing digital synthesis algorithms.

Candidate engines include:

- Nonlinear FM and feedback FM.
- Phase distortion.
- Wavefolding and nonlinear waveshaping.
- Inharmonic resonators.
- Physical-modeling variations.
- Chaotic oscillators.
- Metallic and friction-inspired synthesis.
- Feedback-based drones and unstable spectral textures.

A first implementation should target replacing one existing engine rather than expanding the complete engine catalog.

Engine work must be isolated from sequencer and modulation development until CPU, memory and DSP integration constraints are sufficiently understood.

### 2.10 FreakBridge — External MIDI and CV Performance

**Priority: P2**

Extend the MicroFreak's usefulness as a generative controller for external synthesizers and modular equipment.

Initial target: **Make Noise 0-Coast**.

**Proposed functionality**

- Generate MIDI notes and clock-aware modulation events.
- Route generative sequences to external equipment.
- Provide configurable transposition and scale quantization.
- Explore enhanced use of existing pitch CV, gate and pressure outputs.
- Synchronize generative modulation with incoming or outgoing clock.
- Define external modulation mappings independently of internal synthesis.

FreakBridge must respect the physical output count, voltage ranges, DAC behavior and update capabilities. Arbitrary multichannel CV output cannot be assumed.

## 3. Technical Architecture

FREAKOS should use a modular architecture built around five major subsystems.

| Subsystem | Responsibility |
|---|---|
| Sequencing Core | Musical clock, events, step data, locks, note allocation and conditional triggering |
| Modulation Engine | Signal generators, transformations, modulation routing and per-voice state |
| Synthesis Adapter | Integration with existing oscillator engines, parameter structures and analog-control interfaces |
| Performance/UI Layer | OLED navigation, hardware controls, live editing, scenes and macros |
| Persistence & Compatibility | Extended patch data, migrations, firmware validation, backup and recovery |

**Proposed logical signal flow**

Input and clock events → sequencer and generative event processing → modulation evaluation → parameter resolution → voice/synthesis integration → audio and external outputs.

The parameter resolver must define an explicit precedence model for physical controls, preset values, parameter locks, morphing, generative modulation and incoming MIDI.

A possible default order is:

1. Preset and scene values establish the base state.
2. Active step locks override designated base parameters.
3. Morphing changes the relevant effective base or lock values.
4. Modulation is applied using defined additive or multiplicative rules.
5. Values are constrained, smoothed and sent to compatible destinations.

The ordering must be configurable only where justified; inconsistent parameter interactions would make the instrument unpredictable in an undesirable way.

### Implementation strategy

Favor patching and extending the existing firmware rather than immediately attempting a full replacement.

Maintain a hardware-independent reference implementation of sequencer and modulation algorithms for desktop testing.

Only deploy modules to the MicroFreak after proving their memory, timing and integration requirements.

Evaluate compatibility with existing patch frameworks. Do not assume separately developed binary modifications can be combined safely.

## 4. Development Roadmap

| Phase | Scope | Exit criterion |
|---|---|---|
| 0 — Research | Firmware analysis, hardware inventory, recovery and baseline measurements | A safe patching workflow and documented extension points |
| 1 — Sequencer | FreakLocks, live editing and basic OLED navigation | Real-time editing of a running 16-step pattern |
| 2 — Modulation | Random walks, clocked sources, modulation processors | Stable generative modulation of supported destinations |
| 3 — Voice & Drone | Per-voice experiments and FreakDrone | Sustained, independently evolving four-voice texture |
| 4 — Evolution | FreakMorph and FreakMutate | Reversible morphing and controlled patch evolution |
| 5 — Performance | Scenes, generative arp and external control | Playable integrated performance workflow |
| 6 — DSP Research | Experimental oscillators and advanced routing | At least one validated experimental synthesis engine |
| 7 — Release | Documentation, tests, packaging and compatibility | Reproducible public beta with recovery instructions |

This ordering represents dependencies, not a fixed calendar. The scope of later phases must remain adjustable according to hardware findings.

## 5. Initial Minimum Viable Product

The first playable version should deliberately exclude the most difficult oscillator and per-voice architectural changes.

**FREAKOS 0.1 — Generative Sequencer**

Deliver the following:

- A 16-step sequence with live parameter-lock editing.
- Locks for at least Wave, Timbre, Shape and one compatible modulation amount or filter parameter.
- Per-step probability and conditional triggering.
- Two generative modulation sources: bounded random walk and clocked sample-and-hold.
- A minimal OLED editor using existing controls.
- Real-time changes without playback interruption.
- Functional save, load and rollback.
- Integration with original MIDI clock behavior.

The main objective is a playable proof of concept, not a broad feature demonstration.

**Definition of done**

A user can create and play a 16-step sequence, introduce several different timbres, modify locks during playback, apply generative modulation and save the resulting performance configuration.

Playback must remain stable under extended testing. Recovery to the official firmware must be demonstrated before beta distribution.

Oscillator-type locks should only enter this release if engine-switch testing proves them reliable.

## 6. Critical Technical Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Limited flash and RAM | Critical | Memory audit, compact representations, reclaimable code investigation |
| Real-time engine switching | High | Early proof of concept and defined fallback behavior |
| Shared analog filter | Architectural | Separate global and per-voice destinations |
| Modulation CPU cost | High | Control-rate evaluation, profiling and bounded complexity |
| Firmware compatibility | High | Exact-version matching, checksums and isolated patches |
| Preset corruption | High | Backups, versioned metadata and migration tests |
| OLED/UI limitations | Medium | Minimal paging, reusable components and usability tests |
| Clock jitter and audio glitches | Critical | Baseline comparison, timing instrumentation and hardware stress tests |
| Third-party code and licensing | High | Source/provenance audit and compatible distribution model |

**Go/no-go decision:** If native code capacity prevents a reliable, playable implementation of the initial sequencer, the project should retain its portable sequencing and modulation core and evaluate an external MIDI controller/companion architecture.

This fallback must be treated as a separate delivery architecture, not represented as equivalent native firmware functionality.

## 7. Development Standards

The project should be developed as a reproducible embedded-systems research project rather than a succession of experimental binary modifications.

Minimum requirements:

- Version-controlled source, tooling and reverse-engineering findings.
- Architecture decision records for consequential firmware modifications.
- A single continuously maintained development status file.
- Automated tests for sequencing, modulation and serialization.
- Deterministic test cases with random seeds.
- Firmware image integrity checks.
- Explicit memory and performance budgets.
- Hardware-in-the-loop tests for critical changes.
- Documented recovery and rollback procedures.
- No redistribution of proprietary firmware binaries.
- Clear attribution and licensing review of reused implementations.

Development agents may assist with binary analysis, implementation and testing, but should not independently flash hardware or modify calibration and bootloader regions.

## 8. Success Criteria

The project will be considered successful when the resulting instrument can:

1. Create musically varied sequences with independently programmed synthesis parameters.
2. Edit parameter locks while playback continues.
3. Produce evolving, partly autonomous modulation and drones.
4. Support controlled improvisation, mutation and sound morphing.
5. Maintain musical timing and audio reliability under extended operation.
6. Operate primarily through the MicroFreak's existing physical controls.
7. Recover safely from failed updates and preserve user data.
8. Provide a documented, reproducible research and development foundation for future custom oscillator engines.

## 9. Long-Term Direction

The intended final result is a compact experimental instrument that can serve simultaneously as:

- A digital noise and inharmonic synthesis laboratory.
- An autonomous dark-ambient drone generator.
- A parameter-locked performance sequencer.
- A generative modulation source for modular equipment.
- An evolving sound-design instrument.

**FREAKOS should prioritize expressive depth, controlled complexity and sonic originality over raw feature count.**

