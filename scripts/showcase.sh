#!/usr/bin/env bash
# The website showcase, built without KiCad: route the board (native plane
# verification), fill and check it natively, plot it, read the plot back,
# render the five promo views from the plotted Gerbers and record a snapshot
# that binds every input and output by SHA-256.
#
#   scripts/showcase.sh [--copper PATH] [--run-dir DIR]
#
# Writes docs/showcase/{routing-top,routing-inner,routing-bottom,routing-all,
# placement}.svg, rendering.json, the two IR excerpts and snapshot.json; the
# run keeps the board, reports and plots under build/board/runs/. A showcase is
# a routing review illustration, not a manufacturing export or release.
set -euo pipefail

die() { echo "SHOWCASE ERROR: $*" >&2; exit 2; }
sha256() { sha256sum "$1" | cut -d' ' -f1; }

project="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
copper="${COPPER:-$project/../CopperScript/target/release/copper}" run=""
while [ $# -gt 0 ]; do
  case "$1" in
    --copper) copper="$2"; shift 2 ;;
    --run-dir) run="$2"; shift 2 ;;
    *) die "unknown argument: $1" ;;
  esac
done
command -v jq > /dev/null || die "jq is required"
[ -x "$copper" ] || die "copper executable missing: $copper (make copper)"
copper="$(cd "$(dirname "$copper")" && pwd -P)/$(basename "$copper")"
cd "$project"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
run="${run:-build/board/runs/$stamp-showcase}"
[ ! -e "$run" ] || die "run directory exists: $run"
mkdir -p "$run" && run="$(cd "$run" && pwd -P)"
out="$project/docs/showcase"
mkdir -p "$out"

# Route settings: the Makefile's shared defaults plus this board's
# EXTRA_ROUTE_ARGS, with native plane verification instead of KiCad's.
route_args=(--layers 6 --fab-profile jlcpcb-six-layer --candidates 1 --feedback-iterations 1
  --router-iterations 5 --progress --fanout --plane-contact-radius-mm 5
  $(sed -n 's/^EXTRA_ROUTE_ARGS ?= //p' Makefile))

echo "Showcase run: $run"
"$copper" check board.copper --locked > "$run/check.log"
"$copper" route-board board.copper --locked "${route_args[@]}" --verify-plane-fill native \
  --report "$run/route-report.json" -o "$run/board.kicad_pcb" > "$run/routing.log" 2>&1 ||
  die "routing did not pass; see $run/routing.log"
jq -e '.status == "pass"' "$run/route-report.json" > /dev/null || die "route status is not pass"

# Fill, plot (filled and, for the fill-free combined view, unfilled) and
# check the filled board, reading its plotted copper and drills back.
"$copper" fill "$run/board.kicad_pcb" -o "$run/filled.kicad_pcb" > "$run/fill.log"
cp "$run/board.kicad_pro" "$run/filled.kicad_pro"
cp "$run/board.kicad_dru" "$run/filled.kicad_dru"
"$copper" plot "$run/filled.kicad_pcb" -o "$run/plot" > /dev/null
"$copper" plot "$run/board.kicad_pcb" -o "$run/plot-unfilled" > /dev/null
"$copper" drc "$run/filled.kicad_pcb" --report "$run/drc.json" --cam "$run/plot" > "$run/drc.log" ||
  die "native DRC or CAM read-back failed; see $run/drc.log"
grep -q '^CAM read-back PASSED' "$run/drc.log" || die "CAM read-back did not pass"

# The five promo views, from the plotted artwork. Gold is exposed copper
# (copper inside the solder-mask openings) or, in placement, the openings.
gold='#d9a441' ink='#3a3f3b' edge='Edge.Cuts:#5b605a'
declare -A views=(
  [routing-top]="plot|CopperAssetTracker F.Cu: top copper and silkscreen|F.Cu F.Cu&F.Mask:$gold F.Silkscreen:$ink $edge"
  [routing-inner]="plot|CopperAssetTracker In2.Cu: inner copper|In2.Cu:#c27a2c $edge"
  [routing-bottom]="plot|CopperAssetTracker B.Cu: bottom copper, viewed from above|B.Cu B.Cu&B.Mask:$gold $edge"
  [routing-all]="plot-unfilled|CopperAssetTracker: all six copper layers, zone fills not drawn|B.Cu:#4d7fc4:0.85 In4.Cu:#db628b:0.85 In3.Cu:#4fcbcb:0.85 In2.Cu:#c27a2c:0.85 In1.Cu:#5aa95a:0.85 F.Cu:#c83434:0.9 B.Cu&B.Mask:$gold F.Cu&F.Mask:$gold $edge"
  [placement]="plot|CopperAssetTracker placement: front silkscreen and solder-mask openings|F.Mask:$gold F.Silkscreen:$ink $edge"
)
rendering='{}'
for name in routing-top routing-inner routing-bottom routing-all placement; do
  IFS='|' read -r plot title layers <<< "${views[$name]}"
  args=()
  for layer in $layers; do args+=(--layer "$layer"); done
  "$copper" render "$run/$plot" -o "$out/$name.svg" --title "$title" "${args[@]}" > /dev/null
  rendering="$(jq --arg name "$name.svg" --arg plot "$plot" --arg title "$title" --arg layers "$layers" \
    '.[$name] = {plot: $plot, zone_fills: ($plot == "plot"), title: $title, plates: ($layers | split(" "))}' <<< "$rendering")"
done

# IR excerpts: one decoupling capacitor with its pin association and one
# supply net, from the compiled source; their placements from the board.
"$copper" compile board.copper --locked --offline -o "$run/board.json" > /dev/null
jq '{schema, kind, name, components: [.components[] | select(.ref == "C_MCU")], nets: [.nets[] | select(.name == "V3V8")]}' \
  "$run/board.json" > "$out/electrical-ir.excerpt.json"
awk '
  /^  \(footprint "/ { split($0, q, "\""); footprint = q[2]; at = ""; next }
  /^    \(at / && footprint != "" && at == "" { at = $2 " " $3 " " ($4 == "" ? "0)" : $4); next }
  /^    \(property "Reference" "/ && footprint != "" { split($0, q, "\""); print q[4] "\t" footprint "\t" at; footprint = "" }
' "$run/filled.kicad_pcb" | tr -d ')' | jq -R -s '
  split("\n") | map(select(length > 0) | split("\t")) | map({reference: .[0], footprint: .[1],
    position_mm: {x: (.[2] | split(" ")[0]), y: (.[2] | split(" ")[1])}, rotation_degrees: (.[2] | split(" ")[2])})
  | map(select(.reference == "U_MODEM" or .reference == "C_MCU"))
  | {note: "Selected placements from the routed showcase board; not a full physical-IR serialization or production approval.",
     placements: ., units: "millimetres and degrees as represented in the KiCad PCB"}' > "$out/physical-ir.excerpt.json"
[ "$(jq '.placements | length' "$out/physical-ir.excerpt.json")" = 2 ] || die "IR placement excerpt incomplete"

jq -n --argjson views "$rendering" --arg renderer "copper render" \
  '{schema: "copperassettracker-showcase-rendering/v3", renderer: $renderer, viewpoint: "from above, unmirrored",
    exposed_copper_color: "#d9a441", views: $views}' > "$out/rendering.json"

# The snapshot: inputs, compiler, results and every published asset.
compiler_root="$(cd "$(dirname "$copper")/../.." && pwd -P)"
inputs='{}'
for file in board.copper copper.mod copper.lock assembly.lock Makefile $(find packages src -name '*.copper' 2> /dev/null | sort); do
  [ -f "$file" ] && inputs="$(jq --arg f "$file" --arg h "$(sha256 "$file")" '.[$f] = $h' <<< "$inputs")"
done
assets='{}'
for name in routing-top.svg routing-inner.svg routing-bottom.svg routing-all.svg placement.svg rendering.json \
  electrical-ir.excerpt.json physical-ir.excerpt.json; do
  assets="$(jq --arg f "$name" --arg h "$(sha256 "$out/$name")" '.[$f] = $h' <<< "$assets")"
done
jq -n \
  --arg candidate "native-showcase-${stamp:0:8}" --arg created "$stamp" \
  --arg commit "$(git rev-parse HEAD)" --arg changes "$(git status --porcelain --untracked-files=no | grep -v '^ M docs/showcase/' || true)" \
  --argjson inputs "$inputs" \
  --arg compiler_commit "$(git -C "$compiler_root" rev-parse HEAD 2> /dev/null || echo unknown)" \
  --arg compiler_changes "$(git -C "$compiler_root" status --porcelain --untracked-files=no 2> /dev/null | grep -v '^ M site/' || true)" \
  --arg compiler_sha "$(sha256 "$copper")" \
  --arg route_args "${route_args[*]}" \
  --slurpfile route "$run/route-report.json" --slurpfile drc "$run/drc.json" \
  --arg route_sha "$(sha256 "$run/route-report.json")" --arg board_sha "$(sha256 "$run/board.kicad_pcb")" \
  --arg filled_sha "$(sha256 "$run/filled.kicad_pcb")" --arg drc_sha "$(sha256 "$run/drc.json")" \
  --arg cam "$(grep '^CAM read-back' "$run/drc.log")" \
  --arg footprints "$(grep -c '^  (footprint ' "$run/filled.kicad_pcb")" \
  --argjson assets "$assets" '
  $route[0] as $r | $drc[0] as $d | {
    schema: "copperassettracker-showcase/v3",
    candidate: $candidate, created_utc: $created,
    source: {git_commit: $commit, tracked_changes: $changes, input_sha256: $inputs},
    compiler: {copperscript_commit: $compiler_commit, tracked_changes: $compiler_changes, executable_sha256: $compiler_sha},
    route: {options: $route_args, status: $r.status, report_sha256: $route_sha, unfilled_pcb_sha256: $board_sha,
      ordinary_nets_routed: $r.connectivity.routed_ordinary_net_count, unrouted_ordinary_nets: $r.connectivity.unrouted_ordinary_nets,
      tracks: $r.summary.copper.tracks, vias: $r.summary.copper.vias, track_length_mm: $r.summary.copper.track_length_mm,
      plane_fill: "native", requirements: $r.requirements.counts},
    pcb_sha256: $filled_sha, component_count: ($footprints | tonumber),
    copper_layers: ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "B.Cu"],
    native_drc: {report_sha256: $drc_sha, passed: $d.passed, violations: ($d.violations | length),
      unconnected: ($d.unconnected_items | length), not_checked: $d.not_checked, cam_readback: $cam},
    kicad: "not run: fill, DRC, plot and rendering are native",
    independent_cam: "not run", manufacturing_export: "not generated", qualified_release: false,
    rendered_assets: $assets}' > "$out/snapshot.json"
echo "Showcase -> docs/showcase (candidate native-showcase-${stamp:0:8}); review captions and counts before publishing."
