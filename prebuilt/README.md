# prebuilt/

Dictionary-app formats that can't be compiled in CI, built by hand on a Mac
and committed here. `build_all.py` picks up any `<source-id>-<format>.zip`
found in this directory and adds it to the site's manifest alongside the
auto-generated formats, under a filename with `-compiled` appended so it
never collides with the pyglossary-generated version of the same format.

## Apple Dictionary (`.dictionary`)

pyglossary can only emit the *source* for Apple's format (`.xml` + `.css` +
`.plist` + `Makefile`) — see `<source-id>-appledict.zip` in the normal
per-source output. Turning that into an actual `.dictionary` bundle that
Dictionary.app can load requires Apple's **Dictionary Development Kit**,
a macOS-only, login-gated download from developer.apple.com with no public
URL or API — it cannot run in GitHub Actions (`ubuntu-latest`).

### Regenerating after av-ru data changes

1. Install the Dictionary Development Kit once (developer.apple.com →
   Downloads → "Dictionary Development Kit"), unpack it to
   `/Applications/Dictionary Development Kit`.
2. Rebuild normally (`./build.sh`) so `docs/av-ru/av-ru-appledict.zip`
   (source form) is current.
3. Unzip it to a scratch folder and run:
   ```sh
   make all      # -> objects/av-ru.dictionary
   ```
4. Zip the bundle preserving its directory structure and the `.dictionary`
   name as the top-level entry:
   ```sh
   ditto -c -k --sequesterRsrc --keepParent objects/av-ru.dictionary \
     av-ru-appledict-compiled.zip
   ```
5. Copy the result into `prebuilt/av-ru-appledict-compiled.zip`, commit.

Repeat per source id if other dictionaries get an AppleDict export too.
