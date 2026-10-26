# Local inputs

The repository contains original code, patch definitions and documentation. It
does not include Arturia firmware, generated updates, the Arturia manual or local
editor settings. Those files remain on your computer and are ignored by Git.

## Official firmware

Obtain your own official MicroFreak 5.0.0.2084 update through Arturia or MIDI
Control Center. Store it at:

```text
original_firmware/MicroFreak_Firmware_Update_5_0_0_2084.mff
```

Expected SHA-256:
`c2b405e3c8565b7b73b4dd06522559458190082a8ba633cc5f1bcc43dc64332c`.
The builder rejects other versions and previously patched inputs. Validate it
with `python3 tools/firmware.py inspect` followed by the local file path. Tests
also accept another location through `FREAKPATCH_STOCK_MFF`.

## Optional manual

Obtain the English MicroFreak 5.0.1 user manual from
[Arturia downloads](https://www.arturia.com/support/downloads-manuals/product/microfreak).
For the same local reference path used during development, save your copy as:

```text
docs/microfreak_Manual_5_0_1_EN.pdf
```

The manual is for reference only; building and testing do not require it. An
existing local copy is preserved when preparing the Git checkpoint. It is not
part of the repository's MIT-licensed source distribution.

Generated MFFs, JSON build manifests, private firmware analysis and emulator
scratch data stay under ignored `build/`. Never commit or upload those artifacts.
Versioned revision notes record hashes and selected build metadata without
including firmware bytes; see [revisions](revisions.md).
