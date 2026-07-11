#!/bin/sh

set -eu

ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
TMP=$(mktemp -d "${TMPDIR:-/tmp}/skills-installer-test.XXXXXXXX")
trap 'rm -rf "$TMP"' EXIT HUP INT TERM

fail() {
    printf 'FAIL: %s\n' "$*" >&2
    exit 1
}

assert_file() {
    [ -f "$1" ] || fail "expected file: $1"
}

assert_absent() {
    [ ! -e "$1" ] || fail "expected path to be absent: $1"
}

assert_contains() {
    grep -F "$2" "$1" >/dev/null 2>&1 || fail "expected '$2' in $1"
}

make_skill() {
    mkdir -p "$1/skills/$2"
    printf '%s\n' '---' "name: $2" 'description: Test fixture.' '---' '' "# $2" >"$1/skills/$2/SKILL.md"
    printf '%s\n' "$3" >"$1/skills/$2/payload.txt"
}

mkdir -p "$TMP/archives" "$TMP/bin"

main_tree=$TMP/main/repository-main
make_skill "$main_tree" zebra-skill zebra
make_skill "$main_tree" alpha-skill alpha
make_skill "$main_tree" newly-added dynamic
tar -czf "$TMP/archives/main.tar.gz" -C "$TMP/main" repository-main

develop_tree=$TMP/develop/repository-develop
make_skill "$develop_tree" develop-only develop
tar -czf "$TMP/archives/develop.tar.gz" -C "$TMP/develop" repository-develop
printf '%s\n' 'not an archive' >"$TMP/archives/broken.tar.gz"

cat >"$TMP/bin/curl" <<'EOF'
#!/bin/sh
set -eu
output=''
url=''
while [ "$#" -gt 0 ]; do
    case "$1" in
        -o) output=$2; shift 2 ;;
        -*) shift ;;
        *) url=$1; shift ;;
    esac
done
ref=${url##*/}
cp "$FIXTURE_ARCHIVES/$ref.tar.gz" "$output"
EOF
chmod +x "$TMP/bin/curl"

run_installer() {
    home=$1
    shift
    PATH="$TMP/bin:$PATH" FIXTURE_ARCHIVES="$TMP/archives" AGENTS_HOME="$home" sh "$ROOT/install.sh" "$@"
}

PATH="$TMP/bin:$PATH" FIXTURE_ARCHIVES="$TMP/archives" sh "$ROOT/install.sh" --list >"$TMP/list.out" 2>"$TMP/list.err"
expected=$(printf '%s\n' alpha-skill newly-added zebra-skill)
actual=$(cat "$TMP/list.out")
[ "$actual" = "$expected" ] || fail "skills were not listed in sorted order"
printf 'ok - dynamic discovery and sorted listing\n'

run_installer "$TMP/all-home" --all >"$TMP/all.out" 2>"$TMP/all.err"
assert_file "$TMP/all-home/skills/alpha-skill/SKILL.md"
assert_file "$TMP/all-home/skills/newly-added/SKILL.md"
assert_file "$TMP/all-home/skills/zebra-skill/SKILL.md"
printf 'ok - install all\n'

run_installer "$TMP/selected-home" zebra-skill alpha-skill >"$TMP/selected.out" 2>"$TMP/selected.err"
assert_file "$TMP/selected-home/skills/zebra-skill/SKILL.md"
assert_file "$TMP/selected-home/skills/alpha-skill/SKILL.md"
assert_absent "$TMP/selected-home/skills/newly-added"
printf 'ok - install selected skills\n'

run_installer "$TMP/ref-home" --ref develop --all >"$TMP/ref.out" 2>"$TMP/ref.err"
assert_file "$TMP/ref-home/skills/develop-only/SKILL.md"
assert_absent "$TMP/ref-home/skills/alpha-skill"
printf 'ok - custom ref\n'

if run_installer "$TMP/unknown-home" missing-skill >"$TMP/unknown.out" 2>"$TMP/unknown.err"; then
    fail "unknown skill succeeded"
fi
assert_contains "$TMP/unknown.err" "unknown skill 'missing-skill'"
assert_absent "$TMP/unknown-home"
printf 'ok - unknown skill rejected before destination changes\n'

if run_installer "$TMP/broken-home" --ref broken --all >"$TMP/broken.out" 2>"$TMP/broken.err"; then
    fail "malformed archive succeeded"
fi
assert_contains "$TMP/broken.err" 'not a valid gzip tar archive'
assert_absent "$TMP/broken-home"
printf 'ok - malformed archive rejected\n'

if run_installer "$TMP/invalid-ref-home" --ref ../unsafe --all >"$TMP/invalid-ref.out" 2>"$TMP/invalid-ref.err"; then
    fail "invalid ref succeeded"
fi
assert_contains "$TMP/invalid-ref.err" 'invalid ref: ../unsafe'
assert_absent "$TMP/invalid-ref-home"
printf 'ok - invalid ref rejected before filesystem changes\n'

if run_installer "$TMP/no-tty-home" </dev/null >"$TMP/no-tty.out" 2>"$TMP/no-tty.err"; then
    fail "installer without a TTY or selection succeeded"
fi
assert_contains "$TMP/no-tty.err" 'pass --all or one or more skill names'
assert_absent "$TMP/no-tty-home"
printf 'ok - non-interactive run requires an explicit selection\n'

mkdir -p "$TMP/update-home/skills/zebra-skill" "$TMP/update-home/skills/unselected-skill"
printf '%s\n' stale >"$TMP/update-home/skills/zebra-skill/stale.txt"
printf '%s\n' keep >"$TMP/update-home/skills/unselected-skill/keep.txt"
run_installer "$TMP/update-home" zebra-skill >"$TMP/update.out" 2>"$TMP/update.err"
assert_absent "$TMP/update-home/skills/zebra-skill/stale.txt"
assert_file "$TMP/update-home/skills/zebra-skill/payload.txt"
assert_file "$TMP/update-home/skills/unselected-skill/keep.txt"
printf 'ok - clean replacement and preservation of unselected skills\n'

printf 'All installer tests passed.\n'
